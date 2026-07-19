"""QRU Video Fulfillment™ — turn a product's/book's video "contract" into a real, publishable MP4.

Honest by design (Treasure Standard™): the video is IMAGE-BASED MOTION (Ken Burns pans/zooms
over AI scene art) + real AI narration — NOT frame-by-frame cel animation. Rendered MP4s are
registered as Factory-owned vault assets (db.media_assets, provider=qru_production) so the
YouTube Publisher™ and the Distribution Framework™ can publish them directly.

Caching (Founder policy, 2026-06): a completed MP4 is REUSED unless its underlying source
(script/content for products, description for book trailers) changes, or a re-render is explicitly
requested (force=True). Rendering happens on PUBLISH or explicit request — never automatically on
every manufacture.
"""
import os
import shutil
import hashlib
import logging

from database import db
from models import gen_id, now_iso
import cinema_studio as cinema
import rendering_engine as re_engine
import media_production as mp
import storage
from media_division import _resolve_kr, _is_verified

logger = logging.getLogger("qru.video_fulfillment")

DEFAULT_FORMAT = "promo_video"
_TECHNIQUE = "Image-based motion (Ken Burns) + AI narration — NOT frame-by-frame animation."

# Product types whose OWN script/content is the narration source (Knowledge-First exception:
# the script is the governed work product derived from a verified KR upstream).
_SCRIPT_TYPES = {"video script", "short video", "youtube video script", "podcast script"}


def _sig(*parts):
    h = hashlib.sha256()
    for p in parts:
        h.update((str(p) or "").encode("utf-8", "ignore"))
    return h.hexdigest()[:32]


def _asset_on_disk(doc):
    path = doc.get("internal_storage_url") if doc else None
    if path and os.path.exists(os.path.abspath(path)) and os.path.getsize(os.path.abspath(path)) > 0:
        return os.path.abspath(path)
    return None


def _available(doc):
    """Available if in durable object storage (survives redeploys) OR present on local disk."""
    if not doc:
        return False
    return bool(doc.get("storage_path")) or bool(_asset_on_disk(doc))


async def materialize(doc):
    """Return a LOCAL file path for a stored video, downloading from object storage if needed."""
    local = _asset_on_disk(doc)
    if local:
        return local
    sp = doc.get("storage_path") if doc else None
    if not sp:
        return None
    os.makedirs(mp.MEDIA_ROOT, exist_ok=True)
    dest = os.path.join(mp.MEDIA_ROOT, os.path.basename(sp))
    data = await storage.aget_object(sp)
    with open(dest, "wb") as f:
        f.write(data)
    return dest


async def _persist(dest, qru_asset_id):
    """Upload a rendered MP4 to durable object storage; return its storage_path."""
    storage_path = f"{storage.APP_NAME}/videos/{qru_asset_id}.mp4"
    with open(dest, "rb") as f:
        await storage.aput_object(storage_path, f.read(), "video/mp4")
    return storage_path


async def existing_video_asset(product_id):
    return await db.media_assets.find_one(
        {"product_id": product_id, "kind": "video", "provider": "qru_production",
         "internal_storage_url": {"$exists": True}}, {"_id": 0})


def _product_script(product):
    return (product.get("content") or product.get("summary") or product.get("script") or "").strip()


def _is_script_product(product):
    return (product.get("product_type") or "").strip().lower() in _SCRIPT_TYPES


async def _render_mp4(context_kr, format_id):
    """Render an MP4 via the shared cinema pipeline and return (dest_path, media) or (None, err)."""
    spec = cinema.FMT.get(format_id) or cinema.FMT[DEFAULT_FORMAT]
    try:
        media = await cinema._make_video(context_kr, spec)
    except Exception as e:
        return None, f"Video render failed: {str(e)[:160]}"
    fid = (media.get("url") or "").rstrip("/").split("/")[-1]
    src = os.path.join(re_engine.ASSET_DIR, fid)
    if not fid or not os.path.exists(src) or os.path.getsize(src) == 0:
        return None, "Rendered video file was not produced."
    return src, media


