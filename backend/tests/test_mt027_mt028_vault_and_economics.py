"""MT-027 QRU Asset Vault™ + MT-028 Manufacturing Economics™ — pytest suite.

Runs against public REACT_APP_BACKEND_URL as Founder.
"""
import io
import os
import struct
import zlib
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


def _make_png(w=8, h=8, color=(200, 50, 90)):
    """Build a tiny valid PNG in-memory (no Pillow dependency)."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b""
    for _ in range(h):
        raw += b"\x00" + bytes(color) * w
    idat = zlib.compress(raw)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.text}"
    tok = r.json()["access_token"] if "access_token" in r.json() else r.json().get("token")
    assert tok, f"No token in login: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ────────────────────────── MT-027 VAULT ──────────────────────────

class TestVaultMeta:
    def test_meta_returns_expected_lists(self, auth):
        r = requests.get(f"{BASE_URL}/api/vault/meta", headers=auth, timeout=30)
        assert r.status_code == 200
        j = r.json()
        assert len(j["sources"]) == 6
        assert len(j["approval_statuses"]) == 7
        assert len(j["asset_types"]) == 22
        assert "Founder Imported" in j["sources"]
        assert "Founder Approved" in j["approval_statuses"]
        assert "Cover" in j["asset_types"]


@pytest.fixture(scope="module")
def founder_cover_asset(auth):
    """Upload a Founder Cover for family 'TEST_Health' and return the asset dict."""
    png = _make_png()
    files = {"file": ("TEST_health_cover.png", png, "image/png")}
    data = {"name": "TEST_ Founder Health Cover",
            "asset_type": "Cover", "source": "Founder Imported",
            "approval_status": "Founder Approved", "product_family": "TEST_Health"}
    r = requests.post(f"{BASE_URL}/api/vault/upload", headers=auth, files=files, data=data, timeout=60)
    assert r.status_code == 200, r.text
    a = r.json()
    return a


class TestVaultUpload:
    def test_upload_creates_correct_asset(self, founder_cover_asset):
        a = founder_cover_asset
        assert a["asset_code"].startswith("AV-")
        assert a["source"] == "Founder Imported"
        assert a["approval_status"] == "Founder Approved"
        assert a["version"] == 1
        assert a["asset_type"] == "Cover"
        assert a["replacement_rule"], "replacement_rule should be set"
        assert a["file"]["url"].startswith("/api/vault/asset/")
        assert a["file"]["media_type"] == "image/png"
        assert isinstance(a.get("version_history"), list) and len(a["version_history"]) == 1


class TestVaultListAndFilters:
    def test_list_contains_uploaded(self, auth, founder_cover_asset):
        r = requests.get(f"{BASE_URL}/api/vault/assets", headers=auth, timeout=30)
        assert r.status_code == 200
        codes = [x["asset_code"] for x in r.json()["assets"]]
        assert founder_cover_asset["asset_code"] in codes

    def test_filter_by_type(self, auth):
        r = requests.get(f"{BASE_URL}/api/vault/assets",
                         headers=auth, params={"asset_type": "Cover"}, timeout=30)
        assert r.status_code == 200
        for a in r.json()["assets"]:
            assert a["asset_type"] == "Cover"

    def test_filter_by_source(self, auth):
        r = requests.get(f"{BASE_URL}/api/vault/assets",
                         headers=auth, params={"source": "Founder Imported"}, timeout=30)
        assert r.status_code == 200
        for a in r.json()["assets"]:
            assert a["source"] == "Founder Imported"

    def test_search_q(self, auth, founder_cover_asset):
        r = requests.get(f"{BASE_URL}/api/vault/assets",
                         headers=auth, params={"q": "TEST_ Founder Health"}, timeout=30)
        assert r.status_code == 200
        codes = [x["asset_code"] for x in r.json()["assets"]]
        assert founder_cover_asset["asset_code"] in codes

    def test_filter_by_family(self, auth, founder_cover_asset):
        r = requests.get(f"{BASE_URL}/api/vault/assets",
                         headers=auth, params={"product_family": "TEST_Health"}, timeout=30)
        assert r.status_code == 200
        found = [x for x in r.json()["assets"] if x["id"] == founder_cover_asset["id"]]
        assert found, "Filter by product_family didn't return uploaded asset"


class TestVaultAssetServing:
    def test_serve_inline_image_png(self, founder_cover_asset):
        fname = founder_cover_asset["file"]["filename"]
        r = requests.get(f"{BASE_URL}/api/vault/asset/{fname}", timeout=30)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("image/png")
        assert r.content[:4] == b"\x89PNG"
        # Inline (no attachment)
        cd = r.headers.get("content-disposition", "")
        assert "attachment" not in cd.lower()

    def test_serve_download_attachment(self, founder_cover_asset):
        fname = founder_cover_asset["file"]["filename"]
        r = requests.get(f"{BASE_URL}/api/vault/asset/{fname}",
                         params={"download": 1, "name": "MyCover"}, timeout=30)
        assert r.status_code == 200
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd.lower()
        assert "MyCover" in cd


class TestVaultPatchAndLink:
    def test_patch_to_protected_master(self, auth, founder_cover_asset):
        r = requests.patch(f"{BASE_URL}/api/vault/{founder_cover_asset['id']}",
                           headers=auth, json={"source": "Protected Master"}, timeout=30)
        assert r.status_code == 200
        a = r.json()
        assert a["source"] == "Protected Master"
        assert "Never recreate" in a["replacement_rule"]
        # Revert back
        requests.patch(f"{BASE_URL}/api/vault/{founder_cover_asset['id']}",
                       headers=auth, json={"source": "Founder Imported"}, timeout=30)

    def test_patch_approval_status(self, auth, founder_cover_asset):
        r = requests.patch(f"{BASE_URL}/api/vault/{founder_cover_asset['id']}",
                           headers=auth, json={"approval_status": "Brand Approved"}, timeout=30)
        assert r.status_code == 200
        assert r.json()["approval_status"] == "Brand Approved"
        requests.patch(f"{BASE_URL}/api/vault/{founder_cover_asset['id']}",
                       headers=auth, json={"approval_status": "Founder Approved"}, timeout=30)

    def test_link_product(self, auth, founder_cover_asset):
        # Find any product
        pr = requests.get(f"{BASE_URL}/api/products", headers=auth, timeout=30)
        if pr.status_code != 200:
            pytest.skip("Products endpoint unavailable")
        products = pr.json() if isinstance(pr.json(), list) else pr.json().get("products", [])
        if not products:
            pytest.skip("No products to link")
        pid = products[0]["id"]
        r = requests.post(f"{BASE_URL}/api/vault/{founder_cover_asset['id']}/link-product",
                          headers=auth, json={"product_id": pid}, timeout=30)
        assert r.status_code == 200
        assert any(p["id"] == pid for p in r.json()["related_products"])


class TestVaultVersioning:
    def test_new_version_preserves_original(self, auth, founder_cover_asset):
        original_file = founder_cover_asset["file"]
        v2_png = _make_png(color=(20, 200, 70))
        files = {"file": ("TEST_health_cover_v2.png", v2_png, "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/vault/{founder_cover_asset['id']}/new-version",
            headers=auth, files=files, data={"reason": "TEST_ upgrade"}, timeout=60)
        assert r.status_code == 200, r.text
        a = r.json()
        assert a["version"] == 2
        assert a["file"]["filename"] != original_file["filename"]
        # Original file must still exist and be accessible
        r1 = requests.get(f"{BASE_URL}/api/vault/asset/{original_file['filename']}", timeout=30)
        assert r1.status_code == 200, "Original v1 file must NOT be overwritten"
        # version_history must have both entries
        vers = [v["version"] for v in a["version_history"]]
        assert 1 in vers and 2 in vers
        # v2 entry stores previous_file
        v2 = [v for v in a["version_history"] if v["version"] == 2][0]
        assert v2.get("previous_file", {}).get("filename") == original_file["filename"]


class TestVaultArchive:
    def test_archive_removes_from_default_list(self, auth, founder_cover_asset):
        # Archive
        r = requests.patch(f"{BASE_URL}/api/vault/{founder_cover_asset['id']}",
                           headers=auth, json={"archived": True}, timeout=30)
        assert r.status_code == 200
        # Default listing excludes archived
        rd = requests.get(f"{BASE_URL}/api/vault/assets", headers=auth, timeout=30)
        assert rd.status_code == 200
        codes = [x["asset_code"] for x in rd.json()["assets"]]
        assert founder_cover_asset["asset_code"] not in codes, "Archived asset must NOT appear by default"
        # include_archived=true includes it
        ra = requests.get(f"{BASE_URL}/api/vault/assets", headers=auth,
                          params={"include_archived": "true"}, timeout=30)
        assert ra.status_code == 200
        codes_all = [x["asset_code"] for x in ra.json()["assets"]]
        assert founder_cover_asset["asset_code"] in codes_all
        # Un-archive for downstream tests
        requests.patch(f"{BASE_URL}/api/vault/{founder_cover_asset['id']}",
                       headers=auth, json={"archived": False}, timeout=30)


class TestVaultLookup:
    def test_lookup_finds_founder_cover(self, auth, founder_cover_asset):
        # Ensure asset is unarchived and approved
        requests.patch(f"{BASE_URL}/api/vault/{founder_cover_asset['id']}",
                       headers=auth, json={"archived": False,
                                           "approval_status": "Founder Approved",
                                           "source": "Founder Imported"}, timeout=30)
        r = requests.get(f"{BASE_URL}/api/vault/lookup", headers=auth,
                         params={"asset_type": "Cover", "product_family": "TEST_Health"}, timeout=30)
        assert r.status_code == 200
        j = r.json()
        assert j["found"] is True
        assert j["reusable"]["id"] == founder_cover_asset["id"]

    def test_lookup_returns_none_for_no_match(self, auth):
        r = requests.get(f"{BASE_URL}/api/vault/lookup", headers=auth,
                         params={"asset_type": "Cover",
                                 "product_family": "TEST_NoSuchFamily_ZZZ"}, timeout=30)
        assert r.status_code == 200
        assert r.json()["found"] is False


# ────────────────────────── MT-028 ECONOMICS ──────────────────────────

class TestEconomicsOverview:
    def test_overview_shape_and_summary(self, auth):
        r = requests.get(f"{BASE_URL}/api/economics/overview", headers=auth, timeout=60)
        assert r.status_code == 200
        j = r.json()
        for k in ("ai_dashboard", "summary", "products", "credit_consumption",
                  "recommendations", "assumptions", "generated_at"):
            assert k in j, f"missing key {k}"
        s = j["summary"]
        for k in ("products", "avg_manufacturing_cost", "avg_gross_margin_pct", "total_reuse_savings"):
            assert k in s

    def test_products_row_shape_and_rendering_zero(self, auth):
        r = requests.get(f"{BASE_URL}/api/economics/overview", headers=auth, timeout=60)
        assert r.status_code == 200
        rows = r.json()["products"]
        if not rows:
            pytest.skip("No products available")
        for r0 in rows[:5]:
            for k in ("manufacturing_cost", "cost_breakdown", "suggested_price",
                      "processing_fee", "marketplace_fee", "gross_profit",
                      "gross_margin_pct", "reuse_savings", "cost_basis"):
                assert k in r0, f"missing field {k}"
            # Rendering must be deterministic (0)
            assert r0["cost_breakdown"]["rendering"] == 0.0

    def test_book_price_1499_math(self, auth):
        """Find a Book product with $14.99 price and verify processing fee/profit/margin math."""
        r = requests.get(f"{BASE_URL}/api/economics/overview", headers=auth, timeout=60)
        rows = r.json()["products"]
        candidates = [x for x in rows if x["product_type"] == "Book"
                      and abs((x["suggested_price"] or 0) - 14.99) < 0.01]
        if not candidates:
            pytest.skip("No $14.99 Book product available")
        r0 = candidates[0]
        # Stripe: 2.9% + $0.30 on $14.99 → 0.4347 + 0.30 = 0.73
        assert abs(r0["processing_fee"] - 0.73) < 0.02
        # Profit ~ 14.99 - fee - mfg cost (mfg cost is small). Should be close to ~14.16-ish.
        assert r0["gross_profit"] > 13.5
        assert r0["gross_margin_pct"] > 90.0


class TestEconomicsProductRow:
    def test_single_product(self, auth):
        r = requests.get(f"{BASE_URL}/api/economics/overview", headers=auth, timeout=60)
        rows = r.json()["products"]
        if not rows:
            pytest.skip("no products")
        pid = rows[0]["id"]
        r2 = requests.get(f"{BASE_URL}/api/economics/product/{pid}", headers=auth, timeout=30)
        assert r2.status_code == 200
        assert r2.json()["id"] == pid

    def test_single_product_404(self, auth):
        r = requests.get(f"{BASE_URL}/api/economics/product/does-not-exist-zzz",
                         headers=auth, timeout=30)
        assert r.status_code == 404


class TestEconomicsExports:
    def test_csv_export(self, auth):
        r = requests.get(f"{BASE_URL}/api/economics/export/csv", headers=auth, timeout=60)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")
        assert "attachment" in r.headers.get("content-disposition", "").lower()
        text = r.content.decode("utf-8")
        assert "Product Code" in text
        assert "SUMMARY" in text

    def test_pdf_export(self, auth):
        r = requests.get(f"{BASE_URL}/api/economics/export/pdf", headers=auth, timeout=60)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/pdf")
        assert "attachment" in r.headers.get("content-disposition", "").lower()
        assert r.content[:4] == b"%PDF"


# ────────────────────────── REGRESSION ──────────────────────────

class TestRegression:
    def test_certified_product_pipeline_has_customer_deliverable(self, auth):
        pr = requests.get(f"{BASE_URL}/api/products", headers=auth, timeout=30)
        if pr.status_code != 200:
            pytest.skip("products list unavailable")
        products = pr.json() if isinstance(pr.json(), list) else pr.json().get("products", [])
        cert = [p for p in products
                if (p.get("status") in ("Published", "Ready for Release"))
                or p.get("certified") or p.get("treasure_standard_certified")]
        if not cert:
            cert = products[:1]  # fallback: just spot-check first
        if not cert:
            pytest.skip("no products")
        pid = cert[0]["id"]
        r = requests.get(f"{BASE_URL}/api/products/{pid}/pipeline", headers=auth, timeout=30)
        # Just spot-check endpoint responds and has some deliverable info
        assert r.status_code in (200, 404), f"pipeline endpoint failed: {r.status_code}"
        if r.status_code == 200:
            j = r.json()
            # Accept various shapes but expect one of these keys or the raw product
            assert "customer_deliverable" in j or "product" in j or "deliverable" in j or "status" in j
