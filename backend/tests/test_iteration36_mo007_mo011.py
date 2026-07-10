"""Iteration 36 — MO-007 connector expansion (devto/shopify) + MO-011 Media Starter Kit™.

Treasure Standard™: no live third-party credentials. Validates honest NEEDS_SETUP states,
400 validation paths, and deterministic Media Starter Kit™ engine.
"""
import os
import pytest
import requests
from pathlib import Path


def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    env_file = Path("/app/frontend/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not configured")


BASE_URL = _load_backend_url()
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def sample_product_id(auth_headers):
    r = requests.get(f"{BASE_URL}/api/founder-inbox", headers=auth_headers, timeout=30)
    assert r.status_code == 200, f"founder-inbox failed: {r.status_code}"
    prods = r.json().get("products", [])
    assert prods, "No products in founder inbox — cannot test MO-011"
    return prods[0]["id"]


# ============================================================ MO-007 CONNECTORS
class TestMO007Connectors:
    def test_connectors_list_shape(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/distribution/connectors", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        items = r.json()["connectors"]
        ids = [c["id"] for c in items]
        # Expect 9 connectors total (per problem statement)
        assert len(items) == 9, f"Expected 9 connectors, got {len(items)}: {ids}"
        for req in ("qru_store", "youtube", "wordpress", "devto", "shopify",
                    "google_drive", "email", "etsy", "amazon_kdp"):
            assert req in ids, f"Missing connector: {req}"

    def test_devto_configurable_fields(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/distribution/connectors", headers=auth_headers, timeout=30)
        devto = next(c for c in r.json()["connectors"] if c["id"] == "devto")
        assert devto["configurable"] is True
        assert devto["config_fields"] == ["api_key"]
        assert "api_key" in devto["config_secret"]
        assert devto["config_hint"], "config_hint must be present"
        # Honest: unconfigured => can_distribute=False
        assert devto["can_distribute"] is False, f"devto should not be able to distribute unconfigured: {devto}"

    def test_shopify_configurable_fields(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/distribution/connectors", headers=auth_headers, timeout=30)
        sh = next(c for c in r.json()["connectors"] if c["id"] == "shopify")
        assert sh["configurable"] is True
        assert sh["config_fields"] == ["store_domain", "access_token"]
        assert "access_token" in sh["config_secret"]
        assert sh["config_hint"]
        assert sh["can_distribute"] is False

    def test_wordpress_configurable_fields(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/distribution/connectors", headers=auth_headers, timeout=30)
        wp = next(c for c in r.json()["connectors"] if c["id"] == "wordpress")
        assert wp["configurable"] is True
        assert wp["config_fields"] == ["site_url", "username", "app_password"]
        assert "app_password" in wp["config_secret"]

    def test_etsy_not_configurable(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/distribution/connectors", headers=auth_headers, timeout=30)
        etsy = next(c for c in r.json()["connectors"] if c["id"] == "etsy")
        assert etsy["configurable"] is False

    def test_config_rejects_non_configurable(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/distribution/connectors/etsy/config",
                          headers=auth_headers, json={"credentials": {"foo": "bar"}}, timeout=30)
        assert r.status_code == 400, f"expected 400, got {r.status_code} {r.text[:200]}"
        assert "not configurable" in r.text.lower()

    def test_config_rejects_missing_required_devto(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/distribution/connectors/devto/config",
                          headers=auth_headers, json={"credentials": {}}, timeout=30)
        assert r.status_code == 400
        assert "api_key" in r.text.lower()

    def test_config_rejects_missing_required_shopify(self, auth_headers):
        # missing access_token
        r = requests.post(f"{BASE_URL}/api/distribution/connectors/shopify/config",
                          headers=auth_headers,
                          json={"credentials": {"store_domain": "example.myshopify.com"}}, timeout=30)
        assert r.status_code == 400
        assert "access_token" in r.text.lower()

    def test_config_rejects_missing_required_wordpress(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/distribution/connectors/wordpress/config",
                          headers=auth_headers,
                          json={"credentials": {"site_url": "https://example.com"}}, timeout=30)
        assert r.status_code == 400
        body = r.text.lower()
        assert "username" in body and "app_password" in body

    def test_config_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/distribution/connectors/devto/config",
                          json={"credentials": {"api_key": "x"}}, timeout=30)
        assert r.status_code in (401, 403), f"expected 401/403 without auth, got {r.status_code}"


# ============================================================ MO-011 MEDIA STARTER KIT
class TestMO011MediaStarterKit:
    def test_config_returns_13_components_and_8_outputs(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/media-starter-kit/config", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        cfg = data["config"]
        assert len(cfg["components"]) == 13, f"Expected 13 components, got {len(cfg['components'])}"
        assert len(cfg["outputs"]) == 8, f"Expected 8 outputs, got {len(cfg['outputs'])}"
        assert cfg["enabled"] is True
        assert "component_labels" in data and "output_labels" in data
        assert set(data["component_labels"].keys()) == set(cfg["components"])
        assert set(data["output_labels"].keys()) == set(cfg["outputs"])

    def test_kit_shape_for_real_product(self, auth_headers, sample_product_id):
        r = requests.get(f"{BASE_URL}/api/media-starter-kit/kit/{sample_product_id}",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200, f"kit failed: {r.status_code} {r.text[:200]}"
        k = r.json()
        # Gate
        assert "gate" in k
        assert "treasure_standard" in k["gate"]
        assert "gold_standard" in k["gate"]
        assert isinstance(k["gate"]["passed"], bool)
        # 13 components
        assert isinstance(k["components"], dict) and len(k["components"]) == 13
        for cname, comp in k["components"].items():
            assert comp["status"] in ("ready", "pending"), f"{cname}: {comp['status']}"
            assert "source" in comp and "detail" in comp
        # Completeness 0-100
        assert 0 <= k["kit_completeness"] <= 100
        assert k["ready_count"] <= k["component_total"] == 13
        # 8 outputs
        assert isinstance(k["outputs"], list) and len(k["outputs"]) == 8
        for o in k["outputs"]:
            assert o["status"] in ("ready_to_produce", "blocked")
            assert "requires" in o and "missing" in o

    def test_kit_404_for_missing_product(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/media-starter-kit/kit/NOPE-NOT-A-PRODUCT",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 404

    def test_generate_gated_behavior(self, auth_headers, sample_product_id):
        # Peek gate first
        r = requests.get(f"{BASE_URL}/api/media-starter-kit/kit/{sample_product_id}",
                         headers=auth_headers, timeout=30)
        gate_passed = r.json()["gate"]["passed"]

        rg = requests.post(f"{BASE_URL}/api/media-starter-kit/generate/{sample_product_id}",
                           headers=auth_headers, timeout=30)
        if gate_passed:
            assert rg.status_code == 200, f"expected 200 when gate passed, got {rg.status_code} {rg.text[:200]}"
            record = rg.json()
            assert record.get("product_id") == sample_product_id
            assert "kit" in record and "_id" not in record
        else:
            assert rg.status_code == 400, f"expected 400 when gate blocked, got {rg.status_code} {rg.text[:200]}"
            # The detail should mention Treasure Standard
            assert "treasure" in rg.text.lower() or "standard" in rg.text.lower()

    def test_generate_blocked_for_missing_product(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/media-starter-kit/generate/NOPE-NOT-A-PRODUCT",
                          headers=auth_headers, timeout=30)
        assert r.status_code == 404

    def test_kits_list(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/media-starter-kit/kits", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "kits" in data and isinstance(data["kits"], list)
        for k in data["kits"]:
            assert "_id" not in k

    def test_governance_binding_media(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/governance-binding/strip/media",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200
        gov = r.json().get("governed_by", [])
        assert len(gov) >= 2, f"expected >=2 governing standards for 'media', got {gov}"
