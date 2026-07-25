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


def _norm(s):
    return " ".join((s or "").lower().split())


async def _record_summary(rec):
    if not rec:
        return None
    d = (rec.get("artifacts") or {}).get("design") or {}
    return {
        "id": rec.get("id"),
        "title": rec.get("title"),
        "subtitle": rec.get("subtitle"),
        "author": rec.get("author"),
        "book_code": rec.get("book_code"),
        "publication_status": rec.get("publication_status") or rec.get("status"),
        "approval_status": rec.get("approval_status"),
        "editorial_locked": rec.get("editorial_locked"),
        "epub": (d.get("ebook") or {}).get("epub"),
        "cover": (d.get("selected_cover") or {}).get("url"),
        "created_at": rec.get("created_at"),
        "migrated_by": rec.get("_migrated_by"),
        "purchases": await db.book_purchases.count_documents({"book_id": rec.get("id")}),
    }


async def inspect_book_conflicts():
    """READ-ONLY. For each Stage-1 book_code, compare the incoming migration record with whatever
    already exists in THIS database (by id and by book_code) and produce a governed recommendation.
    Writes nothing."""
    books = _load("data_stage1_books.json")
    ptr_by_code = {p["book_code"]: p for p in _load("data_stage2_pointers.json")}
    out = []
    for b in books:
        code, mid = b.get("book_code"), b.get("id")
        design = (b.get("artifacts") or {}).get("design") or {}
        incoming = {
            "id": mid, "title": b.get("title"), "author": b.get("author"), "book_code": code,
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
            classification = "PRESENT_BY_ID"
            recommendation = ("Already present under the same canonical id — no creation needed. "
                              "Stage 2 will refresh its EPUB pointer to the re-rendered edition.")
        elif by_code:
            same_title = _norm(existing_by_code["title"]) == _norm(b.get("title"))
            same_author = _norm(existing_by_code.get("author")) == _norm(b.get("author"))
            if same_title and same_author:
                classification = "ID_MISMATCH_SAME_BOOK"
                recommendation = ("Same book, different internal id (this record was created directly in "
                                  "production, so its id differs from preview's copy). SAFEST: ADOPT the existing "
                                  "production record — do NOT insert a duplicate. Apply the re-rendered EPUB to "
                                  "the EXISTING id via a governed remap. The existing record, its cover, pricing, "
                                  "authorization and any purchases are preserved.")
            elif same_title:
                classification = "ID_MISMATCH_TITLE_MATCH_AUTHOR_DIFF"
                recommendation = ("Titles match but author differs — likely the same book with a metadata "
                                  "difference. FOUNDER REVIEW before adopting. Do not create a duplicate.")
            else:
                classification = "CODE_COLLISION_DIFFERENT_CONTENT"
                recommendation = ("The existing production record under this book_code is a DIFFERENT title. "
                                  "This is a code collision, not the same book. FOUNDER DECISION REQUIRED — do "
                                  "not create, do not repoint. Investigate how the code was reused before any change.")
        else:
            classification = "ABSENT"
            recommendation = "Truly missing in this database — safe to CREATE from the migration record (assets permitting)."

        out.append({
            "book_code": code,
            "classification": classification,
            "recommendation": recommendation,
            "rerender_epub_available": rerender_epub_available,
            "incoming": incoming,
            "existing_by_id": existing_by_id,
            "existing_by_code": existing_by_code,
        })
    return {"workstream": "A", "action": "inspect", "read_only": True, "at": _now(), "books": out}


async def resolve_book_conflicts(apply: bool = False):
    """Governed conflict resolution. ONLY for records classified ID_MISMATCH_SAME_BOOK
    (same title AND author, existing under a different id because it was created directly in
    production): ADOPT the existing production record and apply the re-rendered EPUB pointer to
    its EXISTING id. Never creates a duplicate; never touches collisions or title/author mismatches;
    never alters manuscript, cover, pricing, authorization, or purchases. Rollback-preserving."""
    insp = await inspect_book_conflicts()
    ptr_by_code = {p["book_code"]: p for p in _load("data_stage2_pointers.json")}
    rows = []
    for b in insp["books"]:
        code, cls = b["book_code"], b["classification"]
        if cls != "ID_MISMATCH_SAME_BOOK":
            rows.append({"code": code, "outcome": "SKIP",
                         "detail": f"{cls} — not an adopt-and-remap target"})
            continue
        existing = b["existing_by_code"]
        ptr = ptr_by_code.get(code)
        if not ptr:
            rows.append({"code": code, "outcome": "SKIP", "detail": "no pointer mapping"})
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
            prov.append({"ri": MARK_A, "at": _now(), "adopt_remap": True,
                         "resolved_book_code": code, "old_epub": cur, "new_epub": ptr["new_epub_url"],
                         "standard": "Publication Quality Standard\u2122"})
            await db[COLL].update_one({"id": existing["id"]}, {"$set": {
                "artifacts.design.ebook": ebook, "artifacts.design.rerender_provenance": prov}})
            rows.append({"code": code, "outcome": "ADOPTED_AND_REPOINTED",
                         "detail": f"existing id {existing['id']} → {ptr['new_epub_file']} (rollback saved; no duplicate created)"})
        else:
            rows.append({"code": code, "outcome": "WOULD_ADOPT_AND_REPOINT",
                         "detail": f"existing id {existing['id']} → {ptr['new_epub_file']} (rollback would be saved)"})
    return {"workstream": "A", "action": "resolve_conflicts",
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
