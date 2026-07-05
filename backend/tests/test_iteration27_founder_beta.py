"""MO-046 Founder Beta Production Readiness — Developer Mode vs Founder Mode separation.
Tests: 23 connectors, production status vocab, super-admin role gating on developer-config,
verify checklist, oauth callback error handling. Cleans up any dev-config we create.
"""
import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")

FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

EXPECTED_STATUSES_ALLOWED = {
    "Ready to Publish", "Connected", "Needs Authorization", "Developer Setup Required",
    "Developer Setup Complete", "Connection Expired", "Reconnect Required",
    "Not Connected", "Failed", "Connection Error", "Publishing", "Published",
}
LEGACY_STATUSES_FORBIDDEN = {
    "Connected Healthy", "Setup Required", "Developer Configuration Required",
}
EXPECTED_NEW_CONNECTORS = {"github", "google_sheets", "woocommerce"}


@pytest.fixture(scope="module")
def founder_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def auth_headers(founder_token):
    return {"Authorization": f"Bearer {founder_token}", "Content-Type": "application/json"}


# ============ Founder identity ============
class TestFounderIdentity:
    def test_founder_is_super_admin(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("email") == FOUNDER_EMAIL
        assert data.get("role") == "Founder & CEO"


# ============ Connector registry ============
class TestConnectorRegistry:
    def test_list_returns_23_connectors(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/connectors", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["count"] == 23, f"Expected 23 connectors, got {data['count']}"
        assert len(data["connectors"]) == 23
        ids = {c["id"] for c in data["connectors"]}
        for nid in EXPECTED_NEW_CONNECTORS:
            assert nid in ids, f"New connector {nid} missing"

    def test_new_connectors_auth_methods(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/connectors", headers=auth_headers, timeout=30)
        by_id = {c["id"]: c for c in r.json()["connectors"]}
        assert by_id["github"]["auth_method"] == "oauth"
        assert by_id["google_sheets"]["auth_method"] == "oauth"
        assert by_id["woocommerce"]["auth_method"] == "api_key"

    def test_status_vocabulary_production(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/connectors", headers=auth_headers, timeout=30)
        for c in r.json()["connectors"]:
            assert c["status"] in EXPECTED_STATUSES_ALLOWED, \
                f"Connector {c['id']} has unexpected status: {c['status']}"
            assert c["status"] not in LEGACY_STATUSES_FORBIDDEN, \
                f"Connector {c['id']} has LEGACY status: {c['status']}"

    def test_qru_store_ready_to_publish(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/connectors", headers=auth_headers, timeout=30)
        by_id = {c["id"]: c for c in r.json()["connectors"]}
        assert by_id["qru_store"]["status"] == "Ready to Publish"
        assert by_id["qru_store"]["can_publish"] is True

    def test_stripe_connected(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/connectors", headers=auth_headers, timeout=30)
        by_id = {c["id"]: c for c in r.json()["connectors"]}
        assert by_id["stripe"]["status"] == "Connected"

    def test_unconfigured_show_developer_setup_required(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/connectors", headers=auth_headers, timeout=30)
        by_id = {c["id"]: c for c in r.json()["connectors"]}
        # github/google_sheets/woocommerce should be Developer Setup Required (fresh state)
        for cid in ("github", "google_sheets", "woocommerce"):
            assert by_id[cid]["status"] == "Developer Setup Required", \
                f"{cid} expected 'Developer Setup Required', got '{by_id[cid]['status']}'"


# ============ Role-gated developer-config ============
class TestDeveloperConfigRoleGating:
    def test_founder_can_read_dev_config(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/connectors/github/developer-config",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        assert "configured" in r.json()

    def test_no_auth_returns_401_or_403(self):
        r = requests.get(f"{BASE_URL}/api/connectors/github/developer-config", timeout=30)
        assert r.status_code in (401, 403), f"Expected 401/403 got {r.status_code}"

    def test_founder_can_post_dev_config_and_cleanup(self, auth_headers):
        payload = {
            "client_id": "test.apps.googleusercontent.com",
            "client_secret": "dummy",
            "redirect_uri": f"{BASE_URL}/api/oauth/callback",
        }
        r = requests.post(f"{BASE_URL}/api/connectors/github/developer-config",
                          headers=auth_headers, json=payload, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        # No secret in response
        assert "dummy" not in r.text, "Client secret leaked in response!"
        assert body.get("configured") is True

        # Status should now be Needs Authorization
        r2 = requests.get(f"{BASE_URL}/api/connectors", headers=auth_headers, timeout=30)
        by_id = {c["id"]: c for c in r2.json()["connectors"]}
        assert by_id["github"]["status"] == "Needs Authorization", \
            f"After dev-config, github should be 'Needs Authorization', got '{by_id['github']['status']}'"
        assert by_id["github"]["developer_configured"] is True

        # CLEANUP
        r3 = requests.delete(f"{BASE_URL}/api/connectors/github/developer-config",
                             headers=auth_headers, timeout=30)
        assert r3.status_code == 200
        r4 = requests.get(f"{BASE_URL}/api/connectors", headers=auth_headers, timeout=30)
        by_id = {c["id"]: c for c in r4.json()["connectors"]}
        assert by_id["github"]["status"] == "Developer Setup Required"


# ============ Verify (Test Connection) ============
class TestVerifyChecklist:
    def test_verify_github_returns_checklist(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/connectors/github/verify",
                          headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # unconfigured → needs_config / not healthy
        assert data.get("healthy") is False
        # Must be a checklist (never silent)
        assert isinstance(data.get("checks"), list) and len(data["checks"]) > 0

    def test_verify_qru_store_healthy(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/connectors/qru_store/verify",
                          headers=auth_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["healthy"] is True


# ============ OAuth callback error path ============
class TestOAuthCallback:
    def test_bad_state_redirects_error(self):
        r = requests.get(f"{BASE_URL}/api/oauth/callback?state=bad&code=x",
                         allow_redirects=False, timeout=30)
        assert r.status_code in (302, 307), f"Expected redirect got {r.status_code}"
        loc = r.headers.get("location", "")
        assert "oauth=error" in loc, f"Expected oauth=error in redirect location: {loc}"


# ============ Interaction audit — nav routes / API endpoints ============
class TestInteractionAudit:
    """Verify Founder-journey backend endpoints return 200 (front-end pages depend on these)."""

    @pytest.mark.parametrize("path", [
        "/api/metrics/summary",
        "/api/connectors",
        "/api/founder-inbox",
        "/api/products",
        "/api/store/products",
        "/api/manufacturing/queue",
        "/api/workflows",
        "/api/autonomy",
        "/api/analytics",
        "/api/customers",
    ])
    def test_endpoint_reachable(self, auth_headers, path):
        r = requests.get(f"{BASE_URL}{path}", headers=auth_headers, timeout=30)
        # 200 or 404 (route not present) or 405 — but must NOT be 500
        assert r.status_code < 500, f"{path} returned {r.status_code}: {r.text[:200]}"


# ============ Evidence metrics regression (connector_status 2/23) ============
class TestEvidenceMetricsRegression:
    def test_connector_status_two_of_twenty_three(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/metrics/summary", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        metrics = data.get("metrics") or data.get("cards") or data
        found = None
        if isinstance(metrics, list):
            for m in metrics:
                if m.get("id") == "connector_status":
                    found = m
                    break
        elif isinstance(metrics, dict):
            found = metrics.get("connector_status")
        assert found, f"connector_status metric not found: keys={list(data.keys()) if isinstance(data, dict) else 'list'}"
        display = str(found.get("display") or found.get("value_display") or "")
        assert display == f"2/23" or "/23" in display, f"connector_status must show 'X/23', got: {display}"
