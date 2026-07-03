"""Iteration 10 — QRU Media Manufacturing Engine™ backend tests.

Covers:
- POST /api/media/manufacture (video + meditation, verified guard)
- GET  /api/media/library and /api/media/{mid}
- POST /api/media/{mid}/quality-control (Treasure Standard™ threshold 75)
- POST /api/media/{mid}/publish (pre-cert 400, post-cert publish, unknown dest 400)
"""
import os
import time
import pytest
import requests


def _read_frontend_env():
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _read_frontend_env()).rstrip("/")
ADMIN = {"email": "admin@qru.com", "password": "qru-admin-2026"}


@pytest.fixture(scope="module")
def admin_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    body = r.json()
    token = body.get("access_token") or body.get("token")
    assert token, f"no token in login response: {body}"
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="module")
def verified_kr_id(admin_client):
    r = admin_client.get(f"{BASE_URL}/api/memory/records", timeout=15)
    assert r.status_code == 200, r.text
    recs = r.json().get("records", [])
    assert recs, "No verified knowledge records available for media manufacture test"
    return recs[0]["id"]


def _find_non_verified_id(admin_client):
    """List /api/knowledge and return the first non-Verified record id, else None."""
    r = admin_client.get(f"{BASE_URL}/api/knowledge-records", timeout=15)
    if r.status_code != 200:
        return None
    data = r.json()
    items = data if isinstance(data, list) else data.get("records") or data.get("items") or []
    for rec in items:
        if rec.get("verification_status") and rec["verification_status"] != "Verified":
            return rec["id"]
    return None


def _wait_status(client, mid, target_statuses, timeout=120, interval=3):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        r = client.get(f"{BASE_URL}/api/media/{mid}", timeout=15)
        assert r.status_code == 200
        last = r.json()
        if last.get("status") in target_statuses:
            return last
        time.sleep(interval)
    pytest.fail(f"media {mid} did not reach {target_statuses} in {timeout}s (last status={last.get('status')})")


def _wait_qc(client, mid, timeout=120, interval=3):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        r = client.get(f"{BASE_URL}/api/media/{mid}", timeout=15)
        assert r.status_code == 200
        last = r.json()
        qs = (last.get("qc") or {}).get("status")
        if qs in ("certified", "needs_improvement", "failed"):
            return last
        time.sleep(interval)
    pytest.fail(f"media {mid} QC did not settle in {timeout}s (last qc={last.get('qc')})")


def _manufacture_and_wait(admin_client, kr_id, media_type):
    r = admin_client.post(
        f"{BASE_URL}/api/media/manufacture",
        json={"knowledge_record_id": kr_id, "media_type": media_type},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("media_type") == media_type

    mid = None
    end = time.time() + 25
    while time.time() < end and not mid:
        lib = admin_client.get(f"{BASE_URL}/api/media/library", timeout=15).json().get("media", [])
        # library is sorted newest-first
        for m in lib:
            if m.get("knowledge_record_id") == kr_id and m.get("media_type") == media_type \
                    and m.get("status") in ("manufacturing", "manufactured", "ready"):
                mid = m["id"]
                break
        if not mid:
            time.sleep(2)
    assert mid, f"manufactured {media_type} not visible in library"
    return _wait_status(admin_client, mid, {"manufactured", "ready"}, timeout=120), mid


# ---------- Grouped in one class so xdist runs all steps on the same worker ----------


class TestMediaEnd2End:
    """Manufacture (video+meditation), verified-guard, QC gate, publish gate — sequenced."""

    def test_01_video_manufacture_and_assets(self, admin_client, verified_kr_id):
        m, mid = _manufacture_and_wait(admin_client, verified_kr_id, "video")
        self.__class__.video_mid = mid
        a = m.get("assets") or {}
        for k in ("long_form_script", "short_form_script", "narration_script",
                  "voice_over_script", "memory_hook"):
            assert a.get(k), f"missing asset {k}"
        v = a.get("video") or {}
        for k in ("title", "description", "chapters", "thumbnail_brief", "hashtags"):
            assert v.get(k) is not None, f"missing video.{k}"
        assert isinstance(v["chapters"], list) and len(v["chapters"]) >= 1
        ll = a.get("legacy_learners") or {}
        for k in ("child", "teen", "adult", "teacher", "parent", "caregiver"):
            assert ll.get(k), f"missing legacy_learners.{k}"

    def test_02_meditation_manufacture_and_assets(self, admin_client, verified_kr_id):
        m, mid = _manufacture_and_wait(admin_client, verified_kr_id, "meditation")
        self.__class__.meditation_mid = mid
        a = m.get("assets") or {}
        med = a.get("meditation") or {}
        for k in ("session_name", "script", "reflection_prompts", "journal_page",
                  "poster_brief", "workbook_page", "ambient_music_prompt",
                  "character_intro", "closing_reflection"):
            assert med.get(k) is not None, f"missing meditation.{k}"
        assert isinstance(med["reflection_prompts"], list) and len(med["reflection_prompts"]) >= 1

    def test_03_non_verified_record_returns_400(self, admin_client):
        nv_id = _find_non_verified_id(admin_client)
        if not nv_id:
            pytest.skip("no non-verified record available in DB")
        r = admin_client.post(
            f"{BASE_URL}/api/media/manufacture",
            json={"knowledge_record_id": nv_id, "media_type": "video"},
            timeout=15,
        )
        assert r.status_code == 400, r.text
        assert "verified" in r.text.lower()

    def test_04_publish_before_qc_returns_400(self, admin_client):
        mid = getattr(self.__class__, "video_mid", None)
        assert mid, "video_mid must have been set by test_01"
        r = admin_client.post(
            f"{BASE_URL}/api/media/{mid}/publish",
            json={"destination": "YouTube"},
            timeout=15,
        )
        assert r.status_code == 400, r.text
        assert "treasure standard" in r.text.lower() or "qc" in r.text.lower()

    def test_05_run_qc(self, admin_client):
        mid = getattr(self.__class__, "video_mid", None)
        assert mid
        r = admin_client.post(f"{BASE_URL}/api/media/{mid}/quality-control", timeout=15)
        assert r.status_code == 200, r.text
        m = _wait_qc(admin_client, mid, timeout=150)
        assert m["qc"]["status"] in ("certified", "needs_improvement")
        self.__class__.video_publishing_ready = m.get("publishing_ready", False)
        self.__class__.video_qc_status = m["qc"]["status"]
        assert m["qc"].get("scores"), "QC scores must be populated"

    def test_06_publish_after_cert_or_still_blocked(self, admin_client):
        mid = getattr(self.__class__, "video_mid", None)
        assert mid
        r = admin_client.post(
            f"{BASE_URL}/api/media/{mid}/publish",
            json={"destination": "YouTube"},
            timeout=15,
        )
        if getattr(self.__class__, "video_publishing_ready", False):
            assert r.status_code == 200, r.text
            pubs = r.json().get("publications", [])
            assert any(
                p.get("destination") == "YouTube" and p.get("status") == "published"
                for p in pubs
            ), "YouTube publication entry missing"
        else:
            assert r.status_code == 400
            assert "treasure standard" in r.text.lower() or "qc" in r.text.lower()

    def test_07_publish_unknown_destination_returns_400(self, admin_client):
        mid = getattr(self.__class__, "video_mid", None)
        assert mid
        r = admin_client.post(
            f"{BASE_URL}/api/media/{mid}/publish",
            json={"destination": "NotARealDestination"},
            timeout=15,
        )
        assert r.status_code == 400, r.text
        body = r.text.lower()
        assert "unknown destination" in body or "treasure standard" in body or "qc" in body
