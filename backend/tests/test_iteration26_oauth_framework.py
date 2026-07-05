"""MO-046 Universal OAuth Framework™ — end-to-end backend tests.

Covers:
- GET /api/connectors returns 20 connectors with honest statuses (Developer Configuration Required
  for OAuth, Connected Healthy for native, oauth_supported=False for amazon_kdp/tpt).
- Developer config lifecycle: POST/GET/DELETE never expose secret; status transitions.
- Authorize-URL correctness: Google URL contains required params; PKCE providers add code_challenge.
- Verify checklist: needs_config → needs_auth → checks list human-readable.
- OAuth callback with bad state → 307 redirect to /connectors?oauth=error (no crash).
- Disconnect + delete developer-config revert to Developer Configuration Required (clean state).
"""
import os
from urllib.parse import urlparse, parse_qs

import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")

FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

OAUTH_IDS = [
    "youtube", "etsy", "linkedin", "dropbox", "x", "tiktok", "canva",
    "google_drive", "google_docs", "google_slides", "microsoft", "onedrive",
    "facebook", "instagram", "pinterest",
]
PKCE_IDS = {"etsy", "x", "tiktok", "canva"}
NON_OAUTH_HONEST = {"amazon_kdp", "tpt"}


@pytest.fixture(scope="module")
def founder_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"Founder login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("token") or r.json().get("access_token")


