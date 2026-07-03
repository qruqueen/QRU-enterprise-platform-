"""MT-029 — Founder Asset Selection™ backend tests.

Validates:
  1. POST /api/vault/upload creates a selectable asset (Cover, Protected Master or
     Founder Imported, Treasure Standard™ Approved, product_family=Health).
  2. GET /api/vault/assets?selectable=true returns the uploaded asset (reusable-only).
  3. GET /api/vault/recommend?product_family=Health returns recommendations.
  4. POST /api/products/assemble with asset_mode='use_imported' + asset_vault_id:
       - creates a product with cover_source='asset_vault_selected'
       - populates manufacturing_asset with the required fields
       - does NOT regenerate: cover_has_hero_art=false
       - the asset's related_products lists the new product
  5. asset_mode='generate' sets product.asset_mode='generate'
  6. asset_mode default ('director') works without asset_vault_id
  7. Backwards compatibility: omitting asset_mode still assembles normally.
"""
import io
import os
import struct
import uuid
import zlib

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"

FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    return s


@pytest.fixture(scope="session")
def token(session):
    r = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD},
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="session")
def auth(session, token):
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


@pytest.fixture(scope="session")
def kr_id(auth):
    r = auth.get(f"{BASE_URL}/api/knowledge-records?limit=1")
    krs = r.json() if isinstance(r.json(), list) else r.json().get("records", [])
    assert krs, "Need at least one KR to assemble products"
    return krs[0]["id"]


def _tiny_png() -> bytes:
    """32x32 solid-color PNG built by hand (no PIL dep)."""
    # Use a minimal valid PNG. We construct via zlib+crc.
    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 32, 32, 8, 2, 0, 0, 0)  # 8-bit RGB
    # 32 rows of 32 pixels RGB (each row prefixed with filter byte 0)
    raw = b""
    for _ in range(32):
        raw += b"\x00" + (b"\x80\x40\xC0" * 32)
    idat = zlib.compress(raw)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


@pytest.fixture(scope="class")
def uploaded_asset(auth):
    """Upload a selectable Cover asset (Protected Master + Treasure Standard™ Approved)."""
    png = _tiny_png()
    name = f"TEST_MT029_Cover_{uuid.uuid4().hex[:6]}"
    files = {"file": (f"{name}.png", png, "image/png")}
    data = {
        "name": name,
        "asset_type": "Cover",
        "source": "Protected Master",
        "approval_status": "Treasure Standard™ Approved",
        "product_family": "Health",
    }
    # requests will strip Content-Type: application/json for multipart when file provided
    # but session set it earlier — need to override for this call
    headers = dict(auth.headers)
    headers.pop("Content-Type", None)
    r = auth.post(f"{BASE_URL}/api/vault/upload", files=files, data=data, headers=headers)
    assert r.status_code in (200, 201), r.text[:300]
    asset = r.json()
    assert asset["asset_type"] == "Cover"
    assert asset["source"] == "Protected Master"
    assert asset["approval_status"] == "Treasure Standard™ Approved"
    assert asset["product_family"] == "Health"
    assert asset["version"] == 1
    yield asset
    # cleanup: archive (there's no explicit delete)
    try:
        auth.patch(f"{BASE_URL}/api/vault/{asset['id']}", json={"archived": True})
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# 1) Upload + listing + recommend
# --------------------------------------------------------------------------- #
class TestVaultSelectableAndRecommend:
    def test_selectable_list_includes_uploaded(self, auth, uploaded_asset):
        r = auth.get(f"{BASE_URL}/api/vault/assets?selectable=true")
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()["assets"]]
        assert uploaded_asset["id"] in ids, "Uploaded selectable asset not returned by selectable=true"

    def test_recommend_returns_health_assets(self, auth, uploaded_asset):
        r = auth.get(f"{BASE_URL}/api/vault/recommend?product_family=Health")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 1
        assert any(a["id"] == uploaded_asset["id"] for a in data["assets"]), (
            "Uploaded Health-family asset missing from recommendations"
        )


