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
import hashlib
from datetime import datetime, timezone

from database import db
from models import gen_id, now_iso, clean
from org_activity import log_org
import book_structure as bs
import product_governance as pg

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


# -------------------------- BUTTON 2 — PROOF & POLISH --------------------------
def _proof_checks(content):
    """Deterministic proofing — NEVER rewrites voice. Only reports classified findings."""
    import re
    findings = []
    lines = content.split("\n")
    # repeated consecutive words ("the the")
    for m in re.finditer(r"\b(\w+)\s+\1\b", content, flags=re.IGNORECASE):
        findings.append({"type": "Required correction", "issue": f"Repeated word: '{m.group(0)}'",
                         "detail": "Duplicate consecutive word detected."})
    # double spaces
    dbl = content.count("  ")
    if dbl:
        findings.append({"type": "Recommended improvement", "issue": f"{dbl} double-space occurrence(s)",
                         "detail": "Collapse to single spaces for clean typesetting."})
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
        return {"error": "Editorial edition is locked. Unlock via a governed revision to re-proof."}
    content = b["working_copy"]["content"]
    findings, structure = _proof_checks(content)
    required = [f for f in findings if f["type"] == "Required correction"]
    report = {
        "generated_at": _now(),
        "findings": findings,
        "counts": {
            "required": len(required),
            "recommended": len([f for f in findings if f["type"] == "Recommended improvement"]),
            "optional": len([f for f in findings if f["type"] == "Optional stylistic suggestion"]),
            "founder_decision": len([f for f in findings if f["type"] == "Founder decision required"]),
            "words": len(content.split()), "chapters": len(structure["chapters"]),
        },
        "unresolved_questions": [f["issue"] for f in findings if f["type"] == "Founder decision required"],
        "voice_note": "The Factory never silently rewrites the author's voice. All items above are reported for your decision.",
    }
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "editorial_status": "Proofed — awaiting approval", "proofing_report": report,
        "manufacturing_job": {"stage": "Proof & Polish complete", "next": "Approve & lock editorial edition, then Design"},
        "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Proof & Polish", "by": actor, "at": _now(),
                                       "note": f"{len(findings)} finding(s); {len(required)} required."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"proofed '{b['title']}' ({len(findings)} findings)", b["book_code"])
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


