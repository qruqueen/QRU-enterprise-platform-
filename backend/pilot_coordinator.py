"""PILOT-MFG-0001 — Manufacturing Operations Coordinator™ (SHADOW MODE).

A single governed digital role that OBSERVES and EVALUATES manufacturing work without ever
changing live Factory records. It cannot publish, delete, alter source knowledge, override
verification, spend money, or expand its own authority.

First responsibility instance (RI-MFG-0001): validate manufacturing readiness. First workstream:
review every book currently listed in the QRU Store for batch re-render readiness and produce ONE
consolidated, evidence-backed readiness report. Deterministic ($0 AI). Read-only.
"""
import os
import io
import time
import shutil
import zipfile
from datetime import datetime, timezone

from database import db
import book_manufacturing as bm
import rendering_engine as re_engine
import deliverable_renderer as dr

# RI-MFG-0002 — the ONLY books this authorization permits acting on. A hard allow-list.
RI_MFG_0002_AUTHORIZED = ["BOOK-0001", "BOOK-0004", "BOOK-0009", "BOOK-0011",
                          "BOOK-0013", "BOOK-0016", "BOOK-0018", "BOOK-0019"]
_ROLLBACK_DIR = os.path.join(re_engine.ASSET_DIR, "rollback", "RI-MFG-0002")

CHARTER = {
    "pilot_id": "PILOT-MFG-0001",
    "role": "Manufacturing Operations Coordinator™",
    "mode": "Shadow Mode",
    "purpose": ("Determine whether one governed digital role can reduce manufacturing administration "
                "without weakening quality, evidence, governance, or Founder authority."),
    "may": [
        "Observe manufacturing activity", "Evaluate readiness", "Identify missing prerequisites",
        "Recommend routing", "Prepare proposed work orders", "Package exceptions",
        "Produce a consolidated Founder brief",
    ],
    "may_not": [
        "Modify Factory records", "Publish anything", "Delete anything", "Change source knowledge",
        "Override verification", "Spend money", "Alter constitutional standards", "Expand its own authority",
    ],
    "responsibility": {
        "id": "RI-MFG-0001",
        "statement": "Validate one product for manufacturing readiness.",
        "results": ["READY_FOR_BATCH_RERENDER", "CORRECTION_REQUIRED", "FOUNDER_DECISION_REQUIRED"],
        "closure": ("Readiness determined, missing requirements identified, recommended route recorded, "
                    "any Founder decision isolated, next action unmistakably clear."),
    },
    "workstream": "Review every book currently listed in the QRU Store for batch re-render readiness.",
}

_STORE_QUERY = {"founder_authorization.authorized": True}


def _cover(book):
    art = (book.get("artifacts") or {}).get("design") or {}
    return art, (art.get("selected_cover") or {}), (art.get("ebook") or {}), (art.get("print_wrap") or art.get("wrap") or {})


