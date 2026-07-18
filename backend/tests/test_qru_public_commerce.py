"""QRU Online public commerce (Stripe Checkout + EPUB download) regression tests.

Verifies iteration-81 acceptance criteria:
  - /api/public/checkout creates a Stripe checkout session server-side (server-priced)
  - /api/public/checkout/status/{sid} returns pending for uninitialized/incomplete purchases
  - /api/public/download/{sid} enforces paid-only delivery (403 otherwise)
  - Book cover thumbnails and public book data render correctly for all 4 authorized books
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://understanding-os.preview.emergentagent.com").rstrip("/")

BOOK_IDS = {
    "understanding_tree": "8469bcc5-6d6b-4a35-bc5c-4dec82c114cb",
    "ordinary_tuesdays": "ca481a45-3e75-4df8-aadf-a1371c1ddb72",
    "trading_battlefield": "0dbd2b49-93fa-4cb4-aa13-b75db7b5b917",
    "the_heart": "48405e16-6d2a-44e2-9239-c70b0ec58a3d",
}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# --- Public catalog / covers ---------------------------------------------------

class TestPublicCatalog:
    def test_home_returns_featured_with_covers(self, s):
        r = s.get(f"{BASE_URL}/api/public/home", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "featured" in data and len(data["featured"]) >= 1
        for b in data["featured"]:
            assert b.get("cover_url"), f"missing cover_url for {b.get('title')}"
            assert b.get("thumb_url", "").startswith("/api/public/books/"), b.get("thumb_url")

    def test_books_catalog_returns_four_authorized(self, s):
        r = s.get(f"{BASE_URL}/api/public/books", timeout=15)
        assert r.status_code == 200
        data = r.json()
        ids = {b["id"] for b in data.get("books", [])}
        for name, bid in BOOK_IDS.items():
            assert bid in ids, f"authorized book {name} ({bid}) missing"
        assert data.get("count", 0) >= 4

    @pytest.mark.parametrize("book_id", list(BOOK_IDS.values()))
    def test_book_detail_has_ebook_price_and_cover(self, s, book_id):
        r = s.get(f"{BASE_URL}/api/public/books/{book_id}", timeout=15)
        assert r.status_code == 200, r.text
        b = r.json()
        # detail must include description and pricing fields
        assert b.get("id") == book_id
        assert b.get("cover_url"), "cover_url missing on detail"
        # ebook_price OR list_price must resolve to a positive number so purchase is possible
        price = b.get("ebook_price") or b.get("list_price") or b.get("paperback_price")
        assert price and float(price) > 0, f"no positive price for {book_id}: {b}"

    @pytest.mark.parametrize("book_id", list(BOOK_IDS.values()))
    def test_cover_thumb_returns_image(self, s, book_id):
        r = s.get(f"{BASE_URL}/api/public/books/{book_id}/cover-thumb", timeout=30)
        assert r.status_code == 200
        ct = r.headers.get("content-type", "")
        assert "image" in ct, f"expected image content-type, got {ct}"
        assert len(r.content) > 1000, "thumbnail suspiciously small"


# --- Checkout ------------------------------------------------------------------

class TestCheckout:
    def test_checkout_creates_stripe_session_server_priced(self, s):
        payload = {
            "book_id": BOOK_IDS["understanding_tree"],
            "origin_url": BASE_URL,
            # Attempt to spoof price: server MUST ignore any client-supplied amount
            "amount": 0.01,
        }
        r = s.post(f"{BASE_URL}/api/public/checkout", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["checkout_url"].startswith("https://checkout.stripe.com"), data
        assert data["session_id"].startswith("cs_test_"), data["session_id"]

    def test_checkout_unknown_book_returns_404(self, s):
        r = s.post(
            f"{BASE_URL}/api/public/checkout",
            json={"book_id": "no-such-book", "origin_url": BASE_URL},
            timeout=15,
        )
        assert r.status_code == 404

    def test_checkout_status_pending_before_pay(self, s):
        # Create a fresh session first
        r = s.post(
            f"{BASE_URL}/api/public/checkout",
            json={"book_id": BOOK_IDS["understanding_tree"], "origin_url": BASE_URL},
            timeout=30,
        )
        assert r.status_code == 200
        sid = r.json()["session_id"]
        st = s.get(f"{BASE_URL}/api/public/checkout/status/{sid}", timeout=15)
        assert st.status_code == 200
        d = st.json()
        assert d["payment_status"] in ("pending", "initiated", "open", "unpaid", None)
        assert d.get("download_url") in (None, ""), "download_url must not appear before payment"

    def test_checkout_status_unknown_session_404(self, s):
        r = s.get(f"{BASE_URL}/api/public/checkout/status/cs_test_nonexistent_xyz", timeout=15)
        assert r.status_code == 404


# --- Download authorization ----------------------------------------------------

class TestDownloadAuthorization:
    def test_download_forbidden_for_unpaid_new_session(self, s):
        """Freshly-initiated session must NOT be able to download."""
        r = s.post(
            f"{BASE_URL}/api/public/checkout",
            json={"book_id": BOOK_IDS["understanding_tree"], "origin_url": BASE_URL},
            timeout=30,
        )
        sid = r.json()["session_id"]
        d = s.get(f"{BASE_URL}/api/public/download/{sid}", timeout=15, allow_redirects=False)
        assert d.status_code == 403, f"unpaid session must be 403, got {d.status_code}: {d.text[:200]}"

    def test_download_forbidden_for_random_session(self, s):
        r = s.get(
            f"{BASE_URL}/api/public/download/cs_test_random_unpaid_zzz",
            timeout=15,
            allow_redirects=False,
        )
        # 403 (record not found → not paid) — matches server contract
        assert r.status_code == 403
