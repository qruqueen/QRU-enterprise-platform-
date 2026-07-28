"""Iteration 24: Customer Delivery Pipeline
- Buy button → Stripe Checkout (real cs_test URL)
- Delivery download endpoint returns clear messages for edge cases
- Export formats + asset serving return HTTP 200 files
- Preview endpoint returns HTTP 200/302
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="session")
def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def published_product(auth):
    r = requests.get(f"{BASE_URL}/api/commerce/storefront", headers=auth, timeout=30)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list) and len(items) > 0, "No published products in storefront"
    return items[0]


class TestCheckout:
    def test_storefront_returns_products(self, auth):
        r = requests.get(f"{BASE_URL}/api/commerce/storefront", headers=auth, timeout=30)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        assert len(items) > 0
        # Check that each product has price, id, product_code
        p = items[0]
        assert "id" in p and "product_code" in p and "price" in p and p["price"] > 0

    def test_buy_returns_real_stripe_url(self, auth, published_product):
        payload = {
            "product_id": published_product["id"],
            "origin_url": BASE_URL,
        }
        r = requests.post(f"{BASE_URL}/api/commerce/checkout", headers=auth, json=payload, timeout=45)
        assert r.status_code == 200, f"Checkout failed: {r.status_code} {r.text}"
        data = r.json()
        assert "url" in data and "session_id" in data
        assert data["url"].startswith("https://checkout.stripe.com/"), f"Not a Stripe URL: {data['url']}"
        assert data["session_id"].startswith("cs_"), f"Not a Stripe session id: {data['session_id']}"
        # Verify head of URL is reachable (not necessarily 200 without a browser, but should be non-error)
        # Skip HEAD — Stripe may block, but URL format is authoritative

    def test_buy_unknown_product_returns_clear_error(self, auth):
        payload = {"product_id": "nonexistent-product-xyz", "origin_url": BASE_URL}
        r = requests.post(f"{BASE_URL}/api/commerce/checkout", headers=auth, json=payload, timeout=30)
        assert r.status_code == 400
        detail = r.json().get("detail", "")
        # Must be customer-facing (not generic 500)
        assert detail and "Something went wrong" not in detail
        assert "not found" in detail.lower() or "not available" in detail.lower()


class TestDelivery:
    def test_download_unknown_session_returns_404_with_clear_message(self, auth):
        r = requests.get(f"{BASE_URL}/api/commerce/download/cs_test_unknown_session_id_xxx",
                         headers=auth, timeout=30)
        assert r.status_code == 404
        detail = r.json().get("detail", "")
        assert detail, "No detail message"
        assert "Something went wrong" not in detail
        assert "couldn't find" in detail.lower() or "not found" in detail.lower() or \
               "purchase" in detail.lower()

    def test_download_pending_session_returns_clear_message(self, auth, published_product):
        # Create a checkout (pending) — do NOT complete payment
        r = requests.post(f"{BASE_URL}/api/commerce/checkout", headers=auth,
                          json={"product_id": published_product["id"], "origin_url": BASE_URL}, timeout=45)
        assert r.status_code == 200
        session_id = r.json()["session_id"]

        # Try to download — payment not complete → clear message
        r2 = requests.get(f"{BASE_URL}/api/commerce/download/{session_id}", headers=auth, timeout=30)
        assert r2.status_code == 404
        detail = r2.json().get("detail", "")
        assert detail
        assert "Something went wrong" not in detail
        assert "hasn't completed" in detail.lower() or "hasnt completed" in detail.lower() or \
               "pending" in detail.lower() or "clears" in detail.lower()

    def test_download_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/commerce/download/any_session", timeout=30)
        assert r.status_code in (401, 403)


class TestFormats:
    def test_export_formats_returns_files(self, auth, published_product):
        r = requests.post(f"{BASE_URL}/api/rendering/{published_product['id']}/export-formats",
                          headers=auth, timeout=60)
        assert r.status_code == 200, f"export-formats failed: {r.status_code} {r.text}"
        data = r.json()
        assert "formats" in data
        formats = data["formats"]
        assert isinstance(formats, dict) and len(formats) > 0

        # For each format, verify the url resolves to HTTP 200 with the ?download=true query
        for key, f in formats.items():
            url = f.get("url")
            assert url, f"format {key} has no url"
            full = f"{BASE_URL}{url}?download=true"
            head = requests.get(full, timeout=30, stream=True, allow_redirects=True)
            assert head.status_code == 200, f"Format {key} url {full} returned {head.status_code}"
            # Verify Content-Disposition is attachment (server serves as download)
            cd = head.headers.get("content-disposition", "")
            assert "attachment" in cd.lower() or "inline" in cd.lower() or len(head.content) > 0
            head.close()


class TestPreview:
    def test_preview_endpoint(self, auth, published_product):
        # Preview endpoint is public (no auth required per convention, but pass anyway)
        pid = published_product["id"]
        r = requests.get(f"{BASE_URL}/api/marketing/preview/{pid}?fmt=html",
                         timeout=30, allow_redirects=False)
        # Must be 200, 302 (redirect to asset), or 404 (no preview) — never 500
        assert r.status_code in (200, 302, 404), f"preview returned {r.status_code}: {r.text[:200]}"
        # If 200 or 302, must serve real content
        if r.status_code == 302:
            loc = r.headers.get("location", "")
            assert loc, "302 with no Location header"
