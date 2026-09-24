"""Portable QRU object storage with legacy Emergent compatibility.

The container filesystem is EPHEMERAL (wiped on every redeploy/restart), so all runtime-generated
binary files (currently videos) are stored here instead. MongoDB records reference the object
`storage_path`; the DB is the source of truth. Access is always brokered through the backend.
"""
import os
import time
import logging
import requests

logger = logging.getLogger("qru.storage")

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "qru-online"
_EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
_storage_key = None


def _s3_enabled():
    return bool(os.environ.get("S3_BUCKET"))


def _s3_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT_URL") or None,
        region_name=os.environ.get("S3_REGION") or None,
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY_ID") or os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("S3_SECRET_ACCESS_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )


def init_storage(force=False):
    global _storage_key
    if _storage_key and not force:
        return _storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": _EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    _storage_key = resp.json()["storage_key"]
    logger.info("object storage initialized")
    return _storage_key


def put_object(path: str, data: bytes, content_type: str) -> dict:
    if _s3_enabled():
        _s3_client().put_object(Bucket=os.environ["S3_BUCKET"], Key=path, Body=data, ContentType=content_type)
        return {"path": path, "provider": "s3"}
    for attempt in range(3):
        key = init_storage(force=(attempt > 0))
        resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": key, "Content-Type": content_type},
                            data=data, timeout=180)
        if resp.status_code == 403 and attempt < 2:
            continue
        if resp.status_code == 429 and attempt < 2:
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()


def get_object(path: str) -> bytes:
    if _s3_enabled():
        return _s3_client().get_object(Bucket=os.environ["S3_BUCKET"], Key=path)["Body"].read()
    for attempt in range(3):
        key = init_storage(force=(attempt > 0))
        resp = requests.get(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": key}, timeout=120)
        if resp.status_code == 403 and attempt < 2:
            continue
        if resp.status_code == 429 and attempt < 2:
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
        return resp.content
    resp.raise_for_status()


# Async wrappers (offload blocking requests to a thread so the event loop isn't blocked).
import asyncio


async def aput_object(path: str, data: bytes, content_type: str) -> dict:
    return await asyncio.to_thread(put_object, path, data, content_type)


async def aget_object(path: str) -> bytes:
    return await asyncio.to_thread(get_object, path)


def path_exists(path: str) -> bool:
    if _s3_enabled():
        try:
            _s3_client().head_object(Bucket=os.environ["S3_BUCKET"], Key=path)
            return True
        except Exception:
            return False
    for attempt in range(2):
        try:
            key = init_storage(force=(attempt > 0))
            response = requests.get(f"{STORAGE_URL}/objects/{path}",
                                    headers={"X-Storage-Key": key, "Range": "bytes=0-0"}, timeout=30)
            if response.status_code == 403 and attempt < 1:
                continue
            return response.status_code in (200, 206)
        except Exception:
            return False
    return False


def put_verified_object(path: str, data: bytes, content_type: str) -> bool:
    for _ in range(2):
        try:
            put_object(path, data, content_type)
            if path_exists(path):
                return True
        except Exception as exc:
            logger.warning("verified object write failed for %s: %s", path, exc)
    return False


async def aput_verified_object(path: str, data: bytes, content_type: str) -> bool:
    return await asyncio.to_thread(put_verified_object, path, data, content_type)


# --------------------------------------------------------------------------- #
# Phase B — Durable rendered-asset mirror.
# The rendered-assets directory (/app/backend/rendered_assets) is EPHEMERAL. To
# survive redeploys every rendered file (cover / EPUB / PDF / deliverable / audio)
# is mirrored here under a durable `{APP_NAME}/assets/{fid}` object path. The
# filename (fid) is globally unique, so it doubles as the durable key.
# --------------------------------------------------------------------------- #
ASSET_PREFIX = f"{APP_NAME}/assets"

_MIME = {
    "pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "html": "text/html", "epub": "application/epub+zip", "mp4": "video/mp4", "mp3": "audio/mpeg",
    "zip": "application/zip", "json": "application/json", "txt": "text/plain",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def content_type_for(fid: str) -> str:
    ext = fid.rsplit(".", 1)[-1].lower() if "." in fid else ""
    return _MIME.get(ext, "application/octet-stream")


def asset_object_path(fid: str) -> str:
    return f"{ASSET_PREFIX}/{fid}"


def object_exists(fid: str) -> bool:
    """Cheap existence check for a durable asset (ranged 1-byte GET, no full download)."""
    if _s3_enabled():
        return path_exists(asset_object_path(fid))
    for attempt in range(2):
        try:
            key = init_storage(force=(attempt > 0))
            resp = requests.get(f"{STORAGE_URL}/objects/{asset_object_path(fid)}",
                                headers={"X-Storage-Key": key, "Range": "bytes=0-0"}, timeout=30)
            if resp.status_code == 403 and attempt < 1:
                continue
            return resp.status_code in (200, 206)
        except Exception as e:
            logger.info("object_exists check failed for %s: %s", fid, e)
            return False
    return False


def mirror_file(fid: str, data: bytes, content_type: str = None) -> bool:
    """Best-effort durable mirror of a rendered asset WITH retrieval verification.
    A successful PUT is NOT proof the object is actually retrievable (that gap is exactly
    what lost cover masters in production), so we verify with a ranged GET and retry once.
    NEVER raises — a storage hiccup must not fail a render. Returns True only when the
    object is confirmed retrievable from durable storage."""
    ct = content_type or content_type_for(fid)
    for attempt in range(2):
        try:
            put_object(asset_object_path(fid), data, ct)
        except Exception as e:
            logger.warning("asset mirror put failed for %s (attempt %d): %s", fid, attempt + 1, e)
            continue
        try:
            if object_exists(fid):
                return True
        except Exception as e:
            logger.warning("asset mirror verify errored for %s: %s", fid, e)
        logger.warning("asset mirror UNVERIFIED for %s (attempt %d) — retrying", fid, attempt + 1)
    logger.warning("asset mirror FAILED durable verification for %s", fid)
    return False


def ensure_local(fid: str, dest_path: str) -> bool:
    """Guarantee a rendered asset exists on the local disk, re-downloading it from durable
    object storage if the ephemeral copy is gone. Returns True if the file is present locally."""
    if os.path.exists(dest_path):
        return True
    try:
        data = get_object(asset_object_path(fid))
    except Exception as e:
        logger.info("asset %s unavailable in durable storage: %s", fid, e)
        return False
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        logger.warning("failed to write materialized asset %s: %s", fid, e)
        return False


async def amirror_file(fid: str, data: bytes, content_type: str = None) -> bool:
    return await asyncio.to_thread(mirror_file, fid, data, content_type)


async def aensure_local(fid: str, dest_path: str) -> bool:
    return await asyncio.to_thread(ensure_local, fid, dest_path)


async def aobject_exists(fid: str) -> bool:
    return await asyncio.to_thread(object_exists, fid)
