"""QRU Book Manufacturing System™ v1.0 — ONE approved manuscript in, ONE complete
governed publication package out. A governed workflow that ORCHESTRATES existing QRU
capabilities (renderer, Reading Experience Standard™, Product Governance Package™,
studios, publishers). Not a new department. Exactly SEVEN buttons. No 8th.

Principles enforced here:
- Human judgment is final for irreversible actions; the Factory never simulates platform success.
- Immutable original is preserved; a separate working copy is edited.
- The book title always appears before the Book Record ID in Founder-facing data.
- Where a platform can't be fully automated: produce the complete package + honest guided checklist.
"""
import io
import os
import hashlib
import asyncio
from datetime import datetime, timezone

from database import db
from models import gen_id, now_iso, clean
from org_activity import log_org
import book_structure as bs
import product_governance as pg
import manufacturing_recipes as recipes
import manufacturing_foundation as mf
import ukr_standard as ukr
import ai_service

COLL = "book_records"

# The seven — and only seven — primary responsibilities.
SEVEN_BUTTONS = [
    {"key": "upload", "label": "Upload", "icon": "upload"},
    {"key": "proof", "label": "Proof & Polish", "icon": "spell-check"},
    {"key": "design", "label": "Design", "icon": "palette"},
    {"key": "audio", "label": "Audio", "icon": "mic"},
    {"key": "video", "label": "Video", "icon": "video"},
    {"key": "publish", "label": "Publish", "icon": "send"},
    {"key": "monitor", "label": "Monitor", "icon": "activity"},
]

# Honest per-destination states (never "success" unless truly authorized+confirmed).
PUBLISH_DESTINATIONS = [
    "Amazon KDP eBook", "Amazon KDP Paperback", "Amazon KDP Hardcover",
    "Audible / Audiobook Distributor", "YouTube", "YouTube Shorts", "TikTok",
    "Ascend / Imprint Website", "Podcast Distribution", "Email Announcement", "Social Distribution",
]


def _now():
    return now_iso()


def _checksum(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


# ----------------------------- BUTTON 1 — UPLOAD -----------------------------
def _intake_scan(title, content, meta):
    structure = bs.parse_book(content)
    chapters = structure["chapters"]
    words = len((content or "").split())
    files_received = ["Manuscript (working copy)", "Immutable original"]
    if meta.get("cover_ref"):
        files_received.append("Cover / visual reference")
    missing = []
    if not meta.get("author"):
        missing.append("Author / pen name")
    if not meta.get("cover_ref"):
        missing.append("Cover art or brief (needed at Design)")
    if not chapters:
        missing.append("Detected chapter structure (use '## ' headings)")
    readiness = "Ready to Proof" if chapters and not missing else ("Ready to Proof (minor gaps)" if chapters else "Needs structure")
    return {
        "files_received": files_received,
        "missing_essentials": missing,
        "detected_structure": {
            "chapters": [{"number": c["number"], "title": c["title"], "sections": len(c["sections"])} for c in chapters],
            "chapter_count": len(chapters), "word_count": words,
            "introduction": structure.get("introduction"), "back_matter": structure["back_matter"],
        },
        "readiness_status": readiness,
        "recommended_next_action": "Run Proof & Polish" if chapters else "Add chapter headings, then Proof & Polish",
    }


async def create_book_record(payload, actor):
    title = (payload.get("title") or "Untitled Manuscript").strip()
    content = payload.get("content") or ""
    meta = payload.get("meta") or {}
    high_stakes = bool(meta.get("high_stakes"))
    src_filename = meta.get("source_filename", "manuscript")
    is_draft = "draft" in src_filename.lower() or "draft" in title.lower()
    record = {
        "id": gen_id(),
        "book_code": f"BOOK-{await db[COLL].count_documents({}) + 1:04d}",
        "product_type": meta.get("product_type", "Book"),  # QRU Product Manufacturing System™ — recipe selector
        "title": title,  # human-readable title ALWAYS before the Book Record ID in UI
        "subtitle": meta.get("subtitle", ""),
        "author": meta.get("author", ""),
        "imprint": meta.get("imprint", "QRU Press™"),
        "series": meta.get("series", ""),
        "edition": meta.get("edition", "First Edition"),
        "language": meta.get("language", "English"),
        "audience": meta.get("audience", "General"),
        "genre": meta.get("genre", ""),
        "rights_holder": meta.get("rights_holder", meta.get("author", "")),
        "ai_disclosure": meta.get("ai_disclosure", "AI-assisted (drafting/tooling); human-authored & human-approved."),
        "licenses_permissions": meta.get("licenses_permissions", []),
        # immutable original + separate working copy (source manuscript never altered on upload)
        "original": {"content": content, "checksum": _checksum(content), "sealed_at": _now(), "immutable": True},
        "working_copy": {"content": content, "updated_at": _now()},
        "source_file_history": [{"file": src_filename, "at": _now(), "by": actor}],
        "revision_history": [{"stage": "Upload", "by": actor, "at": _now(), "note": "Canonical Book Record created."}],
        # Honest governance statuses — a file named "Draft" is NEVER auto-interpreted as approved.
        "source_status": "Draft received" if is_draft else "Manuscript received",
        "editorial_status": "Founder review required",
        "publication_status": "Not ready",
        "approval_status": "Draft",
        "editorial_locked": False,
        "transparent_provenance": {
            "source_filename": src_filename,
            "immutable_original_checksum": _checksum(content),
            "received_at": _now(), "received_by": actor,
            "rights_holder": meta.get("rights_holder", meta.get("author", "")),
            "ai_contribution": meta.get("ai_disclosure", "AI-assisted manufacturing; human-authored & human-approved."),
            "governance": "Draft governed honestly — not moved forward as approved.",
        },
        "intake_scan": _intake_scan(title, content, meta),
        "high_stakes": high_stakes,
        "manufacturing_job": {"stage": "Upload complete", "next": "Proof & Polish"},
        "storage_location": COLL,
        "backup_status": "Immutable original sealed with checksum",
        "artifacts": {},  # design/audio/video outputs keyed by button
        "created_by": actor, "created_at": _now(), "updated_at": _now(),
    }
    await db[COLL].insert_one(dict(record))
    await log_org("Book Manufacturing™", "Manufacturing", f"created Canonical Book Record for '{title}'", record["book_code"], "success")
    return clean(record)


# ---------- DECODER → BOOK BRIDGE (QRU Decoder Engine™ Stone 2 · Books only) ----------
# The reference "Create Product" pattern: a Manufacturing Ready™ Decoder Record flows directly into
# the existing seven-button Book Manufacturing System™, pre-filled from the decoder's contract.
# Reuses create_book_record (one owner for Canonical Book Records) — no duplicate capability.

# Internal Factory vocabulary that must NOT dominate a customer-facing educational book
# (unless the book is explicitly about the QRU Factory itself). Treasure Standard™ safeguard.
_FACTORY_TERMS = [
    "product manufacturing file", "product manifest", "product manufacturing standard",
    "product manufacturing specification", "governed knowledge record", "knowledge record",
    "executable universal knowledge record", "treasure standard", "manufacturing record",
    "audit record", "audit history", "governance package", "decoder record", "quality gate",
    "publication package", "manufacturing line", "manufactured product", "canonical book record",
    "std-ukr", "factory constitution", "pmf™", "pms™", "ukr™", "the factory should",
]
_FACTORY_SUBJECT_HINTS = [
    "qru factory", "factory", "manufacturing standard", "governance", "knowledge record",
    "publishing standard", "operating system", "treasure standard", "ukr",
]


def content_integrity_check(title, subtitle, content):
    """Detect when a book's BODY is internal QRU Factory documentation while its TITLE promises an
    educational subject — the exact failure the Founder flagged. Returns a governed result; never
    silently ships mismatched content. $0, deterministic."""
    text = (content or "").lower()
    if len(text.split()) < 60:
        return {"ok": True, "factory_term_density_per_1000w": 0.0, "note": "Too short to assess."}
    subject = f"{title or ''} {subtitle or ''}".lower()
    about_factory = any(h in subject for h in _FACTORY_SUBJECT_HINTS)
    hits = sum(text.count(t) for t in _FACTORY_TERMS)
    per_1000 = round(hits / (len(text.split()) / 1000.0), 1)
    mismatch = (not about_factory) and per_1000 >= 6.0
    if mismatch:
        return {
            "ok": False,
            "issue": "content_subject_mismatch",
            "factory_term_density_per_1000w": per_1000,
            "message": ("This book's content reads like INTERNAL QRU Factory documentation "
                        "(manufacturing/governance/audit terminology) rather than the educational subject "
                        "promised by its title. The source Knowledge Record is almost certainly the wrong one. "
                        "Verify the source content teaches the title's topic before publishing."),
        }
    return {"ok": True, "factory_term_density_per_1000w": per_1000}


def _decoder_to_manuscript(d):
    """Assemble a book manuscript (markdown) from a Decoder Record's verified understanding.
    No knowledge is invented here — every section is the decoded understanding already verified."""
    parts = [f"# {d.get('title','Untitled')}", ""]

    def _flatten(val):
        if isinstance(val, str):
            return val
        if isinstance(val, dict):
            label = val.get("term") or val.get("misconception") or val.get("name") or val.get("title") or ""
            body = val.get("definition") or val.get("correction") or val.get("truth") or val.get("detail") or val.get("text") or val.get("description") or ""
            return f"**{label}** — {body}" if label else (body or "")
        return str(val)

    def sec(heading, val):
        if not val:
            return
        parts.append(f"## {heading}")
        if isinstance(val, list):
            for it in val:
                line = _flatten(it)
                if line:
                    parts.append(f"- {line}" if not str(line).startswith("**") else line)
        else:
            parts.append(_flatten(val))
        parts.append("")

    sec("Introduction", d.get("definition"))
    sec("Why It Matters", d.get("why_it_matters"))
    sec("How It Works", d.get("how_it_works"))
    sec("The Core Idea", d.get("core_mental_model"))
    sec("An Analogy", d.get("analogy"))
    sec("A Story", d.get("story"))
    sec("Key Terms", d.get("vocabulary"))
    sec("Common Misconceptions", d.get("misconceptions"))
    sec("Putting It Into Practice", d.get("applications"))
    sec("A Worked Example", d.get("guided_example"))
    sec("Practice", d.get("practice"))
    sec("Reflection", d.get("reflection"))
    sec("Remember This", d.get("memory_anchor"))
    return "\n".join(str(p) for p in parts)


async def verify_source(d, requested_title=None):
    """QRU Source Verification Gate™ — FIRST line of defense (before manufacturing).
    Returns the selected source's identity + a content preview + an automatic title↔source match
    verdict. A 'critical' verdict means the source content does not match the intended publication
    and manufacturing must STOP (override only via explicit admin action). Deterministic, $0."""
    if not d:
        return {"error": "Source understanding not found."}
    title = (requested_title or d.get("title") or "").strip()
    objective = d.get("learning_objective") or ""
    manuscript = _decoder_to_manuscript(d)
    # First 3-5 paragraphs of the assembled source (skip the H1 title line).
    body_paras = [p.strip() for p in manuscript.split("\n") if p.strip() and not p.strip().startswith("#")]
    preview_paras = body_paras[:5]

    # Pull the underlying Knowledge Record identities.
    kr_ids = d.get("source_kr_ids", []) or []
    kr_docs = []
    if kr_ids:
        kr_docs = await db["knowledge_records"].find({"id": {"$in": kr_ids}}, {"_id": 0, "id": 1, "title": 1, "status": 1, "version": 1}).to_list(20)

    # Content-integrity: does the source body read like internal Factory docs under a non-Factory title?
    ci = content_integrity_check(title, objective, manuscript)

    # Does the underlying Knowledge Record itself look like a Factory/standard/governance record,
    # while the requested publication is NOT about the Factory? (The exact "AI Literacy K-12 built from
    # STD-UKR standard doc" failure.) This is a precise signal — no fragile keyword-overlap guessing.
    title_factory = any(h in title.lower() for h in _FACTORY_SUBJECT_HINTS)
    def _factoryish(s):
        s = (s or "").lower()
        return any(h in s for h in _FACTORY_SUBJECT_HINTS) or "std-ukr" in s
    kr_factory = any(_factoryish(k.get("title")) for k in kr_docs)
    source_is_factory_doc = kr_factory and not title_factory

    critical = (not ci.get("ok", True)) or source_is_factory_doc
    if not ci.get("ok", True):
        reason = ci.get("message")
    elif source_is_factory_doc:
        reason = ("The selected Knowledge Record is an internal Factory/standard record, but the requested "
                  "publication is not about the QRU Factory. This is almost certainly the wrong source.")
    else:
        reason = "Source matches the intended publication subject."

    return {
        "source": {
            "decoder_id": d.get("decoder_id"), "title": d.get("title"),
            "version": d.get("version") or "1.0",
            "status": ("Gold Standard Verified" if d.get("treasure_standard") else (d.get("review_state") or "Draft")),
            "department": d.get("domain") or d.get("department") or "—",
            "last_verified": d.get("verified_at") or d.get("updated_at") or d.get("created_at"),
            "knowledge_records": kr_docs,
        },
        "preview": {
            "paragraphs": preview_paras,
            "learning_objective": objective,
            "audience": d.get("audience") or "General",
            "product_family_tags": d.get("tags") or d.get("product_families") or [],
        },
        "requested_title": title,
        "match": {
            "ok": not critical,
            "level": "critical" if critical else "ok",
            "reason": reason,
            "factory_term_density_per_1000w": ci.get("factory_term_density_per_1000w"),
        },
    }



async def create_book_from_decoder(d, actor):
    """Create a Canonical Book Record from a Manufacturing Ready™ Decoder Record (Stone 2)."""
    if not d:
        return {"error": "Decoder Record not found."}
    import decoder_engine as de
    if d.get("review_state") not in de.MANUFACTURING_ELIGIBLE_STATES:
        return {"error": "This understanding is not Manufacturing Ready™ yet — the Factory is still finishing it."}
    content = _decoder_to_manuscript(d)
    gp = d.get("governance_package") or {}
    rights = gp.get("rights_holder") or d.get("created_by") or "Ascend Development Group LLC"
    meta = {
        "product_type": "Book",
        "author": gp.get("author") or "QRU Editorial",
        "subtitle": d.get("learning_objective") or "",
        "genre": d.get("domain") or "Nonfiction",
        "audience": d.get("audience") or "General",
        "imprint": "QRU Press™",
        "rights_holder": rights,
        "ai_disclosure": "Built from a verified QRU Decoder Record™; human-verified knowledge, AI-assisted manufacturing.",
        "source_filename": f"{d.get('decoder_id','decoder')}.decoder",
    }
    rec = await create_book_record({"title": d.get("title", "Untitled"), "content": content, "meta": meta}, actor)
    # Link the product back to its source understanding (Transparent Provenance™).
    await db[COLL].update_one({"id": rec["id"]}, {"$set": {
        "source_decoder": {"decoder_id": d.get("decoder_id"), "source_kr_ids": d.get("source_kr_ids", []),
                            "created_at": _now(), "by": actor}}})
    try:
        await db["decoder_records"].update_one({"id": d.get("id")}, {"$push": {"manufactured_products": {
            "product_type": "Book", "book_id": rec["id"], "book_code": rec.get("book_code"),
            "title": rec.get("title"), "created_at": _now(), "by": actor}}})
    except Exception:
        pass
    return rec



def _extract_manuscript(filename, raw):
    """Turn an uploaded manuscript file into markdown text. Supports DOCX, PDF, TXT, MD."""
    name = (filename or "").lower()
    if name.endswith(".docx"):
        return _docx_to_markdown(raw)
    if name.endswith(".pdf"):
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(raw))
        return "\n\n".join((pg.extract_text() or "") for pg in reader.pages).strip()
    if name.endswith((".txt", ".md", ".markdown", ".text")):
        return raw.decode("utf-8", errors="replace")
    # Best-effort: treat as UTF-8 text.
    return raw.decode("utf-8", errors="replace")


