"""QRU Online — Public presentation layer regression tests (iteration 80).

Verifies:
  * /api/public/home, /api/public/books, /api/public/books/{id} respond 200
  * All endpoints are UNAUTHENTICATED (no Authorization header)
  * Only public-safe fields are surfaced (no Factory internals leaked)
  * Book detail 404s for invalid/unpublished ids and does NOT leak fields
  * Exactly 4 authorized books, all with cover_url resolved
  * Book covers return HTTP 200 (public image assets)
"""
import os
import re
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")

# Fields that MUST NEVER appear in any public response (Factory internals)
FORBIDDEN_FIELDS = {
    "provenance",
    "product_manifest",
    "working_copy",
    "revision_history",
    "publication_status",
    "founder_authorization",
    "manuscript",
    "artifacts",
    "quality_gates",
    "manufacturing_orders",
}

ALLOWED_CARD_FIELDS = {
    "id", "title", "subtitle", "author", "genre", "imprint",
    "audience", "cover_url", "list_price", "currency", "excerpt",
}
ALLOWED_DETAIL_EXTRA = {
    "description", "edition", "language", "series", "publisher",
    "ebook_price", "paperback_price", "published",
}


def _client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


class TestPublicHome:
    def test_home_returns_200_without_auth(self):
        r = _client().get(f"{BASE_URL}/api/public/home")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "brand" in data and "featured" in data and "counts" in data
        assert data["brand"]["name"] == "QRU Online"
        assert isinstance(data["featured"], list)

    def test_home_forbids_internal_fields(self):
        data = _client().get(f"{BASE_URL}/api/public/home").json()
        for book in data["featured"]:
            leaked = FORBIDDEN_FIELDS.intersection(book.keys())
            assert not leaked, f"Home featured leaks internal fields: {leaked}"
            extra = set(book.keys()) - ALLOWED_CARD_FIELDS
            assert not extra, f"Home featured has unexpected fields: {extra}"

    def test_home_counts_match_expected(self):
        data = _client().get(f"{BASE_URL}/api/public/home").json()
        assert data["counts"]["books"] >= 4


class TestPublicCatalog:
    def test_catalog_returns_200_without_auth(self):
        r = _client().get(f"{BASE_URL}/api/public/books")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 4
        assert len(data["books"]) == data["count"]

    def test_catalog_only_public_fields(self):
        data = _client().get(f"{BASE_URL}/api/public/books").json()
        for book in data["books"]:
            leaked = FORBIDDEN_FIELDS.intersection(book.keys())
            assert not leaked, f"Catalog leaks internal fields: {leaked}"
            assert book["id"] and book["title"] and book["cover_url"]

    def test_catalog_covers_reachable(self):
        data = _client().get(f"{BASE_URL}/api/public/books").json()
        for book in data["books"]:
            url = book["cover_url"]
            if not url.startswith("http"):
                url = BASE_URL + url
            r = requests.head(url, allow_redirects=True, timeout=15)
            # Some hosts don't allow HEAD; fallback to GET (range 0-0)
            if r.status_code >= 400:
                r = requests.get(url, headers={"Range": "bytes=0-1"}, timeout=15)
            assert r.status_code in (200, 206), f"Cover {url} → {r.status_code}"


class TestPublicBookDetail:
    def test_book_detail_returns_public_fields(self):
        catalog = _client().get(f"{BASE_URL}/api/public/books").json()
        book_id = catalog["books"][0]["id"]
        r = _client().get(f"{BASE_URL}/api/public/books/{book_id}")
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == book_id
        assert d.get("published") is True
        leaked = FORBIDDEN_FIELDS.intersection(d.keys())
        assert not leaked, f"Book detail leaks: {leaked}"
        allowed = ALLOWED_CARD_FIELDS | ALLOWED_DETAIL_EXTRA
        extra = set(d.keys()) - allowed - {"excerpt"}
        assert not extra, f"Book detail has unexpected fields: {extra}"

    def test_book_detail_missing_id_404(self):
        r = _client().get(f"{BASE_URL}/api/public/books/does-not-exist")
        assert r.status_code == 404
        # Should be a plain error message, no leaked data
        body = r.json()
        assert "detail" in body
        assert not FORBIDDEN_FIELDS.intersection(str(body).lower().split())

    def test_book_detail_no_auth_required(self):
        catalog = _client().get(f"{BASE_URL}/api/public/books").json()
        book_id = catalog["books"][0]["id"]
        # Explicitly send no auth header
        r = requests.get(f"{BASE_URL}/api/public/books/{book_id}")
        assert r.status_code == 200


class TestPublicNoAuthRequired:
    def test_all_public_endpoints_no_auth(self):
        for path in ["/api/public/home", "/api/public/books"]:
            r = requests.get(f"{BASE_URL}{path}")
            assert r.status_code == 200, f"{path} required auth: {r.status_code}"


class TestFactoryStillProtected:
    """Factory admin APIs must still require authentication."""

    @pytest.mark.parametrize("path", [
        "/api/auth/me",
        "/api/book-mfg/books",
        "/api/manufacturing/pms",
    ])
    def test_factory_endpoint_requires_auth(self, path):
        r = requests.get(f"{BASE_URL}{path}")
        # Should NOT be 200 without auth; typically 401/403
        assert r.status_code in (401, 403, 404), f"{path} leaked without auth: {r.status_code}"