async def ensure_product_video(product_id, actor="Founder", format_id=DEFAULT_FORMAT, force=False):
    """Idempotently produce + register a real MP4 for a product. Reuses the cached MP4 unless the
    product's script/content changed or force=True. Returns {"ok",..} or {"ok":False,"error"}."""
    product = await db.products.find_one({"id": product_id})
    if not product:
        return {"ok": False, "error": "Product not found."}

    script = _product_script(product)
    is_script = _is_script_product(product)

    # Resolve the narration/scene source + a signature for cache invalidation.
    kr = None
    if is_script and script:
        # The script itself is the source (already governed upstream).
        source_kr = {"id": product.get("id"), "kr_code": product.get("product_code"),
                     "title": product.get("title"), "verified_truth": script[:2000],
                     "why_it_matters": product.get("subtitle") or "", "everyday_analogy": "",
                     "real_world_example": "", "memory_sentence": product.get("title")}
        signature = _sig(product.get("title"), script)
    else:
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
        source_kr = kr
        signature = _sig(kr.get("id"), kr.get("kr_code"), kr.get("version"))

    # Cache: reuse unless the source changed or a re-render is forced.
    existing = await existing_video_asset(product_id)
    if existing and _available(existing) and not force and existing.get("source_signature") == signature:
        return {"ok": True, "asset": existing, "path": await materialize(existing), "reused": True}

    src, media = await _render_mp4(source_kr, format_id)
    if src is None:
        logger.warning(f"video fulfillment render failed [product {product_id}]: {media}")
        return {"ok": False, "error": media}

    os.makedirs(mp.MEDIA_ROOT, exist_ok=True)
    qru_asset_id = f"QRU-VIDEO-{gen_id()[:8].upper()}"
    dest = os.path.join(mp.MEDIA_ROOT, f"{qru_asset_id}.mp4")
    shutil.copyfile(src, dest)
    size = os.path.getsize(dest)
    storage_path = await _persist(dest, qru_asset_id)

    title = product.get("title") or media.get("title") or "QRU Educational Video"
    body = (script or product.get("content") or product.get("summary") or "")
    description = (body[:4000].strip() + "\n\n" + _TECHNIQUE +
                   "\n\n— Manufactured by QRU Factory™ (Quest for Real Understanding).").strip()
    tags = [t for t in [product.get("category"), product.get("product_type"), product.get("audience")]
            if t and isinstance(t, str)][:6] + ["QRU", "education"]

    doc = {
        "id": gen_id(), "qru_asset_id": qru_asset_id, "kind": "video", "provider": "qru_production",
        "title": title, "internal_storage_url": dest, "storage_path": storage_path, "file_size_bytes": size,
        "duration_seconds": media.get("duration"), "width": None, "height": None,
        "has_narration": True, "technique": _TECHNIQUE, "scenes": media.get("scenes"),
        "captions": media.get("captions"), "source_signature": signature,
        "rendered_from": "script" if (is_script and script) else "knowledge_record",
        "production_status": "APPROVED", "approval_status": "Approved", "active_status": "Active",
        "distribution_ready": True, "is_draft_preview": False, "gold_master_certified": False,
        "product_id": product_id, "kr_id": (kr or {}).get("id"), "kr_code": (kr or {}).get("kr_code"),
        "publish_title": title[:100], "publish_description": description[:4900], "publish_tags": tags[:12],
        "license_type": "QRU Production (image-based motion + AI narration)",
        "imported_by": actor, "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    # Replace-not-append: one current video per product (removes the stale cached asset + file).
    if existing:
        ep = _asset_on_disk(existing)
        try:
            if ep and os.path.exists(ep):
                os.remove(ep)
        except Exception:
            pass
        await db.media_assets.delete_many({"product_id": product_id, "kind": "video", "provider": "qru_production"})
    await db.media_assets.insert_one(dict(doc))
    doc.pop("_id", None)
    logger.info(f"video fulfilled for product {product_id} -> {qru_asset_id} ({size} bytes, from {doc['rendered_from']})")
    return {"ok": True, "asset": doc, "path": dest, "reused": False}


# --------------------------------------------------------------- BOOK PROMO TRAILERS
_BOOK_AUTHORIZED = {"founder_authorization.authorized": True}


def _book_pseudo_kr(book):
    """Adapt a Founder-authored book_record into the KR-shape the cinema renderer expects."""
    return {
        "id": book.get("id"), "kr_code": book.get("book_code"), "title": book.get("title"),
        "verified_truth": (book.get("description") or book.get("blurb") or book.get("subtitle") or "")[:1200],
        "why_it_matters": book.get("subtitle") or "", "everyday_analogy": "",
        "real_world_example": "", "memory_sentence": book.get("subtitle") or book.get("title"),
    }


def _book_signature(book):
    return _sig(book.get("title"), book.get("subtitle"), book.get("description") or book.get("blurb"))


async def existing_book_promo(book_id):
    return await db.media_assets.find_one(
        {"book_id": book_id, "kind": "video", "provider": "qru_production", "asset_role": "book_promo",
         "internal_storage_url": {"$exists": True}}, {"_id": 0})


async def ensure_book_promo(book_id, actor="Founder", force=False):
    """Render + register a short promo trailer for a published book, queued for YouTube. Cached
    (reused unless the title/subtitle/description changes or force=True)."""
    book = await db.book_records.find_one({"id": book_id})
    if not book:
        return {"ok": False, "error": "Book not found."}
    if not ((book.get("founder_authorization") or {}).get("authorized")):
        return {"ok": False, "error": "This book is not Founder-authorized/published yet — "
                                       "only published titles get a public trailer."}
    signature = _book_signature(book)
    existing = await existing_book_promo(book_id)
    if existing and _available(existing) and not force and existing.get("source_signature") == signature:
        return {"ok": True, "asset": existing, "path": await materialize(existing), "reused": True}

    src, media = await _render_mp4(_book_pseudo_kr(book), "youtube_short")
    if src is None:
        logger.warning(f"book promo render failed [book {book_id}]: {media}")
        return {"ok": False, "error": media}

    os.makedirs(mp.MEDIA_ROOT, exist_ok=True)
    qru_asset_id = f"QRU-PROMO-{gen_id()[:8].upper()}"
    dest = os.path.join(mp.MEDIA_ROOT, f"{qru_asset_id}.mp4")
    shutil.copyfile(src, dest)
    size = os.path.getsize(dest)
    storage_path = await _persist(dest, qru_asset_id)

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
        "asset_role": "book_promo", "title": title, "internal_storage_url": dest, "storage_path": storage_path,
        "file_size_bytes": size,
        "duration_seconds": media.get("duration"), "width": None, "height": None,
        "has_narration": True, "technique": _TECHNIQUE, "scenes": media.get("scenes"),
        "captions": media.get("captions"), "source_signature": signature,
        "production_status": "APPROVED", "approval_status": "Approved", "active_status": "Active",
        "distribution_ready": True, "is_draft_preview": False, "gold_master_certified": False,
        "book_id": book_id, "book_code": book.get("book_code"),
        "publish_title": title[:100], "publish_description": description[:4900], "publish_tags": tags[:12],
        "pending_distribution": ["youtube"], "queued_at": now_iso(),
        "license_type": "QRU Production (image-based motion + AI narration)",
        "imported_by": actor, "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    if existing:
        ep = _asset_on_disk(existing)
        try:
            if ep and os.path.exists(ep):
                os.remove(ep)
        except Exception:
            pass
        await db.media_assets.delete_many({"book_id": book_id, "kind": "video", "provider": "qru_production",
                                           "asset_role": "book_promo"})
    await db.media_assets.insert_one(dict(doc))
    doc.pop("_id", None)
    logger.info(f"book promo rendered for {book_id} -> {qru_asset_id} ({size} bytes)")
    return {"ok": True, "asset": doc, "path": dest, "reused": False}


async def generate_all_book_promos(actor="Founder", force=False):
    books = await db.book_records.find(_BOOK_AUTHORIZED, {"_id": 0, "id": 1, "title": 1}).to_list(500)
    results = []
    for b in books:
        res = await ensure_book_promo(b["id"], actor=actor, force=force)
        results.append({"book_id": b["id"], "title": b.get("title"), "ok": res.get("ok"),
                        "reused": res.get("reused"), "asset_id": (res.get("asset") or {}).get("qru_asset_id"),
                        "error": res.get("error")})
    return {"total": len(books), "rendered": sum(1 for r in results if r["ok"]), "results": results}


async def _book_needs_render(book_id):
    book = await db.book_records.find_one({"id": book_id}, {"_id": 0})
    if not book:
        return False
    existing = await existing_book_promo(book_id)
    return not (existing and _available(existing) and existing.get("source_signature") == _book_signature(book))


async def _product_needs_render(product_id):
    p = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not p:
        return False
    script = _product_script(p)
    if _is_script_product(p) and script:
        sig = _sig(p.get("title"), script)
    else:
        kr_id = p.get("knowledge_record_id") or (p.get("inherits_from") or {}).get("kr_id")
        if not kr_id:
            return False
        sig = None  # KR sig computed on render; treat as needs-render unless matching sig present
    existing = await existing_video_asset(product_id)
    if not (existing and _available(existing)):
        return True
    return sig is None or existing.get("source_signature") != sig


async def backfill_all(actor="Founder", force=False, limit=3):
    """Incremental production backfill — renders up to `limit` missing/stale videos per call and
    reports remaining, so the caller can loop without hitting request timeouts. Idempotent + cached."""
    # Candidate lists
    books = await db.book_records.find(_BOOK_AUTHORIZED, {"_id": 0, "id": 1, "title": 1}).to_list(500)
    prods = await db.products.find(
        {"product_type": {"$in": ["Video Script", "Short Video", "YouTube Video Script"]}},
        {"_id": 0, "id": 1, "title": 1, "product_type": 1}).to_list(500)

    # Pending = needs render (unless force, then everything)
    pending = []
    for b in books:
        if force or await _book_needs_render(b["id"]):
            pending.append(("book", b))
    for p in prods:
        if force or await _product_needs_render(p["id"]):
            pending.append(("product", p))

    total_book = len(books)
    total_prod = len(prods)
    rendered = []
    for kind, item in pending[:limit]:
        if kind == "book":
            res = await ensure_book_promo(item["id"], actor=actor, force=force)
        else:
            res = await ensure_product_video(item["id"], actor=actor, force=force)
        rendered.append({"kind": kind, "id": item["id"], "title": item.get("title"),
                         "ok": res.get("ok"), "asset_id": (res.get("asset") or {}).get("qru_asset_id"),
                         "error": res.get("error")})
    remaining = max(0, len(pending) - limit)
    # Totals present after this pass
    have_books = 0
    for b in books:
        if not await _book_needs_render(b["id"]):
            have_books += 1
    have_prods = 0
    for p in prods:
        if not await _product_needs_render(p["id"]):
            have_prods += 1
    return {
        "rendered_this_call": rendered,
        "remaining": remaining,
        "done": remaining == 0,
        "summary": {
            "book_trailers_ok": have_books, "book_trailers_total": total_book,
            "script_videos_ok": have_prods, "script_videos_total": total_prod,
        },
    }


async def distribution_queue():
    rows = await db.media_assets.find(
        {"provider": "qru_production", "kind": "video", "pending_distribution": {"$exists": True, "$ne": []}},
        {"_id": 0}).sort("queued_at", -1).to_list(500)
    return [{"qru_asset_id": r.get("qru_asset_id"), "title": r.get("title"), "asset_role": r.get("asset_role"),
             "book_id": r.get("book_id"), "duration_seconds": r.get("duration_seconds"),
             "pending_distribution": r.get("pending_distribution"), "queued_at": r.get("queued_at"),
             "file_available": _available(r)} for r in rows]