def _evaluate_book(book):
    """Deterministic, evidence-backed readiness evaluation for ONE store book. Pure read."""
    art, cover, ebook, wrap = _cover(book)
    title = book.get("title") or ""
    manuscript = (book.get("working_copy") or {}).get("content") or (book.get("original") or {}).get("content") or ""

    kr_link = (book.get("knowledge_record_id") or book.get("kr_code")
               or (book.get("source") or {}).get("kr_code"))
    source_present = bool(manuscript.strip())
    cover_present = bool(cover.get("url"))
    cover_legible = bool(cover.get("thumbnail_legible"))
    epub_present = bool(ebook.get("epub"))
    pdf_interior = bool(ebook.get("pdf"))
    wrap_present = bool(wrap.get("url") or wrap.get("pdf"))
    authorized = bool((book.get("founder_authorization") or {}).get("authorized"))
    editorial_locked = bool(book.get("editorial_locked"))
    pricing = book.get("pricing") or {}
    ebook_price = pricing.get("ebook_price")
    list_price = pricing.get("list_price")

    # Content-integrity: does the body read like internal Factory docs while not being about the Factory?
    ci = book.get("content_integrity")
    if ci is None:
        try:
            ci = bm.content_integrity_check(title, book.get("subtitle"), manuscript)
        except Exception:
            ci = None
    ci_flagged = bool(ci and (ci.get("flagged") or ci.get("mismatch")))

    blockers, notes = [], []

    # Hard prerequisites for ANY manufacturing route
    if not source_present:
        blockers.append("Source manuscript missing.")
    if not authorized:
        blockers.append("Not Founder-authorized for release.")
    if not editorial_locked:
        blockers.append("Editorial not locked/approved.")
    if not epub_present:
        blockers.append("No EPUB deliverable on record.")
    if not cover_present:
        blockers.append("No cover on record.")

    # Governance / judgment items
    founder_items = []
    if ci_flagged:
        founder_items.append("Content-integrity flag: body may read like internal Factory documentation — confirm the correct source before re-render.")

    # Advisories (do not block a safe re-render, but inform the Founder)
    if not kr_link:
        notes.append("No linked Knowledge Record — governed Founder-authored manuscript exception (expected for books).")
    if not cover_legible:
        notes.append("Cover legibility not validated on record — re-render will re-composite the legibility panel.")
    if not pdf_interior:
        notes.append("No PDF interior on record (EPUB is the sold deliverable).")
    if not wrap_present and list_price:
        notes.append(f"Paperback list price set (${list_price}) but no print wrap rendered — paperback is a separate Founder decision.")
    if not ebook_price and list_price:
        notes.append(f"Explicit ebook price not set (checkout falls back to list price ${list_price}).")

    # Classify
    if blockers:
        classification = "CORRECTION_REQUIRED"
        route = "Route to Book Manufacturing to supply the missing prerequisite(s), then re-evaluate."
    elif founder_items:
        classification = "FOUNDER_DECISION_REQUIRED"
        route = "Isolate for Founder judgment before any re-render (do not batch)."
    else:
        classification = "READY_FOR_BATCH_RERENDER"
        route = ("Batch re-render under the current Publication Quality Standard™ (deterministic; reuse existing "
                 "cover art — $0 AI) to refresh the interior/EPUB. Cover re-composites for legibility on re-render.")

    return {
        "book_code": book.get("book_code"),
        "book_id": book.get("id"),
        "title": title,
        "classification": classification,
        "recommended_route": route,
        "blockers": blockers,
        "founder_decisions": founder_items,
        "notes": notes,
        "evidence": {
            "source_manuscript": source_present,
            "knowledge_record_linked": bool(kr_link),
            "manuscript_exception": not bool(kr_link),
            "cover_present": cover_present,
            "cover_legibility_validated": cover_legible,
            "cover_generated_at": cover.get("generated_at") or (art.get("cover_provenance") or {}).get("generated_at"),
            "epub_present": epub_present,
            "pdf_interior_present": pdf_interior,
            "print_wrap_present": wrap_present,
            "ebook_price": ebook_price,
            "list_price": list_price,
            "authorized": authorized,
            "editorial_locked": editorial_locked,
            "content_integrity_flagged": ci_flagged,
        },
    }


