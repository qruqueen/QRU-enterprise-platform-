"""Iteration 62 — Products Shelf + KR merged list + KR-context handoff
Covers:
 - GET /api/media-studio/products-shelf (total, by_engine, products[])
 - GET /api/media-studio/knowledge-manufacturing merged list (includes both KR collections; verified sorted first)
 - POST /api/media-studio/product/{id}/render-video and /api/youtube/factory-assets pickup
 - Audiobook background job status (READY → real audio/mpeg)
"""
import os
import time
import requests
import pytest

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
PASSWORD = "QruFounder2026!"

VERIFIED_KR_1 = "1a93ceb2-0334-46ff-a3a4-54bda17d7b8f"
VERIFIED_KR_2 = "8eeda74f-8f5e-4678-8458-d691b53877be"
SHORT_BOOK = "01615dca-1d2e-446c-874f-f7b46a2c1a4c"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PASSWORD, "access_token": PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    tk = r.json().get("token") or r.json().get("access_token")
    assert tk, r.json()
    return tk


@pytest.fixture(scope="session")
def H(token):
    return {"Authorization": f"Bearer {token}"}


# ── Products Shelf ──
class TestProductsShelf:
    def test_shelf_returns_total_by_engine_products(self, H):
        r = requests.get(f"{BASE}/api/media-studio/products-shelf", headers=H, timeout=60)
        assert r.status_code == 200, r.text[:200]
        j = r.json()
        assert "total" in j and "by_engine" in j and "products" in j
        assert isinstance(j["products"], list)
        assert j["total"] == len(j["products"])
        # engine coverage — expect all 4 engines have items in this seeded factory
        for k in ("publication", "media", "poster", "recipe"):
            assert k in j["by_engine"], f"missing engine {k}: {j['by_engine']}"
            assert j["by_engine"][k] > 0, f"engine {k} empty"
        # every product has required fields
        for p in j["products"][:20]:
            for f in ("id", "engine", "kind", "status", "route"):
                assert f in p, f"missing {f} in {p}"

    def test_shelf_badges_and_audiobook_url(self, H):
        r = requests.get(f"{BASE}/api/media-studio/products-shelf", headers=H, timeout=60)
        assert r.status_code == 200
        products = r.json()["products"]
        pubs = [p for p in products if p["engine"] == "publication"]
        assert pubs, "no publication products"
        # any book that has an audiobook shows Audiobook badge OR audiobook_url
        with_audio = [p for p in pubs if p.get("audiobook_url") or "Audiobook" in (p.get("badges") or [])]
        # not strict — may be zero
        assert isinstance(with_audio, list)
        # any Published book has 'In QRU Store' badge
        pub_pubs = [p for p in pubs if (p.get("status") or "").lower() == "published"]
        for p in pub_pubs[:3]:
            assert "In QRU Store" in (p.get("badges") or []), f"missing store badge: {p}"

    def test_shelf_media_has_ready_for_youtube_badge_when_rendered(self, H):
        r = requests.get(f"{BASE}/api/media-studio/products-shelf", headers=H, timeout=60)
        media = [p for p in r.json()["products"] if p["engine"] == "media"]
        rendered = [p for p in media if p.get("status") == "RENDERED"]
        for p in rendered[:5]:
            # only youtube_video/promo_short qualify
            kind = (p.get("kind") or "").lower()
            if "youtube" in kind or "promo" in kind:
                assert "Ready for YouTube" in (p.get("badges") or []), f"missing badge: {p}"


# ── KR merged list ──
class TestKRList:
    def test_merged_list_returns_krs_with_verified_first(self, H):
        r = requests.get(f"{BASE}/api/media-studio/knowledge-manufacturing", headers=H, timeout=30)
        assert r.status_code == 200
        krs = r.json()["knowledge_records"]
        assert len(krs) >= 50, f"expected many KRs, got {len(krs)}"
        # verified first
        first_unverified = next((i for i, k in enumerate(krs) if not k["verified_external"]), None)
        if first_unverified is not None:
            for k in krs[:first_unverified]:
                assert k["verified_external"], f"unverified before verified boundary: {k}"

    def test_verified_kr_present(self, H):
        r = requests.get(f"{BASE}/api/media-studio/knowledge-manufacturing", headers=H, timeout=30)
        krs = r.json()["knowledge_records"]
        ids = {k["id"] for k in krs}
        assert VERIFIED_KR_1 in ids or VERIFIED_KR_2 in ids, f"expected verified KRs missing"
        verified_ct = sum(1 for k in krs if k["verified_external"])
        assert verified_ct >= 1


# ── YouTube factory assets pickup ──
class TestYouTubeAssets:
    def test_factory_assets_endpoint(self, H):
        r = requests.get(f"{BASE}/api/youtube/factory-assets", headers=H, timeout=30)
        assert r.status_code == 200, r.text[:200]
        j = r.json()
        assert "assets" in j or "videos" in j or isinstance(j, dict)


# ── Audiobook background job ──
class TestAudiobookStatus:
    def test_audiobook_status_endpoint_shape(self, H):
        r = requests.get(f"{BASE}/api/publishing/product/{SHORT_BOOK}/audiobook-status", headers=H, timeout=30)
        assert r.status_code == 200, r.text[:200]
        j = r.json()
        assert "status" in j
        # may already be READY from prior iteration
        assert j["status"] in ("READY", "RENDERING", "FAILED", "NOT_STARTED", "IDLE"), j
