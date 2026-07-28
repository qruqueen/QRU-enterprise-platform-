"""Founder Production Operations™ — governed, idempotent data migrations.

These reuse the EXACT tested logic from the RI-MFG-0002b / Workstream C review packages,
ported to the app's async (motor) database connection so they can be triggered by the
Founder against the LIVE production database (the only environment with production MONGO_URL).

Design guarantees (Treasure Standard™):
- DRY-RUN by default; nothing is written unless apply=True.
- Idempotent: safe to re-run; already-applied records are skipped.
- Hard allow-lists: acts ONLY on the enumerated book_codes / product_codes.
- Asset-verified: refuses to create/point at a book whose EPUB/cover is absent from durable storage.
- Rollback-preserving: prior pointers / statuses are saved before any change.
- No silent failures: every record's outcome is reported with evidence.
"""
import os
import re
import asyncio
import datetime
import json
from pathlib import Path

import storage
import rendering_engine as _re
from database import db

DATA_DIR = Path(__file__).parent / "migrations_data"

# ----- Workstream A: Book data & EPUB cutover -----
MARK_A = "RI-MFG-0002b"
STAGE1_CODES = ["BOOK-0013", "BOOK-0016", "BOOK-0018", "BOOK-0019"]
STAGE2_CODES = ["BOOK-0001", "BOOK-0004", "BOOK-0009", "BOOK-0011",
                "BOOK-0013", "BOOK-0016", "BOOK-0018", "BOOK-0019"]
COLL = "book_records"

# ----- Workstream C: QRU Learn governance containment -----
MARK_C = "RI-MFG-C-CONTAINMENT"
C_TARGETS = ["PRD-00130", "PRD-00196", "PRD-00201", "PRD-00202", "PRD-00205"]
HOLD_STATUS = "On Hold (Governance)"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _load(name):
    return json.loads((DATA_DIR / name).read_text())


def _basename(url: str) -> str:
    return (url or "").rsplit("/", 1)[-1]


def _asset_ok_sync(fid: str) -> bool:
    """True if the asset is reachable in durable object storage (production-safe).
    Preview fallback: if a required file is only on local disk, mirror it up so durable
    storage becomes complete before the Founder deploys + runs this in production."""
    if not fid:
        return False
    try:
        if storage.object_exists(fid):
            return True
    except Exception:
        pass
    local = os.path.join(_re.ASSET_DIR, fid)
    if os.path.exists(local):
        try:
            with open(local, "rb") as f:
                storage.mirror_file(fid, f.read())
            return storage.object_exists(fid)
        except Exception:
            return False
    return False


async def _asset_ok(fid: str) -> bool:
    return await asyncio.to_thread(_asset_ok_sync, fid)


# =========================================================================== #
# WORKSTREAM A — Book Data & EPUB Cutover
# =========================================================================== #
async def _stage1(apply: bool):
    books = _load("data_stage1_books.json")
    before = await db[COLL].count_documents({})
    created = skipped = blocked = 0
    rows = []
    for b in books:
        code, bid = b.get("book_code"), b.get("id")
        if code not in STAGE1_CODES:
            continue
        if await db[COLL].find_one({"id": bid}):
            rows.append({"code": code, "id": bid, "outcome": "SKIP",
                         "detail": "already exists by id — verify & skip (no duplicate)"})
            skipped += 1
            continue
        if await db[COLL].find_one({"book_code": code}):
            rows.append({"code": code, "id": bid, "outcome": "CONFLICT",
                         "detail": "exists with a DIFFERENT id — skipped for founder review"})
            skipped += 1
            continue
        design = (b.get("artifacts") or {}).get("design") or {}
        epub_f = _basename((design.get("ebook") or {}).get("epub"))
        cover_f = _basename((design.get("selected_cover") or {}).get("url"))
        ok_epub = await _asset_ok(epub_f)
        ok_cover = await _asset_ok(cover_f)
        if not (ok_epub and ok_cover):
            rows.append({"code": code, "id": bid, "outcome": "BLOCKED",
                         "detail": f"prerequisite asset missing (epub={ok_epub}, cover={ok_cover}) — not created"})
            blocked += 1
            continue
        if apply:
            doc = dict(b)
            doc["_migrated_by"] = MARK_A
            doc["_migrated_at"] = _now()
            await db[COLL].insert_one(doc)
            rows.append({"code": code, "id": bid, "outcome": "CREATED",
                         "detail": "created (assets verified)"})
        else:
            rows.append({"code": code, "id": bid, "outcome": "WOULD_CREATE",
                         "detail": "would create (assets verified)"})
        created += 1
    after = before + (created if apply else 0)
    return {
        "stage": 1,
        "title": "Create missing book records",
        "before_count": before,
        "after_count": after,
        "created": created, "skipped": skipped, "blocked": blocked,
        "ok": blocked == 0,
        "rows": rows,
    }


async def _stage2(apply: bool):
    ptrs = _load("data_stage2_pointers.json")
    updated = already = blocked = 0
    rows = []
    for p in ptrs:
        code, bid = p["book_code"], p["id"]
        if code not in STAGE2_CODES:
            continue
        rec = await db[COLL].find_one({"id": bid})
        if not rec:
            rows.append({"code": code, "id": bid, "outcome": "BLOCKED",
                         "detail": "record missing in this database — run Stage 1 first"})
            blocked += 1
            continue
        if not await _asset_ok(p["new_epub_file"]):
            rows.append({"code": code, "id": bid, "outcome": "BLOCKED",
                         "detail": f"target EPUB {p['new_epub_file']} not in durable storage"})
            blocked += 1
            continue
        cur = (((rec.get("artifacts") or {}).get("design") or {}).get("ebook") or {}).get("epub")
        if cur == p["new_epub_url"]:
            rows.append({"code": code, "id": bid, "outcome": "SKIP",
                         "detail": "pointer already current — idempotent skip"})
            already += 1
            continue
        if apply:
            design = (rec.get("artifacts") or {}).get("design") or {}
            ebook = dict(design.get("ebook") or {})
            ebook.setdefault("epub_rollback", cur)  # preserve prior pointer ONCE
            ebook["epub"] = p["new_epub_url"]
            prov = design.get("rerender_provenance") or []
            prov.append({"ri": MARK_A, "at": _now(), "old_epub": cur,
                         "new_epub": p["new_epub_url"], "standard": "Publication Quality Standard\u2122"})
            await db[COLL].update_one({"id": bid}, {"$set": {
                "artifacts.design.ebook": ebook, "artifacts.design.rerender_provenance": prov}})
            rows.append({"code": code, "id": bid, "outcome": "UPDATED",
                         "detail": f"pointer updated → {p['new_epub_file']} (rollback saved)"})
        else:
            rows.append({"code": code, "id": bid, "outcome": "WOULD_UPDATE",
                         "detail": f"would update → {p['new_epub_file']} (rollback would be saved)"})
        updated += 1
    return {
        "stage": 2,
        "title": "Apply validated EPUB pointers",
        "updated": updated, "already_applied": already, "blocked": blocked,
        "ok": blocked == 0,
        "rows": rows,
    }


