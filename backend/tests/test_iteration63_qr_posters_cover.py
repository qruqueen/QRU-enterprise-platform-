"""Iteration 63 — QRU Factory tests
- QICS QR portal 403 → 200 fix (public URL)
- 5 new poster templates render (DRAFT + TREASURE_STANDARD_PASSED)
- Cover Studio KR-brief auto-fill endpoint
"""
import base64
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
PUBLIC_URL = "https://enterprise-os-17.preview.emergentagent.com"
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"
KR_ID = "1a93ceb2-0334-46ff-a3a4-54bda17d7b8f"
QICS_IDENTITY = "QRU-BK-000004"
NEW_TEMPLATES = [
    "identity-anatomy-v1",
    "give-credit-v1",
    "why-forex-v1",
    "utility-principle-v1",
    "brain-translation-v1",
]


@pytest.fixture(scope="module")
def founder_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD, "access_token": FOUNDER_PASSWORD},
                      timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def auth_headers(founder_token):
    return {"Authorization": f"Bearer {founder_token}"}


# ---- QICS portal fix ----
class TestQicsPortalUrl:
    def test_portals_use_public_https(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/qics/portals", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        portals = body if isinstance(body, list) else body.get("portals") or body.get("items") or []
        assert isinstance(portals, list) and len(portals) >= 1, f"no portals in {body}"
        for p in portals:
            purl = p.get("portal_url", "")
            assert purl.startswith(PUBLIC_URL), f"portal_url not public https: {purl}"
            assert "cluster-" not in purl, f"portal_url still uses internal cluster host: {purl}"

    def test_public_portal_scan_is_200(self):
        # Public — MUST NOT require auth
        r = requests.get(f"{BASE_URL}/api/qics/portal/{QICS_IDENTITY}", timeout=30)
        assert r.status_code == 200, f"Portal scan not 200: {r.status_code} {r.text[:200]}"
        j = r.json()
        # basic portal shape
        assert isinstance(j, dict)

    def test_activate_produces_public_url(self, auth_headers):
        # Try storefront first (public), then fallback to any known product
        pid = None
        r = requests.get(f"{BASE_URL}/api/commerce/storefront", headers=auth_headers, timeout=30)
        if r.status_code == 200:
            body = r.json()
            items = body if isinstance(body, list) else (body.get("products") or body.get("items") or [])
            if items:
                pid = items[0].get("id") or items[0].get("product_id")
        if not pid:
            pytest.skip("No product available to activate a fresh portal")
        ra = requests.post(f"{BASE_URL}/api/qics/activate/{pid}", headers=auth_headers, timeout=60)
        assert ra.status_code in (200, 201), f"activate failed: {ra.status_code} {ra.text[:200]}"
        doc = ra.json()
        purl = doc.get("portal_url", "")
        assert purl.startswith(PUBLIC_URL), f"newly-activated portal_url not public: {purl}"
        # And the resulting portal must actually be scan-able (200) at the public URL
        ident = doc.get("qics_identity")
        rs = requests.get(f"{BASE_URL}/api/qics/portal/{ident}", timeout=30)
        assert rs.status_code == 200


# ---- Poster templates ----
class TestPosterTemplates:
    def test_templates_list_has_new_5(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/publishing/poster/templates", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text[:200]
        payload = r.json()
        tpls = payload if isinstance(payload, list) else payload.get("templates") or payload.get("items") or []
        assert isinstance(tpls, list)
        ids = {t.get("id") or t.get("template_id") for t in tpls}
        assert len(tpls) >= 11, f"expected >=11 templates, got {len(tpls)}: {ids}"
        for tid in NEW_TEMPLATES:
            assert tid in ids, f"missing new template {tid} in {ids}"

    @pytest.mark.parametrize("tid", NEW_TEMPLATES)
    def test_generate_each_template(self, auth_headers, tid):
        payload = {"template_id": tid, "kr_id": KR_ID}
        r = requests.post(f"{BASE_URL}/api/publishing/poster/generate",
                          headers=auth_headers, json=payload, timeout=60)
        assert r.status_code == 200, f"[{tid}] generate failed: {r.status_code} {r.text[:400]}"
        data = r.json()
        # Locate PNG bytes / url and status/treasure fields robustly
        status = (data.get("status") or (data.get("poster") or {}).get("status") or "").upper()
        treasure = (data.get("treasure_status") or (data.get("poster") or {}).get("treasure_status") or "").upper()
        assert status == "DRAFT", f"[{tid}] status expected DRAFT, got {status}. Full: {list(data.keys())}"
        assert treasure == "TREASURE_STANDARD_PASSED", f"[{tid}] treasure_status={treasure}"
        # Check PNG produced
        png_b64 = data.get("png_base64") or (data.get("poster") or {}).get("png_base64")
        png_url = data.get("png_url") or data.get("file_url") or (data.get("poster") or {}).get("file")
        assert png_b64 or png_url, f"[{tid}] no PNG bytes or URL in response keys={list(data.keys())}"
        if png_b64:
            raw = base64.b64decode(png_b64)
            assert len(raw) > 500, f"[{tid}] PNG too small: {len(raw)} bytes"
            assert raw[:4] == b"\x89PNG", f"[{tid}] not a real PNG"
        elif png_url:
            # follow url; may be relative /api path
            url = png_url if png_url.startswith("http") else f"{BASE_URL}{png_url}"
            g = requests.get(url, headers=auth_headers, timeout=30)
            assert g.status_code == 200
            assert len(g.content) > 500
            assert g.content[:4] == b"\x89PNG" or "png" in g.headers.get("content-type", "").lower()


# ---- Cover Studio KR-brief ----
class TestCoverKrBrief:
    def test_kr_brief_autofill(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/publishing/cover/kr-brief/{KR_ID}", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text[:200]
        j = r.json()
        for k in ("title", "subtitle", "series", "concept_notes"):
            assert k in j and j[k], f"kr-brief missing/empty field: {k}"
        assert isinstance(j["title"], str) and len(j["title"]) > 0
        assert "QRU" in j["series"] or "Foundations" in j["series"]

    def test_kr_brief_404_missing(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/publishing/cover/kr-brief/does-not-exist-xyz",
                         headers=auth_headers, timeout=30)
        assert r.status_code in (404, 400)
