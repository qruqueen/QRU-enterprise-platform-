"""MO-027 QRU Creative Director™ — Creative Direction Report tests (iteration 47).

Coverage:
 - POST /api/media-library/creative-direction returns full governed report
 - Low-scoring scenes (<70 match) get cd_approved=false, quality_rating=Needs Improvement, improvements[], scenes_needing_improvement, approval.default=MODIFY
 - Style override (Cinematic) forces visual_mood to that style (CHANGE STYLE behaviour)
 - Mood inference from narration text (Inspirational vs Professional)
 - Thumbnail concepts: exactly 3, exactly 1 recommended, recommended has the highest total
 - Regression: /director-plan still works; /scene-match dedup still ok; /showcase/produce (human_approval_required) still renders MO-012 directed video (MO-012 path preserved)
"""
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PW = "QruFounder2026!"


# ------------------- Fixtures -------------------
@pytest.fixture(scope="module")
def token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": FOUNDER_EMAIL, "password": FOUNDER_PW},
        timeout=30,
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    d = r.json()
    tok = d.get("access_token") or d.get("token")
    assert tok, f"No token in login response: {d}"
    return tok


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# Baseline scenes with mixed match scores (one below 70 -> should be flagged)
BASE_SCENES = [
    {"scene_text": "Forex means trading the world's currencies across global markets.",
     "learning_purpose": "Define forex", "match_score": 92},
    {"scene_text": "Every trade carries real risk of loss that you must respect.",
     "learning_purpose": "Respect risk", "match_score": 88},
    {"scene_text": "Understanding how currency pairs move takes patient study and practice.",
     "learning_purpose": "Patience", "match_score": 60},  # LOW quality - flag
    {"scene_text": "Learning to trade responsibly builds lasting confidence over time.",
     "learning_purpose": "Responsibility", "match_score": 85},
]

ALL_HIGH_SCENES = [
    {"scene_text": "Forex means trading the world's currencies across global markets.",
     "learning_purpose": "Define forex", "match_score": 92},
    {"scene_text": "Every trade carries real risk of loss that you must respect.",
     "learning_purpose": "Respect risk", "match_score": 88},
    {"scene_text": "Learning to trade responsibly builds lasting confidence over time.",
     "learning_purpose": "Responsibility", "match_score": 90},
]

NARRATION = (
    "Forex means trading the world's currencies across global markets. "
    "Every trade carries real risk of loss. Learning to trade responsibly builds confidence."
)


