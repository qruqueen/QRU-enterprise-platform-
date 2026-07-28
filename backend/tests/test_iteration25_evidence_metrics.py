"""Iteration 25: Evidence Metrics Engine + Universal Connector Framework backend tests.

Verifies:
- /api/metrics/summary returns metrics with real provenance (TEST/LIVE/NOT_TRACKED)
- /api/metrics/{id}/evidence returns real records or honest empty state
- /api/metrics/beta-status returns Founder Beta Status™ panel data
- Revenue is REAL Stripe payment records (not synthetic)
- /api/connectors lists Universal Connector Framework entries
- /api/command-center/mission-impact business Revenue is real (not synthetic)
- /api/dashboard/stats revenue is real (not synthetic)
"""
import os
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def H(token):
    return {"Authorization": f"Bearer {token}"}


# -------- /api/metrics/summary ---------------------------------------------
class TestMetricsSummary:
    def test_summary_ok(self, H):
        r = requests.get(f"{BASE_URL}/api/metrics/summary", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "metrics" in d and isinstance(d["metrics"], list)
        assert d["pay_mode"] == "TEST", f"Expected TEST mode, got {d['pay_mode']}"
        assert d["stripe_test"] is True
        assert d["groups"] == ["Commerce", "Manufacturing", "Publishing"]

    def test_summary_has_expected_metric_ids(self, H):
        d = requests.get(f"{BASE_URL}/api/metrics/summary", headers=H, timeout=30).json()
        ids = {m["id"] for m in d["metrics"]}
        for req in ("revenue", "paid_orders", "refunds", "subscriptions",
                    "products", "knowledge_records", "published", "connector_status"):
            assert req in ids, f"Missing metric id: {req}"

    def test_revenue_metric_is_real_not_synthetic(self, H):
        d = requests.get(f"{BASE_URL}/api/metrics/summary", headers=H, timeout=30).json()
        m = next(x for x in d["metrics"] if x["id"] == "revenue")
        # provenance is TEST (there is 1 paid order per task context) OR NOT_TRACKED if none
        assert m["provenance"] in ("TEST", "NOT_TRACKED"), m["provenance"]
        # value must NEVER be the old synthetic ~11450 number
        assert m["value"] != 11450
        assert m["value"] < 1000, f"Revenue looks synthetic: {m['value']}"
        # display must start with $
        assert m["display"].startswith("$")

    def test_paid_orders_provenance_TEST(self, H):
        d = requests.get(f"{BASE_URL}/api/metrics/summary", headers=H, timeout=30).json()
        m = next(x for x in d["metrics"] if x["id"] == "paid_orders")
        assert m["provenance"] in ("TEST", "NOT_TRACKED")

    def test_refunds_and_subscriptions_not_tracked(self, H):
        d = requests.get(f"{BASE_URL}/api/metrics/summary", headers=H, timeout=30).json()
        refunds = next(x for x in d["metrics"] if x["id"] == "refunds")
        subs = next(x for x in d["metrics"] if x["id"] == "subscriptions")
        assert refunds["provenance"] == "NOT_TRACKED"
        assert subs["provenance"] == "NOT_TRACKED"
        assert refunds["value"] == 0
        assert subs["value"] == 0

    def test_products_and_kr_and_published_are_LIVE(self, H):
        d = requests.get(f"{BASE_URL}/api/metrics/summary", headers=H, timeout=30).json()
        for mid in ("products", "knowledge_records", "published"):
            m = next(x for x in d["metrics"] if x["id"] == mid)
            assert m["provenance"] == "LIVE", f"{mid} provenance={m['provenance']}"

    def test_connector_status_display(self, H):
        d = requests.get(f"{BASE_URL}/api/metrics/summary", headers=H, timeout=30).json()
        m = next(x for x in d["metrics"] if x["id"] == "connector_status")
        assert m["provenance"] == "LIVE"
        assert "/" in m["display"], f"expected N/M format: {m['display']}"


# -------- /api/metrics/{id}/evidence ---------------------------------------
class TestEvidence:
    def test_revenue_evidence_records(self, H):
        r = requests.get(f"{BASE_URL}/api/metrics/revenue/evidence", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "columns" in d and "records" in d
        if d["records"]:
            row = d["records"][0]
            assert row.get("mode") == "TEST"
            for key in ("order_id", "product", "customer", "revenue", "payment_status"):
                assert key in row

    def test_paid_orders_evidence(self, H):
        r = requests.get(f"{BASE_URL}/api/metrics/paid_orders/evidence", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d.get("provenance") in ("TEST", "NOT_TRACKED")

    def test_refunds_empty_state(self, H):
        r = requests.get(f"{BASE_URL}/api/metrics/refunds/evidence", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["records"] == []
        assert d["provenance"] == "NOT_TRACKED"
        assert "refund" in d["empty_message"].lower()

    def test_subscriptions_empty_state(self, H):
        r = requests.get(f"{BASE_URL}/api/metrics/subscriptions/evidence", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["records"] == []
        assert d["provenance"] == "NOT_TRACKED"

    def test_products_evidence_populated(self, H):
        r = requests.get(f"{BASE_URL}/api/metrics/products/evidence", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["provenance"] == "LIVE"
        assert isinstance(d["records"], list)
        assert len(d["columns"]) > 0

    def test_knowledge_records_evidence(self, H):
        r = requests.get(f"{BASE_URL}/api/metrics/knowledge_records/evidence", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["provenance"] == "LIVE"

    def test_unknown_metric_404(self, H):
        r = requests.get(f"{BASE_URL}/api/metrics/not_a_thing/evidence", headers=H, timeout=30)
        assert r.status_code == 404


# -------- /api/metrics/beta-status -----------------------------------------
class TestBetaStatus:
    def test_beta_status_founder_preview(self, H):
        # simulate preview host
        r = requests.get(f"{BASE_URL}/api/metrics/beta-status",
                         params={"host": "understanding-os.preview.emergentagent.com"},
                         headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["deployment_state"] == "Founder Preview (Private Beta)"
        assert d["shareable"] == "LIMITED"
        assert d["pay_mode"] == "TEST"
        assert d["stripe_test"] is True
        assert isinstance(d["questions"], list)
        assert len(d["questions"]) >= 17, f"expected ~19 questions, got {len(d['questions'])}"
        assert isinstance(d["blocks_promotion"], list) and d["blocks_promotion"]
        assert d["is_production"] is False
        assert isinstance(d["operational_connectors"], list)
        assert "QRU Store™" in d["operational_connectors"]


# -------- /api/connectors --------------------------------------------------
class TestConnectors:
    def test_list_connectors(self, H):
        r = requests.get(f"{BASE_URL}/api/connectors", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "connectors" in d
        cs = d["connectors"]
        assert len(cs) >= 10, f"expected many connectors, got {len(cs)}"
        # QRU Store should be Connected/Healthy
        qru = next(c for c in cs if c["id"] == "qru_store")
        assert qru["status"] in ("Connected Healthy", "Connected")
        assert qru["operational"] is True
        assert qru["can_publish"] is True
        # Stripe operational, but publishing not applicable — accept either shape
        stripe = next(c for c in cs if c["id"] == "stripe")
        assert stripe["operational"] is True
        # non-operational entries have honest publish_disabled_reason
        for c in cs:
            if not c["operational"]:
                assert c["can_publish"] is False
                assert c["publish_disabled_reason"], f"{c['id']} missing publish disabled reason"


# -------- Regression: dashboard + mission-impact revenue -------------------
class TestRevenueRegression:
    def test_dashboard_stats_revenue_real(self, H):
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        # must not be the old synthetic ~11450 number
        assert d.get("revenue") != 11450
        assert d.get("revenue", 0) < 1000, f"Revenue looks synthetic: {d.get('revenue')}"

    def test_mission_impact_business_revenue_real(self, H):
        r = requests.get(f"{BASE_URL}/api/command-center/mission-impact", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        rev = next(b for b in d["business"] if b["label"] == "Revenue")
        assert rev["value"] != 11450
        assert rev["value"] < 1000, f"Business revenue looks synthetic: {rev['value']}"
        assert rev.get("provenance") == "TEST"
