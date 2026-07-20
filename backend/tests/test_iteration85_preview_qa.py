"""Iteration 85 — PREVIEW security (signed file+action+user tokens), inline vs attachment
headers, QA Cleanup™ safeguards, and Upgrade-All-Documents batch (Publication Quality)."""
import os
import re
import time
import pytest
import requests
from urllib.parse import urlparse, parse_qs

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        try:
            with open("/app/frontend/.env", "r") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
    assert url, "REACT_APP_BACKEND_URL not configured"
    return url.rstrip("/")

BASE_URL = _load_backend_url()
ADMIN_EMAIL = "demo.admin@qru.com"
ADMIN_PASSWORD = "qru-demo-admin-2026"


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="session")
def api(admin_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {admin_token}",
                      "Content-Type": "application/json"})
    return s


def _find_doc_product_with_deliverable(api):
    """Return a product dict for a document-family product that has a rendered deliverable pdf."""
    r = api.get(f"{BASE_URL}/api/products", timeout=30)
    assert r.status_code == 200, r.text[:200]
    d = r.json(); prods = d if isinstance(d, list) else d.get("products", [])
    for p in prods:
        pid = p.get("id")
        if not pid:
            continue
        cd = (p.get("customer_deliverable") or {})
        files = cd.get("files") or []
        pdfs = [f for f in files if f.get("format") == "pdf" and str(f.get("filename", "")).startswith("deliverable-")]
        if pdfs:
            return p, pdfs[0]["filename"]
    return None, None


# ---------- AUTH sanity ----------
class TestAuth:
    def test_login_returns_token(self, admin_token):
        assert isinstance(admin_token, str) and len(admin_token) > 20

    def test_me_role(self, api):
        r = api.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("email") == ADMIN_EMAIL
        assert data.get("role") in ("Administrator", "Super Admin", "Founder & CEO")


# ---------- Preview / Download token behaviour ----------
class TestFileTokens:
    _pid = None
    _pdf_fid = None

    @pytest.fixture(autouse=True)
    def _bootstrap(self, api):
        if TestFileTokens._pid is None:
            p, fid = _find_doc_product_with_deliverable(api)
            assert p, "No document-family product with a rendered deliverable PDF found"
            TestFileTokens._pid = p["id"]
            TestFileTokens._pdf_fid = fid

    def _mint(self, api, action="preview", fmt="pdf"):
        r = api.post(f"{BASE_URL}/api/products/{self._pid}/file-token",
                     json={"format": fmt, "action": action}, timeout=15)
        assert r.status_code == 200, f"mint {action} failed: {r.status_code} {r.text[:200]}"
        return r.json()

    def test_preview_token_returns_inline_pdf(self, api):
        info = self._mint(api, "preview")
        url = info["url"]
        assert url.startswith("/api/rendering/asset/deliverable-")
        assert "token=" in url
        assert "download=1" not in url
        full = f"{BASE_URL}{url}"
        r = requests.get(full, timeout=30, allow_redirects=False)
        assert r.status_code == 200, r.text[:200]
        assert r.headers.get("content-type", "").startswith("application/pdf")
        cd = r.headers.get("content-disposition", "").lower()
        assert cd.startswith("inline"), f"expected inline, got {cd!r}"
        assert "no-store" in r.headers.get("cache-control", "").lower()
        assert r.headers.get("referrer-policy", "").lower() == "no-referrer"

    def test_download_token_returns_attachment(self, api):
        info = self._mint(api, "download")
        assert "download=1" in info["url"]
        full = f"{BASE_URL}{info['url']}"
        r = requests.get(full, timeout=30, allow_redirects=False)
        assert r.status_code == 200
        cd = r.headers.get("content-disposition", "").lower()
        assert cd.startswith("attachment"), f"expected attachment, got {cd!r}"
        assert "filename=" in cd

    def test_deliverable_without_token_forbidden(self, api):
        # Direct GET with NO token → 403
        r = requests.get(f"{BASE_URL}/api/rendering/asset/{self._pdf_fid}", timeout=20)
        assert r.status_code == 403, f"expected 403 no-token, got {r.status_code}"

    def test_preview_token_cannot_download(self, api):
        info = self._mint(api, "preview")
        # tack on &download=1 to escalate to download
        q = info["url"]
        if "?" in q:
            q = q + "&download=1"
        else:
            q = q + "?download=1"
        r = requests.get(f"{BASE_URL}{q}", timeout=20)
        assert r.status_code == 403, f"expected 403 action-scope, got {r.status_code}"

    def test_tampered_token_rejected(self, api):
        info = self._mint(api, "preview")
        u = info["url"]
        # tamper last char of token in query
        parsed = urlparse(u)
        qs = parse_qs(parsed.query)
        tok = qs["token"][0]
        tampered = tok[:-2] + ("A" if tok[-1] != "A" else "B") + tok[-1]
        bad_url = f"{BASE_URL}{parsed.path}?token={tampered}"
        r = requests.get(bad_url, timeout=20)
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

    def test_token_scoped_to_file(self, api):
        # Mint token for our pid, then attempt to use it on some OTHER deliverable file.
        info = self._mint(api, "preview")
        parsed = urlparse(info["url"])
        tok = parse_qs(parsed.query)["token"][0]
        # find any other deliverable filename
        r = api.get(f"{BASE_URL}/api/products", timeout=30)
        d = r.json(); prods = d if isinstance(d, list) else d.get("products", [])
        other_fid = None
        for p in prods:
            if p.get("id") == self._pid:
                continue
            files = ((p.get("customer_deliverable") or {}).get("files") or [])
            for f in files:
                fn = f.get("filename")
                if fn and str(fn).startswith("deliverable-") and fn != self._pdf_fid:
                    other_fid = fn; break
            if other_fid:
                break
        if not other_fid:
            pytest.skip("no second deliverable file to cross-scope check")
        r2 = requests.get(f"{BASE_URL}/api/rendering/asset/{other_fid}?token={tok}", timeout=20)
        assert r2.status_code == 403, f"expected 403 file-scope, got {r2.status_code}"


