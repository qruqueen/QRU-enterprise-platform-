"""MO-003 Knowledge Record 2.0 — backend tests."""
import os
import pytest
import requests

# All tests share state on KR-00047 → force single worker via xdist_group.
pytestmark = pytest.mark.xdist_group("kr2_serial")

BASE = (os.environ.get("REACT_APP_BACKEND_URL")
        or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].splitlines()[0]).rstrip("/")
FOUNDER = {"email": "22j2rsdzb8@privaterelay.appleid.com", "password": "QruFounder2026!"}
API = f"{BASE}/api"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{API}/auth/login", json=FOUNDER, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


def _find_kr(client, kr_code):
    r = client.get(f"{API}/knowledge-records", timeout=30)
    data = r.json()
    records = data if isinstance(data, list) else data.get("records", [])
    for k in records:
        if k.get("kr_code") == kr_code:
            return k
    return None


@pytest.fixture(scope="session")
def kr47(client):
    kr = _find_kr(client, "KR-00047")
    assert kr, "KR-00047 not found"
    return kr


@pytest.fixture(scope="session", autouse=True)
def reset_test_sections(client, kr47):
    """Reset test-polluted sections (from prior runs) so acceptance criteria hold."""
    for sid in ("youtube_script", "image_concepts", "question_library", "quiz_bank"):
        client.put(f"{API}/kr2/{kr47['id']}/section/{sid}",
                   json={"content": "", "status": "Pending", "source": "Deterministic"}, timeout=30)
    yield


