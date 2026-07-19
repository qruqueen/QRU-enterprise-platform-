"""QRU Video Fulfillment™ — turn a product's video "contract" into a real, publishable MP4.

Honest by design (Treasure Standard™): the video is IMAGE-BASED MOTION (Ken Burns pans/zooms
over AI scene art) + real AI narration — NOT frame-by-frame cel animation. Every video inherits
from the product's verified Knowledge Record™ (Knowledge-First). The rendered MP4 is registered
as a Factory-owned vault asset (db.media_assets, provider=qru_production) so the YouTube Publisher™
and the Distribution Framework™ can publish it directly — no manual upload needed.
"""
import os
import shutil
import logging

from database import db
from models import gen_id, now_iso
import cinema_studio as cinema
import rendering_engine as re_engine
import media_production as mp
from media_division import _resolve_kr, _is_verified

logger = logging.getLogger("qru.video_fulfillment")

# Default technique — a short, honest promotional/educational video.
DEFAULT_FORMAT = "promo_video"
_TECHNIQUE = "Image-based motion (Ken Burns) + AI narration — NOT frame-by-frame animation."


async def existing_video_asset(product_id):
    """Return an already-manufactured, distribution-ready Factory video for this product, if any."""
    return await db.media_assets.find_one(
        {"product_id": product_id, "kind": "video", "provider": "qru_production",
         "internal_storage_url": {"$exists": True}},
        {"_id": 0})


def _asset_on_disk(doc):
    path = doc.get("internal_storage_url") if doc else None
    if path and os.path.exists(os.path.abspath(path)) and os.path.getsize(os.path.abspath(path)) > 0:
        return os.path.abspath(path)
    return None


