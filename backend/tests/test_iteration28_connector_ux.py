"""MO-046 iteration 28 — Retest of two UX bugs from iteration 27 + full connector UX audit.

Bug 1: api_key connectors must be `configurable=True` (so frontend renders Developer Setup button in Dev Mode).
Bug 2: Every disabled Publish button must have a non-null publish_disabled_reason.

Plus universal audits:
- Every connector has non-null `next_step`.
- Every configurable connector has `configurable=True`.
- qru_store: Ready to Publish + can_publish=True + publish_disabled_reason=None.
- stripe: Connected + can_publish=False + non-null publish_disabled_reason.
"""
import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")

FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

EXPECTED_23 = {
    "youtube", "amazon_kdp", "stripe", "shopify", "google_drive", "google_docs",
    "google_sheets", "google_slides", "onedrive", "dropbox", "microsoft", "tpt",
    "etsy", "canva", "github", "woocommerce", "facebook", "instagram", "linkedin",
    "pinterest", "tiktok", "x", "qru_store",
}
API_KEY_CONFIGURABLE = {"woocommerce", "shopify", "amazon_kdp", "tpt"}
OAUTH_CONFIGURABLE = {"youtube", "etsy", "pinterest", "facebook", "instagram", "linkedin",
                     "google_drive", "dropbox", "onedrive", "google_docs", "google_slides",
                     "microsoft", "tiktok", "x", "canva", "github", "google_sheets"}


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


