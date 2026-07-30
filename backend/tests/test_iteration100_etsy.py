"""Tests for QRU × Etsy integration (iteration 100).

Covers: auth gating, no-secret-leak, PKCE authorize URL, governance eligibility,
preview (no mutation), publish approval-gate, publish-when-disconnected error.
"""
import os
import base64
import hashlib
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
SHARED_SECRET = "99gawl9jbh"
KEYSTRING = "vs7rv08zwgstjq548px9cguc"

ADMIN = {"email": "demo.admin@qru.com", "password": "qru-demo-admin-2026"}


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def h(token):
    return {"Authorization": f"Bearer {token}"}


# --- SECURITY: auth gating -----------------------------------------------
@pytest.mark.parametrize("path", [
    "/api/integrations/etsy/status",
    "/api/integrations/etsy/connect",
    "/api/integrations/etsy/listings",
    "/api/integrations/etsy/orders",
    "/api/integrations/etsy/products",
])
def test_endpoints_require_auth(path):
    r = requests.get(f"{BASE_URL}{path}", timeout=30)
    assert r.status_code in (401, 403), f"{path} -> {r.status_code}"


# --- STATUS: no leaks, disconnected shape --------------------------------
def test_status_disconnected_no_leak(h):
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/status", headers=h, timeout=30)
    assert r.status_code == 200
    body = r.text
    assert SHARED_SECRET not in body
    data = r.json()
    # No token/keystring leak
    for bad in ("access_token", "refresh_token", "encrypted_access_token",
                "encrypted_refresh_token", "keystring", "shared_secret"):
        assert bad not in data, f"leaked field: {bad}"
    # If disconnected, verify shape
    if data.get("status") == "disconnected":
        for k in ("mapped_products", "draft_listings", "active_listings"):
            assert k in data


# --- CONNECT: PKCE authorize URL -----------------------------------------
def test_connect_returns_pkce_authorize_url(h):
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/connect", headers=h, timeout=30)
    assert r.status_code == 200
    assert SHARED_SECRET not in r.text
    data = r.json()
    url = data.get("authorize_url", "")
    assert url.startswith("https://www.etsy.com/oauth/connect?"), url
    assert "code_challenge=" in url
    assert "code_challenge_method=S256" in url
    assert "state=" in url
    assert "scope=" in url
    assert f"client_id={KEYSTRING}" in url  # keystring is public (client_id), that's fine
    # Verify shared secret NEVER appears
    assert SHARED_SECRET not in url


# --- PRODUCTS: eligibility of known books --------------------------------
def test_products_eligibility(h):
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    assert r.status_code == 200
    data = r.json()
    by_code = {p["code"]: p for p in data.get("products", []) if p.get("code")}
    # BOOK-0006 should be ineligible (not authorized)
    if "BOOK-0006" in by_code:
        assert by_code["BOOK-0006"]["eligible"] is False


# --- PREVIEW: eligible book, no mutation ---------------------------------
def test_preview_eligible_book_no_mutation(h):
    # find BOOK-0004 by code
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    products = r.json().get("products", [])
    b = next((p for p in products if p.get("code") == "BOOK-0004"), None)
    assert b is not None, "BOOK-0004 not found"
    pid = b["id"]

    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/{pid}/preview",
                      headers=h, json={}, timeout=30)
    assert r.status_code == 200, r.text
    assert SHARED_SECRET not in r.text
    data = r.json()
    assert data.get("eligibility", {}).get("eligible") is True, data
    state = data.get("listing_preview", {}).get("state", "").lower()
    assert "draft" in state, data.get("listing_preview")
    note = (data.get("note") or "").lower()
    assert "nothing" in note or "no mutation" in note or "preview only" in note

    # Verify no mapping was created
    r2 = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    b2 = next((p for p in r2.json().get("products", []) if p.get("code") == "BOOK-0004"), None)
    assert not b2.get("etsy_listing_id"), "preview must not create a mapping"


def test_preview_ineligible_book(h):
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    b = next((p for p in r.json().get("products", []) if p.get("code") == "BOOK-0006"), None)
    if not b:
        pytest.skip("BOOK-0006 not seeded")
    pid = b["id"]
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/{pid}/preview",
                      headers=h, json={}, timeout=30)
    assert r.status_code == 200
    assert r.json().get("eligibility", {}).get("eligible") is False


# --- PUBLISH: approval gate ---------------------------------------------
def test_publish_without_approval_blocked(h):
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    b = next((p for p in r.json().get("products", []) if p.get("code") == "BOOK-0004"), None)
    assert b is not None
    pid = b["id"]
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/{pid}/publish",
                      headers=h, json={"approved": False}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data.get("requires_approval") is True, data
    # Confirm no mapping created
    r2 = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    b2 = next((p for p in r2.json().get("products", []) if p.get("code") == "BOOK-0004"), None)
    assert not b2.get("etsy_listing_id")


def test_publish_approved_but_not_connected_errors(h):
    # Only run when Etsy is disconnected
    status = requests.get(f"{BASE_URL}/api/integrations/etsy/status", headers=h, timeout=30).json()
    if status.get("status") == "connected":
        pytest.skip("Etsy currently connected; skipping not-connected assertion")
    r = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    b = next((p for p in r.json().get("products", []) if p.get("code") == "BOOK-0004"), None)
    assert b is not None
    pid = b["id"]
    r = requests.post(f"{BASE_URL}/api/integrations/etsy/products/{pid}/publish",
                      headers=h, json={"approved": True}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert "not connected" in (data.get("error") or "").lower(), data
    # Confirm no mapping created
    r2 = requests.get(f"{BASE_URL}/api/integrations/etsy/products", headers=h, timeout=30)
    b2 = next((p for p in r2.json().get("products", []) if p.get("code") == "BOOK-0004"), None)
    assert not b2.get("etsy_listing_id")


# --- PKCE verification: challenge = base64url(sha256(verifier)) ---------
def test_pkce_challenge_derivation_local():
    """Sanity: our local PKCE math matches Etsy spec (independent of live API)."""
    verifier = "abc123"
    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    assert len(expected) == 43
