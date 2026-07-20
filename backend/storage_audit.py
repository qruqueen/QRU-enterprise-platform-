"""Phase B — Durable Storage Audit & Recovery.

Compares the production DATABASE references (covers / EPUBs / PDFs / HTML / wrap deliverables /
audio) against what is actually available on the local ephemeral disk AND in durable object
storage, then classifies every MISSING asset by how it can be recovered:

  • deterministic  — document-family covers/PDF/EPUB/HTML/wrap → regenerate at $0 (no AI).
  • ai_art         — Founder-selected AI hero-art covers → regeneration costs Gemini AND produces
                     DIFFERENT art. NEVER auto-regenerated (needs Founder approval).
  • ai_tts         — audiobooks → regeneration costs OpenAI TTS. NEVER auto-regenerated.
  • book           — published book_records deliverables → recovered via the Book pipeline (manual).

The audit is READ-ONLY. Recovery only ever runs the deterministic ($0) path automatically; every
asset that would require AI/TTS is placed on a separate APPROVAL LIST and left untouched. Recovery
is resumable + idempotent (a file already present locally or in object storage is skipped).
"""
import os
import asyncio
import logging

from database import db
from models import now_iso
import rendering_engine as re_engine
import storage

logger = logging.getLogger("qru.storage_audit")

_DOC_CATS = {"book", "guide", "workbook", "card"}
_AUDIT_DOC = "storage_audit_reports"
_RECOVERY_JOB = "storage_recovery_jobs"
_CAP = 200  # cap id lists so the report stays lightweight


def _fid(url):
    return url.rstrip("/").split("/")[-1] if url else None


def _local_path(fid):
    if fid and fid.startswith("audiobook-"):
        try:
            from product_publishing import AUDIOBOOK_DIR
            return str(AUDIOBOOK_DIR / fid[len("audiobook-"):])
        except Exception:
            return os.path.join(re_engine.ASSET_DIR, fid)
    return os.path.join(re_engine.ASSET_DIR, fid) if fid else None


def _availability(fid):
    """Return ('local'|'object'|'missing')."""
    path = _local_path(fid)
    if path and os.path.exists(path):
        return "local"
    if fid and storage.object_exists(fid):
        return "object"
    return "missing"


async def _paid_book_ids():
    ids = set()
    try:
        async for o in db.book_purchases.find({"payment_status": "paid"}, {"book_id": 1}):
            if o.get("book_id"):
                ids.add(o["book_id"])
    except Exception:
        pass
    return ids


async def _audit_worker():
    import product_recipes as pr
    await db[_AUDIT_DOC].update_one({"id": "current"}, {"$set": {
        "id": "current", "status": "running", "started_at": now_iso(), "finished_at": None}}, upsert=True)

    by_type = {}   # type -> {"referenced","local","object","missing"}
    cls = {"deterministic": [], "ai_art": [], "ai_tts": [], "book": [], "other": []}

    def bump(t, key):
        d = by_type.setdefault(t, {"referenced": 0, "local": 0, "object": 0, "missing": 0})
        d["referenced"] += 1
        d[key] += 1

    prods_scanned = 0
    prods = await db.products.find(
        {}, {"id": 1, "product_type": 1, "cover_url": 1, "cover_has_hero_art": 1,
             "customer_deliverable": 1, "audiobook": 1, "status": 1}).to_list(20000)
    for p in prods:
        prods_scanned += 1
        cat = pr.get_recipe(p.get("product_type", "")).get("category")
        # cover
        cfid = _fid(p.get("cover_url"))
        if cfid:
            avail = _availability(cfid)
            bump("cover", avail)
            if avail == "missing":
                if p.get("cover_has_hero_art"):
                    cls["ai_art"].append(p["id"])
                elif cat in _DOC_CATS:
                    cls["deterministic"].append(p["id"])
                else:
                    cls["other"].append(p["id"])  # poster/media/etc — own engine
        # rendered deliverable files
        for f in ((p.get("customer_deliverable") or {}).get("files") or []):
            dfid = f.get("filename")
            if not dfid:
                continue
            fmt = f.get("format", "")
            avail = _availability(dfid)
            bump(f"deliverable_{fmt}", avail)
            if avail == "missing":
                cls["deterministic"].append(p["id"])
        # audio
        ab = p.get("audiobook") or {}
        if ab.get("status") == "READY":
            afid = f"audiobook-{p['id']}.mp3"
            avail = _availability(afid)
            bump("audio", avail)
            if avail == "missing":
                cls["ai_tts"].append(p["id"])

    books_scanned = 0
    paid_books = await _paid_book_ids()
    try:
        import routers.public_site as ps
    except Exception:
        ps = None
    try:
        import routers.public_commerce as pc
    except Exception:
        pc = None
    books = await db.book_records.find({}, {"_id": 0}).to_list(5000)
    for b in books:
        books_scanned += 1
        # cover + epub resolved via the same helpers the storefront uses
        cfid = _fid(ps._cover_url(b)) if ps else None
        if cfid:
            avail = _availability(cfid)
            bump("book_cover", avail)
            if avail == "missing":
                cls["book"].append(b.get("id"))
        try:
            efid = _fid(pc._epub_url(b)) if pc else None
        except Exception:
            efid = None
        if efid:
            avail = _availability(efid)
            bump("book_epub", avail)
            if avail == "missing" and b.get("id") not in cls["book"]:
                cls["book"].append(b.get("id"))

    def dedupe(lst):
        return list(dict.fromkeys(lst))

    cls = {k: dedupe(v) for k, v in cls.items()}
    totals = {"referenced": 0, "local": 0, "object": 0, "missing": 0}
    for d in by_type.values():
        for k in totals:
            totals[k] += d.get(k, 0)

    report = {
        "id": "current", "status": "complete", "started_at": None,
        "generated_at": now_iso(), "finished_at": now_iso(),
        "products_scanned": prods_scanned, "books_scanned": books_scanned,
        "totals": totals, "by_type": by_type,
        "missing_classification": {
            "deterministic": {"count": len(cls["deterministic"]), "product_ids": cls["deterministic"][:_CAP],
                              "recovery": "Auto-recoverable at $0 (no AI). Run recovery."},
            "ai_art": {"count": len(cls["ai_art"]), "product_ids": cls["ai_art"][:_CAP],
                       "recovery": "APPROVAL REQUIRED — Founder-selected AI art; regeneration costs Gemini and yields different art."},
            "ai_tts": {"count": len(cls["ai_tts"]), "product_ids": cls["ai_tts"][:_CAP],
                       "recovery": "APPROVAL REQUIRED — audiobook; regeneration costs OpenAI TTS."},
            "book": {"count": len(cls["book"]), "book_ids": cls["book"][:_CAP],
                     "recovery": "Recover via the Book Manufacturing pipeline (re-render/re-assemble)."},
            "other": {"count": len(cls["other"]), "product_ids": cls["other"][:_CAP],
                      "recovery": "Non-document engine (poster/media). Regenerate via its own studio or Regenerate-Cover."},
        },
        "paid_books_total": len(paid_books),
        "note": ("Referenced = DB says the file should exist. Missing = absent from BOTH local disk "
                 "and durable object storage. Deterministic-missing is safe to auto-recover at $0."),
    }
    await db[_AUDIT_DOC].replace_one({"id": "current"}, report, upsert=True)
    return report


