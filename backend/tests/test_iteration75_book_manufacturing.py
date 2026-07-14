"""Iteration 75 — QRU Book Manufacturing System™ v1.0

Validates:
- Seven-button config
- Pilot 'The Understanding Tree' seeded, immutable original + working copy + provenance
- Proof & Polish real work (does NOT rewrite)
- Approve & lock edition
- Design gating (400 before lock) then real interior PDF + EPUB + 3 covers
- select-cover
- audio/video/publish/monitor honest states
- Final Release Gate not-ready when authorization/pricing missing
"""
import os
import requests
import pytest

_env = os.environ.get("REACT_APP_BACKEND_URL")
if not _env:
    # Load from frontend/.env for CI
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    _env = line.split("=", 1)[1].strip()
                    break
    except Exception:
        pass
BASE_URL = (_env or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL missing"
FOUNDER = {"email": "22j2rsdzb8@privaterelay.appleid.com", "password": "QruFounder2026!"}


@pytest.fixture(scope="module")
def founder_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=FOUNDER, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"No access_token in response: {data}"
    return tok


@pytest.fixture(scope="module")
def headers(founder_token):
    return {"Authorization": f"Bearer {founder_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def pilot(headers):
    r = requests.get(f"{BASE_URL}/api/book-mfg/books", headers=headers, timeout=30)
    assert r.status_code == 200, r.text
    books = r.json().get("books", [])
    pilot = next((b for b in books if "Understanding Tree" in (b.get("title") or "")), None)
    assert pilot, f"Pilot not found. Books: {books}"
    return pilot


# ------------------------------ CONFIG ------------------------------
class TestConfig:
    def test_seven_buttons_exact_order(self, headers):
        r = requests.get(f"{BASE_URL}/api/book-mfg/config", headers=headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        keys = [b["key"] for b in data["buttons"]]
        assert keys == ["upload", "proof", "design", "audio", "video", "publish", "monitor"], keys
        labels = [b["label"] for b in data["buttons"]]
        assert labels == ["Upload", "Proof & Polish", "Design", "Audio", "Video", "Publish", "Monitor"], labels
        assert len(data["publish_destinations"]) >= 5


# ------------------------------ PILOT ------------------------------
class TestPilot:
    def test_pilot_listed(self, pilot):
        assert pilot["title"] == "The Understanding Tree"
        assert pilot["author"] == "E.Q. Rothwell"
        assert "QRU Press" in pilot["imprint"]
        # editorial_status could have changed if prior test ran; accept either
        assert pilot.get("book_code", "").startswith("BOOK-")

    def test_canonical_record_has_immutable_and_working_copy(self, headers, pilot):
        r = requests.get(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}", headers=headers, timeout=30)
        assert r.status_code == 200
        b = r.json()
        # Title before Book Record ID: verify both exist
        assert b["title"] == "The Understanding Tree"
        assert b["book_code"].startswith("BOOK-")
        # Immutable original
        orig = b["original"]
        assert orig["immutable"] is True
        assert orig["checksum"] and isinstance(orig["checksum"], str) and len(orig["checksum"]) == 64
        # Separate working copy
        assert "working_copy" in b and b["working_copy"]["content"]
        # Provenance
        p = b["transparent_provenance"]
        assert "Understanding Tree Draft.docx" in p["source_filename"]
        assert p["rights_holder"]
        assert p["immutable_original_checksum"] == orig["checksum"]
        # Intake scan detected 11 chapters
        assert b["intake_scan"]["detected_structure"]["chapter_count"] == 11, b["intake_scan"]["detected_structure"]
        # Draft-file honest statuses (source_status must be Draft received unless proof/approve already ran)
        assert b["source_status"] == "Draft received", b["source_status"]
        # publication_status must remain 'Not ready' until true publish (never happens in factory)
        assert b["publication_status"] == "Not ready"


# ------------------------------ PROOF ------------------------------
class TestProofAndApprove:
    def test_proof_real_work(self, headers, pilot):
        # Fetch pre-proof content checksum to verify no rewrite
        pre = requests.get(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}", headers=headers, timeout=30).json()
        pre_wc_content = pre["working_copy"]["content"]
        pre_original_checksum = pre["original"]["checksum"]

        # If already locked from a previous run, skip proof (endpoint 400s)
        if pre.get("editorial_locked"):
            pytest.skip("Edition already locked from prior run; proof cannot be re-run without unlock.")

        r = requests.post(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}/proof", headers=headers, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        rep = data["report"]
        assert rep["counts"]["chapters"] == 11, rep["counts"]
        assert rep["counts"]["words"] > 1000
        # Classifications exist as keys
        for key in ("required", "recommended", "optional", "founder_decision"):
            assert key in rep["counts"]
        assert "unresolved_questions" in rep
        assert isinstance(rep["findings"], list)
        # Voice-not-rewritten proof: fetch again and content must be byte-identical
        post = requests.get(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}", headers=headers, timeout=30).json()
        assert post["working_copy"]["content"] == pre_wc_content, "Proof MUST NOT rewrite content"
        assert post["original"]["checksum"] == pre_original_checksum, "Immutable original checksum must not change"
        assert post["editorial_status"] == "Proofed — awaiting approval"

    def test_design_blocked_before_lock(self, headers, pilot):
        # Only if not yet locked
        cur = requests.get(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}", headers=headers, timeout=30).json()
        if cur.get("editorial_locked"):
            pytest.skip("Already locked from prior run; cannot verify pre-lock 400.")
        r = requests.post(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}/design",
                          headers=headers, json={"base_url": BASE_URL}, timeout=60)
        assert r.status_code == 400, f"Design must 400 before edition lock. Got {r.status_code}: {r.text}"

    def test_approve_and_lock(self, headers, pilot):
        r = requests.post(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}/approve-edition",
                          headers=headers, timeout=30)
        assert r.status_code == 200, r.text
        b = r.json()
        assert b["editorial_locked"] is True
        assert b["editorial_status"] == "Approved & locked"
        ee = b["editorial_edition"]
        assert ee["checksum"] and len(ee["checksum"]) == 64
        assert ee["content"]


# ------------------------------ DESIGN ------------------------------
class TestDesign:
    def test_design_generates_covers_pdf_epub(self, headers, pilot):
        r = requests.post(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}/design",
                          headers=headers, json={"base_url": BASE_URL}, timeout=180)
        assert r.status_code == 200, r.text
        b = r.json()
        d = b["artifacts"]["design"]
        assert len(d["cover_concepts"]) == 3
        for c in d["cover_concepts"]:
            assert c["url"], c
        # Real paperback interior PDF URL
        assert d["print"]["paperback_interior_pdf"], d["print"]
        # EPUB
        assert d["ebook"]["epub"], d["ebook"]

        # Verify PDF asset is reachable
        pdf_url = d["print"]["paperback_interior_pdf"]
        if pdf_url.startswith("/"):
            pdf_url = f"{BASE_URL}{pdf_url}"
        head = requests.get(pdf_url, timeout=60, stream=True)
        assert head.status_code == 200, f"PDF not reachable: {head.status_code}"
        # Read a chunk to check it starts with PDF magic
        chunk = next(head.iter_content(chunk_size=8), b"")
        assert chunk.startswith(b"%PDF"), f"Not a real PDF: {chunk[:8]!r}"

    def test_select_cover(self, headers, pilot):
        r = requests.post(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}/select-cover",
                          headers=headers, json={"concept": 2}, timeout=30)
        assert r.status_code == 200, r.text
        b = r.json()
        assert b["artifacts"]["design"]["selected_cover"]["concept"] == 2


