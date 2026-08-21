import json

import pytest

import routers.package_intake as route


class FakeUpload:
    def __init__(self, body=b"package-bytes"):
        self.body = body
        self.closed = False

    async def read(self, _limit):
        return self.body

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_approved_ingest_auto_publishes(monkeypatch):
    calls = []

    async def fake_ingest(body, *, actor, trace_id):
        calls.append(("ingest", body, actor, trace_id))
        return {
            "ok": True,
            "idempotent_replay": False,
            "trace_id": trace_id,
            "product_id": "pkg-123",
            "product_key": "qru-test",
            "version": "1.0.0",
            "archive_sha256": "a" * 64,
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

    monkeypatch.setattr(route, "new_trace_id", lambda: "trace-auto")
    monkeypatch.setattr(route, "ingest_factory_package", fake_ingest)
    monkeypatch.setattr(route, "publish_to_store", fake_publish)

    upload = FakeUpload()
    result = await route.ingest_package(upload, {"name": "Founder"})

    assert result["ok"] is True
    assert result["status"] == "Published"
    assert result["published"] is True
    assert result["auto_published"] is True
    assert result["store_url"] == "/store"
    assert calls == [
        ("ingest", b"package-bytes", "Founder", "trace-auto"),
        ("publish", "pkg-123", "Founder"),
    ]
    assert upload.closed is True


@pytest.mark.asyncio
async def test_exact_replay_does_not_create_a_second_product_and_still_finishes_published(monkeypatch):
    async def fake_ingest(body, *, actor, trace_id):
        return {
            "ok": True,
            "idempotent_replay": True,
            "trace_id": trace_id,
            "product_id": "pkg-existing",
            "product_key": "qru-test",
            "version": "1.0.0",
            "archive_sha256": "b" * 64,
            "status": "Ready for Publisher",
            "published": False,
        }

    async def fake_publish(product_id, actor="Founder"):
        assert product_id == "pkg-existing"
        return {"ok": True, "status": "Published", "store_url": "/store"}

    monkeypatch.setattr(route, "new_trace_id", lambda: "trace-replay")
    monkeypatch.setattr(route, "ingest_factory_package", fake_ingest)
    monkeypatch.setattr(route, "publish_to_store", fake_publish)

    result = await route.ingest_package(FakeUpload(), {"name": "Founder"})
    assert result["idempotent_replay"] is True
    assert result["status"] == "Published"
    assert result["published"] is True


@pytest.mark.asyncio
async def test_publish_failure_is_reported_instead_of_claiming_success(monkeypatch):
    async def fake_ingest(body, *, actor, trace_id):
        return {
            "ok": True,
            "idempotent_replay": False,
            "trace_id": trace_id,
            "product_id": "pkg-456",
            "product_key": "qru-test",
            "version": "1.0.0",
            "archive_sha256": "c" * 64,
        }

    async def fake_publish(product_id, actor="Founder"):
        return {"ok": False, "message": "Customer deliverable is missing."}

    monkeypatch.setattr(route, "new_trace_id", lambda: "trace-fail")
    monkeypatch.setattr(route, "ingest_factory_package", fake_ingest)
    monkeypatch.setattr(route, "publish_to_store", fake_publish)

    response = await route.ingest_package(FakeUpload(), {"name": "Founder"})
    body = json.loads(response.body)

    assert response.status_code == 502
    assert body["ok"] is False
    assert body["code"] == "AUTO_PUBLISH_FAILED"
    assert body["stage"] == "store_publish"
    assert body["product_id"] == "pkg-456"
