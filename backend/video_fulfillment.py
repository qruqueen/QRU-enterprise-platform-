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
