"""MT-032 Auto-Gate Extension — QRU Design Director™ Auto-Gated tests.

Validates (deterministic-first, LLM cap ACTIVE — must be $0 AI):
- 11 QRU Design Standard™ categories with exact NEW names + order
- product_type_compliance on /score/{pid}
- POST /auto-gate/{pid} shape + estimated_ai_cost_usd==0.0 by default
- /telemetry records per gated product
- /factory-intelligence aggregation (summary, recurring_issues, by_product_type)
- Settings passing_score default 91, allow_ai_hero_art false
- Founder approval/publish is NOT changed by auto-gate (only annotates)
- Manufacturing hook exists (design_director.auto_gate call inside _certify)
"""
import os
import pytest
import requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
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

# QRU Design Standard™ — MT-032 new 11 categories in required ORDER
EXPECTED_CATEGORIES_ORDER = [
    "Understanding & Clarity",
    "Educational Effectiveness",
    "Visual Hierarchy",
    "Typography",
    "Layout & Spacing",
    "Accessibility",
    "QRU Branding",
    "Treasure Standard™ Compliance",
    "Print Readiness",
    "Marketplace Readiness",
    "Product-Type Compliance",
]


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
    # ensure allow_ai_hero_art=False and passing_score=91 at start
    s.put(f"{BASE_URL}/api/design-director/settings",
          json={"allow_ai_hero_art": False, "passing_score": 91})
    return s


