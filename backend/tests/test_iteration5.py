"""Iteration 5 — QRU Factory V2.0 (Enterprise Mode / Consumer Mode / Command Center).

Validates:
- Command Center endpoints (briefing, mission-impact, health-detailed, departments, alerts).
- Enterprise Health + Experience Lab (organization router).
- Consumer catalog, product understanding assembly, enroll/progress/certificate flow,
  favorites, my-learning, pathways.
- Role locking: learner (Customer) can access /api/consumer/* but must be denied on
  enterprise-only endpoints (server side we still allow tokens; role gating is FE).
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or None
if not BASE_URL:
    # fall back to reading frontend .env manually — required so tests exercise the ingress
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

API = f"{BASE_URL}/api"
ADMIN = ("admin@qru.com", "qru-admin-2026")
LEARNER = ("learner@qru.com", "qru-learn-2026")


def _login(email, pwd):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=30)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login(*ADMIN)


@pytest.fixture(scope="module")
def learner_token():
    return _login(*LEARNER)


def hdr(t):
    return {"Authorization": f"Bearer {t}"}


# ------------------------- Auth / roles -------------------------
class TestAuth:
    def test_admin_login_returns_admin_role(self, admin_token):
        r = requests.get(f"{API}/auth/me", headers=hdr(admin_token), timeout=15)
        assert r.status_code == 200
        me = r.json()
        assert me["email"] == "admin@qru.com"
        assert me["role"] in ("Administrator", "Admin", "Executive")

    def test_learner_role_is_customer(self, learner_token):
        r = requests.get(f"{API}/auth/me", headers=hdr(learner_token), timeout=15)
        assert r.status_code == 200
        me = r.json()
        assert me["email"] == "learner@qru.com"
        assert me["role"] == "Customer", f"learner role should be Customer, got {me['role']}"


# ------------------------- Command Center -------------------------
class TestCommandCenter:
    def test_briefing(self, admin_token):
        r = requests.get(f"{API}/command-center/briefing", headers=hdr(admin_token), timeout=20)
        assert r.status_code == 200
        b = r.json()
        for k in ("greeting", "enterprise_health", "lines", "recommendation"):
            assert k in b
        assert isinstance(b["enterprise_health"], int)
        assert 0 <= b["enterprise_health"] <= 100
        assert isinstance(b["lines"], list) and len(b["lines"]) >= 1

    def test_mission_impact(self, admin_token):
        r = requests.get(f"{API}/command-center/mission-impact", headers=hdr(admin_token), timeout=20)
        assert r.status_code == 200
        m = r.json()
        assert isinstance(m["impact"], list) and len(m["impact"]) >= 8
        assert isinstance(m["business"], list) and len(m["business"]) >= 1
        labels = {x["label"] for x in m["impact"]}
        assert "People Reached" in labels
        assert "Products Published" in labels

    def test_health_detailed(self, admin_token):
        r = requests.get(f"{API}/command-center/health-detailed", headers=hdr(admin_token), timeout=20)
        assert r.status_code == 200
        h = r.json()
        assert "overall" in h and isinstance(h["overall"], int)
        assert isinstance(h["systems"], dict) and len(h["systems"]) >= 7
        for name, s in h["systems"].items():
            for k in ("score", "owner", "why", "recommendation", "urgency", "next_action"):
                assert k in s, f"{name} missing {k}"

    def test_departments(self, admin_token):
        r = requests.get(f"{API}/command-center/departments", headers=hdr(admin_token), timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["departments"], list) and len(d["departments"]) >= 5

    def test_alerts(self, admin_token):
        r = requests.get(f"{API}/command-center/alerts", headers=hdr(admin_token), timeout=20)
        assert r.status_code == 200
        a = r.json()
        assert isinstance(a["alerts"], list) and len(a["alerts"]) >= 1


# ------------------------- Enterprise Health + Experience Lab -------------------------
class TestOrganization:
    def test_enterprise_health(self, admin_token):
        r = requests.get(f"{API}/enterprise-health", headers=hdr(admin_token), timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ("overall", "systems", "bottlenecks", "recommendations", "metrics"):
            assert k in d

    def test_experience_criteria(self, admin_token):
        r = requests.get(f"{API}/experience-lab/criteria", headers=hdr(admin_token), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json()["criteria"], list) and len(r.json()["criteria"]) >= 5

    def test_experience_lab_evaluate(self, admin_token):
        # get a published product
        pr = requests.get(f"{API}/consumer/catalog", headers=hdr(admin_token), timeout=20)
        assert pr.status_code == 200
        prods = pr.json()["products"]
        assert prods, "no published products to evaluate"
        pid = prods[0]["id"]
        r = requests.post(f"{API}/experience-lab/evaluate", headers=hdr(admin_token),
                          json={"product_id": pid}, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["product"]["id"] == pid
        ev = d["evaluation"]
        assert isinstance(ev, dict)
        assert "scores" in ev and isinstance(ev["scores"], dict)
        # every criterion should have a numeric score
        for k in ("Clarity", "Understanding", "Engagement"):
            assert k in ev["scores"], f"missing score {k}"
            assert isinstance(ev["scores"][k], (int, float))


# ------------------------- Consumer Learning Platform -------------------------
class TestConsumer:
    def test_catalog_has_demo_products(self, learner_token):
        r = requests.get(f"{API}/consumer/catalog", headers=hdr(learner_token), timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["products"], list) and len(data["products"]) >= 3
        titles = {p["title"] for p in data["products"]}
        for expected in ("How the Human Heart Pumps Blood",
                         "Why Sleep Strengthens Memory",
                         "How Insulin Controls Blood Sugar"):
            assert expected in titles, f"demo product missing: {expected}"

    def test_product_understanding_has_layers_sections_modes(self, learner_token):
        r = requests.get(f"{API}/consumer/catalog", headers=hdr(learner_token), timeout=20)
        heart = next(p for p in r.json()["products"] if p["title"].startswith("How the Human Heart"))
        r2 = requests.get(f"{API}/consumer/products/{heart['id']}", headers=hdr(learner_token), timeout=20)
        assert r2.status_code == 200
        d = r2.json()
        assert d["product"]["id"] == heart["id"]
        u = d["understanding"]
        assert u is not None
        assert isinstance(u["layers"], list) and len(u["layers"]) == 4
        assert isinstance(u["sections"], list) and len(u["sections"]) >= 10
        assert isinstance(u["learning_modes"], list) and len(u["learning_modes"]) >= 4
        assert u["verification"]["status"] == "Verified"

    def test_pathways(self, learner_token):
        r = requests.get(f"{API}/consumer/pathways", headers=hdr(learner_token), timeout=20)
        assert r.status_code == 200
        p = r.json()["pathways"]
        assert isinstance(p, list) and len(p) >= 1
        # each pathway has products
        for path in p:
            assert path["topic_count"] == len(path["products"])

    def test_enroll_progress_certificate_flow(self, learner_token):
        # pick a product
        r = requests.get(f"{API}/consumer/catalog", headers=hdr(learner_token), timeout=20)
        prods = r.json()["products"]
        pid = prods[-1]["id"]  # use last to avoid clash
        # enroll
        r = requests.post(f"{API}/consumer/enroll", headers=hdr(learner_token),
                          json={"product_id": pid}, timeout=15)
        assert r.status_code == 200
        # progress → 100 (idempotent: cert only issued once)
        r = requests.post(f"{API}/consumer/progress", headers=hdr(learner_token),
                          json={"product_id": pid, "progress": 100}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["progress"] == 100
        assert body["completed"] is True
        # certificate is only issued the first time — verify one exists in the list
        r = requests.get(f"{API}/consumer/certificates", headers=hdr(learner_token), timeout=15)
        assert r.status_code == 200
        certs = r.json()["items"]
        matched = [c for c in certs if c["product_id"] == pid]
        assert matched, f"no certificate persisted for product {pid}"
        assert matched[0]["code"].startswith("QRU-CERT-")

    def test_favorite_toggle(self, learner_token):
        r = requests.get(f"{API}/consumer/catalog", headers=hdr(learner_token), timeout=20)
        pid = r.json()["products"][0]["id"]
        r1 = requests.post(f"{API}/consumer/favorite", headers=hdr(learner_token),
                           json={"product_id": pid}, timeout=15)
        assert r1.status_code == 200
        fav1 = r1.json()["favorite"]
        r2 = requests.post(f"{API}/consumer/favorite", headers=hdr(learner_token),
                           json={"product_id": pid}, timeout=15)
        assert r2.status_code == 200
        assert r2.json()["favorite"] == (not fav1)
        # ensure favorites endpoint reflects state
        # toggle again to end in favorited state
        if not r2.json()["favorite"]:
            requests.post(f"{API}/consumer/favorite", headers=hdr(learner_token),
                          json={"product_id": pid}, timeout=15)
        r3 = requests.get(f"{API}/consumer/favorites", headers=hdr(learner_token), timeout=15)
        assert r3.status_code == 200
        ids = [i["id"] for i in r3.json()["items"]]
        assert pid in ids

    def test_my_learning_lists_enrolled(self, learner_token):
        r = requests.get(f"{API}/consumer/my-learning", headers=hdr(learner_token), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json()["items"], list) and len(r.json()["items"]) >= 1
