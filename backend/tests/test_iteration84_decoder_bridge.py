"""Iteration 84 — Decoder→Create-Product bridge, generalized (Phase 3).

Founder flow: pick a Manufacturing Ready™ understanding linked to a Verified KR,
create a Workbook and a Teacher Guide via the shared UI/API path, verify the
Publication Quality Standard™ output (Title/Copyright/Colophon, no factory chrome,
Publication Sanitization Pass), verify DB persistence + Knowledge-First linkage,
verify Zero AI/LLM spend, and CLEAN UP the created records so no throwaway data
lingers in the preview DB.
"""
import os
import re
import time
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
EMAIL = "demo.admin@qru.com"
PASSWORD = "qru-demo-admin-2026"

ASSET_DIR = "/app/backend/rendered_assets"

# Terms that indicate factory chrome / unsanitized draft artifacts.
DISALLOWED = [
    "Manufactured by QRU Factory",
    "working title",
    "TODO",
    "TKTK",
    "[PLACEHOLDER]",
    "DRAFT ONLY",
]


# ---------- shared session ----------
@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok, "no access_token in login response"
    return tok


@pytest.fixture(scope="module")
def sess(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# ---------- helpers ----------
def _pick_manufacturing_ready(sess):
    """Prefer DEC-00008 / DEC-00013 as hinted, else first Manufacturing Ready linked to a KR."""
    r = sess.get(f"{BASE}/api/decoder/shelf?state=Manufacturing Ready", timeout=30)
    assert r.status_code == 200, r.text
    decs = r.json().get("decoders", [])
    preferred = {"DEC-00008", "DEC-00013"}
    for d in decs:
        if d.get("decoder_id") in preferred and (d.get("source_kr_ids") or []):
            return d
    for d in decs:
        if d.get("source_kr_ids"):
            return d
    pytest.skip("No Manufacturing Ready decoder linked to a KR is available.")


def _pdf_text(path):
    from pypdf import PdfReader
    reader = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in reader.pages)


# ---------- test state (shared across the ordered test) ----------
CREATED_IDS = []
DECODER = {}
KR_ID = None


# ---------- STEP 1/2: login + pick decoder ----------
def test_00_available_product_types(sess):
    r = sess.get(f"{BASE}/api/decoder/product-types/available", timeout=30)
    assert r.status_code == 200, r.text
    types = r.json().get("product_types", [])
    assert "Workbook" in types and "Teacher Guide" in types and "Book" in types, types


def test_01_pick_decoder(sess):
    global DECODER, KR_ID
    d = _pick_manufacturing_ready(sess)
    DECODER = d
    KR_ID = (d.get("source_kr_ids") or [{}])[0].get("kr_id")
    assert KR_ID, "picked decoder has no source_kr_ids[0].kr_id"
    # Factory Confidence Summary — Knowledge gate must PASS
    rows = (d.get("factory_confidence") or {}).get("rows") or []
    knowledge = next((r for r in rows if r.get("gate") == "Knowledge"), None)
    assert knowledge and knowledge.get("status") == "PASS", f"Knowledge gate not PASS: {knowledge}"


