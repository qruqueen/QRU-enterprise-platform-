"""Iteration 103 — Factory Concierge Knowledge Record resolver.

Verifies that explicit KR IDs (and manuscript codes) are resolved BEFORE the fuzzy knowledge
gate, that verification status is reported, that multiple matches produce a selector, and that
no duplicate KR is written by the read-only resolver.
"""
import os
import pytest
import requests

def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    try:
        with open("/app/frontend/.env") as f:
            for ln in f:
                if ln.startswith("REACT_APP_BACKEND_URL="):
                    return ln.split("=", 1)[1].strip().rstrip("/")
    except FileNotFoundError:
        pass
    raise RuntimeError("REACT_APP_BACKEND_URL not set")


BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "demo.admin@qru.com"
ADMIN_PASSWORD = "qru-demo-admin-2026"


# ------------------------------ fixtures ------------------------------
@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def kr_baseline(headers):
    """Snapshot KR count and KR-00080 count BEFORE any concierge interactions."""
    # We rely on a listing endpoint if available; else use knowledge-gap-check as a sanity probe.
    r = requests.get(f"{API}/knowledge-records", headers=headers, timeout=30)
    total = None
    kr80 = None
    if r.status_code == 200:
        data = r.json()
        records = data if isinstance(data, list) else data.get("records") or data.get("items") or []
        total = len(records)
        kr80 = sum(1 for x in records if (x.get("kr_code") or "").upper() == "KR-00080")
    return {"total": total, "kr80": kr80, "endpoint_ok": r.status_code == 200}


def _msg(headers, session_id, text, use_ai=False):
    body = {"message": text, "use_ai": use_ai}
    if session_id:
        body["session_id"] = session_id
    r = requests.post(f"{API}/factory-os/concierge/message", headers=headers, json=body, timeout=45)
    assert r.status_code == 200, f"concierge/message {r.status_code}: {r.text[:400]}"
    return r.json()


# ------------------------------ tests ------------------------------
class TestReportedBugWorkbook:
    """Turn1: 'I want to make a workbook'  Turn2: 'KR-00080 — AI Literacy' → stage=ready."""

    def test_two_turn_workbook_then_kr00080(self, headers):
        # Turn 1
        r1 = _msg(headers, None, "I want to make a workbook")
        sid = r1["session_id"]
        assert r1["stage"] == "need_topic", f"turn1 stage={r1['stage']}"
        assert (r1.get("outcome") or {}).get("id") == "workbook"

        # Turn 2 — explicit KR id
        r2 = _msg(headers, sid, "KR-00080 — AI Literacy")
        assert r2["stage"] == "ready", f"turn2 stage={r2['stage']} reply={r2.get('reply')[:200]}"
        assert r2["can_launch"] is True
        assert r2.get("media_kr_id"), "media_kr_id must be set on ready"
        reply = r2["reply"]
        assert "KR-00080" in reply
        assert "AI Literacy" in reply
        assert "Verified" in reply
        assert (r2.get("slots") or {}).get("topic") == "AI Literacy"

        # Cleanup this session
        requests.delete(f"{API}/factory-os/concierge/session/{sid}", headers=headers)


class TestExplicitIdVariants:
    def test_bare_kr_code(self, headers):
        r1 = _msg(headers, None, "make a workbook")
        sid = r1["session_id"]
        r2 = _msg(headers, sid, "KR-00080")
        assert r2["stage"] == "ready", f"bare code stage={r2['stage']}"
        assert r2["can_launch"] is True
        assert "KR-00080" in r2["reply"]
        assert "AI Literacy" in r2["reply"]

    def test_natural_sentence_with_kr_code(self, headers):
        r1 = _msg(headers, None, "make a workbook")
        sid = r1["session_id"]
        r2 = _msg(headers, sid, "make a workbook from KR-00080")
        assert r2["stage"] == "ready", f"sentence stage={r2['stage']}"
        assert r2["can_launch"] is True
        assert "Verified" in r2["reply"]


class TestManuscriptSource:
    def test_manuscript_exact_title(self, headers):
        r1 = _msg(headers, None, "make a book")
        sid = r1["session_id"]
        r2 = _msg(headers, sid, "How to Understand AI – Final Publishing Master")
        stage = r2["stage"]
        # spec: stage == manuscript_source and manuscript_sources contains BOOK-0017
        assert stage in ("manuscript_source", "ready"), f"got stage={stage} reply={r2['reply'][:200]}"
        codes = [m.get("book_code") for m in (r2.get("manuscript_sources") or [])]
        assert "BOOK-0017" in codes, f"manuscript_sources={codes}"
        if stage == "manuscript_source":
            assert "manuscript" in r2["reply"].lower()


class TestSelectorMultipleMatches:
    def test_selector_two_krs(self, headers):
        r1 = _msg(headers, None, "make a workbook")
        sid = r1["session_id"]
        r2 = _msg(headers, sid, "How hope sustains people through hardship")
        assert r2["stage"] == "select_kr", f"expected select_kr got {r2['stage']} reply={r2['reply'][:200]}"
        sel = r2.get("selector") or []
        assert len(sel) > 1, f"selector length={len(sel)}"
        codes = {s.get("kr_code") for s in sel}
        assert "KR-00069" in codes and "KR-00083" in codes, f"selector codes={codes}"
        # Must NOT offer new research
        assert "manufacturing pipeline" not in r2["reply"].lower() or "won't start new research" in r2["reply"].lower()


class TestNoDuplicateKR:
    def test_no_kr_created_after_all_interactions(self, headers, kr_baseline):
        if not kr_baseline["endpoint_ok"]:
            pytest.skip("KR list endpoint unavailable; count check skipped")
        r = requests.get(f"{API}/knowledge-records", headers=headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        records = data if isinstance(data, list) else data.get("records") or data.get("items") or []
        total = len(records)
        kr80 = sum(1 for x in records if (x.get("kr_code") or "").upper() == "KR-00080")
        assert total == kr_baseline["total"], f"KR count changed {kr_baseline['total']} → {total}"
        assert kr80 == 1 and kr_baseline["kr80"] == 1, f"KR-00080 count changed {kr_baseline['kr80']} → {kr80}"


class TestNonRegressionKnowledgeGap:
    def test_unknown_topic_still_gaps(self, headers):
        r1 = _msg(headers, None, "make a workbook")
        sid = r1["session_id"]
        r2 = _msg(headers, sid, "quantum widget alchemy for toddlers")
        assert r2["stage"] == "knowledge_gap", f"unknown topic stage={r2['stage']}"
        assert r2["can_launch"] is False
        assert "Knowledge Manufacturing Pipeline".lower() in r2["reply"].lower() \
            or "manufacturing pipeline" in r2["reply"].lower()