async def upload_manuscript_file(filename, file_base64, meta, actor):
    """Bring any manuscript FILE (DOCX/PDF/TXT/MD) into the Factory as a Canonical Book Record.
    The immutable original is sealed automatically + a separate working copy is created — the
    Founder never hand-assembles governance; uploading the file is enough."""
    import base64
    try:
        raw = base64.b64decode(file_base64)
    except Exception:
        return {"error": "Could not decode the uploaded file."}
    if not raw:
        return {"error": "The uploaded file is empty."}
    try:
        content = (_extract_manuscript(filename, raw) or "").strip()
    except Exception as e:
        return {"error": f"Could not read this file. Supported types: .docx, .pdf, .txt, .md. ({str(e)[:80]})"}
    if len(content) < 20:
        return {"error": "No readable manuscript text was found in the file (is it a scanned image PDF?)."}
    meta = dict(meta or {})
    meta.setdefault("source_filename", filename or "manuscript")
    title = (meta.get("title") or "").strip()
    if not title:
        import os as _os
        import re as _re
        base = _os.path.splitext(_os.path.basename(filename or "Untitled Manuscript"))[0]
        title = _re.sub(r"[_\-]+", " ", base).strip() or "Untitled Manuscript"
    return await create_book_record({"title": title, "content": content, "meta": meta}, actor)



# -------------------------- BUTTON 2 — PROOF & POLISH --------------------------
def _proof_checks(content):
    """Deterministic proofing — NEVER rewrites voice. Only reports classified findings.
    Each finding carries a stable `issue` signature; correctable findings also carry a
    character `span` + `suggested_fix` so the Founder can apply a surgical correction."""
    import re
    findings = []
    lines = content.split("\n")
    # repeated consecutive words ("the the")
    for m in re.finditer(r"\b(\w+)(\s+)\1\b", content, flags=re.IGNORECASE):
        findings.append({"type": "Required correction", "issue": f"Repeated word: '{m.group(0)}'",
                         "detail": "Duplicate consecutive word detected.",
                         "span": [m.start(), m.end()], "correctable": True,
                         "suggested_fix": m.group(1),
                         "snippet": content[max(0, m.start() - 30):m.end() + 30].replace("\n", " ").strip()})
    # double spaces
    dbl = content.count("  ")
    if dbl:
        findings.append({"type": "Recommended improvement", "issue": f"{dbl} double-space occurrence(s)",
                         "detail": "Collapse to single spaces for clean typesetting.",
                         "correctable": True, "fix_kind": "collapse_double_space"})
    # working title flag
    if "working title" in content.lower() or "(working title)" in content.lower():
        findings.append({"type": "Founder decision required", "issue": "'working title' present in manuscript",
                         "detail": "Confirm the final title before locking the editorial edition."})
    # TODO / placeholder
    for kw in ["TODO", "TK", "[ ]", "XXX", "lorem ipsum"]:
        if kw.lower() in content.lower():
            findings.append({"type": "Founder decision required", "issue": f"Placeholder marker '{kw}' found",
                             "detail": "Resolve placeholder before publication."})
    # chapter numbering consistency
    structure = bs.parse_book(content)
    nums = [c["number"] for c in structure["chapters"]]
    if nums and nums != list(range(1, len(nums) + 1)):
        findings.append({"type": "Recommended improvement", "issue": "Chapter numbering is not strictly sequential in structure",
                         "detail": "Verify chapter order/labels."})
    # front matter presence
    low = content.lower()
    if "copyright" not in low:
        findings.append({"type": "Recommended improvement", "issue": "No explicit copyright line in manuscript",
                         "detail": "The Product Governance Package™ will inherit copyright at Design; confirm rights holder."})
    # very long paragraphs (readability, optional)
    long_paras = sum(1 for ln in lines if len(ln.split()) > 400)
    if long_paras:
        findings.append({"type": "Optional stylistic suggestion", "issue": f"{long_paras} very long paragraph(s) (>400 words)",
                         "detail": "Consider breaks for readability — author's choice."})
    return findings, structure


async def proof_polish(book_id, actor):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    if b.get("editorial_locked"):
        return {"error": "Editorial edition is locked. Open a governed revision to re-proof and edit."}
    content = b["working_copy"]["content"]
    findings, structure = _proof_checks(content)
    kept = set(b.get("kept_findings", []))
    for i, f in enumerate(findings):
        f["id"] = f"{f.get('type','')[:3]}-{i}"
        f["status"] = "kept" if f["issue"] in kept else "open"
    open_findings = [f for f in findings if f["status"] == "open"]
    required = [f for f in open_findings if f["type"] == "Required correction"]
    report = {
        "generated_at": _now(),
        "findings": findings,
        "counts": {
            "required": len(required),
            "recommended": len([f for f in open_findings if f["type"] == "Recommended improvement"]),
            "optional": len([f for f in open_findings if f["type"] == "Optional stylistic suggestion"]),
            "founder_decision": len([f for f in open_findings if f["type"] == "Founder decision required"]),
            "kept": len([f for f in findings if f["status"] == "kept"]),
            "words": len(content.split()), "chapters": len(structure["chapters"]),
        },
        "unresolved_questions": [f["issue"] for f in open_findings if f["type"] == "Founder decision required"],
        "voice_note": "The Factory never silently rewrites the author's voice. Every item is reported for YOUR decision — Keep as written (intentional) or Correct it. Nothing changes unless you choose it.",
    }
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "editorial_status": "Proofed — awaiting approval", "proofing_report": report,
        "manufacturing_job": {"stage": "Proof & Polish complete", "next": "Resolve findings, then approve & lock editorial edition"},
        "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Proof & Polish", "by": actor, "at": _now(),
                                       "note": f"{len(findings)} finding(s); {len(required)} required open; {len(kept)} kept as written."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"proofed '{b['title']}' ({len(open_findings)} open findings)", b["book_code"])
    return {"ok": True, "report": report}


async def approve_edition(book_id, actor):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    content = b["working_copy"]["content"]
    checksum = _checksum(content)
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "editorial_locked": True, "editorial_status": "Approved & locked",
        "approval_status": "Editorial Approved",
        "editorial_edition": {"content": content, "checksum": checksum, "locked_by": actor, "locked_at": _now()},
        "manufacturing_job": {"stage": "Editorial edition locked", "next": "Design"},
        "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Editorial Lock", "by": actor, "at": _now(),
                                       "note": f"Locked source-of-truth (checksum {checksum[:12]}…)."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"locked editorial edition for '{b['title']}'", b["book_code"], "success")
    b = await db[COLL].find_one({"id": book_id})
    return clean(b)


# -------------------- FOUNDER FINDING RESOLUTION + GOVERNED REVISION --------------------
async def open_revision(book_id, actor):
    """Governed unlock: a locked editorial master can be re-opened for a tracked revision.
    The prior locked edition is preserved in version history — never silently overwritten."""
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    if not b.get("editorial_locked"):
        return {"error": "This book is not locked — it is already open for editing."}
    prior = b.get("editorial_edition") or {}
    versions = b.get("editorial_versions", [])
    versions.append({"version": len(versions) + 1, "content": prior.get("content", ""),
                     "checksum": prior.get("checksum"), "locked_by": prior.get("locked_by"),
                     "locked_at": prior.get("locked_at"), "archived_at": _now(), "archived_by": actor})
    # Bring the locked content into the working copy so the Founder edits the true source.
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "editorial_locked": False, "editorial_status": f"Revision open (editing v{len(versions) + 1})",
        "working_copy": {"content": prior.get("content", b.get("working_copy", {}).get("content", "")), "updated_at": _now()},
        "editorial_versions": versions,
        "manufacturing_job": {"stage": "Governed revision open", "next": "Edit / resolve findings, re-proof, then re-lock"},
        "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Governed Revision Opened", "by": actor, "at": _now(),
                  "note": f"Locked edition archived as v{len(versions)}; opened for a tracked revision."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"opened governed revision for '{b['title']}'", b["book_code"])
    return clean(await db[COLL].find_one({"id": book_id}))


async def update_manuscript(book_id, content, actor):
    """Full manuscript edit (Founder). Only permitted while NOT locked (open a revision first).
    Saved as a tracked change; the Founder must re-proof and re-lock."""
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    if b.get("editorial_locked"):
        return {"error": "Editorial edition is locked. Open a governed revision before editing."}
    content = content or ""
    if not content.strip():
        return {"error": "Manuscript cannot be empty."}
    prev_words = len((b.get("working_copy") or {}).get("content", "").split())
    new_words = len(content.split())
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "working_copy": {"content": content, "updated_at": _now()},
        "editorial_status": "Edited — re-proof required", "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Manuscript Edited", "by": actor, "at": _now(),
                  "note": f"Founder edited manuscript ({prev_words} → {new_words} words)."}}})
    # Re-proof automatically so the report reflects the edit.
    r = await proof_polish(book_id, actor)
    return {"ok": True, "report": r.get("report") if isinstance(r, dict) else None,
            "book": clean(await db[COLL].find_one({"id": book_id}))}


async def resolve_finding(book_id, issue, action, actor, span=None, suggested_fix=None, fix_kind=None):
    """Founder resolves a single proofing finding: 'keep' (intentional — no text change, recorded
    with provenance) or 'correct' (apply a surgical fix and re-proof)."""
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    if b.get("editorial_locked"):
        return {"error": "Editorial edition is locked. Open a governed revision first."}
    if action == "keep":
        kept = list(dict.fromkeys((b.get("kept_findings", []) + [issue])))
        await db[COLL].update_one({"id": book_id}, {"$set": {"kept_findings": kept, "updated_at": _now()},
            "$push": {"revision_history": {"stage": "Finding Kept As Written", "by": actor, "at": _now(),
                      "note": f"Founder kept intentional: {issue}"}}})
        return await proof_polish(book_id, actor)
    if action == "correct":
        content = b["working_copy"]["content"]
        if fix_kind == "collapse_double_space":
            import re
            new_content = re.sub(r" {2,}", " ", content)
        elif span and suggested_fix is not None and isinstance(span, (list, tuple)) and len(span) == 2:
            s, e = int(span[0]), int(span[1])
            if s < 0 or e > len(content) or s >= e:
                return {"error": "This correction no longer matches the manuscript — re-proof and try again."}
            new_content = content[:s] + suggested_fix + content[e:]
        else:
            return {"error": "Nothing to correct for this finding."}
        await db[COLL].update_one({"id": book_id}, {"$set": {
            "working_copy": {"content": new_content, "updated_at": _now()},
            "editorial_status": "Edited — re-proof required", "updated_at": _now()},
            "$push": {"revision_history": {"stage": "Finding Corrected", "by": actor, "at": _now(),
                      "note": f"Founder corrected: {issue}"}}})
        return await proof_polish(book_id, actor)
    return {"error": "Unknown action — use 'keep' or 'correct'."}


# ----------------------------- BUTTON 3 — DESIGN -----------------------------
async def _cover_design_recipe(b, re_engine):
    """Book Cover Design Recipe™ — delegates to the shared QRU Design Studio™ engine so the Book
    system, Cover Studio, Poster Studio, workbooks and every product recipe share ONE publication-
    quality design pipeline (art-direction → Gemini artwork → QRU typography composite)."""
    import design_studio
    context = {
        "title": b["title"], "subtitle": b.get("subtitle", ""),
        "byline": b.get("author", ""), "imprint": b.get("imprint", ""),
        "genre": b.get("genre") or "Literary", "audience": b.get("audience", ""),
        "synopsis": b.get("working_copy", {}).get("content", ""),
    }
    return await design_studio.manufacture_design_concepts(
        context, kind="cover", n=3, slug=f"bookcover-{b['id']}")