# ----------------------------- BUTTON 3 — DESIGN -----------------------------
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
    # Cover concepts (≥3 strategically different) — deterministic, rights-safe.
    from PIL import Image, ImageDraw
    concepts = []
    palettes = [((53, 16, 106), (34, 26, 66), "Royal Depth"),
                ((26, 42, 74), (12, 20, 40), "Midnight Ascend"),
                ((74, 30, 30), (30, 12, 12), "Warm Literary")]
    for idx, (c1, c2, name) in enumerate(palettes, 1):
        img = Image.new("RGB", (1024, 1536), c1); d = ImageDraw.Draw(img)
        for y in range(1536):
            t = y / 1536
            d.line([(0, y), (1024, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
        d.rectangle([80, 90, 944, 1446], outline=(245, 178, 26), width=6)
        d.text((512, 520), b["title"][:40], fill=(255, 255, 255), anchor="mm")
        if b.get("author"):
            d.text((512, 1360), b["author"], fill=(245, 178, 26), anchor="mm")
        d.text((512, 180), b.get("imprint", "").upper(), fill=(245, 178, 26), anchor="mm")
        buf = io.BytesIO(); img.save(buf, "PNG")
        fid = re_engine._save(f"bookcover-c{idx}", "png", buf.getvalue())
        concepts.append({"concept": idx, "name": name, "url": re_engine._asset_url(fid),
                         "thumbnail_legible": True, "rights": "Rights-safe (generated, no third-party imagery)"})
    cover_bytes = None
    cpath = concepts[0]["url"].split("/")[-1]
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
    artifacts = b.get("artifacts", {})
    artifacts["design"] = {
        "generated_at": _now(),
        "cover_concepts": concepts, "selected_cover": None,
        "print": {"paperback_interior_pdf": re_engine._asset_url(interior_fid),
                  "trim_size": "6x9 in", "bleed": "0.125 in", "toc": "Clickable + printed (Reading Experience Standard™)"},
        "ebook": {"epub": epub_url, "kindle_ready": bool(epub_url), "clickable_toc": True},
        "governance_package": gp,
        "notes": "Hardcover case-laminate + barcode-safe wrap are prepared at Publish once final trim & page count confirm.",
    }
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "artifacts": artifacts, "manufacturing_job": {"stage": "Design drafted", "next": "Select final cover, then Audio/Video/Publish"},
        "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Design", "by": actor, "at": _now(),
                                       "note": f"{len(concepts)} cover concepts, print interior + EPUB rendered."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"designed print + ebook for '{b['title']}'", b["book_code"], "success")
    b = await db[COLL].find_one({"id": book_id})
    return clean(b)


async def select_cover(book_id, concept_no, actor):
    b = await db[COLL].find_one({"id": book_id})
    if not b or not b.get("artifacts", {}).get("design"):
        return {"error": "Run Design first."}
    design_art = b["artifacts"]["design"]
    match = next((c for c in design_art["cover_concepts"] if c["concept"] == concept_no), None)
    if not match:
        return {"error": "Cover concept not found."}
    design_art["selected_cover"] = match
    await db[COLL].update_one({"id": book_id}, {"$set": {"artifacts.design": design_art, "updated_at": _now()}})
    await log_org("Book Manufacturing™", "Manufacturing", f"selected cover concept {concept_no} for '{b['title']}'", b["book_code"])
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
        "pricing_approved": False,
        "platform_files_passed": design_done,
        "founder_authorization_received": False,
    }
    return {"book_title": b["title"], "book_code": b["book_code"], "destinations": destinations,
            "final_release_gate": gate,
            "gate_ready": all(gate.values()),
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
        # 03_PRINT / 04_EBOOK
        pdf = _read_asset(design_art.get("print", {}).get("paperback_interior_pdf"))
        if pdf:
            z.writestr("03_PRINT/paperback_interior.pdf", pdf)
        epub = _read_asset(design_art.get("ebook", {}).get("epub"))
        if epub:
            z.writestr("04_EBOOK/book.epub", epub)
        sel = design_art.get("selected_cover")
        cover = _read_asset(sel.get("url")) if sel else None
        if cover:
            z.writestr("04_EBOOK/cover.png", cover)
        # 07_METADATA
        z.writestr("07_METADATA/master_metadata.json", json.dumps(meta, indent=2, default=str))
        # 09_RIGHTS_AND_GOVERNANCE
        if design_art.get("governance_package"):
            z.writestr("09_RIGHTS_AND_GOVERNANCE/product_governance_package.json",
                       json.dumps(design_art["governance_package"], indent=2, default=str))
        z.writestr("09_RIGHTS_AND_GOVERNANCE/transparent_provenance.json",
                   json.dumps(b.get("transparent_provenance", {}), indent=2, default=str))
        # manifest of what's included vs pending (honest)
        included = [n for n in z.namelist()]
        z.writestr("00_MANIFEST.json", json.dumps({
            "included": included,
            "pending": {"audio": "Guided package (Button 4) — not yet rendered",
                        "video": "Guided package (Button 5) — not yet rendered",
                        "marketing": "Prepared at Design/Publish",
                        "monitoring": "Activates post-publication"},
        }, indent=2))
    data = buf.getvalue()
    safe = "".join(c for c in b["title"] if c.isalnum() or c in " -_").strip().replace(" ", "_")
    fid = re_engine._save(f"master-package-{safe}", "zip", data)
    url = re_engine._asset_url(fid)
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "master_package_url": url, "master_package_at": _now(), "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Master Package", "by": actor, "at": _now(),
                                       "note": f"Assembled Master Output Package ({len(data)//1024} KB)."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"assembled Master Output Package for '{b['title']}'", b["book_code"], "success")
    return {"ok": True, "url": url, "size_kb": len(data) // 1024, "sections": len(buf.getvalue()) and True}


async def get_book(book_id):
    b = await db[COLL].find_one({"id": book_id}, {"_id": 0})
    return clean(b) if b else None


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
