"""QRU Decoder Engine™ (Stone 1) — backend API tests

Covers:
- Taxonomy (15 governed review states inc. Verification/Educational/Accessibility/Brand)
- Verified-KR picker (Knowledge-First)
- Decode a Verified KR → 38-field record, 5-part understanding checks, scorecard rows
- Append-only versioning (re-decode same KR → v2 non-canonical, v1 preserved)
- Certify-before-approve rejected (400)
- Approve → Certify Treasure Standard lifecycle
- Request Revision → Archive lifecycle (on a fresh decode)
- Knowledge-First rejection when decoding an unverified KR (400)
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to frontend/.env
    try:
        with open("/app/frontend/.env") as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                    break
    except Exception:
        pass
assert BASE_URL, "REACT_APP_BACKEND_URL not set"

FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

# Long decode timeout (LLM + advisory calls)
DECODE_TIMEOUT = 180


# ---------- fixtures ----------

@pytest.fixture(scope="module")
def founder_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"No access_token in login response: {data}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(founder_token):
    return {"Authorization": f"Bearer {founder_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def verified_kr_id(auth_headers):
    r = requests.get(f"{BASE_URL}/api/decoder/verified-krs", headers=auth_headers, timeout=30)
    assert r.status_code == 200, r.text
    records = r.json().get("records", [])
    assert len(records) > 0, "No verified KRs available for decoding"
    return records[0]["id"]


@pytest.fixture(scope="module")
def fresh_decoder(auth_headers, verified_kr_id):
    """Perform a fresh decode used by lifecycle tests."""
    r = requests.post(
        f"{BASE_URL}/api/decoder/decode",
        headers=auth_headers,
        json={"kr_id": verified_kr_id, "audience": "TEST_Founder Review", "level": "Introductory"},
        timeout=DECODE_TIMEOUT,
    )
    assert r.status_code == 200, f"Decode failed: {r.status_code} {r.text[:400]}"
    return r.json()["decoder"]


# ---------- taxonomy ----------

class TestTaxonomy:
    def test_taxonomy_has_15_governed_review_states(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/decoder/taxonomy", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        states = data.get("review_states", [])
        assert isinstance(states, list)
        assert len(states) == 15, f"Expected 15 review states, got {len(states)}: {states}"
        for required in ["Verification Review", "Educational Review", "Accessibility Review", "Brand Review",
                         "Founder Review Required", "Founder Approved", "Treasure Standard Certified",
                         "Revision Requested", "Archived"]:
            assert required in states, f"Missing review state: {required}"
        assert isinstance(data.get("domains", []), list) and len(data["domains"]) > 0


# ---------- verified KRs (Knowledge-First) ----------

class TestVerifiedKRs:
    def test_verified_krs_endpoint(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/decoder/verified-krs", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        records = r.json().get("records", [])
        assert isinstance(records, list)
        assert len(records) > 0, "Expected at least one Verified Knowledge Record"
        # Each record should carry the fields the picker relies on
        sample = records[0]
        assert "id" in sample and "title" in sample


# ---------- decode + 38-field contract ----------

class TestDecode:
    def test_decode_produces_38_field_record(self, fresh_decoder):
        d = fresh_decoder
        # Governed shell
        assert d["decoder_id"].startswith("DEC-"), d["decoder_id"]
        assert d["artifact_type"] == "QRU Decoder Record™"
        assert d["review_state"] == "Founder Review Required"
        assert d["treasure_standard_certified"] is False
        # source KR provenance preserved
        assert isinstance(d["source_kr_ids"], list) and len(d["source_kr_ids"]) == 1
        src = d["source_kr_ids"][0]
        assert "kr_id" in src and "version" in src
        # kr_code should be preserved (may be null in edge KRs but expected non-empty for verified pool)
        assert "kr_code" in src
        # Understanding checks — 5 parts
        uc = d.get("understanding_checks") or {}
        for k in ["explain", "recognize", "apply", "correct", "teach"]:
            assert uc.get(k), f"Missing understanding check: {k}"
        # Scorecard
        sc = d.get("scorecard") or {}
        rows = sc.get("rows") or []
        assert len(rows) >= 15, f"Expected >=15 scorecard rows (6 deterministic + 12 advisory), got {len(rows)}"
        det_rows = [r for r in rows if r.get("evaluator") == "deterministic"]
        adv_rows = [r for r in rows if r.get("evaluator") == "AI-assisted advisory"]
        assert len(det_rows) >= 6, f"Expected >=6 deterministic rows, got {len(det_rows)}"
        assert len(adv_rows) >= 12, f"Expected >=12 advisory rows, got {len(adv_rows)}"
        # Governance banner + shelf routing
        assert "Governed" in (d.get("governance_banner") or "")
        assert "Review Shelf" in (d.get("shelf_location") or "")
        # 38-field contract keys present (allow None but keys must exist)
        contract_fields = [
            "title", "artifact_type", "purpose", "governance_banner", "decoder_id", "source_kr_ids",
            "decoder_version", "domain", "subdomain", "audience", "level", "learning_objective",
            "confidence_status", "definition", "why_it_matters", "how_it_works", "core_mental_model",
            "analogy", "analogy_mapping", "analogy_limitations", "story", "visual_spec", "vocabulary",
            "misconceptions", "applications", "guided_example", "practice", "reflection", "memory_anchor",
            "verification", "understanding_checks", "next_understanding", "downstream_notes",
            "accessibility_notes", "safety_notes", "provenance", "inheritance", "review_history",
        ]
        missing = [k for k in contract_fields if k not in d]
        assert not missing, f"Missing 38-field contract keys: {missing}"

    def test_decoder_visible_on_founder_review_shelf(self, auth_headers, fresh_decoder):
        r = requests.get(
            f"{BASE_URL}/api/decoder/shelf",
            params={"state": "Founder Review Required"},
            headers=auth_headers, timeout=30,
        )
        assert r.status_code == 200, r.text
        decoders = r.json().get("decoders", [])
        ids = [d["id"] for d in decoders]
        assert fresh_decoder["id"] in ids, "Fresh decoder not found on Founder Review Shelf"


# ---------- append-only versioning ----------

class TestVersioning:
    def test_redecode_same_kr_produces_v2_non_canonical(self, auth_headers, verified_kr_id, fresh_decoder):
        # First decode already happened via fresh_decoder fixture (or older records may exist).
        # Snapshot canonical count BEFORE we re-decode
        r = requests.post(
            f"{BASE_URL}/api/decoder/decode",
            headers=auth_headers,
            json={"kr_id": verified_kr_id, "audience": "TEST_v2 check", "level": "Introductory"},
            timeout=DECODE_TIMEOUT,
        )
        assert r.status_code == 200, r.text
        d2 = r.json()["decoder"]
        assert d2["decoder_version"] >= 2, f"Expected version >= 2, got {d2['decoder_version']}"
        assert d2["is_canonical"] is False, "Second decode must not be canonical (append-only)"
        # Original canonical must still be present, unchanged, retrievable
        first = requests.get(f"{BASE_URL}/api/decoder/{fresh_decoder['id']}", headers=auth_headers, timeout=30)
        assert first.status_code == 200
        assert first.json()["decoder_id"] == fresh_decoder["decoder_id"]  # canonical id preserved


# ---------- lifecycle & permissions ----------

class TestLifecycle:
    def test_certify_before_approve_returns_400(self, auth_headers, fresh_decoder):
        r = requests.post(
            f"{BASE_URL}/api/decoder/{fresh_decoder['id']}/certify-treasure",
            headers=auth_headers, timeout=30,
        )
        assert r.status_code == 400, f"Expected 400 (Founder Approved required); got {r.status_code}: {r.text}"
        assert "Founder Approved" in r.text or "requires" in r.text.lower()

    def test_approve_then_certify_treasure(self, auth_headers, fresh_decoder):
        did = fresh_decoder["id"]
        # Approve
        r = requests.post(f"{BASE_URL}/api/decoder/{did}/approve", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        approved = r.json()
        assert approved["review_state"] == "Founder Approved"
        # Certify Treasure Standard (separate step)
        r2 = requests.post(f"{BASE_URL}/api/decoder/{did}/certify-treasure", headers=auth_headers, timeout=30)
        assert r2.status_code == 200, r2.text
        certified = r2.json()
        assert certified["review_state"] == "Treasure Standard Certified"
        assert certified["treasure_standard_certified"] is True
        # Review history should contain both entries (append-only audit log)
        hist_states = [h.get("state") for h in certified.get("review_history", [])]
        assert "Founder Approved" in hist_states
        assert "Treasure Standard Certified" in hist_states


class TestRevisionAndArchive:
    """Uses a fresh decode so it does not interfere with the approve/certify flow above."""

    @pytest.fixture(scope="class")
    def revision_decoder(self, auth_headers, verified_kr_id):
        r = requests.post(
            f"{BASE_URL}/api/decoder/decode",
            headers=auth_headers,
            json={"kr_id": verified_kr_id, "audience": "TEST_revision path", "level": "Introductory"},
            timeout=DECODE_TIMEOUT,
        )
        assert r.status_code == 200, r.text
        return r.json()["decoder"]

    def test_request_revision_then_archive(self, auth_headers, revision_decoder):
        did = revision_decoder["id"]
        r = requests.post(
            f"{BASE_URL}/api/decoder/{did}/request-revision",
            headers=auth_headers,
            json={"notes": "TEST_notes: tighten memory anchor"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        assert r.json()["review_state"] == "Revision Requested"
        r2 = requests.post(f"{BASE_URL}/api/decoder/{did}/archive", headers=auth_headers, timeout=30)
        assert r2.status_code == 200, r2.text
        assert r2.json()["review_state"] == "Archived"


# ---------- Knowledge-First gate ----------

class TestKnowledgeFirstGate:
    def test_decode_unverified_kr_rejected(self, auth_headers):
        # Look for an unverified KR in the DB via the KR listing endpoint (if any).
        # We'll first try a well-known "not verified" path: an obviously invalid id → 400 with
        # "Knowledge Record not found" — but we want the Knowledge-First path specifically.
        # Try to find an unverified KR from /api/knowledge (many QRU builds expose this).
        candidates = []
        for url in [f"{BASE_URL}/api/knowledge/records", f"{BASE_URL}/api/knowledge-records",
                    f"{BASE_URL}/api/knowledge"]:
            try:
                rr = requests.get(url, headers=auth_headers, timeout=15)
                if rr.status_code == 200:
                    payload = rr.json()
                    items = payload.get("records") if isinstance(payload, dict) else payload
                    if isinstance(items, list):
                        for it in items:
                            if not (it.get("verification_status") == "Verified"
                                    or it.get("approval_status") == "Approved"
                                    or it.get("treasure_standard")
                                    or it.get("verified_external")):
                                candidates.append(it.get("id"))
                        if candidates:
                            break
            except Exception:
                pass

        if not candidates:
            pytest.skip("No unverified KR available in this environment to exercise the gate.")

        r = requests.post(
            f"{BASE_URL}/api/decoder/decode",
            headers=auth_headers,
            json={"kr_id": candidates[0]},
            timeout=DECODE_TIMEOUT,
        )
        assert r.status_code == 400, f"Expected 400 Knowledge-First rejection, got {r.status_code}: {r.text}"
        assert "Verified" in r.text or "verified" in r.text
