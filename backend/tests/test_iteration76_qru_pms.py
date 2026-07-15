"""Iteration 76 — QRU Product Manufacturing System™ QA pass.

Covers:
  * AUTH — founder login (no password change)
  * CONFIG — system_title + 7 buttons + recipes list contains Book
  * UPLOAD — POST /api/book-mfg/upload-file with .txt manuscript → NEW BOOK-000X
  * DESIGN via shared engine — throwaway book cover concepts w/ provenance.design_engine=='QRU Design Studio™'
  * SANITIZATION — cleans (working title)/[TK]/TODO placeholders + release gate honesty
  * KDP CHECKLIST — presence of required fields
  * SHARE + Factory Library — using pilot BOOK-0001 (no state mutation)
  * COVER STUDIO — POST /api/publishing/cover/generate with 2 concepts, provenance + downloadable
  * LITTLE LEGACY — POST /api/little-legacy/episodes from VERIFIED KR returns Verified/Draft (NOT Knowledge Required)

Never runs Proof/Design/Sanitize on the pilot BOOK-0001. Never changes founder password.
"""
import os
import base64
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASS = "QruFounder2026!"

TIMEOUT_LONG = 120
TIMEOUT_STD = 30


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASS},
                      timeout=TIMEOUT_STD)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:300]}"
    d = r.json()
    tok = d.get("access_token") or d.get("token")
    assert tok, f"No token in login response: {d}"
    return tok


