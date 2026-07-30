"""Governed Product Description Manufacturing™ (STD-MFG-0001) + Governed Back Cover (STD-BLB-0001)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from auth import get_current_user, require_super_admin
import product_description as pd

router = APIRouter(prefix="/api/descriptions", tags=["descriptions"])


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return {"standard": pd.STANDARD_ID, "back_cover_standard": pd.BACK_COVER_STANDARD_ID,
            "modes": pd.MODES, "channels": [{"id": k, **v} for k, v in pd.CHANNELS.items()],
            "ai_styles": pd.AI_STYLES}


@router.get("/{engine}/{record_id}")
async def get_descriptions(engine: str, record_id: str, user=Depends(get_current_user)):
    meta = await pd.gather_meta(engine, record_id)
    if not meta:
        raise HTTPException(404, "Record not found.")
    return {"engine": engine, "id": meta["id"], "title": meta["title"],
            "descriptions": meta.get("descriptions", {}), "modes": pd.MODES,
            "channels": [{"id": k, **v} for k, v in pd.CHANNELS.items()]}


@router.get("/{engine}/{record_id}/preview")
async def preview_governed(engine: str, record_id: str, channel: str = "generic", user=Depends(get_current_user)):
    """Read-only Governed Manufacturing™ preview ($0) — does not save."""
    meta = await pd.gather_meta(engine, record_id)
    if not meta:
        raise HTTPException(404, "Record not found.")
    return pd.governed_description(meta, channel)


class ManufactureReq(BaseModel):
    mode: Optional[str] = "governed"      # governed | ai | founder
    channel: Optional[str] = "generic"
    text: Optional[str] = None            # required for founder mode
    styles: Optional[List[str]] = None    # ai mode
    save: Optional[bool] = True


@router.post("/{engine}/{record_id}/manufacture")
async def manufacture(engine: str, record_id: str, req: ManufactureReq = ManufactureReq(),
                      user=Depends(require_super_admin)):
    r = await pd.manufacture(engine, record_id, mode=(req.mode or "governed"),
                             channel=(req.channel or "generic"), text=req.text,
                             styles=req.styles, save=bool(req.save), actor=user.get("name", "Founder"))
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


class SaveVariantReq(BaseModel):
    channel: Optional[str] = "generic"
    text: str
    mode: Optional[str] = "ai"
    ai_used: Optional[bool] = True
    canonical: Optional[bool] = False


@router.post("/{engine}/{record_id}/save")
async def save_variant(engine: str, record_id: str, req: SaveVariantReq,
                       user=Depends(require_super_admin)):
    """Persist a chosen variant (e.g. a selected AI Enhancement™ variant) as the record's description."""
    if not (req.text or "").strip():
        raise HTTPException(400, "Text is required.")
    entry = await pd.save_description(engine, record_id, req.channel or "generic", req.text,
                                      mode=req.mode or "ai", ai_used=bool(req.ai_used),
                                      canonical=bool(req.canonical), actor=user.get("name", "Founder"))
    return {"ok": True, "saved": entry}