@pytest.fixture(scope="module")
def client(founder_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {founder_token}", "Content-Type": "application/json"})
    # Pre-test cleanup: ensure a clean slate for our OAuth targets
    for pid in ("youtube", "etsy"):
        try:
            s.post(f"{BASE_URL}/api/connectors/{pid}/disconnect", timeout=10)
            s.delete(f"{BASE_URL}/api/connectors/{pid}/developer-config", timeout=10)
        except Exception:
            pass
    return s


# ---------------- baseline listing ---------------- #

class TestConnectorList:
    def test_list_returns_20(self, client):
        r = client.get(f"{BASE_URL}/api/connectors", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "connectors" in data
        assert data["count"] == 20, f"Expected 20 connectors, got {data['count']}"
        assert len(data["connectors"]) == 20

    def test_native_and_stripe_statuses(self, client):
        r = client.get(f"{BASE_URL}/api/connectors", timeout=20)
        by_id = {c["id"]: c for c in r.json()["connectors"]}
        assert by_id["qru_store"]["status"] == "Connected Healthy"
        # Stripe is api_key, should be either Connected Healthy/Connected/Setup Required
        assert by_id["stripe"]["status"] in ("Connected Healthy", "Connected", "Setup Required")

    def test_honest_non_oauth_platforms(self, client):
        r = client.get(f"{BASE_URL}/api/connectors", timeout=20)
        by_id = {c["id"]: c for c in r.json()["connectors"]}
        for pid in NON_OAUTH_HONEST:
            c = by_id[pid]
            # oauth_supported must be False OR auth_method must be api_key (honest)
            assert (c.get("oauth_supported") is False) or (c["auth_method"] == "api_key"), \
                f"{pid} must be honest: oauth_supported=False OR auth_method=api_key, got {c}"


# ---------------- developer config lifecycle ---------------- #

DUMMY_CID = "test-client-id.apps.googleusercontent.com"
DUMMY_SEC = "GOCSPX-dummy-secret-value"


@pytest.fixture(scope="module")
def redirect_uri():
    return f"{BASE_URL}/api/oauth/callback"


class TestDeveloperConfig:
    def test_before_config_status_is_devconfig(self, client):
        r = client.get(f"{BASE_URL}/api/connectors", timeout=20)
        by_id = {c["id"]: c for c in r.json()["connectors"]}
        for pid in OAUTH_IDS:
            assert by_id[pid]["status"] == "Developer Configuration Required", \
                f"{pid} should start at Developer Configuration Required, got {by_id[pid]['status']}"
            assert by_id[pid]["developer_configured"] in (False, None)

    def test_authorize_url_400_before_config(self, client):
        # youtube should be in devconfig state
        r = client.get(f"{BASE_URL}/api/connectors/youtube/authorize-url", timeout=20)
        assert r.status_code == 400
        assert "Developer Configuration Required" in r.json().get("detail", "")

    def test_verify_before_config_returns_needs_config(self, client):
        r = client.post(f"{BASE_URL}/api/connectors/youtube/verify", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data.get("overall") == "needs_config"
        assert isinstance(data.get("checks"), list) and len(data["checks"]) >= 1

    def test_post_dev_config_never_returns_secret(self, client, redirect_uri):
        r = client.post(
            f"{BASE_URL}/api/connectors/youtube/developer-config",
            json={"client_id": DUMMY_CID, "client_secret": DUMMY_SEC, "redirect_uri": redirect_uri},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["configured"] is True
        assert "client_id_masked" in body
        assert body["has_secret"] is True
        raw = r.text
        # secret must never appear anywhere in the response body
        assert DUMMY_SEC not in raw, "Client secret leaked in POST response!"
        # full client_id must not appear raw (masked)
        assert body["client_id_masked"] != DUMMY_CID

    def test_get_dev_config_never_returns_secret(self, client):
        r = client.get(f"{BASE_URL}/api/connectors/youtube/developer-config", timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert body["configured"] is True
        assert body["has_secret"] is True
        assert DUMMY_SEC not in r.text, "Client secret leaked in GET response!"
        assert "secret" not in body or body.get("secret") in (None, "")

    def test_status_after_config_is_needs_auth(self, client):
        r = client.get(f"{BASE_URL}/api/connectors", timeout=20)
        by_id = {c["id"]: c for c in r.json()["connectors"]}
        yt = by_id["youtube"]
        assert yt["status"] == "Needs Authorization", f"Expected Needs Authorization, got {yt['status']}"
        assert yt["developer_configured"] is True
        assert yt["authorized"] in (False, None)


# ---------------- authorize URL ---------------- #

class TestAuthorizeUrl:
    def test_youtube_authorize_url_correct(self, client):
        r = client.get(
            f"{BASE_URL}/api/connectors/youtube/authorize-url",
            params={"frontend_origin": "https://example.com"},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        url = r.json()["authorize_url"]
        parsed = urlparse(url)
        assert parsed.netloc == "accounts.google.com"
        q = parse_qs(parsed.query)
        assert q.get("client_id") == [DUMMY_CID]
        assert q.get("response_type") == ["code"]
        assert q.get("redirect_uri") and q["redirect_uri"][0].endswith("/api/oauth/callback")
        assert q.get("state") and len(q["state"][0]) > 6
        assert q.get("access_type") == ["offline"]
        assert "scope" in q and q["scope"][0]

    def test_pkce_provider_authorize_url_has_code_challenge(self, client, redirect_uri):
        # configure etsy so we can request authorize URL
        r0 = client.post(
            f"{BASE_URL}/api/connectors/etsy/developer-config",
            json={"client_id": "etsy-dummy-cid", "client_secret": "etsy-dummy-secret",
                  "redirect_uri": redirect_uri},
            timeout=20,
        )
        assert r0.status_code == 200

        r = client.get(
            f"{BASE_URL}/api/connectors/etsy/authorize-url",
            params={"frontend_origin": "https://example.com"},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        url = r.json()["authorize_url"]
        q = parse_qs(urlparse(url).query)
        assert "code_challenge" in q and q["code_challenge"][0]
        assert q.get("code_challenge_method") == ["S256"]


# ---------------- verify after config ---------------- #

class TestVerifyAfterConfig:
    def test_verify_after_config_needs_auth(self, client):
        r = client.post(f"{BASE_URL}/api/connectors/youtube/verify", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data["overall"] == "needs_auth"
        # Ensure the auth check is human-readable
        text = " ".join(c.get("detail", "") + c.get("name", "") for c in data["checks"]).lower()
        assert "not authorized" in text or "authorization" in text
        assert any(c["name"].lower().startswith("authentication") for c in data["checks"])


# ---------------- oauth callback ---------------- #

class TestOAuthCallback:
    def test_callback_bad_state_redirects_no_crash(self):
        # No auth (public endpoint), no auto-follow
        r = requests.get(
            f"{BASE_URL}/api/oauth/callback",
            params={"state": "definitely-not-a-valid-state", "code": "xyz"},
            allow_redirects=False,
            timeout=20,
        )
        assert r.status_code in (302, 307), f"Expected redirect, got {r.status_code}: {r.text[:200]}"
        loc = r.headers.get("location", "")
        assert "/connectors?" in loc
        assert "oauth=error" in loc


# ---------------- disconnect + cleanup ---------------- #

class TestDisconnectAndCleanup:
    def test_disconnect_youtube(self, client):
        r = client.post(f"{BASE_URL}/api/connectors/youtube/disconnect", timeout=20)
        assert r.status_code == 200

    def test_delete_dev_config_youtube_reverts_status(self, client):
        r = client.delete(f"{BASE_URL}/api/connectors/youtube/developer-config", timeout=20)
        assert r.status_code == 200
        r2 = client.get(f"{BASE_URL}/api/connectors", timeout=20)
        by_id = {c["id"]: c for c in r2.json()["connectors"]}
        assert by_id["youtube"]["status"] == "Developer Configuration Required"

    def test_delete_dev_config_etsy_cleanup(self, client):
        r = client.delete(f"{BASE_URL}/api/connectors/etsy/developer-config", timeout=20)
        assert r.status_code == 200
        r2 = client.get(f"{BASE_URL}/api/connectors", timeout=20)
        by_id = {c["id"]: c for c in r2.json()["connectors"]}
        assert by_id["etsy"]["status"] == "Developer Configuration Required"
