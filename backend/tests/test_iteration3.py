"""Iteration 3 backend tests — AI Manufacturing Pipeline (background job),
per-field regenerate/approve, product assembly recipes, traceability, dashboard."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://understanding-os.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@qru.com"
ADMIN_PASSWORD = "qru-admin-2026"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def fresh_kr(client):
    """Create a fresh KR so it starts with `understanding_status`='Not Manufactured'."""
    payload = {
        "title": "TEST_Iter3 Sunlight Vitamin D",
        "subtitle": "How the body makes vitamin D",
        "category": "Health",
        "division": "Health",
        "verified_truth": ("Ultraviolet-B radiation from sunlight converts 7-dehydrocholesterol in the skin into "
                            "previtamin D3, which is then converted to active vitamin D. Vitamin D is essential "
                            "for calcium absorption and bone health."),
    }
    r = client.post(f"{BASE_URL}/api/knowledge-records", json=payload)
    assert r.status_code == 200, r.text
    rec = r.json()
    assert rec["understanding_status"] == "Not Manufactured"
    yield rec
    # cleanup
    client.delete(f"{BASE_URL}/api/knowledge-records/{rec['id']}")


# ---------- Schema ----------
class TestSchema:
    def test_schema_groups(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing-jobs/schema")
        assert r.status_code == 200
        data = r.json()
        assert "groups" in data and isinstance(data["groups"], list)
        labels = [g["label"] for g in data["groups"]]
        # expect 7 groups
        for expected in ["Core Understanding", "Comprehension Aids", "Vocabulary & FAQ",
                         "Assessment", "Audience Versions", "Guidance Notes", "Media & Product Assets"]:
            assert expected in labels
        # every group has fields
        for g in data["groups"]:
            assert isinstance(g["fields"], list) and len(g["fields"]) > 0
        assert "all_fields" in data and len(data["all_fields"]) >= 40


# ---------- Manufacture-all background job ----------
class TestManufactureAllJob:
    def test_start_and_poll_to_completion(self, client, fresh_kr):
        rid = fresh_kr["id"]
        r = client.post(f"{BASE_URL}/api/knowledge-records/{rid}/manufacture-all")
        assert r.status_code == 200, r.text
        job_id = r.json()["job_id"]
        assert job_id

        # Poll: at least one intermediate reading, then complete
        deadline = time.time() + 180
        last = None
        seen_running = False
        while time.time() < deadline:
            jr = client.get(f"{BASE_URL}/api/manufacturing-jobs/{job_id}")
            assert jr.status_code == 200, jr.text
            last = jr.json()
            if last["status"] == "running":
                seen_running = True
                assert 0 <= last["progress"] <= 100
            if last["status"] in ("complete", "failed"):
                break
            time.sleep(4)

        assert last is not None
        assert last["status"] == "complete", f"Job did not complete: {last}"
        assert last["progress"] == 100
        assert len(last["steps"]) >= 8  # 7 batches + finalize

        # Now verify KR has field_status entries as Draft and multiple populated fields
        kr = client.get(f"{BASE_URL}/api/knowledge-records/{rid}").json()
        fs = kr.get("field_status", {})
        draft_count = sum(1 for v in fs.values() if v == "Draft")
        assert draft_count >= 15, f"Expected many draft fields, got {draft_count}: {fs}"
        # spot check populated fields
        populated = [f for f in ("quiz", "story_version", "faq", "poster_text", "memory_sentence",
                                 "vocabulary_decoder", "kingdom_lion_questions", "call_to_action",
                                 "children_version") if kr.get(f)]
        assert len(populated) >= 5, f"Expected populated fields, got: {populated}"

    def test_active_jobs_filter(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing-jobs?active=true")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------- Per-field regen & approve ----------
class TestPerFieldOps:
    def test_regenerate_and_approve_memory_sentence(self, client, fresh_kr):
        rid = fresh_kr["id"]
        r = client.post(f"{BASE_URL}/api/knowledge-records/{rid}/fields/memory_sentence/regenerate", timeout=60)
        assert r.status_code == 200, r.text
        rec = r.json()
        assert rec.get("memory_sentence"), "memory_sentence should be filled"
        assert rec["field_status"].get("memory_sentence") == "Draft"

        # Approve field
        r2 = client.patch(f"{BASE_URL}/api/knowledge-records/{rid}/fields/memory_sentence/approve",
                          json={"status": "Approved"})
        assert r2.status_code == 200
        assert r2.json()["field_status"]["memory_sentence"] == "Approved"

    def test_regenerate_unknown_field_rejected(self, client, fresh_kr):
        r = client.post(f"{BASE_URL}/api/knowledge-records/{fresh_kr['id']}/fields/not_a_field/regenerate")
        assert r.status_code == 400


# ---------- Assemble product from recipe ----------
class TestAssemble:
    def test_recipes_endpoint(self, client):
        r = client.get(f"{BASE_URL}/api/products/recipes")
        assert r.status_code == 200
        data = r.json()
        assert "Poster" in data["recipes"]
        assert isinstance(data["recipes"]["Poster"], list)

    def test_assemble_poster(self, client, fresh_kr):
        rid = fresh_kr["id"]
        r = client.post(f"{BASE_URL}/api/products/assemble",
                        json={"knowledge_record_id": rid, "product_type": "Poster"})
        assert r.status_code == 200, r.text
        p = r.json()
        assert p["assembled"] is True
        assert p["kr_version"] == 1
        assert p["knowledge_record_id"] == rid
        assert p["status"] in ("Ready", "Needs Review")
        assert p["content"].startswith("# ")  # markdown title
        assert "recipe" in p and len(p["recipe"]) >= 3
        # Verify persisted via GET
        gr = client.get(f"{BASE_URL}/api/products/{p['id']}")
        assert gr.status_code == 200
        assert gr.json()["knowledge_record_id"] == rid
        return p["id"]

    def test_assemble_unknown_product_type(self, client, fresh_kr):
        r = client.post(f"{BASE_URL}/api/products/assemble",
                        json={"knowledge_record_id": fresh_kr["id"], "product_type": "Nonexistent"})
        assert r.status_code == 400


# ---------- Traceability ----------
class TestTraceability:
    def test_update_bumps_version_and_flags_products(self, client, fresh_kr):
        rid = fresh_kr["id"]
        # ensure a product assembled first
        client.post(f"{BASE_URL}/api/products/assemble",
                    json={"knowledge_record_id": rid, "product_type": "Poster"})
        # fetch current version
        before = client.get(f"{BASE_URL}/api/knowledge-records/{rid}").json()
        before_ver = before["version"]

        # Edit KR
        upd_payload = {
            "title": before["title"] + " (updated)",
            "category": before["category"],
            "verified_truth": before["verified_truth"] + " Updated statement.",
        }
        u = client.put(f"{BASE_URL}/api/knowledge-records/{rid}", json=upd_payload)
        assert u.status_code == 200, u.text
        after = u.json()
        assert after["version"] == before_ver + 1

        # Dependents endpoint should show products with Needs Regeneration
        dep = client.get(f"{BASE_URL}/api/knowledge-records/{rid}/dependents")
        assert dep.status_code == 200
        prods = dep.json()
        assert len(prods) >= 1
        assert any(p.get("status") == "Needs Regeneration" for p in prods), f"Expected NR product, got {prods}"


# ---------- Dashboard ----------
class TestDashboard:
    def test_dashboard_has_new_iter3_fields(self, client):
        r = client.get(f"{BASE_URL}/api/dashboard/stats")
        assert r.status_code == 200
        d = r.json()
        for k in ("manufacturing_jobs_active", "active_jobs", "recently_updated", "products_needs_regeneration"):
            assert k in d, f"missing {k} in dashboard stats"
        assert isinstance(d["active_jobs"], list)
        assert isinstance(d["recently_updated"], list)
        assert isinstance(d["products_needs_regeneration"], int)