# ------------------- Registry / Dependency Map
class TestRegistry:
    def test_registry(self, client):
        r = client.get(f"{API}/kr2/registry", timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["schema_version"] == 2
        assert j["section_count"] == 36
        expected_groups = {"Core", "Translations", "Understanding", "Verification",
                           "Application", "Assessment", "Media", "Education", "Visual", "Relationships"}
        assert expected_groups.issubset(set(j["groups"].keys())), j["groups"].keys()
        assert "Pending" in j["status_values"] and "Verified" in j["status_values"]
        assert "Imported" in j["source_values"] and "Founder" in j["source_values"]
        assert "Unverified" in j["verification_values"]

    def test_dependency_map(self, client):
        r = client.get(f"{API}/kr2/dependency-map", timeout=30)
        assert r.status_code == 200
        dm = r.json()["dependency_map"]
        teacher = dm["teacher"]
        for req in ["Executive Summary", "Deep Explanation", "Teacher Translation™",
                    "Question Library", "Quiz Bank", "Scientific References", "Teacher Notes"]:
            assert req in teacher, f"teacher missing {req}: {teacher}"


# ------------------- Migration idempotency
class TestMigration:
    def test_migrate_idempotent(self, client):
        r1 = client.post(f"{API}/kr2/migrate", timeout=120)
        assert r1.status_code == 200, r1.text
        j1 = r1.json()
        assert j1["schema_version"] == 2
        assert j1["migrated"] >= 1
        r2 = client.post(f"{API}/kr2/migrate", timeout=120)
        assert r2.status_code == 200
        j2 = r2.json()
        assert j2["migrated"] == j1["migrated"]


# ------------------- GET KR
class TestGetKR:
    def test_kr47_shape(self, client, kr47):
        r = client.get(f"{API}/kr2/{kr47['id']}", timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["schema_version"] == 2
        assert len(j["sections"]) == 36
        assert j["sections"][0]["section_id"] == "executive_summary"
        assert j["sections"][1]["section_id"] == "deep_explanation"
        c = j["completeness"]
        assert c["total"] == 36
        assert 0 <= c["percent"] <= 100
        for s in j["sections"]:
            for key in ("section_id", "title", "content", "status", "source",
                        "verification_status", "confidence_score", "version",
                        "manufacturing_ready", "depended_on_by"):
                assert key in s, f"missing {key} in section {s.get('section_id')}"
            assert isinstance(s["depended_on_by"], list)

    def test_kr47_verified_core_sections(self, client, kr47):
        r = client.get(f"{API}/kr2/{kr47['id']}", timeout=30)
        j = r.json()
        sec_by_id = {s["section_id"]: s for s in j["sections"]}
        if kr47.get("verification_status") == "Verified":
            for sid in ("executive_summary", "deep_explanation", "qru_translation"):
                s = sec_by_id[sid]
                assert s["version"] > 0
                assert s["status"] == "Verified", f"{sid} status={s['status']}"
                assert s["source"] == "Imported", f"{sid} source={s['source']}"
                assert s["content"], f"{sid} content empty"
        pending = [s for s in j["sections"] if s["status"] == "Pending"]
        assert len(pending) > 0


# ------------------- Manufacturing readiness (before we pollute state further)
class TestManufacturingReadiness:
    def test_youtube_missing(self, client, kr47):
        r = client.get(f"{API}/kr2/{kr47['id']}/manufacturing-readiness",
                       params={"product_type": "YouTube Video"}, timeout=30)
        assert r.status_code == 200
        j = r.json()
        assert "YouTube Script" in j["missing_sections"], j
        assert "Image Concepts" in j["missing_sections"], j
        assert j["manufacturing_allowed"] is False

    def test_consumer_guide_allowed(self, client, kr47):
        r = client.get(f"{API}/kr2/{kr47['id']}/manufacturing-readiness",
                       params={"product_type": "Consumer Guide"}, timeout=30)
        assert r.status_code == 200
        j = r.json()
        assert j["manufacturing_allowed"] is True, j


# ------------------- Manufacturing gate integration
class TestManufacturingGate:
    def test_video_manufacture_blocked(self, client, kr47):
        r = client.post(f"{API}/automation/manufacture/{kr47['id']}",
                        json={"product_types": ["YouTube Video Script"]}, timeout=60)
        assert r.status_code == 400, r.text
        detail = str(r.json().get("detail") or r.json())
        assert ("Knowledge Record 2.0" in detail
                or "sections are incomplete" in detail), detail


# ------------------- Update section (runs last since it mutates state)
class TestSectionUpdate:
    def test_update_and_version_increments(self, client, kr47):
        r0 = client.get(f"{API}/kr2/{kr47['id']}", timeout=30)
        current = next(s for s in r0.json()["sections"] if s["section_id"] == "image_concepts")
        prev_v = current["version"]

        payload = {"content": "TEST image concept content", "status": "Draft", "source": "Founder"}
        r = client.put(f"{API}/kr2/{kr47['id']}/section/image_concepts", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        s = r.json()
        assert s["version"] == prev_v + 1
        assert s["content"] == "TEST image concept content"
        assert s["status"] == "Draft"
        assert s["manufacturing_ready"] is True

    def test_invalid_status(self, client, kr47):
        r = client.put(f"{API}/kr2/{kr47['id']}/section/image_concepts",
                       json={"status": "Bogus"}, timeout=30)
        assert r.status_code == 400

    def test_invalid_source(self, client, kr47):
        r = client.put(f"{API}/kr2/{kr47['id']}/section/image_concepts",
                       json={"source": "Alien"}, timeout=30)
        assert r.status_code == 400

    def test_migrate_preserves_edits(self, client, kr47):
        """Re-running migrate must not overwrite our edited section."""
        r = client.post(f"{API}/kr2/migrate", timeout=120)
        assert r.status_code == 200
        r2 = client.get(f"{API}/kr2/{kr47['id']}", timeout=30)
        ic = next(s for s in r2.json()["sections"] if s["section_id"] == "image_concepts")
        assert ic["content"] == "TEST image concept content", "migration overwrote edited section!"

    def test_reset_polluted_sections(self, client, kr47):
        """Cleanup: reset image_concepts back to Pending so next runs start clean."""
        r = client.put(f"{API}/kr2/{kr47['id']}/section/image_concepts",
                       json={"content": "", "status": "Pending", "source": "Deterministic"},
                       timeout=30)
        assert r.status_code == 200
