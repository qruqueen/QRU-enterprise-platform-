"""Iteration 4 backend tests: QRU Organization (registry, assemble, org-activity),
Creative Studio (creative-brief, creative-queue), and Publication Gate."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@qru.com"
ADMIN_PASSWORD = "qru-admin-2026"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def api(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# ---------- Organization: registry ----------
class TestRegistry:
    def test_registry_returns_26_agents(self, api):
        r = api.get(f"{BASE_URL}/api/registry", timeout=15)
        assert r.status_code == 200
        agents = r.json()
        assert isinstance(agents, list)
        board = [a for a in agents if a.get("is_board") is True]
        emergent = [a for a in agents if a.get("origin") == "Emergent"]
        assert len(board) == 13, f"expected 13 board, got {len(board)}"
        assert len(emergent) == 13, f"expected 13 Emergent, got {len(emergent)}"
        assert len(agents) >= 26
        # Verify key board members
        names = {a["name"] for a in board}
        for expected in ["Kingdom Lion™", "Legacy Eagle™", "Legacy Bear™", "Queen Unity™",
                         "Crowned Bull™", "Royal Phoenix™", "Consumer Advocate™",
                         "Creative Studio Director™", "Manufacturing Director™"]:
            assert expected in names, f"missing board member {expected}"
        # Emergent specialists have origin=Emergent and is_board false
        for a in emergent:
            assert a["is_board"] is False
            assert a["title"] in [
                "Software Architect", "Coding Specialist", "Database Engineer",
                "Security Specialist", "Performance Engineer", "Testing Specialist",
                "Deployment Engineer", "Accessibility Specialist", "UX Designer",
                "Product Designer", "Infrastructure Engineer",
                "Documentation Specialist", "Automation Specialist",
            ]

    def test_task_types(self, api):
        r = api.get(f"{BASE_URL}/api/registry/task-types", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "task_types" in data
        assert "Manufacture Product" in data["task_types"]
        assert "Verify Knowledge" in data["task_types"]

    def test_assemble_manufacture_product(self, api):
        r = api.post(f"{BASE_URL}/api/registry/assemble",
                     json={"task_type": "Manufacture Product"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["task_type"] == "Manufacture Product"
        assert set(data["departments"]) == {"Manufacturing", "Creative Studio", "Brand", "Education"}
        team = data["team"]
        assert len(team) >= 4
        depts = {m["department"] for m in team}
        # Must include all 4 targeted departments
        for d in ["Manufacturing", "Creative Studio", "Brand", "Education"]:
            assert d in depts, f"team missing department {d}"

    def test_assemble_unknown_task(self, api):
        r = api.post(f"{BASE_URL}/api/registry/assemble",
                     json={"task_type": "Nonexistent Task"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["departments"] == []
        assert data["team"] == []


# ---------- Org Activity via Verification approve ----------
class TestOrgActivity:
    def test_approve_kr_emits_org_activity(self, api):
        # Create a fresh KR
        payload = {
            "title": "TEST_iter4 Photosynthesis",
            "category": "Science",
            "division": "Health",
            "verified_truth": "Plants convert sunlight, water, and CO2 into glucose and oxygen.",
        }
        cr = api.post(f"{BASE_URL}/api/knowledge-records", json=payload, timeout=15)
        assert cr.status_code == 200, cr.text
        kr = cr.json()
        kr_id = kr["id"]
        kr_code = kr["kr_code"]

        # Approve — should log Kingdom Lion™ org activity and start manufacturing job
        rev = api.post(f"{BASE_URL}/api/knowledge-records/{kr_id}/review",
                       json={"decision": "approve", "confidence_score": 95}, timeout=20)
        assert rev.status_code == 200

        # Poll org-activity for Kingdom Lion entry mentioning kr_code
        found_lion = False
        found_mfg = False
        deadline = time.time() + 25
        while time.time() < deadline and not (found_lion and found_mfg):
            r = api.get(f"{BASE_URL}/api/org-activity", timeout=10)
            assert r.status_code == 200
            items = r.json()
            for it in items:
                if it.get("entity") == kr_code:
                    if it.get("agent") == "Kingdom Lion™":
                        found_lion = True
                    if "Manufacturing" in (it.get("department") or ""):
                        found_mfg = True
            if not (found_lion and found_mfg):
                time.sleep(2)
        assert found_lion, "Kingdom Lion™ org-activity not emitted after approve"
        assert found_mfg, "Manufacturing dept org-activity not emitted after approve"

        # Cleanup KR
        api.delete(f"{BASE_URL}/api/knowledge-records/{kr_id}", timeout=15)


# ---------- Creative Studio + Publication Gate ----------
class TestCreativeStudioAndPublishGate:
    @pytest.fixture(scope="class")
    def product_id(self, api):
        # Create/find a KR then assemble a Poster product
        kr_payload = {
            "title": "TEST_iter4 Kindness",
            "category": "Wellbeing",
            "division": "Health",
            "verified_truth": "Kindness improves social bonds and emotional wellbeing.",
            "poster_text": "Choose kindness every day.",
            "memory_sentence": "Small kindness. Big impact.",
            "why_it_matters": "Kindness builds trust and community.",
            "call_to_action": "Be kind to one person today.",
        }
        cr = api.post(f"{BASE_URL}/api/knowledge-records", json=kr_payload, timeout=15)
        assert cr.status_code == 200
        kr = cr.json()
        # Assemble a Poster product from KR (uses fields directly)
        ar = api.post(f"{BASE_URL}/api/products/assemble",
                      json={"knowledge_record_id": kr["id"], "product_type": "Poster"}, timeout=20)
        assert ar.status_code == 200, ar.text
        pid = ar.json()["id"]
        yield pid
        # cleanup
        api.delete(f"{BASE_URL}/api/products/{pid}", timeout=10)
        api.delete(f"{BASE_URL}/api/knowledge-records/{kr['id']}", timeout=10)

    def test_publish_blocked_without_brief(self, api, product_id):
        r = api.patch(f"{BASE_URL}/api/products/{product_id}/status",
                      json={"status": "Published"}, timeout=15)
        assert r.status_code == 400, r.text
        detail = r.json().get("detail", "")
        assert "Creative Studio" in detail, f"unexpected detail: {detail}"

    def test_creative_queue_includes_product(self, api, product_id):
        r = api.get(f"{BASE_URL}/api/products/creative-queue", timeout=15)
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()}
        assert product_id in ids, "product not in creative queue before brief"

    def test_generate_creative_brief(self, api, product_id):
        r = api.post(f"{BASE_URL}/api/products/{product_id}/creative-brief", timeout=90)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("creative_status") == "Reviewed"
        brief = data.get("creative_brief") or {}
        for k in ["who_for", "problem_solved", "will_understand",
                  "skills_gained", "whats_included", "reading_level",
                  "completion_time", "next_path"]:
            assert k in brief, f"brief missing key {k}"
        # skills_gained & whats_included should be lists
        assert isinstance(brief["skills_gained"], list)
        assert isinstance(brief["whats_included"], list)

    def test_creative_queue_excludes_after_review(self, api, product_id):
        r = api.get(f"{BASE_URL}/api/products/creative-queue", timeout=15)
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()}
        assert product_id not in ids, "product should be removed from creative queue after brief"

    def test_publish_succeeds_after_brief(self, api, product_id):
        r = api.patch(f"{BASE_URL}/api/products/{product_id}/status",
                      json={"status": "Published"}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "Published"
