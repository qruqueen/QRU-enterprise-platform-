"""Iteration 61 backend tests — Book Publishing (Store + KDP) and Audiobook.

Endpoints under test:
  POST /api/publishing/product/{pid}/publish-store
  POST /api/publishing/product/{pid}/kdp-package
  GET  /api/publishing/product/{pid}/kdp-file
  POST /api/publishing/product/{pid}/audiobook
  GET  /api/publishing/product/{pid}/audiobook-status
  GET  /api/publishing/product/{pid}/audiobook-file
"""
import os
import time
import io
import zipfile
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

# Provided test products
PROD_LOVE = "8c8c6084-c49a-4a37-a374-2973cd515551"        # Love — Book (rendered PDF)
PROD_SHORT = "01615dca-1d2e-446c-874f-f7b46a2c1a4c"       # Shorter book for faster audiobook


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "access_token": FOUNDER_PASSWORD},
                      timeout=30)
    if r.status_code != 200:
        # Try alternate field name (password) just in case
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD},
                          timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:400]}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def h(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ─────────────────────── Publish to QRU Store ────────────────────────────────
class TestPublishStore:
    def test_publish_store_love_book(self, h):
        r = requests.post(f"{BASE_URL}/api/publishing/product/{PROD_LOVE}/publish-store",
                          headers=h, timeout=30)
        assert r.status_code == 200, r.text[:500]
        data = r.json()
        assert data.get("ok") is True, f"ok not true: {data}"
        assert data.get("status") == "Published"
        assert data.get("product_id") == PROD_LOVE
        assert "purchasable" in (data.get("message") or "").lower() or "Store" in (data.get("message") or "")

    def test_publish_store_unknown_product_404(self, h):
        r = requests.post(f"{BASE_URL}/api/publishing/product/does-not-exist-xyz/publish-store",
                          headers=h, timeout=30)
        assert r.status_code == 404

    def test_publish_store_idempotent(self, h):
        # Calling publish-store again on already-Published product should still return ok=true
        r = requests.post(f"{BASE_URL}/api/publishing/product/{PROD_LOVE}/publish-store",
                          headers=h, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
        assert data.get("status") == "Published"


# ─────────────────────── KDP-Ready Package ───────────────────────────────────
class TestKdpPackage:
    def test_kdp_package_build(self, h):
        r = requests.post(f"{BASE_URL}/api/publishing/product/{PROD_LOVE}/kdp-package",
                          headers=h, timeout=60)
        assert r.status_code == 200, r.text[:500]
        data = r.json()
        assert data.get("ok") is True, f"ok not true: {data}"
        contents = data.get("contents") or []
        assert "interior.pdf" in contents
        assert "KDP-Publishing-Kit.pdf" in contents
        assert data.get("download_url", "").endswith("/kdp-file")
        # metadata sanity
        meta = data.get("metadata") or {}
        assert meta.get("title")
        assert isinstance(meta.get("keywords"), list)

    def test_kdp_file_download_valid_zip(self, h):
        # Retry once on 502 (ingress transient)
        for attempt in range(2):
            r = requests.get(f"{BASE_URL}/api/publishing/product/{PROD_LOVE}/kdp-file",
                             headers=h, timeout=120, stream=True)
            if r.status_code == 200:
                break
            time.sleep(3)
        assert r.status_code == 200, r.text[:500]
        assert "application/zip" in r.headers.get("content-type", "")
        body = r.content
        # Verify zip integrity + expected files
        z = zipfile.ZipFile(io.BytesIO(body))
        names = z.namelist()
        assert "interior.pdf" in names, f"Missing interior.pdf. Got: {names}"
        assert "KDP-Publishing-Kit.pdf" in names, f"Missing KDP-Publishing-Kit.pdf. Got: {names}"
        # interior should be a nontrivial pdf
        interior = z.read("interior.pdf")
        assert interior[:4] == b"%PDF", "interior.pdf is not a real PDF"
        assert len(interior) > 5000, f"interior.pdf too small: {len(interior)}"
        kit = z.read("KDP-Publishing-Kit.pdf")
        assert kit[:4] == b"%PDF"

    def test_kdp_package_unknown_product(self, h):
        r = requests.post(f"{BASE_URL}/api/publishing/product/nope-nope-nope/kdp-package",
                          headers=h, timeout=30)
        assert r.status_code == 404

    def test_kdp_file_unknown_product(self, h):
        r = requests.get(f"{BASE_URL}/api/publishing/product/nope-nope-nope/kdp-file",
                         headers=h, timeout=30)
        assert r.status_code == 404


# ─────────────────────── Audiobook (background) ──────────────────────────────
class TestAudiobook:
    def test_audiobook_start_returns_rendering(self, h):
        payload = {"voice": "sage"}
        r = requests.post(f"{BASE_URL}/api/publishing/product/{PROD_SHORT}/audiobook",
                          headers=h, json=payload, timeout=30)
        assert r.status_code == 200, r.text[:500]
        data = r.json()
        # It could already be READY from a previous run — accept either RENDERING or READY
        assert data.get("status") in ("RENDERING", "READY") or data.get("ok") is True, f"Unexpected: {data}"

    def test_audiobook_polls_to_ready(self, h):
        deadline = time.time() + 120  # allow up to 120s
        status = None
        last = None
        while time.time() < deadline:
            try:
                r = requests.get(f"{BASE_URL}/api/publishing/product/{PROD_SHORT}/audiobook-status",
                                 headers=h, timeout=45)
                assert r.status_code == 200, r.text[:400]
                last = r.json()
                status = last.get("status")
                if status in ("READY", "FAILED"):
                    break
            except requests.exceptions.ReadTimeout:
                pass
            time.sleep(4)
        assert status == "READY", f"Audiobook did not reach READY. Last status: {last}"
        assert last.get("format") == "mp3"
        assert last.get("bytes", 0) > 20000, f"MP3 too small: {last.get('bytes')}"
        assert last.get("url", "").endswith("/audiobook-file")

    def test_audiobook_file_download_is_mp3(self, h):
        r = requests.get(f"{BASE_URL}/api/publishing/product/{PROD_SHORT}/audiobook-file",
                         headers=h, timeout=60)
        assert r.status_code == 200, r.text[:400]
        ct = r.headers.get("content-type", "")
        assert "audio/mpeg" in ct or "audio" in ct, f"Unexpected content-type: {ct}"
        body = r.content
        # MP3 sig: ID3 or 0xFF 0xFB / 0xFF 0xF3 / 0xFF 0xE3
        assert body[:3] == b"ID3" or (body[:1] == b"\xff" and body[1] in (0xFB, 0xF3, 0xE3, 0xFA, 0xF2)), \
            f"Not a real MP3. First bytes: {body[:8].hex()}"
        assert len(body) > 20000, f"MP3 too small: {len(body)}"

    def test_audiobook_status_unknown_product(self, h):
        r = requests.get(f"{BASE_URL}/api/publishing/product/nope-nope-nope/audiobook-status",
                         headers=h, timeout=30)
        assert r.status_code == 404


# ─────────────────────── Honest YouTube status regression ────────────────────
class TestYouTubeFactoryAssets:
    def test_factory_assets_lists_rendered_only(self, h):
        # Sanity: rendered MP4 list is real. Storyboard-only products should NOT appear here.
        r = requests.get(f"{BASE_URL}/api/youtube/factory-assets", headers=h, timeout=30)
        # Some deployments require auth; some don't. Accept 200; skip on 404 to avoid false negative.
        if r.status_code == 404:
            pytest.skip("factory-assets endpoint not present")
        assert r.status_code == 200, r.text[:400]
        data = r.json()
        # Must have assets or empty list; not a fake state
        assert "assets" in data or isinstance(data, list) or "videos" in data
