"""
QRU Factory - Iteration 2 backend tests.
Covers: QRU methodology sections, manufacture-understanding, translation engine,
review workflow, colleges + workspace, workforce department, expanded dashboard,
search including colleges.
"""
import os
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip())
BASE_URL = BASE_URL.rstrip("/")

ADMIN_EMAIL = "admin@qru.com"
ADMIN_PASSWORD = "qru-admin-2026"

QRU_SECTIONS = [
    "the_question", "simple_answer", "why_it_matters", "real_world_example",
    "qru_translation", "everyday_analogy", "memory_sentence",
    "practice_application", "key_vocabulary", "deep_roots",
]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def admin_client(admin_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"})
    return s


# =====================================================================
# Expanded Executive Command Center Dashboard
# =====================================================================
class TestExpandedDashboard:
    def test_dashboard_has_iteration2_stats(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/dashboard/stats", timeout=15)
        assert r.status_code == 200
        d = r.json()
        # New iteration-2 keys
        for k in ("verified_records", "master_files", "treasure_standard",
                  "verification_queue", "active_orders", "published_products",
                  "digital_employees_active", "marketplace_opportunities",
                  "revenue", "enterprise_health"):
            assert k in d, f"Missing dashboard key: {k}"
        assert isinstance(d["enterprise_health"], int)
        assert 0 <= d["enterprise_health"] <= 100
        assert isinstance(d["revenue"], int)
        assert d["revenue"] >= 0


# =====================================================================
# QRU methodology sections on Knowledge Records
# =====================================================================
class TestKRQruMethodology:
    def test_create_kr_has_section_status_and_qru_fields(self, admin_client):
        payload = {
            "title": "TEST_QRU_Methodology",
            "category": "Heart Health",
            "verified_truth": "The heart is a muscular organ that pumps blood through the circulatory system.",
        }
        r = admin_client.post(f"{BASE_URL}/api/knowledge-records", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        rec = r.json()
        try:
            assert "section_status" in rec
            assert set(QRU_SECTIONS).issubset(rec["section_status"].keys())
            # All QRU fields should exist on the record
            for s in QRU_SECTIONS:
                assert s in rec, f"KR missing section field {s}"
            assert rec["understanding_status"] == "Not Manufactured"
            assert rec["treasure_standard"] is False
            assert rec["is_master_file"] is False
        finally:
            admin_client.delete(f"{BASE_URL}/api/knowledge-records/{rec['id']}", timeout=15)

    def test_migrated_seed_records_have_section_status(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/knowledge-records", timeout=15)
        assert r.status_code == 200
        records = r.json()
        assert len(records) > 0
        # After migration every KR should carry section_status
        for rec in records:
            assert "section_status" in rec, f"KR {rec.get('kr_code')} missing section_status"

    @pytest.mark.slow
    def test_manufacture_understanding_fills_sections(self, admin_client):
        payload = {
            "title": "TEST_Manufacture_Photosynthesis",
            "category": "Biology",
            "verified_truth": "Photosynthesis converts light energy into chemical energy stored as sugars in plants.",
        }
        r = admin_client.post(f"{BASE_URL}/api/knowledge-records", json=payload, timeout=15)
        rid = r.json()["id"]
        try:
            # Retry once on transient LLM 503
            for attempt in range(2):
                m = admin_client.post(
                    f"{BASE_URL}/api/knowledge-records/{rid}/manufacture-understanding", timeout=180)
                if m.status_code != 503:
                    break
            assert m.status_code == 200, m.text
            updated = m.json()
            # At least half of the QRU sections should be populated by the AI
            filled = sum(1 for s in QRU_SECTIONS if updated.get(s) not in (None, "", []))
            assert filled >= 5, f"Only {filled} sections filled: {updated}"
            # Draft status on AI-filled sections
            drafts = [s for s in QRU_SECTIONS if updated["section_status"].get(s) == "Draft"]
            assert len(drafts) >= 3, f"Expected several Draft sections, got {drafts}"
            assert updated["understanding_status"] == "Draft"
        finally:
            admin_client.delete(f"{BASE_URL}/api/knowledge-records/{rid}", timeout=15)


# =====================================================================
# Review workflow (approve / reject / request_revision)
# =====================================================================
class TestReviewWorkflow:
    def _make_kr(self, admin_client, title):
        r = admin_client.post(f"{BASE_URL}/api/knowledge-records", json={
            "title": title, "category": "Heart Health",
            "verified_truth": "The heart contracts rhythmically to pump blood.",
        }, timeout=15)
        assert r.status_code == 200
        return r.json()["id"]

    def test_review_approve(self, admin_client):
        rid = self._make_kr(admin_client, "TEST_Review_Approve")
        try:
            review = {
                "decision": "approve", "confidence_score": 95,
                "evidence": "Peer-reviewed cardiology textbooks confirm.",
                "sources": ["Guyton Physiology 14th ed.", "AHA guidelines"],
                "observed_facts": "Heart auscultation reveals rhythmic sounds.",
                "calculated_data": "Cardiac output ~5 L/min at rest.",
                "analytical_judgment": "High confidence based on established physiology.",
                "conflicting_evidence": "None found.",
                "open_questions": "None outstanding.",
                "reviewer_comments": "Approved without changes.",
            }
            r = admin_client.post(f"{BASE_URL}/api/knowledge-records/{rid}/review",
                                  json=review, timeout=15)
            assert r.status_code == 200, r.text
            d = r.json()
            assert d["verification_status"] == "Verified"
            assert d["approval_status"] == "Approved"
            assert d["is_master_file"] is True
            assert d["confidence_score"] == 95
            assert d["verification"]["decision"] == "approve"
            assert d["verification"]["reviewer"]
            assert d["verification"]["sources"] == review["sources"]
            # Persistence check
            g = admin_client.get(f"{BASE_URL}/api/knowledge-records/{rid}", timeout=15)
            assert g.json()["verification_status"] == "Verified"
        finally:
            admin_client.delete(f"{BASE_URL}/api/knowledge-records/{rid}", timeout=15)

    def test_review_reject(self, admin_client):
        rid = self._make_kr(admin_client, "TEST_Review_Reject")
        try:
            r = admin_client.post(f"{BASE_URL}/api/knowledge-records/{rid}/review",
                                  json={"decision": "reject", "reviewer_comments": "Not enough evidence."},
                                  timeout=15)
            assert r.status_code == 200
            d = r.json()
            assert d["verification_status"] == "Rejected"
            assert d["approval_status"] == "Rejected"
        finally:
            admin_client.delete(f"{BASE_URL}/api/knowledge-records/{rid}", timeout=15)

    def test_review_request_revision(self, admin_client):
        rid = self._make_kr(admin_client, "TEST_Review_Revision")
        try:
            r = admin_client.post(f"{BASE_URL}/api/knowledge-records/{rid}/review",
                                  json={"decision": "request_revision",
                                        "reviewer_comments": "Please cite primary sources."},
                                  timeout=15)
            assert r.status_code == 200
            d = r.json()
            assert d["verification_status"] == "Revision Requested"
            assert d["approval_status"] == "Pending"
        finally:
            admin_client.delete(f"{BASE_URL}/api/knowledge-records/{rid}", timeout=15)


# =====================================================================
# QRU Translation Engine
# =====================================================================
class TestTranslationEngine:
    @pytest.mark.slow
    def test_translation_engine_returns_full_methodology(self, admin_client):
        payload = {
            "title": "Mitochondria",
            "content": ("Mitochondria are membrane-bound organelles that generate ATP through oxidative "
                        "phosphorylation, providing the primary energy currency of eukaryotic cells."),
        }
        for attempt in range(2):
            r = admin_client.post(f"{BASE_URL}/api/translation-engine", json=payload, timeout=180)
            if r.status_code != 503:
                break
        assert r.status_code == 200, r.text
        body = r.json()
        assert "result" in body
        result = body["result"]
        # Expect several QRU sections present
        expected_keys = ["the_question", "simple_answer", "why_it_matters",
                         "qru_translation", "everyday_analogy", "memory_sentence"]
        present = [k for k in expected_keys if result.get(k)]
        assert len(present) >= 4, f"Only {present} present in translation result"


# =====================================================================
# Colleges (Understanding Colleges)
# =====================================================================
class TestColleges:
    def test_list_colleges_includes_health_and_future(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/colleges", timeout=15)
        assert r.status_code == 200
        colls = r.json()
        assert len(colls) >= 7, f"expected >=7 colleges, got {len(colls)}"
        divisions = {c["division"] for c in colls}
        assert "Health" in divisions
        # future divisions marked Coming Soon
        future_divs = divisions - {"Health"}
        assert len(future_divs) >= 3, f"Expected future divisions, got {future_divs}"
        statuses = {c["status"] for c in colls}
        assert "Active" in statuses
        assert "Coming Soon" in statuses
        # Live counts attached
        assert all("records" in c and "products" in c for c in colls)

    def test_divisions_endpoint(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/colleges/divisions", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list)
        assert any(row["division"] == "Health" for row in d)

    def test_college_workspace(self, admin_client):
        colls = admin_client.get(f"{BASE_URL}/api/colleges?division=Health", timeout=15).json()
        assert len(colls) > 0
        cid = colls[0]["id"]
        r = admin_client.get(f"{BASE_URL}/api/colleges/{cid}/workspace", timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("college", "knowledge_records", "products",
                  "manufacturing_orders", "product_breakdown", "stats"):
            assert k in d, f"workspace missing {k}"
        assert d["college"]["id"] == cid
        for k in ("records", "verified", "products", "orders"):
            assert k in d["stats"]

    def test_college_workspace_not_found(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/colleges/nonexistent-id/workspace", timeout=15)
        assert r.status_code == 404


# =====================================================================
# Workforce Department view
# =====================================================================
class TestWorkforceDepartment:
    def test_department_returns_full_view(self, admin_client):
        emps = admin_client.get(f"{BASE_URL}/api/digital-employees", timeout=15).json()
        assert len(emps) > 0
        eid = emps[0]["id"]
        r = admin_client.get(f"{BASE_URL}/api/digital-employees/{eid}/department", timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("employee", "current_orders", "assigned_records",
                  "product_output", "team_activity", "metrics"):
            assert k in d, f"missing {k}"
        assert d["employee"]["id"] == eid
        for k in ("active_orders", "assigned_records", "products_output",
                  "published", "performance", "quality_score", "tasks_completed"):
            assert k in d["metrics"]
        assert isinstance(d["current_orders"], list)
        assert isinstance(d["assigned_records"], list)

    def test_department_404(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/digital-employees/nonexistent/department", timeout=15)
        assert r.status_code == 404


# =====================================================================
# Global Search includes Colleges
# =====================================================================
class TestSearchColleges:
    def test_search_returns_colleges_group(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/search", params={"q": "heart"}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "colleges" in d, "search response should include colleges group"
        # Heart Health college should match
        names = [c.get("name", "") for c in d["colleges"]]
        assert any("Heart" in n for n in names), f"expected Heart college in {names}"
