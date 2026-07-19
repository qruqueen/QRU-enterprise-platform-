"""QRU Video Fulfillment™ router — render + register a real, publishable MP4 for a product."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user, require_super_admin
import video_fulfillment as vf

router = APIRouter(prefix="/api/video", tags=["video-fulfillment"])


class RenderInput(BaseModel):
    format_id: Optional[str] = None
    force: Optional[bool] = False
    limit: Optional[int] = 3


def _public(asset):
    if not asset:
        return None
    return {
        "qru_asset_id": asset.get("qru_asset_id"), "title": asset.get("title"),
        "duration_seconds": asset.get("duration_seconds"), "scenes": asset.get("scenes"),
        "technique": asset.get("technique"), "distribution_ready": bool(asset.get("distribution_ready")),
        "file_size_bytes": asset.get("file_size_bytes"), "product_id": asset.get("product_id"),
        "book_id": asset.get("book_id"), "asset_role": asset.get("asset_role"),
        "pending_distribution": asset.get("pending_distribution"),
        "kr_code": asset.get("kr_code"), "created_at": asset.get("created_at"),
    }


@router.get("/products/{product_id}")
async def product_video(product_id: str, user=Depends(get_current_user)):
    asset = await vf.existing_video_asset(product_id)
    available = bool(vf._asset_on_disk(asset))
    return {"has_video": bool(asset) and available, "asset": _public(asset)}


@router.post("/products/{product_id}/render")
async def render_product_video(product_id: str, data: RenderInput, user=Depends(require_super_admin)):
    res = await vf.ensure_product_video(
        product_id, actor=user.get("name", "Founder"),
        format_id=data.format_id or vf.DEFAULT_FORMAT, force=bool(data.force))
    if not res.get("ok"):
        raise HTTPException(400, res.get("error", "Video render failed."))
    return {"ok": True, "reused": res.get("reused", False), "asset": _public(res["asset"])}


@router.get("/books/{book_id}/promo")
async def book_promo_status(book_id: str, user=Depends(get_current_user)):
    asset = await vf.existing_book_promo(book_id)
    available = bool(vf._asset_on_disk(asset))
    return {"has_promo": bool(asset) and available, "asset": _public(asset)}


@router.post("/books/{book_id}/promo")
async def render_book_promo(book_id: str, data: RenderInput, user=Depends(require_super_admin)):
    res = await vf.ensure_book_promo(book_id, actor=user.get("name", "Founder"), force=bool(data.force))
    if not res.get("ok"):
        raise HTTPException(400, res.get("error", "Promo render failed."))
    return {"ok": True, "reused": res.get("reused", False), "asset": _public(res["asset"])}


@router.post("/books/promos/generate-all")
async def generate_all_promos(data: RenderInput, user=Depends(require_super_admin)):
    return await vf.generate_all_book_promos(actor=user.get("name", "Founder"), force=bool(data.force))


@router.post("/backfill")
async def backfill(data: RenderInput, user=Depends(require_super_admin)):
    """Start a NON-BLOCKING background render of all missing/stale videos. Returns immediately;
    poll GET /video/backfill/status for progress. Avoids proxy/Cloudflare timeouts."""
    return await vf.start_backfill(actor=user.get("name", "Founder"), force=bool(data.force))


@router.get("/backfill/status")
async def backfill_status(user=Depends(get_current_user)):
    return await vf.backfill_status()


@router.get("/queue")
async def video_queue(user=Depends(get_current_user)):
    q = await vf.distribution_queue()
    return {"queued": q, "count": len(q)}
