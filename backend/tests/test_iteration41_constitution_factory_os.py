"""Iteration 41 — QRU Factory™ Constitution (QRU-CON-0001) adoption + Factory OS Phase A (Create).

Backend contract tests for:
  * GET  /api/governance/factory-constitution
  * GET  /api/governance/factory-constitution/bindings
  * GET  /api/factory-os/outcomes
  * POST /api/factory-os/knowledge-gap-check
  * POST /api/factory-os/plan
  * (regression) GET /api/media-library/showcase/modes
"""
import os
import pytest
import requests

def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    # Fallback: read from /app/frontend/.env
    try:
        with open("/app/frontend/.env", "r") as f:
            for ln in f:
                if ln.strip().startswith("REACT_APP_BACKEND_URL="):
                    return ln.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    raise RuntimeError("REACT_APP_BACKEND_URL not found in env or /app/frontend/.env")


BASE_URL = _load_backend_url()
FOUNDER = {"email": "22j2rsdzb8@privaterelay.appleid.com", "password": "QruFounder2026!"}

EXACT_GAP_MESSAGE = "This topic has not yet been manufactured as a governed QRU Knowledge Record\u2122."


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=FOUNDER, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="session")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# -------------------- Constitution --------------------
class TestConstitution:
    def test_get_constitution(self, client):
        r = client.get(f"{BASE_URL}/api/governance/factory-constitution", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["doc_id"] == "QRU-CON-0001"
        assert d["version"] == "1.0"
        assert d["status"] == "Founder Approved"
        assert d["authority_level"] == "Foundational"
        assert isinstance(d["sections"], list) and len(d["sections"]) == 14
        # Verify sections carry n + title + summary and are 1..14
        ns = [s["n"] for s in d["sections"]]
        assert ns == [str(i) for i in range(1, 15)]
        for s in d["sections"]:
            assert s["title"] and s["summary"]
        assert isinstance(d["full_text"], str) and len(d["full_text"]) > 500
        assert isinstance(d["product_statuses"], list) and len(d["product_statuses"]) == 12
        assert isinstance(d["quality_gates"], list) and len(d["quality_gates"]) == 4
        assert isinstance(d["automation_modes"], list) and len(d["automation_modes"]) == 3
        # Full text must be a verbatim record (no _id leakage)
        assert "_id" not in d

    def test_constitution_bindings(self, client):
        r = client.get(f"{BASE_URL}/api/governance/factory-constitution/bindings", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["constitution"]["adopted"] is True
        assert d["constitution"]["doc_id"] == "QRU-CON-0001"
        assert isinstance(d["bindings"], list) and len(d["bindings"]) == 9
        for b in d["bindings"]:
            assert b["system"] and b["why"]
            assert isinstance(b["section_titles"], list) and len(b["section_titles"]) >= 1
            # Section titles are formatted as "§n Title"
            for t in b["section_titles"]:
                assert t.startswith("\u00a7")
        assert "acceptance_note" in d and d["acceptance_note"]


# -------------------- Factory OS outcomes --------------------
class TestFactoryOSOutcomes:
    def test_outcomes(self, client):
        r = client.get(f"{BASE_URL}/api/factory-os/outcomes", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["operating_question"] == "What would you like to create today?"
        assert isinstance(d["outcomes"], list) and len(d["outcomes"]) == 11
        ids = {o["id"] for o in d["outcomes"]}
        for oid in ["video", "workbook", "poster", "presentation", "assessment",
                    "knowledge_card", "book", "course", "podcast", "audiobook", "bundle"]:
            assert oid in ids
        for o in d["outcomes"]:
            assert o["name"] and o["icon"] and o["description"]
            assert o["route"] and o["workflow"] and o["maturity_label"]
        video = next(o for o in d["outcomes"] if o["id"] == "video")
        assert video["route"] == "/flagship-showcase"
        assert video["maturity_label"] == "Gold Master Ready"
        # Legend present
        assert isinstance(d["maturity_legend"], dict) and len(d["maturity_legend"]) >= 5


# -------------------- Knowledge-Gap Check --------------------
class TestKnowledgeGapCheck:
    def test_gap_found_forex(self, client):
        r = client.post(f"{BASE_URL}/api/factory-os/knowledge-gap-check",
                        json={"topic": "forex trading basics", "goal": "understand currency risk"}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["knowledge_record_found"] is True
        kr = d["knowledge_record"]
        assert kr["kr_code"] and kr["title"]
        assert kr["kr_code"] in ("KR-00048", "KR-00075") or "forex" in (kr["title"] or "").lower() or "trading" in (kr["title"] or "").lower()
        # Message shape
        assert d["message"].startswith("Approved Knowledge Record found:")
        assert kr["kr_code"] in d["message"]

    def test_gap_not_found_obscure(self, client):
        r = client.post(f"{BASE_URL}/api/factory-os/knowledge-gap-check",
                        json={"topic": "quantum basket weaving on mars", "goal": ""}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["knowledge_record_found"] is False
        # EXACT honesty message per Constitution §3.1
        assert d["message"] == EXACT_GAP_MESSAGE
        offer = d.get("offer") or {}
        assert offer.get("route") == "/promotion-pipeline"
        assert offer.get("action") == "begin_knowledge_manufacturing"
        # Never fabricate a KR
        assert "knowledge_record" not in d or not d.get("knowledge_record")


# -------------------- Factory OS Plan --------------------
class TestFactoryOSPlan:
    def test_plan_video_forex_can_launch(self, client):
        payload = {"outcome_id": "video", "topic": "forex trading basics",
                   "audience": "beginner adult", "goal": "understand currency risk"}
        r = client.post(f"{BASE_URL}/api/factory-os/plan", json=payload, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["can_launch"] is True
        assert d["launch"]["route"] == "/flagship-showcase"
        gov = d["governed_by"]
        # video sections = 3, 6, 9, 10
        for s in ["QRU-CON-0001 \u00a73", "QRU-CON-0001 \u00a76",
                  "QRU-CON-0001 \u00a79", "QRU-CON-0001 \u00a710"]:
            assert s in gov
        assert isinstance(d["steps"], list) and len(d["steps"]) == 8
        g = d["guidance"]
        for key in ["where_am_i", "what_am_i_creating", "whats_happening_now",
                    "what_happens_next", "what_needs_my_approval",
                    "where_is_my_product", "how_do_i_publish"]:
            assert key in g and g[key]
        # KR gate resolved
        kg = d["knowledge_gap"]
        assert kg["knowledge_record_found"] is True

    def test_plan_no_kr_blocks_launch(self, client):
        payload = {"outcome_id": "video", "topic": "quantum basket weaving on mars",
                   "audience": "beginner adult", "goal": ""}
        r = client.post(f"{BASE_URL}/api/factory-os/plan", json=payload, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["can_launch"] is False
        # guidance next mentions the Knowledge Manufacturing Pipeline
        assert "knowledge" in d["guidance"]["what_happens_next"].lower()
        assert d["knowledge_gap"]["knowledge_record_found"] is False
        assert d["knowledge_gap"]["message"] == EXACT_GAP_MESSAGE

    def test_plan_unknown_outcome(self, client):
        r = client.post(f"{BASE_URL}/api/factory-os/plan",
                        json={"outcome_id": "nonexistent", "topic": "x"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d.get("ok") is False
        assert "error" in d


# -------------------- Regression --------------------
class TestRegression:
    def test_showcase_modes(self, client):
        r = client.get(f"{BASE_URL}/api/media-library/showcase/modes", timeout=20)
        assert r.status_code == 200
        d = r.json()
        modes = d.get("approval_modes") or d.get("modes") or []
        assert len(modes) == 3
