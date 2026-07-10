"""Iteration 39 — Founder-facing LIVE PROOF (Milestone 001) + Scene Asset Matcher™ certification.

Covers:
  1) POST /api/media-library/produce-proof — full transparent pipeline output with split
     technical_qa + brand_content_qa, full license-evidence source_asset record, summary
     block, and playable /asset/{id}/file MP4.
  2) POST /api/media-library/scene-match — narration→scene segmentation, learning purpose,
     search terms (literal/metaphorical/emotional/environmental) + primary_query,
     forex exclusions, candidate scoring/tiering, licensing capture, per-scene
     recommendation, empty-narration 400, no-result note, exclusion filtering.
  3) Regression — providers list (pixabay ACTIVE with masked key, pexels ACTIVE env),
     honest search error handling, master asset vault list, GET /milestones.
"""
import os
import time
import pytest
import requests


def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    # Fallback to frontend/.env (test env doesn't inherit frontend env)
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    raise RuntimeError("REACT_APP_BACKEND_URL not found")


BASE_URL = _load_backend_url()
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def founder_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD},
                      timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def auth(founder_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {founder_token}",
                      "Content-Type": "application/json"})
    return s


def _ensure_pixabay_active(auth):
    """Iteration 38 lesson: /providers/{id}/test can transient-demote; retry up to 5x."""
    for _ in range(5):
        p = auth.get(f"{BASE_URL}/api/media-library/providers", timeout=15).json()["providers"]
        px = next((x for x in p if x["id"] == "pixabay_video"), None)
        if px and px.get("connected"):
            return px
        time.sleep(2)
    return px


# ---------- Regression: providers ----------
class TestProviders:
    def test_providers_list(self, auth):
        r = auth.get(f"{BASE_URL}/api/media-library/providers", timeout=15)
        assert r.status_code == 200
        provs = r.json()["providers"]
        ids = {p["id"]: p for p in provs}
        assert "pixabay_video" in ids and "pexels_video" in ids
        # no raw api_key ever leaked
        for p in provs:
            assert "api_key" not in p, f"raw key leaked on {p['id']}"

    def test_pixabay_active_with_masked_key(self, auth):
        px = _ensure_pixabay_active(auth)
        assert px and px.get("connected") is True, f"Pixabay not active: {px}"
        assert px.get("status") == "ACTIVE"
        # masked key present, not raw
        mk = px.get("masked_key")
        assert mk and "•" in mk, f"masked_key missing or unmasked: {mk!r}"

    def test_pexels_active_env_provided(self, auth):
        provs = auth.get(f"{BASE_URL}/api/media-library/providers", timeout=15).json()["providers"]
        pex = next((x for x in provs if x["id"] == "pexels_video"), None)
        assert pex is not None
        # spec: pexels env-provided ACTIVE. Honest env access flag present.
        assert pex.get("env_provided") is True or pex.get("connected") is True, f"pexels not env active: {pex}"


# ---------- Scene Asset Matcher ----------
class TestSceneMatcher:
    def test_empty_narration_400(self, auth):
        r = auth.post(f"{BASE_URL}/api/media-library/scene-match",
                      json={"narration": "   ", "topic": "forex"}, timeout=30)
        assert r.status_code == 400, f"expected 400, got {r.status_code} {r.text[:200]}"

    def test_forex_match_full_shape(self, auth):
        _ensure_pixabay_active(auth)
        narration = ("Currencies move through a global network of banks and businesses. "
                     "Leverage increases your buying power, but it also increases your risk. "
                     "Take a breath and understand the market before you risk your money.")
        r = auth.post(f"{BASE_URL}/api/media-library/scene-match",
                      json={"narration": narration, "topic": "forex", "aspect": "landscape"},
                      timeout=60)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        # Exclusions include forex-safe blocklist
        excl = [e.lower() for e in data.get("exclusions", [])]
        for kw in ("gambling", "casino", "guaranteed profit", "get rich quick"):
            assert kw in excl, f"exclusion missing: {kw} in {excl}"
        # cryptocurrency listed in forex list per code
        assert "cryptocurrency" in excl
        # scenes
        assert data["scene_count"] >= 2
        for s in data["scenes"]:
            assert "scene_text" in s and s["scene_text"].strip()
            assert "learning_purpose" in s and s["learning_purpose"]
            terms = s["search_terms"]
            for k in ("literal", "metaphorical", "emotional", "environmental"):
                assert k in terms and isinstance(terms[k], list), f"missing search_terms.{k}"
            assert s.get("primary_query"), "primary_query missing"
            # candidates OR honest note
            if s["candidates"]:
                for c in s["candidates"]:
                    assert 0 <= c["match_score"] <= 100
                    for b in ("relevance", "technical", "composition", "brand_fit", "licensing", "representation"):
                        assert b in c["score"], f"score breakdown missing {b}"
                    assert c["tier"] in ("Gold Gallery", "Approved", "Shortlist", "Below threshold")
                    assert "license_type" in c
                    assert "commercial_use_allowed" in c
                    rec = c["recommendation"]
                    for rk in ("suggested_crop", "suggested_start", "suggested_end",
                               "suggested_duration", "suggested_speed", "suggested_transition",
                               "text_safe_zone"):
                        assert rk in rec, f"recommendation missing {rk}"
            else:
                assert s.get("note"), "empty candidates must carry honest note"

    def test_nonsense_narration_honest_note(self, auth):
        _ensure_pixabay_active(auth)
        r = auth.post(f"{BASE_URL}/api/media-library/scene-match",
                      json={"narration": "xzqwv plkjm zzznnn.", "topic": "forex"}, timeout=45)
        assert r.status_code == 200
        data = r.json()
        # At least one scene must either yield candidates or an honest note.
        for s in data["scenes"]:
            if not s["candidates"]:
                assert s.get("note"), f"scene {s['scene_index']} missing note"

    def test_exclusion_filters_candidates(self, auth):
        """Verify that if any candidate title matched an exclusion, it is not returned."""
        _ensure_pixabay_active(auth)
        r = auth.post(f"{BASE_URL}/api/media-library/scene-match",
                      json={"narration": "A city skyline at sunrise. The world market opens.",
                            "topic": "forex"},
                      timeout=45)
        assert r.status_code == 200
        data = r.json()
        excl = [e.lower() for e in data["exclusions"]]
        for s in data["scenes"]:
            for c in s["candidates"]:
                t = str(c.get("title") or "").lower()
                for kw in excl:
                    assert kw not in t, f"excluded '{kw}' leaked in candidate title: {t}"


