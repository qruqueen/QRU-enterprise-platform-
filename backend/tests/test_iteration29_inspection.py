"""Iteration 29 — QRU Manufacturing Inspection System™ (MO-001 / P4).

Tests deterministic quality gates ($0 AI):
 - GET /api/inspection/summary
 - GET /api/inspection/product/{id}
 - GET /api/inspection/knowledge-record/{id}
 - GATE ENFORCEMENT via POST /api/automation/manufacture/{kr_id}
 - Regression: /api/connectors, /api/evidence
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


# --------- fixtures ---------
@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    body = r.json()
    tok = body.get("access_token") or body.get("token")
    assert tok, f"no token in login response: {body}"
    return tok


@pytest.fixture(scope="module")
def api(token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    return s


# --------- /gates registry ---------
class TestGateRegistry:
    def test_gates_registry(self, api):
        r = api.get(f"{BASE_URL}/api/inspection/gates")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "gates" in body
        keys = [g["key"] for g in body["gates"]]
        expected = ["knowledge_completeness", "verification_completeness", "educational_value",
                    "consumer_clarity", "visual_readiness", "product_eligibility",
                    "connector_readiness", "publication_readiness", "treasure_standard"]
        assert keys == expected, f"gate order/keys mismatch: {keys}"
        # blocking flags per spec
        blocking = {g["key"]: g["blocking"] for g in body["gates"]}
        assert blocking["knowledge_completeness"] is True
        assert blocking["verification_completeness"] is True
        assert blocking["educational_value"] is False
        assert blocking["consumer_clarity"] is False
        assert blocking["visual_readiness"] is False
        assert blocking["product_eligibility"] is True
        assert blocking["connector_readiness"] is False
        assert blocking["publication_readiness"] is True
        assert blocking["treasure_standard"] is True


# --------- /summary ---------
class TestSummary:
    def test_summary_structure(self, api):
        r = api.get(f"{BASE_URL}/api/inspection/summary")
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("total", "cleared", "paused", "operational_connectors", "products"):
            assert k in d, f"missing key: {k}"
        assert isinstance(d["products"], list)
        assert d["total"] == len(d["products"])
        assert d["cleared"] + d["paused"] == d["total"]
        # expect ~125 products per spec (allow some tolerance because tests may create some)
        assert d["total"] >= 100, f"expected many products, got {d['total']}"

    def test_summary_product_row_shape(self, api):
        r = api.get(f"{BASE_URL}/api/inspection/summary")
        d = r.json()
        assert len(d["products"]) > 0
        p = d["products"][0]
        for k in ("id", "product_code", "title", "status", "overall_score",
                  "gate_status", "blocking_failures"):
            assert k in p, f"row missing {k}: {p}"
        assert p["gate_status"] in ("Cleared", "Paused")
        assert isinstance(p["overall_score"], int)
        assert 0 <= p["overall_score"] <= 100
        assert isinstance(p["blocking_failures"], list)

    def test_summary_paused_majority(self, api):
        # Per spec: most products are Paused.
        d = api.get(f"{BASE_URL}/api/inspection/summary").json()
        assert d["paused"] >= d["cleared"], (
            f"expected majority Paused; cleared={d['cleared']} paused={d['paused']}")


# --------- /product/{id} ---------
class TestProductInspection:
    def test_product_detail(self, api):
        d = api.get(f"{BASE_URL}/api/inspection/summary").json()
        pid = d["products"][0]["id"]
        r = api.get(f"{BASE_URL}/api/inspection/product/{pid}")
        assert r.status_code == 200, r.text
        rep = r.json()
        for k in ("overall_score", "manufacturing_allowed", "status", "gates",
                  "blocking_failures", "director_report", "subject"):
            assert k in rep
        assert len(rep["gates"]) == 9, f"expected 9 gates, got {len(rep['gates'])}"
        for g in rep["gates"]:
            for k in ("key", "label", "threshold", "blocking", "score", "passed", "findings"):
                assert k in g, f"gate missing {k}: {g}"
            assert isinstance(g["findings"], list)
        dr = rep["director_report"]
        for k in ("verdict", "missing_information", "blocking_gates"):
            assert k in dr

    def test_product_404(self, api):
        r = api.get(f"{BASE_URL}/api/inspection/product/nonexistent-id-xyz")
        assert r.status_code == 404


# --------- /knowledge-record/{id} ---------
class TestKRInspection:
    def _kr_by_code(self, api, code):
        # Try to find a KR by kr_code. Endpoint: /api/knowledge-records
        r = api.get(f"{BASE_URL}/api/knowledge-records")
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("records", []))
        for kr in items:
            if kr.get("kr_code") == code:
                return kr
        return None

    def test_kr_cleared_kr00047(self, api):
        kr = self._kr_by_code(api, "KR-00047")
        if not kr:
            pytest.skip("KR-00047 not found in this environment")
        r = api.get(f"{BASE_URL}/api/inspection/knowledge-record/{kr['id']}")
        assert r.status_code == 200, r.text
        rep = r.json()
        assert rep["status"] == "Cleared", f"KR-00047 expected Cleared, got: {rep}"
        assert rep["manufacturing_allowed"] is True
        assert rep["overall_score"] >= 90

    def test_kr_thin_paused(self, api):
        # Find any unverified/thin KR
        r = api.get(f"{BASE_URL}/api/knowledge-records")
        if r.status_code != 200:
            pytest.skip("KR listing endpoint not available")
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("records", []))
        # pick a KR that is Unverified or thin
        thin = None
        for kr in items:
            if kr.get("verification_status") != "Verified":
                thin = kr
                break
        if not thin:
            pytest.skip("no unverified KR available to test paused state")
        r = api.get(f"{BASE_URL}/api/inspection/knowledge-record/{thin['id']}")
        assert r.status_code == 200
        rep = r.json()
        assert rep["status"] == "Paused"
        assert rep["manufacturing_allowed"] is False
        assert len(rep["blocking_failures"]) >= 1

    def test_kr_404(self, api):
        r = api.get(f"{BASE_URL}/api/inspection/knowledge-record/nonexistent-kr")
        assert r.status_code == 404


# --------- gate enforcement in /automation/manufacture ---------
class TestManufactureGateEnforcement:
    def _get_recipe(self, api):
        r = api.get(f"{BASE_URL}/api/automation/recipes")
        assert r.status_code == 200, r.text
        d = r.json()
        # RECIPES exposed as list of objects with product_type
        raw = d["recipes"] if isinstance(d, dict) and "recipes" in d else d
        if isinstance(raw, dict):
            names = list(raw.keys())
        else:
            names = [item.get("product_type") if isinstance(item, dict) else item for item in raw]
        names = [n for n in names if n]
        assert names, f"no recipe names from response: {d}"
        for pref in ("Blog Article", "Interactive Lesson", "Workbook", "Quiz"):
            if pref in names:
                return pref
        return names[0]

    def _find_kr(self, api, code=None, verified=None):
        r = api.get(f"{BASE_URL}/api/knowledge-records")
        if r.status_code != 200:
            return None
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("records", []))
        for kr in items:
            if code and kr.get("kr_code") == code:
                return kr
            if verified is True and kr.get("verification_status") == "Verified":
                return kr
            if verified is False and kr.get("verification_status") != "Verified":
                return kr
        return None

    def test_manufacture_paused_kr_returns_400(self, api):
        thin = self._find_kr(api, verified=False)
        if not thin:
            pytest.skip("no unverified KR available")
        recipe = self._get_recipe(api)
        r = api.post(f"{BASE_URL}/api/automation/manufacture/{thin['id']}",
                     json={"product_types": [recipe]})
        assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text[:300]}"
        msg = r.json().get("detail") or r.text
        assert "Manufacturing paused by the Inspection System" in str(msg), f"msg: {msg}"

    def test_manufacture_cleared_kr_creates_order(self, api):
        kr = self._find_kr(api, code="KR-00047")
        if not kr:
            kr = self._find_kr(api, verified=True)
        if not kr:
            pytest.skip("no cleared/verified KR available")
        # Confirm it's actually cleared
        insp = api.get(f"{BASE_URL}/api/inspection/knowledge-record/{kr['id']}").json()
        if insp.get("status") != "Cleared":
            pytest.skip(f"KR {kr.get('kr_code')} isn't cleared in current DB (score={insp.get('overall_score')})")
        recipe = self._get_recipe(api)
        r = api.post(f"{BASE_URL}/api/automation/manufacture/{kr['id']}",
                     json={"product_types": [recipe]})
        assert r.status_code in (200, 201), f"expected 200/201, got {r.status_code}: {r.text[:300]}"
        body = r.json()
        # order id should be present somewhere
        oid = body.get("id") or body.get("order_id") or (body.get("order") or {}).get("id")
        assert oid, f"no order id in response: {body}"


# --------- regression ---------
class TestRegression:
    def test_connectors_endpoint(self, api):
        r = api.get(f"{BASE_URL}/api/connectors")
        assert r.status_code == 200, r.text
        d = r.json()
        items = d if isinstance(d, list) else d.get("connectors", d.get("items", []))
        assert len(items) >= 20, f"expected >=20 connectors, got {len(items)}"

    def test_evidence_metrics(self, api):
        # Evidence dashboard powered by /api/metrics/summary
        r = api.get(f"{BASE_URL}/api/metrics/summary")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
        d = r.json()
        # find a metric id to drill into
        metrics = d.get("metrics") if isinstance(d, dict) else None
        if metrics is None and isinstance(d, dict):
            for v in d.values():
                if isinstance(v, list) and v and isinstance(v[0], dict) and "id" in v[0]:
                    metrics = v
                    break
        if metrics:
            mid = metrics[0].get("id")
            if mid:
                r2 = api.get(f"{BASE_URL}/api/metrics/{mid}/evidence")
                assert r2.status_code == 200, f"evidence drilldown failed: {r2.status_code}"
