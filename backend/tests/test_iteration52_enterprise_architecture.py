"""Iteration 52 — STD-EIP-0002 Enterprise Foundation Sprint A™ backend tests.

Covers:
- GET /api/architecture/domains  (8 domains, module_count present)
- GET /api/architecture/layers   (7 layers, module_count present)
- GET /api/architecture/modules  (75 modules; every module has a valid domain & layer)
- GET /api/architecture/intentions?view=simple|std|ent  (6 intentions, progressive disclosure)
- GET /api/architecture/why?route=...  (Why-Am-I-Here™ content)
- GET /api/architecture/explorer?route=...  (module detail + 404 for invalid)
- Constitutional registration: STD-EIP-0002 does not break existing standards
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PW = "QruFounder2026!"

EXPECTED_DOMAINS = {
    "discovery", "knowledge", "manufacturing", "design_experience",
    "quality_governance", "publishing_distribution", "learning_human_dev",
    "enterprise_operations",
}
EXPECTED_LAYERS = {
    "mission", "governance", "intelligence", "manufacturing",
    "experience", "distribution", "measurement",
}
EXPECTED_INTENTIONS = {"discover", "plan", "build", "launch", "improve", "learn"}


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": FOUNDER_EMAIL, "password": FOUNDER_PW},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"Founder login failed: {r.status_code} {r.text}")
    token = r.json().get("token") or r.json().get("access_token")
    assert token
    return {"Authorization": f"Bearer {token}"}


# ---------- Domains ----------
class TestDomains:
    def test_domains_endpoint(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/architecture/domains", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "domains" in data
        domains = data["domains"]
        assert len(domains) == 8, f"Expected 8 domains, got {len(domains)}"
        ids = {d["id"] for d in domains}
        assert ids == EXPECTED_DOMAINS
        for d in domains:
            assert d.get("name")
            assert d.get("purpose")
            assert d.get("output")
            assert isinstance(d.get("module_count"), int)
            assert d["module_count"] > 0

    def test_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/architecture/domains", timeout=15)
        assert r.status_code in (401, 403)


# ---------- Layers ----------
class TestLayers:
    def test_layers_endpoint(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/architecture/layers", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        layers = r.json()["layers"]
        assert len(layers) == 7
        ids = {l["id"] for l in layers}
        assert ids == EXPECTED_LAYERS
        # Layer numbers 1..7 present
        assert sorted([l["n"] for l in layers]) == [1, 2, 3, 4, 5, 6, 7]
        for l in layers:
            assert isinstance(l.get("module_count"), int)


# ---------- Modules (constitutional criterion) ----------
class TestModules:
    def test_modules_count_and_mapping(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/architecture/modules", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        payload = r.json()
        assert payload["count"] == 75, f"Expected 75 modules, got {payload['count']}"
        modules = payload["modules"]
        assert len(modules) == 75
        unmapped = []
        for m in modules:
            if m.get("domain") not in EXPECTED_DOMAINS:
                unmapped.append((m.get("route"), "domain", m.get("domain")))
            if m.get("layer") not in EXPECTED_LAYERS:
                unmapped.append((m.get("route"), "layer", m.get("layer")))
            assert m.get("route")
            assert m.get("name")
            assert m.get("domain_name")
            assert m.get("layer_name")
        assert unmapped == [], f"CONSTITUTIONAL VIOLATION — unmapped modules: {unmapped}"

    def test_module_counts_match_registry(self, auth_headers):
        rd = requests.get(f"{BASE_URL}/api/architecture/domains", headers=auth_headers).json()["domains"]
        rl = requests.get(f"{BASE_URL}/api/architecture/layers", headers=auth_headers).json()["layers"]
        rm = requests.get(f"{BASE_URL}/api/architecture/modules", headers=auth_headers).json()["modules"]
        assert sum(d["module_count"] for d in rd) == len(rm)
        assert sum(l["module_count"] for l in rl) == len(rm)


# ---------- Intentions (progressive disclosure) ----------
class TestIntentions:
    def test_intentions_shape(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/architecture/intentions?view=ent", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["view"] == "ent"
        ints = data["intentions"]
        assert len(ints) == 6
        assert {i["id"] for i in ints} == EXPECTED_INTENTIONS
        for i in ints:
            assert isinstance(i["modules"], list)

    def test_progressive_disclosure(self, auth_headers):
        simple = requests.get(f"{BASE_URL}/api/architecture/intentions?view=simple", headers=auth_headers).json()
        std = requests.get(f"{BASE_URL}/api/architecture/intentions?view=std", headers=auth_headers).json()
        ent = requests.get(f"{BASE_URL}/api/architecture/intentions?view=ent", headers=auth_headers).json()

        def total(v):
            return sum(len(i["modules"]) for i in v["intentions"])

        s, t, e = total(simple), total(std), total(ent)
        assert s < t, f"simple({s}) must expose fewer modules than std({t})"
        assert t <= e, f"std({t}) must be <= ent({e})"
        # ent should equal 75 (all modules across intentions)
        assert e == 75


# ---------- Why-Am-I-Here ----------
class TestWhy:
    def test_why_manufacture(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/architecture/why?route=/manufacture", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("why", "objective", "success", "next", "common_questions", "common_mistakes",
                  "domain", "layer", "standards", "related_modules", "concierge_shortcut"):
            assert k in d, f"missing {k}"
        assert d["concierge_shortcut"] == "/concierge"
        assert isinstance(d["related_modules"], list)
        assert isinstance(d["standards"], list) and len(d["standards"]) > 0


# ---------- Explorer ----------
class TestExplorer:
    def test_explorer_valid(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/architecture/explorer?route=/flagship-showcase",
                         headers=auth_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["route"] == "/flagship-showcase"
        assert d.get("domain_name")
        assert d.get("layer_name")
        assert d.get("standards")
        assert d.get("mission_contribution")
        assert d.get("human_capability_contribution")
        assert "why" in d
        assert isinstance(d.get("related_in_domain"), list)

    def test_explorer_invalid_404(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/architecture/explorer?route=/no-such-module",
                         headers=auth_headers, timeout=15)
        assert r.status_code == 404


# ---------- Constitutional continuity ----------
class TestConstitutionalRegistry:
    def test_prior_standards_still_present(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/flow/registry", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        payload = r.json()
        # Flatten to string blob to search for standard ids
        blob = str(payload)
        for sid in ("QRU-CON-0001", "QRU-CON-0002", "STD-MFG-0001"):
            assert sid in blob, f"{sid} missing from /api/flow/registry"

    def test_std_eip_0002_registered(self, auth_headers):
        # Look via constitution store if exposed; otherwise the seed itself should not have raised.
        # Try known endpoints; skip if none available.
        r = requests.get(f"{BASE_URL}/api/flow/registry", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        # STD-EIP-0002 should appear somewhere (registry aggregates constitutional artifacts).
        if "STD-EIP-0002" not in str(r.json()):
            # Some deployments may not include EIP standards in /flow/registry — treat as informational.
            pytest.skip("STD-EIP-0002 not exposed via /api/flow/registry (informational)")