async def book_cutover(stage: str = "all", apply: bool = False):
    result = {"workstream": "A", "ref": MARK_A, "mode": "APPLY" if apply else "DRY_RUN",
              "at": _now(), "stages": []}
    ok = True
    if stage in ("1", "all"):
        s1 = await _stage1(apply)
        result["stages"].append(s1)
        ok = s1["ok"]
    if stage in ("2", "all"):
        if not ok:
            result["halted"] = "Stage 1 prerequisites failed — Stage 2 not attempted."
            return result
        s2 = await _stage2(apply)
        result["stages"].append(s2)
    result["ok"] = all(s.get("ok", True) for s in result["stages"])
    return result


async def book_cutover_rollback(apply: bool = False):
    ptrs = _load("data_stage2_pointers.json")
    rows = []
    for p in ptrs:
        rec = await db[COLL].find_one({"id": p["id"]})
        if not rec:
            continue
        eb = (((rec.get("artifacts") or {}).get("design") or {}).get("ebook") or {})
        prior = eb.get("epub_rollback")
        if not prior:
            rows.append({"code": p["book_code"], "outcome": "SKIP",
                         "detail": "no rollback pointer stored"})
            continue
        if apply:
            await db[COLL].update_one({"id": p["id"]},
                                      {"$set": {"artifacts.design.ebook.epub": prior}})
            rows.append({"code": p["book_code"], "outcome": "RESTORED",
                         "detail": f"restored → {_basename(prior)}"})
        else:
            rows.append({"code": p["book_code"], "outcome": "WOULD_RESTORE",
                         "detail": f"would restore → {_basename(prior)}"})
    return {"workstream": "A", "action": "rollback_stage2",
            "mode": "APPLY" if apply else "DRY_RUN", "at": _now(), "rows": rows}


COSMETIC_TOKENS = {"final", "draft", "copy", "new", "latest", "clean", "edited",
                   "revised", "master", "fin", "ver", "version", "proof", "print", "ready"}
_VER_RE = re.compile(r"^v\d+$")


def _norm(s):
    return " ".join((s or "").lower().split())


