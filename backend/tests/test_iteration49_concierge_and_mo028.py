"""Iteration 49 — MO-028 all-6-departments + cycle_log improvement AND Phase B Factory Concierge™.

Tests:
  A) MO-028 improvement — civilization_status now ALWAYS contains all 6 departments (idle→standby=true,
     progress=100, activity mentions 'Standing by'); response includes cycle_log[] with entries
     {cycle, department, dimension, from, to, delta, line} that record which dept raised which score.
  B) MO-028 honesty regression — when gold_master_candidate_ready=true, every NON-blocking + NON-standby
     department reports progress=100; sensitive topic without verified KR returns candidate=false +
     knowledge_verification blocked=true row.
  C) Factory Concierge™ — POST /api/factory-os/concierge/message (auth required) handles:
        (a) full request 'Create a video about forex trading for beginners' → stage='ready',
            slots.outcome_id='video', slots.topic≈'Forex Trading', audience='Beginner adult',
            can_launch=true, plan.knowledge_gap.knowledge_record_found=true.
        (b) partial 'I want to make a workbook' → stage='need_topic', outcome captured, no topic.
        (c) follow-up in SAME session_id 'about medieval basket weaving' → session accumulates,
            stage='knowledge_gap', can_launch=false, honest reply, no fabricated KR.
        (d) empty/hello → stage='need_outcome' + suggestions[] chips.
  D) Concierge session persistence — GET /api/factory-os/concierge/session/{sid}.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

DEPARTMENTS = {"creative_director", "design_intelligence", "director_intelligence",
               "learning_experience", "knowledge_verification", "qa"}


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD},
                      timeout=15)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="session")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ----------------------- MO-028 improvement tests -----------------------

WEAK_SCENES = [
    {"scene_text": "Intro to trading.", "learning_purpose": "hook", "match_score": 55},
    {"scene_text": "More talk about markets.", "learning_purpose": "concept", "match_score": 52},
    {"scene_text": "Recap of nothing much.", "learning_purpose": "recap", "match_score": 50},
]


class TestMO028AllSixDepartmentsAndCycleLog:
    """Improvement 1: civilization_status always has all 6 departments + cycle_log[] recorded."""

    def test_run_requiring_improvement_all_6_depts_and_cycle_log_populated(self, auth_headers):
        payload = {
            "scenes": WEAK_SCENES,
            "narration": "This video is about forex trading fundamentals for beginners.",
            "topic": "forex",
            "threshold": 95,
        }
        r = requests.post(f"{BASE_URL}/api/media-library/improvement-loop",
                          json=payload, headers=auth_headers, timeout=45)
        assert r.status_code == 200, f"loop failed: {r.status_code} {r.text}"
        data = r.json()

        # All 6 departments present in civilization_status
        cs = data.get("civilization_status", [])
        depts = {c["department"] for c in cs}
        assert depts == DEPARTMENTS, f"Expected all 6 departments, got {depts}"
        assert len(cs) == 6, f"Expected exactly 6 rows, got {len(cs)}"

        # Every row typed correctly and has standby flag
        for row in cs:
            assert "standby" in row, f"Row missing 'standby': {row}"
            assert isinstance(row["standby"], bool)
            assert isinstance(row["progress"], int) and 0 <= row["progress"] <= 100
            assert isinstance(row["blocked"], bool)
            assert isinstance(row["activity"], str) and row["activity"]
            if row["standby"]:
                assert row["progress"] == 100, "Standby dept must have progress=100"
                assert row["blocked"] is False, "Standby dept must not be blocked"
                assert "standing by" in row["activity"].lower(), \
                    f"Standby activity should mention 'Standing by': {row['activity']}"

        # cycle_log is present and populated for a weak-scene run
        cycle_log = data.get("cycle_log")
        assert isinstance(cycle_log, list), "cycle_log must be a list"
        assert len(cycle_log) > 0, "Weak-scene run at threshold=95 must produce cycle_log entries"
        for entry in cycle_log:
            for key in ("cycle", "department", "dimension", "from", "to", "delta", "line"):
                assert key in entry, f"cycle_log entry missing {key}: {entry}"
            assert entry["to"] >= entry["from"], "cycle_log 'to' must be >= 'from'"
            assert entry["delta"] == entry["to"] - entry["from"]
            assert entry["cycle"] >= 1
            assert isinstance(entry["line"], str) and entry["department"] in entry["line"]

    def test_passing_case_forex_all_nonblocking_nonstandby_progress_100(self, auth_headers):
        payload = {
            "scenes": [
                {"scene_text": "Strong hook — what is forex.", "learning_purpose": "hook", "match_score": 90},
                {"scene_text": "Clear explanation of pips and pairs.", "learning_purpose": "concept", "match_score": 92},
                {"scene_text": "Actionable recap and next step.", "learning_purpose": "recap", "match_score": 91},
            ],
            "narration": "Forex trading is the exchange of currencies. Beginners should learn pips, spreads and risk management.",
            "topic": "forex",
            "threshold": 85,
        }
        r = requests.post(f"{BASE_URL}/api/media-library/improvement-loop",
                          json=payload, headers=auth_headers, timeout=45)
        assert r.status_code == 200
        data = r.json()

        cs = data["civilization_status"]
        assert {c["department"] for c in cs} == DEPARTMENTS

        # Honesty: gold_master_candidate_ready → every non-blocking, non-standby dept @ 100
        if data.get("gold_master_candidate_ready"):
            for row in cs:
                if not row["blocked"] and not row.get("standby"):
                    assert row["progress"] == 100, \
                        f"Non-blocking non-standby dept must be @100 when candidate ready: {row}"

    def test_sensitive_topic_no_kr_returns_blocked_knowledge_verification(self, auth_headers):
        payload = {
            "scenes": WEAK_SCENES,
            "narration": "This video makes medical health claims about experimental protocols.",
            "topic": "obscure medical xyz zzz",
            "threshold": 95,
        }
        r = requests.post(f"{BASE_URL}/api/media-library/improvement-loop",
                          json=payload, headers=auth_headers, timeout=45)
        assert r.status_code == 200
        data = r.json()

        # Never claim gold master when knowledge is missing
        assert data["gold_master_candidate_ready"] is False
        assert data["blocking_count"] >= 1

        # All 6 depts still present
        cs = data["civilization_status"]
        assert {c["department"] for c in cs} == DEPARTMENTS

        # knowledge_verification row must be blocked
        kv = next(c for c in cs if c["department"] == "knowledge_verification")
        assert kv["blocked"] is True, f"knowledge_verification must be blocked when no KR: {kv}"


# ----------------------- Factory Concierge tests -----------------------

class TestFactoryConciergeAuth:
    def test_message_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/factory-os/concierge/message",
                          json={"message": "hello"}, timeout=15)
        assert r.status_code in (401, 403), f"Expected auth error, got {r.status_code}"


class TestFactoryConciergeFlow:
    """Phase B — deterministic parse + Knowledge-First check."""

    def test_a_full_request_video_forex_beginners_ready(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/factory-os/concierge/message",
                          json={"message": "Create a video about forex trading for beginners"},
                          headers=auth_headers, timeout=25)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        d = r.json()
        assert d["stage"] == "ready", f"Expected stage=ready, got {d['stage']}: {d.get('reply')}"
        assert d["slots"]["outcome_id"] == "video"
        assert "forex" in d["slots"]["topic"].lower(), f"topic mismatch: {d['slots']['topic']}"
        assert "trading" in d["slots"]["topic"].lower()
        assert d["slots"]["audience"] == "Beginner adult", f"audience: {d['slots']['audience']}"
        assert d["can_launch"] is True
        assert d["plan"] is not None
        assert d["plan"]["knowledge_gap"]["knowledge_record_found"] is True
        assert d["plan"]["launch"]["workflow"]  # workflow string present
        assert d["session_id"]

    def test_b_partial_workbook_need_topic(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/factory-os/concierge/message",
                          json={"message": "I want to make a workbook"},
                          headers=auth_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["stage"] == "need_topic", f"Expected need_topic, got {d['stage']}"
        assert d["slots"]["outcome_id"] == "workbook"
        assert not d["slots"]["topic"]
        assert d["can_launch"] is False
        assert d["plan"] is None

    def test_c_followup_same_session_knowledge_gap(self, auth_headers):
        # Turn 1 — create session with outcome only
        r1 = requests.post(f"{BASE_URL}/api/factory-os/concierge/message",
                           json={"message": "I want to make a workbook"},
                           headers=auth_headers, timeout=15)
        assert r1.status_code == 200
        sid = r1.json()["session_id"]

        # Turn 2 — same session, add topic that has no verified KR
        r2 = requests.post(f"{BASE_URL}/api/factory-os/concierge/message",
                           json={"message": "about medieval basket weaving", "session_id": sid},
                           headers=auth_headers, timeout=15)
        assert r2.status_code == 200
        d = r2.json()
        assert d["session_id"] == sid, "Session must persist"
        assert d["slots"]["outcome_id"] == "workbook", "Outcome slot must accumulate"
        assert d["slots"]["topic"], f"Topic must be captured: {d['slots']}"
        assert "basket" in d["slots"]["topic"].lower() or "weaving" in d["slots"]["topic"].lower()
        assert d["stage"] == "knowledge_gap", f"Expected knowledge_gap, got {d['stage']}"
        assert d["can_launch"] is False
        assert d["plan"] is not None
        assert d["plan"]["knowledge_gap"]["knowledge_record_found"] is False
        # Honest reply — must NEVER fabricate a KR
        reply_l = d["reply"].lower()
        assert "knowledge record" in reply_l or "knowledge manufacturing" in reply_l, \
            f"Reply should honestly reference KR / pipeline: {d['reply']}"
        # Offer to begin the pipeline present in plan
        offer = d["plan"]["knowledge_gap"].get("offer") or {}
        assert offer.get("action") == "begin_knowledge_manufacturing" or offer.get("label")

    def test_d_no_outcome_returns_need_outcome_with_suggestions(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/factory-os/concierge/message",
                          json={"message": "hello"},
                          headers=auth_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["stage"] == "need_outcome"
        assert isinstance(d["suggestions"], list) and len(d["suggestions"]) > 0
        for s in d["suggestions"]:
            assert "label" in s and "value" in s and "outcome_id" in s
        assert d["can_launch"] is False

    def test_d2_empty_message_returns_need_outcome(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/factory-os/concierge/message",
                          json={"message": ""},
                          headers=auth_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["stage"] == "need_outcome"
        assert len(d["suggestions"]) > 0


class TestFactoryConciergeSessionPersistence:
    def test_get_session_returns_accumulated_messages_and_slots(self, auth_headers):
        # Create session
        r1 = requests.post(f"{BASE_URL}/api/factory-os/concierge/message",
                           json={"message": "Create a video about forex trading for beginners"},
                           headers=auth_headers, timeout=25)
        assert r1.status_code == 200
        sid = r1.json()["session_id"]

        # Fetch it back
        r2 = requests.get(f"{BASE_URL}/api/factory-os/concierge/session/{sid}",
                          headers=auth_headers, timeout=15)
        assert r2.status_code == 200, f"{r2.status_code} {r2.text}"
        s = r2.json()
        assert s["session_id"] == sid
        assert isinstance(s.get("messages"), list) and len(s["messages"]) >= 2
        # Slots preserved
        assert s["slots"]["outcome_id"] == "video"
        assert "forex" in s["slots"]["topic"].lower()

    def test_get_session_unknown_returns_404(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/factory-os/concierge/session/definitely_not_a_real_sid_zzz",
                         headers=auth_headers, timeout=15)
        assert r.status_code == 404