# ---------- Public storefront images stay public ----------
class TestPublicStorefront:
    def test_cover_image_public(self, api):
        # find any cover-*.png filename on any product with rendered_assets
        r = api.get(f"{BASE_URL}/api/products", timeout=30)
        d = r.json(); prods = d if isinstance(d, list) else d.get("products", [])
        cover_fname = None
        for p in prods:
            ra = p.get("rendered_assets") or {}
            for k, v in ra.items():
                if isinstance(v, str) and "cover-" in v and (v.endswith(".png") or v.endswith(".jpg")):
                    # extract filename tail
                    tail = v.rsplit("/", 1)[-1]
                    if tail.startswith("cover-"):
                        cover_fname = tail; break
            if cover_fname:
                break
        if not cover_fname:
            pytest.skip("no cover-*.png filename discoverable in listings")
        r = requests.get(f"{BASE_URL}/api/rendering/asset/{cover_fname}", timeout=20)
        assert r.status_code == 200, f"expected 200 for public cover, got {r.status_code}"

    def test_public_home(self):
        r = requests.get(f"{BASE_URL}/api/public/home", timeout=20)
        assert r.status_code == 200

    def test_public_books(self):
        r = requests.get(f"{BASE_URL}/api/public/books", timeout=20)
        assert r.status_code == 200


# ---------- Upgrade-all-documents (Publication Quality batch) ----------
class TestPublicationOps:
    def test_status_has_eligible_count(self, api):
        r = api.get(f"{BASE_URL}/api/products/rerender-documents/status", timeout=20)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert isinstance(data.get("eligible_count"), int)
        assert data.get("eligible_count") >= 0
        assert "status" in data


