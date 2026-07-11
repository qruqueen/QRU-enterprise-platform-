"""Iteration 46 — MO-027 Director Intelligence™ backend regression.
Tests:
  1. POST /api/media-library/director-plan — governed Direction Plan shape + honest applied/suggested split.
  2. POST /api/media-library/showcase/produce (human_approval_required, 2 & 3 scenes) — directed render
     with cinematic crossfades. Verifies:
       - ok=true, direction_plan echoed, mp4_assembly step says "Directed N-scene 720p MP4 ... with cinematic crossfades"
       - Technical QA has_video + resolution_ok pass
       - GET /api/media-library/asset/{id}/file streams a valid MP4
  3. Regression: draft mode still works (auto_select_draft).
NOTE: These tests trigger real ffmpeg renders (30–90s each) but do NOT publish to YouTube.
"""
import os
import time
import requests
import pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PW = "QruFounder2026!"

# Multi-scene forex narration (produces 3+ scenes with the QRU scene matcher).
NARRATION_3 = (
    "Forex means trading the world's currencies across global markets. "
    "Every trade carries real risk of loss that you must respect. "
    "Understanding how currency pairs move takes patient study and practice. "
    "Learning to trade responsibly builds lasting confidence over time. "
    "A calm and focused mind makes clearer decisions. "
    "Take a slow breath and reflect on your progress with gratitude."
)
# 2-scene narration — three shorter sentences typically produce 2 scenes after merging.
NARRATION_2 = (
    "Forex means trading currencies across global markets. "
    "Every trade carries real risk of loss you must respect. "
    "Learning to trade responsibly builds lasting confidence."
)


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PW}, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def hdr(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# --- 1. Director Plan endpoint ---
class TestDirectorPlanEndpoint:
    def test_3_scene_plan_shape(self, hdr):
        payload = {
            "topic": "forex",
            "aspect": "landscape",
            "scenes": [
                {"scene_text": "Forex means trading currencies.", "learning_purpose": "hook"},
                {"scene_text": "Every trade carries real risk.", "learning_purpose": "risk-awareness"},
                {"scene_text": "Learn responsibly with QRU.", "learning_purpose": "cta"},
            ],
        }
        r = requests.post(f"{BASE}/api/media-library/director-plan", json=payload, headers=hdr, timeout=30)
        assert r.status_code == 200, r.text
        p = r.json()
        # engine + governance
        assert p["engine"] == "Director Intelligence™ (MO-027)"
        assert "Treasure Standard™" in p["governed_by"]
        assert any("§6" in g for g in p["governed_by"])
        assert p["scene_count"] == 3
        assert isinstance(p["target_runtime_seconds"], (int, float)) and p["target_runtime_seconds"] > 0
        # arc roles from allowed set
        allowed_roles = {"Hook", "Context", "Insight", "Reinforcement", "Closing CTA"}
        for sp in p["scenes"]:
            assert sp["arc_role"] in allowed_roles
            assert 3.0 <= sp["duration_seconds"] <= 8.0
            assert isinstance(sp["energy"], int)
            assert "camera_move" in sp
            assert "text_timing" in sp
            assert "pacing_note" in sp
            assert "transition_label" in sp
        # last scene should be Closing CTA (or Insight if n==1)
        assert p["scenes"][0]["arc_role"] == "Hook"
        assert p["scenes"][-1]["arc_role"] == "Closing CTA"
        # transitions: all-but-last must have a transition_out; last has None
        assert p["scenes"][-1]["transition_out"] is None
        assert all(s["transition_out"] for s in p["scenes"][:-1])
        # emotional flow shape
        assert len(p["emotional_flow"]) == 3
        for ef in p["emotional_flow"]:
            assert set(ef.keys()) >= {"scene", "role", "energy"}
        # honesty split
        assert isinstance(p["applied_by_engine"], list) and len(p["applied_by_engine"]) >= 3
        assert isinstance(p["suggested_for_review"], list) and len(p["suggested_for_review"]) >= 3
        # Treasure Standard™: camera Ken Burns, on-screen text/CTA overlays, music bed, thumbnail overlay text
        # MUST be in suggested (not applied)
        joined_sugg = " ".join(p["suggested_for_review"]).lower()
        joined_app = " ".join(p["applied_by_engine"]).lower()
        assert "ken burns" in joined_sugg or "camera movement" in joined_sugg
        assert "on-screen text" in joined_sugg or "cta overlay" in joined_sugg
        assert "music" in joined_sugg
        assert "thumbnail" in joined_sugg
        # And these MUST NOT be in applied
        assert "ken burns" not in joined_app
        assert "music" not in joined_app
        # Pacing + transitions + variety + soft captions ARE applied
        assert "pacing" in joined_app
        assert "transition" in joined_app
        # extras
        assert "closing_cta" in p and isinstance(p["closing_cta"], str) and len(p["closing_cta"]) > 0
        assert "learning_reinforcement" in p
        assert "music_cues" in p and len(p["music_cues"]) >= 2
        assert "thumbnail_concept" in p and "hero_scene_index" in p["thumbnail_concept"]
        assert 0 <= p["thumbnail_concept"]["hero_scene_index"] < 3
        assert "retention_optimization" in p and len(p["retention_optimization"]) >= 3

    def test_2_scene_plan(self, hdr):
        payload = {"topic": "forex", "scenes": [
            {"scene_text": "Currencies move.", "learning_purpose": "hook"},
            {"scene_text": "Learn with QRU.", "learning_purpose": "cta"},
        ]}
        r = requests.post(f"{BASE}/api/media-library/director-plan", json=payload, headers=hdr, timeout=30)
        assert r.status_code == 200
        p = r.json()
        assert p["scene_count"] == 2
        assert p["scenes"][0]["arc_role"] == "Hook"
        assert p["scenes"][-1]["arc_role"] == "Closing CTA"
        # first scene has a transition; last does not
        assert p["scenes"][0]["transition_out"] is not None
        assert p["scenes"][-1]["transition_out"] is None


def _get_scene_selections(hdr, narration):
    """Run scene-match, auto-pick top candidate per scene, return the payload scene list."""
    r = requests.post(f"{BASE}/api/media-library/scene-match",
                      json={"narration": narration, "topic": "forex", "aspect": "landscape"},
                      headers=hdr, timeout=120)
    assert r.status_code == 200, r.text
    data = r.json()
    scenes = []
    for sc in data["scenes"]:
        cands = sc.get("candidates", [])
        # prefer marked-selected, else top scored unique candidate
        sel = next((c for c in cands if c.get("selected")), None)
        if not sel and cands:
            sel = cands[0]
        assert sel, f"No candidate for scene {sc.get('scene_index')}"
        scenes.append({
            "scene_index": sc["scene_index"],
            "scene_text": sc["scene_text"],
            "learning_purpose": sc.get("learning_purpose"),
            "approved": True,
            "selected": sel,
        })
    return scenes


# --- 2. Directed produce (2 & 3 scenes) ---
class TestDirectedProduce:
    @pytest.mark.parametrize("min_scenes,narration", [
        (3, NARRATION_3),
        (2, NARRATION_2),
    ])
    def test_directed_render_and_stream(self, hdr, min_scenes, narration):
        scenes = _get_scene_selections(hdr, narration)
        assert len(scenes) >= min_scenes, f"Expected >= {min_scenes} scenes, got {len(scenes)}"
        nscenes = len(scenes)
        payload = {
            "product_title": "Forex Foundations",
            "topic": "forex",
            "aspect": "landscape",
            "narration": narration,
            "approval_mode": "human_approval_required",
            "scenes": scenes,
        }
        t0 = time.time()
        r = requests.post(f"{BASE}/api/media-library/showcase/produce",
                          json=payload, headers=hdr, timeout=300)
        elapsed = time.time() - t0
        assert r.status_code == 200, f"produce failed: {r.status_code} {r.text[:400]}"
        res = r.json()
        assert res.get("ok") is True, f"produce not ok ({elapsed:.1f}s): {res}"

        # direction_plan echoed
        dp = res.get("direction_plan")
        assert dp and dp.get("engine") == "Director Intelligence™ (MO-027)"
        assert dp.get("scene_count") == nscenes

        # mp4_assembly step wording
        steps = res.get("steps", [])
        mp4_steps = [s for s in steps if s["step"] == "mp4_assembly"]
        assert mp4_steps, "no mp4_assembly step"
        detail = mp4_steps[0]["detail"]
        assert mp4_steps[0]["status"] == "ok", f"mp4_assembly not ok: {detail}"
        assert f"Directed {nscenes}-scene 720p MP4" in detail, f"assembly wording missing: {detail}"
        assert "cinematic crossfades" in detail, f"cinematic crossfades missing: {detail}"

        # director_intelligence step includes applied + suggested
        di_steps = [s for s in steps if s["step"] == "director_intelligence"]
        assert di_steps, "no director_intelligence step"
        assert di_steps[0].get("applied") and di_steps[0].get("suggested")

        # Technical QA
        tqa = [s for s in steps if s["step"] == "technical_qa"]
        assert tqa and tqa[0]["status"] == "ok", f"technical_qa: {tqa}"
        checks = tqa[0].get("checks", {})
        assert checks.get("has_video") is True
        assert checks.get("resolution_ok") is True
        assert checks.get("multi_scene") is True

        # asset streamable
        asset_id = res["showcase_asset"]["qru_asset_id"]
        file_url = f"{BASE}/api/media-library/asset/{asset_id}/file"
        h = requests.get(file_url, timeout=60, stream=True)
        assert h.status_code == 200, f"asset file HTTP {h.status_code}"
        assert h.headers.get("content-type", "").startswith("video/mp4")
        # read a small chunk to verify streaming works
        first_chunk = next(h.iter_content(4096), b"")
        assert len(first_chunk) > 0, "empty MP4 stream"
        h.close()

        print(f"[iter46] {nscenes}-scene directed render OK in {elapsed:.1f}s — asset {asset_id}")


# --- 3. Regression: draft mode still works ---
class TestDraftRegression:
    def test_draft_mode_produces(self, hdr):
        payload = {
            "product_title": "Forex Foundations DRAFT",
            "topic": "forex",
            "aspect": "landscape",
            "narration": NARRATION_3,
            "approval_mode": "auto_select_draft",
        }
        r = requests.post(f"{BASE}/api/media-library/showcase/produce",
                          json=payload, headers=hdr, timeout=300)
        assert r.status_code == 200, r.text
        res = r.json()
        assert res.get("ok") is True, f"draft not ok: {res.get('error') or res}"
        assert res.get("is_draft_preview") is True
        # direction plan still present in draft mode
        assert res.get("direction_plan", {}).get("engine") == "Director Intelligence™ (MO-027)"
        # DRAFT PREVIEW guard step
        assert any(s["step"] == "draft_preview" for s in res.get("steps", []))