async def start_audit():
    existing = await db[_AUDIT_DOC].find_one({"id": "current"}, {"_id": 0})
    if existing and existing.get("status") == "running":
        return {"ok": True, "status": "running", "message": "An audit is already running."}
    asyncio.create_task(_audit_worker())
    return {"ok": True, "status": "started", "message": "Storage audit started. Poll status to read results."}


async def audit_status():
    r = await db[_AUDIT_DOC].find_one({"id": "current"}, {"_id": 0})
    return r or {"status": "idle", "message": "No audit has been run yet."}


# --------------------------------------------------------------------------- #
# Recovery — deterministic ($0) only. AI/TTS assets go to the approval list.
# Resumable + idempotent: a product whose files are all available is skipped.
# --------------------------------------------------------------------------- #
async def _product_files_missing(p):
    """True if the product's cover or any deliverable file is missing from local+object storage."""
    fids = []
    cfid = _fid(p.get("cover_url"))
    if cfid and not p.get("cover_has_hero_art"):  # deterministic cover only
        fids.append(cfid)
    for f in ((p.get("customer_deliverable") or {}).get("files") or []):
        if f.get("filename"):
            fids.append(f["filename"])
    for fid in fids:
        if _availability(fid) == "missing":
            return True
    return False


async def _recovery_worker(actor, base_url=""):
    import product_recipes as pr
    import deliverable_renderer as dr
    prods = await db.products.find(
        {"content": {"$exists": True, "$ne": ""}},
        {"id": 1, "product_type": 1, "cover_url": 1, "cover_has_hero_art": 1,
         "customer_deliverable": 1, "audiobook": 1}).to_list(20000)
    docs = [p for p in prods if pr.get_recipe(p.get("product_type", "")).get("category") in _DOC_CATS]

    # Approval list (never auto-regenerated).
    approval = {"ai_art": [], "ai_tts": []}
    for p in prods:
        cfid = _fid(p.get("cover_url"))
        if cfid and p.get("cover_has_hero_art") and _availability(cfid) == "missing":
            approval["ai_art"].append(p["id"])
        ab = p.get("audiobook") or {}
        if ab.get("status") == "READY" and _availability(f"audiobook-{p['id']}.mp3") == "missing":
            approval["ai_tts"].append(p["id"])

    total = len(docs)
    await db[_RECOVERY_JOB].update_one({"id": "current"}, {"$set": {
        "id": "current", "status": "running", "total": total, "done": 0, "recovered": 0,
        "skipped": 0, "failed": 0, "failed_ids": [], "approval_needed": approval,
        "started_at": now_iso(), "finished_at": None, "by": actor}}, upsert=True)

    done = recovered = skipped = failed = 0
    failed_ids = []
    for p in docs:
        try:
            if not await _product_files_missing(p):
                skipped += 1  # idempotent — already durable/present
            else:
                res = await dr.ensure_deliverable(p["id"], actor=actor, base_url=base_url,
                                                  build_marketing=False, allow_ai_cover=False)
                if res and res.get("files"):
                    recovered += 1
                else:
                    failed += 1; failed_ids.append(p["id"])
        except Exception as e:
            logger.warning("recovery failed for %s: %s", p.get("id"), e)
            failed += 1; failed_ids.append(p["id"])
        done += 1
        if done % 5 == 0:
            await db[_RECOVERY_JOB].update_one({"id": "current"}, {"$set": {
                "done": done, "recovered": recovered, "skipped": skipped,
                "failed": failed, "failed_ids": failed_ids}})

    await db[_RECOVERY_JOB].update_one({"id": "current"}, {"$set": {
        "status": "complete", "done": done, "recovered": recovered, "skipped": skipped,
        "failed": failed, "failed_ids": failed_ids, "finished_at": now_iso()}})


