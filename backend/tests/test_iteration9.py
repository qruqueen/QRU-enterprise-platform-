"""Iteration 9 — QRU Product Rendering Engine™ regression.

Covers:
- POST /api/rendering/{pid}/render — 404 for non-existent, 400 for non-certified.
- POST /api/rendering/{pid}/render — starts an async job on Treasure Standard product.
  Polling GET /api/rendering/{pid} moves render_status to 'rendered' within ~90s
  and returns rendered_assets with 5 keys: cover, thumbnail, store_graphic, qr_code, print_pdf.
- GET /api/rendering/asset/{fname} — PNGs served as image/png, PDF as application/pdf.
  Path-traversal (`..` or `/`) returns 400.
- Regression: after rendering, consumer catalog shows cover_url on product card data.
"""
import os
import time
import pytest
import requests


def _read_frontend_env():
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return None


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _read_frontend_env()).rstrip("/")

ADMIN = {"email": "admin@qru.com", "password": "qru-admin-2026"}
LEARNER = {"email": "learner@qru.com", "password": "qru-learn-2026"}

RENDER_ASSET_KEYS = ["cover", "thumbnail", "store_graphic", "qr_code", "print_pdf"]


@pytest.fixture(scope="module")
def admin_client():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    s.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return s


@pytest.fixture(scope="module")
def learner_client():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json=LEARNER, timeout=30)
    assert r.status_code == 200, r.text
    s.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return s


@pytest.fixture(scope="module")
def demo_products(learner_client):
    """Fetch the 3 published demo products (Treasure Standard) from consumer catalog."""
    r = learner_client.get(f"{BASE_URL}/api/consumer/catalog", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    products = body.get("products") if isinstance(body, dict) else body
    assert isinstance(products, list) and products, "no products in catalog"
    # All demo products should be treasure_standard=True
    ts = [p for p in products if p.get("treasure_standard")]
    assert ts, "no treasure_standard products found in catalog"
    return ts


# -------- Rendering Guard --------
class TestRenderGuards:
    def test_render_404_for_nonexistent_product(self, admin_client):
        r = admin_client.post(f"{BASE_URL}/api/rendering/NON-EXISTENT-PID/render", timeout=15)
        assert r.status_code == 404, r.text

    def test_render_400_for_non_certified(self, admin_client):
        """Try to find a non-certified product; fall back to skip."""
        # Grab admin's product list
        for path in ["/api/products", "/api/manufacturing2/products"]:
            r = admin_client.get(f"{BASE_URL}{path}", timeout=15)
            if r.status_code == 200:
                data = r.json()
                items = data if isinstance(data, list) else (data.get("products") or [])
                non_ts = [p for p in items if not p.get("treasure_standard")]
                if non_ts:
                    pid = non_ts[0]["id"]
                    r2 = admin_client.post(f"{BASE_URL}/api/rendering/{pid}/render", timeout=15)
                    assert r2.status_code == 400, f"Expected 400 for non-certified, got {r2.status_code}: {r2.text}"
                    return
        pytest.skip("No non-certified product available to test 400 guard")


# -------- Rendering end-to-end --------
class TestRenderEndToEnd:
    def test_render_and_poll_treasure_standard_product(self, admin_client, demo_products):
        # Pick a demo product; try in the order Heart, Sleep, Insulin
        target = None
        for kw in ["Heart", "Sleep", "Insulin"]:
            for p in demo_products:
                if kw.lower() in (p.get("title") or "").lower():
                    target = p
                    break
            if target:
                break
        target = target or demo_products[0]
        pid = target["id"]

        # Kick off render
        r = admin_client.post(f"{BASE_URL}/api/rendering/{pid}/render", timeout=30)
        assert r.status_code == 200, r.text
        assert r.json().get("pid") == pid

        # Poll for up to 90s
        deadline = time.time() + 90
        status = None
        assets = None
        while time.time() < deadline:
            r2 = admin_client.get(f"{BASE_URL}/api/rendering/{pid}", timeout=20)
            assert r2.status_code == 200, r2.text
            body = r2.json()
            status = body.get("render_status")
            if status in ("rendered", "failed"):
                assets = body.get("rendered_assets")
                break
            time.sleep(3)

        assert status == "rendered", f"Final render_status={status}"
        assert isinstance(assets, dict), "rendered_assets missing"
        for k in RENDER_ASSET_KEYS:
            assert k in assets and assets[k], f"Missing rendered asset: {k}"
            assert assets[k].startswith("/api/rendering/asset/"), f"Bad asset URL for {k}: {assets[k]}"

        # Verify each asset is fetchable with proper content-type
        for k in ["cover", "thumbnail", "store_graphic", "qr_code"]:
            url = f"{BASE_URL}{assets[k]}"
            resp = requests.get(url, timeout=20)
            assert resp.status_code == 200, f"{k} fetch failed: {resp.status_code}"
            assert resp.headers.get("content-type", "").startswith("image/png"), (
                f"{k} content-type: {resp.headers.get('content-type')}"
            )
            assert len(resp.content) > 500, f"{k} too small ({len(resp.content)} bytes)"

        pdf_url = f"{BASE_URL}{assets['print_pdf']}"
        pdf_resp = requests.get(pdf_url, timeout=30)
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers.get("content-type", "").startswith("application/pdf"), (
            f"print_pdf content-type: {pdf_resp.headers.get('content-type')}"
        )
        assert len(pdf_resp.content) > 2000

        # Persist pid for regression test via pytest cache
        # (also expose via module-level attribute)
        TestRenderEndToEnd.rendered_pid = pid


# -------- Asset serving traversal guard --------
class TestAssetTraversal:
    def test_traversal_dotdot_blocked(self):
        r = requests.get(f"{BASE_URL}/api/rendering/asset/..%2Fetc%2Fpasswd", timeout=15)
        # URL-encoded still contains `..` after unquote by FastAPI's path handler
        # But the raw path segment matcher on FastAPI treats %2F as encoded slash; guard should catch `..`
        assert r.status_code in (400, 404), f"Expected 400/404 got {r.status_code}"

    def test_traversal_dotdot_literal_blocked(self):
        # Directly attempt with .. — FastAPI still routes because `{fname}` is a path param
        r = requests.get(f"{BASE_URL}/api/rendering/asset/..hidden.png", timeout=15)
        assert r.status_code == 400, r.text
        assert "invalid" in (r.text or "").lower()

    def test_missing_asset_returns_404(self):
        r = requests.get(f"{BASE_URL}/api/rendering/asset/nope-does-not-exist.png", timeout=15)
        assert r.status_code == 404


# -------- Regression: catalog cover_url after render --------
class TestCatalogCoverRegression:
    def test_rendered_product_shows_cover_url(self, learner_client):
        pid = getattr(TestRenderEndToEnd, "rendered_pid", None)
        if not pid:
            pytest.skip("No rendered_pid available (upstream test skipped/failed)")
        r = learner_client.get(f"{BASE_URL}/api/consumer/catalog", timeout=15)
        assert r.status_code == 200
        body = r.json()
        products = body.get("products") if isinstance(body, dict) else body
        target = next((p for p in products if p.get("id") == pid), None)
        assert target is not None, f"Product {pid} not found in consumer catalog"
        assert target.get("cover_url"), f"cover_url missing for rendered product: {target}"
        assert target["cover_url"].startswith("/api/rendering/asset/"), target["cover_url"]
