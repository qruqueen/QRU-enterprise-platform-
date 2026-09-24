"""Publisher Lite 1.0 -> QRU Online catalog bridge."""
from __future__ import annotations

import hashlib
import io
import mimetypes
import os
import posixpath
import re
import stat
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping, Optional

MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 250 * 1024 * 1024
MAX_MEMBER_BYTES = 100 * 1024 * 1024
MAX_MEMBERS = 100
CURRENT_SCHEMA_VERSION = "1.0"
CURRENT_CHANNEL = "qru_online_v2"


class PublisherLiteError(Exception):
    def __init__(self, code: str, stage: str, message: str, *, status: int = 400,
                 details: Optional[Mapping[str, Any]] = None):
        super().__init__(message)
        self.code, self.stage, self.message, self.status = code, stage, message, status
        self.details = dict(details or {})

    def as_dict(self) -> dict:
        result = {"ok": False, "code": self.code, "stage": self.stage, "message": self.message}
        if self.details:
            result["details"] = self.details
        return result


@dataclass(frozen=True)
class ValidatedPublisherRelease:
    record: Mapping[str, Any]
    package_bytes: bytes
    archive_sha256: str
    members: Mapping[str, bytes]
    product_key: str
    version: str
    customer_asset: Mapping[str, Any]
    cover_asset: Optional[Mapping[str, Any]]

    @property
    def idempotency_key(self):
        return f"{self.product_key}:{self.version}:{self.archive_sha256}"

    @property
    def version_key(self):
        return f"{self.product_key}:{self.version}"


def _fail(code, stage, message, *, status=400, details=None):
    raise PublisherLiteError(code, stage, message, status=status, details=details)


def _safe_path(name: str) -> str:
    if not name or "\\" in name or "\x00" in name:
        _fail("UNSAFE_ARCHIVE_PATH", "archive_safety", "Package contains an invalid path.", details={"path": name})
    path, normalized = PurePosixPath(name), posixpath.normpath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts) or normalized != name:
        _fail("UNSAFE_ARCHIVE_PATH", "archive_safety", "Package contains an unsafe path.", details={"path": name})
    return name


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _approved(value: Any) -> bool:
    normalized = re.sub(r"\s+", "_", str(value or "").strip().upper())
    return normalized in {"APPROVED", "APPROVED_FOR_RELEASE", "FOUNDER_APPROVED", "AUTHORIZED"}


def _asset_entries(assets: Mapping[str, Any]):
    entries = assets.get("files")
    if isinstance(entries, list):
        return [entry for entry in entries if isinstance(entry, Mapping)]
    return [entry for entry in (assets.get("customer"), assets.get("cover")) if isinstance(entry, Mapping)]


