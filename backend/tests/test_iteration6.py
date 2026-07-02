"""Iteration 6 — QRU Manufacturing Engine 2.0 + Automatic Treasure Standard™ Quality Control.

Covers:
- GET /api/manufacturing2/recipes — 13 recipes with required_fields/stages/deliverables
- POST /api/manufacturing2/detect-missing — for Book (missing fields) and Interactive Lesson (ready)
- POST /api/manufacturing2/assemble — creates a Manufacturing product with stages/gates/deliverables
- GET  /api/manufacturing2/{pid}/pipeline — full pipeline shape
- POST /api/manufacturing2/{pid}/quality-control + polling — converges to certified/treasure_standard/all gates passed
- POST /api/manufacturing2/{pid}/release — 400 before, then Published after certification
- Regression: consumer Student Mode renders (mode-btn-student equivalent — key='student')
"""
import os
import time
import pytest
import requests
from pathlib import Path


def _load_frontend_env():
    env = Path("/app/frontend/.env")
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


_load_frontend_env()
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN = ("admin@qru.com", "qru-admin-2026")
LEARNER = ("learner@qru.com", "qru-learn-2026")


@pytest.fixture(scope="module")
def admin_client():
    s = requests.Session()
    s.headers["Content-Type"] = "application/json"
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN[0], "password": ADMIN[1]}, timeout=30)
    assert r.status_code == 200, r.text
    token = r.json().get("token") or r.json().get("access_token")
    assert token
    s.headers["Authorization"] = f"Bearer {token}"
    return s


@pytest.fixture(scope="module")
def learner_client():
    s = requests.Session()
    s.headers["Content-Type"] = "application/json"
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": LEARNER[0], "password": LEARNER[1]}, timeout=30)
    assert r.status_code == 200, r.text
    token = r.json().get("token") or r.json().get("access_token")
    s.headers["Authorization"] = f"Bearer {token}"
    return s


@pytest.fixture(scope="module")
def demo_kr(admin_client):
    """Find one of the seeded demo Knowledge Records."""
    r = admin_client.get(f"{BASE_URL}/api/knowledge-records?status=Verified", timeout=30)
    assert r.status_code == 200
    krs = r.json()
    # prefer Insulin (mentioned by main agent) or fall back to any demo
    for candidate in ("Insulin", "Sleep", "Heart"):
        for kr in krs:
            if candidate.lower() in (kr.get("title") or "").lower():
                return kr
    assert krs, "no verified knowledge records"
    return krs[0]


