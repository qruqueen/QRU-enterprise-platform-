import asyncio
import copy
import hashlib
import io
import sys
import zipfile
from types import SimpleNamespace

import pytest

from publisher_lite import CURRENT_CHANNEL, CURRENT_SCHEMA_VERSION, PublisherLiteError, publish_release, validate_release


def _fixture():
    files = {
        "customer/example.pdf": b"%PDF-1.7\nsynthetic fixture\n%%EOF\n",
        "cover/example.png": b"\x89PNG\r\n\x1a\nsynthetic fixture",
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, value in files.items():
            archive.writestr(path, value)
    package = output.getvalue()
    record = {
        "schema_version": "1.0",
        "product": {
            "product_key": "qru-synthetic-publisher-lite-test", "version": "1.0.0",
            "title": "Synthetic Publisher Lite Test", "description": "Non-production fixture.",
            "publisher": "QRU Press", "series": "Test", "category": "Test",
            "product_type": "Digital Guide / Workbook",
            "price": {"currency": "USD", "amount_cents": 100}, "tags": ["test"],
        },
        "assets": {
            "package": {"provider": "test", "sha256": hashlib.sha256(package).hexdigest()},
            "files": [
                {"role": "customer_download", "path": "customer/example.pdf", "media_type": "application/pdf",
                 "sha256": hashlib.sha256(files["customer/example.pdf"]).hexdigest()},
                {"role": "storefront_cover", "path": "cover/example.png", "media_type": "image/png",
                 "sha256": hashlib.sha256(files["cover/example.png"]).hexdigest()},
            ],
        },
        "distribution": {"channel": "qru_online_v2", "slug": "synthetic-publisher-lite-test",
                         "visibility": "public", "delivery": "secure_download"},
        "approval": {"status": "APPROVED_FOR_RELEASE", "approved_by": "Founder",
                     "customer_files_frozen": True},
        "validation": {"ready_for_ingest": True, "checksums_verified": True,
                       "customer_files_modified_after_approval": False},
    }
    return record, package


def test_current_contract_is_publisher_lite_1_0():
    record, _ = _fixture()
    assert CURRENT_SCHEMA_VERSION == "1.0"
    assert record["schema_version"] == CURRENT_SCHEMA_VERSION
    assert record["distribution"]["channel"] == CURRENT_CHANNEL == "qru_online_v2"
    assert {"product", "assets", "distribution", "approval", "validation"} <= set(record)


def test_approved_zip_validates_unchanged():
    record, package = _fixture()
    release = validate_release(record, package)
    assert release.product_key == "qru-synthetic-publisher-lite-test"
    assert release.version == "1.0.0"
    assert release.idempotency_key.endswith(hashlib.sha256(package).hexdigest())


@pytest.mark.parametrize("mutator,code", [
    (lambda r: r["distribution"].update(channel="legacy"), "WRONG_CHANNEL"),
    (lambda r: r["approval"].update(status="PENDING"), "FOUNDER_APPROVAL_REQUIRED"),
    (lambda r: r["validation"].update(ready_for_ingest=False), "NOT_READY_FOR_INGEST"),
])
def test_governance_failure_is_blocked_before_catalog_write(mutator, code):
    record, package = _fixture()
    mutator(record)
    with pytest.raises(PublisherLiteError) as exc:
        validate_release(record, package)
    assert exc.value.code == code


class _Result:
    upserted_id = None


class _Collection:
    def __init__(self):
        self.docs = []

    def _match(self, doc, query):
        return all(doc.get(key) == value for key, value in query.items())

    async def find_one(self, query, projection=None):
        value = next((copy.deepcopy(doc) for doc in self.docs if self._match(doc, query)), None)
        if value and projection and projection.get("_id") == 0:
            value.pop("_id", None)
        return value

    async def find_one_and_update(self, query, update, upsert=False, return_document=None):
        value = await self.find_one(query)
        if not value and upsert:
            value = {**query, **update.get("$setOnInsert", {})}
            self.docs.append(copy.deepcopy(value))
        return copy.deepcopy(value)

    async def update_one(self, query, update, upsert=False):
        index = next((i for i, doc in enumerate(self.docs) if self._match(doc, query)), None)
        if index is None:
            if not upsert:
                return _Result()
            self.docs.append({**query, **update.get("$setOnInsert", {}), **update.get("$set", {})})
        else:
            self.docs[index].update(update.get("$set", {}))
        return _Result()

    async def replace_one(self, query, replacement, upsert=False):
        index = next((i for i, doc in enumerate(self.docs) if self._match(doc, query)), None)
        if index is None:
            self.docs.append(copy.deepcopy(replacement))
        else:
            self.docs[index] = copy.deepcopy(replacement)
        return _Result()


class _Db:
    def __init__(self):
        self.publisher_lite_version_claims = _Collection()
        self.publisher_lite_receipts = _Collection()
        self.publisher_lite_queue = _Collection()
        self.products = _Collection()


def test_catalog_write_receipt_and_exact_replay(monkeypatch):
    record, package = _fixture()
    db, stored = _Db(), {}

    async def put(path, data, media_type):
        stored[path] = (bytes(data), media_type)
        return True

    monkeypatch.setitem(sys.modules, "database", SimpleNamespace(db=db))
    monkeypatch.setitem(sys.modules, "models", SimpleNamespace(now_iso=lambda: "2026-09-24T12:00:00Z"))
    monkeypatch.setitem(sys.modules, "storage", SimpleNamespace(aput_verified_object=put))
    monkeypatch.setitem(sys.modules, "pymongo", SimpleNamespace(ReturnDocument=SimpleNamespace(AFTER="after")))
    monkeypatch.setitem(sys.modules, "pymongo.errors", SimpleNamespace(DuplicateKeyError=RuntimeError))
    first = asyncio.run(publish_release(record, package))
    second = asyncio.run(publish_release(record, package))
    assert first["status"] == "Published"
    assert first["download_attached"] is True
    assert first["product_url"] == "https://qru-online.com/product/synthetic-publisher-lite-test"
    assert second["receipt_id"] == first["receipt_id"]
    assert second["idempotent_replay"] is True
    assert len(db.products.docs) == 1
    assert len(db.publisher_lite_receipts.docs) == 1
    assert len(stored) == 2
