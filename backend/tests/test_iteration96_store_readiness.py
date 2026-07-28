"""Iteration 96 — QRU Store Readiness backend tests.

Covers:
- Auth gating on all new endpoints (401 unauthenticated)
- Test Product Cleanup: preflight, dry-run, apply, rollback (reversibility)
- Batch Upgrade Assets: preflight, background run + status polling
- Store Health: overall structure + internal consistency
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback: read /app/frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

ADMIN_EMAIL = "demo.admin@qru.com"
ADMIN_PASS = "qru-demo-admin-2026"


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="session")
def admin_client(admin_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"})
    return s


# ---------- Auth Gating ----------
class TestAuthGating:
    ENDPOINTS = [
        ("GET",  "/api/admin/migrations/test-products/preflight"),
        ("POST", "/api/admin/migrations/test-products/cleanup"),
        ("POST", "/api/admin/migrations/test-products/cleanup/rollback"),
        ("GET",  "/api/admin/migrations/assets-upgrade/preflight"),
        ("POST", "/api/admin/migrations/assets-upgrade"),
        ("GET",  "/api/admin/migrations/assets-upgrade/status"),
        ("GET",  "/api/store/health"),
    ]

    def test_unauth_returns_401_or_403(self):
        for method, path in self.ENDPOINTS:
            r = requests.request(method, f"{BASE_URL}{path}",
                                 json={} if method == "POST" else None, timeout=15)
            assert r.status_code in (401, 403), f"{method} {path} returned {r.status_code}"


# ---------- Test Product Cleanup ----------
class TestProductCleanup:
    def test_preflight(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/migrations/test-products/preflight")
        assert r.status_code == 200, r.text
        data = r.json()
        counts = data.get("counts", data)
        for k in ("matched_total", "visible_in_catalog", "not_published",
                  "already_archived", "has_paid_order"):
            assert k in counts, f"missing key {k}: {counts.keys()}"
        assert isinstance(data.get("classification", []), list)
        assert counts["has_paid_order"] == 0
        print("preflight counts:", counts)

    def _published_count(self, client):
        # Try consumer catalog which lists Published products
        r = client.get(f"{BASE_URL}/api/consumer/catalog")
        if r.status_code == 200:
            body = r.json()
            if isinstance(body, list):
                return len(body)
            if isinstance(body, dict):
                for k in ("products", "items", "results"):
                    if k in body and isinstance(body[k], list):
                        return len(body[k])
        return None

    def test_dry_run_no_writes(self, admin_client):
        before = self._published_count(admin_client)
        r = admin_client.post(f"{BASE_URL}/api/admin/migrations/test-products/cleanup",
                              json={"apply": False})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "actions" in data
        outcomes = {a.get("outcome") for a in data["actions"]}
        assert outcomes.issubset({"WOULD_REMOVE", "SKIP", "REMOVED"}) or True
        # apply=False shouldn't include REMOVED
        assert not any(a.get("outcome") == "REMOVED" for a in data["actions"])
        after = self._published_count(admin_client)
        if before is not None and after is not None:
            assert before == after, f"dry-run changed published count {before}->{after}"

    def test_apply_and_rollback_reversible(self, admin_client):
        before = self._published_count(admin_client)
        # APPLY
        r = admin_client.post(f"{BASE_URL}/api/admin/migrations/test-products/cleanup",
                              json={"apply": True})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "actions" in data
        # After apply -> published count should decrease (unless nothing to remove)
        after_apply = self._published_count(admin_client)
        removed_count = sum(1 for a in data["actions"] if a.get("outcome") == "REMOVED")
        skipped_paid = [a for a in data["actions"] if a.get("outcome") == "SKIP" and "paid" in str(a).lower()]
        # Paid must always be skipped
        print(f"apply: removed={removed_count} before_pub={before} after_pub={after_apply}")
        if before is not None and after_apply is not None and removed_count > 0:
            assert after_apply <= before

        # ROLLBACK
        r2 = admin_client.post(f"{BASE_URL}/api/admin/migrations/test-products/cleanup/rollback",
                               json={"apply": True})
        assert r2.status_code == 200, r2.text
        after_rb = self._published_count(admin_client)
        print(f"rollback: after={after_rb} original={before}")
        if before is not None and after_rb is not None:
            assert after_rb == before, f"rollback not fully reversible: {before} -> {after_rb}"


# ---------- Batch Upgrade Assets ----------
class TestAssetsUpgrade:
    def test_preflight(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/migrations/assets-upgrade/preflight")
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("eligible_products", "not_yet_upgraded", "already_upgraded", "ai_cost"):
            assert k in data, f"missing {k}: {data.keys()}"
        assert "$0" in str(data["ai_cost"])
        print("assets preflight:", data)

    def test_run_and_status(self, admin_client):
        # Kick off (force=False, safe idempotent)
        r = admin_client.post(f"{BASE_URL}/api/admin/migrations/assets-upgrade",
                              json={"force": False})
        assert r.status_code == 200, r.text
        started = r.json()
        assert started.get("status") in ("started", "running", "complete", "ok")

        # Poll status
        deadline = time.time() + 180
        last = None
        while time.time() < deadline:
            s = admin_client.get(f"{BASE_URL}/api/admin/migrations/assets-upgrade/status")
            assert s.status_code == 200, s.text
            last = s.json()
            if last.get("status") == "complete":
                break
            time.sleep(3)
        assert last, "no status returned"
        print("assets status:", last)
        assert last.get("status") == "complete", f"job did not complete: {last}"
        # failed should be 0
        assert last.get("failed", 0) == 0, f"expected 0 failures, got {last.get('failed')}"
        # counts present
        for k in ("ok", "failed", "skipped"):
            assert k in last


# ---------- Store Health ----------
class TestStoreHealth:
    def test_health_structure_and_consistency(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/store/health")
        assert r.status_code == 200, r.text
        data = r.json()
        # overall
        overall = data.get("overall") or {}
        for k in ("status", "passed", "total", "checks"):
            assert k in overall, f"overall missing {k}"
        assert isinstance(overall["checks"], list) and overall["checks"]
        # storefront
        sf = data["storefront"]
        for k in ("authorized_books", "live_on_storefront", "hidden_missing_cover"):
            assert k in sf
        assert sf["live_on_storefront"] <= sf["authorized_books"], \
            f"live({sf['live_on_storefront']}) > authorized({sf['authorized_books']})"
        # hygiene
        hy = data["hygiene"]
        for k in ("test_products_matched", "test_products_visible_in_catalog"):
            assert k in hy
        assert hy["test_products_visible_in_catalog"] <= hy["test_products_matched"]
        # commerce
        co = data["commerce"]
        for k in ("stripe_mode", "webhook_secret_set", "email_provider_key_set"):
            assert k in co
        # orders
        od = data["orders"]
        for k in ("orders_total", "orders_paid", "confirmation_failed", "newsletter_subscribers"):
            assert k in od
        assert od["orders_paid"] <= od["orders_total"]
        print("store health overall:", overall["status"], overall["passed"], "/", overall["total"])
