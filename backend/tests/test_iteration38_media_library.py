"""Iteration 38 — MO-021 Stock Media Intelligence + MO-023 Audio foundation + Milestone 001.

Covers /api/media-library/* provider security, validate-before-save, live search,
Master Asset Vault, and end-to-end produce-proof pipeline.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

# --- fixtures ---
@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth(token):
    return {"Authorization": f"Bearer {token}"}


def _ensure_pixabay_active(auth, retries=5):
    """Some flows (POST /providers/{id}/test) can transiently demote pixabay when the
    upstream API times out. Re-test until CONNECTED before running search-dependent tests."""
    for _ in range(retries):
        r = requests.post(f"{BASE_URL}/api/media-library/providers/pixabay_video/test",
                          headers=auth, timeout=30)
        if r.status_code == 200 and r.json().get("test_code") == "CONNECTED":
            return True
        time.sleep(2)
    return False


# --- provider status & credential security ---
class TestProviderStatus:
    def test_providers_returns_ten(self, auth):
        r = requests.get(f"{BASE_URL}/api/media-library/providers", headers=auth, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "providers" in data
        assert len(data["providers"]) == 10

    def test_pexels_and_pixabay_status(self, auth):
        # Ensure pixabay is CONNECTED before this check (upstream Pixabay can be flaky and
        # a prior /test call may have transiently demoted the provider — see code review note).
        _ensure_pixabay_active(auth)
        r = requests.get(f"{BASE_URL}/api/media-library/providers", headers=auth, timeout=20)
        provs = {p["id"]: p for p in r.json()["providers"]}
        assert provs["pexels_video"]["status"] == "ACTIVE", provs["pexels_video"]
        assert provs["pexels_video"].get("env_provided") is True
        assert provs["pexels_video"].get("masked_key") is None
        assert provs["pixabay_video"]["status"] == "ACTIVE", provs["pixabay_video"]
        mk = provs["pixabay_video"].get("masked_key")
        assert mk and "•" in mk, f"Pixabay masked key missing/malformed: {mk}"

    def test_developer_setup_required_providers(self, auth):
        r = requests.get(f"{BASE_URL}/api/media-library/providers", headers=auth, timeout=20)
        provs = {p["id"]: p for p in r.json()["providers"]}
        assert provs["pixabay_music"]["status"] == "DEVELOPER_SETUP_REQUIRED"
        assert provs["freesound"]["status"] == "DEVELOPER_SETUP_REQUIRED"

    def test_tier2_prepared_not_activated(self, auth):
        r = requests.get(f"{BASE_URL}/api/media-library/providers", headers=auth, timeout=20)
        provs = {p["id"]: p for p in r.json()["providers"]}
        for pid in ("storyblocks", "adobe_stock", "shutterstock", "epidemic_sound", "artlist"):
            assert provs[pid]["status"] == "PREPARED_NOT_ACTIVATED", pid

    def test_no_full_key_ever_returned(self, auth):
        # response bytes must not contain any obvious long unmasked base64/hex-ish "key" field
        r = requests.get(f"{BASE_URL}/api/media-library/providers", headers=auth, timeout=20)
        data = r.json()
        # Ensure no raw api_key field on any provider entry and masked keys use bullets
        for p in data["providers"]:
            assert "api_key" not in p, f"raw api_key leaked on {p['id']}"
            mk = p.get("masked_key")
            if mk:
                # Must contain the masking bullet character
                assert "•" in mk, f"masked_key for {p['id']} not masked: {mk}"
                # A real Pixabay key is >= 32 chars; masked must be substantially shorter/different
                assert len(mk) < 30, f"masked_key looks like a full key for {p['id']}"


# --- validate-before-save ---
class TestValidateBeforeSave:
    def test_invalid_pixabay_key_rejected_and_no_overwrite(self, auth):
        # Ensure baseline is ACTIVE
        assert _ensure_pixabay_active(auth), "Baseline pixabay not restorable to CONNECTED"
        # Attempt to save an invalid key
        r = requests.post(f"{BASE_URL}/api/media-library/providers/pixabay_video/config",
                          headers=auth, json={"api_key": "INVALID_TESTER_KEY_1234"}, timeout=30)
        assert r.status_code == 400, r.text
        assert "not validated" in r.text.lower() or "invalid_key" in r.text.lower()

        # Now confirm pixabay is STILL active
        p = requests.get(f"{BASE_URL}/api/media-library/providers", headers=auth, timeout=20).json()
        provs = {x["id"]: x for x in p["providers"]}
        assert provs["pixabay_video"]["status"] == "ACTIVE", "Pixabay was overwritten by invalid key!"

        # A live search must still work
        s = requests.post(f"{BASE_URL}/api/media-library/search", headers=auth,
                          json={"provider_id": "pixabay_video", "query": "forest", "per_page": 3},
                          timeout=30).json()
        assert s.get("configured") is True
        assert isinstance(s.get("results"), list) and len(s["results"]) >= 1

    def test_provider_test_returns_test_code(self, auth):
        r = requests.post(f"{BASE_URL}/api/media-library/providers/pixabay_video/test",
                          headers=auth, timeout=30)
        assert r.status_code == 200
        assert "test_code" in r.json()

    def test_logs_endpoint(self, auth):
        r = requests.get(f"{BASE_URL}/api/media-library/providers/pixabay_video/logs",
                         headers=auth, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "logs" in data
        # At least one 'validate' event from the invalid-key test above should exist
        actions = [l.get("action") for l in data["logs"]]
        assert "validate" in actions or "save" in actions or "test" in actions


# --- Live search ---
class TestSearch:
    def test_pixabay_live_search_returns_real_results(self, auth):
        assert _ensure_pixabay_active(auth), "Could not restore pixabay to CONNECTED"
        r = requests.post(f"{BASE_URL}/api/media-library/search", headers=auth,
                          json={"provider_id": "pixabay_video", "query": "peaceful forest sunrise", "per_page": 5},
                          timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d.get("configured") is True, d
        assert len(d["results"]) == 5, d
        for it in d["results"]:
            assert it.get("preview_url")
            assert it.get("width") and it.get("height")
            assert it.get("duration_seconds") is not None
            assert it.get("creator_name")
            assert it.get("license_type")

    def test_pexels_search_best_effort(self, auth):
        # Pexels is env-provided, rate-limited. Either results or honest error is acceptable.
        r = requests.post(f"{BASE_URL}/api/media-library/search", headers=auth,
                          json={"provider_id": "pexels_video", "query": "forex trading", "per_page": 3},
                          timeout=45)
        assert r.status_code == 200
        d = r.json()
        assert d.get("configured") is True
        # Either results or an honest error message — both acceptable
        assert isinstance(d.get("results"), list)
        if not d["results"]:
            assert d.get("error"), "Pexels returned no results without an honest error message"

    def test_non_active_provider_returns_honest_reason(self, auth):
        r = requests.post(f"{BASE_URL}/api/media-library/search", headers=auth,
                          json={"provider_id": "pixabay_music", "query": "test", "per_page": 3},
                          timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d.get("configured") is False
        assert d.get("reason")
        assert d["results"] == []


# --- Master Asset Vault ---
class TestVault:
    def test_get_assets(self, auth):
        r = requests.get(f"{BASE_URL}/api/media-library/assets", headers=auth, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "assets" in d and "count" in d
        assert isinstance(d["assets"], list)

    def test_register_asset(self, auth):
        # First search for an item — retry search a few times to work around Pixabay flakiness
        assert _ensure_pixabay_active(auth), "Could not restore pixabay to CONNECTED"
        s = None
        for _ in range(3):
            s = requests.post(f"{BASE_URL}/api/media-library/search", headers=auth,
                              json={"provider_id": "pixabay_video", "query": "forest", "per_page": 3},
                              timeout=30).json()
            if s.get("results"):
                break
            time.sleep(2)
            _ensure_pixabay_active(auth)
        assert s.get("results"), s
        item = s["results"][0]
        r = requests.post(f"{BASE_URL}/api/media-library/register", headers=auth,
                          json={"item": item, "collection": "QRU General Backgrounds"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d.get("qru_asset_id", "").startswith("QRU-MEDIA-")
        assert d.get("provider") == item.get("provider")
        assert d.get("license_type") == item.get("license_type")
        assert d.get("creator_name") == item.get("creator_name")

    def test_collections(self, auth):
        r = requests.get(f"{BASE_URL}/api/media-library/collections", headers=auth, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert len(d["video_collections"]) == 22
        assert len(d["audio_collections"]) == 27


# --- Full production pipeline (Milestone 001) ---
class TestProducePipeline:
    def test_produce_proof_full_pipeline(self, auth):
        # Long-running: real Pixabay download + OpenAI TTS + ffmpeg render (~40-60s)
        assert _ensure_pixabay_active(auth), "Could not restore pixabay to CONNECTED"
        t0 = time.time()
        r = requests.post(f"{BASE_URL}/api/media-library/produce-proof", headers=auth,
                          json={"provider_id": "pixabay_video",
                                "query": "peaceful forest sunrise",
                                "product_title": "Forex Foundations"},
                          timeout=180)
        elapsed = time.time() - t0
        print(f"produce-proof took {elapsed:.1f}s")
        assert r.status_code == 200, r.text[:600]
        d = r.json()
        assert d.get("ok") is True, d
        # Every step must be present + status 'ok' (narration may be 'degraded' but still ok pipeline)
        step_map = {s["step"]: s for s in d["steps"]}
        required = ["live_provider_search", "asset_recommendation", "human_approval",
                    "license_verification", "download", "asset_registration",
                    "narration", "caption_generation", "mp4_rendering",
                    "quality_review", "master_asset_vault", "distribution_ready"]
        for step in required:
            assert step in step_map, f"missing step: {step}"
            assert step_map[step]["status"] in ("ok", "degraded"), step_map[step]

        # download has checksum
        assert step_map["download"].get("checksum")

        # source + showcase assets
        assert d["source_asset"]["qru_asset_id"].startswith("QRU-MEDIA-")
        assert d["source_asset"].get("checksum")
        show = d["showcase_asset"]
        assert show["qru_asset_id"].startswith("QRU-SHOWCASE-")
        assert show["width"] == 1280 and show["height"] == 720
        assert show.get("distribution_ready") is True
        assert show.get("checksum")

        # Save for the file-streaming test
        pytest.showcase_id = show["qru_asset_id"]

    def test_milestones_endpoint(self, auth):
        r = requests.get(f"{BASE_URL}/api/media-library/milestones", headers=auth, timeout=20)
        assert r.status_code == 200
        d = r.json()
        codes = [m.get("code") for m in d.get("milestones", [])]
        assert "QRU-MILESTONE-001" in codes, codes

    def test_asset_file_streams_video(self, auth):
        aid = getattr(pytest, "showcase_id", None)
        if not aid:
            # fallback: query any showcase asset
            r = requests.get(f"{BASE_URL}/api/media-library/assets", headers=auth, timeout=20).json()
            aid = next((a["qru_asset_id"] for a in r["assets"] if a.get("qru_asset_id", "").startswith("QRU-SHOWCASE-")), None)
            assert aid, "No showcase asset present"
        r = requests.get(f"{BASE_URL}/api/media-library/asset/{aid}/file", timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("video/")
        assert len(r.content) > 10_000