# ---------- QA Cleanup™ — mark → trash → restore → safeguards ----------
class TestQACleanup:
    _pid = None
    _title = None

    @pytest.fixture(autouse=True)
    def _pick_unpublished(self, api):
        if TestQACleanup._pid:
            return
        r = api.get(f"{BASE_URL}/api/products", timeout=30)
        assert r.status_code == 200
        d = r.json(); prods = d if isinstance(d, list) else d.get("products", [])
        # unpublished product (no status published/live/production)
        for p in prods:
            st = (p.get("status") or "").lower()
            if st in ("published", "live", "production"):
                continue
            if p.get("published") or p.get("live"):
                continue
            TestQACleanup._pid = p["id"]
            TestQACleanup._title = p.get("title")
            break
        assert TestQACleanup._pid, "no unpublished product found"

    def test_mark_qa_status_test(self, api):
        r = api.post(f"{BASE_URL}/api/products/{self._pid}/qa-status",
                     json={"qa_status": "test"}, timeout=15)
        assert r.status_code == 200, r.text[:200]
        assert r.json().get("qa_status") == "test"

    def test_eligible_list_contains_product(self, api):
        r = api.get(f"{BASE_URL}/api/products/qa-cleanup/eligible", timeout=20)
        assert r.status_code == 200
        data = r.json()
        ids = [x["id"] for x in data.get("products", []) if x.get("eligible")]
        assert self._pid in ids, "product not in eligible list"

    def test_soft_delete_and_restore(self, api):
        r = api.post(f"{BASE_URL}/api/products/{self._pid}/qa-cleanup",
                     json={"reason": "iter85 e2e test"}, timeout=20)
        assert r.status_code == 200, r.text[:200]
        trash_id = r.json().get("trash_id")
        assert trash_id
        # confirm in trash
        r = api.get(f"{BASE_URL}/api/products/qa-cleanup/trash", timeout=20)
        assert r.status_code == 200
        assert any(t.get("id") == trash_id for t in r.json().get("trash", []))
        # restore
        r = api.post(f"{BASE_URL}/api/products/qa-cleanup/trash/{trash_id}/restore",
                     json={}, timeout=20)
        assert r.status_code == 200, r.text[:200]
        # clear qa_status to leave state clean
        r = api.post(f"{BASE_URL}/api/products/{self._pid}/qa-status",
                     json={"qa_status": None}, timeout=15)
        assert r.status_code == 200

    def test_permanent_delete_requires_exact_title(self, api):
        # create a throwaway product? we skip creating & instead test the safeguard by
        # re-soft-deleting a marked-'test' product then attempting perm delete with wrong title.
        r = api.post(f"{BASE_URL}/api/products/{self._pid}/qa-status",
                     json={"qa_status": "test"}, timeout=15)
        assert r.status_code == 200
        r = api.post(f"{BASE_URL}/api/products/{self._pid}/qa-cleanup",
                     json={"reason": "iter85 perm-delete safeguard"}, timeout=20)
        assert r.status_code == 200
        trash_id = r.json()["trash_id"]
        # WRONG title → error
        r = api.post(f"{BASE_URL}/api/products/qa-cleanup/trash/{trash_id}/permanent-delete",
                     json={"confirm_title": "WRONG"}, timeout=15)
        assert r.status_code == 400
        assert "does not match" in r.text.lower() or "confirmation" in r.text.lower()
        # restore to leave state clean
        r = api.post(f"{BASE_URL}/api/products/qa-cleanup/trash/{trash_id}/restore",
                     json={}, timeout=20)
        assert r.status_code == 200
        r = api.post(f"{BASE_URL}/api/products/{self._pid}/qa-status",
                     json={"qa_status": None}, timeout=15)
        assert r.status_code == 200

    def test_published_product_protected(self, api):
        r = api.get(f"{BASE_URL}/api/products", timeout=30)
        d = r.json(); prods = d if isinstance(d, list) else d.get("products", [])
        pub = None
        for p in prods:
            st = (p.get("status") or "").lower()
            if st in ("published", "live", "production") or p.get("published") or p.get("live"):
                pub = p; break
        if not pub:
            pytest.skip("no published product to verify safeguard")
        # marking is allowed by super-admin, but attempted qa-cleanup soft-delete must block
        r = api.post(f"{BASE_URL}/api/products/{pub['id']}/qa-status",
                     json={"qa_status": "test"}, timeout=15)
        # cleanup MUST refuse — either via eligible=false or via /qa-cleanup returning 400
        r = api.post(f"{BASE_URL}/api/products/{pub['id']}/qa-cleanup",
                     json={"reason": "attempt on published"}, timeout=20)
        assert r.status_code == 400, r.text[:300]
        body = r.text.lower()
        assert "publish" in body or "production" in body or "protected" in body
        # cleanup: unmark
        api.post(f"{BASE_URL}/api/products/{pub['id']}/qa-status",
                 json={"qa_status": None}, timeout=15)