# ------------------- Creative Direction Report -------------------
class TestCreativeDirectionReport:
    def test_full_report_shape(self, headers):
        r = requests.post(
            f"{BASE_URL}/api/media-library/creative-direction",
            headers=headers,
            json={"topic": "forex", "narration": NARRATION, "scenes": BASE_SCENES},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        d = r.json()

        # Engine identity
        assert d["engine"] == "QRU Creative Director™ (MO-027)"
        assert isinstance(d.get("governed_by"), list) and len(d["governed_by"]) >= 1

        # Visual mood + options
        assert d["visual_mood"] in ["Educational", "Inspirational", "Professional", "Cinematic"]
        assert d["visual_mood_options"] == ["Educational", "Inspirational", "Professional", "Cinematic"]

        # Pacing
        assert d["recommended_pacing"] in ["Slow", "Medium", "Fast"]
        assert d["pacing_options"] == ["Slow", "Medium", "Fast"]

        # Scores block
        sc = d["scores"]
        for k in ["scene_quality", "brand_score", "learning_score", "thumbnail_score", "composite"]:
            assert k in sc and isinstance(sc[k], int)
            assert 0 <= sc[k] <= 100
        assert sc["scene_quality_rating"] in ["Excellent", "Good", "Needs Improvement"]

        # Treasure Standard prediction
        assert d["treasure_standard_prediction"] in [
            "Likely to Pass", "At Risk — review recommended", "Needs Improvement"
        ]

        # Direction blocks
        assert "story_direction" in d and "emotional_progression" in d["story_direction"]
        assert "visual_direction" in d
        assert "learning_direction" in d
        assert "brand_direction" in d

        # Scene reviews
        reviews = d["scene_reviews"]
        assert len(reviews) == len(BASE_SCENES)
        for r_ in reviews:
            assert "checks" in r_
            for c in ["helps_the_learner", "visually_interesting", "supports_the_narration"]:
                assert c in r_["checks"]
            assert isinstance(r_["cd_approved"], bool)
            assert r_["quality_rating"] in ["Excellent", "Good", "Needs Improvement"]
            assert isinstance(r_["improvements"], list)

        # Approval options exact
        assert d["approval"]["options"] == ["APPROVE", "MODIFY", "CHANGE STYLE"]

    def test_low_quality_scene_flagged_and_default_modify(self, headers):
        r = requests.post(
            f"{BASE_URL}/api/media-library/creative-direction",
            headers=headers,
            json={"topic": "forex", "narration": NARRATION, "scenes": BASE_SCENES},
            timeout=30,
        )
        d = r.json()
        # Scene index 2 has match_score=60 -> should NOT be cd_approved and rated Needs Improvement
        low = next((s for s in d["scene_reviews"] if s["scene_index"] == 2), None)
        assert low is not None
        assert low["cd_approved"] is False, low
        assert low["quality_rating"] == "Needs Improvement", low
        # improvements array must contain the specific suggestion about higher-scoring clip
        assert any("higher-scoring" in imp or "dynamic clip" in imp for imp in low["improvements"]), low["improvements"]

        # scenes_needing_improvement must include index 2
        assert 2 in d["scenes_needing_improvement"]

        # Approval default flips to MODIFY when any scene needs improvement
        assert d["approval"]["default"] == "MODIFY"

    def test_all_high_quality_defaults_to_approve(self, headers):
        r = requests.post(
            f"{BASE_URL}/api/media-library/creative-direction",
            headers=headers,
            json={"topic": "forex", "narration": NARRATION, "scenes": ALL_HIGH_SCENES},
            timeout=30,
        )
        d = r.json()
        assert d["scenes_needing_improvement"] == []
        assert d["approval"]["default"] == "APPROVE"
        # All scenes should be cd_approved when scores >= 70 + learning_purpose + reasonable length
        assert all(r_["cd_approved"] for r_ in d["scene_reviews"])

    def test_thumbnail_concepts_three_and_one_recommended(self, headers):
        r = requests.post(
            f"{BASE_URL}/api/media-library/creative-direction",
            headers=headers,
            json={"topic": "forex", "narration": NARRATION, "scenes": ALL_HIGH_SCENES},
            timeout=30,
        )
        d = r.json()
        concepts = d["thumbnail_concepts"]
        assert len(concepts) == 3
        # Verify score keys
        for c in concepts:
            for k in ["hierarchy", "emotional_impact", "readability", "contrast", "branding", "curiosity"]:
                assert k in c["scores"]
            assert isinstance(c["total"], int)
        # Exactly one recommended
        recs = [c for c in concepts if c.get("recommended")]
        assert len(recs) == 1
        # Recommended has the highest total
        assert recs[0]["total"] == max(c["total"] for c in concepts)
        # recommended_thumbnail matches
        assert d["recommended_thumbnail"]["name"] == recs[0]["name"]

    def test_style_override_cinematic(self, headers):
        """CHANGE STYLE behavior: passing style='Cinematic' forces visual_mood to Cinematic."""
        r = requests.post(
            f"{BASE_URL}/api/media-library/creative-direction",
            headers=headers,
            json={"topic": "forex", "narration": NARRATION,
                  "scenes": ALL_HIGH_SCENES, "style": "Cinematic"},
            timeout=30,
        )
        assert r.status_code == 200
        d = r.json()
        assert d["visual_mood"] == "Cinematic"

    def test_style_override_professional(self, headers):
        r = requests.post(
            f"{BASE_URL}/api/media-library/creative-direction",
            headers=headers,
            json={"topic": "forex", "narration": NARRATION,
                  "scenes": ALL_HIGH_SCENES, "style": "Professional"},
            timeout=30,
        )
        d = r.json()
        assert d["visual_mood"] == "Professional"

    def test_mood_inference_inspirational(self, headers):
        """Mood inference: narration full of hope/dream/confidence keywords -> Inspirational."""
        narr = ("Dream of a calm mind. Renewal and hope shape confidence. Gratitude and growth guide your future.")
        scenes = [
            {"scene_text": narr, "learning_purpose": "mindset", "match_score": 90},
            {"scene_text": "Take a slow breath and reflect with gratitude.",
             "learning_purpose": "mindset", "match_score": 88},
        ]
        r = requests.post(
            f"{BASE_URL}/api/media-library/creative-direction",
            headers=headers,
            json={"topic": "mindset", "narration": narr, "scenes": scenes},
            timeout=30,
        )
        d = r.json()
        assert d["visual_mood"] == "Inspirational", f"expected Inspirational, got {d['visual_mood']}"


# ------------------- Regression -------------------
class TestRegression:
    def test_director_plan_intact(self, headers):
        r = requests.post(
            f"{BASE_URL}/api/media-library/director-plan",
            headers=headers,
            json={"topic": "forex", "aspect": "landscape", "scenes": [
                {"scene_text": s["scene_text"], "learning_purpose": s["learning_purpose"]}
                for s in ALL_HIGH_SCENES
            ]},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["engine"].startswith("Director Intelligence"), d["engine"]
        assert d["scene_count"] == 3
        assert "scenes" in d and len(d["scenes"]) == 3

    def test_scene_match_dedup_intact(self, headers):
        r = requests.post(
            f"{BASE_URL}/api/media-library/scene-match",
            headers=headers,
            json={"narration": NARRATION, "topic": "forex", "aspect": "landscape"},
            timeout=90,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["scene_count"] >= 2
        assert d.get("variety_ok") is True or d.get("project_variety_score", 0) > 0

    def test_showcase_produce_mo012_render_after_approval(self, headers):
        """MO-012 render path preserved — produce a real showcase in human_approval_required mode."""
        # 1) scene-match to get real scenes
        m = requests.post(
            f"{BASE_URL}/api/media-library/scene-match",
            headers=headers,
            json={"narration": NARRATION, "topic": "forex", "aspect": "landscape"},
            timeout=90,
        )
        assert m.status_code == 200
        mr = m.json()
        # Build approved scene payload for produce (subset - 2 scenes suffices)
        approved = []
        for s in mr["scenes"][:2]:
            sel = next((c for c in s["candidates"]
                        if c["provider_asset_id"] == s.get("selected_provider_asset_id")),
                       s["candidates"][0] if s["candidates"] else None)
            if not sel:
                continue
            approved.append({
                "scene_index": s["scene_index"],
                "scene_text": s["scene_text"],
                "learning_purpose": s["learning_purpose"],
                "approved": True,
                "selected": sel,
            })
        assert len(approved) >= 2

        t0 = time.time()
        r = requests.post(
            f"{BASE_URL}/api/media-library/showcase/produce",
            headers=headers,
            json={
                "product_title": "TEST_MO027_Regression",
                "topic": "forex",
                "aspect": "landscape",
                "narration": NARRATION,
                "approval_mode": "human_approval_required",
                "scenes": approved,
            },
            timeout=180,
        )
        elapsed = time.time() - t0
        print(f"produce elapsed={elapsed:.1f}s status={r.status_code}")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True, d
        # Direction plan present (from iteration 46 baseline)
        assert "direction_plan" in d
        # Showcase asset returned
        assert d.get("showcase_asset", {}).get("qru_asset_id")
