"""Iteration 30 — QRU Enterprise Manufacturing Dashboard™ (MO-002 / P6).

Verifies deterministic aggregation endpoint GET /api/manufacturing-dashboard:
 - all required top-level keys with correct shapes
 - real (non-synthetic) values (KRs, products, connectors, revenue, quality)
 - provenance labels (LIVE / TEST / NOT_TRACKED)
 - alerts array is populated & actionable
 - connector_health has 23 rows
Regression: /inspection/summary and /connectors still work.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def api(token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="module")
def dashboard(api):
    r = api.get(f"{BASE_URL}/api/manufacturing-dashboard")
    assert r.status_code == 200, r.text
    return r.json()


# --- structure & shape ---
class TestDashboardStructure:
    def test_top_level_keys(self, dashboard):
        for k in ("knowledge_records", "products_manufactured", "products_in_queue",
                  "connector_status", "publishing_status", "revenue", "licensing",
                  "manufacturing_throughput", "quality_scores", "treasure_standard",
                  "connector_health", "alerts"):
            assert k in dashboard, f"missing top-level key: {k}"

    def test_knowledge_records(self, dashboard):
        kr = dashboard["knowledge_records"]
        assert "total" in kr and "verified" in kr and kr["provenance"] == "LIVE"
        assert isinstance(kr["total"], int) and kr["total"] > 0
        assert 0 <= kr["verified"] <= kr["total"]

    def test_products_manufactured(self, dashboard):
        p = dashboard["products_manufactured"]
        assert p["provenance"] == "LIVE"
        assert isinstance(p["total"], int) and p["total"] >= 100  # spec ~127
        assert 0 <= p["published"] <= p["total"]

    def test_products_in_queue(self, dashboard):
        q = dashboard["products_in_queue"]
        assert q["provenance"] == "LIVE"
        for k in ("value", "completed"):
            assert isinstance(q[k], int) and q[k] >= 0

    def test_connector_status_23(self, dashboard):
        c = dashboard["connector_status"]
        assert c["provenance"] == "LIVE"
        assert c["total"] == 23, f"expected 23 connectors, got {c['total']}"
        assert 0 <= c["operational"] <= 23

    def test_publishing(self, dashboard):
        pub = dashboard["publishing_status"]
        assert pub["provenance"] == "LIVE"
        assert isinstance(pub["published"], int) and pub["published"] >= 0
        # consistent with products_manufactured
        assert pub["published"] == dashboard["products_manufactured"]["published"]

    def test_revenue_real_and_test_provenance(self, dashboard):
        rev = dashboard["revenue"]
        # STRIPE_API_KEY is sk_test_ per spec → provenance MUST be TEST
        assert rev["provenance"] == "TEST", f"expected TEST, got {rev['provenance']}"
        assert isinstance(rev["value"], (int, float))
        assert rev["value"] >= 0
        assert isinstance(rev["orders"], int) and rev["orders"] >= 0
        # if there are orders, value must be > 0 (real payment_transactions)
        if rev["orders"] > 0:
            assert rev["value"] > 0

    def test_licensing_not_tracked_when_zero(self, dashboard):
        lic = dashboard["licensing"]
        assert isinstance(lic["value"], int)
        if lic["value"] == 0:
            assert lic["provenance"] == "NOT_TRACKED"
        else:
            assert lic["provenance"] == "LIVE"

    def test_throughput(self, dashboard):
        t = dashboard["manufacturing_throughput"]
        assert t["provenance"] == "LIVE"
        assert isinstance(t["last_7_days"], int) and t["last_7_days"] >= 0
        assert isinstance(t["total_orders"], int)
        assert t["last_7_days"] <= t["total_orders"]

    def test_quality_scores_matches_inspection(self, dashboard, api):
        qs = dashboard["quality_scores"]
        assert qs["provenance"] == "LIVE"
        assert 0 <= qs["average"] <= 100
        assert qs["cleared"] + qs["paused"] == dashboard["products_manufactured"]["total"]
        # cross-check against /api/inspection/summary
        r = api.get(f"{BASE_URL}/api/inspection/summary")
        if r.status_code == 200:
            s = r.json()
            assert qs["cleared"] == s["cleared"]
            assert qs["paused"] == s["paused"]

    def test_treasure_standard(self, dashboard):
        ts = dashboard["treasure_standard"]
        assert ts["provenance"] == "LIVE"
        assert isinstance(ts["certified"], int) and isinstance(ts["total"], int)
        assert 0 <= ts["certified"] <= ts["total"]

    def test_connector_health_23_rows(self, dashboard):
        health = dashboard["connector_health"]
        assert isinstance(health, list)
        assert len(health) == 23, f"expected 23 connector rows, got {len(health)}"
        for row in health:
            for k in ("name", "status", "operational", "category"):
                assert k in row, f"connector row missing {k}: {row}"
            assert isinstance(row["operational"], bool)
        # cross-check operational count with connector_status.operational
        ops = sum(1 for c in health if c["operational"])
        assert ops == dashboard["connector_status"]["operational"]

    def test_alerts_shape(self, dashboard):
        alerts = dashboard["alerts"]
        assert isinstance(alerts, list) and len(alerts) >= 1
        for a in alerts:
            assert "level" in a and a["level"] in ("warn", "info", "ok")
            assert "message" in a and isinstance(a["message"], str) and a["message"].strip()
            assert "link" in a  # may be None or a route string

    def test_alerts_include_paused_products(self, dashboard):
        # Per spec: 117 paused → there must be a paused-products alert linking to /inspection
        if dashboard["quality_scores"]["paused"] > 0:
            found = any(a.get("link") == "/inspection" and "paused" in a["message"].lower()
                        for a in dashboard["alerts"])
            assert found, f"expected paused-products alert w/ link=/inspection; alerts={dashboard['alerts']}"

    def test_alerts_include_stripe_test_mode(self, dashboard):
        # STRIPE test mode should surface an info alert
        found = any("test" in a["message"].lower() and a["level"] == "info"
                    for a in dashboard["alerts"])
        assert found, f"expected Stripe TEST mode info alert; alerts={dashboard['alerts']}"


# --- auth ---
class TestAuth:
    def test_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/manufacturing-dashboard")
        assert r.status_code in (401, 403), f"expected auth-required, got {r.status_code}"


# --- regression ---
class TestRegression:
    def test_inspection_summary_still_works(self, api):
        r = api.get(f"{BASE_URL}/api/inspection/summary")
        assert r.status_code == 200, r.text
        s = r.json()
        assert s["total"] > 0

    def test_connectors_still_23(self, api):
        r = api.get(f"{BASE_URL}/api/connectors")
        assert r.status_code == 200, r.text
        d = r.json()
        items = d if isinstance(d, list) else d.get("connectors", d.get("items", []))
        assert len(items) == 23, f"expected 23 connectors, got {len(items)}"
