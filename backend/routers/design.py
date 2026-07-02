"""QRU Design Intelligence™ API — Brand Library, Design Library, Master Asset Library,
Design Language, the Design Checklist™, and Creative Studio autonomy."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from database import db
from auth import get_current_user
from models import clean
import design_intelligence as di

router = APIRouter(prefix="/api/design", tags=["design"])


@router.get("/brand-library")
async def brand_library(user=Depends(get_current_user)):
    doc = await db.brand_library.find_one({"kind": "standards"})
    return clean(doc) if doc else {}


@router.get("/design-library")
async def design_library(product_type: Optional[str] = None, user=Depends(get_current_user)):
    q = {}
    if product_type:
        q["product_type"] = product_type
    refs = await db.design_library.find(q).sort("created_at", -1).to_list(200)
    return {"references": clean(refs)}


@router.get("/master-assets")
async def master_assets(q: Optional[str] = None, category: Optional[str] = None, user=Depends(get_current_user)):
    query = {}
    if category:
        query["category"] = category
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"keywords": {"$regex": q, "$options": "i"}},
            {"asset_id": {"$regex": q, "$options": "i"}},
        ]
    assets = await db.master_assets.find(query).sort("created_at", -1).to_list(300)
    return {"assets": clean(assets)}


@router.get("/design-language")
async def design_language(user=Depends(get_current_user)):
    principles = await db.design_language.find().sort("created_at", 1).to_list(300)
    return {"principles": clean(principles)}


@router.get("/stats")
async def stats(user=Depends(get_current_user)):
    return await di.library_stats()


@router.get("/recommend-templates")
async def recommend_templates(product_type: str, audience: str = "General public", user=Depends(get_current_user)):
    return di.recommend_templates(product_type, audience)


@router.post("/checklist/{pid}")
async def checklist(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    result = await di.run_design_checklist(p)
    return result
