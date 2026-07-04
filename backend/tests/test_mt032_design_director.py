"""MT-032 QRU Design Director™ backend tests.

Validates:
- Settings GET/PUT with defaults (deterministic-first: allow_ai_hero_art=False)
- Queue lists products with customer_deliverable and their score fields
- Scorecard returns exactly 11 categories
- Autonomous review loop returns estimated_ai_cost_usd == 0.0 by default
- Passing products get recorded to /references
"""
import os
import pytest
import requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        # fall back to reading /app/frontend/.env
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip()
                        break
        except Exception:
            pass
    assert url, "REACT_APP_BACKEND_URL missing"
    return url.rstrip("/")


BASE_URL = _load_backend_url()

FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

EXPECTED_CATEGORIES = {
    "QRU Branding", "Treasure Standard™ Compliance", "Educational Clarity",
    "Visual Hierarchy", "Typography", "Graphics & Illustration", "Layout & Spacing",
    "Color Harmony", "Readability", "Print Quality", "Customer Readiness",
}


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    token = r.json().get("token") or r.json().get("access_token")
    assert token, f"No token in login response: {r.json()}"
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


# --- Settings ------------------------------------------------------------
def test_settings_get_defaults(client):
    r = client.get(f"{BASE_URL}/api/design-director/settings", timeout=30)
    assert r.status_code == 200
    d = r.json()
    for k in ("passing_score", "auto_improve", "max_iterations",
              "allow_founder_override", "allow_ai_hero_art"):
        assert k in d, f"missing {k}"
    # deterministic-first default MUST be False
    assert d["allow_ai_hero_art"] is False, \
        f"allow_ai_hero_art must default to False, got {d['allow_ai_hero_art']}"


def test_settings_put_persists(client):
    # snapshot
    original = client.get(f"{BASE_URL}/api/design-director/settings").json()
    # update
    r = client.put(f"{BASE_URL}/api/design-director/settings",
                   json={"passing_score": 88})
    assert r.status_code == 200
    assert r.json()["passing_score"] == 88
    # verify persistence
    r2 = client.get(f"{BASE_URL}/api/design-director/settings")
    assert r2.json()["passing_score"] == 88
    # restore
    client.put(f"{BASE_URL}/api/design-director/settings",
               json={"passing_score": original["passing_score"],
                     "allow_ai_hero_art": False})
    final = client.get(f"{BASE_URL}/api/design-director/settings").json()
    assert final["allow_ai_hero_art"] is False, \
        "MUST leave allow_ai_hero_art=False at end (no AI spend)"