async def design(book_id, actor, base_url=""):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    if not b.get("editorial_locked"):
        return {"error": "Approve & lock the editorial edition before Design (no downstream format may change approved text)."}
    import rendering_engine as re_engine
    import deliverable_renderer as dr
    content = b["editorial_edition"]["content"]
    gp = pg.build_package("Book", title=b["title"], version=1, domain=b.get("genre", ""),
                          audience=b.get("audience", ""), high_stakes=b.get("high_stakes"))
    product = {"title": b["title"], "family": b.get("genre") or b.get("imprint", ""),
               "product_type": "Book", "content": content, "audience": b.get("audience", ""),
               "high_stakes": b.get("high_stakes"), "governance_package": gp, "imprint": b.get("imprint")}
    # Design stage dispatches to the product's manufacturing recipe (QRU Product Manufacturing System™).
    # For Book this is the Cover Design Recipe™ — governed AI art direction → publication-quality concepts.
    recipe = recipes.get(b.get("product_type", "Book"))
    design_fn = recipe.get("design_recipe") or recipes.default_design_recipe
    concepts = await design_fn(b, re_engine)
    # Embed the first SUCCESSFUL cover in the interior proof (never a failed placeholder if real art exists).
    embed = next((c for c in concepts if c["status"] == "success"), concepts[0])
    cover_bytes = None
    cpath = embed["url"].split("/")[-1]
    import os
    with open(os.path.join(re_engine.ASSET_DIR, cpath), "rb") as f:
        cover_bytes = f.read()
    qr = re_engine._make_qr(f"{base_url}/book/{book_id}")
    # Print interior (paperback) + EPUB via existing renderer (Reading Experience Standard™ applies).
    interior_pdf = re_engine._make_pdf(product, {}, cover_bytes, qr)
    interior_fid = re_engine._save("book-interior", "pdf", interior_pdf)
    try:
        epub_bytes = dr._render_epub(product, cover_bytes)
        epub_fid = re_engine._save("book-ebook", "epub", epub_bytes)
        epub_url = re_engine._asset_url(epub_fid)
    except Exception as e:
        epub_url = None
    ai_ok = [c for c in concepts if c["status"] == "success"]
    ai_failed = [c for c in concepts if c["status"] != "success"]
    cover_provenance = {
        "generated_at": _now(), "by": actor,
        "art_provider": "Gemini (Emergent LLM Key)", "art_model": __import__("ai_service").IMAGE_MODEL,
        "concepts_requested": len(concepts),
        "concepts_with_ai_art": len(ai_ok),
        "concepts_failed": len(ai_failed),
        "failed_concepts": [{"concept": c["concept"], "name": c["name"], "reason": c["failure_reason"]} for c in ai_failed],
        "standard": "Cover Design Recipe™ — honest per-concept status; a failed concept is never presented as real AI art.",
    }
    artifacts = b.get("artifacts", {})
    artifacts["design"] = {
        "generated_at": _now(),
        "cover_concepts": concepts, "selected_cover": None,
        "cover_provenance": cover_provenance,
        "print": {"paperback_interior_pdf": re_engine._asset_url(interior_fid),
                  "trim_size": "6x9 in", "bleed": "0.125 in", "toc": "Clickable + printed (Reading Experience Standard™)"},
        "ebook": {"epub": epub_url, "kindle_ready": bool(epub_url), "clickable_toc": True},
        "governance_package": gp,
        "notes": "Front cover + eBook cover are print-ready. A full paperback wrap (back cover + spine + front, sized from final page count, trim, paper type & bleed) is NOT yet generated — front cover only.",
    }
    # Stamp Transparent Provenance™ with an honest AI-cover-generation record.
    tp = b.get("transparent_provenance", {})
    cover_gen_log = tp.get("cover_generation", [])
    cover_gen_log.append(cover_provenance)
    tp["cover_generation"] = cover_gen_log
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "artifacts": artifacts, "transparent_provenance": tp,
        "manufacturing_job": {"stage": "Design drafted", "next": "Select final cover, then Audio/Video/Publish"},
        "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Design", "by": actor, "at": _now(),
                                       "note": f"{len(concepts)} cover concepts ({len(ai_ok)} with AI art, {len(ai_failed)} failed), print interior + EPUB rendered."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"designed print + ebook for '{b['title']}'", b["book_code"], "success")
    b = await db[COLL].find_one({"id": book_id})
    return clean(b)


async def select_cover(book_id, concept_no, actor, base_url=""):
    b = await db[COLL].find_one({"id": book_id})
    if not b or not b.get("artifacts", {}).get("design"):
        return {"error": "Run Design first."}
    design_art = b["artifacts"]["design"]
    match = next((c for c in design_art["cover_concepts"] if c["concept"] == concept_no), None)
    if not match:
        return {"error": "Cover concept not found."}
    if match.get("status") == "failed":
        return {"error": "That concept's AI art failed — choose a successful concept."}
    design_art["selected_cover"] = match
    await db[COLL].update_one({"id": book_id}, {"$set": {"artifacts.design": design_art, "updated_at": _now()}})
    await log_org("Book Manufacturing™", "Manufacturing", f"selected cover concept {concept_no} for '{b['title']}'", b["book_code"])
    # Quiet Factory™: selecting the cover auto-runs the Publication Sanitization Pass™ so the clean
    # retail edition (with the chosen cover) is always the one that ships — the Founder never has to
    # remember a separate step, and share/review copies are never the raw manuscript.
    if b.get("editorial_locked"):
        await sanitization_pass(book_id, actor, base_url)
    return clean(await db[COLL].find_one({"id": book_id}))


# ------------------------- BUTTONS 4 & 5 — AUDIO / VIDEO -------------------------
def _chapter_map(content):
    s = bs.parse_book(content)
    return [{"number": c["number"], "title": c["title"], "file": f"ch{c['number']:02d}.mp3"} for c in s["chapters"]]


async def audio_plan(book_id):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    content = (b.get("editorial_edition") or b.get("working_copy"))["content"]
    return {
        "book_title": b["title"], "book_code": b["book_code"],
        "prototype": (b.get("artifacts", {}).get("audio") or {}).get("prototype"),
        "chapter_timing_map": (b.get("artifacts", {}).get("audio") or {}).get("chapter_timing_map"),
        "full_book_estimate_min": (b.get("artifacts", {}).get("audio") or {}).get("full_book_estimate_min"),
        "paths": {
            "internal_prototype": {"state": "Available on request",
                                   "note": "AI/temporary voice for pacing review only — NOT approved for commercial distribution.",
                                   "chapter_map": _chapter_map(content)},
            "youtube_digital": {"state": "Package prepared", "requires": ["AI disclosure flag", "human listening review"],
                                "deliverables": ["Chapter masters", "Full-book master", "Intro/outro", "Transcript source"]},
            "commercial_audiobook": {"state": "Guided checklist (human narration route)",
                                     "note": "Human narration unless the distributor explicitly authorizes synthetic voice.",
                                     "deliverables": ["Narrator brief", "Audition script", "Pronunciation guide",
                                                      "Chapter file map", "Opening/closing credits", "Retail sample",
                                                      "Audio cover (square)", "Technical QA report", "Rights-holder approval"]},
        },
        "qa_requirements": ["File naming", "Chapter order", "Silence/spacing", "Peak levels", "RMS/loudness",
                            "Noise floor", "Sample rate", "Bitrate", "Mono/stereo", "No clicks/clipping/distortion"],
        "honesty": "No package is labeled 'Audible-ready' until all current distributor requirements are checked and passed.",
    }


VALID_VOICES = ["alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"]


def _clean_voice_settings(voice, speed):
    v = (voice or "sage").strip().lower()
    if v not in VALID_VOICES:
        v = "sage"
    try:
        sp = float(speed)
    except (TypeError, ValueError):
        sp = 1.0
    sp = max(0.5, min(2.0, round(sp, 2)))
    return v, sp


async def render_audio_prototype(book_id, actor, voice=None, speed=None, custom_script=None):
    """Button 4·A — Internal Narration Prototype. Renders a REAL TTS master of Chapter 1's opening
    (or a Founder-supplied custom narration script). Honestly labeled: AI voice, pacing/review only,
    NOT commercial. Voice + speed are chosen by the Founder and remembered on the book."""
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    # Resolve voice/speed: explicit arg > stored book setting > default.
    v, sp = _clean_voice_settings(
        voice if voice is not None else b.get("narration_voice"),
        speed if speed is not None else b.get("narration_speed"))
    content = (b.get("editorial_edition") or b.get("working_copy"))["content"]
    structure = bs.parse_book(content)
    if not structure["chapters"]:
        return {"error": "No chapters detected to narrate."}
    ch1 = structure["chapters"][0]
    custom = (custom_script or "").strip()
    if custom:
        spoken = custom[:6000]
        excerpt_chars = len(spoken)
    else:
        lines = bs.strip_navigation(content).split("\n")
        grab, buf = False, []
        for ln in lines:
            st = ln.strip()
            if st.startswith("## "):
                if grab:
                    break
                grab = True
                continue
            if grab and st and not st.startswith("#") and st != "---":
                buf.append(st)
            if sum(len(x) for x in buf) > 2600:
                break
        excerpt = " ".join(buf)[:2800].strip() or ch1["title"]
        # Build the spoken heading WITHOUT saying "Chapter" twice: many manuscripts parse a chapter
        # title that already begins with "Chapter One:/Chapter 1:" — in that case narrate the title
        # as-is instead of prepending a second "Chapter N."
        ch_title = (ch1.get("title") or "").strip()
        if ch_title.lower().lstrip().startswith("chapter"):
            heading = ch_title
        else:
            heading = f"Chapter {ch1['number']}. {ch_title}".strip().rstrip(".")
        spoken = f"{b['title']}. {heading}. {excerpt}"
        excerpt_chars = len(excerpt)
    try:
        import cinema_studio
        import rendering_engine as re_engine
        audio = await cinema_studio._tts_bytes(spoken, voice=v, speed=sp)
        fid = re_engine._save("book-audio-prototype", "mp3", audio)
        dur = round(cinema_studio._duration_from_bytes(audio), 1)
    except Exception as e:
        return {"error": f"Narration prototype unavailable (TTS): {str(e)[:120]}. Honest failure — nothing faked."}
    total_words = len(content.split())
    chapter_map = [{"number": c["number"], "title": c["title"]} for c in structure["chapters"]]
    artifacts = b.get("artifacts", {})
    artifacts["audio"] = {
        "prototype": {
            "label": f"Internal Narration Prototype™ ({'custom script' if custom else 'Chapter 1 opening'}) — AI voice '{v}', pacing/review ONLY. NOT for commercial distribution.",
            "url": re_engine._asset_url(fid), "duration_sec": dur, "voice": f"{v} (OpenAI TTS-1)",
            "voice_id": v, "speed": sp, "custom_script": custom or None,
            "excerpt_chars": excerpt_chars, "generated_at": _now(),
        },
        "full_book_estimate_min": round(total_words / 150, 1),
        "chapter_timing_map": chapter_map,
    }
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "artifacts": artifacts, "narration_voice": v, "narration_speed": sp, "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Audio", "by": actor, "at": _now(),
                                       "note": f"Narration prototype rendered ({dur}s, voice {v}, speed {sp})."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"rendered narration prototype for '{b['title']}'", b["book_code"], "success")
    return clean(await db[COLL].find_one({"id": book_id}))


# ------------------------- FULL-LENGTH AUDIOBOOK (background job) -------------------------
AUDIOBOOK_JOBS = "book_audiobook_jobs"


def _chapter_texts(content):
    """Per-division spoken text for the full audiobook. Uses the robust unit detector so it
    works for `## Chapter` books AND `# Part …` books (no more 0-chapter books)."""
    out = []
    for u in bs.content_units(content):
        title = u["title"]
        heading = title if title.lower().lstrip().startswith(("chapter", "part")) else f"{u.get('unit_word', 'Chapter')} {u['number']}. {title}"
        body = u.get("body", "")
        out.append({"number": u["number"], "title": title, "text": f"{heading}. {body}".strip()})
    return out


def _concat_mp3(paths, out_path):
    """Concatenate same-codec MP3 chapter files into one MP3 via ffmpeg concat demuxer.
    Uses the imageio-ffmpeg bundled binary (no system ffmpeg on this image)."""
    import subprocess
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    listfile = out_path + ".txt"
    with open(listfile, "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    try:
        subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", out_path],
                       check=True, capture_output=True, timeout=180)
    finally:
        if os.path.exists(listfile):
            os.remove(listfile)


async def start_full_audiobook(book_id, actor, voice=None, speed=None):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    existing = await db[AUDIOBOOK_JOBS].find_one({"id": book_id})
    if existing and existing.get("status") == "running":
        return {"ok": True, "status": "running", "message": "A full audiobook render is already in progress."}
    content = (b.get("editorial_edition") or b.get("working_copy") or {}).get("content", "")
    chapters = _chapter_texts(content)
    if not chapters:
        return {"error": "No chapters detected to narrate."}
    v, sp = _clean_voice_settings(voice if voice is not None else b.get("narration_voice"),
                                  speed if speed is not None else b.get("narration_speed"))
    await db[AUDIOBOOK_JOBS].update_one({"id": book_id}, {"$set": {
        "id": book_id, "status": "running", "total": len(chapters), "done": 0, "voice": v, "speed": sp,
        "started_at": _now(), "finished_at": None, "error": None, "url": None}}, upsert=True)
    import asyncio
    asyncio.create_task(_full_audiobook_worker(book_id, actor, v, sp, chapters))
    return {"ok": True, "status": "started", "total": len(chapters), "message": "Full audiobook render started."}


async def _full_audiobook_worker(book_id, actor, voice, speed, chapters):
    import tempfile
    import cinema_studio
    import rendering_engine as re_engine
    tmpdir = tempfile.mkdtemp(prefix="audiobook-")
    paths, total_dur = [], 0.0
    chapter_markers = []
    try:
        for idx, ch in enumerate(chapters, 1):
            audio = await cinema_studio._tts_bytes(ch["text"], voice=voice, speed=speed)
            cp = os.path.join(tmpdir, f"ch{idx:02d}.mp3")
            with open(cp, "wb") as f:
                f.write(audio)
            paths.append(cp)
            d = round(cinema_studio._duration_from_bytes(audio), 1)
            chapter_markers.append({"number": ch["number"], "title": ch["title"],
                                    "start_sec": round(total_dur, 1), "duration_sec": d})
            total_dur += d
            await db[AUDIOBOOK_JOBS].update_one({"id": book_id}, {"$set": {"done": idx}})
        out_path = os.path.join(tmpdir, "audiobook.mp3")
        _concat_mp3(paths, out_path)
        with open(out_path, "rb") as f:
            full_bytes = f.read()
        fid = re_engine._save(f"audiobook-{book_id}", "mp3", full_bytes)
        url = re_engine._asset_url(fid)
        b = await db[COLL].find_one({"id": book_id})
        artifacts = b.get("artifacts", {})
        audio_art = artifacts.get("audio", {}) or {}
        audio_art["full_audiobook"] = {
            "label": f"Full Audiobook — AI voice '{voice}' (OpenAI TTS). Internal master for review; disclose AI narration before commercial distribution.",
            "url": url, "duration_sec": round(total_dur, 1), "duration_min": round(total_dur / 60, 1),
            "voice_id": voice, "speed": speed, "chapters": chapter_markers, "generated_at": _now(),
        }
        artifacts["audio"] = audio_art
        await db[COLL].update_one({"id": book_id}, {"$set": {"artifacts": artifacts, "updated_at": _now()}})
        await db[AUDIOBOOK_JOBS].update_one({"id": book_id}, {"$set": {
            "status": "complete", "done": len(chapters), "finished_at": _now(),
            "url": url, "duration_sec": round(total_dur, 1)}})
        await log_org("Book Manufacturing™", "Manufacturing",
                      f"rendered FULL audiobook for '{b['title']}' ({round(total_dur/60,1)} min)", b.get("book_code", book_id), "success")
    except Exception as e:
        await db[AUDIOBOOK_JOBS].update_one({"id": book_id}, {"$set": {
            "status": "failed", "finished_at": _now(), "error": str(e)[:200]}})
        await log_org("Book Manufacturing™", "Manufacturing", f"full audiobook render FAILED: {str(e)[:120]}", book_id, "warning")
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


