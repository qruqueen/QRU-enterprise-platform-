"""Iteration 13 backend tests — Treasure Standard™ Improvement Loop, Enterprise Readiness
Review + Factory Acceptance Test endpoints, publish gate, product review endpoint."""
import os
import time
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def founder_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth(founder_token):
    return {"Authorization": f"Bearer {founder_token}"}


# ================= AUTH / FOUNDER LOGIN =================
class TestFounderAuth:
    def test_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data.get("user", {}).get("email") == FOUNDER_EMAIL

    def test_setup_status_flags_temporary(self, auth):
        r = requests.get(f"{BASE_URL}/api/auth/setup-status", headers=auth, timeout=15)
        assert r.status_code == 200
        data = r.json()
        # Founder is on temporary password by design; must expose flag(s)
        assert data.get("using_temporary_password") is True or data.get("setup_required") is True


# ================= ENTERPRISE READINESS =================
class TestEnterpriseReadiness:
    def test_readiness_shape(self, auth):
        r = requests.get(f"{BASE_URL}/api/enterprise/readiness", headers=auth, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data.get("readiness_score"), int)
        assert 0 <= data["readiness_score"] <= 100
        assert data.get("overall") in ("ready", "needs_attention")
        checks = data.get("checks")
        assert isinstance(checks, list) and len(checks) > 0
        for c in checks:
            assert set(c.keys()) >= {"area", "label", "status", "detail"}
            assert c["status"] in ("pass", "warn", "fail")
        assert data.get("recipes", 0) > 0
        assert data.get("packages", 0) > 0


# ================= FACTORY ACCEPTANCE TEST =================
class TestFactoryAcceptanceTest:
    def test_fat_shape(self, auth):
        r = requests.get(f"{BASE_URL}/api/enterprise/factory-acceptance-test",
                         headers=auth, timeout=15)
        assert r.status_code == 200
        data = r.json()
        eqs = data.get("enterprise_quality_score")
        assert isinstance(eqs, int) and 0 <= eqs <= 100
        assert isinstance(data.get("production_ready"), bool)
        modules = data.get("modules")
        assert isinstance(modules, list) and len(modules) == 12, f"Expected 12 modules got {len(modules) if modules else 0}"
        for m in modules:
            assert set(m.keys()) >= {"module", "score", "status", "note"}
            assert isinstance(m["score"], int) and 0 <= m["score"] <= 100
            assert m["status"] in ("ready", "good", "attention")
        lifecycle = data.get("lifecycle")
        assert isinstance(lifecycle, list) and len(lifecycle) > 0


# ================= TREASURE STANDARD IMPROVEMENT LOOP (LLM, ~2-4 min) =================
def _get_verified_kr(auth):
    r = requests.get(f"{BASE_URL}/api/knowledge-records", headers=auth, timeout=30)
    assert r.status_code == 200
    for kr in r.json():
        if kr.get("verification_status") == "Verified":
            return kr
    pytest.skip("No verified Knowledge Record available for Treasure Standard test")


class TestTreasureStandardImprovementLoop:
    def test_manufacture_and_improvement_loop(self, auth):
        kr = _get_verified_kr(auth)
        payload = {"product_types": ["Blog Article"]}
        r = requests.post(f"{BASE_URL}/api/automation/manufacture/{kr['id']}",
                          json=payload, headers=auth, timeout=30)
        assert r.status_code == 200, r.text
        order = r.json()
        assert order["total"] == 1
        oid = order["id"]

        # Poll up to ~4 minutes (loop can do verify → improve → re-verify twice)
        final = None
        for _ in range(80):  # 80 * 3s = 240s
            time.sleep(3)
            r = requests.get(f"{BASE_URL}/api/automation/orders/{oid}", headers=auth, timeout=15)
            assert r.status_code == 200
            o = r.json()
            if o["status"] in ("completed", "completed_with_errors", "failed"):
                final = o
                break
        assert final is not None, "manufacture order timed out (>4min)"
        assert final["status"] in ("completed", "completed_with_errors"), f"Order not completed: {final.get('status')}"

        item = final["items"][0]
        pid = item.get("product_id")
        assert pid, f"Product not produced: {item}"

        # Fetch product
        r = requests.get(f"{BASE_URL}/api/products/{pid}", headers=auth, timeout=15)
        assert r.status_code == 200
        prod = r.json()
        assert prod.get("production_order_id") == oid, f"production_order_id mismatch: {prod.get('production_order_id')} vs {oid}"

        # Two acceptable outcomes: Published+verified+treasure_standard OR Needs Review + open quality escalation
        status = prod.get("status")
        if status == "Published":
            assert prod.get("verified") is True, "Published product must be verified"
            assert prod.get("treasure_standard") is True, "Published product must meet Treasure Standard"
            # improvement_history may be present (0+ entries) — allowed
        elif status == "Needs Review":
            # Verify open quality escalation exists for this product
            r = requests.get(f"{BASE_URL}/api/verification/escalations", headers=auth, timeout=15)
            assert r.status_code == 200
            escs = r.json()
            match = [e for e in escs if e.get("product_id") == pid and e.get("type") == "quality" and e.get("status") == "Open"]
            assert match, f"No open quality escalation found for product {pid} that could not reach Treasure Standard"
        else:
            pytest.fail(f"Unexpected product status after improvement loop: {status}")

        # NOTE: Confirms no manual founder click was required — status is a terminal state (Published or Needs Review with auto-escalation).
        # improvement_history should exist as a field (may be [] if standard hit on first verify)
        hist = prod.get("improvement_history")
        assert hist is None or isinstance(hist, list)

    # Save the produced product id for downstream tests via class scope
    # (each pytest test method is independent; downstream tests self-fetch)