@pytest.fixture(scope="session")
def H(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------- AUTH ----
def test_auth_founder_login(token):
    r = requests.get(f"{BASE_URL}/api/auth/me",
                     headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT_STD)
    assert r.status_code == 200
    me = r.json()
    assert me.get("email") == FOUNDER_EMAIL


# ---------------------------------------------------------------- CONFIG ----
def test_config_system_title_and_seven_buttons(H):
    r = requests.get(f"{BASE_URL}/api/book-mfg/config", headers=H, timeout=TIMEOUT_STD)
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    assert d["system_title"] == "QRU Product Manufacturing System™", d["system_title"]
    assert isinstance(d["buttons"], list) and len(d["buttons"]) == 7
    keys = [b["key"] for b in d["buttons"]]
    for k in ("upload", "proof", "design", "audio", "video", "publish", "monitor"):
        assert k in keys, f"Missing {k} in {keys}"
    # 8th? forbidden
    assert len(keys) == 7
    # recipes contains Book
    recs = d.get("recipes") or []
    pts = [r.get("product_type") for r in recs]
    assert "Book" in pts, f"Recipes list missing Book: {pts}"


def test_recipes_endpoint(H):
    r = requests.get(f"{BASE_URL}/api/book-mfg/recipes", headers=H, timeout=TIMEOUT_STD)
    assert r.status_code == 200
    d = r.json()
    assert d["system_title"] == "QRU Product Manufacturing System™"
    assert any(x.get("product_type") == "Book" for x in d.get("recipes", []))


# ---------------------------------------------------------------- UPLOAD ----
def _new_txt_manuscript():
    body = (
        "# TEST_QA_Manuscript (working title)\n\n"
        "By Test Author\n\nA short throwaway manuscript for automated QA.\n\n"
        "## Chapter 1\n\n"
        "This is chapter one of the throwaway TEST_QA book used by the QRU QA suite. "
        "It has enough text to trigger structure detection. TODO: replace with the real chapter. [TK]\n\n"
        "The wind rose over the tree, and the tree remembered every seed it had ever dropped.\n\n"
        "## Chapter 2\n\n"
        "This is chapter two. It exists only to give the intake scan two chapters to see.\n\n"
        "The river carried the stone until the stone learned to float in its own way.\n"
    )
    return base64.b64encode(body.encode("utf-8")).decode("ascii")


@pytest.fixture(scope="session")
def throwaway_book(H):
    payload = {
        "filename": "TEST_QA_Manuscript.txt",
        "file_base64": _new_txt_manuscript(),
        "meta": {
            "title": "TEST_QA Throwaway",
            "author": "QA Bot",
            "genre": "Literary Fiction",
            "audience": "Adult",
            "rights_holder": "QRU Test Estate",
            "ai_disclosure": "Fully test-generated; no human authorship.",
        },
    }
    r = requests.post(f"{BASE_URL}/api/book-mfg/upload-file",
                      headers=H, json=payload, timeout=TIMEOUT_STD)
    assert r.status_code == 200, f"upload-file failed: {r.status_code} {r.text[:400]}"
    b = r.json()
    assert b.get("id"), b
    assert (b.get("book_code") or "").startswith("BOOK-"), b.get("book_code")
    return b


def test_upload_file_creates_new_book(throwaway_book):
    b = throwaway_book
    assert b["title"] == "TEST_QA Throwaway"
    assert b["book_code"].startswith("BOOK-")
    # working copy checksum sealed
    assert b["original"]["immutable"] is True
    assert b["original"]["checksum"]


def test_book_appears_in_list(H, throwaway_book):
    r = requests.get(f"{BASE_URL}/api/book-mfg/books", headers=H, timeout=TIMEOUT_STD)
    assert r.status_code == 200
    ids = [b["id"] for b in r.json()["books"]]
    assert throwaway_book["id"] in ids


# ------------------------------------------------------ DESIGN via engine ----
@pytest.fixture(scope="session")
def designed_book(H, throwaway_book):
    bid = throwaway_book["id"]
    # Proof
    r = requests.post(f"{BASE_URL}/api/book-mfg/books/{bid}/proof",
                      headers=H, timeout=TIMEOUT_STD)
    assert r.status_code == 200, r.text[:300]
    # Approve edition (lock)
    r = requests.post(f"{BASE_URL}/api/book-mfg/books/{bid}/approve-edition",
                      headers=H, timeout=TIMEOUT_STD)
    assert r.status_code == 200, r.text[:300]
    # Design — AI, ~20s. Test ONCE.
    r = requests.post(f"{BASE_URL}/api/book-mfg/books/{bid}/design",
                      headers=H, json={"base_url": BASE_URL}, timeout=TIMEOUT_LONG)
    assert r.status_code == 200, f"design failed: {r.status_code} {r.text[:400]}"
    return r.json()


def test_design_returns_qru_design_studio_concepts(designed_book):
    art = designed_book.get("artifacts", {}).get("design", {})
    concepts = art.get("cover_concepts") or []
    assert len(concepts) == 3, f"Expected 3 concepts, got {len(concepts)}"
    for c in concepts:
        prov = c.get("provenance") or {}
        assert prov.get("design_engine") == "QRU Design Studio™", \
            f"concept {c.get('concept')} provenance={prov}"
        assert c.get("status") in ("success", "failed"), c
    # honest status  — at least one status field per concept
    assert all("status" in c for c in concepts)


# --------------------------------------------------- SELECT COVER + SANITIZE ----
@pytest.fixture(scope="session")
def sanitized_book(H, throwaway_book, designed_book):
    bid = throwaway_book["id"]
    concepts = designed_book["artifacts"]["design"]["cover_concepts"]
    ok = next((c for c in concepts if c["status"] == "success"), None)
    assert ok, "No successful cover concept — cannot select cover"
    r = requests.post(f"{BASE_URL}/api/book-mfg/books/{bid}/select-cover",
                      headers=H, json={"concept": ok["concept"], "base_url": BASE_URL},
                      timeout=TIMEOUT_LONG)
    assert r.status_code == 200, r.text[:400]
    # select-cover auto-runs sanitize per Quiet Factory; but call sanitize explicitly to test route.
    r = requests.post(f"{BASE_URL}/api/book-mfg/books/{bid}/sanitize",
                      headers=H, json={"base_url": BASE_URL}, timeout=TIMEOUT_LONG)
    assert r.status_code == 200, r.text[:400]
    return r.json()


def test_sanitization_removes_placeholders_and_produces_clean_pages(sanitized_book):
    sanit = sanitized_book.get("artifacts", {}).get("sanitization")
    assert sanit, "No sanitization block on book"
    assert sanit["status"] == "Clean retail edition prepared"
    # placeholders detected in TEST_QA manuscript
    assert sanit["placeholders_removed"] >= 1
    # clean pages
    assert sanit.get("title_page") and sanit["title_page"].get("title")
    assert sanit.get("copyright_page") and isinstance(sanit["copyright_page"], list)
    assert sanit.get("colophon") and isinstance(sanit["colophon"], list)
    retail = sanit.get("retail_edition") or {}
    assert retail.get("paperback_interior_pdf"), "No retail PDF"


def test_release_gate_includes_publication_sanitized_and_honest(H, throwaway_book):
    bid = throwaway_book["id"]
    r = requests.get(f"{BASE_URL}/api/book-mfg/books/{bid}/publish",
                     headers=H, timeout=TIMEOUT_STD)
    assert r.status_code == 200
    d = r.json()
    gate = d["final_release_gate"]
    assert "publication_sanitized" in gate
    assert gate["publication_sanitized"] is True
    # honest: pricing_approved + founder_authorization_received still False after design/sanitize
    assert gate["pricing_approved"] is False, "pricing must not be auto-approved"
    assert gate["founder_authorization_received"] is False
    # gate_ready must honestly reflect all values
    assert d["gate_ready"] == all(gate.values()), \
        f"gate_ready dishonest: reported {d['gate_ready']} but gate={gate}"
    assert d["gate_ready"] is False, "gate_ready must be False when pricing+auth pending"


# ------------------------------------------------------ KDP CHECKLIST ----
def test_kdp_checklist_fields_and_statuses(H, throwaway_book):
    r = requests.get(f"{BASE_URL}/api/book-mfg/books/{throwaway_book['id']}/kdp-checklist",
                     headers=H, timeout=TIMEOUT_STD)
    assert r.status_code == 200
    d = r.json()
    fields = d.get("fields") or []
    names = [f["field"] for f in fields]
    for req in ("Book title", "Author / contributor", "ISBN", "Page count",
                "List price", "Book description / blurb", "Cover file (front)"):
        assert req in names, f"KDP checklist missing '{req}': {names}"
    statuses = {f["status"] for f in fields}
    assert statuses.issubset({"confirmed", "suggested", "needs_founder"}), statuses


# ------------------------------------------------------ SHARE + LIBRARY ----
@pytest.fixture(scope="session")
def pilot_book_id(H):
    r = requests.get(f"{BASE_URL}/api/book-mfg/books", headers=H, timeout=TIMEOUT_STD)
    assert r.status_code == 200
    for b in r.json()["books"]:
        if b.get("book_code") == "BOOK-0001":
            return b["id"]
    pytest.skip("Pilot BOOK-0001 not present")


def test_share_pilot_returns_clean_review_copy(H, pilot_book_id):
    # Pilot is already designed + cover selected + sanitized per prior iterations
    r = requests.post(f"{BASE_URL}/api/book-mfg/books/{pilot_book_id}/share",
                      headers=H, json={"hours": 24, "base_url": BASE_URL},
                      timeout=TIMEOUT_LONG)
    assert r.status_code == 200, f"share failed: {r.status_code} {r.text[:400]}"
    d = r.json()
    assert d.get("share_url"), d
    assert d.get("token"), d
    token = d["token"]
    # Resolve share — returns zip
    r2 = requests.get(f"{BASE_URL}/api/book-mfg/share/{token}", timeout=TIMEOUT_LONG)
    assert r2.status_code == 200, f"resolve share: {r2.status_code}"
    assert "zip" in r2.headers.get("content-type", "").lower() \
        or r2.headers.get("content-disposition", "").endswith('.zip"')
    body = r2.content
    assert len(body) > 500
    # sanity: nothing "(working title)" in the raw bytes of readme or contents
    # (may be false-positive if in PDF stream; do a light check)
    assert b"working title" not in body.lower(), \
        "Share zip appears to contain 'working title' string — sanitized edition suspect"


def test_factory_library_contains_share_link(H, pilot_book_id):
    r = requests.get(f"{BASE_URL}/api/book-mfg/books/{pilot_book_id}",
                     headers=H, timeout=TIMEOUT_STD)
    assert r.status_code == 200
    b = r.json()
    links = b.get("share_links") or []
    assert any(sl.get("share_url") for sl in links), \
        f"Factory Library share_links empty for pilot: {links}"


# ------------------------------------------------------ COVER STUDIO ----
def test_cover_studio_generate_ai(H):
    payload = {"title": "TEST_QA Cover Studio",
               "subtitle": "A QA fixture",
               "series": "TEST_QA",
               "concepts": 2, "mode": "ai", "trim": "kdp_ebook"}
    r = requests.post(f"{BASE_URL}/api/publishing/cover/generate",
                      headers=H, json=payload, timeout=TIMEOUT_LONG)
    assert r.status_code == 200, f"cover/generate failed: {r.status_code} {r.text[:400]}"
    d = r.json()
    assert d.get("ok") is True, d
    concepts = d.get("concepts") or []
    assert len(concepts) == 2, f"expected 2 concepts, got {len(concepts)}"
    for c in concepts:
        prov = c.get("provenance") or {}
        assert prov.get("design_engine") == "QRU Design Studio™", \
            f"cover concept provenance not QRU Design Studio: {prov}"
    # file_url loadable
    fu = concepts[0].get("file_url") or concepts[0].get("url")
    assert fu, f"no file_url on cover concept: {concepts[0]}"
    if not fu.startswith("http"):
        fu = BASE_URL + fu
    r2 = requests.get(fu, timeout=TIMEOUT_STD)
    assert r2.status_code == 200, f"cover file not loadable: {r2.status_code}"
    assert len(r2.content) > 1000


# ------------------------------------------------------ LITTLE LEGACY ----
def test_little_legacy_episode_from_verified_kr(H):
    payload = {
        "kr_id": "bfbcbe07-b762-4230-ba67-5b1003e32e8f",
        "title": "TEST_QA — How does the brain work?",
        "age_band": "Emerging Thinkers",
        "featured_character_key": "nova-sparkle",
    }
    r = requests.post(f"{BASE_URL}/api/little-legacy/episodes",
                      headers=H, json=payload, timeout=TIMEOUT_STD)
    assert r.status_code == 200, f"LL episodes failed: {r.status_code} {r.text[:400]}"
    d = r.json()
    assert d.get("ok") is True, d
    assert d.get("verification_status") == "Verified", \
        f"KR was Verified but episode says {d.get('verification_status')} — bug not fixed. Full: {d}"
    assert d.get("status") == "Draft", d
