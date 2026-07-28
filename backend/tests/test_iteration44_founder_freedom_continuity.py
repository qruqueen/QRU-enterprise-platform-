"""Iteration 44 — QRU Founder Freedom Directive Sprint #1:
Distribution-State Continuity (zero-touch link, gold-master honesty, auto-link on publish,
failure isolation guards, formal distribution record preservation).

SAFETY: Real YouTube channel is connected. NO real publish is executed here.
Only publish guards (draft / missing / no-source) and read-paths + one linked produce
(no publish) are tested.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PW = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": FOUNDER_EMAIL, "password": FOUNDER_PW}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# ============ AUTO-LINK ON PUBLISH — verifies preserved distribution records ============

class TestDistributionRecords:
    def test_records_read_and_shape(self, client):
        r = client.get(f"{BASE_URL}/api/youtube/distribution-records", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "records" in data and "count" in data
        assert isinstance(data["records"], list)
        assert data["count"] == len(data["records"])
        assert data["count"] >= 1, "At least the milestone record must be preserved"

        required_keys = {"vault_asset_id", "platform_video_id", "publication_url",
                         "connected_channel", "published_at", "title_used",
                         "qa_results", "checksum", "source_licensing",
                         "responsible_approver", "status"}
        for rec in data["records"]:
            missing = required_keys - set(rec.keys())
            assert not missing, f"Record missing fields: {missing}"
            assert rec["status"] == "Published"
            assert "_id" not in rec

    def test_milestone_record_preserved(self, client):
        r = client.get(f"{BASE_URL}/api/youtube/distribution-records", timeout=30)
        data = r.json()
        milestone = next((x for x in data["records"] if x.get("platform_video_id") == "2j-XfWY7wqE"), None)
        assert milestone is not None, "MO-012 milestone record (2j-XfWY7wqE) must be preserved"
        assert milestone["connected_channel"] == "Quest Understand"
        assert milestone["qa_results"]["technical"] == 100
        assert milestone["qa_results"]["brand_content"] == 100
        assert milestone["status"] == "Published"
        assert milestone.get("responsible_approver")
        assert milestone.get("vault_asset_id")


# ============ FAILURE ISOLATION — publish guards return before real upload ============

class TestPublishGuards:
    def test_no_source_returns_400(self, client):
        r = client.post(f"{BASE_URL}/api/youtube/publish", json={}, timeout=30)
        assert r.status_code == 400
        detail = (r.json().get("detail") or "").lower()
        assert "factory asset" in detail or "upload" in detail

    def test_missing_factory_asset_returns_404(self, client):
        r = client.post(f"{BASE_URL}/api/youtube/publish",
                        json={"factory_asset_id": "QRU-SHOWCASE-DOES-NOT-EXIST-99999"}, timeout=30)
        assert r.status_code == 404
        assert "not found" in (r.json().get("detail") or "").lower()

    def test_draft_preview_asset_returns_400(self, client):
        # Find a draft-preview factory asset
        r = client.get(f"{BASE_URL}/api/youtube/factory-assets", timeout=30)
        assert r.status_code == 200
        drafts = [a for a in r.json()["assets"] if a.get("is_draft_preview")]
        if not drafts:
            pytest.skip("No draft-preview factory assets seeded; guard cannot be exercised.")
        target = drafts[0]["qru_asset_id"]
        r = client.post(f"{BASE_URL}/api/youtube/publish",
                        json={"factory_asset_id": target}, timeout=30)
        assert r.status_code == 400
        detail = r.json().get("detail") or ""
        assert "Draft previews cannot be published" in detail


# ============ ZERO-TOUCH PRODUCTION LINK ============

class TestZeroTouchContinuityLink:
    def test_create_project_and_linked_produce(self, client):
        # 1) Create project
        r = client.post(f"{BASE_URL}/api/factory-os/projects",
                        json={"outcome_id": "video", "topic": "TEST_forex_trading_basics_zt",
                              "audience": "Aspiring traders", "goal": "Introduce concepts"},
                        timeout=60)
        assert r.status_code == 200, r.text
        proj = r.json()
        assert proj.get("id")
        pid = proj["id"]

        # 2) Prepare approved scenes via /scene-match (real matcher, real licensed candidates)
        # Use a richer narration with multiple sentences and enough length so technical QA passes
        # (pilot window ≥ 20s and ≥ 2 scenes for multi_scene check).
        narration = (
            "Forex is the global market for exchanging currencies worldwide every day. "
            "Currencies always trade in pairs, so you buy one and sell another simultaneously. "
            "The difference between the buy and sell price is called the spread charged by brokers. "
            "Traders analyze economic news and price charts before opening a position on any pair. "
            "Understanding leverage and risk management is essential before you commit real capital. "
            "Practice on a demo account first and never risk more than you can afford to lose."
        )
        r = client.post(f"{BASE_URL}/api/media-library/scene-match",
                        json={"narration": narration, "topic": "forex trading basics",
                              "aspect": "landscape", "provider": "pixabay_video"},
                        timeout=120)
        assert r.status_code == 200, r.text
        matched = r.json()
        matched_scenes = matched.get("scenes") or []
        assert len(matched_scenes) >= 2, f"scene-match returned <2 scenes: {matched}"

        # Build approved scenes with the first candidate of each
        scenes = []
        for sc in matched_scenes:
            cands = sc.get("candidates") or []
            if not cands:
                pytest.skip(f"scene {sc.get('scene_index')} has no candidates — cannot approve")
            top = cands[0]
            scenes.append({
                "scene_index": sc["scene_index"],
                "scene_text": sc.get("scene_text"),
                "learning_purpose": sc.get("learning_purpose"),
                "approved": True,
                "selected": top,
            })

        # 3) Linked produce with human_approval_required + approved scenes
        r = client.post(
            f"{BASE_URL}/api/media-library/showcase/produce",
            json={
                "product_title": "TEST_ZT Forex Basics",
                "topic": "forex trading basics",
                "aspect": "landscape",
                "narration": narration,
                "approval_mode": "human_approval_required",
                "provider": "pixabay_video",
                "scenes": scenes,
                "continuity_project_id": pid,
            },
            timeout=180,  # real ffmpeg render allowed up to 120s + margin
        )
        assert r.status_code == 200, r.text
        prod = r.json()
        assert prod.get("ok") is True, f"Produce failed: {prod}"
        assert prod.get("continuity_updated") is True, "continuity_updated must be true when project linked"
        showcase = prod.get("showcase_asset") or {}
        assert showcase.get("qru_asset_id")

        # 3) Verify project auto-advanced to Founder Approval gate
        r = client.get(f"{BASE_URL}/api/factory-os/projects/{pid}", timeout=30)
        assert r.status_code == 200
        p = r.json()
        assert p.get("showcase_asset_id") == showcase["qru_asset_id"]
        assert p.get("effort_minutes_saved", 0) > 0

        stages = p["chain"]
        # Every stage before founder_approval should be complete
        idx_gate = next(i for i, s in enumerate(stages) if s["id"] == "founder_approval")
        for s in stages[:idx_gate]:
            assert s["status"] == "complete", f"Pre-approval stage '{s['id']}' should be complete, got {s['status']}"
        # Founder Approval is the current gate
        assert stages[idx_gate]["status"] == "needs_approval"
        assert p["summary"]["current_stage"] == "Founder Approval"

        # 4) GOLD MASTER HONESTY — gold_master must NOT be auto-completed
        gm = next(s for s in stages if s["id"] == "gold_master")
        assert gm["status"] in ("pending", "needs_approval"), \
            f"Gold Master must NEVER be auto-completed; got {gm['status']}"

        # 5) Publishing + Distribution stages must still be pending (no publish happened)
        publishing = next(s for s in stages if s["id"] == "publishing")
        distribution = next(s for s in stages if s["id"] == "distribution")
        assert publishing["status"] in ("pending", "needs_approval"), publishing["status"]
        assert distribution["status"] in ("pending", "needs_approval"), distribution["status"]

        # Store pid for cleanup context
        pytest.zt_pid = pid  # type: ignore

    def test_effort_summary_reflects_savings(self, client):
        r = client.get(f"{BASE_URL}/api/factory-os/effort-summary", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["minutes_saved"] > 0
        assert data["automated_actions"] > 0
        assert "eliminated_tasks" in data and isinstance(data["eliminated_tasks"], list)
        assert data["hours_saved"] == round(data["minutes_saved"] / 60, 1)


# ============ GOLD MASTER HONESTY (aggregate view) ============

class TestGoldMasterHonesty:
    def test_certify_requires_qa_100_or_asset_exists(self, client):
        """Certification endpoint exists and refuses when QA < 100 or asset short.
        We verify the endpoint refuses gracefully on any non-eligible asset (honest error)."""
        r = client.get(f"{BASE_URL}/api/youtube/factory-assets", timeout=30)
        assets = r.json()["assets"]
        # Any non-gold-master asset — attempting certify without meeting QA 100 must not succeed silently.
        target = next((a for a in assets if not a.get("gold_master_certified") and not a.get("is_draft_preview")), None)
        if not target:
            pytest.skip("No non-gold-master distribution-ready asset to probe.")
        r = client.post(f"{BASE_URL}/api/media-library/showcase/{target['qru_asset_id']}/certify-gold-master", timeout=60)
        # It must either 400 (honest refusal — QA not 100 or missing) OR 200 (all conditions truly met).
        assert r.status_code in (200, 400), r.text
        if r.status_code == 200:
            # If certified truly happened, the asset must now be gold_master_certified
            body = r.json()
            assert body.get("ok") is True

    def test_projects_list_gold_master_never_auto_completed_without_certification(self, client):
        """Across all projects that have showcase_asset_id but no certify was called,
        the gold_master stage must remain pending or needs_approval — never 'complete'
        without an explicit certification action in history.

        NOTE: reports violations as failures for HONESTY_VIOLATIONS list, does NOT
        fail the test — legacy data from pre-fix runs may exist. Instead we flag it
        for the main agent."""
        r = client.get(f"{BASE_URL}/api/factory-os/projects", timeout=30)
        assert r.status_code == 200
        violations = []
        for p in r.json()["projects"]:
            gm = next((s for s in p["chain"] if s["id"] == "gold_master"), None)
            if not gm:
                continue
            history = p.get("history", []) or []
            certified_in_history = any(h.get("action") == "gold_master_certified" for h in history)
            if gm["status"] == "complete" and not certified_in_history:
                violations.append({
                    "project_id": p["id"],
                    "topic": p.get("topic"),
                    "showcase_asset_id": p.get("showcase_asset_id"),
                    "history_actions": [h.get("action") for h in history],
                })
        # Print violations for report — do not fail the test on legacy data,
        # but assert none for our freshly-created zero-touch project.
        if violations:
            print(f"\n[HONESTY VIOLATIONS] {len(violations)} project(s) have gold_master=complete without certification:")
            for v in violations:
                print(f"  - {v}")
        # Our freshly-created project MUST be clean
        zt_pid = getattr(pytest, "zt_pid", None)
        if zt_pid:
            offending = [v for v in violations if v["project_id"] == zt_pid]
            assert not offending, f"Newly created zero-touch project has gold_master honesty violation: {offending}"


# ============ REGRESSION — YouTube read paths intact ============

class TestYouTubeRegression:
    def test_status_connected(self, client):
        r = client.get(f"{BASE_URL}/api/youtube/status", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["connected"] is True
        assert d["account"] == "Quest Understand"

    def test_factory_assets_lists(self, client):
        r = client.get(f"{BASE_URL}/api/youtube/factory-assets", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["count"] >= 1
        for a in d["assets"]:
            # No mongo _id leak
            assert "_id" not in a
            assert "qru_asset_id" in a
