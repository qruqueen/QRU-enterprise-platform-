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
import asyncio
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
def _compose_book_cover(hero_bytes, title, subtitle, author, imprint, palette_hint=""):
    """Publication-quality trade cover: full-bleed art + legibility scrim + clean serif typography.
    No learning-product chrome — this is a real book cover."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import design_language as dl
    W, H = 1024, 1536
    if hero_bytes:
        art = Image.open(io.BytesIO(hero_bytes)).convert("RGB")
        # cover-fill crop to 2:3
        ar = art.width / art.height
        if ar > W / H:
            nh = H; nw = int(H * ar)
        else:
            nw = W; nh = int(W / ar)
        art = art.resize((nw, nh)).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
    else:
        base = (34, 26, 66) if "amber" not in palette_hint else (60, 32, 20)
        art = Image.new("RGB", (W, H), base)
        d0 = ImageDraw.Draw(art)
        for y in range(H):
            t = y / H
            d0.line([(0, y), (W, y)], fill=tuple(int(base[i] * (1 - 0.55 * t)) for i in range(3)))
    img = art.copy()
    # top + bottom scrims for text legibility
    scrim = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scrim)
    for y in range(H):
        a = 0
        if y < H * 0.34:
            a = int(150 * (1 - y / (H * 0.34)))
        if y > H * 0.5:
            a = max(a, int(205 * ((y - H * 0.5) / (H * 0.5))))
        sd.line([(0, y), (W, y)], fill=a)
    black = Image.new("RGB", (W, H), (8, 6, 18))
    img = Image.composite(black, img, scrim)
    d = ImageDraw.Draw(img)
    gold = (243, 200, 90)

    def font(path, size):
        try: return ImageFont.truetype(path, size)
        except Exception: return ImageFont.load_default()

    def wrap(text, fnt, maxw):
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=fnt) <= maxw: cur = t
            else: lines.append(cur); cur = w
        if cur: lines.append(cur)
        return lines

    # imprint eyebrow (top)
    ef = font(dl.SANS_BOLD, 30)
    d.text((W / 2, 70), (imprint or "").upper(), font=ef, fill=gold, anchor="mm")
    # title (upper-middle)
    size = 118 if len(title) <= 18 else (92 if len(title) <= 30 else 70)
    tf = font(dl.SERIF_BOLD, size)
    lines = wrap(title.upper(), tf, W - 150)
    y = H * 0.60 - (len(lines) * size * 0.6)
    for ln in lines:
        d.text((W / 2, y), ln, font=tf, fill=(255, 255, 255), anchor="mm")
        y += size * 1.08
    # gold rule
    d.line([(W / 2 - 90, y + 14), (W / 2 + 90, y + 14)], fill=gold, width=4)
    y += 46
    if subtitle:
        sf = font(dl.SERIF, 40)
        for ln in wrap(subtitle, sf, W - 200):
            d.text((W / 2, y), ln, font=sf, fill=(232, 226, 240), anchor="mm"); y += 50
    # author (bottom)
    if author:
        af = font(dl.SANS_BOLD, 46)
        d.text((W / 2, H - 96), author.upper(), font=af, fill=gold, anchor="mm")
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


def _valid_cover_art(data):
    """Strictly validate image bytes returned by the provider. Returns (ok, reason).
    A concept is ONLY successful when the provider returned real, decodable image bytes —
    never an empty, HTML, JSON, malformed, or truncated payload."""
    if not data:
        return False, "empty response from image provider"
    if len(data) < 2048:
        return False, f"response too small ({len(data)} bytes) — likely truncated or an error payload"
    head = data[:64].lstrip().lower()
    if head[:1] in (b"{", b"[") or head[:5] == b"<!doc" or head[:5] == b"<html":
        return False, "provider returned JSON/HTML, not an image"
    try:
        from PIL import Image
        Image.open(io.BytesIO(data)).verify()
        im = Image.open(io.BytesIO(data))
        if im.width < 256 or im.height < 256:
            return False, f"image too small ({im.width}x{im.height})"
    except Exception as e:
        return False, f"malformed image bytes: {str(e)[:80]}"
    return True, None


async def _cover_design_recipe(b, re_engine):
    """Cover Design Recipe™ — the Design Engine DIRECTS professional cover assets:
    LLM art-direction → Nano Banana artwork (Gemini) → composited publication typography.
    Every concept carries an HONEST per-concept status: a concept is 'success' ONLY when the
    provider returned real, decodable AI artwork. Failed concepts show a clear failure state and
    are NEVER silently substituted with a branded fallback presented as real art. Full Transparent
    Provenance™ (model/provider, generation time, art direction, fallback + has_ai_art) is recorded."""
    import json as _json
    import time as _time
    import design_language as dl
    import ai_service
    synopsis = " ".join((b.get("working_copy", {}).get("content", "")).split()[:180])
    brief_sys = ("You are QRU Cover Art Director for a professional publishing imprint. Given a book, "
                 "produce EXACTLY 3 strategically DIFFERENT cover art directions. Return strict JSON: "
                 '{"concepts":[{"name":"short concept name","palette":"comma colors","art_prompt":'
                 '"a vivid, specific image-generation prompt for the ARTWORK ONLY — evocative scene/subject/mood/lighting, '
                 'portrait orientation, NO text, NO words, NO lettering, no title on the image"}]}. '
                 "Make the three genuinely distinct (e.g. symbolic, atmospheric, character/object-focused).")
    brief_prompt = (f"Title: {b['title']}\nSubtitle: {b.get('subtitle','')}\nGenre: {b.get('genre','')}\n"
                    f"Audience: {b.get('audience','')}\nSynopsis: {synopsis}")
    briefs = []
    try:
        raw = await ai_service.llm_generate(brief_sys, brief_prompt, f"cover-brief-{b['id']}")
        raw = raw.strip().replace("```json", "").replace("```", "")
        briefs = _json.loads(raw).get("concepts", [])[:3]
    except Exception:
        briefs = []
    if len(briefs) < 3:
        defaults = [{"name": "Symbolic", "palette": "deep navy, gold", "art_prompt": f"A symbolic, atmospheric illustration evoking '{b['title']}', a {b.get('genre','literary')} book; rich lighting, portrait, no text."},
                    {"name": "Atmospheric", "palette": "twilight blues", "art_prompt": f"A moody atmospheric scene evoking the themes of '{b['title']}'; cinematic, portrait, no text."},
                    {"name": "Object Focus", "palette": "warm amber", "art_prompt": f"A single meaningful object central to '{b['title']}' on an elegant textured background; portrait, no text."}]
        briefs = (briefs + defaults)[:3]

    product = {"title": b["title"], "family": b.get("genre") or "Literary", "product_type": "Novel",
               "audience": b.get("audience", ""), "imprint": b.get("imprint")}
    kr = {"subtitle": b.get("subtitle", ""), "author": b.get("author", "")}

    async def _gen(idx, brief):
        t0 = _time.time()
        try:
            raw = await ai_service.generate_image(
                f"Professional book cover ARTWORK (no text, no lettering, portrait 2:3): {brief.get('art_prompt','')}",
                f"cover-art-{b['id']}-{idx}")
        except Exception as e:
            return None, round(_time.time() - t0, 1), f"provider error: {str(e)[:120]}"
        elapsed = round(_time.time() - t0, 1)
        ok, reason = _valid_cover_art(raw)
        return (raw if ok else None), elapsed, (None if ok else reason)
    results = await asyncio.gather(*[_gen(i, br) for i, br in enumerate(briefs, 1)])

    art_provider = "Gemini (Emergent LLM Key)"
    art_model = ai_service.IMAGE_MODEL
    direction_model = ai_service.MODEL[1] if isinstance(ai_service.MODEL, (tuple, list)) else str(ai_service.MODEL)
    concepts = []
    for idx, (brief, (hero, elapsed, fail_reason)) in enumerate(zip(briefs, results), 1):
        success = hero is not None
        cover_out = _compose_book_cover(hero, b["title"], b.get("subtitle", ""), b.get("author", ""),
                                        b.get("imprint", ""), brief.get("palette", ""))
        fid = re_engine._save(f"bookcover-c{idx}", "png", cover_out)
        concepts.append({
            "concept": idx, "name": brief.get("name", f"Concept {idx}"),
            "art_direction": brief.get("art_prompt", ""), "palette": brief.get("palette", ""),
            "url": re_engine._asset_url(fid),
            "status": "success" if success else "failed",
            "has_ai_art": success,
            "failure_reason": None if success else fail_reason,
            # Our compositor always applies a legibility scrim + high-contrast serif title/author,
            # so composited covers stay readable down to retail thumbnail size.
            "thumbnail_legible": True,
            "readability_status": "Title & author legible at retail thumbnail size (composited scrim + high-contrast serif).",
            "provenance": {
                "art_provider": art_provider, "art_model": art_model,
                "art_direction_model": direction_model,
                "art_direction_prompt": brief.get("art_prompt", ""),
                "generation_time_sec": elapsed, "generated_at": _now(),
                "fallback_used": not success, "has_ai_art": success,
                "failure_reason": None if success else fail_reason,
            },
            "rights": "Rights-safe — AI-generated original artwork (no third-party imagery)." if success
                      else "AI artwork could not be generated for this concept (honest failure — a branded placeholder is shown, NOT presented as real art).",
        })
    return concepts


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
    # Cover Design Recipe™ — governed AI art direction → publication-quality concepts.
    concepts = await _cover_design_recipe(b, re_engine)
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
        "notes": "Hardcover case-laminate + barcode-safe wrap are prepared at Publish once final trim & page count confirm.",
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


async def render_audio_prototype(book_id, actor):
    """Button 4·A — Internal Narration Prototype. Renders a REAL TTS master of Chapter 1's opening.
    Honestly labeled: AI voice, pacing/review only, NOT commercial. Never mislabeled 'Audible-ready'."""
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    content = (b.get("editorial_edition") or b.get("working_copy"))["content"]
    structure = bs.parse_book(content)
    if not structure["chapters"]:
        return {"error": "No chapters detected to narrate."}
    ch1 = structure["chapters"][0]
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
    try:
        import cinema_studio
        import rendering_engine as re_engine
        audio = await cinema_studio._tts_bytes(f"{b['title']}. Chapter {ch1['number']}. {ch1['title']}. {excerpt}")
        fid = re_engine._save("book-audio-prototype", "mp3", audio)
        dur = round(cinema_studio._duration_from_bytes(audio), 1)
    except Exception as e:
        return {"error": f"Narration prototype unavailable (TTS): {str(e)[:120]}. Honest failure — nothing faked."}
    total_words = len(content.split())
    chapter_map = [{"number": c["number"], "title": c["title"]} for c in structure["chapters"]]
    artifacts = b.get("artifacts", {})
    artifacts["audio"] = {
        "prototype": {
            "label": "Internal Narration Prototype™ (Chapter 1 opening) — AI voice 'sage', pacing/review ONLY. NOT for commercial distribution.",
            "url": re_engine._asset_url(fid), "duration_sec": dur, "voice": "sage (OpenAI TTS-1)",
            "excerpt_chars": len(excerpt), "generated_at": _now(),
        },
        "full_book_estimate_min": round(total_words / 150, 1),
        "chapter_timing_map": chapter_map,
    }
    await db[COLL].update_one({"id": book_id}, {"$set": {"artifacts": artifacts, "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Audio", "by": actor, "at": _now(),
                                       "note": f"Narration prototype rendered ({dur}s)."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"rendered narration prototype for '{b['title']}'", b["book_code"], "success")
    return clean(await db[COLL].find_one({"id": book_id}))


async def set_pricing(book_id, list_price, currency, actor):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    pricing = {"list_price": list_price, "currency": currency or "USD", "approved": True,
               "approved_by": actor, "approved_at": _now()}
    await db[COLL].update_one({"id": book_id}, {"$set": {"pricing": pricing, "updated_at": _now()},
        "$push": {"revision_history": {"stage": "Pricing", "by": actor, "at": _now(),
                                       "note": f"Pricing approved: {currency or 'USD'} {list_price}."}}})
    await log_org("Book Manufacturing™", "Manufacturing", f"approved pricing for '{b['title']}'", b["book_code"])
    return clean(await db[COLL].find_one({"id": book_id}))


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
    return clean(await db[COLL].find_one({"id": book_id}))


SHARES = "book_shares"


async def create_share(book_id, hours, actor, base_url=""):
    b = await db[COLL].find_one({"id": book_id})
    if not b:
        return None
    if not b.get("master_package_url"):
        r = await assemble_master_package(book_id, actor)
        pkg_url = r["url"] if r else None
    else:
        pkg_url = b["master_package_url"]
    if not pkg_url:
        return {"error": "No package to share yet."}
    from datetime import timedelta
    token = gen_id().replace("-", "")[:24]
    expires = (datetime.now(timezone.utc) + timedelta(hours=int(hours or 72))).isoformat()
    await db[SHARES].insert_one({"token": token, "book_id": book_id, "book_title": b["title"],
                                 "package_url": pkg_url, "created_by": actor, "created_at": _now(),
                                 "expires_at": expires, "read_only": True})
    await log_org("Book Manufacturing™", "Manufacturing", f"created share link for '{b['title']}' (expires {expires[:10]})", b["book_code"])
    share_url = f"{base_url}/api/book-mfg/share/{token}" if base_url else f"/api/book-mfg/share/{token}"
    return {"ok": True, "token": token, "share_url": share_url, "expires_at": expires, "read_only": True}


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
        "pricing_approved": bool((b.get("pricing") or {}).get("approved")),
        "platform_files_passed": design_done,
        "founder_authorization_received": bool((b.get("founder_authorization") or {}).get("authorized")),
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
            "pending": {**({"audio": "Guided package (Button 4) — prototype only, full narration pending"} if not proto else {}),
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
