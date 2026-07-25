"""PILOT-MFG-0001 — Manufacturing Operations Coordinator™ (SHADOW MODE).

A single governed digital role that OBSERVES and EVALUATES manufacturing work without ever
changing live Factory records. It cannot publish, delete, alter source knowledge, override
verification, spend money, or expand its own authority.

First responsibility instance (RI-MFG-0001): validate manufacturing readiness. First workstream:
review every book currently listed in the QRU Store for batch re-render readiness and produce ONE
consolidated, evidence-backed readiness report. Deterministic ($0 AI). Read-only.
"""
from datetime import datetime, timezone

from database import db
import book_manufacturing as bm

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
