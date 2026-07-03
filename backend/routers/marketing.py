"""MT-033 — QRU Preview & Marketing Manufacturing System™ API."""
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import db
from auth import get_current_user
from models import clean
import marketing_engine as me

router = APIRouter(prefix="/api/marketing", tags=["marketing"])
BACKEND_PUBLIC = os.environ.get("REACT_APP_BACKEND_URL", "")


@router.post("/{pid}/build")
async def build(pid: str, user=Depends(get_current_user)):
    kit = await me.build_family(pid, user["name"], BACKEND_PUBLIC)
    if kit is None:
        raise HTTPException(404, "Product not found")
    return kit


@router.get("/{pid}")
async def get_kit(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid}, {"marketing_kit": 1, "preview_config": 1, "title": 1, "product_code": 1})
    if not p:
        raise HTTPException(404, "Product not found")
    p = clean(p)
    return {"product_id": pid, "title": p.get("title"), "product_code": p.get("product_code"),
            "marketing_kit": p.get("marketing_kit"),
            "preview_config": p.get("preview_config") or me.DEFAULT_PREVIEW_CONFIG,
            "ready": bool(p.get("marketing_kit"))}


class PreviewConfig(BaseModel):
    include_percentage: Optional[int] = None
    show_cover: Optional[bool] = None
    show_table_of_contents: Optional[bool] = None
    watermark_text: Optional[str] = None
    preview_message: Optional[str] = None
    cta_text: Optional[str] = None


@router.put("/{pid}/preview-config")
async def preview_config(pid: str, data: PreviewConfig, user=Depends(get_current_user)):
    cfg = await me.update_preview_config(pid, {k: v for k, v in data.model_dump().items() if v is not None})
    if cfg is None:
        raise HTTPException(404, "Product not found")
    return {"preview_config": cfg}
