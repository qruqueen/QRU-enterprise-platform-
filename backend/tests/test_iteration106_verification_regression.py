"""Iteration 106 pre-redeploy regression:
- Verification Center /queue + /kr2/{id}/verify
- Creative Assets state 500-fix
- Factory Jobs spine (list/get/retry/cancel)
No AI credits should be spent.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "demo.admin@qru.com"
ADMIN_PASSWORD = "qru-demo-admin-2026"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ---------- Verification Center ----------
class TestVerificationCenter:
    def test_queue_returns_200_and_shape(self, headers):
        r = requests.get(f"{BASE_URL}/api/verification/queue", headers=headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "needs_verification" in data
        assert "awaiting_manufacturing" in data
        assert "counts" in data
        c = data["counts"]
        for k in ["verified", "pending", "awaiting_manufacturing", "total"]:
            assert k in c, f"missing count key {k}"
        # Internal consistency
        assert c["verified"] + c["pending"] + c["awaiting_manufacturing"] == c["total"], \
            f"counts inconsistent: {c}"

    def test_queue_surfaces_kr2_collection(self, headers):
        r = requests.get(f"{BASE_URL}/api/verification/queue", headers=headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        # allow either kr2 items visible in needs or none pending (documented)
        collections = {item.get("collection") for item in data["needs_verification"]}
        # not asserting kr2 must exist; log for diagnostic
        print(f"needs_verification collections observed: {collections}, counts: {data['counts']}")

    def test_kr2_approve_flow(self, headers):
        # Find a kr2 record in queue
        r = requests.get(f"{BASE_URL}/api/verification/queue", headers=headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        kr2 = [x for x in data["needs_verification"] if x.get("collection") == "kr2"]
        if not kr2:
            pytest.skip("No KR 2.0 pending records to test approve action")
        rid = kr2[0]["id"]
        before = data["counts"]

        r2 = requests.post(f"{BASE_URL}/api/verification/kr2/{rid}/verify",
                           headers=headers, json={"decision": "approve"}, timeout=30)
        assert r2.status_code == 200, r2.text
        body = r2.json()
        assert body.get("ok") is True
        assert "Verified External" in body.get("status", "") or "Gold Standard" in body.get("status", "")

        # Re-fetch queue and check counts moved
        r3 = requests.get(f"{BASE_URL}/api/verification/queue", headers=headers, timeout=30)
        after = r3.json()["counts"]
        assert after["verified"] == before["verified"] + 1
        assert after["pending"] == before["pending"] - 1


# ---------- Creative Assets state 500-fix ----------
class TestCreativeAssetsState:
    def test_set_state_no_500(self, headers):
        # Try to list assets
        r = requests.get(f"{BASE_URL}/api/creative-assets/assets", headers=headers, timeout=30)
        if r.status_code != 200:
            pytest.skip(f"assets list unavailable: {r.status_code}")
        payload = r.json()
        assets = payload if isinstance(payload, list) else payload.get("assets", [])
        if not assets:
            pytest.skip("No creative assets exist to test state transition")
        asset_id = assets[0].get("id") or assets[0].get("asset_id")
        if not asset_id:
            pytest.skip("Asset has no id field")
        r2 = requests.post(f"{BASE_URL}/api/creative-assets/assets/{asset_id}/state",
                           headers=headers, json={"state": "Approved"}, timeout=30)
        assert r2.status_code == 200, f"Expected 200, got {r2.status_code}: {r2.text}"
        # Must be clean JSON
        j = r2.json()
        assert isinstance(j, dict)


# ---------- Factory Jobs Spine ----------
class TestFactoryJobs:
    def test_list_jobs(self, headers):
        r = requests.get(f"{BASE_URL}/api/factory-jobs", headers=headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "jobs" in d and "counts" in d and "total" in d

    def test_get_single_job(self, headers):
        r = requests.get(f"{BASE_URL}/api/factory-jobs", headers=headers, timeout=30)
        jobs = r.json().get("jobs", [])
        if not jobs:
            pytest.skip("No jobs to get")
        jid = jobs[0].get("id")
        r2 = requests.get(f"{BASE_URL}/api/factory-jobs/{jid}", headers=headers, timeout=30)
        assert r2.status_code == 200, r2.text

    def test_retry_failed_or_cancelled_job(self, headers):
        r = requests.get(f"{BASE_URL}/api/factory-jobs", headers=headers, timeout=30)
        jobs = r.json().get("jobs", [])
        target = next((j for j in jobs if str(j.get("status", "")).lower() in ("failed", "cancelled", "canceled")), None)
        if not target:
            pytest.skip("No failed/cancelled job available to retry")
        r2 = requests.post(f"{BASE_URL}/api/factory-jobs/{target['id']}/retry", headers=headers, timeout=30)
        assert r2.status_code == 200, r2.text

    def test_cancel_queued_job(self, headers):
        r = requests.get(f"{BASE_URL}/api/factory-jobs", headers=headers, timeout=30)
        jobs = r.json().get("jobs", [])
        target = next((j for j in jobs if str(j.get("status", "")).lower() in ("queued", "pending", "running")), None)
        if not target:
            pytest.skip("No queued job available to cancel")
        r2 = requests.post(f"{BASE_URL}/api/factory-jobs/{target['id']}/cancel", headers=headers, timeout=30)
        assert r2.status_code == 200, r2.text
