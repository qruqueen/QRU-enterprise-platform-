"""Iteration 35 — QRU Visual Intelligence Studio™ (MO-009) + Media Intelligence Division™ (MO-010).

Validates the four endpoints wired by the new /visual-studio page:
  * GET /api/visual-studio/config
  * GET /api/visual-studio/media/config
  * GET /api/visual-studio/analyze/{product_id}
  * GET /api/visual-studio/gold-review/{product_id}
Plus verifies the governance strip endpoint used by the page:
  * GET /api/governance-binding/strip/design
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def product_id(headers):
    # Use founder-inbox first (that's what the UI uses), fall back to /api/products
    r = requests.get(f"{BASE_URL}/api/founder-inbox", headers=headers, timeout=30)
    assert r.status_code == 200, f"founder-inbox failed: {r.status_code}"
    prods = r.json().get("products") or []
    if prods:
        pid = prods[0].get("id")
        assert pid
        return pid
    r2 = requests.get(f"{BASE_URL}/api/products", headers=headers, timeout=30)
    assert r2.status_code == 200
    plist = r2.json() if isinstance(r2.json(), list) else r2.json().get("products", [])
    assert plist, "No products in database"
    return plist[0]["id"]


# ----- Visual Studio config -----
class TestVisualStudioConfig:
    def test_config_endpoint(self, headers):
        r = requests.get(f"{BASE_URL}/api/visual-studio/config", headers=headers, timeout=30)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert "config" in body and "department_labels" in body
        c = body["config"]
        assert c.get("enabled") is True
        assert c.get("governing_standard") == "QRU Visual Intelligence Studio"
        assert isinstance(c.get("departments"), dict) and len(c["departments"]) >= 10
        assert isinstance(c.get("layout_rules"), dict) and len(c["layout_rules"]) >= 6
        assert isinstance(c.get("quality_checks"), dict) and len(c["quality_checks"]) >= 8
        # department_labels covers all department keys
        for k in c["departments"].keys():
            assert k in body["department_labels"], f"Missing label for department {k}"

    def test_config_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/visual-studio/config", timeout=15)
        assert r.status_code in (401, 403)


# ----- Media Intelligence config -----
class TestMediaConfig:
    def test_media_config(self, headers):
        r = requests.get(f"{BASE_URL}/api/visual-studio/media/config", headers=headers, timeout=30)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert "config" in body and "capabilities" in body
        caps = body["capabilities"]
        assert isinstance(caps.get("integrations"), list) and len(caps["integrations"]) >= 5
        assert isinstance(caps.get("live_count"), int)
        assert isinstance(caps.get("total"), int)
        assert caps["total"] == len(caps["integrations"])
        assert caps["live_count"] <= caps["total"]
        assert isinstance(caps.get("available_now"), list)
        # Honest: at least one integration explicitly needs a key
        needs_key = [i for i in caps["integrations"] if "needs_key" in i.get("status", "")]
        assert needs_key, "Expected at least one honest 'needs_key' integration"
        # Each integration well-formed
        for it in caps["integrations"]:
            assert set(["id", "name", "status", "note"]).issubset(it.keys())


# ----- Layout Intelligence analyze -----
class TestAnalyze:
    def test_analyze_valid_product(self, headers, product_id):
        r = requests.get(f"{BASE_URL}/api/visual-studio/analyze/{product_id}", headers=headers, timeout=30)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("product_id") == product_id
        assert isinstance(data.get("layout_score"), int)
        assert 0 <= data["layout_score"] <= 100
        assert isinstance(data.get("violations"), list)
        assert isinstance(data.get("passed"), bool)
        assert isinstance(data.get("word_count"), int)

    def test_analyze_missing_product(self, headers):
        r = requests.get(f"{BASE_URL}/api/visual-studio/analyze/does-not-exist-xyz", headers=headers, timeout=30)
        assert r.status_code == 404


# ----- Gold Standard review -----
class TestGoldReview:
    def test_gold_review_valid_product(self, headers, product_id):
        r = requests.get(f"{BASE_URL}/api/visual-studio/gold-review/{product_id}", headers=headers, timeout=30)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("product_id") == product_id
        assert isinstance(data.get("checks"), list) and len(data["checks"]) >= 8
        # honest: some checks must be human_review (subjective visual)
        statuses = {c["status"] for c in data["checks"]}
        assert "human_review" in statuses, "Expected honest 'human_review' status on subjective checks"
        assert data.get("treasure_standard") in ("Met", "Not Met")
        assert data.get("gold_standard")
        assert isinstance(data.get("auto_score"), int)
        assert 0 <= data["auto_score"] <= 100
        assert "layout" in data and isinstance(data["layout"], dict)

    def test_gold_review_missing_product(self, headers):
        r = requests.get(f"{BASE_URL}/api/visual-studio/gold-review/nonexistent-id-abc", headers=headers, timeout=30)
        assert r.status_code == 404


# ----- Governance strip (used by the Visual Studio GovernedBy component) -----
class TestGovernanceStrip:
    def test_strip_design(self, headers):
        r = requests.get(f"{BASE_URL}/api/governance-binding/strip/design", headers=headers, timeout=30)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert "governed_by" in body
        assert isinstance(body["governed_by"], list)
        # governance strip should list at least one governing document
        assert len(body["governed_by"]) >= 1
