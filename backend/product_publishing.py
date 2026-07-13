"""QRU Product Publishing™ — the honest last mile for a rendered book/product.

Two governed destinations from a rendered deliverable:
  • Add to QRU Store™ — native, real. Sets the product Published so it is purchasable (only when a
    customer-ready deliverable actually exists — never a faked publish).
  • KDP-Ready Export™ — Amazon KDP has NO public publishing API, so we honestly produce a print-ready
    package (interior PDF + cover + a metadata/keywords sheet + step-by-step upload instructions) that
    the founder uploads once at kdp.amazon.com. No fake "published to Amazon" state.
"""
import os
import zipfile
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from database import db
from models import now_iso
import rendering_engine as re_engine
import kr_inheritance as kri

KDP_DIR = Path(os.environ.get("QRU_KDP_DIR", "/app/backend/generated_kdp"))
KDP_DIR.mkdir(parents=True, exist_ok=True)
AUDIOBOOK_DIR = Path(os.environ.get("QRU_AUDIOBOOK_DIR", "/app/backend/generated_audiobooks"))
AUDIOBOOK_DIR.mkdir(parents=True, exist_ok=True)

VOICES = {"onyx", "sage", "nova", "shimmer", "echo", "alloy", "fable"}

NAVY = (11, 16, 48)
GOLD = (231, 181, 60)


def _s(t):
    return str(t or "").encode("latin-1", "replace").decode("latin-1")


async def _cover_bytes(p):
    cid = p.get("cover_asset_id")
    if cid:
        ca = await db.cover_assets.find_one({"id": cid}, {"_id": 0})
        if ca and ca.get("file") and os.path.exists(ca["file"]):
            with open(ca["file"], "rb") as f:
                return f.read()
    return None


def _pdf_bytes_from_deliverable(p):
    cd = p.get("customer_deliverable") or {}
    for f in cd.get("files", []):
        if f.get("format") == "pdf" and f.get("filename"):
            path = os.path.join(re_engine.ASSET_DIR, f["filename"])
            if os.path.exists(path):
                with open(path, "rb") as fh:
                    return fh.read()
    return None


async def publish_to_store(product_id, actor="Founder"):
    p = await db.products.find_one({"id": product_id})
    if not p:
        return None
    if not p.get("deliverable_ready"):
        return {"ok": False, "message": "Render the deliverable first — nothing is published to the Store until a customer-ready file exists (Treasure Standard™).",
                "blockers": ["Deliverable not rendered"]}
    upd = {"status": "Published", "founder_approved_at": now_iso(), "updated_at": now_iso()}
    if not p.get("cover_url") and p.get("cover_asset_id"):
        upd["cover_url"] = f"/api/publishing/cover/{p['cover_asset_id']}/file"
    await db.products.update_one({"id": product_id}, {"$set": upd})
    await db.activities.insert_one({"actor": actor, "action": "publish:store", "entity": "Product",
                                    "entity_id": product_id, "detail": p.get("product_code", ""), "created_at": now_iso()})
    return {"ok": True, "message": "Published to the QRU Store™ — now purchasable.", "store_url": "/store",
            "product_id": product_id, "status": "Published"}


def _metadata(p, inh):
    title = p.get("title") or (inh or {}).get("term") or "Untitled"
    subtitle = p.get("subtitle") or (inh or {}).get("subtitle") or ""
    desc = (inh or {}).get("definition_professional") or (p.get("content") or "")[:600] or (inh or {}).get("definition_plain") or ""
    keywords = [k for k in ((inh or {}).get("tags") or []) if str(k).lower() not in ("qru", "draft", "verified")]
    audience = p.get("audience") or "General readers"
    return {
        "title": title, "subtitle": subtitle, "author": p.get("author") or "QRU Press",
        "description": desc.strip()[:1200], "keywords": [str(k) for k in keywords][:7] or ["understanding", "learning", "education"],
        "categories": ["Education & Teaching", "Study & Test Preparation"],
        "language": "English", "audience": audience,
        "trim_size": '6" x 9" (15.24 x 22.86 cm)', "interior": "Black & White on White paper",
    }


