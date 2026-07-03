"""MT-030 — Customer-Facing Content Filter tests.

Validates that:
  1. PRD-00063 rendered deliverables (HTML, PPTX, PDF) contain NO internal
     production-note phrases and DO contain the real educational content.
  2. render-deliverable response and pipeline endpoint expose
     removed_internal_sections + customer_content_review_required.
  3. filter_customer_content unit strips only internal headings; keeps
     educational sections; raw product content stays untouched in DB.
  4. Publication gate blocks release with 'Customer Content Review Required'
     when leftover internal notes remain (using a DRAFT test product).
  5. Clean product (no internal notes) does NOT get blocked by this specific
     gate.
  6. MT-024/025 regression: HTML+PPTX+PDF present, downloads work with
     attachment Content-Disposition, Treasure-Standard validated.
"""
import io
import os
import re
import sys
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"

# Make the backend package importable for the unit test on filter_customer_content.
sys.path.insert(0, "/app/backend")

PID = "a3a3326e-0046-4681-a13f-38f06ee8fa3a"  # PRD-00063
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

# Internal-note strings that must NEVER appear in any customer-facing rendered file.
INTERNAL_TERMS = [
    "Deck-Wide",
    "Design Guidance",
    "Brand feel",
    "Suggested colors",
    "Footer on every slide",
    "Visual style",
]

# Educational content markers we expect to STILL be present in the rendered files.
EDUCATIONAL_MARKERS_HTML = ["Slide 1", "Sleep", "Takeaways"]


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def token(session):
    r = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD},
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="session")
def auth(session, token):
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _text_of(b: bytes) -> str:
    """Return best-effort UTF-8 text from arbitrary bytes (utf-8 replace)."""
    return b.decode("utf-8", errors="replace")


def _pptx_text(data: bytes) -> str:
    """Extract all text from a PPTX zip: search all XML parts (any string in any slide)."""
    import zipfile

    out = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if name.startswith("ppt/slides/") and name.endswith(".xml"):
                out.append(_text_of(zf.read(name)))
            elif name.endswith(".xml"):
                # Include notes/masters etc. — any leftover internal text anywhere is a bug.
                out.append(_text_of(zf.read(name)))
    return "\n".join(out)


def _pdf_text(data: bytes) -> str:
    """Extract text from PDF. Prefer pypdf if installed; else raw bytes as text."""
    try:
        import pypdf
    except Exception:
        try:
            import PyPDF2 as pypdf  # type: ignore
        except Exception:
            return _text_of(data)
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:
        return _text_of(data)


def _download(auth, url) -> requests.Response:
    if url.startswith("/"):
        url = BASE_URL + url
    return auth.get(url)


