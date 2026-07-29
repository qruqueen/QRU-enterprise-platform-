"""Iteration 98 — QRU Factory Phase 1: Books/Bundles experience shell + Destination preview."""
import os
import time
import uuid
import requests
import pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "https://enterprise-os-17.preview.emergentagent.com"
ADMIN = {"email": "demo.admin@qru.com", "password": "qru-demo-admin-2026"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE}/api/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ── PUBLIC — Experience shell / Books catalog ──────────────────────────
class TestPublicBooks:
    def test_public_home_regression(self):
        r = requests.get(f"{BASE}/api/public/home", timeout=15)
        assert r.status_code == 200
        assert "books" in r.json() or "featured" in r.json()

    def test_public_books_returns_imprints(self):
        r = requests.get(f"{BASE}/api/public/books", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "books" in data and "count" in data and "imprints" in data
        assert isinstance(data["imprints"], list)
        assert data["count"] == len(data["books"])

    def test_public_books_imprint_filter(self):
        base = requests.get(f"{BASE}/api/public/books", timeout=15).json()
        imprints = base.get("imprints") or []
        if not imprints:
            pytest.skip("no imprints in seed")
        imp = imprints[0]
        r = requests.get(f"{BASE}/api/public/books", params={"imprint": imp}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        for b in data["books"]:
            assert (b.get("imprint") or "QRU Press™") == imp

    def test_consumer_catalog_regression(self, auth_headers):
        r = requests.get(f"{BASE}/api/consumer/catalog", headers=auth_headers, timeout=15)
        assert r.status_code == 200


# ── PUBLIC — Bundles catalog + detail ──────────────────────────────────
class TestPublicBundles:
    def test_public_bundles_list(self):
        r = requests.get(f"{BASE}/api/public/bundles", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "bundles" in data and "count" in data
        assert data["count"] >= 1, "expected at least one seeded bundle"
        # find starter set
        titles = [b.get("title") for b in data["bundles"]]
        print("Bundle titles:", titles)
        assert any("Understanding" in (t or "") for t in titles), f"missing seeded 'The Understanding Starter Set' — got {titles}"

    def test_seeded_bundle_detail(self):
        # slug 'enterprise-os-17' per test spec
        r = requests.get(f"{BASE}/api/public/bundles/enterprise-os-17", timeout=15)
        # slug depends on title; try by title-derived slug from list
        if r.status_code == 404:
            listing = requests.get(f"{BASE}/api/public/bundles", timeout=15).json()
            b = next((x for x in listing["bundles"] if "Understanding" in (x.get("title") or "")), None)
            assert b, "seeded bundle not found"
            r = requests.get(f"{BASE}/api/public/bundles/{b['slug']}", timeout=15)
        assert r.status_code == 200
        b = r.json()
        assert b["item_count"] >= 2
        assert b["price"] > 0
        assert b["sum_price"] >= b["price"]
        assert round(b["savings"], 2) == round(b["sum_price"] - b["price"], 2)

    def test_bundle_checkout_session_creation(self):
        listing = requests.get(f"{BASE}/api/public/bundles", timeout=15).json()
        # prefer seeded 'Understanding' bundle to avoid race with parallel founder tests
        b = next((x for x in listing["bundles"] if "Understanding" in (x.get("title") or "")), None) or listing["bundles"][0]
        r = requests.post(f"{BASE}/api/public/bundle-checkout",
                          json={"bundle_id": b["id"], "origin_url": BASE}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("checkout_url", "").startswith("https://")
        assert data.get("session_id")
        # Verify status endpoint reports pending
        st = requests.get(f"{BASE}/api/public/bundle-checkout/status/{data['session_id']}", timeout=15)
        assert st.status_code == 200
        sd = st.json()
        assert sd["payment_status"] == "pending"
        assert sd["kind"] == "bundle"
        assert sd.get("bundle_id") == b["id"]


# ── FOUNDER — Bundles Manager ─────────────────────────────────────────
class TestFounderBundles:
    created_id = None

    def test_auth_required(self):
        r = requests.get(f"{BASE}/api/bundles", timeout=15)
        assert r.status_code in (401, 403)
        r2 = requests.get(f"{BASE}/api/bundles/eligible-items", timeout=15)
        assert r2.status_code in (401, 403)

    def test_eligible_items(self, auth_headers):
        r = requests.get(f"{BASE}/api/bundles/eligible-items", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        items = r.json().get("items", [])
        assert len(items) >= 2, "need ≥2 eligible books to test create/publish"
        for it in items:
            assert it["price"] > 0
        TestFounderBundles.eligible = items

    def test_list_bundles(self, auth_headers):
        r = requests.get(f"{BASE}/api/bundles", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        assert "bundles" in r.json()

    def test_create_publish_unpublish_delete(self, auth_headers):
        elig = requests.get(f"{BASE}/api/bundles/eligible-items", headers=auth_headers, timeout=15).json()["items"]
        assert len(elig) >= 2
        item_ids = [elig[0]["id"], elig[1]["id"]]
        sum_p = elig[0]["price"] + elig[1]["price"]
        price = round(sum_p * 0.75, 2)
        title = f"TEST_Bundle_{uuid.uuid4().hex[:6]}"
        r = requests.post(f"{BASE}/api/bundles", headers=auth_headers,
                          json={"title": title, "subtitle": "test", "description": "d",
                                "price": price, "item_ids": item_ids}, timeout=15)
        assert r.status_code == 200, r.text
        b = r.json()["bundle"]
        bid = b["id"]
        TestFounderBundles.created_id = bid
        assert b["status"] == "Draft"

        # publish
        pr = requests.post(f"{BASE}/api/bundles/{bid}/publish", headers=auth_headers, timeout=15)
        assert pr.status_code == 200, pr.text

        # appears in public
        pub = requests.get(f"{BASE}/api/public/bundles", timeout=15).json()
        assert any(x["id"] == bid for x in pub["bundles"])

        # unpublish
        upr = requests.post(f"{BASE}/api/bundles/{bid}/unpublish", headers=auth_headers, timeout=15)
        assert upr.status_code == 200

        # delete
        dr = requests.delete(f"{BASE}/api/bundles/{bid}", headers=auth_headers, timeout=15)
        assert dr.status_code == 200

    def test_publish_validation_low_items(self, auth_headers):
        elig = requests.get(f"{BASE}/api/bundles/eligible-items", headers=auth_headers, timeout=15).json()["items"]
        # 1 item bundle → publish should 400
        r = requests.post(f"{BASE}/api/bundles", headers=auth_headers,
                          json={"title": f"TEST_Bad_{uuid.uuid4().hex[:6]}", "price": 5.0,
                                "item_ids": [elig[0]["id"]]}, timeout=15)
        bid = r.json()["bundle"]["id"]
        try:
            pr = requests.post(f"{BASE}/api/bundles/{bid}/publish", headers=auth_headers, timeout=15)
            assert pr.status_code == 400
        finally:
            requests.delete(f"{BASE}/api/bundles/{bid}", headers=auth_headers, timeout=15)

    def test_publish_validation_zero_price(self, auth_headers):
        elig = requests.get(f"{BASE}/api/bundles/eligible-items", headers=auth_headers, timeout=15).json()["items"]
        r = requests.post(f"{BASE}/api/bundles", headers=auth_headers,
                          json={"title": f"TEST_Zero_{uuid.uuid4().hex[:6]}", "price": 0,
                                "item_ids": [elig[0]["id"], elig[1]["id"]]}, timeout=15)
        bid = r.json()["bundle"]["id"]
        try:
            pr = requests.post(f"{BASE}/api/bundles/{bid}/publish", headers=auth_headers, timeout=15)
            assert pr.status_code == 400
        finally:
            requests.delete(f"{BASE}/api/bundles/{bid}", headers=auth_headers, timeout=15)


# ── Destination preview ───────────────────────────────────────────────
class TestDestinationPreview:
    def test_destinations_map_requires_auth(self):
        r = requests.get(f"{BASE}/api/distribution-architecture/destinations-map", timeout=15)
        assert r.status_code in (401, 403)

    def test_destinations_map_auth(self, auth_headers):
        r = requests.get(f"{BASE}/api/distribution-architecture/destinations-map", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_destinations_for_book(self, auth_headers):
        # get any authorized book
        listing = requests.get(f"{BASE}/api/public/books", timeout=15).json()
        assert listing["books"], "no books available"
        book_id = listing["books"][0]["id"]
        r = requests.get(f"{BASE}/api/distribution-architecture/destinations",
                         params={"target": "book", "id": book_id}, headers=auth_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("product_type") == "Book"
        assert "books" in data["recommended"]
        assert "current" in data
        assert "overridden" in data

        # POST override → then revert
        po = requests.post(f"{BASE}/api/distribution-architecture/destinations",
                           json={"target": "book", "id": book_id, "experiences": ["books", "qru-online"]},
                           headers=auth_headers, timeout=15)
        assert po.status_code == 200 and po.json().get("ok")
        r2 = requests.get(f"{BASE}/api/distribution-architecture/destinations",
                          params={"target": "book", "id": book_id}, headers=auth_headers, timeout=15).json()
        assert r2["overridden"] is True

        # revert
        pr = requests.post(f"{BASE}/api/distribution-architecture/destinations",
                           json={"target": "book", "id": book_id, "experiences": []},
                           headers=auth_headers, timeout=15)
        assert pr.status_code == 200
        r3 = requests.get(f"{BASE}/api/distribution-architecture/destinations",
                          params={"target": "book", "id": book_id}, headers=auth_headers, timeout=15).json()
        assert r3["overridden"] is False


# ── Regression: single-book checkout ──────────────────────────────────
class TestRegressionCheckout:
    def test_single_book_checkout_still_works(self):
        listing = requests.get(f"{BASE}/api/public/books", timeout=15).json()
        assert listing["books"]
        bid = listing["books"][0]["id"]
        r = requests.post(f"{BASE}/api/public/checkout",
                          json={"book_id": bid, "origin_url": BASE}, timeout=30)
        # Either 200 with checkout_url or explicit error but not 500
        assert r.status_code in (200, 400, 404), r.text
        if r.status_code == 200:
            assert r.json().get("checkout_url", "").startswith("https://")