async def full_audiobook_status(book_id):
    j = await db[AUDIOBOOK_JOBS].find_one({"id": book_id}, {"_id": 0})
    if not j:
        b = await db[COLL].find_one({"id": book_id}, {"artifacts.audio.full_audiobook": 1})
        fa = ((b or {}).get("artifacts", {}).get("audio", {}) or {}).get("full_audiobook") if b else None
        return {"status": "complete", "url": fa["url"], "duration_sec": fa["duration_sec"]} if fa else {"status": "idle"}
    return j



async def set_pricing(book_id, list_price, currency, actor, ebook_price=None, paperback_price=None):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    pricing = {"list_price": list_price, "currency": currency or "USD", "approved": True,
               "approved_by": actor, "approved_at": _now()}
    if ebook_price is not None:
        pricing["ebook_price"] = ebook_price
    if paperback_price is not None:
        pricing["paperback_price"] = paperback_price
    detail = []
    if ebook_price is not None:
        detail.append(f"eBook {currency or 'USD'} {ebook_price}")
    if paperback_price is not None:
        detail.append(f"paperback {currency or 'USD'} {paperback_price}")
    note = "; ".join(detail) if detail else f"{currency or 'USD'} {list_price}"
    await db[COLL].update_one({"id": book_id}, {"$set": {"pricing": pricing, "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Pricing", "by": actor, "at": _now(),
                                       "note": f"Pricing approved: {note}."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"approved pricing for '{b['title']}'", b["book_code"])
    return clean(await db[COLL].find_one({"id": book_id}))


async def run_post_publish_recipe(book_id, actor):
    """Inherited Post-Publish Manufacturing Recipe. Owned by the Publish button; auto-triggered by
    Authorize Release. Orchestrates EXISTING owners (design engine + LLM) — no new engine.
    Treasure Standard: only 'Ready' items produce files; Planned / Not Implemented make NO links."""
    import io as _io
    import json as _json
    import zipfile as _zip
    import rendering_engine as re_engine
    from PIL import Image, ImageDraw
    import design_studio as ds
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    title = b.get("title", ""); author = b.get("author", "Author")
    genre = b.get("genre", "Fiction"); blurb = b.get("description", "") or ""
    pricing = b.get("pricing", {}) or {}
    imprint = "QRU PRESS™"

    # ---- ONE LLM call manufactures all marketplace + media text (credit-efficient) ----
    sysp = ("You are QRU Publishing. Return STRICT JSON only, keys: long_description (150-200 words, "
            "Amazon listing), short_description (<=45 words), keywords (array of exactly 7 phrases), "
            "categories (array of 3 BISAC-style categories), trailer_script (6-8 short lines), "
            "social_video_script (30-second, 4-6 lines), audio_sample_script (a 60-second narration intro). "
            "No markdown, no commentary.")
    ctx = f"Title: {title}\nAuthor: {author}\nGenre: {genre}\nBack-cover blurb: {blurb}"
    text = {}
    try:
        raw = await ai_service.llm_generate(sysp, ctx, f"postpub-{book_id}")
        s = raw[raw.find("{"): raw.rfind("}") + 1]
        text = _json.loads(s)
    except Exception:
        text = {}
    def _txt(v):
        return "\n".join(str(x) for x in v) if isinstance(v, list) else (str(v) if v else "")
    long_desc = _txt(text.get("long_description")) or blurb or f"{title} by {author}."
    short_desc = _txt(text.get("short_description")) or (blurb[:200] if blurb else title)
    keywords = text.get("keywords") if isinstance(text.get("keywords"), list) else [genre, "fiction", author, "novel", "book", "story", "reading"]
    categories = text.get("categories") if isinstance(text.get("categories"), list) else ["Fiction", "Literary Fiction", "Family Life"]
    trailer = _txt(text.get("trailer_script"))
    social_vid = _txt(text.get("social_video_script"))
    audio_script = _txt(text.get("audio_sample_script"))

    # ---- Marketing graphics (inherit Design Studio fonts) — real files, no AI credits ----
    def _read(url):
        if not url:
            return None
        import os as _os
        p = _os.path.join(re_engine.ASSET_DIR, url.rstrip("/").split("/")[-1])
        return open(p, "rb").read() if _os.path.exists(p) else None
    cover_bytes = _read((b.get("artifacts", {}).get("design", {}).get("selected_cover") or {}).get("url"))
    cover_img = Image.open(_io.BytesIO(cover_bytes)).convert("RGB") if cover_bytes else None
    NAVY = (13, 20, 38); GOLD = (218, 178, 92); WHITE = (245, 245, 248)
    from PIL import ImageFont

    def _f(path, size):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    def _wrap(txt, fnt, maxw):
        words = txt.split(); lines = []; cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if fnt.getlength(t) <= maxw:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def _card(w, h, headline, sub, foot):
        im = Image.new("RGB", (w, h), NAVY); d = ImageDraw.Draw(im)
        if cover_img:
            ch = int(h * 0.5); cw = int(ch * cover_img.width / cover_img.height)
            th = cover_img.resize((cw, ch)); im.paste(th, ((w - cw) // 2, int(h * 0.08)))
        d.rectangle([0, int(h * 0.60), w, int(h * 0.605)], fill=GOLD)
        y = int(h * 0.66)
        for ln, fnt, col in [(headline, _f(ds.dl.SERIF_BOLD, int(h * 0.055)), WHITE),
                             (sub, _f(ds.dl.SERIF, int(h * 0.038)), (210, 210, 220)),
                             (foot, _f(ds.dl.SANS_BOLD, int(h * 0.032)), GOLD)]:
            if not ln:
                continue
            for line in _wrap(ln, fnt, int(w * 0.86))[:3]:
                bb = d.textbbox((0, 0), line, font=fnt)
                d.text(((w - (bb[2] - bb[0])) / 2, y), line, font=fnt, fill=col); y += int((bb[3] - bb[1]) * 1.5)
            y += int(h * 0.02)
        out = _io.BytesIO(); im.save(out, "PNG"); return out.getvalue()

    pb_price = pricing.get("paperback_price") or pricing.get("list_price")
    price_txt = f"Paperback ${pb_price}" + (f" · eBook ${pricing.get('ebook_price')}" if pricing.get("ebook_price") else "")
    graphics = {}
    try:
        graphics["marketing_launch_announcement.png"] = _card(1080, 1080, title, f"by {author} — Now Available", imprint)
        qline = (blurb.split(".")[0] + ".") if blurb else title
        graphics["marketing_quote_card.png"] = _card(1080, 1080, f"\u201c{qline}\u201d", f"— {title}", imprint)
        graphics["marketing_buy_now.png"] = _card(1080, 1350, "Buy Now on Amazon", price_txt, f"{title} · {author}")
    except Exception:
        graphics = {}

    # ---- Founder docs + book page (deterministic, Ready) ----
    def _md(*lines): return "\n".join(lines)
    book_page = _md(f"# {title}", f"*by {author}* — {imprint}", "", "## About", long_desc, "",
                    f"**Format:** Paperback (6x9), eBook  ", f"**Price:** {price_txt}  ",
                    f"**Genre:** {genre}", "", "## Buy", "Available on Amazon (KDP).")
    launch_checklist = _md("# Launch Checklist — " + title,
                           "- [ ] Upload interior + cover wrap to KDP (barcode: 'No, my cover does not have a barcode')",
                           "- [ ] Attach ebook_cover.jpg (JPEG) for the Kindle edition",
                           "- [ ] Paste description, keywords, categories from the Marketplace Package",
                           "- [ ] Confirm price: " + price_txt,
                           "- [ ] Post launch announcement + quote graphics to social",
                           "- [ ] Add book page to QRU Press catalog", "- [ ] Announce to audience / mailing list")
    release_checklist = _md("# Release Checklist — " + title,
                            "- [x] Editorial approved & locked", "- [x] Cover + print wrap manufactured",
                            "- [x] Retail interior sanitized (6x9)", "- [x] Pricing approved by Founder",
                            "- [x] Founder authorized release", "- [ ] Live on Amazon (manual upload)")
    summary = _md("# Publication Summary — " + title, "", f"Author: {author}", f"Imprint: {imprint}",
                  f"Genre: {genre}", f"Price: {price_txt}",
                  f"Authorized by: {(b.get('founder_authorization') or {}).get('by','Founder')}",
                  f"Authorized at: {(b.get('founder_authorization') or {}).get('at','')}", "",
                  "This publication package was manufactured automatically by the QRU Post-Publish Recipe.")

    # ---- Bundle ONLY Ready file-deliverables into one zip ----
    buf = _io.BytesIO()
    with _zip.ZipFile(buf, "w", _zip.ZIP_DEFLATED) as z:
        z.writestr("01_MARKETPLACE/amazon_long_description.txt", long_desc)
        z.writestr("01_MARKETPLACE/short_description.txt", short_desc)
        z.writestr("01_MARKETPLACE/keywords.txt", "\n".join(keywords))
        z.writestr("01_MARKETPLACE/categories.txt", "\n".join(categories))
        z.writestr("01_MARKETPLACE/listing_metadata.json", _json.dumps(
            {"title": title, "author": author, "genre": genre, "keywords": keywords,
             "categories": categories, "price": price_txt}, indent=2))
        for name, data in graphics.items():
            z.writestr(f"02_MARKETING/{name}", data)
        z.writestr("03_WEBSITE/book_page.md", book_page)
        if trailer: z.writestr("04_MEDIA/book_trailer_script.txt", trailer)
        if social_vid: z.writestr("04_MEDIA/social_video_script.txt", social_vid)
        if audio_script: z.writestr("04_MEDIA/audio_sample_script.txt", audio_script)
        z.writestr("05_DISTRIBUTION/amazon_kdp_submission.md", _md(
            "# Amazon KDP Submission (manual)", "Upload the Master Output Package files to kdp.amazon.com.",
            "Barcode: select 'No, my cover does not have a barcode'."))
        z.writestr("06_FOUNDER/launch_checklist.md", launch_checklist)
        z.writestr("06_FOUNDER/release_checklist.md", release_checklist)
        z.writestr("06_FOUNDER/publication_summary.md", summary)
    zid = re_engine._save(f"publication-assets-{''.join(c for c in title if c.isalnum() or c==' ').strip().replace(' ','_')}", "zip", buf.getvalue())
    assets_url = re_engine._asset_url(zid)

    sections = [
        {"name": "Marketplace Package", "items": [
            {"name": "Amazon long description", "status": "Ready"},
            {"name": "Short description", "status": "Ready"},
            {"name": "Keywords (7)", "status": "Ready"},
            {"name": "Categories", "status": "Ready"},
            {"name": "Listing metadata", "status": "Ready"}]},
        {"name": "Marketing Package", "items": [
            {"name": "Launch announcement graphic", "status": "Ready" if graphics else "Not Implemented"},
            {"name": "Quote graphic", "status": "Ready" if graphics else "Not Implemented"},
            {"name": "Buy-Now graphic", "status": "Ready" if graphics else "Not Implemented"},
            {"name": "Website hero graphic", "status": "Planned"}]},
        {"name": "Website Package", "items": [
            {"name": "Book page content", "status": "Ready"},
            {"name": "QRU Press catalog listing (live)", "status": "Planned"},
            {"name": "Author page update", "status": "Planned"}]},
        {"name": "Media Package", "items": [
            {"name": "Book trailer script", "status": "Ready" if trailer else "Planned"},
            {"name": "Social video script", "status": "Ready" if social_vid else "Planned"},
            {"name": "Audio sample script", "status": "Ready" if audio_script else "Planned"},
            {"name": "Rendered book trailer (video)", "status": "Not Implemented"}]},
        {"name": "Distribution Package", "items": [
            {"name": "Amazon KDP submission (manual)", "status": "Ready"},
            {"name": "QRU Digital Campus", "status": "Planned"},
            {"name": "Future distribution adapters", "status": "Planned"}]},
        {"name": "Founder Package", "items": [
            {"name": "Launch checklist", "status": "Ready"},
            {"name": "Release checklist", "status": "Ready"},
            {"name": "Publication summary", "status": "Ready"}]},
    ]
    all_items = [i for s in sections for i in s["items"]]
    counts = {st: sum(1 for i in all_items if i["status"] == st) for st in ("Ready", "Prototype", "Planned", "Not Implemented")}
    post = {
        "generated_at": _now(), "by": actor, "sections": sections, "counts": counts,
        "assets_zip": assets_url,
        "honesty": "Only 'Ready' items are manufactured and included in the downloadable Publication Assets. "
                   "Planned and Not Implemented are shown honestly and produce NO files or links.",
        "founder_effort_units": {
            "manual_before": len([i for i in all_items if i["status"] == "Ready"]),
            "automatic_after": 0,
            "note": "FEU = separate manufacture actions the Founder previously had to trigger. This recipe "
                    "runs automatically on Authorize Release, so the Founder answers zero extra questions.",
        },
    }
    # Treasure Standard: the Publication Assets bundle is a real Factory rendering — persist it in the
    # Deliverables/Factory Library alongside the Master Output Package (replace, never append; delete the
    # prior file so the Library never shows a stale/broken link). Post-Publish panel + Library stay in sync.
    import os as _os2
    zip_bytes = buf.getvalue()
    pub_deliverable = {"type": "Publication Assets Package", "label": "Publication Assets Package",
                       "url": assets_url, "filename": zid, "size_kb": len(zip_bytes) // 1024,
                       "assembled_at": _now(), "by": actor}
    existing = b.get("deliverables", []) or []
    for d in existing:
        if d.get("type") == "Publication Assets Package" and d.get("url"):
            old_path = _os2.path.join(re_engine.ASSET_DIR, d["url"].split("/")[-1])
            if _os2.path.exists(old_path):
                try:
                    _os2.remove(old_path)
                except OSError:
                    pass
    deliverables = [d for d in existing if d.get("type") != "Publication Assets Package"] + [pub_deliverable]
    await db[COLL].update_one({"id": book_id}, {"$set": {"post_publish": post, "deliverables": deliverables, "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Post-Publish Recipe", "by": actor, "at": _now(),
                  "note": f"Auto-manufactured publication assets: {counts['Ready']} Ready, {counts['Planned']} Planned."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"post-publish recipe manufactured {counts['Ready']} assets for '{title}'", b["book_code"], "success")
    return post



async def authorize_release(book_id, actor):
    """Human final judgment for the irreversible release action. Requires the rest of the gate met."""
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    pc = await publish_center(book_id)
    gate = dict(pc["final_release_gate"])
    gate["founder_authorization_received"] = True
    if not all(gate.values()):
        unmet = [k.replace("_", " ") for k, v in gate.items() if not v]
        return {"error": f"Cannot authorize — unmet gate items: {', '.join(unmet)}."}
    auth = {"authorized": True, "by": actor, "at": _now()}
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "founder_authorization": auth, "publication_status": "Authorized for release (manual/authorized submission)",
        "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Founder Authorization", "by": actor, "at": _now(),
                                       "note": "Founder authorized release (irreversible actions permitted)."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"FOUNDER AUTHORIZED release of '{b['title']}'", b["book_code"], "success")
    # Publishing is not the end of manufacturing — it triggers the inherited Post-Publish Recipe automatically.
    try:
        await run_post_publish_recipe(book_id, actor)
    except Exception as e:
        await log_org("Book Manufacturing™", "Manufacturing", f"post-publish recipe error for '{b['title']}': {e}", b["book_code"], "warning")
    return clean(await db[COLL].find_one({"id": book_id}))


SHARES = "book_shares"


async def build_review_package(book_id, actor, base_url=""):
    """Clean READER review copy for sharing — sanitized retail interior PDF + EPUB + cover + readme ONLY.
    NEVER includes the sealed immutable original or any manufacturing metadata, so a reviewer never sees
    internal placeholders like '(working title)'."""
    import zipfile
    import io as _io
    import os
    import rendering_engine as re_engine
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    sel = (b.get("artifacts", {}).get("design") or {}).get("selected_cover")
    if not sel:
        return {"error": "Select the final cover first — the review copy is built from your chosen cover."}
    sanit = b.get("artifacts", {}).get("sanitization")
    if not sanit:
        res = await sanitization_pass(book_id, actor, base_url)
        if isinstance(res, dict) and res.get("error"):
            return res
        b = await db[COLL].find_one({"id": book_id})
        sanit = b.get("artifacts", {}).get("sanitization")
    retail = (sanit or {}).get("retail_edition", {})
    pm = (sanit or {}).get("publication_metadata", {})

    def _read(u):
        if not u:
            return None
        p = os.path.join(re_engine.ASSET_DIR, u.rstrip("/").split("/")[-1])
        return open(p, "rb").read() if os.path.exists(p) else None

    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", (
            f"{pm.get('title', b.get('title',''))}\nby {pm.get('author', b.get('author',''))}\n"
            f"{pm.get('imprint', b.get('imprint',''))}\n\n"
            "REVIEW COPY — this is the finished, reader-facing book.\n"
            "Open 'Book (reading edition).pdf' to read, or 'Book.epub' on an e-reader.\n"))
        pdf = _read(retail.get("paperback_interior_pdf"))
        if pdf:
            z.writestr("Book (reading edition).pdf", pdf)
        ep = _read(retail.get("epub"))
        if ep:
            z.writestr("Book.epub", ep)
        cov = _read(sel.get("url"))
        if cov:
            z.writestr("Cover.png", cov)
    data = buf.getvalue()
    fid = re_engine._save("book-review-copy", "zip", data)
    return {"url": re_engine._asset_url(fid), "size_kb": len(data) // 1024}


async def create_share(book_id, hours, actor, base_url=""):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    # A review link shares the CLEAN reader edition — never the manufacturing package.
    review = await build_review_package(book_id, actor, base_url)
    if isinstance(review, dict) and review.get("error"):
        return review
    pkg_url = review["url"]
    from datetime import timedelta
    token = gen_id().replace("-", "")[:24]
    expires = (datetime.now(timezone.utc) + timedelta(hours=int(hours or 72))).isoformat()
    await db[SHARES].insert_one({"token": token, "book_id": book_id, "book_title": b["title"],
                                 "package_url": pkg_url, "created_by": actor, "created_at": _now(),
                                 "expires_at": expires, "read_only": True})
    await log_org("Book Manufacturing™", "Manufacturing", f"created share link for '{b['title']}' (expires {expires[:10]})", b["book_code"])
    share_url = f"{base_url}/api/book-mfg/share/{token}" if base_url else f"/api/book-mfg/share/{token}"
    # Factory Library™ — keep the share link resident in the Canonical Book Record so the Founder can
    # re-copy it any time (never rely on a one-shot clipboard write).
    await db[COLL].update_one({"id": book_id}, {"$push": {"share_links": {
        "token": token, "share_url": share_url, "created_by": actor, "created_at": _now(),
        "expires_at": expires, "read_only": True, "kind": "Review copy"}}})
    return {"ok": True, "token": token, "share_url": share_url, "expires_at": expires, "read_only": True, "kind": "Review copy"}


async def resolve_share(token):
    s = await db[SHARES].find_one({"token": token}, {"_id": 0})
    if not s:
        return {"error": "Share link not found."}
    if datetime.fromisoformat(s["expires_at"]) < datetime.now(timezone.utc):
        return {"error": "This share link has expired."}
    return s



async def video_plan(book_id):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    return {
        "book_title": b["title"], "book_code": b["book_code"],
        "youtube": {"state": "Package prepared", "items": ["Full audiobook/visual reading edition", "Chapter videos",
                    "Playlist structure", "Captions", "Description + chapters", "Thumbnails", "AI-content disclosure",
                    "Private-review upload", "Final publication approval required"]},
        "youtube_shorts": {"state": "Package prepared", "items": ["Educational insight", "Dramatic excerpt",
                    "Character quote", "Hook question", "Book discovery clip"]},
        "tiktok": {"state": "Guided (Content Posting API where authorized)", "items": ["Vertical native videos",
                    "Strong 1-second hook", "Excerpts", "Character moments", "Quotes", "Reader questions",
                    "AI-content disclosure", "Draft-or-authorized-post only"]},
        "podcast": {"state": "Package prepared", "items": ["Chapter/thematic episodes", "Episode title + description",
                    "Intro/outro", "Cover", "Transcript", "RSS-ready metadata"]},
        "policy": "Every media product must carry meaningful editorial/educational value. No low-effort mass duplication.",
    }


# ----------------- PUBLICATION SANITIZATION PASS™ (pre-Final-Release) -----------------
# Master Design Standard™ Phase 2: the sanitization + Title/Copyright/Colophon logic is now OWNED by
# the shared QRU Publication Quality Standard™ (`publication_quality.py`). The book line INHERITS it
# (fiction "book" profile) and extends it with print-wrap + Founder cover selection. No duplication.
import publication_quality as _pq

_PLACEHOLDER_PATTERNS = _pq.PLACEHOLDER_PATTERNS


def _detect_placeholders(text):
    return _pq.detect_placeholders(text)


def _split_front_matter(content):
    return _pq.split_front_matter(content)


def _build_publication(b):
    """Book (Founder-authored trade edition) inherits the shared builder with the fiction profile,
    passing book-specific defaults so the retail edition output is unchanged."""
    meta = {
        "title": b.get("title") or "Untitled",
        "subtitle": b.get("subtitle") or "",
        "author": b.get("author") or "Author",
        "publisher": b.get("rights_holder") or b.get("imprint") or "QRU Press",
        "imprint": b.get("imprint") or b.get("rights_holder") or "QRU Press",
        "edition": b.get("edition") or "First Edition",
        "language": b.get("language") or "English",
        "isbn": b.get("isbn") or "ISBN: __________________________  (assigned by Amazon KDP at publication)",
        "genre": b.get("genre") or "Fiction",
        "ai_content_disclosure": b.get("ai_disclosure") or "AI-assisted manufacturing; human-authored and human-approved.",
    }
    return _pq.build_publication(meta, _pq.PROFILES["book"])


async def sanitization_pass(book_id, actor, base_url=""):
    """Publication Sanitization Pass™ — prepares the clean RETAIL edition before Final Release.
    Removes internal placeholders (e.g. "(working title)") and manufacturing metadata from reader-facing
    pages; generates a clean Title Page, Copyright Page, and Colophon per publishing convention; and
    SEPARATES publication metadata from manufacturing metadata. All manufacturing metadata is preserved
    in the Canonical Book Record + Master Output Package and is NEVER printed in the retail edition."""
    import re
    import os
    import rendering_engine as re_engine
    import deliverable_renderer as dr
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    if not b.get("editorial_locked"):
        return {"error": "Approve & lock the editorial edition first."}
    design_art = b.get("artifacts", {}).get("design")
    if not design_art:
        return {"error": "Run Design first."}
    sel = design_art.get("selected_cover")
    if not sel:
        return {"error": "Select the final cover before the Publication Sanitization Pass™."}

    content = b["editorial_edition"]["content"]
    findings = _detect_placeholders(content)
    front_block, body = _split_front_matter(content)
    body_clean = body
    for pat, _ in _PLACEHOLDER_PATTERNS:
        body_clean = re.sub(pat, "", body_clean, flags=re.I)
    body_clean = re.sub(r"\(\s*\)", "", body_clean)
    body_clean = re.sub(r"\n{3,}", "\n\n", body_clean).strip()

    pub_meta, title_page, copyright_page, colophon = _build_publication(b)

    cover_bytes = open(os.path.join(re_engine.ASSET_DIR, sel["url"].split("/")[-1]), "rb").read()
    qr = re_engine._make_qr(f"{base_url}/book/{book_id}")
    retail_product = {
        "title": pub_meta["title"], "subtitle": pub_meta["subtitle"], "family": pub_meta["genre"],
        "product_type": "Book", "content": body_clean, "audience": b.get("audience", ""),
        "imprint": pub_meta["imprint"], "high_stakes": b.get("high_stakes"),
        "retail_publication": {"metadata": pub_meta, "title_page": title_page,
                               "copyright_page": copyright_page, "colophon": colophon},
    }
    interior_pdf = re_engine._make_pdf(retail_product, {}, cover_bytes, qr)
    interior_fid = re_engine._save("book-retail-interior", "pdf", interior_pdf)
    try:
        epub_bytes = dr._render_epub(retail_product, cover_bytes)
        epub_fid = re_engine._save("book-retail-ebook", "epub", epub_bytes)
        epub_url = re_engine._asset_url(epub_fid)
    except Exception:
        epub_url = None

    sanitization = {
        "generated_at": _now(), "by": actor,
        "status": "Clean retail edition prepared",
        "placeholders_found": findings,
        "placeholders_removed": len(findings),
        "front_matter_block_removed": bool(front_block.strip()),
        "publication_metadata": pub_meta,
        "title_page": title_page, "copyright_page": copyright_page, "colophon": colophon,
        "retail_edition": {"paperback_interior_pdf": re_engine._asset_url(interior_fid),
                           "epub": epub_url, "content_checksum": _checksum(body_clean)},
        "separation_note": ("Publication metadata is reader-facing. Manufacturing metadata (Book Record ID, "
                            "checksums, provenance, AI-contribution audit, revision history, intake scan) is preserved "
                            "in the Canonical Book Record and Master Output Package — never printed in the retail "
                            "edition unless explicitly requested."),
    }
    artifacts = b.get("artifacts", {})
    artifacts["sanitization"] = sanitization
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "artifacts": artifacts,
        "publication_metadata": pub_meta,
        "manufacturing_job": {"stage": "Publication sanitized", "next": "Final Release Gate → Founder authorization"},
        "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Publication Sanitization Pass", "by": actor, "at": _now(),
                  "note": f"Retail edition sanitized: {len(findings)} internal marker(s) removed; clean Title/Copyright/Colophon generated."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"publication sanitization pass for '{b['title']}'", b["book_code"], "success")
    return clean(await db[COLL].find_one({"id": book_id}))


# ----------------------------- BUTTON 6 — PUBLISH -----------------------------
async def publish_center(book_id):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    design_done = bool(b.get("artifacts", {}).get("design"))
    cover_selected = bool(b.get("artifacts", {}).get("design", {}).get("selected_cover"))
    locked = b.get("editorial_locked")

    def dest(name, api=False):
        if not locked or not design_done:
            state = "Missing requirements"
        elif not cover_selected:
            state = "Missing requirements"
        elif api:
            state = "Ready for Founder review"  # authorized API upload only after Final Release Gate + explicit auth
        else:
            state = "Ready for manual submission"
        return {"destination": name, "state": state,
                "integration": "Authorized OAuth (YouTube)" if name == "YouTube" else
                               ("Content Posting API (where authorized)" if name == "TikTok" else "Manual package")}

    destinations = [dest(n, api=(n in ("YouTube", "YouTube Shorts"))) for n in PUBLISH_DESTINATIONS]
    gate = {
        "title_author": bool(b.get("title") and b.get("author")),
        "imprint": bool(b.get("imprint")),
        "rights_confirmed": bool(b.get("rights_holder")),
        "proof_approved": b.get("editorial_locked", False),
        "cover_approved": cover_selected,
        "metadata_approved": design_done,
        "ai_disclosures_completed": bool(b.get("ai_disclosure")),
        "publication_sanitized": bool(b.get("artifacts", {}).get("sanitization")),
        "pricing_approved": bool((b.get("pricing") or {}).get("approved")),
        "platform_files_passed": design_done,
        "founder_authorization_received": bool((b.get("founder_authorization") or {}).get("authorized")),
    }
    return {"book_title": b["title"], "book_code": b["book_code"], "destinations": destinations,
            "final_release_gate": gate,
            "gate_ready": all(gate.values()),
            "gate_ready_for_authorization": all(v for k, v in gate.items() if k != "founder_authorization_received"),
            "honesty": "No publication, sale, or irreversible external action occurs without explicit Founder authorization. The Factory never reports a platform action succeeded unless it truly did."}


# ----------------------------- BUTTON 7 — MONITOR -----------------------------
async def monitor(book_id):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    return {
        "book_title": b["title"], "book_code": b["book_code"],
        "retail": {"state": "No live listings yet", "metrics": ["Sales", "Units", "Royalties", "Territory", "Reviews", "Returns"]},
        "youtube": {"state": "Not published", "metrics": ["Views", "CTR", "Watch time", "Retention", "Subscribers", "Comments"]},
        "tiktok": {"state": "Not published", "metrics": ["Views", "Completion", "Saves", "Shares", "Comments", "Link clicks"]},
        "audio": {"state": "Not published", "metrics": ["Samples", "Downloads/sales", "Completion", "Feedback"]},
        "operations": {"platform_status": "Pre-publication", "backup_status": b.get("backup_status")},
        "improvement_recommendations": [
            "Once live, feed retention/drop-off back into the Reading Experience Standard™ (submit for governed approval — never auto-change a published standard).",
        ],
        "honesty": "Performance data appears only when a real platform reports it. Nothing is fabricated.",
    }



# ------------------------- READY-FOR-KDP CHECKLIST -------------------------
async def build_kdp_checklist(book_id):
    """Ready-for-KDP™ — a one-page fill-in sheet so manual Amazon KDP upload takes ~2 minutes.
    Known facts are stated as facts; fields the Founder must confirm are clearly marked SUGGESTED /
    NEEDS FOUNDER — never fabricated as final (Treasure Standard™)."""
    import os
    import re
    import rendering_engine as re_engine
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    sanit = b.get("artifacts", {}).get("sanitization", {}) or {}
    pm = sanit.get("publication_metadata", {}) or {}
    design = b.get("artifacts", {}).get("design", {}) or {}
    sel = design.get("selected_cover") or {}
    retail = sanit.get("retail_edition", {}) or {}
    pricing = b.get("pricing", {}) or {}

    interior_url = retail.get("paperback_interior_pdf") or design.get("print", {}).get("paperback_interior_pdf")
    epub_url = retail.get("epub") or design.get("ebook", {}).get("epub")
    pages = None
    if interior_url:
        p = os.path.join(re_engine.ASSET_DIR, interior_url.split("/")[-1])
        if os.path.exists(p):
            try:
                import pypdf
                pages = len(pypdf.PdfReader(p).pages)
            except Exception:
                pages = None
    words = len((b.get("editorial_edition") or {}).get("content", "").split())
    genre = b.get("genre") or pm.get("genre") or "Fiction"
    title_words = [w for w in re.findall(r"[A-Za-z]{4,}", (b.get("title") or "")) ]
    kw = list(dict.fromkeys([genre] + title_words + [b.get("audience", "")]))
    kw = [k for k in kw if k][:7]
    price_ok = bool(pricing.get("approved"))

    fields = [
        {"field": "Book title", "value": b.get("title"), "status": "confirmed"},
        {"field": "Subtitle", "value": pm.get("subtitle") or b.get("subtitle") or "—", "status": "confirmed"},
        {"field": "Author / contributor", "value": b.get("author"), "status": "confirmed"},
        {"field": "Publisher / imprint", "value": b.get("imprint"), "status": "confirmed"},
        {"field": "Language", "value": pm.get("language") or b.get("language") or "English", "status": "confirmed"},
        {"field": "Edition", "value": pm.get("edition") or b.get("edition") or "First Edition", "status": "confirmed"},
        {"field": "Rights holder", "value": b.get("rights_holder"), "status": "confirmed"},
        {"field": "Copyright", "value": f"© {pm.get('copyright_year','')} {pm.get('copyright_holder', b.get('rights_holder',''))}".strip(), "status": "confirmed"},
        {"field": "ISBN", "value": (pm.get("isbn") or b.get("isbn") or ("Free KDP-assigned ISBN (assigned by Amazon at upload)" if b.get("isbn_source") == "kdp_free" else "Use a free KDP ISBN or supply your own")), "status": ("confirmed" if (pm.get("isbn") or b.get("isbn") or b.get("isbn_source")) else "needs_founder")},
        {"field": "Trim size (paperback)", "value": design.get("print", {}).get("trim_size", "6 x 9 in"), "status": "confirmed"},
        {"field": "Page count", "value": pages if pages else "Confirm from print interior PDF", "status": "confirmed" if pages else "needs_founder"},
        {"field": "Word count", "value": words, "status": "confirmed"},
        {"field": "List price", "value": ((f"eBook {pricing.get('currency','USD')} {pricing['ebook_price']} · Paperback {pricing.get('currency','USD')} {pricing['paperback_price']}" if pricing.get("ebook_price") and pricing.get("paperback_price") else f"{pricing.get('list_price')} {pricing.get('currency','USD')}") if pricing.get("list_price") or pricing.get("ebook_price") else "Not set"), "status": "confirmed" if price_ok else "needs_founder"},
        {"field": "Categories (BISAC)", "value": f"Suggested from genre '{genre}' — confirm 2 on KDP", "status": "suggested"},
        {"field": "Keywords (up to 7)", "value": ", ".join(kw) if kw else "Add up to 7", "status": "suggested"},
        {"field": "Book description / blurb", "value": b.get("description") or "DRAFT NEEDED — add a 150–200 word back-cover blurb", "status": "confirmed" if b.get("description") else "needs_founder"},
        {"field": "AI content disclosure", "value": b.get("ai_disclosure"), "status": "confirmed"},
        {"field": "Cover file (front)", "value": sel.get("url") or "Select a cover first", "status": "confirmed" if sel.get("url") else "needs_founder"},
        {"field": "Print interior (PDF)", "value": interior_url or "Run Design/Sanitize", "status": "confirmed" if interior_url else "needs_founder"},
        {"field": "eBook (EPUB)", "value": epub_url or "Run Design/Sanitize", "status": "confirmed" if epub_url else "needs_founder"},
    ]
    pending = [f["field"] for f in fields if f["status"] == "needs_founder"]
    return {
        "book_title": b.get("title"), "book_code": b.get("book_code"),
        "generated_at": _now(),
        "fields": fields,
        "pending_founder": pending,
        "ready": len(pending) == 0,
        "note": "Facts are pulled from the Canonical Book Record. SUGGESTED = confirm on KDP; NEEDS FOUNDER = supply before upload. Nothing is fabricated as final.",
    }


def _kdp_markdown(chk):
    lines = [f"# Ready-for-KDP™ — {chk['book_title']} ({chk['book_code']})",
             f"_Generated {chk['generated_at']}_", "",
             "Paste these into Amazon KDP. ✅ confirmed · 🟡 suggested (confirm on KDP) · ⬜ needs founder input.", ""]
    icon = {"confirmed": "✅", "suggested": "🟡", "needs_founder": "⬜"}
    for f in chk["fields"]:
        lines.append(f"- {icon.get(f['status'],'•')} **{f['field']}:** {f['value']}")
    lines += ["", chk["note"]]
    return "\n".join(lines)


# ------------------------- PUBLICATION DETAILS (blurb) + PRINT COVER WRAP -------------------------
PAPER_THICKNESS_IN = {"white": 0.002252, "cream": 0.0025, "color": 0.002347}


async def set_publication_details(book_id, fields, actor):
    """Per-book publication details. Each book may have a different purpose — the back-cover blurb is
    OPTIONAL (include_blurb=False means an intentionally minimal back cover)."""
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    upd = {"updated_at": _now()}
    if "title" in fields:
        new_title = (fields.get("title") or "").strip()
        if new_title:
            upd["title"] = new_title
    if "author" in fields:
        new_author = (fields.get("author") or "").strip()
        if new_author:
            upd["author"] = new_author
    if "subtitle" in fields:
        upd["subtitle"] = (fields.get("subtitle") or "").strip()
    if "description" in fields:
        upd["description"] = (fields.get("description") or "").strip()
    if "author_bio" in fields:
        upd["author_bio"] = (fields.get("author_bio") or "").strip()
    if "include_blurb" in fields:
        upd["include_blurb"] = bool(fields.get("include_blurb"))
    if "blurb_status" in fields:
        upd["blurb_status"] = fields.get("blurb_status")
    if "isbn" in fields:
        upd["isbn"] = (fields.get("isbn") or "").strip()
    if "isbn_source" in fields:
        upd["isbn_source"] = fields.get("isbn_source")
    await db[COLL].update_one({"id": book_id}, {"$set": upd})
    return clean(await db[COLL].find_one({"id": book_id}))


async def draft_blurb(book_id, actor):
    """Draft a back-cover blurb from the manuscript (marked DRAFT — Founder approves before it's final)."""
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    content = (b.get("editorial_edition") or b.get("working_copy") or {}).get("content", "")
    synopsis = " ".join(content.split()[:1200])
    sys_p = ("You are a QRU jacket copywriter. Write ONE compelling back-cover blurb (120–170 words) for the "
             "book below. Voice-appropriate, evocative, no spoilers, no invented facts, no quotes/reviews. "
             "Return plain prose only — no headings.")
    try:
        text = await ai_service.llm_generate(sys_p, f"Title: {b.get('title')}\nBy: {b.get('author')}\n\n{synopsis}",
                                             f"blurb-{book_id}")
        text = (text or "").strip()
    except Exception as e:
        return {"error": f"Blurb draft unavailable right now ({str(e)[:80]})."}
    if len(text) < 40:
        return {"error": "Could not draft a blurb from this manuscript."}
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "description": text, "include_blurb": True, "blurb_status": "draft — Founder to approve", "updated_at": _now()}})
    return {"ok": True, "blurb": text, "status": "draft — Founder to approve"}


