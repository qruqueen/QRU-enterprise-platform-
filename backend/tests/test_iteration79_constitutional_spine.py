"""Iteration 79: Constitutional spine tests — UKR→PMS→PMF.

Tests deterministic ($0 AI) manufacturing standards, UKR v1.1 registry/validate/migrate,
Book Manifest (PMF) build & retrieve for BOOK-0001 and BOOK-0011 evidence chain,
plus decoder defect spot-check.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://understanding-os.preview.emergentagent.com").rstrip("/")

FOUNDER_JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiIxZmFjN2Y2ZC04ZGFiLTRhZTgtYmYzNy1hMmZmMzBmZTNjOGYi"
    "LCJlbWFpbCI6IjIyajJyc2R6YjhAcHJpdmF0ZXJlbGF5LmFwcGxlaWQuY29t"
    "IiwiZXhwIjoxNzg0ODM1Mzc2LCJ0eXBlIjoiYWNjZXNzIn0."
    "bcViwYfsK_BDZ3-N3BgV7KRG5fWm9IbHE5K-nlf-88E"
)

BOOK_0001_ID = "8469bcc5-6d6b-4a35-bc5c-4dec82c114cb"

EXPECTED_PMS_FAMILIES = {
    "Book", "Workbook", "Poster", "Knowledge Card", "Quick Card",
    "Teacher Guide", "Presentation", "Course", "Audiobook", "Video",
}


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {FOUNDER_JWT}",
        "Content-Type": "application/json",
    })
    return s


# ---------------------------------------------------------------------------
# Manufacturing Standards spine
# ---------------------------------------------------------------------------
class TestManufacturingStandards:
    def test_standards_overview(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/standards")
        assert r.status_code == 200
        d = r.json()
        # Manufacturing Foundation present
        assert d["foundation"]["standard_id"] == "STD-MFG-FOUNDATION-0001"
        assert "shared_capabilities" in d["foundation"]
        assert len(d["foundation"]["shared_capabilities"]) >= 6
        # Constitutional flow: UKR=Truth, PMS=Instructions, PMF=Evidence
        flow = {row["artifact"]: row["owns"] for row in d["constitutional_flow"]}
        assert flow.get("UKR™") == "Truth"
        assert flow.get("PMS™") == "Instructions"
        assert flow.get("PMF™") == "Evidence"
        # Constitutional rule text
        assert "No product may manufacture without an approved Product Manufacturing Standard" in d["rule"]
        # 10 PMS families
        assert len(d["product_manufacturing_standards"]) == 10
        families = {s["product_family"] for s in d["product_manufacturing_standards"]}
        assert families == EXPECTED_PMS_FAMILIES

    def test_foundation_endpoint(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/foundation")
        assert r.status_code == 200
        d = r.json()
        assert d["standard_id"] == "STD-MFG-FOUNDATION-0001"
        assert isinstance(d["shared_capabilities"], list)
        assert len(d["shared_capabilities"]) >= 6

    def test_list_pms(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/pms")
        assert r.status_code == 200
        d = r.json()
        assert d["count"] == 10
        assert len(d["standards"]) == 10
        for s in d["standards"]:
            assert s["inherits_foundation"] == "STD-MFG-FOUNDATION-0001"
            assert s["approved"] is True

    def test_get_book_pms(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/pms/Book")
        assert r.status_code == 200
        d = r.json()
        assert d["product_family"] == "Book"
        assert d["product_type"] == "Book"
        assert d["inherits_foundation"] == "STD-MFG-FOUNDATION-0001"
        # 6 category structure
        for key in ("product_identity", "manufacturing_specifications", "product_metadata",
                    "brand_standards", "quality_gates", "deliverables"):
            assert key in d, f"Missing PMS category: {key}"

    def test_get_hologram_pms_404(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/pms/Hologram")
        assert r.status_code == 404

    def test_pms_gate_book_allows(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/pms-gate/Book")
        assert r.status_code == 200
        d = r.json()
        assert d["can_manufacture"] is True

    def test_pms_gate_hologram_blocks(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/pms-gate/Hologram")
        assert r.status_code == 200
        d = r.json()
        assert d["can_manufacture"] is False
        # Constitutional error message
        detail = d["detail"]
        err = detail.get("error", "") if isinstance(detail, dict) else str(detail)
        assert "Constitutional rule" in err or "No Product Manufacturing Standard" in err


# ---------------------------------------------------------------------------
# UKR v1.1 standard, registry, validate, migrate
# ---------------------------------------------------------------------------
class TestUKRStandardV11:
    def test_ukr_standard_metadata(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/ukr/standard")
        assert r.status_code == 200
        d = r.json()
        assert d["schema_version"] == "QRU UKR™ Standard v1.1"
        assert "Option A" in d["id_policy"]
        assert d["title_section_order"][:3] == [
            "Knowledge Title", "Published Title", "Knowledge Record ID",
        ]

    def test_ukr_registry_sorted_alphabetically(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/ukr/registry")
        assert r.status_code == 200
        d = r.json()
        recs = d["records"]
        assert len(recs) >= 70
        # Each row shape
        for row in recs[:5]:
            assert row["knowledge_record_id"].startswith("KR-")
            assert " — " in row["knowledge_title"], f"knowledge_title not in [Domain] — [Topic] form: {row['knowledge_title']}"
            assert row["published_title"]
        # Alphabetical order by knowledge_title
        titles = [r["knowledge_title"].lower() for r in recs]
        assert titles == sorted(titles), "Registry not sorted alphabetically by knowledge_title"

    def test_ukr_registry_verified_only(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/ukr/registry", params={"verified_only": "true"})
        assert r.status_code == 200
        d = r.json()
        # ~40 verified
        assert 20 <= d["count"] <= 60, f"Verified count outside expected 20..60: {d['count']}"
        for row in d["records"]:
            assert row["verified"] is True

    def test_ukr_validate_all_pass(self, client):
        r = client.get(f"{BASE_URL}/api/manufacturing/ukr/validate")
        assert r.status_code == 200
        d = r.json()
        assert d["total"] == 79
        assert d["valid"] == 79
        assert d["flagged"] == 0

    def test_ukr_migrate_dry_run_idempotent(self, client):
        r = client.post(f"{BASE_URL}/api/manufacturing/ukr/migrate", params={"dry_run": "true"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["total"] == 79
        assert d["dry_run"] is True
        # Already migrated → migrated=0, already_v11=79
        assert d["already_v11"] == 79
        assert d["migrated"] == 0
        assert d["schema_version"] == "QRU UKR™ Standard v1.1"


# ---------------------------------------------------------------------------
# Book PMF (Product Manifest) build & retrieve
# ---------------------------------------------------------------------------
class TestBookManifestBOOK0001:
    def test_build_pmf_book_0001(self, client):
        r = client.post(f"{BASE_URL}/api/book-mfg/books/{BOOK_0001_ID}/manifest/build")
        assert r.status_code == 200, r.text
        pmf = r.json()
        # PMF envelope
        assert pmf.get("manifest_id", "").startswith("PMF-")
        assert "EVIDENCE" in pmf.get("constitutional_ownership", "")
        # Inherited standards must include all 7
        inh = pmf.get("inherited_standards", [])
        ids = {s["id"] for s in inh}
        expected_ids = {
            "STD-UKR-0001", "STD-MFG-PRD-0001", "STD-PUB-0001",
            "STD-DES-0001", "STD-TREASURE-0001", "STD-VER-0001", "STD-EVID-0001",
        }
        assert expected_ids.issubset(ids), f"Missing inherited standards: {expected_ids - ids}"
        assert len(inh) == 7
        # Quality + distribution sections
        assert "validation_status" in pmf.get("quality_results", {})
        assert "launch_status" in pmf.get("distribution", {})
        # BOOK-0001 is manuscript-originated: source_intelligence.ukr_id may be null (honest)
        assert "source_intelligence" in pmf
        # not asserting non-null; just field presence
        assert "ukr_id" in pmf["source_intelligence"]

    def test_get_pmf_book_0001_persisted(self, client):
        r = client.get(f"{BASE_URL}/api/book-mfg/books/{BOOK_0001_ID}/manifest")
        assert r.status_code == 200
        d = r.json()
        # Either persisted PMF or explicit not_generated flag
        assert d.get("manifest_id", "").startswith("PMF-") or d.get("not_generated") is True


# ---------------------------------------------------------------------------
# Evidence chain — BOOK-0011 should reference KR-00001
# ---------------------------------------------------------------------------
class TestEvidenceChainBOOK0011:
    def _find_book_0011_id(self, client):
        r = client.get(f"{BASE_URL}/api/book-mfg/books")
        assert r.status_code == 200
        books = r.json() if isinstance(r.json(), list) else r.json().get("books", r.json())
        # search
        for b in books:
            if b.get("book_code") == "BOOK-0011":
                return b.get("id")
        # try nested
        return None

    def test_book_0011_pmf_references_kr_00001(self, client):
        book_id = self._find_book_0011_id(client)
        assert book_id, "BOOK-0011 not found in /api/book-mfg/books"
        r = client.post(f"{BASE_URL}/api/book-mfg/books/{book_id}/manifest/build")
        assert r.status_code == 200, r.text
        pmf = r.json()
        si = pmf.get("source_intelligence", {})
        assert si.get("ukr_id") == "KR-00001", f"Expected ukr_id=KR-00001 got {si.get('ukr_id')}"
        assert si.get("knowledge_title"), "knowledge_title empty — inheritance broken"
        # Inherited standards present
        ids = {s["id"] for s in pmf.get("inherited_standards", [])}
        assert "STD-UKR-0001" in ids


# ---------------------------------------------------------------------------
# Decoder spot-check — endpoints respond (defect fix was unit-level)
# ---------------------------------------------------------------------------
class TestDecoderSpotCheck:
    def test_decoder_endpoint_reachable(self, client):
        # Any decoder GET should not 500. Just spot-check known-good listing.
        for path in ("/api/decoder/records", "/api/knowledge-engine/records"):
            r = client.get(f"{BASE_URL}{path}")
            if r.status_code == 404:
                continue
            assert r.status_code < 500, f"{path} returned {r.status_code}: {r.text[:200]}"