def _metadata_pdf(meta):
    pdf = FPDF()
    pdf.set_auto_page_break(True, 18)
    pdf.set_margins(20, 20, 20)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20); pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 10, _s("Amazon KDP — Publishing Kit"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(*GOLD); pdf.set_line_width(0.6); pdf.line(20, pdf.get_y() + 1, 60, pdf.get_y() + 1); pdf.ln(6)

    def field(label, value):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*NAVY)
        pdf.multi_cell(0, 6, _s(label.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 11); pdf.set_text_color(40, 40, 55)
        pdf.multi_cell(0, 6, _s(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(2)

    field("Title", meta["title"])
    if meta["subtitle"]:
        field("Subtitle", meta["subtitle"])
    field("Author", meta["author"])
    field("Language", meta["language"])
    field("Description", meta["description"])
    field("Keywords (7 max)", ", ".join(meta["keywords"]))
    field("Categories", " | ".join(meta["categories"]))
    field("Target Audience", meta["audience"])
    field("Trim Size", meta["trim_size"])
    field("Interior", meta["interior"])

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 8, _s("How to publish on Amazon KDP"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    steps = [
        "Go to kdp.amazon.com and sign in (or create a free KDP account).",
        "Click 'Create' → choose Paperback (or Kindle eBook).",
        "Enter the Title, Subtitle, Author, Description, Keywords and Categories exactly as listed above.",
        "Upload 'interior.pdf' (the book interior) from this package.",
        "Upload 'cover.png' as the cover — confirm KDP's trim size matches 6x9 in.",
        "Preview with KDP's Previewer, set your price and territories, then click Publish.",
        "Amazon reviews and lists your book (usually within 72 hours).",
    ]
    pdf.set_font("Helvetica", "", 11); pdf.set_text_color(40, 40, 55)
    for i, st in enumerate(steps, 1):
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, _s(f"{i}.  {st}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 9); pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, _s("Amazon KDP has no public API for automated publishing, so QRU produces this print-ready kit for a one-time upload. QRU never claims a product is 'live on Amazon' until you publish it there. Treasure Standard(TM)."), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    return bytes(pdf.output())


async def kdp_package(product_id, actor="Founder"):
    p = await db.products.find_one({"id": product_id})
    if not p:
        return None
    if not p.get("deliverable_ready"):
        return {"ok": False, "message": "Render the deliverable first — a KDP kit needs the interior PDF (Treasure Standard™)."}
    interior = _pdf_bytes_from_deliverable(p)
    if not interior:
        return {"ok": False, "message": "No interior PDF found on this deliverable. Re-render the product, then export."}
    cover = await _cover_bytes(p)
    inh = None
    if p.get("knowledge_record_id"):
        kr = await kri.load_kr(db, p["knowledge_record_id"])
        if kr:
            inh = kri.build_inheritance(kr)
    meta = _metadata(p, inh)
    meta_pdf = _metadata_pdf(meta)

    zip_path = KDP_DIR / f"{product_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("interior.pdf", interior)
        if cover:
            z.writestr("cover.png", cover)
        z.writestr("KDP-Publishing-Kit.pdf", meta_pdf)
    files = ["interior.pdf", "KDP-Publishing-Kit.pdf"] + (["cover.png"] if cover else [])
    await db.activities.insert_one({"actor": actor, "action": "export:kdp", "entity": "Product",
                                    "entity_id": product_id, "detail": p.get("product_code", ""), "created_at": now_iso()})
    return {"ok": True, "message": "KDP-Ready package built — upload it once at kdp.amazon.com.",
            "download_url": f"/api/publishing/product/{product_id}/kdp-file",
            "contents": files, "metadata": meta, "cover_included": bool(cover)}


def kdp_file_path(product_id):
    return KDP_DIR / f"{product_id}.zip"


# ── Audiobook edition — narrate any book/product via OpenAI TTS (Emergent key) ──
def _chunk_text(text, limit=3900):
    words, chunks, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > limit:
            chunks.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        chunks.append(cur)
    return chunks or [text[:limit]]


def _clean_for_narration(text):
    import re
    t = re.sub(r"[#*_>`~]", " ", text or "")
    t = re.sub(r"\!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"\n{2,}", ". ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


async def _narration_source(p):
    """Prefer the book's real cleaned content; fall back to the verified KR (Knowledge-First)."""
    cd = p.get("customer_deliverable") or {}
    body = cd.get("clean_content") or p.get("content") or ""
    if len(body.strip()) < 120 and p.get("knowledge_record_id"):
        kr = await kri.load_kr(db, p["knowledge_record_id"])
        if kr:
            inh = kri.build_inheritance(kr)
            parts = [inh["definition_professional"], " ".join(inh["key_points"]), " ".join(inh["examples"]), inh["memory_sentence"]]
            body = ". ".join([x for x in parts if x])
    return _clean_for_narration(body)


async def _audiobook_job(product_id, voice, model, actor):
    p = await db.products.find_one({"id": product_id})
    if not p:
        return
    title = p.get("title") or "This edition"
    body = await _narration_source(p)
    script = f"{title}. Presented by QRU Press. {body}"
    try:
        from emergentintegrations.llm.openai import OpenAITextToSpeech
        tts = OpenAITextToSpeech(api_key=os.getenv("EMERGENT_LLM_KEY"))
        audio = b""
        for chunk in _chunk_text(script):
            audio += await tts.generate_speech(text=chunk, model=model, voice=voice)
    except Exception as e:
        await db.products.update_one({"id": product_id}, {"$set": {
            "audiobook.status": "FAILED", "audiobook.error": str(e)[:180], "updated_at": now_iso()}})
        return
    (AUDIOBOOK_DIR / f"{product_id}.mp3").write_bytes(audio)
    est_seconds = int(len(body.split()) / 2.5)
    await db.products.update_one({"id": product_id}, {"$set": {"audiobook": {
        "status": "READY", "format": "mp3", "voice": voice, "bytes": len(audio),
        "url": f"/api/publishing/product/{product_id}/audiobook-file",
        "est_seconds": est_seconds, "narrated_from": "book" if (p.get("content") or "").strip() else "knowledge_record",
        "created_by": actor, "created_at": now_iso()}, "updated_at": now_iso()}})
    await db.activities.insert_one({"actor": actor, "action": "make:audiobook", "entity": "Product",
                                    "entity_id": product_id, "detail": p.get("product_code", ""), "created_at": now_iso()})


async def make_audiobook(product_id, voice="onyx", model="tts-1", actor="Founder"):
    """Start an audiobook narration in the background (TTS can exceed the 60s ingress limit).
    The founder polls audiobook_status until READY."""
    p = await db.products.find_one({"id": product_id})
    if not p:
        return None
    voice = voice if voice in VOICES else "onyx"
    body = await _narration_source(p)
    if len(body) < 60:
        return {"ok": False, "message": "This product has no readable content yet to narrate — render its deliverable first."}
    await db.products.update_one({"id": product_id}, {"$set": {"audiobook": {
        "status": "RENDERING", "voice": voice, "created_by": actor, "created_at": now_iso()}, "updated_at": now_iso()}})
    import asyncio
    asyncio.create_task(_audiobook_job(product_id, voice, model, actor))
    return {"ok": True, "status": "RENDERING", "voice": voice,
            "message": f"Narrating the audiobook ({voice}) — this runs in the background. It will appear here when ready."}


async def audiobook_status(product_id):
    p = await db.products.find_one({"id": product_id}, {"_id": 0, "audiobook": 1})
    if not p:
        return None
    return p.get("audiobook") or {"status": "NONE"}


def audiobook_file_path(product_id):
    return AUDIOBOOK_DIR / f"{product_id}.mp3"
