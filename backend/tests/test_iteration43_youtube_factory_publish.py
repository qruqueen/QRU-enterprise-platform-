"""Iteration 43 — QRU YouTube Publisher™ Factory-asset publish path (MO-006 continuity).
Validates: factory-assets listing shape, draft-preview publish guard (400 pre-upload),
missing-asset guard (404), no-source guard (400), regression: /status connected + /publications
listing. IMPORTANT: does NOT execute a real publish (channel 'Quest Understand' is live).
"""
import os
import pytest
import requests

def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    envp = "/app/frontend/.env"
    if os.path.exists(envp):
        for line in open(envp):
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not configured")


BASE_URL = _load_backend_url()
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="module")
def founder_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD},
                      timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(founder_token):
    return {"Authorization": f"Bearer {founder_token}", "Content-Type": "application/json"}


# --- Factory Assets listing --------------------------------------------------

class TestFactoryAssetsListing:
    def test_factory_assets_shape(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/youtube/factory-assets",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "assets" in data and "count" in data
        assert isinstance(data["assets"], list)
        assert data["count"] == len(data["assets"])
        # Validate required fields per asset when at least one exists
        if data["assets"]:
            required = {"qru_asset_id", "title", "duration_seconds", "width", "height",
                        "production_status", "distribution_ready", "gold_master_certified",
                        "is_draft_preview", "file_available"}
            for a in data["assets"]:
                missing = required - set(a.keys())
                assert not missing, f"Missing fields on asset: {missing}"
                assert isinstance(a["distribution_ready"], bool)
                assert isinstance(a["gold_master_certified"], bool)
                assert isinstance(a["is_draft_preview"], bool)
                assert isinstance(a["file_available"], bool)

    def test_factory_assets_no_objectid_leak(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/youtube/factory-assets",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200
        assert '"_id"' not in r.text  # Mongo ObjectId key must NOT be present


# --- Publish guards (all return BEFORE any upload — safe to test) -----------

class TestPublishGuards:
    def test_no_source_guard(self, auth_headers):
        """Neither factory_asset_id nor video_upload_id → 400."""
        r = requests.post(f"{BASE_URL}/api/youtube/publish",
                          headers=auth_headers, json={}, timeout=30)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
        detail = (r.json().get("detail") or "").lower()
        assert "factory asset" in detail or "upload" in detail, r.text

    def test_missing_asset_guard(self, auth_headers):
        """Non-existent factory asset id → 404."""
        r = requests.post(f"{BASE_URL}/api/youtube/publish",
                          headers=auth_headers,
                          json={"factory_asset_id": "QRU-SHOWCASE-DOESNOTEXIST"},
                          timeout=30)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"
        assert "Factory asset not found" in (r.json().get("detail") or ""), r.text

    def test_draft_preview_guard(self, auth_headers):
        """A draft-preview asset must be rejected with 400 pre-upload."""
        listing = requests.get(f"{BASE_URL}/api/youtube/factory-assets",
                               headers=auth_headers, timeout=30).json()
        drafts = [a for a in listing.get("assets", []) if a.get("is_draft_preview")]
        if not drafts:
            pytest.skip("No draft-preview factory asset present to test draft guard.")
        draft_id = drafts[0]["qru_asset_id"]
        r = requests.post(f"{BASE_URL}/api/youtube/publish",
                          headers=auth_headers,
                          json={"factory_asset_id": draft_id},
                          timeout=30)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
        detail = r.json().get("detail") or ""
        assert detail == "Draft previews cannot be published. Approve & certify the final asset first.", (
            f"Unexpected detail: {detail!r}"
        )


# --- Regressions -------------------------------------------------------------

class TestRegression:
    def test_status_connected(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/youtube/status",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("connected") is True, f"Expected connected=true, got {data}"
        assert data.get("account"), "Expected an account name"

    def test_publications_list(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/youtube/publications",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "publications" in data
        assert isinstance(data["publications"], list)
        # publication docs must not leak Mongo _id (allow "video_id"/"id" keys, deny "_id" JSON key)
        assert '"_id"' not in r.text


# --- Factory-manufactured assets should exist and expose file_available ------

class TestFactoryAssetsRealContent:
    def test_at_least_one_qru_production_asset(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/youtube/factory-assets",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200
        assets = r.json().get("assets", [])
        # Not required — just informational — but flag if there are NO factory assets at all.
        if not assets:
            pytest.skip("No qru_production factory assets present yet (informational).")
        # Confirm at least one file_available OR at least one draft (either proves the
        # provider filter works and the shape is populated by real docs).
        assert any(a["file_available"] or a["is_draft_preview"] for a in assets), (
            "Expected at least one factory asset with a real file or a draft flag."
        )