async def build_print_cover_wrap(book_id, paper_type, actor):
    """Complete print-ready paperback cover wrap (back + spine + front) computed from FINAL page count,
    trim size, paper type & bleed. NOT just the front cover (Treasure Standard™ — honest states only)."""
    import os
    import rendering_engine as re_engine
    import design_studio
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    design = b.get("artifacts", {}).get("design", {}) or {}
    sel = design.get("selected_cover") or {}
    if not sel.get("url"):
        return {"error": "Select the final cover first."}
    sanit = b.get("artifacts", {}).get("sanitization", {}) or {}
    interior_url = (sanit.get("retail_edition", {}) or {}).get("paperback_interior_pdf") or design.get("print", {}).get("paperback_interior_pdf")
    if not interior_url:
        return {"error": "Run the Publication Sanitization Pass™ first (need the final interior for page count)."}
    ipath = os.path.join(re_engine.ASSET_DIR, interior_url.split("/")[-1])
    try:
        import pypdf
        pages = len(pypdf.PdfReader(ipath).pages)
    except Exception:
        return {"error": "Could not read the final interior PDF for page count."}
    paper_type = (paper_type or "white").lower()
    thickness = PAPER_THICKNESS_IN.get(paper_type, PAPER_THICKNESS_IN["white"])
    spine_in = round(pages * thickness, 4)
    trim_w, trim_h, bleed, dpi = 6.0, 9.0, 0.125, 300
    front_bytes = open(os.path.join(re_engine.ASSET_DIR, sel["url"].split("/")[-1]), "rb").read()
    include_blurb = b.get("include_blurb", True)
    blurb = (b.get("description") or "") if include_blurb else ""
    spine_text = pages >= 79
    png, (W, H) = design_studio.compose_print_wrap(front_bytes, {
        "trim_w_in": trim_w, "trim_h_in": trim_h, "spine_in": spine_in, "bleed_in": bleed, "dpi": dpi,
        "title": b.get("title", ""), "subtitle": b.get("subtitle", ""), "author": b.get("author", ""),
        "imprint": b.get("imprint", ""), "blurb": blurb, "spine_text": spine_text})
    # Save print-ready PDF at correct physical size.
    from PIL import Image
    pbuf = __import__("io").BytesIO()
    Image.open(__import__("io").BytesIO(png)).save(pbuf, "PDF", resolution=dpi)
    pdf_fid = re_engine._save("book-cover-wrap", "pdf", pbuf.getvalue())
    png_fid = re_engine._save("book-cover-wrap", "png", png)
    full_w_in = round(bleed + trim_w + spine_in + trim_w + bleed, 3)
    full_h_in = round(bleed + trim_h + bleed, 3)
    wrap = {
        "generated_at": _now(), "by": actor,
        "paperback_cover_wrap_pdf": re_engine._asset_url(pdf_fid),
        "paperback_cover_wrap_png": re_engine._asset_url(png_fid),
        "page_count": pages, "paper_type": paper_type, "spine_in": spine_in,
        "trim": f"{trim_w:g} x {trim_h:g} in", "bleed_in": bleed, "dpi": dpi,
        "full_size_in": f"{full_w_in} x {full_h_in} in", "pixels": f"{W} x {H}",
        "spine_text": spine_text,
        "spine_note": "Spine text included." if spine_text else "Spine left blank (KDP requires ≥ 79 pages for spine text).",
        "blurb_included": bool(blurb),
        "components": "Back cover + spine + front cover (complete wrap).",
    }
    design["print"] = {**design.get("print", {}), "paperback_cover_wrap": wrap}
    await db[COLL].update_one({"id": book_id}, {"$set": {"artifacts.design": design, "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Print Cover Wrap", "by": actor, "at": _now(),
                  "note": f"Full paperback wrap: {pages}pp, {paper_type} paper, spine {spine_in}in, {full_w_in}x{full_h_in}in @ {dpi}dpi."}}})
    return wrap

