"""MT-IP-001 Protection Center graceful degradation tests.

Verifies:
- POST /api/protection/{pid}/verify returns HTTP 200 with deterministic verification
  while the LLM daily spend limit is active, ai_recommendations_available == False,
  reviewer == 'QRU Deterministic Check™', graceful message present, and persisted.
- POST /api/protection/{pid}/apply-protection (super_admin) returns 200 with protected==true,
  license_type, protection.copyright_applied==true, and ip/version + history entry (no AI dep).
- GET /api/protection/dashboard returns rows + summary (regression).
- POST /api/protection/{pid}/verify on unknown pid returns 404 (not 500).
"""
import os
import pytest
import requests


def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if url:
        return url.rstrip("/")
    # Fallback: read from /app/frontend/.env
    try:
        with open("/app/frontend/.env", "r") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    raise RuntimeError("REACT_APP_BACKEND_URL not configured")


BASE_URL = _load_backend_url()
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PWD = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PWD}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    body = r.json()
    tok = body.get("access_token") or body.get("token")
    assert tok, f"no token in response: {body}"
    return tok


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def product_id(headers):
    r = requests.get(f"{BASE_URL}/api/products", headers=headers, timeout=30)
    assert r.status_code == 200, f"list products failed: {r.status_code} {r.text}"
    products = r.json()
    assert isinstance(products, list) and len(products) > 0, "no products present to test"
    for p in products:
        if p.get("status") in ("Approved", "Published"):
            return p["id"]
    return products[0]["id"]


# --- Dashboard regression ---
class TestDashboard:
    def test_dashboard_returns_rows_and_summary(self, headers):
        r = requests.get(f"{BASE_URL}/api/protection/dashboard", headers=headers, timeout=30)
        assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert "rows" in data and isinstance(data["rows"], list), "rows missing/not list"
        assert "summary" in data and isinstance(data["summary"], dict), "summary missing/not dict"
        s = data["summary"]
        for k in ("total", "verified", "protected", "published", "at_risk"):
            assert k in s, f"summary missing key {k}"
        assert s["total"] == len(data["rows"]), "summary.total mismatch with rows count"
        if data["rows"]:
            row = data["rows"][0]
            for k in ("id", "product_code", "title", "verified", "protected", "license_type"):
                assert k in row, f"row missing key {k}"


# --- MT-IP-001 Verify graceful degradation ---
class TestVerifyGracefulDegradation:
    def test_verify_returns_200_with_deterministic_fallback(self, headers, product_id):
        r = requests.post(f"{BASE_URL}/api/protection/{product_id}/verify",
                          headers=headers, timeout=60)
        assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:400]}"
        data = r.json()
        assert "verified" in data and isinstance(data["verified"], bool), "verified missing/not bool"
        assert data.get("ai_recommendations_available") is False, (
            f"expected ai_recommendations_available=False (LLM capped), got {data.get('ai_recommendations_available')}"
        )
        msg = data.get("message") or ""
        assert "AI recommendations temporarily unavailable" in msg, (
            f"missing graceful message, got: {msg!r}"
        )
        v = data.get("verification") or {}
        assert v.get("reviewer") == "QRU Deterministic Check™", (
            f"expected reviewer 'QRU Deterministic Check™', got {v.get('reviewer')!r}"
        )
        assert v.get("ai_recommendations_available") is False
        assert v.get("decision") in ("approve", "request_revision"), (
            f"unexpected decision {v.get('decision')}"
        )
        assert isinstance(v.get("revision_history"), list) and len(v["revision_history"]) >= 1

    def test_verify_persisted(self, headers, product_id):
        # trigger verification (idempotent) and then re-fetch product
        requests.post(f"{BASE_URL}/api/protection/{product_id}/verify",
                      headers=headers, timeout=60)
        r = requests.get(f"{BASE_URL}/api/products/{product_id}", headers=headers, timeout=30)
        assert r.status_code == 200
        p = r.json()
        v = p.get("verification") or {}
        assert v.get("reviewer") == "QRU Deterministic Check™", (
            f"verification not persisted with deterministic reviewer, got {v.get('reviewer')!r}"
        )
        assert v.get("ai_recommendations_available") is False, (
            "ai_recommendations_available not persisted as False"
        )
        assert v.get("decision") in ("approve", "request_revision")

    def test_verify_unknown_pid_returns_404(self, headers):
        r = requests.post(f"{BASE_URL}/api/protection/does-not-exist-xyz-123/verify",
                          headers=headers, timeout=30)
        assert r.status_code == 404, f"expected 404, got {r.status_code}: {r.text[:300]}"
        body = r.json()
        assert body.get("detail"), "404 must include detail"


# --- Deterministic apply-protection (AI-free) ---
class TestApplyProtectionDeterministic:
    def test_apply_protection_success(self, headers, product_id):
        payload = {"license_type": "Personal Use", "watermark": True,
                   "access_control": "account_required"}
        r = requests.post(f"{BASE_URL}/api/protection/{product_id}/apply-protection",
                          headers=headers, json=payload, timeout=30)
        assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:400]}"
        p = r.json()
        assert p.get("protected") is True, f"protected should be True, got {p.get('protected')}"
        assert p.get("license_type") == "Personal Use", (
            f"license_type should be 'Personal Use', got {p.get('license_type')}"
        )
        prot = p.get("protection") or {}
        assert prot.get("copyright_applied") is True, "protection.copyright_applied missing/false"
        assert prot.get("watermark_applied") is True, "protection.watermark_applied missing/false"
        ip = p.get("ip") or {}
        assert isinstance(ip.get("version"), int) and ip["version"] >= 1, (
            f"ip.version missing/invalid: {ip.get('version')}"
        )
        history = ip.get("history") or []
        assert isinstance(history, list) and len(history) >= 1, "ip.history missing/empty"
        latest = history[-1]
        assert latest.get("action") == "protection applied"
        assert latest.get("by")
        assert latest.get("at")