# ---------------- Recipes ----------------
class TestRecipes:
    def test_list_recipes(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/manufacturing2/recipes", timeout=15)
        assert r.status_code == 200
        data = r.json()
        recipes = data["recipes"]
        assert len(recipes) == 13
        for rec in recipes:
            assert "product_type" in rec
            assert "version" in rec
            assert isinstance(rec["required_fields"], list) and rec["required_fields"]
            for rf in rec["required_fields"]:
                assert "field" in rf and "label" in rf
            assert isinstance(rec["stages"], list) and rec["stages"]
            assert isinstance(rec["deliverables"], list) and rec["deliverables"]

    def test_types_include_book_and_interactive_lesson(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/manufacturing2/recipes", timeout=15)
        types = {rec["product_type"] for rec in r.json()["recipes"]}
        for t in ("Book", "Interactive Lesson", "Workbook", "Poster", "Quiz"):
            assert t in types


# ---------------- Detect Missing ----------------
class TestDetectMissing:
    def test_book_has_missing(self, admin_client, demo_kr):
        r = admin_client.post(f"{BASE_URL}/api/manufacturing2/detect-missing",
                              json={"knowledge_record_id": demo_kr["id"], "product_type": "Book"}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "missing" in data and "ready" in data and "required_count" in data
        # Book requires adult_version, faq etc — should have SOME missing on demo record
        assert data["required_count"] >= 5
        assert isinstance(data["missing"], list)
        # not required to be non-empty, but the spec says demo records usually miss some
        for m in data["missing"]:
            assert "field" in m and "label" in m

    def test_interactive_lesson_is_ready(self, admin_client, demo_kr):
        r = admin_client.post(f"{BASE_URL}/api/manufacturing2/detect-missing",
                              json={"knowledge_record_id": demo_kr["id"], "product_type": "Interactive Lesson"}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ready"] is True, f"Expected ready for Interactive Lesson, got missing={data['missing']}"
        assert data["missing"] == []


# ---------------- Assemble ----------------
@pytest.fixture(scope="module")
def assembled_product(admin_client, demo_kr):
    r = admin_client.post(f"{BASE_URL}/api/manufacturing2/assemble",
                          json={"knowledge_record_id": demo_kr["id"], "product_type": "Interactive Lesson"}, timeout=30)
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["status"] == "Manufacturing"
    assert p["recipe_type"] == "Interactive Lesson"
    return p


class TestAssemble:
    def test_product_shape(self, assembled_product):
        p = assembled_product
        assert p["assembled"] is True
        # stages
        labels = [s["label"] for s in p["stages"]]
        for req in ("Knowledge Master Record", "Required Fields", "Understanding Assets", "Product Assembly", "Quality Control", "Treasure Standard", "Release"):
            assert req in labels
        stage_map = {s["label"]: s for s in p["stages"]}
        assert stage_map["Knowledge Master Record"]["status"] == "done"
        assert stage_map["Required Fields"]["status"] == "done"
        assert stage_map["Product Assembly"]["status"] == "done"
        # gates all pending
        assert set(p["gates"].keys()) >= {"Verification", "Education Review", "Creative Studio", "Brand Review", "Accessibility", "Experience Review", "Quality Control", "Treasure Standard"}
        for gname, gval in p["gates"].items():
            assert gval["status"] == "pending", f"{gname} not pending"
        assert isinstance(p["deliverables"], list) and len(p["deliverables"]) >= 4

    def test_pipeline_endpoint(self, admin_client, assembled_product):
        r = admin_client.get(f"{BASE_URL}/api/manufacturing2/{assembled_product['id']}/pipeline", timeout=15)
        assert r.status_code == 200
        pl = r.json()
        for k in ("id", "product_code", "title", "product_type", "status", "recipe_type", "stages", "gates", "deliverables", "missing_fields", "qc", "treasure_standard"):
            assert k in pl


# ---------------- Release before certification ----------------
class TestReleaseBlocked:
    def test_release_locked_before_qc(self, admin_client, assembled_product):
        r = admin_client.post(f"{BASE_URL}/api/manufacturing2/{assembled_product['id']}/release", timeout=15)
        assert r.status_code == 400, r.text
        detail = r.json().get("detail", "")
        assert "Release locked" in detail
        assert "Pending gates" in detail


# ---------------- Quality Control loop ----------------
class TestQualityControlLoop:
    def test_qc_converges_and_certifies(self, admin_client, assembled_product):
        pid = assembled_product["id"]
        r = admin_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/quality-control", timeout=15)
        assert r.status_code == 200

        # Poll — allow up to ~150s
        deadline = time.time() + 180
        final = None
        while time.time() < deadline:
            time.sleep(5)
            pr = admin_client.get(f"{BASE_URL}/api/manufacturing2/{pid}/pipeline", timeout=15)
            assert pr.status_code == 200
            pl = pr.json()
            final = pl
            print(f"[QC poll] status={pl['status']} qc.status={pl.get('qc',{}).get('status')} iter={pl.get('qc',{}).get('iterations')}")
            if pl["status"] == "Ready for Release" and pl.get("treasure_standard"):
                break
            if pl.get("qc", {}).get("status") in ("failed", "needs_review"):
                break
        assert final is not None
        assert final["status"] == "Ready for Release", f"final status={final['status']}, qc={final.get('qc')}"
        assert final["treasure_standard"] is True
        assert final["qc"]["status"] == "certified"
        for g, v in final["gates"].items():
            assert v["status"] == "passed", f"gate {g} not passed: {v}"

    def test_release_after_certification(self, admin_client, assembled_product):
        pid = assembled_product["id"]
        r = admin_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/release", timeout=15)
        assert r.status_code == 200, r.text
        product = r.json()
        assert product["status"] == "Published"
        # verify via pipeline endpoint
        pr = admin_client.get(f"{BASE_URL}/api/manufacturing2/{pid}/pipeline", timeout=15)
        assert pr.json()["status"] == "Published"


# ---------------- Regression: Student Mode fix ----------------
class TestStudentModeRegression:
    def test_learner_locked_to_consumer(self, learner_client):
        r = learner_client.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r.status_code == 200
        assert r.json().get("role") == "Customer"

    def test_student_mode_available_on_demo(self, learner_client):
        r = learner_client.get(f"{BASE_URL}/api/consumer/catalog", timeout=15)
        assert r.status_code == 200
        products = r.json()["products"]
        assert products, "no published consumer products"
        # find a demo product
        demo = next((p for p in products if "Insulin" in p.get("title", "") or "Heart" in p.get("title", "") or "Sleep" in p.get("title", "")), products[0])
        pr = learner_client.get(f"{BASE_URL}/api/consumer/products/{demo['id']}", timeout=15)
        assert pr.status_code == 200
        modes = pr.json().get("understanding", {}).get("learning_modes", [])
        mode_keys = {m["key"] for m in modes}
        assert "student" in mode_keys, f"Student mode missing. Got keys: {mode_keys}"