async def ensure_product_video(product_id, actor="Founder", format_id=DEFAULT_FORMAT, force=False):
    """Idempotently produce + register a real MP4 for a product.

    Returns {"ok": True, "asset": <vault doc>, "path": <disk path>, "reused": bool}
    or {"ok": False, "error": str} (honest — never fabricates a file).
    """
    product = await db.products.find_one({"id": product_id})
    if not product:
        return {"ok": False, "error": "Product not found."}

    if not force:
        existing = await existing_video_asset(product_id)
        path = _asset_on_disk(existing)
        if existing and path:
            return {"ok": True, "asset": existing, "path": path, "reused": True}

    kr_id = product.get("knowledge_record_id") or (product.get("inherits_from") or {}).get("kr_id")
    if not kr_id:
        return {"ok": False, "error": "This product has no source Knowledge Record — a video must inherit "
                                       "from verified knowledge (Knowledge-First). Manufacture it from a KR first."}
    kr = await _resolve_kr(kr_id)
    if not kr:
        return {"ok": False, "error": "Source Knowledge Record not found."}
    if not _is_verified(kr):
        return {"ok": False, "error": "The source Knowledge Record is not yet Verified. Approve it first — "
                                       "every video must inherit from verified knowledge (Knowledge-First)."}

    spec = cinema.FMT.get(format_id) or cinema.FMT[DEFAULT_FORMAT]
    try:
        media = await cinema._make_video(kr, spec)
    except Exception as e:
        logger.warning(f"video fulfillment render failed [product {product_id}]: {e}")
        return {"ok": False, "error": f"Video render failed: {str(e)[:160]}"}

    # cinema saves the MP4 into rendering_engine.ASSET_DIR; move a copy into the media vault root.
    fid = (media.get("url") or "").rstrip("/").split("/")[-1]
    src = os.path.join(re_engine.ASSET_DIR, fid)
    if not fid or not os.path.exists(src) or os.path.getsize(src) == 0:
        return {"ok": False, "error": "Rendered video file was not produced."}

    os.makedirs(mp.MEDIA_ROOT, exist_ok=True)
    qru_asset_id = f"QRU-VIDEO-{gen_id()[:8].upper()}"
    dest = os.path.join(mp.MEDIA_ROOT, f"{qru_asset_id}.mp4")
    shutil.copyfile(src, dest)
    size = os.path.getsize(dest)

    title = product.get("title") or media.get("title") or "QRU Educational Video"
    content = (product.get("content") or product.get("summary") or "")
    description = (content[:4000].strip() + "\n\n" + _TECHNIQUE +
                   "\n\n— Manufactured by QRU Factory™ (Quest for Real Understanding).").strip()
    tags = [t for t in [product.get("category"), product.get("product_type"), product.get("audience")]
            if t and isinstance(t, str)][:6] + ["QRU", "education"]

    doc = {
        "id": gen_id(), "qru_asset_id": qru_asset_id, "kind": "video", "provider": "qru_production",
        "title": title, "internal_storage_url": dest, "file_size_bytes": size,
        "duration_seconds": media.get("duration"), "width": None, "height": None,
        "has_narration": True, "technique": _TECHNIQUE, "scenes": media.get("scenes"),
        "captions": media.get("captions"),
        "production_status": "APPROVED", "approval_status": "Approved", "active_status": "Active",
        "distribution_ready": True, "is_draft_preview": False, "gold_master_certified": False,
        "product_id": product_id, "kr_id": kr.get("id"), "kr_code": kr.get("kr_code"),
        "publish_title": title[:100], "publish_description": description[:4900],
        "publish_tags": tags[:12],
        "license_type": "QRU Production (image-based motion + AI narration)",
        "imported_by": actor, "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.media_assets.insert_one(dict(doc))
    doc.pop("_id", None)
    logger.info(f"video fulfilled for product {product_id} -> {qru_asset_id} ({size} bytes)")
    return {"ok": True, "asset": doc, "path": dest, "reused": False}


# --------------------------------------------------------------- BOOK PROMO TRAILERS
_BOOK_AUTHORIZED = {"founder_authorization.authorized": True}


def _book_pseudo_kr(book):
    """Adapt a Founder-authored book_record into the KR-shape the cinema renderer expects.
    Books are the governed Knowledge-First exception, so no verified KR is required."""
    return {
        "id": book.get("id"), "kr_code": book.get("book_code"),
        "title": book.get("title"),
        "verified_truth": (book.get("description") or book.get("blurb") or book.get("subtitle") or "")[:1200],
        "why_it_matters": book.get("subtitle") or "",
        "everyday_analogy": "", "real_world_example": "",
        "memory_sentence": book.get("subtitle") or book.get("title"),
    }


async def existing_book_promo(book_id):
    return await db.media_assets.find_one(
        {"book_id": book_id, "kind": "video", "provider": "qru_production", "asset_role": "book_promo",
         "internal_storage_url": {"$exists": True}}, {"_id": 0})


async def ensure_book_promo(book_id, actor="Founder", force=False):
    """Render + register a short promo trailer for a published (Founder-authorized) book,
    queued for YouTube. Idempotent. Honest failure if the book isn't authorized/published."""
    book = await db.book_records.find_one({"id": book_id})
    if not book:
        return {"ok": False, "error": "Book not found."}
    if not ((book.get("founder_authorization") or {}).get("authorized")):
        return {"ok": False, "error": "This book is not Founder-authorized/published yet — "
                                       "only published titles get a public trailer."}
    if not force:
        existing = await existing_book_promo(book_id)
        path = _asset_on_disk(existing)
        if existing and path:
            return {"ok": True, "asset": existing, "path": path, "reused": True}

    spec = cinema.FMT["youtube_short"]
    try:
        media = await cinema._make_video(_book_pseudo_kr(book), spec)
    except Exception as e:
        logger.warning(f"book promo render failed [book {book_id}]: {e}")
        return {"ok": False, "error": f"Promo render failed: {str(e)[:160]}"}

    fid = (media.get("url") or "").rstrip("/").split("/")[-1]
    src = os.path.join(re_engine.ASSET_DIR, fid)
    if not fid or not os.path.exists(src) or os.path.getsize(src) == 0:
        return {"ok": False, "error": "Rendered promo file was not produced."}

    os.makedirs(mp.MEDIA_ROOT, exist_ok=True)
    qru_asset_id = f"QRU-PROMO-{gen_id()[:8].upper()}"
    dest = os.path.join(mp.MEDIA_ROOT, f"{qru_asset_id}.mp4")
    shutil.copyfile(src, dest)
    size = os.path.getsize(dest)

    title = f"{book.get('title')} — Official Trailer"
    blurb = (book.get("description") or book.get("subtitle") or "").strip()
    description = ((blurb[:3500] + "\n\n" if blurb else "") +
                   f"Available now at QRU Online. Read \"{book.get('title')}\""
                   + (f" by {book.get('author')}" if book.get("author") else "") + ".\n\n" +
                   _TECHNIQUE + "\n\n— QRU Online (Quest for Real Understanding).").strip()
    tags = [t for t in [book.get("genre"), book.get("audience"), "book trailer", "QRU Online"]
            if t and isinstance(t, str)][:6] + ["QRU", "books"]

    doc = {
        "id": gen_id(), "qru_asset_id": qru_asset_id, "kind": "video", "provider": "qru_production",
        "asset_role": "book_promo", "title": title, "internal_storage_url": dest, "file_size_bytes": size,
        "duration_seconds": media.get("duration"), "width": None, "height": None,
        "has_narration": True, "technique": _TECHNIQUE, "scenes": media.get("scenes"),
        "captions": media.get("captions"),
        "production_status": "APPROVED", "approval_status": "Approved", "active_status": "Active",
        "distribution_ready": True, "is_draft_preview": False, "gold_master_certified": False,
        "book_id": book_id, "book_code": book.get("book_code"),
        "publish_title": title[:100], "publish_description": description[:4900], "publish_tags": tags[:12],
        "pending_distribution": ["youtube"], "queued_at": now_iso(),
        "license_type": "QRU Production (image-based motion + AI narration)",
        "imported_by": actor, "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.media_assets.insert_one(dict(doc))
    doc.pop("_id", None)
    logger.info(f"book promo rendered for {book_id} -> {qru_asset_id} ({size} bytes)")
    return {"ok": True, "asset": doc, "path": dest, "reused": False}


async def generate_all_book_promos(actor="Founder", force=False):
    """Render promo trailers for every published (Founder-authorized) book. Idempotent per book."""
    books = await db.book_records.find(_BOOK_AUTHORIZED, {"_id": 0, "id": 1, "title": 1}).to_list(500)
    results = []
    for b in books:
        res = await ensure_book_promo(b["id"], actor=actor, force=force)
        results.append({"book_id": b["id"], "title": b.get("title"), "ok": res.get("ok"),
                        "reused": res.get("reused"), "asset_id": (res.get("asset") or {}).get("qru_asset_id"),
                        "error": res.get("error")})
    return {"total": len(books), "rendered": sum(1 for r in results if r["ok"]), "results": results}


async def distribution_queue():
    """Factory-owned videos awaiting distribution (e.g. YouTube) — visible + honest."""
    rows = await db.media_assets.find(
        {"provider": "qru_production", "kind": "video", "pending_distribution": {"$exists": True, "$ne": []}},
        {"_id": 0}).sort("queued_at", -1).to_list(500)
    return [{"qru_asset_id": r.get("qru_asset_id"), "title": r.get("title"), "asset_role": r.get("asset_role"),
             "book_id": r.get("book_id"), "duration_seconds": r.get("duration_seconds"),
             "pending_distribution": r.get("pending_distribution"), "queued_at": r.get("queued_at"),
             "file_available": bool(_asset_on_disk(r))} for r in rows]
