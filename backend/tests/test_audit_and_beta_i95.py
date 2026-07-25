"""Iteration 95 — Regression: audit exports download + beta-status LIVE Stripe wording."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://understanding-os.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "demo.admin@qru.com"
ADMIN_PASSWORD = "qru-demo-admin-2026"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"no access_token in response: {data}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# --- Audit exports regression ---
class TestAuditExports:
    def test_list_exports_returns_three(self, auth_headers):
        r = requests.get(f"{API}/audit/exports", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        exports = data.get("exports", [])
        names = {e["filename"] for e in exports}
        expected = {"QRU_Standards_Full_Export.json", "QRU_Standards_Inventory.csv", "QRU_Standards_Audit_Findings.md"}
        assert expected.issubset(names), f"missing exports: {names}"
        for e in exports:
            assert e["download_url"].startswith("/api/audit/exports/"), e

    @pytest.mark.parametrize("filename", [
        "QRU_Standards_Full_Export.json",
        "QRU_Standards_Inventory.csv",
        "QRU_Standards_Audit_Findings.md",
    ])
    def test_download_each_export(self, auth_headers, filename):
        r = requests.get(f"{API}/audit/exports/{filename}", headers=auth_headers, timeout=30)
        assert r.status_code == 200, f"{filename}: {r.status_code} {r.text[:200]}"
        assert len(r.content) > 0
        # Confirm the doubled-path bug is gone: /api/api/... must 404 (or not double)
        r2 = requests.get(f"{API}/api/audit/exports/{filename}", headers=auth_headers, timeout=15)
        assert r2.status_code == 404


# --- Beta status LIVE Stripe wording ---
class TestBetaStatus:
    def test_beta_status_live_wording(self, auth_headers):
        r = requests.get(f"{API}/metrics/beta-status", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["stripe_test"] is False, f"stripe_test must be False (LIVE keys): {data.get('stripe_test')}"
        assert data["pay_mode"] == "LIVE", f"pay_mode must be LIVE: {data.get('pay_mode')}"
        ps = data["payment_status"]
        assert ps["payment_mode"] == "Live"
        assert ps["accepts_real_money"] == "Yes"
        assert "LIVE" in ps["label"]

        # Contradiction check on questions
        text_blob = " ".join(q["a"] for q in data["questions"]).lower()
        forbidden = ["sandbox", "test mode", "test keys only", "test keys"]
        found = [f for f in forbidden if f in text_blob]
        assert not found, f"forbidden test-mode wording present in LIVE mode: {found}"

        # blocks_promotion must not contain the TEST-mode caveat
        for b in data["blocks_promotion"]:
            assert "test mode" not in b.lower(), f"blocks_promotion still says TEST mode: {b}"
