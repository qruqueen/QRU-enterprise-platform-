"""Iteration 101 — Catalog integrity after imprint migration + Etsy governance gating.

The user reported a bug: after imprint canonicalization + duplicate merge, the QRU catalog
must still be complete (8 authorized books) and 'Patterns of Intelligence' (BOOK-0013) must
still exist under E.Q. Rothwell™. Also verify Etsy publish/activate governance while Etsy
is intentionally DISCONNECTED in preview.
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
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def h(token):
    return {"Authorization": f"Bearer {token}"}


# ============ CATALOG INTEGRITY (user's reported bug) ====================
def test_public_catalog_has_8_authorized_books():
    r = requests.get(f"{BASE_URL}/api/public/books", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    print(f"Public catalog count={data.get('count')} imprints={data.get('imprints')}")
    assert data.get("count") == 8, f"Expected 8 books, got {data.get('count')}: {[b.get('title') for b in data.get('books', [])]}"
    imprints = set(data.get("imprints", []))
    assert imprints == {"E.Q. Rothwell™", "QRU Press™"}, imprints


def test_patterns_of_intelligence_exists_and_is_rothwell():
    r = requests.get(f"{BASE_URL}/api/public/books", timeout=30)
    assert r.status_code == 200
    books = r.json().get("books", [])
    poi = next((b for b in books if "Patterns of Intelligence" in (b.get("title") or "")), None)
    assert poi is not None, f"Patterns of Intelligence missing from public catalog. Titles: {[b.get('title') for b in books]}"
    assert poi.get("imprint") == "E.Q. Rothwell™", f"Wrong imprint: {poi.get('imprint')}"


def test_all_8_authorized_codes_present(h):
    """Use super-admin /etsy/products (which lists book_records with codes) to verify all 8."""
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    assert r.status_code == 200
    prods = r.json().get("products", [])
    by_code = {p.get("code"): p for p in prods if p.get("code")}
    missing = AUTHORIZED_CODES - set(by_code.keys())
    assert not missing, f"Missing authorized book codes: {missing}"
    # BOOK-0013 must be eligible + E.Q. Rothwell™
    poi = by_code.get("BOOK-0013")
    assert poi is not None
    assert poi.get("eligible") is True, f"BOOK-0013 not eligible: {poi}"
    imp = poi.get("imprint") or poi.get("canonical_imprint")
    assert imp == "E.Q. Rothwell™", f"BOOK-0013 imprint wrong: {imp} | full={poi}"


def test_book_0003_removed_book_0004_intact(h):
    """BOOK-0003 (Ordinary Tuesdays FULL MANUSCRIPT duplicate) must be gone; BOOK-0004 remains."""
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    prods = r.json().get("products", [])
    codes = {p.get("code") for p in prods}
    assert "BOOK-0003" not in codes, "BOOK-0003 (duplicate) should have been merged to trash"
    b4 = next((p for p in prods if p.get("code") == "BOOK-0004"), None)
    assert b4 is not None, "BOOK-0004 canonical Ordinary Tuesdays missing"
    assert b4.get("eligible") is True, f"BOOK-0004 must remain authorized/eligible: {b4}"


# ============ ETSY ELIGIBILITY MATRIX ====================================
def test_etsy_products_eligibility_matrix(h):
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    assert r.status_code == 200
    prods = r.json().get("products", [])
    by_code = {p.get("code"): p for p in prods if p.get("code")}
    # All 8 authorized should be eligible
    for code in AUTHORIZED_CODES:
        p = by_code.get(code)
        assert p is not None, f"{code} not in products list"
        assert p.get("eligible") is True, f"{code} unexpectedly ineligible: {p.get('detail')}"
    # Known unauthorized/test books should be ineligible if present
    for code in ("BOOK-0002", "BOOK-0005"):
        if code in by_code:
            assert by_code[code].get("eligible") is False, f"{code} should be ineligible"


# ============ SECURITY: auth required on ALL etsy endpoints ==============
@pytest.mark.parametrize("method,path", [
    ("GET", "/api/integrations/etsy/products"),
    ("GET", "/api/integrations/etsy/diagnostics"),
    ("GET", "/api/integrations/etsy/status"),
    ("POST", "/api/integrations/etsy/products/BOOK-0001/publish"),
    ("POST", "/api/integrations/etsy/products/BOOK-0001/activate"),
])
def test_etsy_endpoints_require_auth(method, path):
    r = requests.request(method, f"{BASE_URL}{path}", json={}, timeout=30)
    assert r.status_code in (401, 403), f"{method} {path} -> {r.status_code}"


def test_no_secret_leak_in_status_or_diagnostics(h):
    for path in ("/api/integrations/etsy/status", "/api/integrations/etsy/diagnostics"):
        r = requests.get(f"{BASE_URL}{path}", headers=h, timeout=30)
        assert r.status_code == 200, f"{path} {r.status_code}"
        assert SHARED_SECRET not in r.text, f"Shared secret leaked in {path}!"
        data = r.json()
        for bad in ("access_token", "refresh_token", "encrypted_access_token",
                    "encrypted_refresh_token", "shared_secret"):
            # allow "keystring" (public client_id) but not tokens/secrets
            assert bad not in data, f"leaked field {bad} in {path}: {data}"


# ============ GOVERNANCE: publish without approval / when disconnected ===
def test_publish_book0001_requires_approval(h):
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/BOOK-0001/publish",
                      headers=h, json={"approved": False}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("requires_approval") is True, data


def test_publish_book0001_approved_but_disconnected(h):
    status = requests.get(f"{BASE_URL}/api/integrations/etsy/status", headers=h, timeout=30).json()
    if status.get("status") == "connected":
        pytest.skip("Etsy connected; not-connected assertion N/A")
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/BOOK-0001/publish",
                      headers=h, json={"approved": True}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    err = (data.get("error") or "").lower()
    assert "not connected" in err, f"Expected 'not connected' error, got: {data}"
    # verify no mapping created
    prods = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30).json().get("products", [])
    b = next((p for p in prods if p.get("code") == "BOOK-0001"), None)
    assert not (b or {}).get("etsy_listing_id"), f"mapping unexpectedly created: {b}"


# ============ GOVERNANCE: activate ========================================
def test_activate_book0001_without_approval(h):
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/BOOK-0001/activate",
                      headers=h, json={"approved": False}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("requires_approval") is True, data


def test_activate_book0001_approved_no_mapping(h):
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/BOOK-0001/activate",
                      headers=h, json={"approved": True}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    err = (data.get("error") or "").lower()
    # Accept "no etsy draft is mapped" or similar. Also acceptable: "not connected".
    assert ("no etsy draft" in err) or ("not mapped" in err) or ("no draft" in err) or ("not connected" in err), \
        f"Expected 'No Etsy draft is mapped...' error, got: {data}"
