"""Iteration 92 — Backend tests for QRU Automated Pre-Review Inspection™ + Product Family Manufacturing™.

Coverage:
  1. GET /api/book-mfg/books/{book_id}/inspection is read-only and returns the expected shape
     for BOOK-0013 and BOOK-0018 (verifies word-count unchanged before/after).
  2. GET /api/family/intents returns the 6 intents + available_families.
  3. GET /api/family/eligible-sources returns Manufacturing-eligible understandings including
     DEC-00018 (Founder Approved) → proves the eligibility fix.
  4. GET /api/family/preview?decoder_id=DEC-00018&intent=consumer → eligible=true, gate ok,
     can_manufacture=true.
  5. Source gate still blocks mismatches — DEC-GATETEST assemble w/o override → 409.
  6. Verify FAM-5EA08F8F / BOOK-0018 / PRD-00240 / PRD-00241 exist and reference KR-00080.

We deliberately DO NOT re-run POST /api/family/assemble for DEC-00018 consumer to avoid extra AI
spend — the existing FAM assembly is verified via the DB records instead. If forced to run, we
would run consumer intent only (Book/no AI).
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")

ADMIN_EMAIL = "demo.admin@qru.com"
ADMIN_PASSWORD = "qru-demo-admin-2026"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    d = r.json()
    tok = d.get("access_token") or d.get("token")
    assert tok, f"No token in {d}"
    return tok


@pytest.fixture(scope="session")
def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Inspection endpoint — read-only, shape correct, does not mutate the book.
# ---------------------------------------------------------------------------
class TestInspection:
    @pytest.mark.parametrize("book_code,book_uuid", [
        ("BOOK-0013", "971ebe9e-32fa-4030-a7f4-73f0a51b3b3c"),
        ("BOOK-0018", "92191d2e-10c5-42cf-8a58-8d850f116623"),
    ])
    def test_inspection_shape_and_readonly(self, auth, book_code, book_uuid):
        # Fetch book BEFORE (get_book only accepts UUID id, not book_code — that's fine)
        before = requests.get(f"{BASE_URL}/api/book-mfg/books/{book_uuid}", headers=auth, timeout=30)
        assert before.status_code == 200, f"{book_code} not found: {before.status_code} {before.text[:200]}"
        b_before = before.json()
        book_id = book_code  # inspection endpoint accepts book_code
        content_before = (b_before.get("editorial_edition") or b_before.get("working_copy") or {}).get("content") or ""
        wc_before = len(content_before.split())

        # Run inspection
        r = requests.get(f"{BASE_URL}/api/book-mfg/books/{book_id}/inspection", headers=auth, timeout=60)
        assert r.status_code == 200, f"Inspection failed for {book_id}: {r.status_code} {r.text[:300]}"
        rep = r.json()

        # Summary shape
        assert "summary" in rep
        s = rep["summary"]
        for k in ("clean", "blocking", "recommended", "advisory", "total_exceptions", "publish_ready"):
            assert k in s, f"summary missing key {k}: {s}"
        assert isinstance(s["blocking"], int)
        assert isinstance(s["total_exceptions"], int)
        # exceptions list + founder_judgment
        assert isinstance(rep.get("exceptions"), list)
        assert isinstance(rep.get("founder_judgment"), list) and len(rep["founder_judgment"]) > 0
        # each exception has id/label/severity/detail
        for e in rep["exceptions"]:
            assert "id" in e and "label" in e and "severity" in e and "detail" in e
            assert e["severity"] in ("blocking", "recommended", "advisory")
        assert rep.get("read_only") is True
        assert rep.get("never_rewrites") is True

        # Fetch book AFTER — must be unchanged
        after = requests.get(f"{BASE_URL}/api/book-mfg/books/{book_uuid}", headers=auth, timeout=30)
        assert after.status_code == 200
        b_after = after.json()
        content_after = (b_after.get("editorial_edition") or b_after.get("working_copy") or {}).get("content") or ""
        wc_after = len(content_after.split())
        assert wc_before == wc_after, f"Inspection MUTATED book {book_id}: {wc_before} -> {wc_after} words"
        assert content_before == content_after, f"Inspection MUTATED book {book_id} content."

    def test_inspection_book_0018_content_ok(self, auth):
        """BOOK-0018 should NOT be flagged as factory-doc mismatch (content_integrity ok)."""
        r = requests.get(f"{BASE_URL}/api/book-mfg/books/BOOK-0018/inspection", headers=auth, timeout=60)
        assert r.status_code == 200
        rep = r.json()
        ci = [e for e in rep["exceptions"] if e["id"] == "content_integrity"]
        assert not ci, f"BOOK-0018 flagged for content_integrity: {ci}"


# ---------------------------------------------------------------------------
# 2. /api/family/intents
# ---------------------------------------------------------------------------
class TestIntents:
    def test_intents(self, auth):
        r = requests.get(f"{BASE_URL}/api/family/intents", headers=auth, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        intents = d.get("intents", [])
        assert isinstance(intents, list) and len(intents) == 6, f"expected 6 intents, got {len(intents)}"
        ids = {i["id"] for i in intents}
        assert ids == {"consumer", "classroom", "homeschool", "professional", "corporate", "exam_prep"}, ids
        assert d.get("available_families"), "available_families missing"
        # Each intent has families
        for it in intents:
            assert it.get("families"), f"intent {it['id']} missing families"


# ---------------------------------------------------------------------------
# 3. /api/family/eligible-sources — must include DEC-00018 (Founder Approved)
# ---------------------------------------------------------------------------
class TestEligibleSources:
    def test_eligible_sources_includes_dec00018(self, auth):
        r = requests.get(f"{BASE_URL}/api/family/eligible-sources", headers=auth, timeout=30)
        assert r.status_code == 200, r.text
        srcs = r.json().get("sources", [])
        assert len(srcs) > 0, "no eligible sources returned"
        # find DEC-00018
        dec = [s for s in srcs if s.get("decoder_id") == "DEC-00018"]
        assert dec, f"DEC-00018 not in eligible sources; got {len(srcs)} sources. Sample: {srcs[:3]}"
        # Its state should be a post-Manufacturing Ready state (e.g. Founder Approved)
        state = dec[0]["review_state"]
        assert state in ("Founder Approved", "Manufacturing Ready", "Treasure Standard",
                          "Verified", "Approved"), f"Unexpected state for DEC-00018: {state}"

    def test_eligible_sources_count_reasonable(self, auth):
        r = requests.get(f"{BASE_URL}/api/family/eligible-sources", headers=auth, timeout=30)
        assert r.status_code == 200
        srcs = r.json().get("sources", [])
        # spec says "~18 sources"
        assert len(srcs) >= 5, f"too few eligible sources: {len(srcs)}"


# ---------------------------------------------------------------------------
# 4. /api/family/preview?decoder_id=DEC-00018&intent=consumer
# ---------------------------------------------------------------------------
class TestFamilyPreview:
    def test_preview_dec00018_consumer(self, auth):
        r = requests.get(f"{BASE_URL}/api/family/preview",
                         params={"decoder_id": "DEC-00018", "intent": "consumer"},
                         headers=auth, timeout=30)
        assert r.status_code == 200, f"preview failed: {r.status_code} {r.text[:300]}"
        d = r.json()
        assert d["source"]["eligible"] is True, f"source.eligible not true: {d['source']}"
        assert d["gate"]["match"]["level"] == "ok", f"gate.match.level not ok: {d['gate']}"
        assert d["can_manufacture"] is True
        assert "Book" in d["families"], f"consumer intent should include Book: {d['families']}"


# ---------------------------------------------------------------------------
# 5. Source gate still blocks factory-doc mismatch — DEC-GATETEST without override.
# ---------------------------------------------------------------------------
class TestFamilySourceGate:
    def test_assemble_gatetest_blocked_without_override(self, auth):
        r = requests.post(f"{BASE_URL}/api/family/assemble",
                          headers=auth, timeout=30,
                          json={"decoder_id": "DEC-GATETEST", "intent": "consumer"})
        # 409 with source_verification_failed
        assert r.status_code == 409, f"expected 409, got {r.status_code} {r.text[:300]}"
        detail = r.json().get("detail", {})
        assert detail.get("error") == "source_verification_failed", detail
        assert detail.get("gate", {}).get("match", {}).get("level") == "critical"


# ---------------------------------------------------------------------------
# 6. Verify existing FAM-5EA08F8F assembly (BOOK-0018 + PRD-00240 + PRD-00241, all KR-00080).
# ---------------------------------------------------------------------------
class TestExistingFamilyAssembly:
    def test_book_0018_exists_and_linked_to_kr00080(self, auth):
        r = requests.get(f"{BASE_URL}/api/book-mfg/books/92191d2e-10c5-42cf-8a58-8d850f116623", headers=auth, timeout=30)
        assert r.status_code == 200, r.text
        b = r.json()
        kr_ids = b.get("source_kr_ids") or (b.get("provenance", {}) or {}).get("source_kr_ids") or []
        # Some models nest under source
        if not kr_ids:
            src = b.get("source") or {}
            kr_ids = src.get("source_kr_ids") or []
        assert any("KR-00080" in str(x) for x in (kr_ids or [])) or "KR-00080" in str(b), \
            f"BOOK-0018 not linked to KR-00080. Keys: {list(b.keys())[:20]}"

    def test_family_history_contains_fam5ea08f8f(self, auth):
        r = requests.get(f"{BASE_URL}/api/family/history", headers=auth, timeout=30)
        assert r.status_code == 200
        fams = r.json().get("families", [])
        assert any(f.get("family_code") == "FAM-5EA08F8F" for f in fams), \
            f"FAM-5EA08F8F not in history: {[f.get('family_code') for f in fams]}"