# ------------------------------ HONEST STATES ------------------------------
class TestHonestStates:
    def test_audio_honest(self, headers, pilot):
        r = requests.get(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}/audio", headers=headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "paths" in d
        # Commercial audiobook must NOT report "Ready"/"Published"
        s = d["paths"]["commercial_audiobook"]["state"]
        assert "Guided" in s or "checklist" in s.lower(), s

    def test_video_honest(self, headers, pilot):
        r = requests.get(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}/video", headers=headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("youtube", "tiktok"):
            assert k in d
            assert "Published" not in d[k]["state"]

    def test_publish_gate_not_ready(self, headers, pilot):
        r = requests.get(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}/publish", headers=headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        g = d["final_release_gate"]
        # Even after lock+design+cover, founder_authorization + pricing must be false → gate not ready
        assert g["founder_authorization_received"] is False
        assert g["pricing_approved"] is False
        assert d["gate_ready"] is False, f"Gate must not be ready without founder auth: {g}"
        # Destinations exist; none should report actual success
        assert len(d["destinations"]) >= 5
        for dest in d["destinations"]:
            assert "Published" not in dest["state"]
            assert "Live" not in dest["state"]

    def test_monitor_honest(self, headers, pilot):
        r = requests.get(f"{BASE_URL}/api/book-mfg/books/{pilot['id']}/monitor", headers=headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("retail", "youtube", "tiktok", "audio"):
            assert k in d
            # No fabricated live data
            assert d[k]["state"] in ("No live listings yet", "Not published"), d[k]["state"]


# ------------------------------ AUTHZ ------------------------------
class TestAuthz:
    def test_upload_requires_super_admin(self):
        # Unauthenticated
        r = requests.post(f"{BASE_URL}/api/book-mfg/upload",
                          json={"title": "TEST_x", "content": "## Chapter One\nHello"}, timeout=30)
        assert r.status_code in (401, 403), r.status_code