# --------------------------------------------------------------------------- #
# 2) Assemble with asset_mode=use_imported
# --------------------------------------------------------------------------- #
class TestAssembleWithImportedAsset:
    def test_use_imported_creates_product_with_manufacturing_asset(self, auth, uploaded_asset, kr_id):
        payload = {
            "knowledge_record_id": kr_id,
            "product_type": "Poster",
            "asset_mode": "use_imported",
            "asset_vault_id": uploaded_asset["id"],
        }
        headers = dict(auth.headers)
        headers.setdefault("Content-Type", "application/json")
        r = auth.post(f"{BASE_URL}/api/products/assemble", json=payload, headers=headers)
        assert r.status_code in (200, 201), r.text[:300]
        product = r.json()
        pid = product["id"]
        # Some clients get the freshly-inserted product without manufacturing_asset
        # because it is applied AFTER insert but the endpoint refetches. Verify via GET.
        p = auth.get(f"{BASE_URL}/api/products/{pid}").json()

        assert p.get("asset_mode") == "use_imported", p.get("asset_mode")
        assert p.get("cover_source") == "asset_vault_selected", p.get("cover_source")
        assert p.get("cover_has_hero_art") is False, p.get("cover_has_hero_art")

        mfg = p.get("manufacturing_asset") or {}
        assert mfg.get("asset_vault_id") == uploaded_asset["id"], mfg
        assert mfg.get("asset_code") == uploaded_asset["asset_code"]
        assert mfg.get("asset_version") == uploaded_asset["version"]
        assert mfg.get("asset_source") == "Protected Master"
        assert mfg.get("asset_name") == uploaded_asset["name"]
        assert mfg.get("asset_type") == "Cover"
        assert mfg.get("approval_status") == "Treasure Standard™ Approved"

        # cleanup created product
        auth.delete(f"{BASE_URL}/api/products/{pid}")

    def test_asset_related_products_updated(self, auth, uploaded_asset, kr_id):
        payload = {
            "knowledge_record_id": kr_id,
            "product_type": "Poster",
            "asset_mode": "use_imported",
            "asset_vault_id": uploaded_asset["id"],
        }
        headers = dict(auth.headers)
        headers.setdefault("Content-Type", "application/json")
        r = auth.post(f"{BASE_URL}/api/products/assemble", json=payload, headers=headers)
        assert r.status_code in (200, 201)
        pid = r.json()["id"]

        av = auth.get(f"{BASE_URL}/api/vault/{uploaded_asset['id']}").json()
        rel_ids = [rp.get("id") for rp in av.get("related_products", [])]
        assert pid in rel_ids, f"Asset.related_products missing new product {pid}: {rel_ids}"

        auth.delete(f"{BASE_URL}/api/products/{pid}")


# --------------------------------------------------------------------------- #
# 3) Other asset modes: generate + director (default) + backward compat
# --------------------------------------------------------------------------- #
class TestAssetModes:
    def _assemble(self, auth, kr_id, **extra):
        payload = {"knowledge_record_id": kr_id, "product_type": "Poster", **extra}
        headers = dict(auth.headers)
        headers.setdefault("Content-Type", "application/json")
        return auth.post(f"{BASE_URL}/api/products/assemble", json=payload, headers=headers)

    def test_generate_mode(self, auth, kr_id):
        r = self._assemble(auth, kr_id, asset_mode="generate")
        assert r.status_code in (200, 201), r.text[:300]
        pid = r.json()["id"]
        p = auth.get(f"{BASE_URL}/api/products/{pid}").json()
        assert p.get("asset_mode") == "generate"
        # Should NOT have manufacturing_asset when no asset selected
        assert p.get("manufacturing_asset") in (None, {}, )
        auth.delete(f"{BASE_URL}/api/products/{pid}")

    def test_director_mode_default_when_omitted(self, auth, kr_id):
        r = self._assemble(auth, kr_id)  # asset_mode omitted
        assert r.status_code in (200, 201), r.text[:300]
        pid = r.json()["id"]
        p = auth.get(f"{BASE_URL}/api/products/{pid}").json()
        # default is 'director'
        assert p.get("asset_mode") == "director", p.get("asset_mode")
        auth.delete(f"{BASE_URL}/api/products/{pid}")

    def test_director_mode_explicit(self, auth, kr_id):
        r = self._assemble(auth, kr_id, asset_mode="director")
        assert r.status_code in (200, 201)
        pid = r.json()["id"]
        p = auth.get(f"{BASE_URL}/api/products/{pid}").json()
        assert p.get("asset_mode") == "director"
        auth.delete(f"{BASE_URL}/api/products/{pid}")