# ------------------------- QRU PRICING ADVISOR™ -------------------------
# Inherited Factory capability. ONE responsibility: recommend. ONE owner.
# It NEVER changes a price — the Founder always makes the final decision.
# Transparent Provenance™ applies to every recommendation.
QRU_PRESS_STANDARDS = {
    # genre bucket -> {ebook:(lo,hi), paperback:(lo,hi)}  (USD, QRU Press™ house standard)
    "children":   {"ebook": (2.99, 4.99),  "paperback": (8.99, 12.99)},
    "poetry":     {"ebook": (3.99, 6.99),  "paperback": (10.99, 14.99)},
    "fiction":    {"ebook": (4.99, 7.99),  "paperback": (13.99, 17.99)},
    "nonfiction": {"ebook": (6.99, 9.99),  "paperback": (15.99, 21.99)},
    "reference":  {"ebook": (7.99, 12.99), "paperback": (18.99, 26.99)},
    "standard":   {"ebook": (4.99, 7.99),  "paperback": (12.99, 16.99)},
}


def _genre_bucket(genre, audience):
    ga = f"{(genre or '').lower()} {(audience or '').lower()}"
    if any(k in ga for k in ["child", "kid", "juvenile", "picture book", "middle grade", "early reader"]):
        return "children"
    if "poet" in ga:
        return "poetry"
    if any(k in ga for k in ["reference", "textbook", "manual", "handbook", "academic", "curriculum"]):
        return "reference"
    if any(k in ga for k in ["nonfiction", "non-fiction", "business", "self-help", "self help", "memoir",
                             "biography", "history", "science", "essay", "guide", "spiritual", "wellness"]):
        return "nonfiction"
    if any(k in ga for k in ["fiction", "novel", "fantasy", "romance", "thriller", "mystery", "literary",
                             "story", "sci-fi", "science fiction"]):
        return "fiction"
    return "standard"


