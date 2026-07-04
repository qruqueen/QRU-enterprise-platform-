"""Iteration 24 — Autonomy Initiative (AO-001, AO-002, MO-038, MO-039) backend tests."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://understanding-os.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASS = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASS}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def H(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- Autonomy Engine (AO-001 + MO-038 + MO-039) ----------

def test_overview_shape(H):
    r = requests.get(f"{BASE_URL}/api/autonomy-engine/overview", headers=H, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    m = j.get("metrics", {})
    for k in ["manufacturing_queue", "blocked_items", "founder_decisions_waiting",
              "products_today", "founder_hours_saved", "automation_rate",
              "treasure_pass_rate", "avg_factory_confidence", "system_health"]:
        assert k in m, f"metrics missing {k}"
    for k in ["next_recommended_action", "factory_learning",
              "manufacturing_queue", "awaiting_founder", "blocked"]:
        assert k in j, f"overview missing {k}"


def test_settings_default_and_toggle(H):
    r = requests.get(f"{BASE_URL}/api/autonomy-engine/settings", headers=H, timeout=30)
    assert r.status_code == 200
    s = r.json()
    assert "enabled" in s and "max_per_cycle" in s and "publish_threshold" in s
    assert s["publish_threshold"] == 91

    # Toggle ON
    r = requests.put(f"{BASE_URL}/api/autonomy-engine/settings",
                     headers=H, json={"enabled": True}, timeout=30)
    assert r.status_code == 200
    assert r.json()["enabled"] is True

    # Confirm persisted
    r = requests.get(f"{BASE_URL}/api/autonomy-engine/settings", headers=H, timeout=30)
    assert r.json()["enabled"] is True

    # Toggle OFF
    r = requests.put(f"{BASE_URL}/api/autonomy-engine/settings",
                     headers=H, json={"enabled": False}, timeout=30)
    assert r.status_code == 200
    assert r.json()["enabled"] is False


def test_priority_queue(H):
    r = requests.get(f"{BASE_URL}/api/autonomy-engine/priority-queue", headers=H, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    assert "queue" in j and "count" in j
    if j["queue"]:
        row = j["queue"][0]
        for k in ["id", "next_action", "factory_confidence", "data_health"]:
            assert k in row, f"queue row missing {k}"


def test_advance_deterministic_fast(H):
    """POST /advance/{pid} must be deterministic ($0 AI) and fast."""
    r = requests.get(f"{BASE_URL}/api/autonomy-engine/priority-queue", headers=H, timeout=30)
    q = r.json().get("queue", [])
    actionable = next((x for x in q if x.get("actionable") is True), None)
    if not actionable:
        actionable = next((x for x in q if x.get("actionable") is not False), None)
    if not actionable:
        pytest.skip("No actionable products in queue")
    pid = actionable["id"]
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/api/autonomy-engine/advance/{pid}",
                      headers=H, timeout=15)
    dt = time.time() - t0
    assert r.status_code == 200, r.text
    j = r.json()
    for k in ["actions", "factory_confidence", "data_health", "next_action"]:
        assert k in j, f"advance response missing {k}"
    assert dt < 10, f"advance too slow ({dt:.1f}s) — possible LLM call"


def test_run_cycle_fire_and_forget(H):
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/api/autonomy-engine/run-cycle", headers=H, timeout=15)
    dt = time.time() - t0
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("ran") is True and j.get("queued") is True
    assert dt < 5, f"run-cycle should return immediately, took {dt:.1f}s"
    # follow-up overview must respond quickly
    r2 = requests.get(f"{BASE_URL}/api/autonomy-engine/overview", headers=H, timeout=15)
    assert r2.status_code == 200


# ---------- MO-038 Publish Gate (Founder Inbox) ----------

def test_founder_inbox_has_health_and_gate(H):
    r = requests.get(f"{BASE_URL}/api/founder-inbox", headers=H, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    items = (j.get("items") or j.get("products")) if isinstance(j, dict) else j
    assert isinstance(items, list) and len(items) > 0, "Inbox empty"
    row = items[0]
    for k in ["data_health", "data_health_label", "data_health_emoji",
              "factory_confidence", "confidence_band", "publishable", "publish_blockers"]:
        assert k in row, f"inbox row missing {k}"


def test_publish_gate_unbypassable(H):
    r = requests.get(f"{BASE_URL}/api/founder-inbox", headers=H, timeout=30)
    j = r.json()
    items = (j.get("items") or j.get("products")) if isinstance(j, dict) else j
    non_ready = next((p for p in items if p.get("data_health") != "ready" or p.get("publishable") is False), None)
    if not non_ready:
        pytest.skip("No non-publishable product to test gate")
    pid = non_ready.get("id") or non_ready.get("_id")
    r = requests.post(f"{BASE_URL}/api/founder-inbox/{pid}/action",
                      headers=H, json={"action": "approve"}, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    # must NOT mark as Published
    status = (j.get("status") or j.get("product", {}).get("status") or "").lower()
    assert "published" not in status, f"Gate bypassed! response={j}"
    assert j.get("ok") is True


# ---------- AO-002 Asset Manufacturing ----------

def test_marketplaces(H):
    r = requests.get(f"{BASE_URL}/api/asset-manufacturing/marketplaces", headers=H, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert "marketplaces" in j and "asset_classes" in j
    assert len(j["marketplaces"]) == 12, f"Expected 12 marketplaces, got {len(j['marketplaces'])}"


def _get_vault_asset(H):
    r = requests.get(f"{BASE_URL}/api/vault/assets", headers=H, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assets = j.get("assets") if isinstance(j, dict) else j
    assert assets and len(assets) > 0, "No vault assets"
    return assets[0]


def test_asset_plan(H):
    a = _get_vault_asset(H)
    aid = a.get("id") or a.get("_id")
    r = requests.get(f"{BASE_URL}/api/asset-manufacturing/plan/{aid}", headers=H, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    for k in ["classification", "compatible_products", "recommended_products",
              "compatible_marketplaces", "estimated_minutes", "is_completed_product",
              "hero_handling"]:
        assert k in j, f"plan missing {k}"


def test_manufacture_from_asset(H):
    a = _get_vault_asset(H)
    aid = a.get("id") or a.get("_id")
    plan = requests.get(f"{BASE_URL}/api/asset-manufacturing/plan/{aid}", headers=H, timeout=30).json()
    recommended = plan.get("recommended_products") or plan.get("compatible_products")
    if not recommended:
        pytest.skip("No recommended products for this asset")
    label = recommended[0]
    if isinstance(label, dict):
        label = label.get("label") or label.get("name") or label.get("id")
    r = requests.post(f"{BASE_URL}/api/asset-manufacturing/manufacture/{aid}",
                      headers=H, json={"product_labels": [label]}, timeout=60)
    assert r.status_code == 200, r.text
    j = r.json()
    created = j.get("created", [])
    assert isinstance(created, list) and len(created) >= 1, f"No products created: {j}"
    # NOT auto-published
    for c in created:
        status = (c.get("status") or "").lower()
        assert "published" not in status, f"Auto-publish leak: {c}"
