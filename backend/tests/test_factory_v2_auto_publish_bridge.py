import hashlib
import io
import json
import zipfile

import pytest

import routers.package_intake as route
from package_intake import parse_factory_package


class FakeUpload:
    def __init__(self, body):
        self.body = body
        self.closed = False

    async def read(self, _limit):
        return self.body

    async def close(self):
        self.closed = True


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, indent=2).encode("utf-8")


def make_factory_v2_package():
    product_key = "family-money-meeting"
    version = "1.0.0"
    metadata_name = "metadata/product-metadata.json"
    pdf_name = "primary/family-money-meeting-workbook.pdf"
    files = {
        pdf_name: b"%PDF-1.7\nFactory v2 bridge fixture\n%%EOF\n",
        metadata_name: _json_bytes({
            "product_key": product_key,
            "version": version,
            "title": "Family Money Meeting",
            "category": "Personal Finance / Family & Relationships",
            "tags": ["family money meeting"],
            "price": {"amount_cents": 900, "currency": "USD"},
        }),
    }
    manifest = {
        "product_key": product_key,
        "version": version,
        "title": "Family Money Meeting",
        "approval_record": {
            "status": "approved",
            "approved_by": "Founder",
            "scope": "Publisher handoff bridge test",
        },
        "files": [
            {"path": pdf_name, "role": "final_pdf"},
            {"path": metadata_name, "role": "metadata"},
        ],
        "package": {
            "schema": "qru.product-package.v1",
            "sha256": {
                name: hashlib.sha256(data).hexdigest()
                for name, data in files.items()
            },
            "handoff_ready": True,
        },
    }

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
        zf.writestr("manifest.json", _json_bytes(manifest))
    return out.getvalue()


@pytest.mark.asyncio
async def test_factory_v2_package_reaches_existing_auto_publish(monkeypatch):
    """Prove the Factory v2 contract can cross the existing Publisher auto-publish seam."""
    calls = []

    async def parse_then_stage(body, *, actor, trace_id):
        parsed = parse_factory_package(body, trace_id=trace_id)
        calls.append(("parsed", parsed.product_key, parsed.metadata["price"]))
        return {
            "ok": True,
            "idempotent_replay": False,
            "trace_id": trace_id,
            "product_id": "pkg-family-money-meeting",
            "product_key": parsed.product_key,
            "version": parsed.version,
            "archive_sha256": parsed.archive_sha256,
            "status": "Ready for Publisher",
            "published": False,
        }

    async def fake_publish(product_id, actor="Founder"):
        calls.append(("publish", product_id, actor))
        return {
            "ok": True,
            "product_id": product_id,
            "status": "Published",
            "store_url": "/store",
        }

    monkeypatch.setattr(route, "new_trace_id", lambda: "trace-v2-bridge")
    monkeypatch.setattr(route, "ingest_factory_package", parse_then_stage)
    monkeypatch.setattr(route, "publish_to_store", fake_publish)

    upload = FakeUpload(make_factory_v2_package())
    result = await route.ingest_package(upload, {"name": "Founder"})

    assert result["ok"] is True
    assert result["product_key"] == "family-money-meeting"
    assert result["status"] == "Published"
    assert result["published"] is True
    assert result["auto_published"] is True
    assert result["store_url"] == "/store"
    assert calls == [
        ("parsed", "family-money-meeting", {"amount_cents": 900, "currency": "USD"}),
        ("publish", "pkg-family-money-meeting", "Founder"),
    ]
    assert upload.closed is True