def validate_release(record: Mapping[str, Any], package_bytes: bytes) -> ValidatedPublisherRelease:
    """Validate the current Publisher Lite contract and unchanged approved ZIP."""
    if not isinstance(record, Mapping):
        _fail("INVALID_RECORD", "contract", "Publisher Lite record must be a JSON object.")
    if str(record.get("schema_version")) != CURRENT_SCHEMA_VERSION:
        _fail("UNSUPPORTED_SCHEMA", "contract", "Publisher Lite schema_version must be 1.0.",
              details={"received": record.get("schema_version")})
    sections = {name: record.get(name) for name in ("product", "assets", "distribution", "approval", "validation")}
    for name, value in sections.items():
        if not isinstance(value, Mapping):
            _fail("INVALID_RECORD", "contract", f"Publisher Lite record requires a {name} object.")
    product, assets = sections["product"], sections["assets"]
    distribution, approval, validation = sections["distribution"], sections["approval"], sections["validation"]
    product_key = str(product.get("product_key") or product.get("key") or "").strip()
    version = str(product.get("version") or "").strip().removeprefix("v")
    if not product_key or not version or not product.get("title"):
        _fail("PRODUCT_IDENTITY_REQUIRED", "contract", "Product key, version, and title are required.")
    if distribution.get("channel") != CURRENT_CHANNEL:
        _fail("WRONG_CHANNEL", "distribution", "Record is not routed to qru_online_v2.",
              details={"received": distribution.get("channel")})
    if not _approved(approval.get("status")):
        _fail("FOUNDER_APPROVAL_REQUIRED", "approval", "Founder approval is required.", status=409)
    if approval.get("customer_files_frozen") is not True:
        _fail("CUSTOMER_FILES_NOT_FROZEN", "approval", "Customer files must be frozen.", status=409)
    if validation.get("ready_for_ingest") is not True:
        _fail("NOT_READY_FOR_INGEST", "validation", "Record is not ready for ingest.", status=409)
    if validation.get("checksums_verified") is not True:
        _fail("CHECKSUMS_NOT_VERIFIED", "validation", "Record checksums are not verified.", status=409)
    if not isinstance(package_bytes, (bytes, bytearray)) or not package_bytes:
        _fail("EMPTY_PACKAGE", "receive", "Approved release ZIP is required.")
    package_bytes = bytes(package_bytes)
    if len(package_bytes) > MAX_ARCHIVE_BYTES:
        _fail("PACKAGE_TOO_LARGE", "receive", "Approved release ZIP exceeds 100 MB.", status=413)
    archive_sha = _sha256(package_bytes)
    expected_archive = str((assets.get("package") or {}).get("sha256") or "").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_archive) or expected_archive != archive_sha:
        _fail("PACKAGE_CHECKSUM_MISMATCH", "checksum_validation", "Release ZIP checksum does not match.",
              details={"expected": expected_archive, "actual": archive_sha})
    try:
        archive = zipfile.ZipFile(io.BytesIO(package_bytes))
    except zipfile.BadZipFile:
        _fail("INVALID_ZIP", "archive_open", "Approved release is not a valid ZIP archive.")
    members, expanded = {}, 0
    with archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        if not infos or len(infos) > MAX_MEMBERS:
            _fail("INVALID_MEMBER_COUNT", "archive_safety", "Approved release has an invalid file count.")
        for info in infos:
            name = _safe_path(info.filename)
            if name in members:
                _fail("DUPLICATE_ARCHIVE_MEMBER", "archive_safety", "Approved release has duplicate paths.")
            mode = (info.external_attr >> 16) & 0xFFFF
            if mode and stat.S_ISLNK(mode):
                _fail("UNSAFE_ARCHIVE_SYMLINK", "archive_safety", "Approved release contains a symlink.")
            if info.file_size > MAX_MEMBER_BYTES:
                _fail("MEMBER_TOO_LARGE", "archive_safety", "Approved release contains an oversized file.")
            expanded += info.file_size
            if expanded > MAX_UNCOMPRESSED_BYTES:
                _fail("UNCOMPRESSED_PACKAGE_TOO_LARGE", "archive_safety", "Expanded release exceeds 250 MB.")
            members[name] = archive.read(info)
    customer_asset, cover_asset = None, None
    for asset in _asset_entries(assets):
        path = _safe_path(str(asset.get("path") or ""))
        role, expected = str(asset.get("role") or "").strip().lower(), str(asset.get("sha256") or "").lower()
        if path not in members:
            _fail("ASSET_MISSING", "asset_validation", "Declared asset is missing.", details={"path": path})
        actual = _sha256(members[path])
        if not re.fullmatch(r"[0-9a-f]{64}", expected) or actual != expected:
            _fail("ASSET_CHECKSUM_MISMATCH", "asset_validation", "Declared asset checksum does not match.",
                  details={"path": path, "expected": expected, "actual": actual})
        if role in {"customer", "customer_download", "deliverable"}:
            if customer_asset:
                _fail("CUSTOMER_ASSET_NOT_UNIQUE", "asset_validation", "Exactly one customer download is required.")
            customer_asset = dict(asset)
        elif role in {"cover", "storefront_cover"}:
            cover_asset = dict(asset)
    if not customer_asset:
        _fail("CUSTOMER_ASSET_REQUIRED", "asset_validation", "One customer download is required.")
    if not str(customer_asset.get("path")).lower().endswith(".pdf"):
        _fail("CUSTOMER_ASSET_FORMAT", "asset_validation", "Customer download must be a PDF.")
    return ValidatedPublisherRelease(record, package_bytes, archive_sha, members, product_key, version,
                                     customer_asset, cover_asset)


