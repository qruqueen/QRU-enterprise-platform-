"""QRU Source Verification Gate™ — iteration_91 backend tests.

Verifies:
- GET /api/decoder/{id}/verify-source returns match.level='critical' for the seeded fixture
  decoder 'gate-test-critical', and 'ok' for a legitimate manufacturing-ready decoder.
- POST /api/decoder/gate-test-critical/create-product WITHOUT override returns HTTP 409
  with detail.error='source_verification_failed'.
- We do NOT actually manufacture (no override) — the critical fixture must stop before any book.
"""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "demo.admin@qru.com"
ADMIN_PASSWORD = "qru-demo-admin-2026"

CRITICAL_DID = "gate-test-critical"
LEGIT_DID = "b407ef84-295a-4471-a09b-7ba0f7ccb8f2"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"no token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ---------- verify-source ----------
def test_verify_source_critical_fixture(headers):
    r = requests.get(f"{API}/decoder/{CRITICAL_DID}/verify-source", headers=headers, timeout=20)
    assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
    data = r.json()
    assert data.get("match", {}).get("level") == "critical", data.get("match")
    assert data["match"]["ok"] is False
    assert "source" in data
    assert "preview" in data
    # Reason must be meaningful, not empty
    assert data["match"].get("reason")


def test_verify_source_legit_decoder(headers):
    r = requests.get(f"{API}/decoder/{LEGIT_DID}/verify-source", headers=headers, timeout=20)
    assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
    data = r.json()
    assert data.get("match", {}).get("level") == "ok", data.get("match")
    assert data["match"]["ok"] is True
    # Preview paragraphs must be present for a legit decoder
    paras = data.get("preview", {}).get("paragraphs") or []
    assert len(paras) >= 1, f"expected preview paragraphs, got {paras}"


# ---------- create-product enforcement ----------
def test_create_product_critical_without_override_blocked(headers):
    r = requests.post(f"{API}/decoder/{CRITICAL_DID}/create-product",
                      headers=headers, json={"product_type": "Book"}, timeout=30)
    assert r.status_code == 409, f"expected 409, got {r.status_code}: {r.text[:300]}"
    # FastAPI wraps HTTPException.detail as {"detail": <detail>}
    body = r.json()
    detail = body.get("detail") if isinstance(body, dict) else None
    assert isinstance(detail, dict), f"detail should be dict, got: {body}"
    assert detail.get("error") == "source_verification_failed", detail
    assert "gate" in detail
    assert detail["gate"]["match"]["level"] == "critical"


def test_create_product_critical_missing_body_still_blocked(headers):
    """Default CreateProductInput (override_source_gate=False) — no body sent — must still block."""
    r = requests.post(f"{API}/decoder/{CRITICAL_DID}/create-product",
                      headers=headers, timeout=30)
    # Either 409 (gate) or 422 if body required; but endpoint has default so should be 409.
    assert r.status_code in (409,), f"expected 409, got {r.status_code}: {r.text[:200]}"


def test_create_product_critical_override_false_explicit_blocked(headers):
    r = requests.post(f"{API}/decoder/{CRITICAL_DID}/create-product",
                      headers=headers, json={"product_type": "Book", "override_source_gate": False}, timeout=30)
    assert r.status_code == 409
    assert r.json().get("detail", {}).get("error") == "source_verification_failed"