# ---------- Live Proof (produce-proof) ----------
# Call ONCE; share across dependent tests.
@pytest.fixture(scope="session")
def proof_response(auth):
    _ensure_pixabay_active(auth)
    r = auth.post(f"{BASE_URL}/api/media-library/produce-proof",
                  json={"provider_id": "pixabay_video",
                        "query": "peaceful forest sunrise",
                        "product_title": "Forex Foundations"},
                  timeout=180)
    return r


class TestProduceProof:
    def test_status_ok(self, proof_response):
        assert proof_response.status_code == 200, proof_response.text[:300]
        data = proof_response.json()
        assert data.get("ok") is True, f"pipeline failed: {data}"

    def test_all_13_stages_present(self, proof_response):
        data = proof_response.json()
        required = ["live_provider_search", "asset_recommendation", "human_approval",
                    "license_verification", "download", "checksum_verification",
                    "master_asset_registration", "narration", "caption_generation",
                    "mp4_rendering", "technical_qa", "brand_content_qa",
                    "master_asset_vault", "distribution_ready"]
        step_names = [s["step"] for s in data["steps"]]
        for r in required:
            assert r in step_names, f"missing step: {r}. Got: {step_names}"
        # Each step has ok/degraded/failed status
        for s in data["steps"]:
            assert s["status"] in ("ok", "degraded", "failed", "blocked"), f"bad status: {s}"

    def test_split_qa_scores(self, proof_response):
        data = proof_response.json()
        steps = {s["step"]: s for s in data["steps"]}
        # both QA stages exist separately with their own scores
        assert "technical_qa" in steps and "brand_content_qa" in steps
        assert "score" in steps["technical_qa"] and isinstance(steps["technical_qa"]["score"], (int, float))
        assert "score" in steps["brand_content_qa"] and isinstance(steps["brand_content_qa"]["score"], (int, float))
        # summary carries both scores
        summary = data["summary"]
        assert "technical_qa_score" in summary and "brand_content_qa_score" in summary

    def test_source_asset_license_evidence(self, proof_response):
        data = proof_response.json()
        src = data["source_asset"]
        required = ["qru_asset_id", "provider", "provider_asset_id", "creator_name",
                    "license_name", "attribution_required", "commercial_use_allowed",
                    "modification_allowed", "original_filename", "checksum",
                    "vault_location", "acquisition_timestamp", "project_id",
                    "approving_user"]
        for k in required:
            assert k in src, f"source_asset missing {k}"
        assert src["project_id"] == "QRU-PROJ-FOREX-FOUNDATIONS"
        assert src["approving_user"] == "Erica Talbert"
        assert len(src["checksum"]) == 64  # sha256 hex

    def test_summary_block(self, proof_response):
        data = proof_response.json()
        s = data["summary"]
        for k in ("job_id", "pipeline_version", "asset_id", "source_provider",
                  "license_type", "render_duration_s", "checksum",
                  "technical_qa_score", "brand_content_qa_score",
                  "vault_location", "distribution_status"):
            assert k in s, f"summary missing {k}"

    def test_playable_video_stream(self, proof_response, auth):
        data = proof_response.json()
        aid = data["showcase_asset"]["qru_asset_id"]
        r = requests.get(f"{BASE_URL}/api/media-library/asset/{aid}/file",
                         timeout=30, stream=True)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("video/mp4")
        # read a chunk to prove streaming works
        first = next(r.iter_content(chunk_size=8192))
        assert first and len(first) > 100


# ---------- Regression: milestones + vault ----------
class TestRegression:
    def test_milestones(self, auth):
        r = auth.get(f"{BASE_URL}/api/media-library/milestones", timeout=15)
        assert r.status_code == 200
        ms = r.json()["milestones"]
        codes = [m.get("code") for m in ms]
        assert "QRU-MILESTONE-001" in codes

    def test_master_vault_list(self, auth):
        r = auth.get(f"{BASE_URL}/api/media-library/assets", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "assets" in d and isinstance(d["assets"], list)
        # No raw mongo _id in any asset
        for a in d["assets"]:
            assert "_id" not in a

    def test_honest_search_error_on_non_active(self, auth):
        """Non-active provider must return honest configured:false, not throw."""
        r = auth.post(f"{BASE_URL}/api/media-library/search",
                      json={"provider_id": "pixabay_music", "query": "calm piano"},
                      timeout=30)
        assert r.status_code == 200
        d = r.json()
        # configured false is the honest state; must include a reason
        if not d.get("configured"):
            assert d.get("reason") or d.get("error")