# --------------------------------------------------------------------------- #
# 1) Reproduction / Fix on PRD-00063
# --------------------------------------------------------------------------- #
class TestMT030PRD00063:
    def test_render_deliverable_response_contract(self, auth):
        r = auth.post(f"{BASE_URL}/api/manufacturing2/{PID}/render-deliverable")
        assert r.status_code == 200, r.text[:300]
        dv = r.json()
        # required fields
        assert "removed_internal_sections" in dv
        assert "customer_content_review_required" in dv
        assert dv["customer_content_review_required"] is False, (
            f"PRD-00063 should be clean; got leftover={dv.get('leftover_internal_notes')}"
        )
        removed = [s.strip() for s in dv["removed_internal_sections"]]
        assert any("Deck-Wide QRU Design Guidance" in s for s in removed), (
            f"Expected 'Deck-Wide QRU Design Guidance' in removed_internal_sections; got {removed}"
        )
        # deliverable set is complete
        formats = {f["format"] for f in dv["files"]}
        assert {"html", "pdf", "pptx"}.issubset(formats), formats
        assert dv.get("ready") is True

    def test_html_contains_no_internal_terms(self, auth):
        r = auth.post(f"{BASE_URL}/api/manufacturing2/{PID}/render-deliverable")
        dv = r.json()
        html_url = dv.get("preview_url") or next(
            f["url"] for f in dv["files"] if f["format"] == "html"
        )
        resp = _download(auth, html_url)
        assert resp.status_code == 200
        html = resp.text
        low = html.lower()
        for term in INTERNAL_TERMS:
            assert term.lower() not in low, (
                f"HTML customer deliverable STILL contains internal term '{term}'"
            )
        # educational content still present
        for marker in EDUCATIONAL_MARKERS_HTML:
            assert marker.lower() in low, f"HTML missing educational marker '{marker}'"

    def test_pptx_contains_no_internal_terms(self, auth):
        r = auth.post(f"{BASE_URL}/api/manufacturing2/{PID}/render-deliverable")
        dv = r.json()
        pptx_file = next(f for f in dv["files"] if f["format"] == "pptx")
        # download via /api/rendering/asset/{fname}?download=1 (MT-025 opt-in attachment)
        url = f"{BASE_URL}/api/rendering/asset/{pptx_file['filename']}?download=1"
        resp = _download(auth, url)
        assert resp.status_code == 200, resp.status_code
        # Content-Disposition: attachment (when download=1)
        cd = resp.headers.get("Content-Disposition", "")
        assert "attachment" in cd.lower(), cd
        text = _pptx_text(resp.content)
        low = text.lower()
        for term in INTERNAL_TERMS:
            assert term.lower() not in low, (
                f"PPTX customer deliverable contains internal term '{term}'"
            )
        # educational: at least "Sleep" or a slide title marker present
        assert ("sleep" in low) or ("takeaways" in low), "PPTX missing educational content"

    def test_pdf_contains_no_internal_terms(self, auth):
        r = auth.post(f"{BASE_URL}/api/manufacturing2/{PID}/render-deliverable")
        dv = r.json()
        pdf_file = next(f for f in dv["files"] if f["format"] == "pdf")
        url = f"{BASE_URL}/api/rendering/asset/{pdf_file['filename']}?download=1"
        resp = _download(auth, url)
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("Content-Disposition", "").lower()
        text = _pdf_text(resp.content)
        low = text.lower()
        # PDF extraction can be lossy but the exact internal phrases should not exist.
        for term in INTERNAL_TERMS:
            assert term.lower() not in low, (
                f"PDF customer deliverable contains internal term '{term}'"
            )


# --------------------------------------------------------------------------- #
# 2) Pipeline endpoint exposes filter state
# --------------------------------------------------------------------------- #
class TestPipelineEndpoint:
    def test_pipeline_returns_filter_state(self, auth):
        r = auth.get(f"{BASE_URL}/api/manufacturing2/{PID}/pipeline")
        assert r.status_code == 200
        data = r.json()
        assert "customer_content_review_required" in data
        assert "removed_internal_sections" in data
        assert data["customer_content_review_required"] is False
        assert any(
            "Deck-Wide QRU Design Guidance" in s for s in data["removed_internal_sections"]
        ), data["removed_internal_sections"]