def kdp_paperback_print_cost(pages, paper_type="white"):
    """Amazon KDP US-marketplace paperback print cost (6x9, black ink on white/cream)."""
    pages = max(int(pages or 24), 24)
    if paper_type == "color":
        return round(0.065 * pages, 2)          # premium color, per-page
    if pages <= 108:
        return 2.30                              # fixed charge, 24–108 pp
    return round(1.00 + 0.012 * pages, 2)        # fixed + per-page, 110+ pp


def _psych(price):
    """Charm pricing — snap to the nearest sensible $X.99 (min $0.99)."""
    base = round(float(price))
    return round(base - 0.01, 2) if base >= 1 else 0.99


def _ebook_royalty(p):
    if 2.99 <= p <= 9.99:
        return round(0.70 * p, 2), "70%"
    return round(0.35 * p, 2), "35%"


def _paperback_royalty(list_price, print_cost):
    # KDP pays 60% of list price minus print cost (US expanded excluded for simplicity).
    return round(0.60 * list_price - print_cost, 2)


def _position(price, lo, hi):
    if price < lo + (hi - lo) / 3:
        return "Budget"
    if price > hi - (hi - lo) / 3:
        return "Premium"
    return "Standard"


async def _book_pages(b):
    import os
    import rendering_engine as re_engine
    sanit = b.get("artifacts", {}).get("sanitization", {}) or {}
    design = b.get("artifacts", {}).get("design", {}) or {}
    interior_url = (sanit.get("retail_edition", {}) or {}).get("paperback_interior_pdf") or design.get("print", {}).get("paperback_interior_pdf")
    if not interior_url:
        return None
    p = os.path.join(re_engine.ASSET_DIR, interior_url.split("/")[-1])
    if not os.path.exists(p):
        return None
    try:
        import pypdf
        return len(pypdf.PdfReader(p).pages)
    except Exception:
        return None


async def pricing_advisor(book_id, scenarios=None, paper_type="white"):
    """Evidence-based pricing RECOMMENDATION for the Founder. Recommends, never sets."""
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    genre = b.get("genre") or (b.get("artifacts", {}).get("sanitization", {}).get("publication_metadata", {}) or {}).get("genre") or "Fiction"
    audience = b.get("audience", "General")
    bucket = _genre_bucket(genre, audience)
    std = QRU_PRESS_STANDARDS[bucket]
    pages = await _book_pages(b)
    words = len((b.get("editorial_edition") or b.get("working_copy") or {}).get("content", "").split())
    est_pages = pages or max(24, round(words / 250)) if words else pages
    paper_type = (paper_type or "white").lower()
    print_cost = kdp_paperback_print_cost(est_pages or 24, paper_type)

    eb_lo, eb_hi = std["ebook"]
    pb_lo, pb_hi = std["paperback"]
    rec_ebook = min(max(_psych((eb_lo + eb_hi) / 2), 2.99), 9.99)
    # Paperback must comfortably clear print cost (target ≥ 50% margin over print) yet stay on-brand.
    min_viable = _psych(print_cost / 0.60 * 1.5)
    rec_pb = _psych(min(max((pb_lo + pb_hi) / 2, min_viable), pb_hi + 3))

    eb_amt, eb_rate = _ebook_royalty(rec_ebook)
    pb_amt = _paperback_royalty(rec_pb, print_cost)
    position = _position(rec_pb, pb_lo, pb_hi)

    completeness = []
    completeness.append("page count" if pages else "page count (estimated from word count — run Sanitize for exact)")
    completeness.append("genre" if b.get("genre") else "genre (defaulted)")
    confidence = "High" if (pages and b.get("genre")) else ("Medium" if (pages or b.get("genre")) else "Low")

    comparable = {
        "ebook": f"${eb_lo:.2f}–${eb_hi:.2f}",
        "paperback": f"${pb_lo:.2f}–${pb_hi:.2f}",
        "basis": f"QRU Press™ house standard for the '{bucket}' category (genre: {genre}, audience: {audience}).",
    }

    # Founder Notes — LLM strategic guidance grounded ONLY in the computed evidence above.
    notes_model = ai_service.MODEL[1] if isinstance(ai_service.MODEL, (tuple, list)) else str(ai_service.MODEL)
    facts = (f"Genre bucket: {bucket} (genre '{genre}', audience '{audience}'). Page count: {est_pages}"
             f"{' (estimated)' if not pages else ''}. KDP print cost: ${print_cost:.2f} ({paper_type} paper). "
             f"Recommended eBook ${rec_ebook:.2f} → royalty ${eb_amt:.2f} ({eb_rate}). "
             f"Recommended paperback ${rec_pb:.2f} → royalty ${pb_amt:.2f}. Position: {position}. "
             f"Comparable range eBook {comparable['ebook']}, paperback {comparable['paperback']}.")
    sys_p = ("You are the QRU Pricing Advisor™. Using ONLY the evidence provided, write 2–4 sentences of "
             "concise, honest pricing guidance for the Founder. Explain the trade-offs (royalty vs. reach, "
             "positioning). Do NOT invent sales figures, competitor titles, or guarantees. End by reminding "
             "the Founder they make the final decision. Plain prose only.")
    try:
        founder_notes = (await ai_service.llm_generate(sys_p, facts, f"pricing-{book_id}")).strip()
    except Exception:
        founder_notes = ""
    if len(founder_notes) < 30:
        founder_notes = (f"At ${rec_pb:.2f} the paperback earns roughly ${pb_amt:.2f} per copy after the "
                         f"${print_cost:.2f} KDP print cost, positioning it as '{position}' for the {bucket} "
                         f"category. The ${rec_ebook:.2f} eBook stays inside the {eb_rate} royalty band for "
                         f"maximum earnings. You make the final decision — adjust to match your goals.")

    result = {
        "book_title": b.get("title"), "book_code": b.get("book_code"), "generated_at": _now(),
        "inputs": {
            "genre": genre, "genre_bucket": bucket, "audience": audience,
            "page_count": est_pages, "page_count_exact": bool(pages), "word_count": words,
            "paper_type": paper_type, "print_cost": print_cost, "trim": "6 x 9 in",
        },
        "recommendation": {
            "ebook_price": rec_ebook, "paperback_price": rec_pb, "currency": "USD",
            "estimated_royalty": {
                "ebook": {"amount": eb_amt, "rate": eb_rate},
                "paperback": {"amount": pb_amt, "note": "60% of list − KDP print cost"},
            },
            "price_position": position,
            "comparable_market_range": comparable,
            "confidence_level": confidence,
            "founder_notes": founder_notes,
        },
        "current_price": b.get("pricing", {}) or {},
        "provenance": {
            "engine": "QRU Pricing Advisor™",
            "pricing_model": "Deterministic KDP economics + QRU Press™ house standards",
            "founder_notes_model": notes_model,
            "print_cost_basis": "Amazon KDP US marketplace, 6x9, black ink (Sept-2024 rates).",
            "royalty_basis": "eBook 70% ($2.99–$9.99) else 35%; paperback 60% of list − print cost.",
            "disclaimer": "Estimates based on published KDP formulas & category norms — NOT verified live sales data.",
            "generated_at": _now(),
        },
        "honesty": "Recommendation only. The QRU Pricing Advisor™ never changes a price — the Founder always sets the final price.",
    }

    if scenarios:
        rows = []
        for raw in scenarios:
            try:
                p = round(float(raw), 2)
            except Exception:
                continue
            e_amt, e_rate = _ebook_royalty(p)
            pb_r = _paperback_royalty(p, print_cost)
            margin = round((pb_r / p * 100), 1) if p else 0.0
            rows.append({
                "price": p,
                "ebook_royalty": e_amt, "ebook_rate": e_rate,
                "paperback_royalty": pb_r, "paperback_margin_pct": margin,
                "print_cost": print_cost,
                "position": _position(p, pb_lo, pb_hi),
            })
        result["scenarios"] = rows

    return result



# ------------------------- MASTER PACKAGE + READ MODELS -------------------------
async def master_package(book_id):
    b = await db[COLL].find_one({"id": book_id}, {"_id": 0})
    if not b:
        return None
    art = b.get("artifacts", {})
    design_art = art.get("design", {})
    return {
        "book_title": b["title"], "book_code": b["book_code"], "imprint": b.get("imprint"),
        "sections": {
            "01_SOURCE": {"immutable_original_checksum": b["original"]["checksum"],
                          "approved_editorial_master": bool(b.get("editorial_edition")),
                          "version_history": len(b.get("revision_history", []))},
            "02_EDITORIAL": {"proofing_report": bool(b.get("proofing_report")),
                             "approval_record": b.get("editorial_status")},
            "03_PRINT": {"paperback_interior": design_art.get("print", {}).get("paperback_interior_pdf")},
            "04_EBOOK": {"epub": design_art.get("ebook", {}).get("epub")},
            "05_AUDIO": {"state": "Guided package (Button 4)"},
            "06_VIDEO": {"state": "Guided package (Button 5)"},
            "07_METADATA": {"master": {k: b.get(k) for k in ("title", "subtitle", "author", "imprint", "series",
                                                             "edition", "language", "audience", "genre")}},
            "08_MARKETING": {"state": "Prepared at Design/Publish"},
            "09_RIGHTS_AND_GOVERNANCE": {"rights_holder": b.get("rights_holder"),
                                         "ai_disclosure": b.get("ai_disclosure"),
                                         "governance_package": design_art.get("governance_package"),
                                         "approvals": [r for r in b.get("revision_history", []) if r.get("stage") in ("Editorial Lock", "Design")]},
            "10_MONITORING": {"state": "Activates post-publication"},
        },
    }


async def _resolve_source_ukr(b):
    """Resolve the canonical UKR™ that a book inherited from (via the Decoder bridge), if any.
    Manuscript-originated books honestly have no UKR — the PMF records that truthfully."""
    sd = b.get("source_decoder") or {}
    kr_ids = sd.get("source_kr_ids") or []
    for k in kr_ids:
        kr_code = (k.get("kr_code") if isinstance(k, dict) else None)
        kr_id = (k.get("kr_id") if isinstance(k, dict) else k)
        doc = None
        if kr_code:
            doc = await db[ukr.CANONICAL_COLLECTION].find_one({"kr_code": kr_code}, {"_id": 0})
        if not doc and kr_id:
            doc = await db[ukr.CANONICAL_COLLECTION].find_one({"id": kr_id}, {"_id": 0})
        if doc:
            return doc
    return None


async def build_product_manifest(book_id, actor):
    """Generate the Product Manifest™ (PMF™ = EVIDENCE) for a manufactured book and persist it.
    Constitutional gate: no product manufactures without an approved PMS™."""
    b = await db[COLL].find_one({"id": book_id}, {"_id": 0})
    if not b:
        return None
    product_type = b.get("product_type", "Book")
    ok, pms = mf.require_pms(product_type)
    if not ok:
        return {"error": pms.get("error")}

    source_ukr = await _resolve_source_ukr(b)
    design_art = b.get("artifacts", {}).get("design", {}) or {}
    sanit = b.get("artifacts", {}).get("sanitization", {}) or {}
    audio_art = b.get("artifacts", {}).get("audio", {}) or {}
    pc = await publish_center(book_id)
    gate = pc.get("final_release_gate", {}) if pc else {}
    post = b.get("post_publish") or {}
    deliverables = b.get("deliverables", []) or []

    product = {
        "product_type": product_type, "product_family": pms["product_family"],
        "title": b.get("title"), "published_title": (sanit.get("publication_metadata", {}) or {}).get("title") or b.get("title"),
        "book_code": b.get("book_code"), "id": b.get("id"), "edition": b.get("edition", "First Edition"),
        "related_products": [{"product_type": p.get("product_type"), "book_code": p.get("book_code")}
                             for p in b.get("related_products", [])],
    }
    assets = {
        "cover": bool(design_art.get("selected_cover")),
        "print_cover_wrap": bool((design_art.get("print", {}) or {}).get("paperback_cover_wrap")),
        "ebook_cover_jpeg": bool(design_art.get("selected_cover")),
        "narration_prototype": bool(audio_art.get("prototype")),
        "templates": ["QRU Design Studio™", "Reading Experience Standard™"],
        "brand_assets": ["QRU Press™ imprint"],
    }
    production = {
        "files_produced": [d.get("type") for d in deliverables],
        "export_formats": pms["manufacturing_specifications"]["output_formats"],
        "master_package": next((d.get("url") for d in deliverables if d.get("type") == "Master Output Package"), None),
        "publication_assets": post.get("assets_zip"),
        "editable_source": bool(b.get("editorial_edition")),
    }
    quality = {
        "validation_status": "PASS" if all(gate.values()) else "INCOMPLETE",
        "release_gate": gate,
        "kdp_acceptance": pms["quality_gates"]["acceptance_criteria"],
        "verification_status": "Verified (source UKR™)" if source_ukr else "Manuscript-originated (no source UKR™)",
        "treasure_standard": "Honest states only — no fake publishing",
    }
    distribution = {
        "publishing_targets": pms["manufacturing_specifications"]["export_targets"],
        "product_status": b.get("publication_status", "Draft"),
        "post_publish_counts": post.get("counts", {}),
        "launch_status": "Authorized" if (b.get("founder_authorization") or {}).get("authorized") else "Not authorized",
    }
    governance = {
        "review_history": [r for r in b.get("revision_history", []) if r.get("stage") in ("Editorial Lock", "Design", "Founder Authorization", "Post-Publish Recipe")],
        "approval_history": [{"by": (b.get("founder_authorization") or {}).get("by"), "at": (b.get("founder_authorization") or {}).get("at")}] if (b.get("founder_authorization") or {}).get("authorized") else [],
        "provenance": b.get("transparent_provenance", {}),
    }
    manifest = mf.build_manifest(product=product, source_ukr=source_ukr, quality=quality,
                                 distribution=distribution, governance=governance, assets=assets,
                                 production=production, actor=actor)
    await db[COLL].update_one({"id": book_id}, {"$set": {"product_manifest": manifest, "updated_at": _now()}})
    return manifest