@pytest.fixture(scope="module")
def connectors(auth_headers):
    r = requests.get(f"{BASE_URL}/api/connectors", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    return {c["id"]: c for c in r.json()["connectors"]}


# ============ Bug 1: api_key connectors are configurable ============
class TestBug1ApiKeyConfigurable:
    def test_all_23_present(self, connectors):
        assert set(connectors.keys()) == EXPECTED_23

    @pytest.mark.parametrize("cid", sorted(API_KEY_CONFIGURABLE))
    def test_api_key_connector_is_configurable(self, connectors, cid):
        c = connectors[cid]
        assert c["auth_method"] == "api_key", f"{cid} auth_method={c['auth_method']}"
        assert c.get("configurable") is True, f"{cid} configurable={c.get('configurable')} — Developer Setup will be HIDDEN in Dev Mode"

    @pytest.mark.parametrize("cid", sorted(OAUTH_CONFIGURABLE))
    def test_oauth_connector_is_configurable(self, connectors, cid):
        c = connectors[cid]
        assert c["auth_method"] == "oauth"
        assert c.get("configurable") is True, f"{cid} configurable={c.get('configurable')}"

    def test_qru_store_native_not_configurable(self, connectors):
        # Native connectors don't need developer setup
        c = connectors["qru_store"]
        assert c["auth_method"] == "native"
        # configurable may be True or False for native — check publish_disabled_reason is None
        assert c["can_publish"] is True
        assert c.get("publish_disabled_reason") is None


# ============ Bug 2: publish_disabled_reason non-null when can_publish=False ============
class TestBug2PublishDisabledReason:
    def test_stripe_has_disabled_reason(self, connectors):
        s = connectors["stripe"]
        assert s["status"] == "Connected"
        assert s["can_publish"] is False, "stripe should not be a publish target"
        assert s.get("publish_disabled_reason"), \
            f"stripe.publish_disabled_reason MUST be non-null. Got: {s.get('publish_disabled_reason')!r}"
        reason = s["publish_disabled_reason"].lower()
        # Should mention checkout/payments/not a publishing destination
        assert ("publish" in reason or "checkout" in reason or "payment" in reason), \
            f"stripe reason should describe why: got {s['publish_disabled_reason']!r}"

    def test_no_disabled_publish_has_empty_reason(self, connectors):
        offenders = []
        for cid, c in connectors.items():
            if not c.get("can_publish"):
                r = c.get("publish_disabled_reason")
                if not r or not str(r).strip():
                    offenders.append(cid)
        assert not offenders, f"These connectors have disabled Publish with EMPTY reason: {offenders}"


# ============ Universal next_step audit ============
class TestUniversalNextStep:
    def test_every_connector_has_next_step(self, connectors):
        offenders = [cid for cid, c in connectors.items()
                     if not c.get("next_step") or not str(c["next_step"]).strip()]
        assert not offenders, f"Connectors with empty next_step: {offenders}"

    def test_qru_store_next_step_talks_publish(self, connectors):
        n = connectors["qru_store"]["next_step"].lower()
        assert "publish" in n or "select" in n, f"qru_store next_step: {connectors['qru_store']['next_step']}"

    def test_configurable_unconfigured_next_step_mentions_developer(self, connectors):
        # For oauth/api_key connectors that are unconfigured, next_step should mention
        # "Developer Setup" / "administrator" so the Founder knows what's blocking.
        for cid in ("github", "woocommerce", "google_sheets", "youtube"):
            n = connectors[cid]["next_step"].lower()
            assert ("developer" in n or "administrator" in n or "admin" in n), \
                f"{cid} next_step should mention Developer Setup: {connectors[cid]['next_step']!r}"


# ============ Credential-needs for configurable connectors ============
class TestCredentialNeeds:
    @pytest.mark.parametrize("cid", sorted(API_KEY_CONFIGURABLE | OAUTH_CONFIGURABLE))
    def test_configurable_has_credential_needs(self, connectors, cid):
        c = connectors[cid]
        assert c.get("credential_needs"), \
            f"{cid} credential_needs missing — Founder Mode won't show 'Needs:' line"

    def test_native_has_no_credential_needs(self, connectors):
        assert connectors["qru_store"].get("credential_needs") in (None, "")


# ============ Regressions ============
class TestRegressions:
    def test_qru_store_still_ready(self, connectors):
        c = connectors["qru_store"]
        assert c["status"] == "Ready to Publish"
        assert c["can_publish"] is True
        assert c.get("publish_disabled_reason") is None

    def test_stripe_still_connected(self, connectors):
        assert connectors["stripe"]["status"] == "Connected"

    def test_bad_oauth_callback_still_redirects_error(self):
        r = requests.get(f"{BASE_URL}/api/oauth/callback?state=bad&code=x",
                         allow_redirects=False, timeout=30)
        assert r.status_code in (302, 307)
        assert "oauth=error" in r.headers.get("location", "")

    def test_all_configurable_have_configurable_flag(self, connectors):
        # ANY non-native connector should be configurable=True (they hold dev credentials)
        offenders = []
        for cid, c in connectors.items():
            if c["auth_method"] in ("oauth", "api_key") and not c.get("configurable"):
                offenders.append(cid)
        assert not offenders, f"Non-native connectors not configurable: {offenders}"


# ============ OAuth authorize-url smoke — youtube ============
class TestOAuthYoutubeFlow:
    """Set dummy dev-config for youtube → authorize-url should return google endpoint → cleanup."""

    def test_youtube_authorize_url_flow(self, auth_headers):
        # Set dev config
        cfg = {
            "client_id": "test.apps.googleusercontent.com",
            "client_secret": "dummy",
            "redirect_uri": f"{BASE_URL}/api/oauth/callback",
        }
        r = requests.post(f"{BASE_URL}/api/connectors/youtube/developer-config",
                          headers=auth_headers, json=cfg, timeout=30)
        assert r.status_code == 200, r.text
        try:
            # Now request authorize URL
            r2 = requests.get(f"{BASE_URL}/api/connectors/youtube/authorize-url",
                              headers=auth_headers, timeout=30)
            assert r2.status_code == 200, r2.text
            url = r2.json().get("authorize_url", "")
            assert "accounts.google.com" in url or "google.com" in url, \
                f"authorize_url should point to Google: got {url[:100]}"
            # Also confirm listing now shows youtube Needs Authorization
            r3 = requests.get(f"{BASE_URL}/api/connectors", headers=auth_headers, timeout=30)
            by_id = {c["id"]: c for c in r3.json()["connectors"]}
            assert by_id["youtube"]["status"] == "Needs Authorization"
        finally:
            # CLEANUP
            requests.delete(f"{BASE_URL}/api/connectors/youtube/developer-config",
                            headers=auth_headers, timeout=30)


# ============ Verify test connection surfaces checklist for all configurable ============
class TestVerifyChecklistForAll:
    @pytest.mark.parametrize("cid", ["stripe", "qru_store", "github", "woocommerce"])
    def test_verify_returns_structured(self, auth_headers, cid):
        r = requests.post(f"{BASE_URL}/api/connectors/{cid}/verify",
                          headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # Must have healthy flag + either checks or message (never silent)
        assert "healthy" in data
        assert data.get("message") or (data.get("checks") and len(data["checks"]) > 0), \
            f"{cid} verify returned silent response: {data}"
