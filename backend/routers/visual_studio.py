"""QRU Visual Intelligence Studio™ (MO-009) + Media Intelligence Division™ (MO-010) config — API."""
from fastapi import APIRouter, Depends, HTTPException

from database import db
from auth import get_current_user
import visual_studio as vs
import media_intelligence as mi

router = APIRouter(prefix="/api/visual-studio", tags=["visual-studio"])


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return {"config": vs.CONFIG, "department_labels": vs.DEPARTMENT_LABELS}


@router.get("/analyze/{product_id}")
async def analyze(product_id: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": product_id})
    if not p:
        raise HTTPException(404, "Product not found")
    return vs.analyze_layout(p)


@router.get("/gold-review/{product_id}")
async def gold_review(product_id: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": product_id})
    if not p:
        raise HTTPException(404, "Product not found")
    return vs.gold_standard_review(p)


@router.get("/media/config")
async def media_config(user=Depends(get_current_user)):
    return {"config": mi.CONFIG, "capabilities": await mi.capabilities()}