# ================= PUBLISH GATE ENFORCEMENT =================
class TestPublishGate:
    def test_publish_gate_blocks_unverified(self, auth):
        # Find a product that is NOT verified — create one via manufacture in Manual mode is heavy;
        # instead find an existing unverified product OR use a product with verified=False if any.
        r = requests.get(f"{BASE_URL}/api/products", headers=auth, timeout=15)
        assert r.status_code == 200
        products = r.json()
        unverified = [p for p in products if not p.get("verified") and p.get("status") not in ("Published",)]
        if not unverified:
            pytest.skip("No unverified product available to test publish gate")
        pid = unverified[0]["id"]
        r = requests.patch(f"{BASE_URL}/api/products/{pid}/status",
                           json={"status": "Published"}, headers=auth, timeout=15)
        assert r.status_code == 400, f"Expected 400 but got {r.status_code}: {r.text}"


# ================= PRODUCT REVIEW ENDPOINT =================
class TestProductReview:
    def _find_product(self, auth, want_status=None):
        r = requests.get(f"{BASE_URL}/api/products", headers=auth, timeout=15)
        assert r.status_code == 200
        for p in r.json():
            if want_status is None or p.get("status") == want_status:
                return p
        return None

    def test_review_reject_sets_rejected(self, auth):
        # Prefer a Needs Review or In Review product; else any non-Rejected/Published one
        prod = None
        for status in ("Needs Review", "In Review", "Draft"):
            prod = self._find_product(auth, status)
            if prod:
                break
        if not prod:
            # fall back to any product not already Rejected
            r = requests.get(f"{BASE_URL}/api/products", headers=auth, timeout=15)
            for p in r.json():
                if p.get("status") != "Rejected":
                    prod = p
                    break
        if not prod:
            pytest.skip("No product available to test review reject")
        pid = prod["id"]
        r = requests.post(f"{BASE_URL}/api/automation/products/{pid}/review",
                          json={"decision": "reject"}, headers=auth, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "Rejected"
        # Verify persistence
        r = requests.get(f"{BASE_URL}/api/products/{pid}", headers=auth, timeout=15)
        assert r.status_code == 200
        assert r.json()["status"] == "Rejected"

    def test_review_approve_publishes(self, auth):
        # Find a Rejected/Needs Review product to approve — approving should publish + distribute.
        # This call may re-verify via LLM, so use short timeout tolerance.
        prod = None
        for status in ("Needs Review", "In Review", "Rejected", "Draft"):
            prod = self._find_product(auth, status)
            if prod:
                break
        if not prod:
            pytest.skip("No product available to test review approve")
        pid = prod["id"]
        r = requests.post(f"{BASE_URL}/api/automation/products/{pid}/review",
                          json={"decision": "approve"}, headers=auth, timeout=120)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("status") == "Published", f"Expected Published, got {body}"
        # Persistence + verified flag flipped
        r = requests.get(f"{BASE_URL}/api/products/{pid}", headers=auth, timeout=15)
        assert r.status_code == 200
        p = r.json()
        assert p["status"] == "Published"
        assert p.get("verified") is True

    def test_review_invalid_product(self, auth):
        r = requests.post(f"{BASE_URL}/api/automation/products/nonexistent-id-abc/review",
                          json={"decision": "reject"}, headers=auth, timeout=15)
        assert r.status_code == 404