# ---------- STEP 3-8: Workbook end-to-end ----------
@pytest.mark.parametrize("product_type", ["Workbook", "Teacher Guide"])
def test_02_create_and_verify_product(sess, product_type):
    assert DECODER, "decoder not selected"
    did = DECODER["id"]
    decoder_id = DECODER["decoder_id"]

    # capture backend log tail before the call → zero-LLM assertion later
    log_path = "/var/log/supervisor/backend.err.log"
    log_before = 0
    try:
        log_before = os.path.getsize(log_path)
    except OSError:
        log_before = 0

    t0 = time.time()
    r = sess.post(f"{BASE}/api/decoder/{did}/create-product",
                  json={"product_type": product_type}, timeout=120)
    dt = time.time() - t0
    assert r.status_code == 200, f"create-product failed: {r.status_code} {r.text}"
    j = r.json()
    assert j.get("ok") is True
    assert j.get("product_type") == product_type
    assert j.get("engine") == "publication"
    assert j.get("route") == "/products"
    assert j.get("publication_quality_applied") is True
    assert j.get("id"), "no product id in response"
    pid = j["id"]
    CREATED_IDS.append(pid)

    # Deterministic + fast → allow generous ceiling for network
    assert dt < 60, f"create-product too slow ({dt:.1f}s) — suggests LLM call"

    # Zero AI/LLM spend — inspect backend log delta for LLM completion calls
    llm_evidence = ""
    try:
        with open(log_path, "rb") as f:
            f.seek(log_before)
            tail = f.read().decode("utf-8", errors="ignore")
        bad_markers = ["ensure_branded_assets", "openai.com/v1/chat/completions",
                       "generativelanguage.googleapis.com", "anthropic.com/v1/messages",
                       "emergentintegrations.llm", "llm_generate"]
        found = [m for m in bad_markers if m in tail]
        llm_evidence = ", ".join(found)
    except Exception:
        pass
    assert not llm_evidence, f"LLM/AI evidence in backend log during create-product: {llm_evidence}"

    # DB verification via the products API
    pr = sess.get(f"{BASE}/api/products/{pid}", timeout=30)
    assert pr.status_code == 200, pr.text
    p = pr.json()
    assert p.get("verified") is True, f"verified must be true (Knowledge-First); got {p.get('verified')}"
    assert p.get("knowledge_record_id") == KR_ID, (p.get("knowledge_record_id"), KR_ID)
    assert p.get("product_type") == product_type
    src_dec = p.get("source_decoder") or {}
    assert src_dec.get("decoder_id") == decoder_id, src_dec
    files = ((p.get("customer_deliverable") or {}).get("files") or [])
    pdfs = [f for f in files if (f.get("format") or "").lower() == "pdf"]
    assert pdfs, f"no PDF in customer_deliverable.files: {files}"

    # PDF on disk — Publication Quality Standard assertions
    pdf_name = pdfs[0].get("filename") or pdfs[0].get("url", "").split("/")[-1]
    assert pdf_name, f"no pdf filename: {pdfs[0]}"
    pdf_path = os.path.join(ASSET_DIR, pdf_name)
    assert os.path.exists(pdf_path), f"PDF file missing at {pdf_path}"

    text = _pdf_text(pdf_path)
    # (a) Copyright page
    assert re.search(r"copyright", text, re.I), "PDF missing Copyright page"
    # (b) Colophon
    assert re.search(r"colophon", text, re.I), "PDF missing Colophon"
    # (c) Title page — product title appears somewhere near the top
    head = text[:2000]
    title_seed = (DECODER.get("title") or "").split(" — ")[0].strip()
    assert title_seed and title_seed.lower() in head.lower(), \
        f"Title '{title_seed}' not found in PDF head: {head[:400]!r}"
    # (d,e) No factory chrome + Publication Sanitization Pass
    lower = text.lower()
    for bad in DISALLOWED:
        assert bad.lower() not in lower, f"Disallowed marker '{bad}' present in PDF"
    # (f) Content actually derives from the decoded understanding
    seeds = [DECODER.get("definition"), DECODER.get("why_it_matters"), DECODER.get("analogy")]
    seeds = [s for s in seeds if isinstance(s, str) and len(s) > 30]
    hits = 0
    for s in seeds:
        snippet = " ".join(s.split()[:6]).lower()
        if snippet and snippet in lower:
            hits += 1
    assert hits >= 1, "PDF body does not appear derived from the decoder's decoded understanding"


# ---------- STEP 5 confirmation: shelf listing contains the created products ----------
def test_03_products_shelf_lists_created(sess):
    assert CREATED_IDS, "no products were created — earlier steps failed"
    r = sess.get(f"{BASE}/api/products", timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    items = body if isinstance(body, list) else (body.get("products") or body.get("items") or [])
    ids = {p.get("id") for p in items}
    for pid in CREATED_IDS:
        assert pid in ids, f"created product {pid} missing from /api/products shelf"


# ---------- STEP 10: MANDATORY cleanup + confirmation ----------
def test_99_cleanup(sess):
    """Direct MongoDB cleanup — the API has no admin-delete endpoint for products.
    Removes products by id, pulls them from the decoder's manufactured_products list,
    and decrements the source KR's products_created counter (floor 0)."""
    if not CREATED_IDS:
        pytest.skip("nothing to clean up")

    from pymongo import MongoClient
    from dotenv import load_dotenv
    load_dotenv("/app/backend/.env")
    client = MongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    # (a) delete products
    del_res = db.products.delete_many({"id": {"$in": CREATED_IDS}})
    assert del_res.deleted_count == len(CREATED_IDS), \
        f"expected {len(CREATED_IDS)} deletes, got {del_res.deleted_count}"

    # confirm gone
    remaining = list(db.products.find({"id": {"$in": CREATED_IDS}}))
    assert not remaining, f"products still present: {remaining}"

    # (b) $pull from decoder
    did = DECODER.get("id")
    db.decoder_records.update_one({"id": did},
                                  {"$pull": {"manufactured_products": {"product_id": {"$in": CREATED_IDS}}}})
    dec = db.decoder_records.find_one({"id": did}, {"manufactured_products": 1, "_id": 0}) or {}
    lingering = [m for m in (dec.get("manufactured_products") or [])
                 if m.get("product_id") in CREATED_IDS]
    assert not lingering, f"decoder still references created products: {lingering}"

    # (c) decrement KR products_created by N, floor at 0
    if KR_ID:
        kr = db.knowledge_records.find_one({"id": KR_ID}, {"products_created": 1, "_id": 0}) or {}
        current = int(kr.get("products_created") or 0)
        new_val = max(0, current - len(CREATED_IDS))
        db.knowledge_records.update_one({"id": KR_ID}, {"$set": {"products_created": new_val}})
        after = db.knowledge_records.find_one({"id": KR_ID}, {"products_created": 1, "_id": 0}) or {}
        assert (after.get("products_created") or 0) == new_val

    print(f"CLEANUP OK — removed product ids: {CREATED_IDS}")
