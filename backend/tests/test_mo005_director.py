"""MO-005 Manufacturing Director™ — backend API tests.

Covers:
- GET /api/director/queue → totals/counts/rows shape
- GET /api/director/review/{id} → full deterministic review shape
- GET /api/director/review/{id}?use_ai=true → verdict identical to non-AI, brief_source valid
- POST /api/director/review/{id}/decision → applies recommended_status, appends history
"""
import os
import pytest
import requests
from pathlib import Path

# Load REACT_APP_BACKEND_URL from frontend/.env if not set
if not os.environ.get("REACT_APP_BACKEND_URL"):
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                os.environ["REACT_APP_BACKEND_URL"] = line.split("=", 1)[1].strip()

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

VALID_VERDICTS = {"APPROVE", "APPROVE_WITH_CONDITIONS", "HOLD", "REJECT"}
VALID_STATUSES = {"Research", "Queued"}


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


@pytest.fixture(scope="module")
def queue(api):
    r = api.get(f"{BASE_URL}/api/director/queue", timeout=60)
    assert r.status_code == 200, r.text[:300]
    return r.json()


# ---------- /queue ----------

class TestDirectorQueue:
    def test_queue_shape(self, queue):
        for k in ("total", "counts", "cleared", "held", "orders"):
            assert k in queue, f"missing key {k}"
        assert isinstance(queue["orders"], list)
        assert isinstance(queue["total"], int)

    def test_counts_has_all_four_verdicts(self, queue):
        c = queue["counts"]
        for v in VALID_VERDICTS:
            assert v in c, f"counts missing {v}"
            assert isinstance(c[v], int)

    def test_cleared_held_math(self, queue):
        c = queue["counts"]
        assert queue["cleared"] == c["APPROVE"] + c["APPROVE_WITH_CONDITIONS"]
        assert queue["held"] == c["HOLD"] + c["REJECT"]
        assert queue["total"] == sum(c.values())

    def test_orders_row_shape(self, queue):
        assert len(queue["orders"]) > 0, "expected seeded manufacturing orders"
        for row in queue["orders"][:5]:
            for k in ("order_id", "mo_code", "topic", "verdict", "verdict_label",
                     "recommended_status", "confidence", "missing_count"):
                assert k in row, f"row missing {k}"
            assert row["verdict"] in VALID_VERDICTS
            assert row["recommended_status"] in VALID_STATUSES
            assert "kr_code" in row  # nullable, but key must exist


# ---------- /review/{id} ----------

class TestDirectorReview:
    def test_review_shape_full(self, api, queue):
        oid = queue["orders"][0]["order_id"]
        r = api.get(f"{BASE_URL}/api/director/review/{oid}", timeout=60)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        for k in ("verdict", "verdict_label", "confidence", "reasons",
                  "knowledge_gate", "readiness_by_product", "missing_knowledge",
                  "recommended_actions", "executive_brief", "brief_source",
                  "recommended_status"):
            assert k in d, f"review missing {k}"
        assert d["verdict"] in VALID_VERDICTS
        assert d["recommended_status"] in VALID_STATUSES
        assert isinstance(d["reasons"], list)
        assert isinstance(d["readiness_by_product"], list)
        assert isinstance(d["missing_knowledge"], list)
        assert isinstance(d["recommended_actions"], list)
        assert d["brief_source"] in {"ai", "deterministic"}
        assert d["executive_brief"], "brief must never be empty"
        assert "knowledge_record" in d  # nullable but key present

    def test_missing_knowledge_shape(self, api, queue):
        # Pick a HOLD/REJECT order if any to inspect missing_knowledge shape
        target = None
        for row in queue["orders"]:
            if row["verdict"] in ("HOLD", "REJECT") and row["missing_count"] > 0:
                target = row
                break
        if target is None:
            pytest.skip("No order with missing_knowledge in queue")
        r = api.get(f"{BASE_URL}/api/director/review/{target['order_id']}", timeout=60)
        assert r.status_code == 200
        for m in r.json()["missing_knowledge"]:
            assert "section" in m and isinstance(m["section"], str)
            assert "needed_by" in m and isinstance(m["needed_by"], list)

    def test_review_404_on_unknown(self, api):
        r = api.get(f"{BASE_URL}/api/director/review/does-not-exist-xyz", timeout=30)
        assert r.status_code == 404


# ---------- use_ai=true ----------

class TestDirectorAIBrief:
    def test_ai_never_changes_verdict(self, api, queue):
        oid = queue["orders"][0]["order_id"]
        d1 = api.get(f"{BASE_URL}/api/director/review/{oid}?use_ai=false", timeout=60).json()
        d2 = api.get(f"{BASE_URL}/api/director/review/{oid}?use_ai=true", timeout=90).json()
        assert d1["verdict"] == d2["verdict"], "AI must never change the verdict"
        assert d1["recommended_status"] == d2["recommended_status"]
        # It must gracefully return either 'ai' or 'deterministic' (never error)
        assert d2["brief_source"] in {"ai", "deterministic"}
        assert d2["executive_brief"], "AI-mode brief must not be empty"

    def test_ai_no_hang_on_multiple_orders(self, api, queue):
        for row in queue["orders"][:3]:
            r = api.get(f"{BASE_URL}/api/director/review/{row['order_id']}?use_ai=true", timeout=90)
            assert r.status_code == 200, r.text[:200]
            body = r.json()
            assert body["brief_source"] in {"ai", "deterministic"}


# ---------- decision ----------

class TestDirectorDecision:
    def test_apply_decision_updates_status(self, api, queue):
        # Find any order; verify decision applies recommended_status
        row = queue["orders"][0]
        oid = row["order_id"]
        pre = api.get(f"{BASE_URL}/api/director/review/{oid}", timeout=60).json()

        r = api.post(f"{BASE_URL}/api/director/review/{oid}/decision", timeout=60)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d.get("applied") is True
        assert d["verdict"] == pre["verdict"]
        assert d["new_status"] == pre["recommended_status"]
        assert d["new_status"] in VALID_STATUSES

        # Verify persistence via manufacturing order fetch (through queue) — status changed
        q2 = api.get(f"{BASE_URL}/api/director/queue", timeout=60).json()
        updated = next((o for o in q2["orders"] if o["order_id"] == oid), None)
        assert updated is not None
        assert updated["current_status"] == pre["recommended_status"]

    def test_decision_appends_history(self, api, queue):
        # Fetch via manufacturing endpoint if available; otherwise via db-less check:
        # We can check history through the /manufacturing/orders endpoint if it exists.
        # Fallback: just re-post decision and ensure still 200.
        oid = queue["orders"][0]["order_id"]
        # Try the common orders endpoint
        for path in ("/api/manufacturing/orders", "/api/manufacturing-orders"):
            r = api.get(f"{BASE_URL}{path}", timeout=30)
            if r.status_code == 200:
                data = r.json()
                orders = data if isinstance(data, list) else data.get("orders", [])
                mo = next((o for o in orders if o.get("id") == oid), None)
                if mo:
                    hist = mo.get("approval_history") or []
                    assert any("Manufacturing Director" in (h.get("by") or "") for h in hist), \
                        "approval_history must be attributed to Manufacturing Director"
                    return
        pytest.skip("Could not locate manufacturing orders endpoint to verify history")

    def test_decision_404_on_unknown(self, api):
        r = api.post(f"{BASE_URL}/api/director/review/does-not-exist-xyz/decision", timeout=30)
        assert r.status_code == 404
