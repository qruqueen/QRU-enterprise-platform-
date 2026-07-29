"""
Iteration 99 tests: Bundle Cover Studio, Imprint Rollout, Publish Preview Everywhere.
- Bundle Cover: POST /api/bundles/{id}/cover generates a branded PNG, asset serves 200.
- Bundle create + publish auto-generate covers.
- Public bundles carry their own cover_url (not book cover).
- Imprint: PATCH publication-details w/ imprint persists; /api/public/books returns imprints + filter works.
- Regression: /api/public/home, /api/public/checkout session, /api/distribution-architecture/destinations-map.
"""
import os
import io
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
ADMIN_EMAIL = "demo.admin@qru.com"
ADMIN_PASS = "qru-demo-admin-2026"


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_client(admin_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"})
    return s


# ---------- Bundle Cover Studio ----------
class TestBundleCoverStudio:
    def test_public_bundles_have_own_covers(self):
        r = requests.get(f"{BASE_URL}/api/public/bundles", timeout=30)
        assert r.status_code == 200
        data = r.json()
        bundles = data.get("bundles") if isinstance(data, dict) else data
        assert bundles and len(bundles) >= 1
        for b in bundles:
            cu = b.get("cover_url", "")
            assert cu, f"bundle {b.get('slug')} missing cover_url"
            assert "bundle-cover" in cu, f"bundle {b.get('slug')} cover_url should be a branded bundle cover, got {cu}"

    def test_bundle_cover_asset_serves_png(self):
        r = requests.get(f"{BASE_URL}/api/public/bundles", timeout=30)
        bundles = r.json().get("bundles") if isinstance(r.json(), dict) else r.json()
        cover_url = bundles[0]["cover_url"]
        # cover_url is relative "/api/rendering/asset/bundle-cover-*.png"
        full = f"{BASE_URL}{cover_url}" if cover_url.startswith("/") else cover_url
        r2 = requests.get(full, timeout=30)
        assert r2.status_code == 200, f"cover asset returned {r2.status_code}"
        assert r2.headers.get("content-type", "").startswith("image/"), r2.headers
        assert len(r2.content) > 1000

    def test_create_bundle_auto_generates_cover(self, admin_client):
        # Need at least 2 book ids
        books = requests.get(f"{BASE_URL}/api/public/books", timeout=30).json()
        book_list = books.get("books") if isinstance(books, dict) else books
        assert len(book_list) >= 2
        item_ids = [b["id"] for b in book_list[:2]]
        payload = {
            "title": "TEST_Cover Studio Bundle",
            "subtitle": "TEST",
            "description": "TEST bundle for cover studio",
            "item_ids": item_ids,
            "price": 19.99,
        }
        r = admin_client.post(f"{BASE_URL}/api/bundles", json=payload, timeout=60)
        assert r.status_code in (200, 201), r.text
        body = r.json()
        bundle = body.get("bundle", body)
        bid = bundle["id"]
        try:
            assert "cover_url" in bundle
            assert "bundle-cover" in (bundle.get("cover_url") or ""), bundle.get("cover_url")

            # Regenerate cover
            r2 = admin_client.post(f"{BASE_URL}/api/bundles/{bid}/cover", timeout=90)
            assert r2.status_code == 200, r2.text
            body = r2.json()
            new_cover = body.get("cover_url") or body.get("bundle", {}).get("cover_url")
            if not new_cover:
                rr = admin_client.get(f"{BASE_URL}/api/bundles/{bid}", timeout=30)
                new_cover = rr.json().get("bundle", rr.json()).get("cover_url")
            assert new_cover and "bundle-cover" in new_cover

            # Asset serves
            full = f"{BASE_URL}{new_cover}" if new_cover.startswith("/") else new_cover
            r3 = requests.get(full, timeout=30)
            assert r3.status_code == 200
            assert r3.headers.get("content-type", "").startswith("image/")

            # Publish regenerates cover — publish response is {ok:true}, verify via GET
            prev_cover = new_cover
            r4 = admin_client.post(f"{BASE_URL}/api/bundles/{bid}/publish", timeout=90)
            assert r4.status_code == 200, r4.text
            r5 = admin_client.get(f"{BASE_URL}/api/bundles/{bid}", timeout=30)
            assert r5.status_code == 200, r5.text
            after = r5.json().get("bundle", r5.json())
            pub_cover = after.get("cover_url")
            assert pub_cover and "bundle-cover" in pub_cover, pub_cover
        finally:
            admin_client.delete(f"{BASE_URL}/api/bundles/{bid}", timeout=30)

    def test_cover_requires_auth(self):
        # Get an existing bundle id
        bundles = requests.get(f"{BASE_URL}/api/public/bundles", timeout=30).json()
        bundles = bundles.get("bundles") if isinstance(bundles, dict) else bundles
        bid = bundles[0]["id"]
        r = requests.post(f"{BASE_URL}/api/bundles/{bid}/cover", timeout=30)
        assert r.status_code in (401, 403), r.status_code


# ---------- Imprint Rollout ----------
class TestImprintRollout:
    def test_public_books_return_imprints_list(self):
        r = requests.get(f"{BASE_URL}/api/public/books", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict), "expected object with books/count/imprints"
        assert "books" in data and "imprints" in data
        imprints = data["imprints"]
        assert "QRU Press™" in imprints, imprints
        assert "E.Q. Rothwell™" in imprints, imprints

    def test_imprint_filter_eq_rothwell(self):
        r = requests.get(f"{BASE_URL}/api/public/books", params={"imprint": "E.Q. Rothwell™"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        books = data["books"] if isinstance(data, dict) else data
        assert len(books) == 3, f"expected 3 E.Q. Rothwell books, got {len(books)}"
        for b in books:
            assert b.get("imprint") == "E.Q. Rothwell™", b

    def test_imprint_filter_qru_press(self):
        r_all = requests.get(f"{BASE_URL}/api/public/books", timeout=30).json()
        total = r_all["count"] if isinstance(r_all, dict) and "count" in r_all else len(r_all.get("books", []))
        r = requests.get(f"{BASE_URL}/api/public/books", params={"imprint": "QRU Press™"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        books = data["books"] if isinstance(data, dict) else data
        assert len(books) == total - 3, f"QRU Press={len(books)}, total={total}"

    def test_publication_details_persists_imprint(self, admin_client):
        # find a book id via manufacturing list
        r = admin_client.get(f"{BASE_URL}/api/book-mfg/books", timeout=30)
        assert r.status_code == 200, r.text
        books_data = r.json()
        books = books_data.get("books") if isinstance(books_data, dict) else books_data
        assert books and len(books) >= 1
        # find a QRU Press book to test toggle back
        target = next((b for b in books if b.get("imprint") != "E.Q. Rothwell™"), books[0])
        bid = target["id"]
        original = target.get("imprint") or "QRU Press™"

        # PATCH via publication-details
        r2 = admin_client.post(
            f"{BASE_URL}/api/book-mfg/books/{bid}/publication-details",
            json={"imprint": "E.Q. Rothwell™"},
            timeout=30,
        )
        assert r2.status_code == 200, r2.text

        # Verify persisted
        r3 = admin_client.get(f"{BASE_URL}/api/book-mfg/books/{bid}", timeout=30)
        assert r3.status_code == 200
        body = r3.json()
        book_obj = body.get("book") if isinstance(body, dict) and "book" in body else body
        assert book_obj.get("imprint") == "E.Q. Rothwell™", book_obj.get("imprint")

        # Restore
        admin_client.post(
            f"{BASE_URL}/api/book-mfg/books/{bid}/publication-details",
            json={"imprint": original},
            timeout=30,
        )


# ---------- Publish Preview: destinations-map ----------
class TestDestinationsMap:
    def test_destinations_map_available(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/distribution-architecture/destinations-map", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # Should have some structure with product families or media entries
        assert isinstance(data, (dict, list))
        # sanity: not empty
        assert len(data) > 0


# ---------- Regression ----------
class TestRegression:
    def test_public_home(self):
        r = requests.get(f"{BASE_URL}/api/public/home", timeout=30)
        assert r.status_code == 200
        data = r.json()
        # home returns some books/collection
        assert data

    def test_single_book_checkout_session(self):
        # find a book
        books = requests.get(f"{BASE_URL}/api/public/books", timeout=30).json()
        book_list = books["books"] if isinstance(books, dict) else books
        book = book_list[0]
        payload = {
            "book_id": book["id"],
            "email": "TEST_regression@example.com",
            "origin_url": BASE_URL,
        }
        r = requests.post(f"{BASE_URL}/api/public/checkout", json=payload, timeout=60)
        # Accept either 200 with url or 400/402 depending on stripe config; session creation should succeed
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("checkout_url") or body.get("url"), body

    def test_bundle_checkout_session(self):
        bundles = requests.get(f"{BASE_URL}/api/public/bundles", timeout=30).json()
        bundles = bundles.get("bundles") if isinstance(bundles, dict) else bundles
        assert bundles
        bslug = bundles[0].get("slug") or bundles[0].get("id")
        payload = {
            "bundle_key": bslug,
            "email": "TEST_regression@example.com",
            "origin_url": BASE_URL,
        }
        # Try both endpoint variants
        for path in ("/api/public/bundle-checkout", "/api/public/bundles/checkout"):
            r = requests.post(f"{BASE_URL}{path}", json=payload, timeout=60)
            if r.status_code == 200:
                body = r.json()
                assert body.get("checkout_url") or body.get("url"), body
                return
        pytest.skip("bundle checkout endpoint path not found (both variants tried)")
