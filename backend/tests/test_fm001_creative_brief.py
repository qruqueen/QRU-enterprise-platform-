"""FM-001 Creative Studio enhancement graceful degradation tests.

Verifies:
- POST /api/products/{pid}/creative-brief returns 200 with a fallback brief when the
  LLM provider is over its daily spend cap.
- Enhancement completes: creative_brief persisted, creative_status='Reviewed',
  enhancement_source='deterministic', enhancement_stage_note names AI Brief Writer.
- 404 clean detail when pid does not exist.
- Regression: GET /api/products and GET /api/products/{pid} still work.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://understanding-os.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PWD = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": FOUNDER_EMAIL, "password": FOUNDER_PWD}, timeout=30)
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
    # Prefer an Approved / Published product to match the FM-001 scenario if present
    for p in products:
        if p.get("status") in ("Approved", "Published"):
            return p["id"]
    return products[0]["id"]


# --- Regression ---
class TestRegression:
    def test_list_products(self, headers):
        r = requests.get(f"{BASE_URL}/api/products", headers=headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0
        first = data[0]
        for k in ("id", "title", "product_type"):
            assert k in first, f"missing {k} in list response"

    def test_get_product_detail(self, headers, product_id):
        r = requests.get(f"{BASE_URL}/api/products/{product_id}", headers=headers, timeout=30)
        assert r.status_code == 200
        p = r.json()
        assert p["id"] == product_id
        assert "title" in p and "product_type" in p


# --- Creative Brief fallback (main FM-001 fix) ---
class TestCreativeBriefFallback:
    def test_creative_brief_returns_200_with_fallback(self, headers, product_id):
        r = requests.post(f"{BASE_URL}/api/products/{product_id}/creative-brief", headers=headers, timeout=60)
        assert r.status_code == 200, f"expected 200, got {r.status_code} — body: {r.text[:400]}"
        data = r.json()

        assert "enhancement_source" in data, "missing enhancement_source"
        assert data["enhancement_source"] == "deterministic", (
            f"expected deterministic fallback (LLM capped), got {data.get('enhancement_source')}"
        )
        assert data.get("enhancement_stage_note"), "missing/empty enhancement_stage_note"
        assert "AI Brief Writer" in data["enhancement_stage_note"], (
            f"stage note must name AI Brief Writer stage, got: {data['enhancement_stage_note']}"
        )

        cb = data.get("creative_brief")
        assert isinstance(cb, dict) and cb, "creative_brief missing/empty"
        for k in ["who_for", "problem_solved", "will_understand", "skills_gained",
                  "whats_included", "reading_level", "completion_time", "next_path"]:
            assert k in cb and cb[k], f"creative_brief missing key '{k}' (value={cb.get(k)!r})"
        assert isinstance(cb["skills_gained"], list) and len(cb["skills_gained"]) > 0
        assert isinstance(cb["whats_included"], list) and len(cb["whats_included"]) > 0

        assert data.get("creative_status") == "Reviewed", (
            f"creative_status should be 'Reviewed', got {data.get('creative_status')}"
        )

    def test_creative_brief_persisted(self, headers, product_id):
        r = requests.get(f"{BASE_URL}/api/products/{product_id}", headers=headers, timeout=30)
        assert r.status_code == 200
        p = r.json()
        assert p.get("creative_status") == "Reviewed", f"not persisted: {p.get('creative_status')}"
        cb = p.get("creative_brief")
        assert isinstance(cb, dict) and cb, "creative_brief not persisted"
        assert cb.get("who_for"), "who_for missing on persisted brief"
        assert p.get("creative_brief_source") == "deterministic", (
            f"creative_brief_source not persisted as deterministic: {p.get('creative_brief_source')}"
        )

    def test_creative_brief_missing_product_returns_404(self, headers):
        r = requests.post(
            f"{BASE_URL}/api/products/does-not-exist-xyz-123/creative-brief",
            headers=headers, timeout=30,
        )
        assert r.status_code == 404, f"expected 404, got {r.status_code} — body: {r.text[:300]}"
        body = r.json()
        assert "detail" in body and body["detail"], "404 must include a clear detail message"
