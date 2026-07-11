"""MO-028 Autonomous Improvement Loop™ — backend contract & honesty tests.

Verifies POST /api/media-library/improvement-loop:
- Case A (passing, non-blocked): well-formed non-sensitive topic reaches gold_master_candidate_ready=true;
  every non-blocking department has progress=100 and blocked=false; no department stuck at 0%.
- Case B (sensitive, blocked): sensitive topic with NO verified Knowledge Record returns
  gold_master_candidate_ready=false, blocking_count>=1, and Knowledge Verification™ blocked=true.
- Threshold clamping between 70 and 98.
- Response contract: cycles[], work_orders[], civilization_status[], honest_note, notification.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=90)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    d = r.json()
    tok = d.get("access_token") or d.get("token")
    assert tok, f"No token in login response: {d}"
    return tok


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    # Wrap post with a generous default timeout to handle warm-cold requests.
    _orig_post = s.post
    def _post(url, **kw):
        kw.setdefault("timeout", 90)
        return _orig_post(url, **kw)
    s.post = _post
    return s


def _scenes_forex():
    return [
        {"scene_text": "Forex means trading the world's currencies across global markets.",
         "learning_purpose": "Hook", "match_score": 88},
        {"scene_text": "Every trade carries real risk of loss that you must respect.",
         "learning_purpose": "Risk framing", "match_score": 86},
        {"scene_text": "Understanding how currency pairs move takes patient study and practice.",
         "learning_purpose": "Reinforcement", "match_score": 90},
        {"scene_text": "Learning to trade responsibly builds lasting confidence over time.",
         "learning_purpose": "Closing CTA", "match_score": 92},
    ]


def _scenes_generic():
    return [
        {"scene_text": "Welcome — a slow calm morning routine can shape the whole day.",
         "learning_purpose": "Hook", "match_score": 90},
        {"scene_text": "Small daily habits add up to lasting personal growth and clarity.",
         "learning_purpose": "Reinforcement", "match_score": 92},
        {"scene_text": "Take a slow breath and reflect on your progress with gratitude.",
         "learning_purpose": "Closing CTA", "match_score": 93},
    ]


# ---------------- Contract shape ----------------
class TestContract:
    def test_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/media-library/improvement-loop",
                          json={"scenes": _scenes_generic(), "topic": "wellness", "threshold": 85}, timeout=90)
        assert r.status_code in (401, 403), f"Expected 401/403 without auth, got {r.status_code}"

    def test_response_shape(self, client):
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_generic(), "narration": "A calm morning routine.",
                              "topic": "wellness", "threshold": 85})
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("cycles", "work_orders", "civilization_status", "baseline_composite", "final_composite",
                  "threshold", "gold_master_candidate_ready", "blocking_count", "notification", "honest_note"):
            assert k in d, f"Missing field: {k}"
        assert isinstance(d["cycles"], list) and len(d["cycles"]) >= 1
        assert isinstance(d["work_orders"], list)
        assert isinstance(d["civilization_status"], list) and len(d["civilization_status"]) >= 1
        for cs in d["civilization_status"]:
            for k in ("department", "department_name", "activity", "progress", "blocked"):
                assert k in cs, f"civilization_status missing {k}: {cs}"
            assert isinstance(cs["blocked"], bool)
            assert isinstance(cs["progress"], int)
            assert 0 <= cs["progress"] <= 100

    def test_threshold_clamps_low(self, client):
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_generic(), "topic": "wellness", "threshold": 30})
        assert r.status_code == 200, r.text
        assert r.json()["threshold"] == 70

    def test_threshold_clamps_high(self, client):
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_generic(), "topic": "wellness", "threshold": 500})
        assert r.status_code == 200, r.text
        assert r.json()["threshold"] == 98

    def test_final_composite_within_bounds(self, client):
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_generic(), "topic": "wellness", "threshold": 85})
        d = r.json()
        assert 0 <= d["final_composite"] <= 100
        assert 0 <= d["baseline_composite"] <= 100
        # ceilings across ROUTING max out at 98, so composite must stay <= 98
        assert d["final_composite"] <= 98


# ---------------- Case A: passing (non-blocked) ----------------
class TestCaseA_Passing:
    def test_forex_reaches_gold_master(self, client):
        # 'forex' is treated as sensitive; but a verified KR for forex is expected to exist
        # in the seeded factory (so knowledge_verification is NOT blocked). Threshold 85.
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_forex(),
                              "narration": ("Forex means trading currencies. Every trade carries real risk of loss "
                                            "that you must respect. Learning to trade responsibly builds confidence."),
                              "topic": "forex", "threshold": 85})
        assert r.status_code == 200, r.text
        d = r.json()
        # Contract: candidate ready
        assert d["gold_master_candidate_ready"] is True, (
            f"Expected gold_master_candidate_ready=true for forex@85. blocking={d['blocking_count']} "
            f"final={d['final_composite']} threshold={d['threshold']} note={d.get('notification')}")
        assert d["blocking_count"] == 0
        assert d["final_composite"] >= d["threshold"]
        # Honesty: no non-blocking department may be stuck at 0% when candidate is ready.
        for cs in d["civilization_status"]:
            if not cs["blocked"]:
                assert cs["progress"] == 100, (
                    f"Department {cs['department']} shows progress={cs['progress']} while candidate is READY. "
                    f"This violates MO-028 honesty (fix: run_loop must upgrade non-blocking depts to 100 when "
                    f"gold_candidate or ceiling met).")
                assert cs["blocked"] is False

    def test_generic_wellness_reaches_gold_master(self, client):
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_generic(),
                              "narration": "A calm morning routine builds daily clarity and gratitude.",
                              "topic": "wellness", "threshold": 85})
        d = r.json()
        assert d["gold_master_candidate_ready"] is True, (
            f"Non-sensitive wellness@85 should be candidate ready; got final={d['final_composite']} "
            f"blocking={d['blocking_count']}")
        # Every non-blocking department shows 100
        for cs in d["civilization_status"]:
            if not cs["blocked"]:
                assert cs["progress"] == 100, f"Dept {cs['department']} at {cs['progress']}% while candidate ready"

    def test_notification_and_actions_when_ready(self, client):
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_generic(), "topic": "wellness", "threshold": 85})
        d = r.json()
        if d["gold_master_candidate_ready"]:
            assert "Gold Master Candidate ready" in d["notification"]
            assert d.get("founder_actions") == ["YES", "REQUEST CHANGES", "PUBLISH"]


# ---------------- Case B: blocking (sensitive + no verified KR) ----------------
class TestCaseB_Blocking:
    def test_sensitive_topic_no_kr_is_blocked(self, client):
        # Use a totally obscure sensitive topic guaranteed to not have a verified KR
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_generic(),
                              "narration": ("This video explains medical health claims about an obscure "
                                            "experimental treatment protocol without a verified source."),
                              "topic": "obscure medical xyz zzz protocol",
                              "threshold": 95})
        assert r.status_code == 200, r.text
        d = r.json()
        # HONEST: must NOT falsely certify
        assert d["gold_master_candidate_ready"] is False, (
            "Sensitive topic without verified KR must NOT be certified as Gold Master Candidate.")
        assert d["blocking_count"] >= 1, "Expected at least one blocking work order for sensitive medical topic"

        # Knowledge Verification™ must be blocked=true
        kv = [c for c in d["civilization_status"] if c["department"] == "knowledge_verification"]
        assert kv, "Knowledge Verification department must appear in civilization_status when sensitive+no KR"
        assert kv[0]["blocked"] is True, f"Knowledge Verification must be blocked=true, got {kv[0]}"

        # Blocking work orders must exist
        blocking_wos = [w for w in d["work_orders"] if w.get("blocking")]
        assert len(blocking_wos) >= 1
        for w in blocking_wos:
            assert w["department"] == "knowledge_verification"
            assert "verified Knowledge Record" in w.get("resolution", "") or "governance" in w.get("resolution", "").lower()

        # Notification should not claim Gold Master Candidate ready
        assert "Gold Master Candidate ready" not in d["notification"]
        # honest_note always present
        assert d["honest_note"] and "never faked" in d["honest_note"]

    def test_qa_reflects_block(self, client):
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_generic(),
                              "narration": "Medical health claims about obscure experimental protocol.",
                              "topic": "obscure medical xyz zzz protocol",
                              "threshold": 95})
        d = r.json()
        qa = [c for c in d["civilization_status"] if c["department"] == "qa"]
        assert qa, "QA row must be present in civilization_status"
        # When blocking exists, QA cannot show 100% Complete honestly
        assert qa[0]["blocked"] is True or qa[0]["progress"] < 100


# ---------------- Cycles & work orders ----------------
class TestCyclesAndWorkOrders:
    def test_cycles_monotonic(self, client):
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_generic(), "topic": "wellness", "threshold": 95})
        d = r.json()
        composites = [c["composite"] for c in d["cycles"]]
        # composite should be non-decreasing across cycles (improvements only add)
        for i in range(1, len(composites)):
            assert composites[i] >= composites[i - 1] - 1, (
                f"Composite went down cycle {i-1}->{i}: {composites}")
        assert d["final_composite"] == composites[-1]
        assert d["baseline_composite"] == composites[0]

    def test_work_orders_have_department_assignment(self, client):
        r = client.post(f"{BASE_URL}/api/media-library/improvement-loop",
                        json={"scenes": _scenes_generic(), "topic": "wellness", "threshold": 90})
        d = r.json()
        valid_depts = {"creative_director", "design_intelligence", "director_intelligence",
                       "learning_experience", "knowledge_verification", "qa"}
        for w in d["work_orders"]:
            assert w["department"] in valid_depts
            assert w["department_name"]
            assert isinstance(w["blocking"], bool)
            assert 0 <= w["progress"] <= 100
            assert w["status"]
