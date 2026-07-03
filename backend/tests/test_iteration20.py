"""Iteration 20 — Forex Seeds, MT-031 Promotion, MT-033 Marketing Kit, MT-034 Failure Intel,
and Product Manufacturing Recipe™ catalog.

Backend-only tests hitting the public REACT_APP_BACKEND_URL. Uses Founder credentials from
/app/memory/test_credentials.md.
"""
import os
import pytest
import requests

_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not _URL:
    # read from frontend/.env
    try:
        with open("/app/frontend/.env") as _f:
            for _line in _f:
                if _line.startswith("REACT_APP_BACKEND_URL="):
                    _URL = _line.split("=", 1)[1].strip()
                    break
    except Exception:
        pass
BASE_URL = (_URL or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL missing"
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

EXPECTED_FOREX_TITLES = [
    "What Is Forex?",
    "What Is Money?",
    "What Is Currency?",
    "What Is a Currency Pair?",
    "What Is a Base Currency?",
    "What Is a Quote Currency?",
    "What Is an Exchange Rate?",
    "Why Do Exchange Rates Change?",
    "What Is a Pip?",
    "What Is the Spread?",
]

# ------- fixtures ---------------------------------------------------------- #

@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={
        "email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD
    }, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("access_token") or r.json().get("token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


# ------- P1: Forex Seeds --------------------------------------------------- #

class TestForexSeeds:
    def test_seeds_list_contains_10_forex(self, session):
        r = session.get(f"{BASE_URL}/api/promotion/seeds", timeout=30)
        assert r.status_code == 200
        seeds = r.json()
        assert isinstance(seeds, list)
        forex = [s for s in seeds if s.get("kr_code", "").startswith("KR-FX-")]
        assert len(forex) == 10, f"Expected 10 Forex seeds, got {len(forex)}"
        forex_sorted = sorted(forex, key=lambda x: x["kr_code"])
        codes = [s["kr_code"] for s in forex_sorted]
        assert codes == [f"KR-FX-{i:04d}" for i in range(1, 11)]
        titles = [s["title"] for s in forex_sorted]
        assert titles == EXPECTED_FOREX_TITLES, f"Titles mismatch: {titles}"

    def test_forex_seed_fields(self, session):
        r = session.get(f"{BASE_URL}/api/promotion/seeds", timeout=30)
        assert r.status_code == 200
        for seed in r.json():
            if not seed.get("kr_code", "").startswith("KR-FX-"):
                continue
            assert seed["record_class"] == "Topic Seed", seed["kr_code"]
            assert seed["approval_status"] == "Founder Approved", seed["kr_code"]
            assert seed["readiness"] == "Topic Seed — Not Ready for Manufacturing", seed["kr_code"]
            assert seed["treasure_standard_status"] == "Pending", seed["kr_code"]
            assert seed["ai_content"] == "None", seed["kr_code"]
            # Content must be empty (no fabricated definitions)
            for k in ("verified_truth", "simple_answer", "why_it_matters",
                      "the_question", "everyday_analogy", "memory_sentence"):
                assert not (seed.get(k) or "").strip(), \
                    f"{seed['kr_code']} has non-empty {k}: {seed.get(k)!r}"


# ------- P2: Promotion Pipeline (MT-031) ---------------------------------- #

class TestPromotionPipeline:
    def test_schema(self, session):
        r = session.get(f"{BASE_URL}/api/promotion/schema", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "required" in data
        required = data["required"]
        for k in ("the_question", "simple_answer", "why_it_matters", "verified_truth"):
            assert k in required, f"Missing required field: {k}"
        assert "fields" in data
        assert isinstance(data["fields"], list) and len(data["fields"]) > 0

    def _get_seed(self, session, code):
        r = session.get(f"{BASE_URL}/api/promotion/seeds", timeout=30)
        assert r.status_code == 200
        for s in r.json():
            if s.get("kr_code") == code:
                return s
        pytest.fail(f"{code} not found")

    def test_promote_empty_returns_400(self, session):
        # KR-FX-0001 is untouched (fields empty) — promoting with no fields should 400
        seed = self._get_seed(session, "KR-FX-0001")
        r = session.post(f"{BASE_URL}/api/promotion/{seed['id']}/promote",
                         json={"source_note": "Founder manuscript p.1"}, timeout=30)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text[:200]}"
        assert "missing" in r.text.lower() or "required" in r.text.lower()

    def test_save_fields_no_ai(self, session):
        # Use KR-FX-0002 for save-draft testing (do not promote)
        seed = self._get_seed(session, "KR-FX-0002")
        payload = {
            "the_question": "TEST_Q What is money?",
            "simple_answer": "TEST_A A shared unit of value.",
            "why_it_matters": "TEST_W You need it to trade.",
            "verified_truth": "TEST_V Money is a social agreement.",
        }
        r = session.put(f"{BASE_URL}/api/promotion/{seed['id']}/fields",
                        json=payload, timeout=30)
        assert r.status_code == 200, r.text[:300]
        updated = r.json()
        for k, v in payload.items():
            assert updated.get(k) == v, f"{k} not saved"
        # readiness should still be Topic Seed until promoted
        assert updated["record_class"] == "Topic Seed"
        # cleanup: clear back to empty so the seed is preserved
        clear = {k: "" for k in payload}
        session.put(f"{BASE_URL}/api/promotion/{seed['id']}/fields", json=clear, timeout=30)

    def test_promote_missing_source_note_400(self, session):
        # Fill KR-FX-0010 fields first, then attempt promote with empty source_note
        seed = self._get_seed(session, "KR-FX-0010")
        payload = {
            "the_question": "What is the spread?",
            "simple_answer": "The difference between bid and ask price.",
            "why_it_matters": "It's the cost of entering a trade.",
            "verified_truth": "Spread = ask - bid.",
        }
        session.put(f"{BASE_URL}/api/promotion/{seed['id']}/fields", json=payload, timeout=30)
        r = session.post(f"{BASE_URL}/api/promotion/{seed['id']}/promote",
                         json={"source_note": "   "}, timeout=30)
        assert r.status_code == 400
        assert "source note" in r.text.lower() or "provenance" in r.text.lower()

    def test_full_promote_kr_fx_0010(self, session):
        # Full promotion path — KR-FX-0010 gets promoted (per review request)
        seed = self._get_seed(session, "KR-FX-0010")
        # ensure fields still present (previous test set them)
        payload = {
            "the_question": "What is the spread?",
            "simple_answer": "The difference between bid and ask price.",
            "why_it_matters": "It's the cost of entering a trade.",
            "verified_truth": "Spread = ask - bid.",
        }
        session.put(f"{BASE_URL}/api/promotion/{seed['id']}/fields", json=payload, timeout=30)
        r = session.post(f"{BASE_URL}/api/promotion/{seed['id']}/promote",
                         json={"source_note": "Founder manuscript QFC-001 pp.14-15",
                               "source_document": "QFC-001_Master_Manuscript_v0.5.docx"},
                         timeout=30)
        assert r.status_code == 200, r.text[:400]
        promoted = r.json()
        assert promoted["record_class"] == "Imported Verified"
        assert promoted["verification_status"] == "Verified"
        assert promoted["readiness"] == "Ready for Manufacturing"
        # GET to verify persistence
        g = session.get(f"{BASE_URL}/api/promotion/{seed['id']}", timeout=30)
        assert g.status_code == 200
        got = g.json()
        assert got["record_class"] == "Imported Verified"
        assert got["verification_status"] == "Verified"


# ------- Recipes Catalog --------------------------------------------------- #

class TestRecipes:
    def test_23_recipes_with_categories(self, session):
        r = session.get(f"{BASE_URL}/api/rendering/recipes", timeout=30)
        assert r.status_code == 200
        data = r.json()
        recipes = data.get("recipes", [])
        assert len(recipes) == 23, f"Expected 23 recipes, got {len(recipes)}"
        cats = {r["category"] for r in recipes}
        expected_cats = {"book", "poster", "workbook", "deck", "quiz",
                         "script", "card", "guide", "lesson", "certificate"}
        missing = expected_cats - cats
        assert not missing, f"Missing categories: {missing}"
        for rc in recipes:
            for k in ("product_type", "category", "primary_format"):
                assert rc.get(k), f"Recipe missing {k}: {rc}"


# ------- MT-033: Marketing Kit --------------------------------------------- #

class TestMarketingKit:
    @pytest.fixture(scope="class")
    def product_id(self, session):
        r = session.get(f"{BASE_URL}/api/products?limit=100", timeout=60)
        assert r.status_code == 200, r.text[:200]
        prods = r.json()
        if isinstance(prods, dict):
            prods = prods.get("items") or prods.get("products") or []
        assert prods, "No products found to test marketing kit"
        # Prefer a Published product
        pub = [p for p in prods if p.get("status") == "Published"]
        chosen = pub[0] if pub else prods[0]
        return chosen["id"]

    def test_build_kit(self, session, product_id):
        r = session.post(f"{BASE_URL}/api/marketing/{product_id}/build", timeout=180)
        assert r.status_code == 200, f"Build failed: {r.status_code} {r.text[:400]}"
        kit = r.json()
        # Editions
        assert "founder_master_edition" in kit
        assert "customer_edition" in kit
        assert "files" in kit["customer_edition"]
        assert "preview_edition" in kit
        pe = kit["preview_edition"]
        assert "files" in pe
        # sections_locked should be present and > 0 typically
        assert "sections_locked" in pe
        # store_images >= 5
        assert isinstance(kit.get("store_images"), list) and len(kit["store_images"]) >= 5
        # social_kit — 7 platforms
        platforms = {s["platform"] for s in kit.get("social_kit", [])}
        for p in ["Facebook", "Instagram", "Pinterest", "LinkedIn", "X", "TikTok", "YouTube"]:
            assert p in platforms, f"Missing social platform {p}"
        # graphics + flyer + thumbnail
        assert isinstance(kit.get("marketing_graphics"), list) and len(kit["marketing_graphics"]) > 0
        assert kit.get("product_flyer", {}).get("url")
        assert kit.get("product_thumbnail", {}).get("url")

    def test_get_kit(self, session, product_id):
        r = session.get(f"{BASE_URL}/api/marketing/{product_id}", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("ready") is True
        assert data.get("marketing_kit") is not None

    def test_preview_config_update(self, session, product_id):
        r = session.put(f"{BASE_URL}/api/marketing/{product_id}/preview-config",
                        json={"include_percentage": 45}, timeout=30)
        assert r.status_code == 200
        cfg = r.json().get("preview_config", {})
        assert cfg.get("include_percentage") == 45
        # revert
        session.put(f"{BASE_URL}/api/marketing/{product_id}/preview-config",
                    json={"include_percentage": 30}, timeout=30)


# ------- MT-034: Failure Intelligence ------------------------------------- #

class TestFailureIntelligence:
    def test_dashboard_structure(self, session):
        r = session.get(f"{BASE_URL}/api/failure-intelligence/dashboard", timeout=60)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert "dashboard" in data
        d = data["dashboard"]
        for k in ("total_runs", "successful", "failed", "in_progress", "paused",
                  "waiting_on_founder", "waiting_on_assets", "waiting_on_knowledge",
                  "waiting_on_ai", "waiting_on_external"):
            assert k in d, f"Missing dashboard key: {k}"
        assert "runs" in data
        assert "failure_classes" in data
        assert isinstance(data["failure_classes"], dict) and len(data["failure_classes"]) > 0
        # inspect failing runs shape
        for run in data["runs"]:
            if run.get("failures"):
                f = run["failures"][0]
                for k in ("root_cause", "explanation", "resolution", "action"):
                    assert k in f, f"failure missing {k}"
                act = f["action"]
                for k in ("label", "route", "testid"):
                    assert k in act, f"action missing {k}"
                break

    def test_retry_orchestrator_run(self, session):
        r = session.get(f"{BASE_URL}/api/failure-intelligence/dashboard", timeout=60)
        assert r.status_code == 200
        runs = r.json().get("runs", [])
        target = None
        for run in runs:
            if run.get("source") == "Orchestrator" and run.get("retryable"):
                target = run
                break
        if not target:
            pytest.skip("No retryable Orchestrator batch present")
        rr = session.post(f"{BASE_URL}/api/failure-intelligence/run/{target['run_id']}/retry", timeout=60)
        assert rr.status_code == 200, rr.text[:300]
        out = rr.json()
        assert out.get("ok") is True, f"Retry not ok: {out}"
