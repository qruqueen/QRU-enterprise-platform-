"""Iteration 40 — QRU Flagship Showcase™ Pilot (MO-012) end-to-end backend tests.

Covers Scene Asset Matcher™ cross-scene dedup, MO-012 approval modes, draft & human-approval
production, gold-master certification and Milestone 001 regression.

Reuses ONE live human-approval production run (session fixture) for gold-master gate checks.
"""
import os
import time
import pytest
import requests

def _load_frontend_env():
    p = "/app/frontend/.env"
    if os.path.exists(p):
        with open(p) as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    return os.environ.get("REACT_APP_BACKEND_URL")

_BASE = _load_frontend_env()
assert _BASE, "REACT_APP_BACKEND_URL missing in frontend/.env"
BASE_URL = _BASE.rstrip("/")
API = f"{BASE_URL}/api"
FOUNDER = {
    "email": "22j2rsdzb8@privaterelay.appleid.com",
    "password": "QruFounder2026!",
}

NARRATION = (
    "Forex means trading the world's currencies across global markets. "
    "Every trade carries real risk of loss that you must respect. "
    "Understanding how currency pairs move takes patient study and practice. "
    "Learning to trade responsibly builds lasting confidence over time. "
    "A calm and focused mind makes clearer decisions. "
    "Take a slow breath and reflect on your progress with gratitude."
)


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def founder_token():
    r = requests.post(f"{API}/auth/login", json=FOUNDER, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, r.text
    return tok


@pytest.fixture(scope="session")
def hdr(founder_token):
    return {"Authorization": f"Bearer {founder_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def scene_match_result(hdr):
    """One live scene-match call reused across dedup tests."""
    r = requests.post(f"{API}/media-library/scene-match",
                      headers=hdr,
                      json={"narration": NARRATION, "topic": "forex", "aspect": "landscape"},
                      timeout=120)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="session")
def human_approval_run(hdr, scene_match_result):
    """One live human-approval produce run. Reused by gold-master + records tests."""
    scenes = []
    for sc in scene_match_result["scenes"]:
        sel = next((c for c in sc["candidates"] if c.get("selected")), None) or (
            sc["candidates"][0] if sc["candidates"] else None
        )
        if not sel:
            continue
        scenes.append({
            "scene_index": sc["scene_index"],
            "scene_text": sc["scene_text"],
            "learning_purpose": sc["learning_purpose"],
            "approved": True,
            "selected": sel,
        })
    assert len(scenes) >= 2, "Need >=2 approved scenes"
    payload = {
        "product_title": "MO-012 Human-Approval Regression",
        "topic": "forex",
        "aspect": "landscape",
        "narration": NARRATION,
        "approval_mode": "human_approval_required",
        "scenes": scenes,
    }
    r = requests.post(f"{API}/media-library/showcase/produce",
                      headers=hdr, json=payload, timeout=300)
    assert r.status_code == 200, f"produce failed {r.status_code}: {r.text[:500]}"
    data = r.json()
    assert data.get("ok") is True, data
    return data


# ---------- SCENE MATCHER dedup + core ----------
class TestSceneMatcherDedup:
    def test_multi_scene_unique_selected_assets(self, scene_match_result):
        d = scene_match_result
        assert d["scene_count"] >= 2
        sel_ids = [s["selected_provider_asset_id"] for s in d["scenes"]
                   if s.get("selected_provider_asset_id")]
        assert len(sel_ids) >= 2, f"need at least 2 selected assets, got {sel_ids}"
        assert len(set(sel_ids)) == len(sel_ids), (
            f"Selected assets are NOT unique across scenes: {sel_ids}"
        )

    def test_project_variety_fields_present(self, scene_match_result):
        d = scene_match_result
        for k in ("project_variety_score", "unique_assets", "unique_creators",
                  "variety_ok", "scenes_needing_review"):
            assert k in d, f"missing field {k}"
        assert isinstance(d["variety_ok"], bool)
        assert 0 <= d["project_variety_score"] <= 100

    def test_candidate_dedup_fields(self, scene_match_result):
        for sc in scene_match_result["scenes"]:
            for c in sc["candidates"]:
                assert "variety_score" in c
                assert c["dedup_status"] in ("unique", "near_duplicate", "hard_duplicate")
                assert "dedup_flags" in c and isinstance(c["dedup_flags"], list)

    def test_hard_duplicates_not_selected(self, scene_match_result):
        for sc in scene_match_result["scenes"]:
            for c in sc["candidates"]:
                if c.get("selected"):
                    assert c["dedup_status"] != "hard_duplicate", (
                        f"scene {sc['scene_index']} selected a hard duplicate"
                    )

    def test_forex_exclusions_present(self, scene_match_result):
        ex = [e.lower() for e in scene_match_result["exclusions"]]
        for expected in ("gambling", "casino", "get rich quick", "cryptocurrency"):
            assert expected in ex, f"missing exclusion '{expected}' in {ex}"


class TestSceneMatcherCore:
    def test_empty_narration_returns_400(self, hdr):
        r = requests.post(f"{API}/media-library/scene-match",
                          headers=hdr, json={"narration": "   ", "topic": "forex"},
                          timeout=30)
        assert r.status_code == 400

    def test_scene_shape(self, scene_match_result):
        for sc in scene_match_result["scenes"]:
            assert sc["learning_purpose"]
            terms = sc["search_terms"]
            for k in ("literal", "metaphorical", "emotional", "environmental"):
                assert k in terms, f"missing search_term key {k}"

    def test_candidate_shape(self, scene_match_result):
        for sc in scene_match_result["scenes"]:
            for c in sc["candidates"]:
                s = c["score"]
                for k in ("relevance", "technical", "composition",
                          "brand_fit", "licensing", "representation"):
                    assert k in s
                assert 0 <= c["match_score"] <= 100
                assert c["tier"] in ("Gold Gallery", "Approved", "Shortlist",
                                     "Below threshold")
                rec = c["recommendation"]
                for k in ("suggested_crop", "suggested_start", "suggested_end",
                          "suggested_duration", "suggested_speed",
                          "suggested_transition", "text_safe_zone"):
                    assert k in rec, f"recommendation missing {k}"


# ---------- MO-012 SHOWCASE MODES ----------
class TestShowcaseModes:
    def test_modes_shape(self, hdr):
        r = requests.get(f"{API}/media-library/showcase/modes", headers=hdr, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        modes = d["modes"]
        assert set(modes.keys()) >= {"human_approval_required", "auto_select_draft",
                                     "governed_auto_select"}
        assert modes["human_approval_required"]["enabled"] is True
        assert modes["human_approval_required"]["default"] is True
        assert modes["auto_select_draft"]["enabled"] is True
        assert modes["governed_auto_select"]["enabled"] is False
        assert isinstance(d["production_statuses"], list)
        assert len(d["gold_master_gates"]) == 11
        assert d["governed_auto_select_unlocked"] is False
        assert "approved_run_count" in d


# ---------- MO-012 PRODUCE draft ----------
class TestDraftProduce:
    def test_draft_run(self, hdr):
        payload = {
            "product_title": "MO-012 Draft Regression",
            "topic": "forex",
            "aspect": "landscape",
            "narration": NARRATION,
            "approval_mode": "auto_select_draft",
        }
        r = requests.post(f"{API}/media-library/showcase/produce",
                          headers=hdr, json=payload, timeout=300)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["ok"] is True
        assert d["is_draft_preview"] is True
        assert isinstance(d["steps"], list) and len(d["steps"]) >= 5
        assert d.get("technical_qa_score") is not None
        assert d.get("brand_content_qa_score") is not None
        sa = d["showcase_asset"]
        assert sa["production_status"] == "Draft"
        assert sa["distribution_ready"] is False
        assert sa["gold_master_certified"] is False
        assert d["acceptance_record_id"]

        # streamable file
        aid = sa["qru_asset_id"]
        f = requests.get(f"{API}/media-library/asset/{aid}/file", timeout=60)
        assert f.status_code == 200
        assert "video/mp4" in f.headers.get("content-type", "").lower() or \
               f.content[:4] in (b"\x00\x00\x00\x18", b"\x00\x00\x00\x20", b"\x00\x00\x00\x1c")
        assert len(f.content) > 10_000

    def test_draft_cannot_be_certified(self, hdr):
        # Trigger a small draft, then attempt to certify → expect refusal.
        payload = {
            "product_title": "MO-012 Draft Certify Guard",
            "topic": "forex",
            "aspect": "landscape",
            "narration": NARRATION,
            "approval_mode": "auto_select_draft",
        }
        r = requests.post(f"{API}/media-library/showcase/produce",
                          headers=hdr, json=payload, timeout=300)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["ok"] and d["is_draft_preview"]
        aid = d["showcase_asset"]["qru_asset_id"]
        cr = requests.post(f"{API}/media-library/showcase/{aid}/certify-gold-master",
                           headers=hdr, timeout=60)
        assert cr.status_code == 400
        assert "Draft previews can never be Gold Master Certified" in cr.text


# ---------- MO-012 PRODUCE human approval ----------
class TestHumanApproval:
    def test_run_ok_and_distribution_ready(self, human_approval_run):
        d = human_approval_run
        assert d["is_draft_preview"] is False
        sa = d["showcase_asset"]
        assert sa["distribution_ready"] is True
        assert sa["production_status"] == "Distribution Ready"
        assert d["technical_qa_score"] == 100
        assert d["brand_content_qa_score"] == 100

    def test_unapproved_scene_blocks(self, hdr, scene_match_result):
        scenes = []
        for sc in scene_match_result["scenes"]:
            sel = next((c for c in sc["candidates"] if c.get("selected")), None) or (
                sc["candidates"][0] if sc["candidates"] else None
            )
            if not sel:
                continue
            # mark ALL as approved=False → guardrail must fire
            scenes.append({
                "scene_index": sc["scene_index"],
                "scene_text": sc["scene_text"],
                "learning_purpose": sc["learning_purpose"],
                "approved": False,
                "selected": sel,
            })
        payload = {
            "product_title": "MO-012 Unapproved Guardrail",
            "topic": "forex",
            "aspect": "landscape",
            "narration": NARRATION,
            "approval_mode": "human_approval_required",
            "scenes": scenes,
        }
        r = requests.post(f"{API}/media-library/showcase/produce",
                          headers=hdr, json=payload, timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is False
        assert "not approved" in (d.get("error") or "").lower()


# ---------- MO-012 GUARDRAILS ----------
class TestGuardrails:
    def test_governed_auto_select_blocked(self, hdr):
        payload = {
            "product_title": "MO-012 Governed Auto-Select Guardrail",
            "topic": "forex",
            "aspect": "landscape",
            "narration": NARRATION,
            "approval_mode": "governed_auto_select",
        }
        r = requests.post(f"{API}/media-library/showcase/produce",
                          headers=hdr, json=payload, timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is False
        assert d.get("blocked") is True
        err = (d.get("error") or "").lower()
        assert "authorization" in err
        assert "approved" in err


# ---------- GOLD MASTER CERTIFY ----------
class TestGoldMaster:
    def test_certify_and_records(self, hdr, human_approval_run):
        aid = human_approval_run["showcase_asset"]["qru_asset_id"]
        record_id = human_approval_run["acceptance_record_id"]
        r = requests.post(f"{API}/media-library/showcase/{aid}/certify-gold-master",
                          headers=hdr, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["certified"] is True
        assert d["certified_by"]
        gates = d["gates"]
        assert len(gates) == 11
        assert all(gates.values()), f"unmet gates: {[k for k,v in gates.items() if not v]}"

        # records list contains our new certified record
        rec = requests.get(f"{API}/media-library/showcase/records/{record_id}",
                           headers=hdr, timeout=30)
        assert rec.status_code == 200
        rd = rec.json()
        assert rd["gold_master_certified"] is True
        assert rd["scene_list"] and len(rd["scene_list"]) >= 2
        for s in rd["scene_list"]:
            assert s["license_type"]
            assert s["checksum"] and len(s["checksum"]) == 64
        assert any("Gold Master" in v.get("status", "")
                   for v in rd.get("version_history", []))

    def test_records_list_endpoint(self, hdr):
        r = requests.get(f"{API}/media-library/showcase/records",
                         headers=hdr, timeout=30)
        assert r.status_code == 200
        assert r.json()["count"] >= 1


# ---------- REGRESSION Milestone 001 ----------
class TestMilestone001Regression:
    def test_milestones_endpoint(self, hdr):
        r = requests.get(f"{API}/media-library/milestones", headers=hdr, timeout=30)
        assert r.status_code == 200
        mils = r.json()["milestones"]
        m1 = next((m for m in mils if m.get("code") == "QRU-MILESTONE-001"), None)
        assert m1 is not None, "Milestone 001 missing!"
        assert m1.get("source_asset")
        assert m1.get("showcase_asset")

    def test_produce_proof_single_scene_still_works(self, hdr):
        payload = {
            "provider_id": "pixabay_video",
            "query": "calm ocean horizon",
            "product_title": "Iter40 Proof Regression",
        }
        r = requests.post(f"{API}/media-library/produce-proof",
                          headers=hdr, json=payload, timeout=240)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d.get("ok") is True
        assert isinstance(d.get("steps"), list) and len(d["steps"]) >= 5
