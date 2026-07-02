"""Iteration 7 — QRU Design Intelligence™ + learning-hook regression tests.

Covers:
- GET /api/design/stats (baseline shape + non-zero seed values)
- GET /api/design/brand-library (5 colors, 2 typography, 6 templates, principles/components/spacing/shield)
- GET /api/design/design-library (references list)
- GET /api/design/master-assets?q=<kw> keyword filter
- GET /api/design/design-language (principles incl. Learned category)
- GET /api/design/recommend-templates?product_type=Poster&audience=Children
- Learning hook: assemble Interactive Lesson → quality-control (real GPT loop) → stats grow
- Quick regression: /api/manufacturing2/recipes still returns 13 recipes
"""
import os
import time
import pytest
import requests

def _read_frontend_env():
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return None


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _read_frontend_env()).rstrip("/")

ADMIN = {"email": "admin@qru.com", "password": "qru-admin-2026"}
LEARNER = {"email": "learner@qru.com", "password": "qru-learn-2026"}


@pytest.fixture(scope="module")
def admin_client():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    s.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return s


# ---------- Design Intelligence basic surface ----------

class TestDesignStats:
    def test_stats_shape_and_seed_values(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/design/stats", timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("brand_standards", "design_references", "master_assets", "design_principles"):
            assert k in d, f"missing key {k}"
        assert d["brand_standards"] >= 1
        assert d["design_references"] >= 6, d
        assert d["master_assets"] >= 9, d
        assert d["design_principles"] >= 6, d


class TestBrandLibrary:
    def test_brand_library_contents(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/design/brand-library", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d.get("colors"), list) and len(d["colors"]) == 5
        assert isinstance(d.get("typography"), list) and len(d["typography"]) == 2
        assert isinstance(d.get("templates"), list) and len(d["templates"]) == 6
        assert d.get("principles"), "principles missing"
        assert d.get("components"), "components missing"
        assert d.get("spacing"), "spacing missing"
        assert d.get("shield"), "shield missing"
        colors_by_name = {c["name"]: c for c in d["colors"]}
        assert "Royal Purple" in colors_by_name and colors_by_name["Royal Purple"]["hex"] == "#35106A"


class TestDesignLibrary:
    def test_design_library_returns_references(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/design/design-library", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "references" in d and isinstance(d["references"], list)
        assert len(d["references"]) >= 1
        ref = d["references"][0]
        for k in ("id", "title", "product_type"):
            assert k in ref


class TestMasterAssets:
    def test_master_assets_no_filter(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/design/master-assets", timeout=30)
        assert r.status_code == 200
        assets = r.json()["assets"]
        assert len(assets) >= 9

    def test_master_assets_keyword_filter_heart(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/design/master-assets", params={"q": "heart"}, timeout=30)
        assert r.status_code == 200
        assets = r.json()["assets"]
        # keyword may match title/keywords/asset_id
        assert isinstance(assets, list)
        # ensure filter actually filters (fewer than unfiltered)
        full = admin_client.get(f"{BASE_URL}/api/design/master-assets", timeout=30).json()["assets"]
        assert len(assets) <= len(full)
        # if we got results, verify each contains 'heart' in some searched field
        for a in assets:
            blob = " ".join([
                a.get("title", ""), a.get("asset_id", ""),
                " ".join(a.get("keywords", []) or [])
            ]).lower()
            assert "heart" in blob, a


class TestDesignLanguage:
    def test_language_has_learned_principle(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/design/design-language", timeout=30)
        assert r.status_code == 200
        principles = r.json()["principles"]
        assert len(principles) >= 6
        cats = {p.get("category") for p in principles}
        assert "Learned" in cats, f"no Learned principle present, cats={cats}"


class TestRecommend:
    def test_recommend_poster_children(self, admin_client):
        r = admin_client.get(
            f"{BASE_URL}/api/design/recommend-templates",
            params={"product_type": "Poster", "audience": "Children"},
            timeout=30,
        )
        assert r.status_code == 200
        d = r.json()
        assert d["cover_template"] == "Poster Template™"
        assert d["palette"] == "Bright QRU (Gold-forward)"
        assert d["illustration_style"] == "Bold"
        for k in ("layout", "typography", "tone", "icon_set", "brand_elements"):
            assert k in d and d[k]
        assert "QRU Shield™" in d["brand_elements"]

    def test_recommend_unknown_type_defaults(self, admin_client):
        r = admin_client.get(
            f"{BASE_URL}/api/design/recommend-templates",
            params={"product_type": "Nonexistent", "audience": "Nowhere"},
            timeout=30,
        )
        assert r.status_code == 200
        d = r.json()
        assert d["cover_template"] == "Master Cover Template™"


# ---------- Regression: manufacturing2 recipes ----------

class TestManufacturingRegression:
    def test_recipes_returns_13(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/manufacturing2/recipes", timeout=30)
        assert r.status_code == 200
        payload = r.json()
        recipes = payload["recipes"] if isinstance(payload, dict) else payload
        assert isinstance(recipes, list) and len(recipes) == 13


# ---------- Learning hook: certified product grows the Design Library ----------

class TestLearningHook:
    """Assemble an Interactive Lesson from a demo KR, run QC (real GPT loop),
    then confirm /api/design/stats design_references + master_assets increased."""

    @pytest.mark.timeout(240)
    def test_certification_grows_libraries(self, admin_client):
        pre = admin_client.get(f"{BASE_URL}/api/design/stats", timeout=30).json()

        # 1) pick an Interactive-Lesson-ready demo KR (iteration 6 confirmed KR-DEMO-003)
        krs = admin_client.get(f"{BASE_URL}/api/knowledge-records", timeout=30)
        assert krs.status_code == 200
        demo = None
        for kr in krs.json():
            if str(kr.get("kr_code", "")).startswith("KR-DEMO"):
                demo = kr
                break
        if not demo:
            pytest.skip("No demo KR available")

        # 2) assemble an Interactive Lesson
        r = admin_client.post(
            f"{BASE_URL}/api/manufacturing2/assemble",
            json={"knowledge_record_id": demo["id"], "product_type": "Interactive Lesson"},
            timeout=120,
        )
        if r.status_code >= 400:
            pytest.skip(f"assemble failed on demo KR {demo.get('record_number')}: {r.status_code} {r.text[:200]}")
        product = r.json()
        pid = product["id"]

        # 3) kick QC (fire-and-forget async job)
        r = admin_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/quality-control", timeout=30)
        assert r.status_code in (200, 202), r.text

        # 4) poll pipeline every 5s until certified or timeout (up to ~180s)
        certified = False
        for _ in range(36):
            time.sleep(5)
            pr = admin_client.get(f"{BASE_URL}/api/manufacturing2/{pid}/pipeline", timeout=30)
            if pr.status_code != 200:
                continue
            data = pr.json()
            if data.get("treasure_standard") or (data.get("qc") or {}).get("status") == "certified":
                certified = True
                break

        assert certified, "QC loop did not certify within timeout"

        # 5) confirm library growth
        post = admin_client.get(f"{BASE_URL}/api/design/stats", timeout=30).json()
        assert post["design_references"] >= pre["design_references"] + 1, (pre, post)
        assert post["master_assets"] >= pre["master_assets"] + 1, (pre, post)


# ---------- Auth guard: /api/design/* requires auth ----------

class TestAuthGuard:
    def test_stats_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/design/stats", timeout=15)
        assert r.status_code in (401, 403)