# --------------------------------------------------------------------------- #
# 3) Unit: filter_customer_content
# --------------------------------------------------------------------------- #
class TestFilterUnit:
    def test_strips_internal_headings_keeps_educational(self):
        from deliverable_renderer import filter_customer_content, detect_internal_notes

        content = (
            "# Sleep Basics\n"
            "\n"
            "## Slide 1: Overview\n"
            "- Sleep is restorative.\n"
            "\n"
            "## Deck-Wide QRU Design Guidance\n"
            "- Brand feel: calm\n"
            "- Suggested colors: navy, gold\n"
            "- Footer on every slide: QRU\n"
            "\n"
            "## Slide 2: Takeaways\n"
            "- Sleep 7-9 hours.\n"
        )
        clean, removed = filter_customer_content(content)
        assert "Deck-Wide" not in clean
        assert "Design Guidance" not in clean
        assert "Brand feel" not in clean
        assert "Suggested colors" not in clean
        assert "Slide 1" in clean and "Slide 2" in clean and "Takeaways" in clean
        assert any("Deck-Wide" in s for s in removed), removed
        # no leftover detected on the clean output
        assert detect_internal_notes(clean) == []

    def test_strips_various_internal_headings(self):
        from deliverable_renderer import filter_customer_content

        for h in [
            "## Creative Brief",
            "## Manufacturing Note",
            "## Rendering Instruction",
            "## QA Note",
            "## Style Guide",
            "## Brand Guidance",
            "## Art Direction",
        ]:
            content = f"## Kept Section\n- educational\n{h}\n- internal detail\n"
            clean, removed = filter_customer_content(content)
            assert "Kept Section" in clean
            assert "internal detail" not in clean, f"failed to strip '{h}'"
            assert len(removed) == 1

    def test_detects_inline_internal_phrases(self):
        from deliverable_renderer import detect_internal_notes

        # inline phrase not under any heading — must be flagged
        content = "## Slide 1\n- Brand feel: calm\n- Regular educational content."
        found = detect_internal_notes(content)
        assert any("brand feel" in f.lower() for f in found), found

    def test_raw_product_content_unchanged_in_db(self, auth):
        """The DB product.content must still contain the internal section — only
        the rendered deliverable is filtered."""
        # Fetch raw product
        r = auth.get(f"{BASE_URL}/api/products/{PID}")
        assert r.status_code == 200, r.text[:200]
        content = r.json().get("content") or ""
        # The internal heading should STILL exist in the source
        assert "Deck-Wide QRU Design Guidance" in content, (
            "Raw product.content should retain the internal section (filter is render-only)."
        )


# --------------------------------------------------------------------------- #
# 4) Publication gate — DRAFT test product with leftover internal notes
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="class")
def dirty_test_product(auth):
    """Create a draft test product whose content will yield a leftover internal note
    even after heading-filtering (an inline 'Brand feel: ...' bullet not under an
    internal heading, plus a '## Creative Brief' section for good measure).

    We assemble from an existing Verified KR then mutate its content field in
    MongoDB directly (there is no PATCH /api/products/{id} for content)."""
    # Pick any KR to assemble from
    kr_resp = auth.get(f"{BASE_URL}/api/knowledge-records?limit=1")
    krs = kr_resp.json() if isinstance(kr_resp.json(), list) else kr_resp.json().get("records", [])
    assert krs, f"No KRs available to assemble from: {kr_resp.text[:200]}"
    kr_id = krs[0]["id"]

    r = auth.post(
        f"{BASE_URL}/api/products/assemble",
        json={"knowledge_record_id": kr_id, "product_type": "Presentation"},
    )
    assert r.status_code in (200, 201), r.text[:300]
    pid = r.json()["id"]

    dirty_content = (
        "# TEST Deck\n"
        "\n"
        "## Slide 1: Overview\n"
        "- Educational overview line about the fundamentals of this topic and why it matters.\n"
        "- Additional educational context that helps students understand the core concept clearly.\n"
        "- Brand feel: calm and confident\n"  # inline leftover
        "\n"
        "## Slide 2: Takeaways\n"
        "- Educational takeaway that reinforces the learning objective for the customer.\n"
        "- Second takeaway with practical application guidance for real-world usage.\n"
        "\n"
        "## Creative Brief\n"
        "- Internal-only brief detail (heading gets stripped, no leftover).\n"
    )

    # Mutate content directly in Mongo (no HTTP PATCH endpoint exists for content)
    import asyncio
    import motor.motor_asyncio
    from pathlib import Path

    # Load backend .env so MONGO_URL/DB_NAME match server
    env_path = Path("/app/backend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k.strip(), v)
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    assert mongo_url and db_name, f"MONGO_URL/DB_NAME not set: {mongo_url} {db_name}"

    async def _update():
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        res = await client[db_name].products.update_one(
            {"id": pid},
            {"$set": {"content": dirty_content, "title": f"TEST_MT030_dirty_{uuid.uuid4().hex[:6]}"}},
        )
        client.close()
        return res.modified_count

    try:
        modified = asyncio.run(_update())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        modified = loop.run_until_complete(_update())
        loop.close()
    assert modified == 1, f"Failed to update product {pid} content (modified={modified})"

    # Force all release gates to pass so the MT-030 gate is reached in test_release.
    async def _pass_gates():
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        # Import RELEASE_GATES from manufacturing2
        import sys
        sys.path.insert(0, "/app/backend")
        from manufacturing2 import RELEASE_GATES  # type: ignore
        gates = {g: {"status": "passed"} for g in RELEASE_GATES}
        await client[db_name].products.update_one(
            {"id": pid},
            {"$set": {"gates": gates, "deliverable_ready": True, "design_review_required": False}},
        )
        client.close()

    try:
        asyncio.run(_pass_gates())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_pass_gates())
        loop.close()

    # Verify via API that content was updated
    check = auth.get(f"{BASE_URL}/api/products/{pid}").json()
    assert "Creative Brief" in (check.get("content") or ""), (
        f"Content update did not persist: {check.get('content','')[:200]}"
    )

    yield pid
    # cleanup best-effort
    try:
        auth.delete(f"{BASE_URL}/api/products/{pid}")
    except Exception:
        pass