def _storage_name(release, asset):
    ext = str(asset["path"]).rsplit(".", 1)[-1].lower()
    role = re.sub(r"[^a-z0-9]+", "-", str(asset.get("role") or "asset").lower()).strip("-")
    return f"publisher-lite/{release.product_key}/{release.version}/{role}-{asset['sha256'][:16]}.{ext}"


async def publish_release(record: Mapping[str, Any], package_bytes: bytes, *, actor="Publisher Lite") -> dict:
    """Store assets, atomically write a complete catalog record, and persist a receipt."""
    from database import db
    from models import now_iso
    from pymongo import ReturnDocument
    from pymongo.errors import DuplicateKeyError
    import storage
    try:
        release = validate_release(record, package_bytes)
    except PublisherLiteError as exc:
        product = record.get("product") if isinstance(record, Mapping) else {}
        product = product if isinstance(product, Mapping) else {}
        product_key = str(product.get("product_key") or product.get("key") or "unknown").strip()
        version = str(product.get("version") or "unknown").strip().removeprefix("v")
        archive_sha = _sha256(bytes(package_bytes)) if isinstance(package_bytes, (bytes, bytearray)) else "unavailable"
        failure_key = f"{product_key}:{version}:{archive_sha}"
        await db.publisher_lite_queue.update_one(
            {"_id": failure_key}, {"$set": {"status": "failed", "stage": exc.stage,
             "product_key": product_key, "version": version, "archive_sha256": archive_sha,
             "error_code": exc.code, "error_message": exc.message, "retryable": True,
             "updated_at": now_iso()}, "$setOnInsert": {"created_at": now_iso()}}, upsert=True)
        raise
    intake_key, trace_id = release.idempotency_key, f"publisher-lite-{uuid.uuid4().hex}"
    try:
        claim = await db.publisher_lite_version_claims.find_one_and_update(
            {"_id": release.version_key}, {"$setOnInsert": {"product_key": release.product_key,
             "version": release.version, "archive_sha256": release.archive_sha256, "created_at": now_iso()}},
            upsert=True, return_document=ReturnDocument.AFTER)
    except DuplicateKeyError:
        claim = await db.publisher_lite_version_claims.find_one({"_id": release.version_key})
    if not claim or claim.get("archive_sha256") != release.archive_sha256:
        _fail("PRODUCT_VERSION_CONFLICT", "idempotency", "This version already points to different ZIP bytes.", status=409)
    receipt = await db.publisher_lite_receipts.find_one({"_id": intake_key}, {"_id": 0})
    if receipt:
        return {**receipt, "idempotent_replay": True}
    await db.publisher_lite_queue.update_one(
        {"_id": intake_key}, {"$set": {"status": "processing", "stage": "validated", "trace_id": trace_id,
         "product_key": release.product_key, "version": release.version, "archive_sha256": release.archive_sha256,
         "updated_at": now_iso()}, "$setOnInsert": {"created_at": now_iso()}}, upsert=True)
    try:
        stored = {}
        for asset in (release.customer_asset, release.cover_asset):
            if not asset:
                continue
            path, object_name = str(asset["path"]), _storage_name(release, asset)
            media = str(asset.get("media_type") or mimetypes.guess_type(path)[0] or "application/octet-stream")
            if not await storage.aput_verified_object(object_name, release.members[path], media):
                _fail("DURABLE_STORAGE_FAILED", "storage", "Asset could not be verified in durable storage.",
                      status=503, details={"path": path})
            stored[str(asset.get("role"))] = {"source_path": path, "storage_path": object_name,
                "sha256": asset["sha256"], "size": len(release.members[path]), "media_type": media,
                "format": path.rsplit(".", 1)[-1].lower()}
        product, distribution = record["product"], record["distribution"]
        product_id = release.product_key
        slug = str(distribution.get("slug") or re.sub(r"[^a-z0-9]+", "-", product_id.lower()).strip("-"))
        customer = stored[str(release.customer_asset.get("role"))]
        cover = stored.get(str((release.cover_asset or {}).get("role")))
        price = product.get("price") or {}
        price_usd = price.get("amount_cents") / 100 if isinstance(price.get("amount_cents"), int) else product.get("price_usd")
        catalog = {"_id": f"publisher-lite:{release.product_key}:{release.version}", "id": product_id,
            "slug": slug, "product_key": release.product_key, "version": release.version,
            "title": product.get("title"), "subtitle": product.get("subtitle"), "description": product.get("description"),
            "product_type": product.get("product_type") or "Digital Guide / Workbook",
            "family": product.get("series") or product.get("category") or "General", "category": product.get("category"),
            "tags": product.get("tags") or [], "price": price_usd, "currency": price.get("currency") or "USD",
            "status": "Published", "published": True, "source": "publisher_lite_1.0", "channel": CURRENT_CHANNEL,
            "archive_sha256": release.archive_sha256, "deliverable_ready": True,
            "customer_deliverable": {"files": [customer], "source": "publisher_lite_1.0"}, "cover_asset": cover,
            "cover_url": f"/api/publisher-lite/products/{product_id}/cover" if cover else None,
            "approval": dict(record["approval"]), "publisher_lite_record": dict(record), "created_by": actor,
            "created_at": now_iso(), "updated_at": now_iso()}
        previous = await db.products.find_one({"product_key": release.product_key, "version": release.version})
        if previous and previous.get("archive_sha256") not in (None, release.archive_sha256):
            _fail("PRODUCT_VERSION_CONFLICT", "catalog_write", "Catalog contains different ZIP bytes.", status=409)
        if previous and previous.get("created_at"):
            catalog["created_at"] = previous["created_at"]
        await db.products.replace_one({"product_key": release.product_key, "version": release.version}, catalog, upsert=True)
        published_at = now_iso()
        site_url = str(os.environ.get("QRU_PUBLIC_SITE_URL") or "https://qru-online.com").rstrip("/")
        result = {"ok": True, "receipt_id": intake_key, "trace_id": trace_id, "product_id": product_id,
            "catalog_id": catalog["_id"], "product_key": release.product_key, "version": release.version,
            "archive_sha256": release.archive_sha256, "product_url": f"{site_url}/product/{slug}",
            "download_attached": True, "status": "Published", "published_at": published_at,
            "idempotent_replay": False}
        await db.publisher_lite_receipts.replace_one({"_id": intake_key}, {"_id": intake_key, **result}, upsert=True)
        await db.publisher_lite_queue.update_one({"_id": intake_key}, {"$set": {"status": "complete", "stage": "complete",
            "receipt_id": intake_key, "updated_at": published_at}})
        return result
    except PublisherLiteError as exc:
        await db.publisher_lite_queue.update_one({"_id": intake_key}, {"$set": {"status": "failed", "stage": exc.stage,
            "error_code": exc.code, "error_message": exc.message, "retryable": exc.status >= 500, "updated_at": now_iso()}})
        raise
    except Exception as exc:
        await db.publisher_lite_queue.update_one({"_id": intake_key}, {"$set": {"status": "failed", "stage": "internal",
            "error_code": "PUBLISH_INTERNAL_ERROR", "error_message": str(exc)[:500], "retryable": True,
            "updated_at": now_iso()}})
        raise PublisherLiteError("PUBLISH_INTERNAL_ERROR", "internal", "Publisher Lite bridge failed.", status=500) from exc
