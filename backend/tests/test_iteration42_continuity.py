"""Iteration 42 — QRU Factory™ Product Continuity Principle™ (Constitution QRU-CON-0001 §4 / §14G).

Validates:
  1. POST /api/factory-os/projects — creation with auto_continue mode, 11-stage chain,
     KR auto-complete when verified KR exists, auto-advance to first workflow stage.
  2. Obscure topic (no verified KR) — KR stage is 'blocked' with '/promotion-pipeline' route.
  3. Auto-continuation + gates lifecycle: complete-stage x N → auto-complete auto stages →
     STOP at 'Founder Approval' gate (needs_approval); approve → STOP at 'Gold Master' gate;
     approve → Vault auto-complete → Publishing 'blocked' (honesty: never faked as published).
  4. Pause / Resume / Stop; invalid mode → 400.
  5. LIST + GET, and 404 on bad id.
  6. Regression: /outcomes and /plan unchanged.
"""
import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# ---------------- CREATE PROJECT ----------------
class TestCreateProject:
    def test_create_video_project_forex_auto_kr_and_advance(self, client):
        r = client.post(
            f"{BASE_URL}/api/factory-os/projects",
            json={"outcome_id": "video", "topic": "forex trading basics", "audience": "beginner adult"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        p = r.json()
        # Must not leak MongoDB _id
        assert "_id" not in p
        assert p.get("id") and isinstance(p["id"], str)
        assert p["outcome_id"] == "video"
        assert p["mode"] == "auto_continue"

        # 11-stage chain for video
        chain = p["chain"]
        assert isinstance(chain, list) and len(chain) == 11
        # First stage KR auto-completed (verified KR exists — KR-00048/KR-00075)
        assert chain[0]["id"] == "knowledge_record"
        assert chain[0]["status"] == "complete", f"KR stage should be complete, got {chain[0]}"
        # Auto-advanced to first workflow stage — 'Video Script & Narration' in_progress
        assert chain[1]["id"] == "video_script"
        assert chain[1]["status"] == "in_progress"
        # All later stages still pending
        for s in chain[2:]:
            assert s["status"] == "pending"

        # Summary
        s = p["summary"]
        assert s["current_stage"] == "Video Script & Narration"
        assert s["current_stage_status"] == "in_progress"
        assert isinstance(s["remaining_stages"], list) and len(s["remaining_stages"]) == 10
        assert s["recommended_next_action"]
        assert isinstance(s["percent"], int) and 0 <= s["percent"] <= 100

        # Persist id for downstream classes (module-level attribute)
        TestCreateProject.forex_pid = p["id"]

    def test_create_video_project_obscure_topic_blocked_kr(self, client):
        r = client.post(
            f"{BASE_URL}/api/factory-os/projects",
            json={"outcome_id": "video", "topic": "quantum basket weaving on mars", "audience": "general public"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        p = r.json()
        # Some plans may return can_launch=false with ok=false — but continuity.create_project only runs when plan.ok
        # The backend returns the plan directly in that case
        if not p.get("chain"):
            # Plan-fail short-circuit path
            assert p.get("ok") is False or p.get("can_launch") is False
            return
        chain = p["chain"]
        # KR stage should be blocked with /promotion-pipeline route
        assert chain[0]["id"] == "knowledge_record"
        assert chain[0]["status"] == "blocked", f"KR should be blocked for obscure topic, got {chain[0]}"
        assert chain[0].get("route") == "/promotion-pipeline"
        # Subsequent stages should stay pending
        for s in chain[1:]:
            assert s["status"] == "pending"


# ---------------- FULL LIFECYCLE: workflow → gates → publishing blocked ----------------
class TestLifecycle:
    @pytest.fixture(scope="class")
    def pid(self, client):
        r = client.post(
            f"{BASE_URL}/api/factory-os/projects",
            json={"outcome_id": "video", "topic": "forex trading basics", "audience": "beginner adult"},
            timeout=15,
        )
        assert r.status_code == 200
        return r.json()["id"]

    def test_walk_workflow_stages_then_founder_approval_gate(self, client, pid):
        # 3 workflow stages: video_script, scene_matching, assembly
        for expected_next in ["scene_matching", "assembly", None]:
            r = client.post(f"{BASE_URL}/api/factory-os/projects/{pid}/complete-stage", timeout=15)
            assert r.status_code == 200, r.text
            p = r.json()
            cur = next((s for s in p["chain"] if s["status"] in ("in_progress", "needs_approval", "blocked")), None)
            assert cur is not None
            if expected_next:
                assert cur["id"] == expected_next, f"Expected {expected_next}, got {cur}"
                assert cur["status"] == "in_progress"
            else:
                # After 3rd workflow complete → auto-completes thumbnail_metadata + quality_review → STOP at founder_approval gate
                assert cur["id"] == "founder_approval"
                assert cur["status"] == "needs_approval"
                assert p["summary"]["current_stage_status"] == "needs_approval"
                assert "approval" in p["summary"]["recommended_next_action"].lower()

        # Verify auto stages were completed
        r = client.get(f"{BASE_URL}/api/factory-os/projects/{pid}", timeout=15)
        assert r.status_code == 200
        p = r.json()
        by_id = {s["id"]: s for s in p["chain"]}
        assert by_id["thumbnail_metadata"]["status"] == "complete"
        assert by_id["quality_review"]["status"] == "complete"

    def test_approve_founder_gate_then_gold_master_gate(self, client, pid):
        r = client.post(f"{BASE_URL}/api/factory-os/projects/{pid}/approve", timeout=15)
        assert r.status_code == 200
        p = r.json()
        by_id = {s["id"]: s for s in p["chain"]}
        assert by_id["founder_approval"]["status"] == "complete"
        assert by_id["gold_master"]["status"] == "needs_approval"
        assert p["summary"]["current_stage"] == "Gold Master Certified™"
        assert p["summary"]["current_stage_status"] == "needs_approval"

    def test_approve_gold_master_then_publishing_blocked_honesty(self, client, pid):
        r = client.post(f"{BASE_URL}/api/factory-os/projects/{pid}/approve", timeout=15)
        assert r.status_code == 200
        p = r.json()
        by_id = {s["id"]: s for s in p["chain"]}
        # Gold master approved
        assert by_id["gold_master"]["status"] == "complete"
        # Vault auto-completed
        assert by_id["vault"]["status"] == "complete", "Vault (auto) should be complete after approving gold master"
        # Publishing is 'blocked' — HONESTY: never faked as complete
        assert by_id["publishing"]["status"] == "blocked", \
            f"Publishing MUST be blocked (needs connector), not complete. Got {by_id['publishing']}"
        # Distribution not complete either
        assert by_id["distribution"]["status"] != "complete"
        # Recommended next action mentions setup / destination
        rec = p["summary"]["recommended_next_action"].lower()
        assert "connector" in rec or "destination" in rec or "set up" in rec, \
            f"Recommendation should mention setup: {rec}"

    def test_publishing_never_complete_via_repeated_complete_stage(self, client, pid):
        # HONESTY guarantee: even if operator hits complete-stage repeatedly, connector stays blocked
        for _ in range(3):
            r = client.post(f"{BASE_URL}/api/factory-os/projects/{pid}/complete-stage", timeout=15)
            assert r.status_code == 200
        r = client.get(f"{BASE_URL}/api/factory-os/projects/{pid}", timeout=15)
        p = r.json()
        by_id = {s["id"]: s for s in p["chain"]}
        assert by_id["publishing"]["status"] != "complete"
        assert by_id["distribution"]["status"] != "complete"


# ---------------- PAUSE / RESUME / STOP ----------------
class TestModeControl:
    @pytest.fixture(scope="class")
    def pid(self, client):
        r = client.post(
            f"{BASE_URL}/api/factory-os/projects",
            json={"outcome_id": "video", "topic": "forex trading basics", "audience": "beginner adult"},
            timeout=15,
        )
        return r.json()["id"]

    def test_pause(self, client, pid):
        r = client.post(f"{BASE_URL}/api/factory-os/projects/{pid}/mode", json={"mode": "paused"}, timeout=15)
        assert r.status_code == 200
        p = r.json()
        assert p["mode"] == "paused"
        assert "paused" in p["summary"]["recommended_next_action"].lower()

    def test_resume_auto_continue(self, client, pid):
        r = client.post(f"{BASE_URL}/api/factory-os/projects/{pid}/mode", json={"mode": "auto_continue"}, timeout=15)
        assert r.status_code == 200
        p = r.json()
        assert p["mode"] == "auto_continue"
        # Should re-advance to a workflow/gate stage (not paused)
        assert "paused" not in p["summary"]["recommended_next_action"].lower()

    def test_stop(self, client, pid):
        r = client.post(f"{BASE_URL}/api/factory-os/projects/{pid}/mode", json={"mode": "stopped"}, timeout=15)
        assert r.status_code == 200
        p = r.json()
        assert p["mode"] == "stopped"

    def test_invalid_mode_returns_400(self, client, pid):
        r = client.post(f"{BASE_URL}/api/factory-os/projects/{pid}/mode", json={"mode": "yolo"}, timeout=15)
        assert r.status_code == 400


# ---------------- LIST + GET ----------------
class TestListAndGet:
    def test_list_projects(self, client):
        r = client.get(f"{BASE_URL}/api/factory-os/projects", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "projects" in data and isinstance(data["projects"], list)
        assert len(data["projects"]) >= 1
        for p in data["projects"]:
            assert "summary" in p
            assert "_id" not in p  # No Mongo id leak
            assert "chain" in p and isinstance(p["chain"], list)

    def test_get_bad_id_404(self, client):
        r = client.get(f"{BASE_URL}/api/factory-os/projects/does-not-exist-abc123", timeout=15)
        assert r.status_code == 404


# ---------------- REGRESSION ----------------
class TestRegression:
    def test_outcomes(self, client):
        r = client.get(f"{BASE_URL}/api/factory-os/outcomes", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "outcomes" in d and len(d["outcomes"]) >= 11
        assert d.get("operating_question")

    def test_plan(self, client):
        r = client.post(
            f"{BASE_URL}/api/factory-os/plan",
            json={"outcome_id": "video", "topic": "forex trading basics", "audience": "beginner adult"},
            timeout=15,
        )
        assert r.status_code == 200
        d = r.json()
        assert d.get("ok") is True
        assert d.get("can_launch") is True
        assert d.get("launch", {}).get("route") == "/flagship-showcase"