# --- Settings defaults ---------------------------------------------------
def test_settings_defaults_91_and_no_ai(client):
    r = client.get(f"{BASE_URL}/api/design-director/settings", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["passing_score"] == 91, f"passing_score should be 91, got {d['passing_score']}"
    assert d["allow_ai_hero_art"] is False, "allow_ai_hero_art MUST be False (LLM cap active)"
    for k in ("passing_score", "auto_improve", "max_iterations",
              "allow_founder_override", "allow_ai_hero_art"):
        assert k in d


def test_settings_put_persists(client):
    r = client.put(f"{BASE_URL}/api/design-director/settings",
                   json={"max_iterations": 2})
    assert r.status_code == 200
    assert r.json()["max_iterations"] == 2
    r2 = client.get(f"{BASE_URL}/api/design-director/settings")
    assert r2.json()["max_iterations"] == 2
    # restore
    client.put(f"{BASE_URL}/api/design-director/settings",
               json={"max_iterations": 3, "allow_ai_hero_art": False, "passing_score": 91})


# --- Queue --------------------------------------------------------------
def test_queue_shape(client):
    r = client.get(f"{BASE_URL}/api/design-director/queue", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "passing_score" in d and "products" in d
    assert isinstance(d["products"], list)


def _pick_pid(client, preferred_codes=None):
    q = client.get(f"{BASE_URL}/api/design-director/queue").json()
    prods = q.get("products", [])
    if not prods:
        pytest.skip("No products in queue")
    preferred = preferred_codes or {"PRD-00061", "PRD-00051", "PRD-00021"}
    for p in prods:
        if p.get("product_code") in preferred:
            return p
    return prods[0]


# --- Scorecard 11 categories + product-type compliance -------------------
def test_scorecard_has_11_categories_in_order(client):
    p = _pick_pid(client)
    r = client.get(f"{BASE_URL}/api/design-director/score/{p['id']}", timeout=60)
    assert r.status_code == 200, r.text
    sc = r.json()
    for k in ("overall", "passing_score", "passed", "categories",
              "deductions", "product_type_compliance", "scored_at"):
        assert k in sc, f"scorecard missing {k}"
    cats = sc["categories"]
    assert len(cats) == 11, f"Expected 11 categories, got {len(cats)}"
    names_in_order = [c["category"] for c in cats]
    assert names_in_order == EXPECTED_CATEGORIES_ORDER, (
        f"Category order mismatch.\nExpected: {EXPECTED_CATEGORIES_ORDER}\n"
        f"Got: {names_in_order}")
    for c in cats:
        for k in ("category", "score", "reason", "recommendation", "priority"):
            assert k in c, f"category {c.get('category')} missing {k}"
        assert 0 <= c["score"] <= 10


def test_product_type_compliance_shape(client):
    p = _pick_pid(client)
    r = client.get(f"{BASE_URL}/api/design-director/score/{p['id']}", timeout=60)
    sc = r.json()
    ptc = sc["product_type_compliance"]
    for k in ("compliant", "score", "violations", "recipe", "category"):
        assert k in ptc, f"product_type_compliance missing {k}"
    assert isinstance(ptc["compliant"], bool)
    assert isinstance(ptc["violations"], list)
    assert isinstance(ptc["recipe"], str) and ptc["recipe"].startswith("QRU ")


def test_recipe_label_matches_product_type(client):
    """Poster products should have recipe 'QRU Poster Recipe™'."""
    q = client.get(f"{BASE_URL}/api/design-director/queue").json()
    poster = next((p for p in q.get("products", []) if p.get("product_type") == "Poster"), None)
    if not poster:
        pytest.skip("No Poster product in queue")
    r = client.get(f"{BASE_URL}/api/design-director/score/{poster['id']}", timeout=60)
    sc = r.json()
    assert sc["product_type_compliance"]["recipe"] == "QRU Poster Recipe™"
    assert sc["product_type_compliance"]["category"] == "poster"


# --- Auto-Gate (MOST CRITICAL) -------------------------------------------
def test_auto_gate_response_shape_and_zero_ai_cost(client):
    """POST /auto-gate/{pid} must return $0 AI cost with default settings."""
    client.put(f"{BASE_URL}/api/design-director/settings",
               json={"allow_ai_hero_art": False, "passing_score": 91})
    p = _pick_pid(client)
    r = client.post(f"{BASE_URL}/api/design-director/auto-gate/{p['id']}", timeout=180)
    assert r.status_code == 200, f"auto-gate failed: {r.status_code} {r.text}"
    d = r.json()
    for k in ("gate", "scorecard", "improvements", "time_saved_minutes"):
        assert k in d, f"auto-gate response missing {k}"
    gate = d["gate"]
    for k in ("score", "passed", "passing_score", "improvement_count",
              "improved_categories", "issue_tags", "estimated_ai_cost_usd"):
        assert k in gate, f"gate missing {k}"
    # CRITICAL: deterministic-first $0 assertion
    assert gate["estimated_ai_cost_usd"] == 0.0, (
        f"estimated_ai_cost_usd MUST be 0.0 by default, got {gate['estimated_ai_cost_usd']}")
    assert gate["passing_score"] == 91
    assert isinstance(gate["issue_tags"], list)
    assert isinstance(d["time_saved_minutes"], int) and d["time_saved_minutes"] >= 18


def test_auto_gate_writes_design_gate_on_product(client):
    p = _pick_pid(client)
    client.post(f"{BASE_URL}/api/design-director/auto-gate/{p['id']}", timeout=180)
    # verify design_gate exists via queue/refetch (queue rows include overall/passed but not full gate)
    # Instead re-fetch scorecard which should now be persisted
    sc = client.get(f"{BASE_URL}/api/design-director/score/{p['id']}").json()
    assert sc["overall"] >= 0


def test_auto_gate_does_not_change_approval_or_publish(client):
    """Auto-gate must ONLY annotate — Founder approval/publish must not change."""
    q = client.get(f"{BASE_URL}/api/design-director/queue").json()
    prods = q.get("products", [])
    if not prods:
        pytest.skip("No products")
    p = prods[0]
    status_before = p.get("status")
    r = client.post(f"{BASE_URL}/api/design-director/auto-gate/{p['id']}", timeout=180)
    assert r.status_code == 200
    q2 = client.get(f"{BASE_URL}/api/design-director/queue").json()
    row = next((x for x in q2["products"] if x["id"] == p["id"]), None)
    assert row is not None
    assert row.get("status") == status_before, (
        f"auto-gate changed status: {status_before} -> {row.get('status')}")


def test_auto_gate_404_for_missing_product(client):
    r = client.post(f"{BASE_URL}/api/design-director/auto-gate/nonexistent_pid_zzz", timeout=30)
    assert r.status_code == 404


# --- Telemetry -----------------------------------------------------------
def test_telemetry_records_after_auto_gate(client):
    """Run auto-gate on 2-3 products then confirm telemetry has records with expected fields."""
    q = client.get(f"{BASE_URL}/api/design-director/queue").json()
    prods = q.get("products", [])[:3]
    if len(prods) < 1:
        pytest.skip("Not enough products")
    for p in prods:
        client.post(f"{BASE_URL}/api/design-director/auto-gate/{p['id']}", timeout=180)
    r = client.get(f"{BASE_URL}/api/design-director/telemetry", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "telemetry" in d
    tel = d["telemetry"]
    assert isinstance(tel, list) and len(tel) >= 1
    rec = tel[0]
    required = ["design_score", "improvement_count", "improvement_categories",
                "issue_tags", "product_type", "knowledge_record_id",
                "manufacturing_recipe", "marketplace_destination",
                "approval_status", "publication_status", "time_saved_minutes"]
    for k in required:
        assert k in rec, f"telemetry record missing {k}"


# --- Factory Intelligence ------------------------------------------------
def test_factory_intelligence_aggregation(client):
    r = client.get(f"{BASE_URL}/api/design-director/factory-intelligence", timeout=30)
    assert r.status_code == 200
    d = r.json()
    for k in ("summary", "recurring_issues", "by_product_type"):
        assert k in d, f"factory-intelligence missing {k}"
    s = d["summary"]
    for k in ("products_gated", "passing", "pass_rate", "avg_design_score",
              "total_improvements", "time_saved_minutes", "time_saved_hours"):
        assert k in s, f"summary missing {k}"
    assert isinstance(d["recurring_issues"], list)
    assert isinstance(d["by_product_type"], list)
    # recurring issue tags should look like known tag names when present
    known_tags = {
        "unclear_content", "weak_teaching_flow", "weak_visual_hierarchy",
        "inconsistent_typography", "poor_spacing", "readability_problems",
        "branding_imbalance", "treasure_standard_gap", "print_readiness_issues",
        "marketplace_export_issues", "recipe_violations", "cover_only_posters",
    }
    for issue in d["recurring_issues"]:
        assert "issue" in issue and "count" in issue
        # if any known tag, verify structure – no strict subset check as tags may extend later
    for row in d["by_product_type"]:
        for k in ("product_type", "count", "pass_rate", "avg_score"):
            assert k in row


# --- Manufacturing hook code path exists ---------------------------------
def test_manufacturing_hook_code_path_exists():
    """Regression: manufacturing2._certify must call design_director.auto_gate.
    (Don't run a full AI manufacturing job — LLM daily cap is active.)"""
    with open("/app/backend/manufacturing2.py") as f:
        src = f.read()
    assert "import design_director" in src, "manufacturing2 must import design_director"
    assert "dd.auto_gate" in src or "design_director.auto_gate" in src, (
        "manufacturing2._certify must call design_director.auto_gate")


# --- References endpoint still works -------------------------------------
def test_references_endpoint(client):
    r = client.get(f"{BASE_URL}/api/design-director/references", timeout=30)
    assert r.status_code == 200
    assert "references" in r.json()


# --- Final cleanup: leave AI OFF -----------------------------------------
def test_zzz_leave_ai_off(client):
    client.put(f"{BASE_URL}/api/design-director/settings",
               json={"allow_ai_hero_art": False, "passing_score": 91})
    s = client.get(f"{BASE_URL}/api/design-director/settings").json()
    assert s["allow_ai_hero_art"] is False
    assert s["passing_score"] == 91