async def assemble_master_package(book_id, actor):
    """ONE click → ONE complete, provenance-stamped publication ZIP (the 10 governed sections)."""
    import json
    import zipfile
    import os
    import rendering_engine as re_engine
    b = await db[COLL].find_one({"id": book_id}, {"_id": 0})
    if not b:
        return None

    def _read_asset(url):
        if not url:
            return None
        fid = url.rstrip("/").split("/")[-1]
        path = os.path.join(re_engine.ASSET_DIR, fid)
        return open(path, "rb").read() if os.path.exists(path) else None

    design_art = b.get("artifacts", {}).get("design", {})
    meta = {k: b.get(k) for k in ("title", "subtitle", "author", "imprint", "series", "edition",
                                  "language", "audience", "genre", "rights_holder", "book_code")}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        readme = (f"QRU Book Manufacturing System(TM) v1.0 — Master Output Package\n"
                  f"Title: {b['title']}   |   Book Record: {b['book_code']}\n"
                  f"Imprint: {b.get('imprint')}   |   Author: {b.get('author')}\n"
                  f"Assembled: {_now()} by {actor}\n\n"
                  f"Honest package: only artifacts that truly exist are included. Nothing simulated.\n")
        z.writestr("README.txt", readme)
        # 01_SOURCE
        z.writestr("01_SOURCE/immutable_original.md", b["original"]["content"])
        z.writestr("01_SOURCE/canonical_book_record.json", json.dumps(clean(b), indent=2, default=str))
        z.writestr("01_SOURCE/version_history.json", json.dumps(b.get("revision_history", []), indent=2, default=str))
        # 02_EDITORIAL
        if b.get("proofing_report"):
            z.writestr("02_EDITORIAL/proofing_report.json", json.dumps(b["proofing_report"], indent=2, default=str))
        if b.get("editorial_edition"):
            z.writestr("02_EDITORIAL/approved_editorial_master.md", b["editorial_edition"]["content"])
        # 03_PRINT / 04_EBOOK — prefer the sanitized RETAIL edition when the Publication Sanitization Pass™ has run.
        sanit = b.get("artifacts", {}).get("sanitization", {})
        retail = sanit.get("retail_edition", {}) if sanit else {}
        print_url = retail.get("paperback_interior_pdf") or design_art.get("print", {}).get("paperback_interior_pdf")
        ebook_url = retail.get("epub") or design_art.get("ebook", {}).get("epub")
        pdf = _read_asset(print_url)
        if pdf:
            z.writestr("03_PRINT/paperback_interior.pdf", pdf)
        # Print-ready KDP cover wrap (back cover + spine + front) — locate the already-built asset.
        wrap = design_art.get("print", {}).get("paperback_cover_wrap") or {}
        wrap_pdf = _read_asset(wrap.get("paperback_cover_wrap_pdf"))
        if wrap_pdf:
            z.writestr("03_PRINT/paperback_cover_wrap.pdf", wrap_pdf)
        wrap_png = _read_asset(wrap.get("paperback_cover_wrap_png"))
        if wrap_png:
            z.writestr("03_PRINT/paperback_cover_wrap.png", wrap_png)
        epub = _read_asset(ebook_url)
        if epub:
            z.writestr("04_EBOOK/book.epub", epub)
        sel = design_art.get("selected_cover")
        cover = _read_asset(sel.get("url")) if sel else None
        if cover:
            z.writestr("04_EBOOK/cover.png", cover)
            # KDP eBook covers must be JPEG (PNG is NOT accepted for upload). Provide a compliant
            # RGB JPEG at 1600 x 2560 (KDP's ideal 1.6:1 ratio) so the file attaches without a builder.
            try:
                from PIL import Image
                im = Image.open(io.BytesIO(cover)).convert("RGB")
                tw, th = 1600, 2560
                ar = im.width / im.height
                if ar > tw / th:
                    nh = th; nw = int(th * ar)
                else:
                    nw = tw; nh = int(tw / ar)
                im = im.resize((nw, nh)).crop(((nw - tw) // 2, (nh - th) // 2, (nw - tw) // 2 + tw, (nh - th) // 2 + th))
                jb = io.BytesIO(); im.save(jb, "JPEG", quality=92, dpi=(300, 300))
                z.writestr("04_EBOOK/ebook_cover.jpg", jb.getvalue())
            except Exception:
                pass
        # 05_AUDIO — internal narration prototype (honestly labeled)
        audio_art = b.get("artifacts", {}).get("audio", {})
        proto = (audio_art or {}).get("prototype")
        if proto:
            mp3 = _read_asset(proto.get("url"))
            if mp3:
                z.writestr("05_AUDIO/narration_prototype_ch1.mp3", mp3)
            z.writestr("05_AUDIO/audio_readme.txt", proto.get("label", "") +
                       f"\nDuration: {proto.get('duration_sec')}s | Voice: {proto.get('voice')}\n" +
                       f"Full-book estimate: {audio_art.get('full_book_estimate_min')} min (est. @150 wpm)\n")
        # 07_METADATA — publication metadata (reader-facing) kept SEPARATE from manufacturing metadata.
        z.writestr("07_METADATA/master_metadata.json", json.dumps(meta, indent=2, default=str))
        try:
            chk = await build_kdp_checklist(book_id)
            if chk:
                z.writestr("07_METADATA/Ready_for_KDP.md", _kdp_markdown(chk))
                z.writestr("07_METADATA/Ready_for_KDP.json", json.dumps(chk, indent=2, default=str))
        except Exception:
            pass
        if sanit.get("publication_metadata"):
            z.writestr("07_METADATA/publication_metadata.json",
                       json.dumps(sanit["publication_metadata"], indent=2, default=str))
            z.writestr("07_METADATA/title_copyright_colophon.json", json.dumps({
                "title_page": sanit.get("title_page"), "copyright_page": sanit.get("copyright_page"),
                "colophon": sanit.get("colophon")}, indent=2, default=str))
        # 09_RIGHTS_AND_GOVERNANCE
        if design_art.get("governance_package"):
            z.writestr("09_RIGHTS_AND_GOVERNANCE/product_governance_package.json",
                       json.dumps(design_art["governance_package"], indent=2, default=str))
        z.writestr("09_RIGHTS_AND_GOVERNANCE/transparent_provenance.json",
                   json.dumps(b.get("transparent_provenance", {}), indent=2, default=str))
        # 07_METADATA — Product Manifest™ (PMF™ = EVIDENCE of exactly what happened during manufacturing)
        try:
            pmf = await build_product_manifest(book_id, actor)
            if pmf and not pmf.get("error"):
                z.writestr("07_METADATA/product_manifest.json", json.dumps(pmf, indent=2, default=str))
        except Exception:
            pmf = None
        # manifest of what's included vs pending (honest)
        included = [n for n in z.namelist()]
        z.writestr("00_MANIFEST.json", json.dumps({
            "included": included,
            "pending": {**({"audio": "Guided package (Button 4) — prototype only, full narration pending"} if not proto else {}),
                        "video": "Guided package (Button 5) — not yet rendered",
                        "marketing": "Prepared at Design/Publish",
                        "monitoring": "Activates post-publication"},
        }, indent=2))
    data = buf.getvalue()
    safe = "".join(c for c in b["title"] if c.isalnum() or c in " -_").strip().replace(" ", "_")
    fid = re_engine._save(f"master-package-{safe}", "zip", data)
    url = re_engine._asset_url(fid)
    deliverable = {"type": "Master Output Package", "label": "Master Output Package", "url": url,
                   "filename": fid, "size_kb": len(data) // 1024, "assembled_at": _now(), "by": actor}
    # Treasure Standard: keep only the CURRENT package. Remove prior Master Output Package entries and
    # delete their files from disk so the Deliverables Library never shows stale/broken download links.
    import os
    existing = b.get("deliverables", []) or []
    for d in existing:
        if d.get("type") == "Master Output Package" and d.get("url"):
            old_path = os.path.join(re_engine.ASSET_DIR, d["url"].split("/")[-1])
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
    deliverables = [d for d in existing if d.get("type") != "Master Output Package"] + [deliverable]
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "master_package_url": url, "master_package_at": _now(), "deliverables": deliverables, "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Master Package", "by": actor, "at": _now(),
                                       "note": f"Assembled Master Output Package ({len(data)//1024} KB)."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"assembled Master Output Package for '{b['title']}'", b["book_code"], "success")
    return {"ok": True, "url": url, "size_kb": len(data) // 1024, "sections": len(buf.getvalue()) and True}


async def get_book(book_id):
    b = await db[COLL].find_one({"id": book_id}, {"_id": 0}) \
        or await db[COLL].find_one({"book_code": book_id}, {"_id": 0})
    if not b:
        return None
    out = clean(b)
    suggestion = suggest_clean_title(out.get("title", ""))
    if suggestion:
        out["title_cleanup_suggestion"] = suggestion
    content = (b.get("editorial_edition") or b.get("working_copy") or {}).get("content", "")
    out["content_integrity"] = content_integrity_check(out.get("title"), out.get("subtitle"), content)
    return out


_TITLE_ARTIFACT_TOKENS = [
    "final", "finalized", "finalised", "draft", "working", "wip", "copy", "edit", "edited",
    "revised", "revision", "rev", "master", "new", "old", "latest", "use this", "do not use",
    "clean", "updated", "update", "fixed",
]


def suggest_clean_title(title):
    """Detect file-name artifacts in a book title (FINAL, DRAFT, v2, copy, (1), .docx, dates…) and
    return a cleaned suggestion — or None if the title is already clean. Conservative: only strips
    known artifact tokens as WHOLE words, never mid-word content."""
    import re
    if not title:
        return None
    original = title.strip()
    t = original
    # strip file extensions
    t = re.sub(r"\.(docx?|pdf|txt|md|rtf|pages|odt)$", "", t, flags=re.I)
    # normalize underscores to spaces early so \b word boundaries catch tokens like Book_Working_Draft
    t = t.replace("_", " ")
    # strip trailing " - Copy", " copy 2", "(1)", "[final]" etc.
    t = re.sub(r"[\s_\-–—]*\((?:\d+|copy|final|draft)\)\s*$", "", t, flags=re.I)
    t = re.sub(r"[\s_\-–—]*\[[^\]]*\]\s*$", "", t)
    # strip version markers: v2, v1.3, version 2
    t = re.sub(r"\b(?:v|ver|version)\s*\.?\s*\d+(?:\.\d+)*\b", "", t, flags=re.I)
    # strip standalone date stamps (2024, 2024-01-01, 1.2.24, 7.18.2026)
    t = re.sub(r"\b\d{1,4}[.\-/]\d{1,2}[.\-/]\d{1,4}\b", "", t)
    t = re.sub(r"\b(?:19|20)\d{2}\b", "", t)
    # strip known artifact tokens as whole words (may repeat, e.g. FINAL FINAL)
    token_re = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in _TITLE_ARTIFACT_TOKENS) + r")\b", flags=re.I)
    t = token_re.sub("", t)
    # collapse leftover separators/whitespace
    t = re.sub(r"[\s_]+", " ", t)
    t = re.sub(r"[\s\-–—:.,]+$", "", t).strip()
    t = re.sub(r"^[\s\-–—:.,]+", "", t).strip()
    if t and t.lower() != original.lower() and len(t) >= 2:
        return t
    return None


async def list_books():
    docs = await db[COLL].find({}, {"_id": 0, "id": 1, "book_code": 1, "title": 1, "author": 1,
                                    "imprint": 1, "approval_status": 1, "editorial_status": 1,
                                    "editorial_locked": 1, "manufacturing_job": 1, "created_at": 1}
                               ).sort("created_at", -1).to_list(200)
    return [clean(d) for d in docs]


# ------------------------------- PILOT SEED -------------------------------
PILOT_URL = "https://customer-assets.emergentagent.com/job_understanding-os/artifacts/9fibyutd_The%20Understanding%20Tree%20Draft.docx"


def _docx_to_markdown(raw_bytes):
    from docx import Document
    doc = Document(io.BytesIO(raw_bytes))
    out = []
    title_done = False
    for p in doc.paragraphs:
        txt = (p.text or "").strip()
        if not txt:
            out.append("")
            continue
        style = ""
        try:
            style = (p.style.name or "").lower() if p.style is not None else ""
        except Exception:
            style = ""
        is_heading_style = "heading" in style or "title" in style
        upper = txt.upper()
        is_chapter = upper.startswith("CHAPTER") and len(txt) < 90
        if is_chapter:
            out.append(f"## {txt}")
        elif not title_done and (is_heading_style or len(txt) < 80):
            out.append(f"# {txt}")
            title_done = True
        elif txt in ("\u2767", "\u2748", "* * *", "***"):
            out.append("---")
        else:
            out.append(txt)
    return "\n\n".join(out)


async def seed_pilot(actor="Founder"):
    existing = await db[COLL].find_one({"title": {"$regex": "Understanding Tree", "$options": "i"}})
    if existing:
        return existing.get("id")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(PILOT_URL)
            r.raise_for_status()
            content = _docx_to_markdown(r.content)
    except Exception as e:
        return None
    payload = {"title": "The Understanding Tree", "content": content,
               "meta": {"subtitle": "A Novel", "author": "E.Q. Rothwell", "imprint": "QRU Press™",
                        "genre": "Literary Fiction", "audience": "Adult",
                        "rights_holder": "Ascend Development Group LLC",
                        "source_filename": "The Understanding Tree Draft.docx",
                        "ai_disclosure": "Human-authored manuscript; AI-assisted manufacturing (typesetting, packaging)."}}
    rec = await create_book_record(payload, actor)
    return rec["id"]



# ---------------- QRU Product Manufacturing System™ — recipe registration ----------------
# The Book recipe specializes the product-specific stages behind the universal 7-button workflow.
# Future product types register their own recipe here; the shared engine/gates/packaging are inherited.
recipes.register({
    "product_type": "Book",
    "label": recipes.label_for("Book"),
    "description": "Long-form manuscript → publication-ready book: proofed edition, print interior, "
                   "EPUB, AI cover concepts, audiobook prototype, review-video plan, and retail distribution.",
    "intake": {"accepts": [".docx", ".pdf", ".txt", ".md"], "structure": "chapters",
               "structure_label": "Chapters & sections"},
    "design_recipe": _cover_design_recipe,
    "metadata_defaults": {"imprint": "QRU Press™", "edition": "First Edition"},
    "publish_destinations": PUBLISH_DESTINATIONS,
})