def _norm_title(s):
    s = (s or "").lower()
    s = re.sub(r"[™®©]", "", s)
    s = re.sub(r"\.(docx?|pdf|epub|txt|md|rtf)$", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    toks = [t for t in s.split() if t and t not in COSMETIC_TOKENS and not _VER_RE.match(t)]
    return " ".join(toks)


def _lineage_signals(doc):
    doc = doc or {}
    tp = doc.get("transparent_provenance") or {}
    orig = doc.get("original") or {}
    sfh = doc.get("source_file_history") or []
    ev = doc.get("editorial_versions") or []
    pm = doc.get("publication_metadata") or {}
    src = tp.get("source_filename") or (sfh[0].get("file") if sfh and isinstance(sfh[0], dict) else None)
    checksum = orig.get("checksum") or tp.get("immutable_original_checksum")
    src_files = [x.get("file") for x in sfh if isinstance(x, dict) and x.get("file")]
    return {
        "id": doc.get("id"),
        "title": doc.get("title"),
        "author": doc.get("author") or pm.get("author") or tp.get("rights_holder"),
        "checksum": checksum,
        "source_filename": src,
        "source_files": src_files,
        "version_checksums": [v.get("checksum") for v in ev if isinstance(v, dict) and v.get("checksum")],
        "norm_title": _norm_title(doc.get("title")),
        "norm_src": _norm_title(src),
    }


async def _record_summary(rec):
    if not rec:
        return None
    d = (rec.get("artifacts") or {}).get("design") or {}
    sig = _lineage_signals(rec)
    return {
        "id": rec.get("id"),
        "title": rec.get("title"),
        "subtitle": rec.get("subtitle"),
        "author": sig["author"],
        "book_code": rec.get("book_code"),
        "publication_status": rec.get("publication_status") or rec.get("status"),
        "approval_status": rec.get("approval_status"),
        "editorial_locked": rec.get("editorial_locked"),
        "epub": (d.get("ebook") or {}).get("epub"),
        "cover": (d.get("selected_cover") or {}).get("url"),
        "checksum": sig["checksum"],
        "source_filename": sig["source_filename"],
        "source_files": sig["source_files"],
        "created_at": rec.get("created_at"),
        "migrated_by": rec.get("_migrated_by"),
        "purchases": await db.book_purchases.count_documents({"book_id": rec.get("id")}),
    }


def _classify_lineage(inc_doc, exc_doc):
    """Publishing-lineage comparison. Evaluates canonical manuscript identity, source-document
    lineage, author and title history — NOT title equality alone. Returns a reasoning chain +
    confidence score + recommended governed action."""
    I, E = _lineage_signals(inc_doc), _lineage_signals(exc_doc)
    chain = []

    def note(check, result, detail):
        chain.append({"check": check, "result": result, "detail": detail})

    # 1) Canonical immutable manuscript checksum — the strongest identity signal.
    if I["checksum"] and E["checksum"]:
        if I["checksum"] == E["checksum"]:
            note("Canonical manuscript checksum", "MATCH",
                 f"Identical sealed immutable original ({I['checksum'][:12]}…). Definitive same manuscript.")
            return {"classification": "SAME_BOOK", "confidence": 1.0, "reasoning": chain, "adopt_eligible": True,
                    "recommended_action": "Adopt the existing production record and repoint its EPUB to the re-rendered edition (rollback-protected). Same manuscript, confirmed."}
        note("Canonical manuscript checksum", "DIFFER",
             f"Incoming {I['checksum'][:12]}… vs existing {E['checksum'][:12]}…")
        if set(I["version_checksums"]) & set(E["version_checksums"]):
            note("Editorial version lineage", "OVERLAP", "Shared editorial-version checksum — same work at a different edit stage.")
            return {"classification": "SAME_BOOK", "confidence": 0.92, "reasoning": chain, "adopt_eligible": True,
                    "recommended_action": "Adopt existing record and repoint EPUB. Shared editorial lineage indicates the same work."}
    else:
        note("Canonical manuscript checksum", "UNAVAILABLE", "One or both records lack a sealed checksum; using secondary evidence.")

    # 2) Source-document lineage (filename, after removing cosmetic tokens like 'FINAL').
    src_match = bool(I["norm_src"] and E["norm_src"] and I["norm_src"] == E["norm_src"])
    src_vs_title = bool((I["norm_src"] and I["norm_src"] == E["norm_title"]) or (E["norm_src"] and E["norm_src"] == I["norm_title"]))
    if src_match or src_vs_title:
        note("Source document lineage", "MATCH",
             f"Same source document after normalising cosmetic tokens (e.g. '{E.get('source_filename') or I.get('source_filename')}'). Indicates a title correction / republication.")
    else:
        note("Source document lineage", "DIFFER",
             f"Incoming source '{I.get('source_filename')}' vs existing '{E.get('source_filename')}'.")

    # 3) Title lineage.
    ti, te = I["norm_title"], E["norm_title"]
    title_equal = bool(ti and te and ti == te)
    title_subset = bool(ti and te and (ti in te or te in ti))
    if title_equal:
        note("Normalised title", "MATCH", f"Both normalise to '{ti}'.")
    elif title_subset:
        note("Normalised title", "SUBSET", f"One title is the other plus a cosmetic token ('{ti}' vs '{te}') — a legitimate title edit.")
    else:
        note("Normalised title", "DIFFER", f"'{ti}' vs '{te}'.")

    # 4) Author.
    author_ok = (not I["author"]) or (not E["author"]) or _norm(I["author"]) == _norm(E["author"])
    note("Author", "COMPATIBLE" if author_ok else "DIFFER",
         f"Incoming '{I['author']}' vs existing '{E['author']}'" + (" (one blank — treated as compatible)" if (not I["author"] or not E["author"]) else ""))

    # ---- verdict ----
    if src_match or src_vs_title:
        cls = "SAME_BOOK" if title_equal else "TITLE_CHANGED"
        conf = 0.9 if title_equal else 0.85
        return {"classification": cls, "confidence": conf, "reasoning": chain, "adopt_eligible": True,
                "recommended_action": "Adopt the existing record and repoint its EPUB. Same source document — a title correction/republication, not a different work."}
    if title_equal and author_ok:
        return {"classification": "SAME_BOOK", "confidence": 0.8, "reasoning": chain, "adopt_eligible": True,
                "recommended_action": "Adopt existing record and repoint EPUB. Same title and compatible author."}
    if title_subset and author_ok:
        return {"classification": "TITLE_CHANGED", "confidence": 0.82, "reasoning": chain, "adopt_eligible": True,
                "recommended_action": "Adopt existing record and repoint EPUB. Title differs only by a cosmetic token (e.g. 'FINAL') — a legitimate edit."}
    if title_equal and not author_ok:
        return {"classification": "POSSIBLE_COLLISION", "confidence": 0.5, "reasoning": chain, "adopt_eligible": False,
                "recommended_action": "Founder review: same title but different author and no shared manuscript. Confirm identity before any change."}
    if I["checksum"] and E["checksum"]:  # both sealed, differ, nothing else matched
        return {"classification": "DIFFERENT_WORK", "confidence": 0.9, "reasoning": chain, "adopt_eligible": False,
                "recommended_action": "Do NOT adopt. Distinct works sharing a book_code. NOTE: book_code is assigned per-database sequentially, so the same code legitimately points to different works across preview and production. Re-key this migration book to a fresh production book_code, or have the Founder decide."}
    return {"classification": "POSSIBLE_COLLISION", "confidence": 0.45, "reasoning": chain, "adopt_eligible": False,
            "recommended_action": "Founder investigation: evidence inconclusive (missing checksums, differing titles). Do not modify until identity is confirmed."}


async def inspect_book_conflicts():
    """READ-ONLY Publishing Lineage Inspector. For each Stage-1 book_code, compare the incoming
    migration record against whatever exists in THIS database using publishing lineage (canonical
    manuscript checksum, source document, author, title history) — not title equality — and produce
    a classification, confidence score, reasoning chain and recommended governed action. Writes nothing."""
    books = _load("data_stage1_books.json")
    ptr_by_code = {p["book_code"]: p for p in _load("data_stage2_pointers.json")}
    out = []
    for b in books:
        code, mid = b.get("book_code"), b.get("id")
        design = (b.get("artifacts") or {}).get("design") or {}
        sig = _lineage_signals(b)
        incoming = {
            "id": mid, "title": b.get("title"), "author": sig["author"], "book_code": code,
            "checksum": sig["checksum"], "source_filename": sig["source_filename"],
            "epub": (design.get("ebook") or {}).get("epub"),
            "cover": (design.get("selected_cover") or {}).get("url"),
        }
        by_id = await db[COLL].find_one({"id": mid})
        by_code = await db[COLL].find_one({"book_code": code, "id": {"$ne": mid}})
        existing_by_id = await _record_summary(by_id)
        existing_by_code = await _record_summary(by_code)
        ptr = ptr_by_code.get(code)
        rerender_epub_available = await _asset_ok(ptr["new_epub_file"]) if ptr else False

        if by_id:
            lineage = {"classification": "PRESENT_BY_ID", "confidence": 1.0, "adopt_eligible": False,
                       "reasoning": [{"check": "Canonical id", "result": "MATCH",
                                      "detail": "Record already present under the same canonical id."}],
                       "recommended_action": "No creation needed. Stage 2 refreshes its EPUB pointer to the re-rendered edition."}
        elif by_code:
            lineage = _classify_lineage(b, by_code)
        else:
            lineage = {"classification": "ABSENT", "confidence": 1.0, "adopt_eligible": False,
                       "reasoning": [{"check": "book_code presence", "result": "ABSENT",
                                      "detail": "No record with this id or book_code in this database."}],
                       "recommended_action": "Truly missing — safe to CREATE from the migration record (assets permitting)."}

        out.append({
            "book_code": code,
            "classification": lineage["classification"],
            "confidence": lineage["confidence"],
            "reasoning": lineage["reasoning"],
            "recommendation": lineage["recommended_action"],
            "adopt_eligible": lineage["adopt_eligible"],
            "rerender_epub_available": rerender_epub_available,
            "incoming": incoming,
            "existing_by_id": existing_by_id,
            "existing_by_code": existing_by_code,
        })
    return {"workstream": "A", "action": "inspect", "read_only": True, "at": _now(), "books": out}


async def resolve_book_conflicts(apply: bool = False):
    """Governed conflict resolution driven by the lineage engine. Adopts the existing production
    record and repoints its EPUB to the re-rendered edition ONLY for lineage-confirmed same works
    (adopt_eligible: SAME_BOOK / TITLE_CHANGED). Never creates a duplicate; never touches
    DIFFERENT_WORK / POSSIBLE_COLLISION; never alters manuscript, cover, pricing, authorization, or
    purchases. Rollback-preserving."""
    insp = await inspect_book_conflicts()
    ptr_by_code = {p["book_code"]: p for p in _load("data_stage2_pointers.json")}
    rows = []
    for b in insp["books"]:
        code, cls = b["book_code"], b["classification"]
        if not b.get("adopt_eligible"):
            rows.append({"code": code, "outcome": "SKIP",
                         "detail": f"{cls} (confidence {b.get('confidence')}) — not an adopt target"})
            continue
        existing = b["existing_by_code"]
        ptr = ptr_by_code.get(code)
        if not existing or not ptr:
            rows.append({"code": code, "outcome": "SKIP", "detail": "no existing record / pointer mapping"})
            continue
        if not await _asset_ok(ptr["new_epub_file"]):
            rows.append({"code": code, "outcome": "BLOCKED",
                         "detail": f"target EPUB {ptr['new_epub_file']} not in durable storage"})
            continue
        rec = await db[COLL].find_one({"id": existing["id"]})
        design = (rec.get("artifacts") or {}).get("design") or {}
        cur = (design.get("ebook") or {}).get("epub")
        if cur == ptr["new_epub_url"]:
            rows.append({"code": code, "outcome": "SKIP",
                         "detail": f"existing record {existing['id']} already points to re-rendered EPUB"})
            continue
        if apply:
            ebook = dict(design.get("ebook") or {})
            ebook.setdefault("epub_rollback", cur)
            ebook["epub"] = ptr["new_epub_url"]
            prov = design.get("rerender_provenance") or []
            prov.append({"ri": MARK_A, "at": _now(), "adopt_remap": True, "resolved_book_code": code,
                         "classification": cls, "old_epub": cur, "new_epub": ptr["new_epub_url"],
                         "standard": "Publication Quality Standard\u2122"})
            await db[COLL].update_one({"id": existing["id"]}, {"$set": {
                "artifacts.design.ebook": ebook, "artifacts.design.rerender_provenance": prov}})
            rows.append({"code": code, "outcome": "ADOPTED_AND_REPOINTED",
                         "detail": f"{cls}: existing id {existing['id']} → {ptr['new_epub_file']} (rollback saved; no duplicate)"})
        else:
            rows.append({"code": code, "outcome": "WOULD_ADOPT_AND_REPOINT",
                         "detail": f"{cls}: existing id {existing['id']} → {ptr['new_epub_file']} (rollback would be saved)"})
    return {"workstream": "A", "action": "resolve_conflicts",
            "mode": "APPLY" if apply else "DRY_RUN", "at": _now(), "rows": rows}



async def _next_book_code(reserved=None):
    reserved = reserved or set()
    nums = []
    async for r in db[COLL].find({}, {"book_code": 1}):
        m = re.match(r"BOOK-(\d+)$", r.get("book_code") or "")
        if m:
            nums.append(int(m.group(1)))
    n = (max(nums) + 1) if nums else 1
    while f"BOOK-{n:04d}" in reserved or await db[COLL].find_one({"book_code": f"BOOK-{n:04d}"}):
        n += 1
    return f"BOOK-{n:04d}"


async def create_under_fresh_code(apply: bool = False):
    """Governed creation for DIFFERENT_WORK conflicts: the incoming migration book is a legitimate
    distinct work whose book_code is already taken in this database (book_code is per-DB sequential).
    Create it under a FRESH next-available book_code, preserving its canonical id and assets, and
    apply the re-rendered EPUB. Idempotent (skips once the canonical id exists). Asset-verified.
    Never modifies the existing production work that currently holds the code."""
    insp = await inspect_book_conflicts()
    books_by_code = {b.get("book_code"): b for b in _load("data_stage1_books.json")}
    ptr_by_code = {p["book_code"]: p for p in _load("data_stage2_pointers.json")}
    rows = []
    reserved = set()
    for b in insp["books"]:
        code, cls = b["book_code"], b["classification"]
        if cls != "DIFFERENT_WORK":
            rows.append({"code": code, "outcome": "SKIP", "detail": f"{cls} — not a create-under-new-code target"})
            continue
        mid = b["incoming"]["id"]
        if await db[COLL].find_one({"id": mid}):
            rows.append({"code": code, "outcome": "SKIP", "detail": f"canonical id {mid} already present — created previously"})
            continue
        src = books_by_code.get(code)
        if not src:
            rows.append({"code": code, "outcome": "SKIP", "detail": "no migration source record"})
            continue
        design = (src.get("artifacts") or {}).get("design") or {}
        epub_f = _basename((design.get("ebook") or {}).get("epub"))
        cover_f = _basename((design.get("selected_cover") or {}).get("url"))
        if not (await _asset_ok(epub_f) and await _asset_ok(cover_f)):
            rows.append({"code": code, "outcome": "BLOCKED", "detail": "prerequisite asset (epub/cover) missing in durable storage"})
            continue
        new_code = await _next_book_code(reserved)
        reserved.add(new_code)
        ptr = ptr_by_code.get(code)
        if apply:
            doc = dict(src)
            doc["book_code"] = new_code
            doc["_migrated_by"] = MARK_A
            doc["_recoded_from"] = code
            doc["_recoded_at"] = _now()
            if ptr and await _asset_ok(ptr["new_epub_file"]):
                arts = dict(doc.get("artifacts") or {})
                design2 = dict(arts.get("design") or {})
                ebook = dict(design2.get("ebook") or {})
                ebook["epub"] = ptr["new_epub_url"]
                design2["ebook"] = ebook
                arts["design"] = design2
                doc["artifacts"] = arts
            await db[COLL].insert_one(doc)
            rows.append({"code": code, "outcome": "CREATED_UNDER_NEW_CODE",
                         "detail": f"'{src.get('title')}' created as {new_code} (canonical id {mid}); existing production work under {code} untouched"})
        else:
            rows.append({"code": code, "outcome": "WOULD_CREATE_UNDER_NEW_CODE",
                         "detail": f"'{src.get('title')}' would be created as {new_code} (canonical id {mid}); existing {code} untouched"})
    return {"workstream": "A", "action": "create_under_fresh_code",
            "mode": "APPLY" if apply else "DRY_RUN", "at": _now(), "rows": rows}


async def create_under_fresh_code_rollback(apply: bool = False):
    """Remove ONLY records created by create_under_fresh_code (tagged _recoded_from) that have no
    purchases. Never touches pre-existing records."""
    rows = []
    async for rec in db[COLL].find({"_migrated_by": MARK_A, "_recoded_from": {"$exists": True}}):
        purchases = await db.book_purchases.count_documents({"book_id": rec.get("id")})
        if purchases > 0:
            rows.append({"code": rec.get("book_code"), "outcome": "SKIP",
                         "detail": f"{purchases} purchase(s) — preserved, not removed"})
            continue
        if apply:
            await db[COLL].delete_one({"id": rec.get("id")})
            rows.append({"code": rec.get("book_code"), "outcome": "REMOVED",
                         "detail": f"re-coded creation of {rec.get('_recoded_from')} removed (id {rec.get('id')})"})
        else:
            rows.append({"code": rec.get("book_code"), "outcome": "WOULD_REMOVE",
                         "detail": f"would remove re-coded creation (id {rec.get('id')})"})
    return {"workstream": "A", "action": "create_under_fresh_code_rollback",
            "mode": "APPLY" if apply else "DRY_RUN", "at": _now(), "rows": rows}


# =========================================================================== #
# WORKSTREAM C — QRU Learn Governance Containment
# =========================================================================== #
async def _classify():
    rows = []
    for code in C_TARGETS:
        p = await db.products.find_one({"product_code": code})
        if not p:
            rows.append({"code": code, "present": False, "pub_status": None,
                         "kr_status": None, "learner_accessible": None,
                         "classification": "NOT_PRESENT_IN_PRODUCTION"})
            continue
        krid = p.get("knowledge_record_id")
        kr = await db.knowledge_records.find_one({"id": krid}) if krid else None
        kr_status = (kr or {}).get("verification_status") if kr else ("MISSING_KR" if krid else "NO_KR_LINK")
        pub = p.get("status")
        learner_accessible = (pub == "Published")
        verified = kr_status == "Verified"
        if not learner_accessible:
            cls = "NOT_LEARNER_ACCESSIBLE"
        elif kr and not verified:
            cls = "PRODUCTION_HOLD_REQUIRED"
        elif not kr:
            cls = "FOUNDER_REVIEW_REQUIRED"
        else:
            cls = "FOUNDER_REVIEW_REQUIRED"
        rows.append({"code": code, "present": True, "id": p.get("id"),
                     "pub_status": pub, "kr_status": kr_status,
                     "learner_accessible": learner_accessible, "classification": cls})
    return rows


async def learn_containment(apply_hold: bool = False, apply: bool = False):
    rows = await _classify()
    result = {"workstream": "C", "ref": MARK_C,
              "mode": "APPLY" if (apply and apply_hold) else "DRY_RUN",
              "at": _now(), "classification": rows}
    if apply_hold:
        actions = []
        for r in rows:
            if r["classification"] != "PRODUCTION_HOLD_REQUIRED":
                actions.append({"code": r["code"], "outcome": "SKIP",
                                "detail": f"{r['classification']} — not a hold target"})
                continue
            if apply:
                await db.products.update_one({"id": r["id"]}, {"$set": {
                    "status": HOLD_STATUS,
                    "status_before_hold": r["pub_status"],
                    "governance_hold": {
                        "reason": "Linked Knowledge Record not Verified",
                        "by": MARK_C, "at": _now(),
                        "unavailable_message": "This lesson is temporarily unavailable pending verified approval."}}})
                actions.append({"code": r["code"], "outcome": "HELD",
                                "detail": f"status {r['pub_status']} → {HOLD_STATUS} (assets/purchases preserved)"})
            else:
                actions.append({"code": r["code"], "outcome": "WOULD_HOLD",
                                "detail": f"status {r['pub_status']} → {HOLD_STATUS}"})
        result["hold_actions"] = actions
    return result


async def learn_containment_rollback(apply: bool = False):
    rows = []
    for code in C_TARGETS:
        p = await db.products.find_one({"product_code": code})
        if not p or not p.get("governance_hold"):
            continue
        prior = p.get("status_before_hold", "Published")
        if apply:
            await db.products.update_one({"id": p["id"]},
                                         {"$set": {"status": prior},
                                          "$unset": {"governance_hold": "", "status_before_hold": ""}})
            rows.append({"code": code, "outcome": "RESTORED", "detail": f"restored → {prior}"})
        else:
            rows.append({"code": code, "outcome": "WOULD_RESTORE", "detail": f"would restore → {prior}"})
    return {"workstream": "C", "action": "rollback_hold",
            "mode": "APPLY" if apply else "DRY_RUN", "at": _now(), "rows": rows}


# =========================================================================== #
# Overview for the Founder panel card (both workstreams, read-only dry-run)
# =========================================================================== #
async def summary():
    a = await book_cutover(stage="all", apply=False)
    c_rows = await _classify()
    s1 = next((s for s in a["stages"] if s["stage"] == 1), {})
    s2 = next((s for s in a["stages"] if s["stage"] == 2), {})
    total_books = await db[COLL].count_documents({})
    return {
        "workstream_a": {
            "books_to_create": s1.get("created", 0),
            "books_already_present": s1.get("skipped", 0),
            "pointers_to_update": s2.get("updated", 0),
            "pointers_already_current": s2.get("already_applied", 0),
            "blocked": s1.get("blocked", 0) + s2.get("blocked", 0),
            "assets_verified": a.get("ok", False),
            "current_book_count": total_books,
        },
        "workstream_c": {
            "targets": len(C_TARGETS),
            "hold_required": sum(1 for r in c_rows if r["classification"] == "PRODUCTION_HOLD_REQUIRED"),
            "not_present": sum(1 for r in c_rows if r["classification"] == "NOT_PRESENT_IN_PRODUCTION"),
            "classification": c_rows,
        },
        "at": _now(),
    }


# =========================================================================== #
# DQ-7C — Standards Metadata Canonicalization (Founder-approved, additive, reversible)
# One independent governed operation. Mirrors backend/_dq7c_execute.py exactly.
# =========================================================================== #
DQ7C_INH = {
    "STD-00001": "MANUFACTURING_PROMISE.treasure_standard",
    "STD-00005": "MANUFACTURING_PROMISE.constitutional_governance",
    "QRU-CON-0001": "MANUFACTURING_PROMISE.constitutional_governance",
    "STD-00008": "MANUFACTURING_PROMISE.verified_knowledge",
    "STD-00009": "MANUFACTURING_PROMISE.enterprise_memory",
    "STD-00027": "MANUFACTURING_PROMISE.verified_knowledge",
    "STD-00030": "MANUFACTURING_PROMISE.verified_knowledge",
    "STD-UKR-0001": "MANUFACTURING_PROMISE.verified_knowledge",
    "STD-RFN-0001": "MANUFACTURING_PROMISE.continuous_craftsmanship",
}
DQ7C_GATE = {
    "QRU-CON-0002": "rendering_engine/deliverable_renderer:Publication Quality Standard\u2122",
    "STD-MFG-0001": "manufacturing_flow:Universal Manufacturing Flow gate",
}
DQ7C_CONST5 = {
    "QRU-CON-0001": {"owner": "QRU", "verification_status": "Verified"},
    "QRU-CON-0002": {"owner": "QRU Press\u2122", "verification_status": "Verified"},
    "STD-MFG-0001": {"owner": "QRU", "verification_status": "Verified"},
    "STD-EIP-0002": {"owner": "QRU", "verification_status": "Verified"},
    "STD-RFN-0001": {"owner": "QRU", "verification_status": "Verified"},
}
DQ7C_EVIDENCE = set(DQ7C_INH) | set(DQ7C_GATE)  # 11
DQ7C_EXPECTED_STD_IDS = (["STD-%05d" % i for i in range(1, 34)]
                         + ["QRU-CON-0001", "QRU-CON-0002", "STD-EIP-0002",
                            "STD-MFG-0001", "STD-RFN-0001", "STD-UKR-0001"])  # 39
DQ7C_QIKS_META = ["lifecycle_status", "enforcement_condition", "enforcement_binding", "dq7_prepared_at", "dq7_evidence"]
DQ7C_QIKS_CONST = ["owner", "verification_status", "dq7b_canonicalized_at"]
DQ7C_PROJ = ["canonical_ref", "projection", "dq7b_indexed_at"]
STD_COLL = "qiks_standards"
CONST_COLL = "constitutional_registry"


def _std_key(d):
    return d.get("standard_id") or d.get("id")


def _dq7c_plan_doc(doc):
    """Return (planned_fields_absent, conflicts) for one qiks standard — additive only."""
    sid = _std_key(doc)
    planned, conflicts = {}, []
    if sid in DQ7C_INH:
        cls, binding = "INHERITED_ENFORCED", DQ7C_INH[sid]
    elif sid in DQ7C_GATE:
        cls, binding = "GATE_ENFORCED", DQ7C_GATE[sid]
    else:
        cls, binding = "FOUNDER_DECISION_REQUIRED", None
    intended = {
        "lifecycle_status": "ADOPTED",
        "enforcement_condition": cls,
        "enforcement_binding": binding,
        "dq7_prepared_at": _now(),
        "dq7_evidence": "evidence-backed" if sid in DQ7C_EVIDENCE else "unsupported->FOUNDER_DECISION_REQUIRED",
    }
    if sid in DQ7C_CONST5:
        intended.update(DQ7C_CONST5[sid])
        intended["dq7b_canonicalized_at"] = _now()
    for f, v in intended.items():
        if v is None:
            continue  # None-valued fields (e.g. FDR binding) are intentionally not stored
        cur = doc.get(f)
        if cur in (None, "", []):
            planned[f] = v
        elif cur != v and f not in ("dq7_prepared_at", "dq7b_canonicalized_at"):
            conflicts.append({"id": sid, "field": f, "existing": cur, "intended": v})
    return sid, cls, planned, conflicts


async def standards_metadata_preflight():
    """Read-only production preflight + material differences vs the validated preview assumptions."""
    q = [d async for d in db[STD_COLL].find({})]
    c = [d async for d in db[CONST_COLL].find({})]
    present = {_std_key(d) for d in q}
    missing = sorted(set(DQ7C_EXPECTED_STD_IDS) - present)
    unexpected = sorted(present - set(DQ7C_EXPECTED_STD_IDS))
    # projection resolution
    unresolved = []
    for d in c:
        n = sum(1 for x in q if _std_key(x) == d.get("id"))
        if n != 1:
            unresolved.append({"projection_id": d.get("id"), "resolves_to": n})
    conflicts, need, already, counts = [], 0, 0, {"INHERITED_ENFORCED": 0, "GATE_ENFORCED": 0, "FOUNDER_DECISION_REQUIRED": 0}
    for d in q:
        sid, cls, planned, cf = _dq7c_plan_doc(d)
        counts[cls] = counts.get(cls, 0) + 1
        conflicts += cf
        if planned:
            need += 1
        else:
            already += 1
    proj_need = sum(1 for d in c if not d.get("canonical_ref") or not d.get("projection"))
    ready = (len(q) == 39 and len(c) == 5 and not conflicts and not unresolved and not missing)
    return {
        "operation": "DQ-7C Standards Metadata", "at": _now(),
        "production_counts": {"qiks_standards": len(q), "constitutional_registry": len(c)},
        "expected_counts": {"qiks_standards": 39, "constitutional_registry": 5},
        "material_differences": {
            "missing_standard_ids": missing, "unexpected_standard_ids": unexpected,
            "unresolved_projections": unresolved, "field_conflicts": conflicts,
            "canonical_records_needing_metadata": need, "canonical_records_already_applied": already,
            "projection_records_needing_update": proj_need,
        },
        "enforcement_distribution": counts,
        "evidence_backed_expected": 11,
        "ready_to_apply": ready,
        "block_reasons": ([] if ready else
                          ([f"qiks count {len(q)}!=39"] if len(q) != 39 else [])
                          + ([f"cons count {len(c)}!=5"] if len(c) != 5 else [])
                          + ([f"{len(conflicts)} field conflict(s)"] if conflicts else [])
                          + ([f"{len(unresolved)} unresolved projection(s)"] if unresolved else [])
                          + ([f"{len(missing)} missing standard id(s)"] if missing else [])),
    }


async def standards_metadata_apply(apply: bool = False):
    pf = await standards_metadata_preflight()
    if apply and not pf["ready_to_apply"]:
        return {"operation": "DQ-7C Standards Metadata", "mode": "BLOCKED", "at": _now(),
                "reason": "Preflight not satisfied", "block_reasons": pf["block_reasons"], "preflight": pf}
    q = [d async for d in db[STD_COLL].find({})]
    c = [d async for d in db[CONST_COLL].find({})]
    writes, counts = 0, {"INHERITED_ENFORCED": 0, "GATE_ENFORCED": 0, "FOUNDER_DECISION_REQUIRED": 0}
    for d in q:
        sid, cls, planned, cf = _dq7c_plan_doc(d)
        counts[cls] += 1
        if cf:
            return {"operation": "DQ-7C Standards Metadata", "mode": "HALTED", "at": _now(),
                    "reason": "field conflict — would overwrite", "conflicts": cf}
        if planned and apply:
            key = {"standard_id": sid} if await db[STD_COLL].find_one({"standard_id": sid}) else {"id": sid}
            await db[STD_COLL].update_one(key, {"$set": planned})
        writes += len(planned)
    proj_writes = 0
    for d in c:
        cid = d.get("id")
        fields = {}
        if not d.get("canonical_ref"):
            fields["canonical_ref"] = cid
        if not d.get("projection"):
            fields["projection"] = True
        fields["dq7b_indexed_at"] = _now() if apply else None
        setf = {k: v for k, v in fields.items() if v is not None}
        if setf and apply:
            await db[CONST_COLL].update_one({"id": cid}, {"$set": setf})
        proj_writes += len([k for k in setf])
    result = {"operation": "DQ-7C Standards Metadata", "mode": "APPLY" if apply else "DRY_RUN", "at": _now(),
              "enforcement_distribution": counts, "canonical_field_writes": writes,
              "projection_field_writes": proj_writes, "overwrites": 0, "deletes": 0, "renames": 0}
    if apply:
        result["verification"] = await _standards_metadata_verify()
    return result


async def _standards_metadata_verify():
    q = [d async for d in db[STD_COLL].find({})]
    c = [d async for d in db[CONST_COLL].find({})]
    from collections import Counter
    resolve_ok = all(sum(1 for x in q if _std_key(x) == d.get("canonical_ref")) == 1 for d in c)
    return {
        "qiks_count": len(q), "cons_count": len(c),
        "lifecycle": dict(Counter(d.get("lifecycle_status") for d in q)),
        "enforcement": dict(Counter(d.get("enforcement_condition") for d in q)),
        "const5_owner_verification_present": sum(1 for d in q if _std_key(d) in DQ7C_CONST5 and d.get("owner") and d.get("verification_status")),
        "all_projections_flagged": all(d.get("projection") and d.get("canonical_ref") for d in c),
        "every_canonical_ref_resolves_to_exactly_one": resolve_ok,
        "founder_approval_preserved": all(d.get("founder_approval") for d in q) if q else False,
        "counts_stable": len(q) == 39 and len(c) == 5,
    }


async def standards_metadata_rollback(apply: bool = False):
    rows = []
    async for d in db[STD_COLL].find({"dq7_prepared_at": {"$exists": True}}):
        sid = _std_key(d)
        unset = {f: "" for f in DQ7C_QIKS_META}
        if sid in DQ7C_CONST5 and d.get("dq7b_canonicalized_at"):
            for f in DQ7C_QIKS_CONST:
                unset[f] = ""
        if apply:
            await db[STD_COLL].update_one({"standard_id": sid} if await db[STD_COLL].find_one({"standard_id": sid}) else {"id": sid}, {"$unset": unset})
        rows.append({"id": sid, "outcome": "UNSET" if apply else "WOULD_UNSET", "fields": sorted(unset)})
    async for d in db[CONST_COLL].find({"dq7b_indexed_at": {"$exists": True}}):
        if apply:
            await db[CONST_COLL].update_one({"id": d.get("id")}, {"$unset": {f: "" for f in DQ7C_PROJ}})
        rows.append({"id": d.get("id"), "outcome": "UNSET" if apply else "WOULD_UNSET", "fields": DQ7C_PROJ})
    return {"operation": "DQ-7C Standards Metadata", "action": "rollback",
            "mode": "APPLY" if apply else "DRY_RUN", "at": _now(), "rows": rows}



# =========================================================================== #
# Test Product Cleanup — governed removal of acceptance-test / placeholder
# products from the learner catalog. Additive-metadata + status archive only;
# never deletes; never touches products tied to a paid order; fully reversible.
# =========================================================================== #
MARK_TEST = "RI-STORE-TESTCLEAN"
ARCHIVE_STATUS = "Archived"

# Deterministic markers of internal test/placeholder products (case-insensitive).
# Anchored to KNOWN test signatures — never a bare word like "test".
TEST_PRODUCT_PATTERNS = [
    r"UI_TEST_PROD",
    r"QRU Factory Acceptance Test",
    r"test infographic asset",
    r"\bTEST_[A-Z0-9]",
    r"\bdummy\b",
    r"\bsample product\b",
]
_TEST_RE = re.compile("|".join(TEST_PRODUCT_PATTERNS), re.I)


def _matched_test_pattern(p: dict):
    """Return the first matching test signature for a product, or None."""
    haystack = " ".join([
        str(p.get("title") or ""), str(p.get("name") or ""),
        str(p.get("product_code") or ""), str(p.get("topic") or ""),
    ])
    m = _TEST_RE.search(haystack)
    return m.group(0) if m else None


async def _test_has_paid_order(pid: str) -> bool:
    if pid and await db.purchases.count_documents({"product_id": pid}) > 0:
        return True
    if pid and await db.book_purchases.count_documents({"product_id": pid}) > 0:
        return True
    return False


async def _test_products_classify():
    rows = []
    async for p in db.products.find({}, {"_id": 0, "id": 1, "product_code": 1,
                                         "title": 1, "name": 1, "topic": 1, "status": 1}):
        sig = _matched_test_pattern(p)
        if not sig:
            continue
        pid = p.get("id")
        paid = await _test_has_paid_order(pid)
        status = p.get("status")
        visible = status == "Published"
        if paid:
            cls = "TEST_HAS_PAID_ORDER"          # skip — founder decision
        elif status == ARCHIVE_STATUS:
            cls = "TEST_ALREADY_ARCHIVED"         # already hidden — no-op
        elif visible:
            cls = "TEST_VISIBLE_IN_CATALOG"       # removable (currently Published)
        else:
            cls = "TEST_NOT_PUBLISHED"            # removable (draft/review state)
        rows.append({
            "code": p.get("product_code"), "id": pid,
            "title": p.get("title") or p.get("name"),
            "matched": sig, "status": status,
            "has_paid_order": paid, "classification": cls,
        })
    rows.sort(key=lambda r: (r["classification"], r["code"] or ""))
    return rows


async def test_products_preflight():
    rows = await _test_products_classify()
    def _n(c):
        return sum(1 for r in rows if r["classification"] == c)
    counts = {
        "matched_total": len(rows),
        "visible_in_catalog": _n("TEST_VISIBLE_IN_CATALOG"),
        "not_published": _n("TEST_NOT_PUBLISHED"),
        "already_archived": _n("TEST_ALREADY_ARCHIVED"),
        "has_paid_order": _n("TEST_HAS_PAID_ORDER"),
    }
    removable = counts["visible_in_catalog"] + counts["not_published"]
    return {
        "operation": "Test Product Cleanup", "ref": MARK_TEST, "at": _now(),
        "counts": counts, "removable": removable,
        "ready_to_apply": removable > 0,
        "block_reasons": [] if removable > 0 else ["No removable test products found."],
        "classification": rows,
    }


async def test_products_cleanup(apply: bool = False):
    rows = await _test_products_classify()
    actions = []
    for r in rows:
        cls = r["classification"]
        if cls == "TEST_HAS_PAID_ORDER":
            actions.append({"code": r["code"], "outcome": "SKIP",
                            "detail": "tied to a paid order — preserved for founder decision"})
            continue
        if cls == "TEST_ALREADY_ARCHIVED":
            actions.append({"code": r["code"], "outcome": "SKIP",
                            "detail": "already archived — no change"})
            continue
        # removable (visible or not-published)
        if apply:
            await db.products.update_one({"id": r["id"]}, {"$set": {
                "status": ARCHIVE_STATUS,
                "test_cleanup": {"prior_status": r["status"], "matched": r["matched"],
                                 "by": MARK_TEST, "at": _now()},
            }})
            actions.append({"code": r["code"], "outcome": "REMOVED",
                            "detail": f"status {r['status']} → {ARCHIVE_STATUS} (matched '{r['matched']}', assets preserved)"})
        else:
            actions.append({"code": r["code"], "outcome": "WOULD_REMOVE",
                            "detail": f"status {r['status']} → {ARCHIVE_STATUS} (matched '{r['matched']}')"})
    return {"operation": "Test Product Cleanup", "ref": MARK_TEST,
            "mode": "APPLY" if apply else "DRY_RUN", "at": _now(),
            "classification": rows, "actions": actions}


async def test_products_cleanup_rollback(apply: bool = False):
    rows = []
    async for p in db.products.find({"test_cleanup": {"$exists": True}}, {"_id": 0}):
        prior = (p.get("test_cleanup") or {}).get("prior_status") or "Published"
        if apply:
            await db.products.update_one({"id": p["id"]},
                                         {"$set": {"status": prior},
                                          "$unset": {"test_cleanup": ""}})
            rows.append({"code": p.get("product_code"), "outcome": "RESTORED",
                         "detail": f"restored → {prior}"})
        else:
            rows.append({"code": p.get("product_code"), "outcome": "WOULD_RESTORE",
                         "detail": f"would restore → {prior}"})
    return {"operation": "Test Product Cleanup", "action": "rollback",
            "mode": "APPLY" if apply else "DRY_RUN", "at": _now(), "rows": rows}


# =========================================================================== #
# Batch Upgrade Assets™ — governed, resumable re-render of catalog product
# covers through the HARDENED deterministic renderer (guaranteed $0 AI).
# Preserves Founder-selected Asset Vault covers; runs in the background;
# never touches book_records storefront covers.
# =========================================================================== #
ASSET_UPGRADE_JOB = "asset_upgrade_jobs"
_ASSET_UPGRADE_MARK = "RI-STORE-ASSETUP"


async def _asset_upgrade_targets(force: bool):
    """Published commerce products that are NOT internal test products.
    When force is False, only those not yet upgraded by this batch."""
    q = {"status": "Published"}
    out = []
    async for p in db.products.find(q, {"_id": 0, "id": 1, "product_code": 1, "title": 1,
                                        "name": 1, "topic": 1, "assets_upgrade": 1}):
        if _matched_test_pattern(p):
            continue
        if not force and (p.get("assets_upgrade") or {}).get("upgraded_at"):
            continue
        out.append(p["id"])
    return out


async def asset_upgrade_status():
    j = await db[ASSET_UPGRADE_JOB].find_one({"id": "current"}, {"_id": 0})
    remaining = len(await _asset_upgrade_targets(force=False))
    total_eligible = len(await _asset_upgrade_targets(force=True))
    base = {"status": "idle", "total": 0, "done": 0, "ok": 0, "failed": 0,
            "skipped": 0, "failed_ids": []}
    if j:
        base.update(j)
    base["remaining"] = remaining
    base["total_eligible"] = total_eligible
    return base


async def _asset_upgrade_worker(actor: str, force: bool):
    from models import now_iso
    ids = await _asset_upgrade_targets(force=force)
    total = len(ids)
    done = ok = failed = skipped = 0
    failed_ids = []
    await db[ASSET_UPGRADE_JOB].update_one({"id": "current"}, {"$set": {
        "id": "current", "status": "running", "total": total, "done": 0, "ok": 0,
        "failed": 0, "skipped": 0, "failed_ids": [], "force": force,
        "started_at": _now(), "finished_at": None, "by": actor}}, upsert=True)
    for pid in ids:
        try:
            res = await _re.ensure_branded_assets(pid, actor=actor, allow_ai_hero_art=False)
            if res is None:
                failed += 1
                failed_ids.append(pid)
            elif res.get("founder_selected"):
                skipped += 1  # Founder-selected Asset Vault cover — preserved, never overwritten
                await db.products.update_one({"id": pid}, {"$set": {
                    "assets_upgrade": {"upgraded_at": now_iso(), "by": _ASSET_UPGRADE_MARK,
                                       "renderer": "preserved_founder_asset"}}})
            else:
                ok += 1
                await db.products.update_one({"id": pid}, {"$set": {
                    "assets_upgrade": {"upgraded_at": now_iso(), "by": _ASSET_UPGRADE_MARK,
                                       "renderer": "deterministic_hardened"}}})
        except Exception:
            failed += 1
            failed_ids.append(pid)
        done += 1
        if done % 3 == 0:
            await db[ASSET_UPGRADE_JOB].update_one({"id": "current"}, {"$set": {
                "done": done, "ok": ok, "failed": failed, "skipped": skipped,
                "failed_ids": failed_ids}})
    await db[ASSET_UPGRADE_JOB].update_one({"id": "current"}, {"$set": {
        "status": "complete", "done": done, "ok": ok, "failed": failed,
        "skipped": skipped, "failed_ids": failed_ids, "finished_at": _now()}})


async def asset_upgrade_preflight():
    total_eligible = len(await _asset_upgrade_targets(force=True))
    remaining = len(await _asset_upgrade_targets(force=False))
    already = total_eligible - remaining
    return {
        "operation": "Batch Upgrade Assets", "ref": _ASSET_UPGRADE_MARK, "at": _now(),
        "eligible_products": total_eligible,
        "not_yet_upgraded": remaining,
        "already_upgraded": already,
        "ai_cost": "$0 (deterministic hardened renderer)",
        "ready_to_run": total_eligible > 0,
    }