async def start_recovery(actor="Founder", base_url=""):
    existing = await db[_RECOVERY_JOB].find_one({"id": "current"}, {"_id": 0})
    if existing and existing.get("status") == "running":
        return {"ok": True, "status": "running", "message": "A recovery run is already in progress."}
    asyncio.create_task(_recovery_worker(actor, base_url))
    return {"ok": True, "status": "started",
            "message": "Deterministic recovery started (ZERO AI spend). AI/TTS assets are listed for approval only."}


async def recovery_status():
    j = await db[_RECOVERY_JOB].find_one({"id": "current"}, {"_id": 0})
    if not j:
        return {"status": "idle", "total": 0, "done": 0, "recovered": 0, "skipped": 0, "failed": 0}
    j["remaining"] = max(0, (j.get("total", 0) or 0) - (j.get("done", 0) or 0))
    return j


# --------------------------------------------------------------------------- #
# Disk backfill — push assets ALREADY on the local disk into durable object
# storage (idempotent). Used in preview to make the current on-disk library
# durable without re-rendering. (Cannot help production's already-lost files.)
# --------------------------------------------------------------------------- #
_BACKFILL_JOB = "storage_disk_backfill_jobs"


async def _backfill_worker(actor):
    files = []
    for fn in os.listdir(re_engine.ASSET_DIR):
        fp = os.path.join(re_engine.ASSET_DIR, fn)
        if os.path.isfile(fp) and not fn.startswith("tmp"):
            files.append((fn, fp))
    try:
        from product_publishing import AUDIOBOOK_DIR
        for fn in os.listdir(AUDIOBOOK_DIR):
            fp = os.path.join(AUDIOBOOK_DIR, fn)
            if os.path.isfile(fp) and fn.endswith(".mp3"):
                files.append((f"audiobook-{fn}", fp))
    except Exception:
        pass

    total = len(files)
    await db[_BACKFILL_JOB].update_one({"id": "current"}, {"$set": {
        "id": "current", "status": "running", "total": total, "done": 0, "uploaded": 0,
        "already": 0, "failed": 0, "started_at": now_iso(), "finished_at": None, "by": actor}}, upsert=True)
    done = uploaded = already = failed = 0
    for fid, fp in files:
        try:
            if storage.object_exists(fid):
                already += 1
            else:
                with open(fp, "rb") as f:
                    ok = await storage.amirror_file(fid, f.read())
                uploaded += 1 if ok else 0
                failed += 0 if ok else 1
        except Exception as e:
            logger.warning("backfill failed for %s: %s", fid, e)
            failed += 1
        done += 1
        if done % 10 == 0:
            await db[_BACKFILL_JOB].update_one({"id": "current"}, {"$set": {
                "done": done, "uploaded": uploaded, "already": already, "failed": failed}})
    await db[_BACKFILL_JOB].update_one({"id": "current"}, {"$set": {
        "status": "complete", "done": done, "uploaded": uploaded, "already": already,
        "failed": failed, "finished_at": now_iso()}})


async def start_disk_backfill(actor="Founder"):
    existing = await db[_BACKFILL_JOB].find_one({"id": "current"}, {"_id": 0})
    if existing and existing.get("status") == "running":
        return {"ok": True, "status": "running", "message": "A disk backfill is already running."}
    asyncio.create_task(_backfill_worker(actor))
    return {"ok": True, "status": "started", "message": "Disk→object-storage backfill started (idempotent)."}


async def disk_backfill_status():
    j = await db[_BACKFILL_JOB].find_one({"id": "current"}, {"_id": 0})
    return j or {"status": "idle", "total": 0, "done": 0, "uploaded": 0, "already": 0, "failed": 0}
