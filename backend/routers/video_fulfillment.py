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


def _public(asset):
    if not asset:
        return None
    return {
        "qru_asset_id": asset.get("qru_asset_id"), "title": asset.get("title"),
        "duration_seconds": asset.get("duration_seconds"), "scenes": asset.get("scenes"),
        "technique": asset.get("technique"), "distribution_ready": bool(asset.get("distribution_ready")),
        "file_size_bytes": asset.get("file_size_bytes"), "product_id": asset.get("product_id"),
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