class TestPublicationGate:
    def test_dirty_product_flags_review_and_blocks_release(self, auth, dirty_test_product):
        pid = dirty_test_product
        r = auth.post(f"{BASE_URL}/api/manufacturing2/{pid}/render-deliverable")
        assert r.status_code == 200, r.text[:300]
        dv = r.json()
        # Creative Brief heading should be stripped
        removed_lower = " ".join(dv.get("removed_internal_sections", [])).lower()
        assert "creative brief" in removed_lower, dv.get("removed_internal_sections")
        # Inline 'Brand feel' survives heading-filter → detected as leftover
        assert dv["customer_content_review_required"] is True, dv
        leftover = " ".join(dv.get("leftover_internal_notes") or []).lower()
        assert "brand feel" in leftover, dv.get("leftover_internal_notes")

        # Pipeline echoes the flag
        pipe = auth.get(f"{BASE_URL}/api/manufacturing2/{pid}/pipeline").json()
        assert pipe["customer_content_review_required"] is True

        # Release blocked with the correct message
        rel = auth.post(f"{BASE_URL}/api/manufacturing2/{pid}/release")
        assert rel.status_code == 400, rel.status_code
        detail = (rel.json().get("detail") or "").lower()
        assert "customer content review required" in detail, rel.json()

    def test_clean_product_not_blocked_by_content_gate(self, auth):
        """PRD-00063 is clean → this gate must not fire. Release may still be
        blocked by other gates (design/QC/deliverable), but NOT by our message."""
        rel = auth.post(f"{BASE_URL}/api/manufacturing2/{PID}/release")
        # Whether it succeeds or fails on other gates, this gate must not fire.
        if rel.status_code == 400:
            detail = (rel.json().get("detail") or "").lower()
            assert "customer content review required" not in detail, (
                f"Clean product was blocked by MT-030 gate incorrectly: {rel.json()}"
            )
        else:
            assert rel.status_code in (200, 201), rel.status_code


# --------------------------------------------------------------------------- #
# 5) Regression — MT-024/025 intact
# --------------------------------------------------------------------------- #
class TestRegression:
    def test_deliverable_has_html_pptx_pdf_and_design(self, auth):
        r = auth.post(f"{BASE_URL}/api/manufacturing2/{PID}/render-deliverable")
        dv = r.json()
        formats = {f["format"] for f in dv["files"]}
        assert {"html", "pptx", "pdf"}.issubset(formats)
        # Design review still present + approved (Treasure-Standard)
        assert dv.get("design_review", {}).get("approved") is True, dv.get("design_review")
        assert dv.get("validated") is True

    def test_downloads_return_attachment(self, auth):
        r = auth.post(f"{BASE_URL}/api/manufacturing2/{PID}/render-deliverable")
        dv = r.json()
        # PDF + PPTX must be attachments when ?download=1 is used
        for fmt in ("pdf", "pptx"):
            f = next(x for x in dv["files"] if x["format"] == fmt)
            resp = _download(auth, f"{BASE_URL}/api/rendering/asset/{f['filename']}?download=1")
            assert resp.status_code == 200
            cd = resp.headers.get("Content-Disposition", "").lower()
            assert "attachment" in cd, f"{fmt} missing attachment CD"
            assert len(resp.content) >= 800
