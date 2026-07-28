"""
Iteration 59 — Enterprise Manufacturing Dashboard™ backend E2E tests.

Covers:
- Founder login (token field = access_token)
- GET /api/media-studio/knowledge-manufacturing  (list of KRs)
- GET /api/media-studio/knowledge-manufacturing/{kr_id}  (matrix)
- POST /api/media-studio/knowledge-manufacturing/{kr_id}/manufacture-all  (batch + idempotency)
- POST /api/media-studio/knowledge-manufacturing/{kr_id}/recipe/{recipe_type} (single)
- GET  /api/media-studio/inherited/{pid}/file  (PDF download)
- POST /api/media-studio/knowledge-manufacturing/{kr_id}/feedback  (Project Zero)
- Coming Soon archetypes are surfaced honestly and NOT manufactured.
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASS = "QruFounder2026!"

# Known KR ids provided in the review request.
KR_GOVERNANCE = "1a93ceb2-0334-46ff-a3a4-54bda17d7b8f"  # already has 4 recipes (idempotency target)
KR_MEMORY = "8eeda74f-8f5e-4678-8458-d691b53877be"      # fresh — good for first-time batch

RECIPES = ["workbook", "student_workbook", "instructor_guide", "assessment_pack"]
COMING_SOON = ["course", "audiobook", "marketing", "bundle"]


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASS},
                      timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    body = r.json()
    tok = body.get("access_token") or body.get("token")
    assert tok, f"No access_token in login response: {body}"
    return tok


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# ── Auth ────────────────────────────────────────────────────────────────────
class TestAuth:
    def test_login_returns_access_token(self, token):
        assert isinstance(token, str) and len(token) > 10


# ── KR List ─────────────────────────────────────────────────────────────────
class TestKrList:
    def test_list_endpoint(self, client):
        r = client.get(f"{BASE_URL}/api/media-studio/knowledge-manufacturing", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "knowledge_records" in data
        assert isinstance(data["knowledge_records"], list)
        assert data.get("philosophy") == "Understand Once. Manufacture Forever."
        # verify shape
        for k in data["knowledge_records"][:3]:
            for key in ("id", "kr_code", "topic", "version", "verified_external", "asset_count"):
                assert key in k, f"missing {key}"

    def test_known_krs_present(self, client):
        r = client.get(f"{BASE_URL}/api/media-studio/knowledge-manufacturing")
        ids = [k["id"] for k in r.json()["knowledge_records"]]
        assert KR_GOVERNANCE in ids, "Governance KR not returned"
        assert KR_MEMORY in ids, "Memory KR not returned"


# ── Matrix ─────────────────────────────────────────────────────────────────
class TestMatrix:
    def test_matrix_governance(self, client):
        r = client.get(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_GOVERNANCE}")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["kr"]["id"] == KR_GOVERNANCE
        assert isinstance(d["matrix"], list) and len(d["matrix"]) >= 15
        keys = {m["key"]: m for m in d["matrix"]}
        # 4 inheriting recipes must exist as matrix entries
        for k in RECIPES:
            assert k in keys, f"missing matrix entry {k}"
        # 4 coming_soon
        for k in COMING_SOON:
            assert k in keys and keys[k]["state"] == "coming_soon", f"{k} not honestly coming_soon"
        # project zero shape
        assert "project_zero" in d
        assert "aggregate" in d["project_zero"]
        assert "feedback_count" in d["project_zero"]

    def test_matrix_not_found(self, client):
        r = client.get(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/does-not-exist-xyz")
        assert r.status_code == 404


# ── Batch Manufacture ──────────────────────────────────────────────────────
class TestBatchManufacture:
    def test_manufacture_all_governance_is_idempotent(self, client):
        """Governance already had 4 recipes manufactured. Re-running should skip all, not duplicate."""
        r = client.post(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_GOVERNANCE}/manufacture-all",
                        timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["kr_id"] == KR_GOVERNANCE
        # idempotency: no new products manufactured
        assert d["manufactured_count"] == 0, f"Expected 0 (idempotent) got {d['manufactured_count']}"
        # each recipe should be listed as skipped with reason "Already manufactured"
        skipped_types = {s["type"] for s in d["skipped"]}
        for r_key in RECIPES:
            assert r_key in skipped_types, f"{r_key} not marked skipped"
        # coming_soon honestly surfaced
        cs_types = {c["type"] for c in d["coming_soon"]}
        for k in COMING_SOON:
            assert k in cs_types

    def test_manufacture_all_memory_fresh(self, client):
        """Manufacture all for KR_MEMORY. If fresh, expect 4; if already run, expect skipped."""
        r = client.post(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_MEMORY}/manufacture-all",
                        timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["kr_id"] == KR_MEMORY
        # total accounted for = manufactured + skipped should equal 4 (RECIPES)
        assert len(d["manufactured"]) + len(d["skipped"]) == len(RECIPES)
        # coming_soon still surfaced
        assert len(d["coming_soon"]) == len(COMING_SOON)
        # If manufactured, each product must have id + label + status
        for p in d["manufactured"]:
            assert p.get("id") and p.get("label") and p.get("status")

    def test_manufacture_all_second_call_idempotent(self, client):
        """Second call for KR_MEMORY must not add duplicates."""
        r = client.post(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_MEMORY}/manufacture-all",
                        timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["manufactured_count"] == 0
        skipped_types = {s["type"] for s in d["skipped"]}
        for k in RECIPES:
            assert k in skipped_types

    def test_matrix_after_batch_shows_manufactured(self, client):
        r = client.get(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_MEMORY}")
        assert r.status_code == 200
        d = r.json()
        keys = {m["key"]: m for m in d["matrix"]}
        for k in RECIPES:
            m = keys[k]
            assert m["state"] == "manufactured", f"{k} state is {m['state']} not manufactured"
            assert m["count"] >= 1
            # each item exposes a download url
            for item in m["items"]:
                assert item.get("download", "").startswith("/api/media-studio/inherited/")

    def test_manufacture_all_kr_not_found(self, client):
        r = client.post(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/does-not-exist/manufacture-all")
        assert r.status_code == 404


# ── Individual Recipe ──────────────────────────────────────────────────────
class TestIndividualRecipe:
    def test_manufacture_unknown_recipe_400(self, client):
        r = client.post(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_MEMORY}/recipe/nonsense")
        assert r.status_code == 400

    def test_manufacture_coming_soon_recipe_400(self, client):
        """Coming-soon recipes must NOT manufacture (Treasure Standard: no faked)."""
        r = client.post(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_MEMORY}/recipe/course")
        assert r.status_code == 400, r.text

    def test_manufacture_workbook_when_missing(self, client):
        """After deleting existing workbook for a fresh test we'd expect to build. We can't safely delete
        production data, so verify the endpoint accepts a valid recipe and returns a product record
        even if it duplicates. (Note: server code inserts each call — main agent should verify
        that individual manufacture prevents duplicates OR that this is intentional.)"""
        # We only smoke-check: request should be 200 OR a well-formed error, never 500.
        r = client.post(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_MEMORY}/recipe/workbook",
                        timeout=60)
        assert r.status_code in (200, 400), r.text
        if r.status_code == 200:
            body = r.json()
            assert body.get("id") and body.get("type") == "workbook"
            assert body["files"][0]["url"].startswith("/api/media-studio/inherited/")


# ── PDF Download ───────────────────────────────────────────────────────────
class TestPdfDownload:
    def test_download_returns_pdf(self, client):
        # get one manufactured product id from the matrix
        r = client.get(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_MEMORY}")
        d = r.json()
        pid = None
        for m in d["matrix"]:
            for i in (m.get("items") or []):
                if i.get("download"):
                    pid = i["id"]; break
            if pid: break
        assert pid, "No inherited product with a download link found"

        r2 = requests.get(f"{BASE_URL}/api/media-studio/inherited/{pid}/file",
                          timeout=30, allow_redirects=True)
        assert r2.status_code == 200, r2.text[:400]
        assert r2.headers.get("content-type", "").lower().startswith("application/pdf")
        # PDF magic
        assert r2.content[:4] == b"%PDF", "downloaded content is not a valid PDF"
        assert len(r2.content) > 500, "PDF suspiciously small"

    def test_download_missing_404(self):
        r = requests.get(f"{BASE_URL}/api/media-studio/inherited/nonexistent-id/file", timeout=15)
        assert r.status_code == 404


# ── Project Zero™ Feedback loop ────────────────────────────────────────────
class TestProjectZero:
    def test_empty_state_governance(self, client):
        r = client.get(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_GOVERNANCE}")
        d = r.json()
        # Per review request context, governance KR feedback was cleaned up.
        assert d["project_zero"]["feedback_count"] == 0

    def test_feedback_ingest_and_aggregate(self, client):
        payload = {
            "product_id": None,
            "product_type": "workbook",
            "source": "learner",
            "rating": 4.5,
            "understanding_before": 3.0,
            "understanding_after": 8.0,
            "comment": "TEST_it59 This workbook clarified governance beautifully.",
            "suggested_improvement": "TEST_it59 add more real world examples of governance."
        }
        r = client.post(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_GOVERNANCE}/feedback",
                        json=payload, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["feedback"]["kr_id"] == KR_GOVERNANCE
        assert d["feedback"]["rating"] == 4.5
        agg = d["aggregate"]
        assert agg["feedback_count"] >= 1
        assert agg["avg_rating"] is not None
        assert agg["avg_understanding_gain"] is not None
        assert agg["avg_understanding_gain"] >= 4.9  # 8.0 - 3.0 = 5.0

    def test_aggregate_written_back_to_kr(self, client):
        # After ingest, matrix endpoint should now show aggregate populated.
        r = client.get(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/{KR_GOVERNANCE}")
        d = r.json()
        assert d["project_zero"]["feedback_count"] >= 1
        assert d["project_zero"]["aggregate"]["avg_rating"] is not None

    def test_feedback_kr_not_found(self, client):
        r = client.post(f"{BASE_URL}/api/media-studio/knowledge-manufacturing/does-not-exist/feedback",
                        json={"comment": "TEST_it59 hi", "rating": 3})
        assert r.status_code == 404