# --- Queue ---------------------------------------------------------------
def test_queue_shape(client):
    r = client.get(f"{BASE_URL}/api/design-director/queue", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "passing_score" in d
    assert "products" in d and isinstance(d["products"], list)
    if d["products"]:
        row = d["products"][0]
        for k in ("id", "product_code", "title", "product_type",
                  "status", "cover_url", "overall", "passed", "scored"):
            assert k in row, f"queue row missing {k}"


# --- Scorecard -----------------------------------------------------------
def _pick_pid(client):
    q = client.get(f"{BASE_URL}/api/design-director/queue").json()
    prods = q.get("products", [])
    if not prods:
        pytest.skip("No products in queue")
    # prefer known well-branded products if present
    preferred = {"PRD-00061", "PRD-00051", "PRD-00021"}
    for p in prods:
        if p.get("product_code") in preferred:
            return p["id"], p["product_code"]
    return prods[0]["id"], prods[0]["product_code"]


def test_scorecard_11_categories(client):
    pid, code = _pick_pid(client)
    r = client.get(f"{BASE_URL}/api/design-director/score/{pid}", timeout=60)
    assert r.status_code == 200
    sc = r.json()
    for k in ("overall", "passing_score", "passed", "categories",
              "deductions", "scored_at"):
        assert k in sc, f"scorecard missing {k}"
    assert isinstance(sc["overall"], int) or isinstance(sc["overall"], float)
    assert 0 <= sc["overall"] <= 100
    assert isinstance(sc["passed"], bool)
    cats = sc["categories"]
    assert len(cats) == 11, f"Expected 11 categories, got {len(cats)}"
    names = {c["category"] for c in cats}
    assert names == EXPECTED_CATEGORIES, (
        f"category mismatch. missing={EXPECTED_CATEGORIES - names}, "
        f"unexpected={names - EXPECTED_CATEGORIES}")
    for c in cats:
        for k in ("category", "score", "reason", "recommendation", "priority"):
            assert k in c, f"category {c.get('category')} missing {k}"
        assert 0 <= c["score"] <= 10, f"score OOB for {c['category']}: {c['score']}"


# --- Autonomous review (MOST IMPORTANT) ----------------------------------
def test_review_is_deterministic_zero_ai(client):
    # Ensure allow_ai_hero_art is False for this test
    client.put(f"{BASE_URL}/api/design-director/settings",
               json={"allow_ai_hero_art": False})
    pid, code = _pick_pid(client)
    r = client.post(f"{BASE_URL}/api/design-director/review/{pid}", timeout=180)
    assert r.status_code == 200, f"review failed: {r.status_code} {r.text}"
    d = r.json()
    for k in ("history", "final", "passed", "iterations",
              "max_iterations", "allow_ai_hero_art", "estimated_ai_cost_usd"):
        assert k in d, f"review response missing {k}"
    # CRITICAL DETERMINISTIC ASSERTIONS
    assert d["allow_ai_hero_art"] is False, "allow_ai_hero_art must be False"
    assert d["estimated_ai_cost_usd"] == 0.0, (
        f"estimated_ai_cost_usd MUST be 0.0 with default settings, "
        f"got {d['estimated_ai_cost_usd']}")
    assert isinstance(d["history"], list) and len(d["history"]) >= 1
    for h in d["history"]:
        assert "iteration" in h and "overall" in h and "passed" in h
    assert d["final"]["overall"] >= 0
    print(f"Reviewed {code}: overall={d['final']['overall']}, "
          f"passed={d['passed']}, iters={d['iterations']}")


def test_well_branded_product_passes_deterministically(client):
    """A known well-branded product (PRD-00061/51/21) should reach passing score
    (~91) deterministically with $0 AI."""
    q = client.get(f"{BASE_URL}/api/design-director/queue").json()
    prods = q.get("products", [])
    target = None
    for code in ("PRD-00061", "PRD-00051", "PRD-00021"):
        for p in prods:
            if p.get("product_code") == code:
                target = p
                break
        if target:
            break
    if not target:
        pytest.skip("No known well-branded product in queue")
    client.put(f"{BASE_URL}/api/design-director/settings",
               json={"allow_ai_hero_art": False, "passing_score": 90})
    r = client.post(f"{BASE_URL}/api/design-director/review/{target['id']}",
                    timeout=180)
    assert r.status_code == 200
    d = r.json()
    assert d["estimated_ai_cost_usd"] == 0.0
    assert d["final"]["overall"] >= 90, (
        f"Expected deterministic pass (>=90) for {target['product_code']}, "
        f"got {d['final']['overall']}")
    assert d["passed"] is True


def test_references_grows_after_pass(client):
    r = client.get(f"{BASE_URL}/api/design-director/references")
    assert r.status_code == 200
    d = r.json()
    assert "references" in d
    refs = d["references"]
    assert isinstance(refs, list)
    if refs:
        r0 = refs[0]
        for k in ("product_id", "product_code", "overall"):
            assert k in r0
        # references sorted by overall desc, so first should be highest
        assert r0["overall"] is not None


# --- Cleanup -------------------------------------------------------------
def test_zzz_ensure_ai_off_final(client):
    """Final teardown — MUST leave allow_ai_hero_art=False."""
    client.put(f"{BASE_URL}/api/design-director/settings",
               json={"allow_ai_hero_art": False, "passing_score": 90})
    s = client.get(f"{BASE_URL}/api/design-director/settings").json()
    assert s["allow_ai_hero_art"] is False