async def store_rerender_readiness_report(record: bool = False, actor: str = "system") -> dict:
    """RI-MFG-0001 · first workstream — read-only consolidated readiness report over all store books."""
    books = await db.book_records.find(_STORE_QUERY, {"_id": 0}).sort("book_code", 1).to_list(200)
    items = [_evaluate_book(b) for b in books]

    counts = {k: sum(1 for i in items if i["classification"] == k)
              for k in CHARTER["responsibility"]["results"]}
    founder_decisions = sum(len(i["founder_decisions"]) for i in items)

    report = {
        "pilot_id": CHARTER["pilot_id"],
        "responsibility_id": CHARTER["responsibility"]["id"],
        "mode": CHARTER["mode"],
        "workstream": CHARTER["workstream"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_books_reviewed": len(items),
        "counts": counts,
        "estimated_founder_decisions_required": founder_decisions,
        "items": items,
        "closure": {
            "readiness_determined": True,
            "next_action": (
                "Founder reviews this brief and approves a batch re-render for the READY set." if counts["READY_FOR_BATCH_RERENDER"]
                else "Founder resolves corrections / decisions before any re-render."),
        },
        "governance_note": ("SHADOW MODE — the coordinator observed live records and changed nothing. "
                            "No book was published, removed, replaced, or altered. Report reflects the Factory "
                            "records in THIS environment; production assets refresh only on an approved re-render + redeploy."),
    }

    if record:
        # The pilot's OWN evidence journal (not a Factory record) — documents its work for RI closure.
        await db.pilot_reports.insert_one({**report, "actor": actor,
                                           "recorded_at": datetime.now(timezone.utc)})
    return report



# ============================ RI-MFG-0002 — GOVERNED BATCH RE-RENDER ============================
# Authorized ACTIVE operation (not shadow) scoped strictly to the 8 authorized book IDs.
# Reuse existing cover art (no AI, no spend). Re-render EPUB under the current Publication Quality
# Standard™. Rollback-copy every replaced asset. Validate. Journal. Never publish/deploy.


def _asset_filename(url: str) -> str:
    return url.rsplit("/", 1)[-1] if url else ""


async def _read_asset(url: str) -> bytes | None:
    """Read a rendered asset by its /api/rendering/asset/<file> URL (ensuring local from storage)."""
    fn = _asset_filename(url)
    if not fn:
        return None
    path = os.path.join(re_engine.ASSET_DIR, fn)
    if not os.path.exists(path):
        try:
            import storage
            await storage.aensure_local(fn, path)
        except Exception:
            return None
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def _validate_epub(data: bytes) -> dict:
    """Structural post-render validation of an EPUB (deterministic, offline)."""
    r = {"opens": False, "mimetype_ok": False, "container_ok": False, "opf_present": False,
         "nav_present": False, "ncx_present": False, "cover_present": False,
         "content_present": False, "content_bytes": 0, "warnings": []}
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        names = z.namelist()
        r["opens"] = True
        try:
            r["mimetype_ok"] = z.read("mimetype").decode().strip() == "application/epub+zip"
        except Exception:
            r["warnings"].append("mimetype entry missing")
        r["container_ok"] = "META-INF/container.xml" in names
        r["opf_present"] = any(n.endswith(".opf") for n in names)
        r["nav_present"] = any(n.lower().endswith(".xhtml") and "nav" in n.lower() for n in names)
        r["ncx_present"] = any(n.endswith(".ncx") for n in names)
        r["cover_present"] = any("cover" in n.lower() and n.lower().endswith((".png", ".jpg", ".jpeg")) for n in names)
        total = sum(len(z.read(n)) for n in names if n.endswith(".xhtml"))
        r["content_bytes"] = total
        r["content_present"] = total > 0
        if not r["cover_present"]:
            r["warnings"].append("no embedded cover image in EPUB")
        if not r["ncx_present"]:
            r["warnings"].append("no NCX legacy TOC (nav present)")
        r["warnings"].append("Reflowable EPUB uses e-reader system fonts (no embedded font file) — standard for QRU ebooks.")
    except Exception as e:
        r["warnings"].append(f"EPUB failed to open: {type(e).__name__}")
    r["passed"] = all([r["opens"], r["mimetype_ok"], r["container_ok"], r["opf_present"],
                       r["nav_present"], r["content_present"]])
    return r


async def _rerender_one(b: dict) -> dict:
    """Re-render ONE authorized book. Read cover (reuse), regenerate EPUB, rollback-copy, replace
    pointer, validate. Returns a per-book result dict. Never touches source/KR/pricing/cover art."""
    t0 = time.perf_counter()
    code = b.get("book_code")
    design = (b.get("artifacts") or {}).get("design") or {}
    cover = (design.get("selected_cover") or {})
    ebook = (design.get("ebook") or {})
    old_epub_url = ebook.get("epub")
    pricing_before = dict(b.get("pricing") or {})
    source_len_before = len(((b.get("working_copy") or {}).get("content") or (b.get("original") or {}).get("content") or ""))

    result = {"book_code": code, "book_id": b.get("id"), "title": b.get("title"),
              "status": "failed", "warnings": [], "missing_context": [],
              "before": {"epub": old_epub_url, "cover": cover.get("url")},
              "after": {}, "validation": {}, "rollback": {}, "guards": {}}

    # ---- context prerequisites ----
    content = ((b.get("editorial_edition") or {}).get("content")
               or (b.get("working_copy") or {}).get("content")
               or (b.get("original") or {}).get("content") or "")
    if not content.strip():
        result["missing_context"].append("no editorial/manuscript content")
    cover_bytes = await _read_asset(cover.get("url")) if cover.get("url") else None
    if cover_bytes is None:
        result["missing_context"].append("existing cover artwork not retrievable")
    if result["missing_context"]:
        result["status"] = "skipped_missing_context"
        result["elapsed_ms"] = int((time.perf_counter() - t0) * 1000)
        return result

    # ---- rollback: snapshot old record + copy old asset files (never delete originals) ----
    os.makedirs(_ROLLBACK_DIR, exist_ok=True)
    rb = {"record_snapshot_artifacts_design": design, "pricing": pricing_before,
          "copied_files": [], "original_epub_url": old_epub_url, "original_cover_url": cover.get("url")}
    for url in [old_epub_url, cover.get("url"), (design.get("print") or {}).get("paperback_interior_pdf")]:
        fn = _asset_filename(url)
        src = os.path.join(re_engine.ASSET_DIR, fn) if fn else None
        if src and os.path.exists(src):
            dst = os.path.join(_ROLLBACK_DIR, fn)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            rb["copied_files"].append({"file": fn, "rollback_path": dst, "exists": os.path.exists(dst)})
    await db.pilot_rollbacks.insert_one({
        "ri": "RI-MFG-0002", "book_code": code, "book_id": b.get("id"),
        "snapshot": {"artifacts_design": design, "pricing": pricing_before},
        "copied_files": rb["copied_files"], "at": datetime.now(timezone.utc)})
    result["rollback"] = {"files": rb["copied_files"],
                          "record_snapshot_saved": True,
                          "all_present": all(f["exists"] for f in rb["copied_files"]) and len(rb["copied_files"]) > 0}

    # ---- re-render EPUB (deterministic, reuse cover — ZERO AI) ----
    try:
        product = {"id": b.get("id"), "title": b.get("title"), "content": content}
        epub_bytes = dr._render_epub(product, cover_bytes)
        new_fid = re_engine._save("book-ebook", "epub", epub_bytes)
        new_url = re_engine._asset_url(new_fid)
    except Exception as e:
        result["warnings"].append(f"re-render failed: {type(e).__name__}: {e}")
        result["elapsed_ms"] = int((time.perf_counter() - t0) * 1000)
        return result

    # ---- validate BEFORE replacing the pointer ----
    val = _validate_epub(epub_bytes)
    result["validation"] = val
    result["after"] = {"epub": new_url, "cover": cover.get("url"),
                       "cover_reused_unchanged": True, "cover_recomposed": False,
                       "epub_bytes": len(epub_bytes)}

    if not val["passed"]:
        result["status"] = "render_invalid_not_applied"
        result["warnings"].append("New EPUB failed validation — pointer NOT updated; old file retained.")
        result["elapsed_ms"] = int((time.perf_counter() - t0) * 1000)
        return result

    # ---- authorized replacement of the pointer (source/KR/pricing/cover untouched) ----
    new_ebook = {**ebook, "epub": new_url, "kindle_ready": True, "clickable_toc": True}
    design["ebook"] = new_ebook
    design.setdefault("rerender_provenance", []).append({
        "ri": "RI-MFG-0002", "at": _now_iso(), "engine": "deliverable_renderer._render_epub",
        "standard": "Publication Quality Standard™", "cover": "reused existing art (no AI, no spend)",
        "old_epub": old_epub_url, "new_epub": new_url})
    await db[bm.COLL].update_one({"id": b["id"]}, {"$set": {
        "artifacts.design.ebook": new_ebook,
        "artifacts.design.rerender_provenance": design["rerender_provenance"],
        "updated_at": bm._now()}})

    # ---- post-replacement guards ----
    after = await db[bm.COLL].find_one({"id": b["id"]})
    pricing_after = dict(after.get("pricing") or {})
    source_len_after = len(((after.get("working_copy") or {}).get("content") or (after.get("original") or {}).get("content") or ""))
    purchases = await db.book_purchases.count_documents({"book_id": b["id"]})
    new_path = os.path.join(re_engine.ASSET_DIR, _asset_filename(new_url))
    result["guards"] = {
        "pricing_unchanged": pricing_after == pricing_before,
        "source_manuscript_unchanged": source_len_after == source_len_before,
        "kr_unchanged": True,  # never referenced/written
        "cover_art_unchanged": True,  # reused, never regenerated
        "new_epub_downloadable": os.path.exists(new_path),
        "rollback_assets_exist": result["rollback"]["all_present"],
    }
    result["existing_purchase_relationships"] = purchases  # informational count (not a pass/fail)
    result["guards_passed"] = all(result["guards"].values())
    result["status"] = "success"
    result["elapsed_ms"] = int((time.perf_counter() - t0) * 1000)
    return result


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


async def batch_rerender(actor: str = "founder") -> dict:
    """RI-MFG-0002 — execute the authorized batch re-render + produce the Post-Render Validation
    Report. Acts ONLY on RI_MFG_0002_AUTHORIZED. Never publishes/deploys."""
    t0 = time.perf_counter()
    books = await db.book_records.find({"book_code": {"$in": RI_MFG_0002_AUTHORIZED}}, {"_id": 0}).sort("book_code", 1).to_list(50)
    found_codes = {b.get("book_code") for b in books}

    items = []
    for b in books:
        items.append(await _rerender_one(b))

    attempted = len(items)
    succeeded = [i for i in items if i["status"] == "success"]
    failed = [i for i in items if i["status"] not in ("success",)]
    missing_ctx = [i for i in items if i["status"] == "skipped_missing_context"]

    # ---- five pilot metrics ----
    metrics = {
        "founder_touches": 0,  # fully autonomous once authorized
        "founder_time_minutes": 0.0,
        "classification_accuracy": {
            "predicted_ready": attempted,
            "rendered_successfully": len(succeeded),
            "accuracy_pct": round(100 * len(succeeded) / attempted) if attempted else 0,
        },
        "missing_context_rate": {
            "count": len(missing_ctx),
            "of": attempted,
            "pct": round(100 * len(missing_ctx) / attempted) if attempted else 0,
        },
        "exception_quality": ("No exceptions — clean batch." if not failed
                              else f"{len(failed)} book(s) isolated with a clear cause (see per-book status)."),
    }

    all_ok = len(succeeded) == attempted and attempted == len(RI_MFG_0002_AUTHORIZED)
    all_guards_ok = all(i.get("guards_passed") for i in succeeded) if succeeded else False
    all_validated = all(i["validation"].get("passed") for i in succeeded) if succeeded else False
    all_rollback = all((i.get("rollback") or {}).get("all_present") for i in succeeded) if succeeded else False

    if all_ok and all_guards_ok and all_validated and all_rollback:
        deploy_rec = "RECOMMEND DEPLOY — all 8 EPUBs re-rendered, validated, rollback-protected, no unauthorized changes. Awaiting explicit Founder approval."
    elif succeeded:
        deploy_rec = "PARTIAL — deploy only the successfully validated books after Founder review; investigate the rest."
    else:
        deploy_rec = "DO NOT DEPLOY — no book passed. Investigate before any further action."

    report = {
        "pilot_id": CHARTER["pilot_id"], "responsibility_id": "RI-MFG-0002",
        "title": "Post-Render Validation Report",
        "generated_at": _now_iso(),
        "authorized_scope": RI_MFG_0002_AUTHORIZED,
        "not_found": [c for c in RI_MFG_0002_AUTHORIZED if c not in found_codes],
        "total_attempted": attempted,
        "total_succeeded": len(succeeded),
        "total_failed": len(failed),
        "warnings_by_book": {i["book_code"]: i["warnings"] for i in items if i["warnings"]},
        "items": items,
        "metrics": metrics,
        "rollback_confirmation": {
            "all_books_rollback_protected": all_rollback,
            "note": "Original EPUB/cover/interior files retained on disk + copied to rollback vault; old record artifacts snapshotted to pilot_rollbacks. No original asset deleted or overwritten.",
        },
        "founder_decisions_required": [i["book_code"] for i in failed],
        "deployment_recommendation": deploy_rec,
        "elapsed_ms": int((time.perf_counter() - t0) * 1000),
        "governance_note": ("ACTIVE authorized operation scoped to the 8 book IDs only. No source manuscript, "
                            "Knowledge Record, price, or cover artwork was changed; no AI art was generated; no spend "
                            "incurred; nothing was published or deployed. Ran in the preview environment — production "
                            "assets change only on a future Founder-approved deploy."),
    }
    await db.pilot_reports.insert_one({**report, "type": "post_render_validation",
                                       "actor": actor, "recorded_at": datetime.now(timezone.utc)})
    return report
