"""Iteration 12 backend tests — Integration Hub, AI Services Manager, Product Automation Engine,
Meditation Studio, Digital Production Line (FAST PATH), Enterprise Command Center."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://understanding-os.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def founder_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth(founder_token):
    return {"Authorization": f"Bearer {founder_token}"}


# ================= INTEGRATION HUB =================
class TestIntegrationHub:
    def test_catalog(self, auth):
        r = requests.get(f"{BASE_URL}/api/integrations/catalog", headers=auth, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "catalog" in data
        assert "AI Services" in data["catalog"], "AI Services category missing"
        assert any("Gemini" in p for p in data["catalog"]["AI Services"])
        assert isinstance(data.get("oauth_platforms"), list)

    def test_monitor(self, auth):
        r = requests.get(f"{BASE_URL}/api/integrations/monitor", headers=auth, timeout=15)
        assert r.status_code == 200
        data = r.json()
        for k in ["platforms_configured", "platforms_connected", "unhealthy", "categories"]:
            assert k in data

    def test_connections_crud_and_credential_masking(self, auth):
        # Create with credential
        payload = {"platform": "QRU Store", "store_name": "TEST_MaskingStore",
                   "credential": "secret123-super-sensitive"}
        r = requests.post(f"{BASE_URL}/api/integrations/connections",
                          json=payload, headers=auth, timeout=15)
        assert r.status_code == 200, r.text
        conn = r.json()
        assert conn.get("has_credentials") is True
        # CRITICAL: raw credential must never leak
        assert "secret123" not in str(conn)
        assert "credential" not in conn or conn.get("credential") in (None, "")
        assert "secret_enc" not in conn
        cid = conn["id"]

        # List — masked
        r = requests.get(f"{BASE_URL}/api/integrations/connections", headers=auth, timeout=15)
        assert r.status_code == 200
        body = r.text
        assert "secret123" not in body, "credential leaked in list response"
        found = next((c for c in r.json() if c["id"] == cid), None)
        assert found is not None
        assert found.get("has_credentials") is True

        # Test connection
        r = requests.post(f"{BASE_URL}/api/integrations/connections/{cid}/test",
                          headers=auth, timeout=15)
        assert r.status_code == 200
        test_res = r.json()
        assert test_res.get("connection_health") in ("healthy", "needs_auth", "unknown")
        assert "secret123" not in r.text

        # Delete
        r = requests.delete(f"{BASE_URL}/api/integrations/connections/{cid}",
                            headers=auth, timeout=15)
        assert r.status_code == 200

    def test_routing_defaults(self, auth):
        r = requests.get(f"{BASE_URL}/api/integrations/routing", headers=auth, timeout=15)
        assert r.status_code == 200
        rules = r.json().get("rules", {})
        # At least product-type rules present
        assert isinstance(rules, dict) and len(rules) > 5

    def test_unknown_platform_rejected(self, auth):
        r = requests.post(f"{BASE_URL}/api/integrations/connections",
                          json={"platform": "TotallyFakePlatform", "credential": "x"},
                          headers=auth, timeout=15)
        assert r.status_code == 400


# ================= AI SERVICES MANAGER =================
class TestAIServices:
    def test_status_capability_matrix(self, auth):
        r = requests.get(f"{BASE_URL}/api/ai-services/status", headers=auth, timeout=15)
        assert r.status_code == 200
        data = r.json()
        caps = data.get("capabilities", [])
        assert len(caps) >= 14, f"Expected 14+ capabilities got {len(caps)}"
        by_name = {c["capability"]: c for c in caps}
        # Text-based caps should be real
        for cap in ("text", "translation", "caption", "quiz"):
            if cap in by_name:
                assert by_name[cap]["mode"] == "real", f"{cap} should be real"
        # image should be real
        assert by_name["image"]["mode"] == "real"
        # Media caps should be simulated when no connector
        for cap in ("video", "animation", "voice", "music"):
            assert by_name[cap]["mode"] == "simulated", f"{cap} should be simulated w/o connector"
            assert by_name[cap]["requires_connector"] is True

    def test_jobs(self, auth):
        r = requests.get(f"{BASE_URL}/api/ai-services/jobs", headers=auth, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ================= PRODUCT AUTOMATION =================
class TestProductAutomation:
    def test_recipes(self, auth):
        r = requests.get(f"{BASE_URL}/api/automation/recipes", headers=auth, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert len(data["recipes"]) > 20
        types = {r["product_type"] for r in data["recipes"]}
        for t in ("Interactive Lesson", "Guided Meditation", "Positive Affirmations", "Sleep Story"):
            assert t in types, f"Missing recipe {t}"
        assert "Guided Meditation" in data["meditation_content_types"]

    def test_agents(self, auth):
        r = requests.get(f"{BASE_URL}/api/automation/agents", headers=auth, timeout=15)
        assert r.status_code == 200
        agents = r.json()["agents"]
        assert len(agents) >= 15
        names = {a["agent"] for a in agents}
        assert "Script Writer™" in names

    def test_packages(self, auth):
        r = requests.get(f"{BASE_URL}/api/automation/packages", headers=auth, timeout=15)
        assert r.status_code == 200
        packs = r.json()["packages"]
        for p in ("Core Package", "Meditation Package", "Full Package"):
            assert p in packs, f"Missing package {p}"

    def test_meditation_profiles(self, auth):
        r = requests.get(f"{BASE_URL}/api/automation/meditation/profiles", headers=auth, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert len(data["profiles"]) == 10, f"Expected 10 profiles got {len(data['profiles'])}"
        assert "Calm Teacher" in data["profiles"]
        assert "Ocean" in data["frequencies"]


# ================= FAST PATH MANUFACTURE + PRODUCTION LINE =================
def _get_verified_kr(auth):
    r = requests.get(f"{BASE_URL}/api/knowledge-records", headers=auth, timeout=30)
    assert r.status_code == 200
    for kr in r.json():
        if kr.get("verification_status") == "Verified":
            return kr
    pytest.skip("No verified Knowledge Record available for fast-path testing")


class TestManufactureSmall:
    """Single small (1-product) hands-free manufacture end-to-end."""

    def test_manufacture_positive_affirmations(self, auth):
        kr = _get_verified_kr(auth)
        payload = {"product_types": ["Positive Affirmations"],
                   "inspiration_profile": "Calm Teacher", "frequency": "Ocean"}
        r = requests.post(f"{BASE_URL}/api/automation/manufacture/{kr['id']}",
                          json=payload, headers=auth, timeout=30)
        assert r.status_code == 200, r.text
        order = r.json()
        assert order["total"] == 1
        oid = order["id"]

        # Poll (LLM ~10-60s)
        final = None
        for _ in range(60):
            time.sleep(3)
            r = requests.get(f"{BASE_URL}/api/automation/orders/{oid}", headers=auth, timeout=15)
            assert r.status_code == 200
            o = r.json()
            if o["status"] in ("completed", "completed_with_errors", "failed"):
                final = o
                break
        assert final is not None, "manufacture order timed out"
        assert final["status"] == "completed", f"Order not completed: {final}"

        item = final["items"][0]
        assert item["status"] == "done"
        pid = item["product_id"]

        # Verify product
        r = requests.get(f"{BASE_URL}/api/products/{pid}", headers=auth, timeout=15)
        assert r.status_code == 200
        prod = r.json()
        assert prod["produced_by_agent"], "produced_by_agent missing"
        assert prod.get("inspiration_profile") == "Calm Teacher"
        assert prod.get("frequency") == "Ocean"
        # hands-free default ON → should be published
        assert prod["status"] == "Published", f"Expected Published got {prod['status']}"
        assert prod.get("verified") is True
        assert prod.get("protected") is True


class TestProductionLineFastPath:
    def test_production_line_fast_path(self, auth):
        kr = _get_verified_kr(auth)
        prev_kr_count_r = requests.get(f"{BASE_URL}/api/knowledge-records", headers=auth, timeout=15)
        prev_count = len(prev_kr_count_r.json())

        payload = {"topic": kr["title"], "product_types": ["Blog Article"]}
        r = requests.post(f"{BASE_URL}/api/automation/production-line",
                          json=payload, headers=auth, timeout=30)
        assert r.status_code == 200, r.text
        run = r.json()
        rid = run["id"]

        final = None
        for _ in range(60):
            time.sleep(3)
            r = requests.get(f"{BASE_URL}/api/automation/production-line/runs/{rid}",
                             headers=auth, timeout=15)
            assert r.status_code == 200
            run = r.json()
            if run["status"] in ("completed", "failed", "escalated", "timeout"):
                final = run
                break
        assert final is not None, "production line run timed out"
        assert final["status"] == "completed", f"Run not completed: {final}"
        # Should reuse existing KR (fast path)
        assert final.get("kr_id") == kr["id"], "Fast path failed — different KR linked"
        assert final.get("review_state") == "auto-published"

        # Verify NO new KR was manufactured
        after_r = requests.get(f"{BASE_URL}/api/knowledge-records", headers=auth, timeout=15)
        assert len(after_r.json()) == prev_count, "Fast path unexpectedly created a new KR"


# ================= REVIEW ENDPOINT (light test — reject only) =================
class TestReview:
    def test_review_reject(self, auth):
        # Fetch any In Review or Published product and reject a fresh one
        # Create a lightweight product via manufacture and immediately reject before hands-free finishes:
        # Simpler: fetch any product and reject it
        r = requests.get(f"{BASE_URL}/api/products", headers=auth, timeout=15)
        assert r.status_code == 200
        products = r.json()
        if not products:
            pytest.skip("No products to test review")
        pid = products[0]["id"]
        r = requests.post(f"{BASE_URL}/api/automation/products/{pid}/review",
                          json={"decision": "reject"}, headers=auth, timeout=15)
        assert r.status_code == 200
        assert r.json()["status"] == "Rejected"
        # Verify
        r = requests.get(f"{BASE_URL}/api/products/{pid}", headers=auth, timeout=15)
        assert r.json()["status"] == "Rejected"

    def test_review_invalid_product(self, auth):
        r = requests.post(f"{BASE_URL}/api/automation/products/nonexistent-id/review",
                          json={"decision": "reject"}, headers=auth, timeout=15)
        assert r.status_code == 404


# ================= ENTERPRISE COMMAND CENTER =================
class TestEnterpriseCommandCenter:
    def test_command_center(self, auth):
        r = requests.get(f"{BASE_URL}/api/enterprise/command-center", headers=auth, timeout=15)
        assert r.status_code == 200
        data = r.json()
        divisions = data.get("divisions", [])
        assert len(divisions) == 6, f"Expected 6 divisions got {len(divisions)}"
        keys = {d["key"] for d in divisions}
        assert keys == {"knowledge", "manufacturing", "ai_services", "integration",
                        "commerce", "analytics"}
        for d in divisions:
            assert "metrics" in d and isinstance(d["metrics"], dict)
            assert "health" in d
        assert data.get("factory_health") in ("healthy", "attention")
        assert "portfolio" in data
        p = data["portfolio"]
        for k in ("products", "published", "protected"):
            assert k in p


# ================= CREDENTIAL LEAK REGRESSION =================
class TestNoCredentialLeak:
    def test_credential_never_leaked_across_endpoints(self, auth):
        # Add a connection with a distinct sentinel value
        sentinel = "TEST_SENTINEL_LEAK_CHECK_A9F2Q"
        r = requests.post(f"{BASE_URL}/api/integrations/connections",
                          json={"platform": "Etsy", "credential": sentinel},
                          headers=auth, timeout=15)
        assert r.status_code == 200
        cid = r.json()["id"]
        try:
            for url in ["/api/integrations/connections",
                        "/api/integrations/catalog",
                        "/api/integrations/monitor",
                        f"/api/integrations/connections/{cid}/test",
                        "/api/enterprise/command-center",
                        "/api/ai-services/status"]:
                method = "post" if url.endswith("/test") else "get"
                fn = requests.post if method == "post" else requests.get
                resp = fn(f"{BASE_URL}{url}", headers=auth, timeout=15)
                assert sentinel not in resp.text, f"Credential leaked at {url}"
        finally:
            requests.delete(f"{BASE_URL}/api/integrations/connections/{cid}",
                            headers=auth, timeout=15)
