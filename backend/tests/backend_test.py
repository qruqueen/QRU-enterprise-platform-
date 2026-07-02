"""
QRU Factory Backend API tests
Covers auth, dashboard/analytics, knowledge records, manufacturing orders,
products, workforce, customers, notifications, search, user mgmt, command,
health university.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip()
BASE_URL = BASE_URL.rstrip("/")

ADMIN_EMAIL = "admin@qru.com"
ADMIN_PASSWORD = "qru-admin-2026"
EXEC_EMAIL = "executive@qru.com"
EXEC_PASSWORD = "qru-exec-2026"

# ---- Session-scoped fixtures ----

@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]

@pytest.fixture(scope="session")
def exec_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": EXEC_EMAIL, "password": EXEC_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Executive login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]

@pytest.fixture
def admin_client(admin_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"})
    return s

@pytest.fixture
def exec_client(exec_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {exec_token}", "Content-Type": "application/json"})
    return s

# =====================================================================
# Auth
# =====================================================================
class TestAuth:
    def test_root(self):
        r = requests.get(f"{BASE_URL}/api/", timeout=15)
        assert r.status_code == 200
        assert r.json().get("status") == "operational"

    def test_admin_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "Administrator"

    def test_executive_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": EXEC_EMAIL, "password": EXEC_PASSWORD}, timeout=15)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "Executive"

    def test_invalid_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": ADMIN_EMAIL, "password": "wrong"}, timeout=15)
        assert r.status_code == 401

    def test_me_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r.status_code == 401

    def test_me_with_token(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r.status_code == 200
        assert r.json()["email"] == ADMIN_EMAIL

# =====================================================================
# Dashboard & Analytics
# =====================================================================
class TestDashboard:
    def test_dashboard_stats(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/dashboard/stats", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("knowledge_records", "manufacturing_orders", "products",
                  "digital_employees", "customers", "pipeline", "recent_activity"):
            assert k in d, f"missing {k}"
        assert isinstance(d["digital_employees"], int)
        assert d["digital_employees"] >= 13, "Expected at least 13 seeded employees"

    def test_analytics_overview(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/analytics/overview", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("knowledge_by_category", "products_by_type", "orders_by_stage",
                  "employee_performance", "knowledge_growth"):
            assert k in d

# =====================================================================
# Knowledge Records
# =====================================================================
class TestKnowledgeRecords:
    def test_list_records(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/knowledge-records", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_and_verify_kr(self, admin_client):
        payload = {
            "title": "TEST_KR_Photosynthesis",
            "category": "Biology",
            "verified_truth": "Plants convert light into chemical energy via chlorophyll.",
        }
        r = admin_client.post(f"{BASE_URL}/api/knowledge-records", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        rec = r.json()
        assert rec["title"] == payload["title"]
        assert rec["verification_status"] == "Draft"
        assert "id" in rec and "_id" not in rec
        rid = rec["id"]

        # GET to verify persistence
        g = admin_client.get(f"{BASE_URL}/api/knowledge-records/{rid}", timeout=15)
        assert g.status_code == 200
        assert g.json()["title"] == payload["title"]

        # Verify endpoint
        v = admin_client.post(f"{BASE_URL}/api/knowledge-records/{rid}/verify", timeout=15)
        assert v.status_code == 200
        assert v.json()["verification_status"] == "Verified"

        # cleanup
        admin_client.delete(f"{BASE_URL}/api/knowledge-records/{rid}", timeout=15)

    @pytest.mark.slow
    def test_translate_kr(self, admin_client):
        # Create draft
        r = admin_client.post(f"{BASE_URL}/api/knowledge-records", json={
            "title": "TEST_KR_Vaccines",
            "category": "Health",
            "verified_truth": "Vaccines train the immune system to recognise pathogens.",
        }, timeout=15)
        rid = r.json()["id"]
        try:
            t = admin_client.post(f"{BASE_URL}/api/knowledge-records/{rid}/translate", timeout=120)
            assert t.status_code == 200, t.text
            d = t.json()
            # AI should populate at least one of the translation fields
            populated = any(d.get(k) for k in
                            ("consumer_translation", "everyday_analogy", "story", "memory_sentence"))
            assert populated, "AI translation returned no populated fields"
        finally:
            admin_client.delete(f"{BASE_URL}/api/knowledge-records/{rid}", timeout=15)

# =====================================================================
# Manufacturing Orders
# =====================================================================
class TestManufacturingOrders:
    def test_list_orders(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/manufacturing-orders", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_and_advance_order(self, admin_client):
        payload = {"topic": "TEST_MO_Sleep", "audience": "Adults", "product_types": ["Book"]}
        r = admin_client.post(f"{BASE_URL}/api/manufacturing-orders", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        o = r.json()
        assert o["status"] == "Queued"
        assert o["topic"] == payload["topic"]
        oid = o["id"]

        # Advance
        r2 = admin_client.patch(f"{BASE_URL}/api/manufacturing-orders/{oid}/status",
                                json={"status": "Research"}, timeout=15)
        assert r2.status_code == 200
        assert r2.json()["status"] == "Research"

        # Invalid stage
        r3 = admin_client.patch(f"{BASE_URL}/api/manufacturing-orders/{oid}/status",
                                json={"status": "Nowhere"}, timeout=15)
        assert r3.status_code == 400

        # cleanup
        admin_client.delete(f"{BASE_URL}/api/manufacturing-orders/{oid}", timeout=15)

# =====================================================================
# Products
# =====================================================================
class TestProducts:
    def test_list_products(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/products", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_types(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/products/types", timeout=15)
        assert r.status_code == 200
        assert "types" in r.json()
        assert "Book" in r.json()["types"]

    @pytest.mark.slow
    def test_generate_product(self, admin_client):
        r = admin_client.post(f"{BASE_URL}/api/products/generate", json={
            "topic": "TEST_PROD_Basic sleep hygiene",
            "product_type": "Infographic",
            "audience": "General public",
        }, timeout=180)
        assert r.status_code == 200, r.text
        p = r.json()
        assert p["product_type"] == "Infographic"
        assert p["content"] and len(p["content"]) > 50, "AI content too short"
        pid = p["id"]

        # Set status
        s = admin_client.patch(f"{BASE_URL}/api/products/{pid}/status",
                               json={"status": "In Review"}, timeout=15)
        assert s.status_code == 200
        assert s.json()["status"] == "In Review"

        s2 = admin_client.patch(f"{BASE_URL}/api/products/{pid}/status",
                                json={"status": "Published"}, timeout=15)
        assert s2.status_code == 200

        admin_client.delete(f"{BASE_URL}/api/products/{pid}", timeout=15)

    def test_generate_requires_topic(self, admin_client):
        r = admin_client.post(f"{BASE_URL}/api/products/generate",
                              json={"product_type": "Book"}, timeout=30)
        assert r.status_code == 400

# =====================================================================
# Workforce
# =====================================================================
class TestWorkforce:
    def test_list_employees(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/digital-employees", timeout=15)
        assert r.status_code == 200
        emps = r.json()
        assert len(emps) >= 13, f"Expected 13 employees, got {len(emps)}"

    def test_toggle_employee(self, admin_client):
        emps = admin_client.get(f"{BASE_URL}/api/digital-employees", timeout=15).json()
        eid = emps[0]["id"]
        original = emps[0]["status"]
        r = admin_client.patch(f"{BASE_URL}/api/digital-employees/{eid}/toggle", timeout=15)
        assert r.status_code == 200
        assert r.json()["status"] != original
        # restore
        admin_client.patch(f"{BASE_URL}/api/digital-employees/{eid}/toggle", timeout=15)

# =====================================================================
# Health, Customers, Notifications, Search
# =====================================================================
class TestMisc:
    def test_health_colleges(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/health-university/colleges", timeout=15)
        assert r.status_code == 200
        colls = r.json()
        assert len(colls) >= 7, f"Expected 7 colleges, got {len(colls)}"

    def test_customers_crud(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/customers", timeout=15)
        assert r.status_code == 200
        c = admin_client.post(f"{BASE_URL}/api/customers", json={
            "name": "TEST_Customer", "email": "test_cust@example.com",
            "organization": "TestOrg", "type": "Enterprise", "license_tier": "Premium"}, timeout=15)
        assert c.status_code == 200
        cid = c.json()["id"]
        admin_client.delete(f"{BASE_URL}/api/customers/{cid}", timeout=15)

    def test_notifications(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/notifications", timeout=15)
        assert r.status_code == 200
        notes = r.json()
        if notes:
            nid = notes[0]["id"]
            m = admin_client.patch(f"{BASE_URL}/api/notifications/{nid}/read", timeout=15)
            assert m.status_code == 200

    def test_search(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/search", params={"q": "heart"}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("knowledge_records", "manufacturing_orders", "products", "digital_employees"):
            assert k in d

# =====================================================================
# User Management (RBAC)
# =====================================================================
class TestUserManagement:
    def test_admin_can_list_users(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/users", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_executive_can_list_users(self, exec_client):
        r = exec_client.get(f"{BASE_URL}/api/users", timeout=15)
        assert r.status_code == 200

    def test_executive_cannot_create_user(self, exec_client):
        r = exec_client.post(f"{BASE_URL}/api/users", json={
            "email": "TEST_forbidden@example.com", "password": "pw12345",
            "name": "Forbidden", "role": "Customer"}, timeout=15)
        assert r.status_code == 403

    def test_admin_create_and_delete_user(self, admin_client):
        email = f"test_user_{int(time.time())}@example.com"
        r = admin_client.post(f"{BASE_URL}/api/users", json={
            "email": email, "password": "pw12345",
            "name": "TEST_Manager", "role": "Manager"}, timeout=15)
        assert r.status_code == 200, r.text
        uid = r.json()["id"]
        # Delete
        d = admin_client.delete(f"{BASE_URL}/api/users/{uid}", timeout=15)
        assert d.status_code == 200

    def test_cannot_delete_admin(self, admin_client):
        users = admin_client.get(f"{BASE_URL}/api/users", timeout=15).json()
        admin = next((u for u in users if u["role"] == "Administrator"), None)
        assert admin is not None
        r = admin_client.delete(f"{BASE_URL}/api/users/{admin['id']}", timeout=15)
        assert r.status_code == 400

# =====================================================================
# Command Console (AI)
# =====================================================================
class TestCommand:
    @pytest.mark.slow
    def test_command_create_kr(self, admin_client):
        r = admin_client.post(f"{BASE_URL}/api/command",
                              json={"message": "Create a Knowledge Record about how vaccines work"},
                              timeout=180)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "reply" in d and "action" in d
        # Cleanup if a KR was created
        if d.get("created") and d["created"].get("type") == "KnowledgeRecord":
            admin_client.delete(f"{BASE_URL}/api/knowledge-records/{d['created']['id']}", timeout=15)

    def test_command_history(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/command/history", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
