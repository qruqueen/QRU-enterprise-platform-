"""Iteration 102 — Retest fixes from iteration_101:
   FIX 1: activate approval-first gate (approved:false returns requires_approval regardless of mapping)
   FIX 2: preview no longer 500s when taxonomy_id is unset
   REGRESSION: catalog complete (8 books incl. Patterns of Intelligence) + endpoint auth.
"""
import os
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
SHARED_SECRET = "99gawl9jbh"
ADMIN = {"email": "demo.admin@qru.com", "password": "qru-demo-admin-2026"}
AUTHORIZED_CODES = {"BOOK-0001", "BOOK-0004", "BOOK-0009", "BOOK-0011",
                    "BOOK-0013", "BOOK-0016", "BOOK-0018", "BOOK-0019"}


@pytest.fixture(scope="module")
def h():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ============== FIX 1: activate approval-first ordering ==================
def test_fix1_activate_book0001_not_approved_returns_requires_approval(h):
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/BOOK-0001/activate",
                      headers=h, json={"approved": False}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("requires_approval") is True, f"Expected requires_approval=true, got {data}"
    # Ensure no mapping-error leaked (approval-first)
    assert "no etsy draft" not in (str(data).lower()), f"Mapping error leaked before approval gate: {data}"


def test_fix1_activate_book0013_not_approved_returns_requires_approval(h):
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/BOOK-0013/activate",
                      headers=h, json={"approved": False}, timeout=30)
    assert r.status_code == 200, r.text
    assert r.json().get("requires_approval") is True, r.text


def test_fix1_activate_book0001_approved_no_mapping_returns_no_draft_error(h):
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/BOOK-0001/activate",
                      headers=h, json={"approved": True}, timeout=30)
    assert r.status_code == 200, r.text
    err = (r.json().get("error") or "").lower()
    assert "no etsy draft is mapped" in err, f"Expected 'No Etsy draft is mapped', got: {r.json()}"


# ============== FIX 2: preview no 500 ====================================
@pytest.mark.parametrize("code", ["BOOK-0001", "BOOK-0013", "BOOK-0016"])
def test_fix2_preview_returns_200_with_eligibility_and_listing_preview(h, code):
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/{code}/preview",
                      headers=h, json={}, timeout=30)
    assert r.status_code == 200, f"{code} preview status={r.status_code} body={r.text}"
    data = r.json()
    assert "eligibility" in data, f"{code}: missing eligibility: {data}"
    assert "listing_preview" in data, f"{code}: missing listing_preview: {data}"
    lp = data["listing_preview"]
    # taxonomy_id may be null but key must exist
    assert "taxonomy_id" in lp, f"{code}: taxonomy_id key missing: {lp}"


# ============== REGRESSION: catalog complete =============================
def test_regression_public_books_count_8_and_poi_present():
    r = requests.get(f"{BASE_URL}/api/public/books", timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("count") == 8, f"count={d.get('count')} titles={[b.get('title') for b in d.get('books',[])]}"
    poi = next((b for b in d.get("books", []) if "Patterns of Intelligence" in (b.get("title") or "")), None)
    assert poi is not None, "Patterns of Intelligence missing"
    assert poi.get("imprint") == "E.Q. Rothwell™", f"PoI imprint: {poi.get('imprint')}"


def test_regression_etsy_products_lists_all_authorized(h):
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    assert r.status_code == 200
    prods = r.json().get("products", [])
    by_code = {p.get("code"): p for p in prods}
    missing = AUTHORIZED_CODES - set(by_code.keys())
    assert not missing, f"missing: {missing}"
    for code in AUTHORIZED_CODES:
        assert by_code[code].get("eligible") is True, f"{code} not eligible: {by_code[code].get('detail')}"


# ============== REGRESSION: security =====================================
def test_regression_activate_requires_auth():
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/BOOK-0001/activate",
                      json={"approved": False}, timeout=30)
    assert r.status_code in (401, 403), r.status_code


def test_regression_preview_requires_auth():
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/BOOK-0001/preview",
                      json={}, timeout=30)
    assert r.status_code in (401, 403), r.status_code


# ============== CLEANUP verification: no mapping left ====================
def test_no_mapping_created_by_this_test_run(h):
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    for p in r.json().get("products", []):
        if p.get("code") in AUTHORIZED_CODES:
            assert not p.get("etsy_listing_id"), f"unexpected mapping on {p.get('code')}: {p}"
