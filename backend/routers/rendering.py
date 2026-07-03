"""QRU Product Rendering Engine™ API — render branded assets and serve them."""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
import asyncio

from database import db
from auth import get_current_user
from models import clean
import rendering_engine as re_engine

router = APIRouter(prefix="/api/rendering", tags=["rendering"])

BACKEND_PUBLIC = os.environ.get("REACT_APP_BACKEND_URL", "")


@router.post("/{pid}/render")
async def render(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    if not p.get("treasure_standard"):
        raise HTTPException(400, "Only Treasure Standard\u2122 certified products can be rendered.")
    asyncio.create_task(re_engine.render_product_job(pid, user["name"], BACKEND_PUBLIC))
    return {"message": "Rendering started", "pid": pid}


@router.post("/{pid}/apply-design-language")
async def apply_design_language(pid: str, user=Depends(get_current_user)):
    res = await re_engine.ensure_branded_assets(pid, user["name"])
    if not res:
        raise HTTPException(404, "Product not found")
    return res


@router.post("/design-language/backfill")
async def backfill_design_language(user=Depends(get_current_user)):
    """Apply the QRU Design Language™ to every published product missing branded assets."""
    q = {"status": "Published", "$or": [{"design_language_applied": {"$ne": True}}, {"cover_url": {"$in": [None, ""]}}]}
    ids = [p["id"] async for p in db.products.find(q)]
    applied = 0
    for pid in ids:
        try:
            if await re_engine.ensure_branded_assets(pid, user["name"]):
                applied += 1
        except Exception:
            pass
    return {"applied": applied, "total_candidates": len(ids)}


@router.get("/{pid}/visual-review")
async def visual_review(pid: str, user=Depends(get_current_user)):
    import design_language as dl
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    return dl.visual_review(clean(p))


@router.post("/{pid}/export-formats")
async def export_formats(pid: str, user=Depends(get_current_user)):
    urls = await re_engine.export_multi_format(pid, user["name"])
    if urls is None:
        raise HTTPException(404, "Product not found")
    return {"formats": urls, "count": len(urls)}


@router.get("/{pid}")
async def get_render(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    p = clean(p)
    return {
        "id": p["id"], "title": p["title"], "product_code": p.get("product_code"),
        "render_status": p.get("render_status", "not_started"),
        "rendered_assets": p.get("rendered_assets"),
        "design_recommendation": p.get("design_recommendation"),
    }


@router.get("/asset/{fname}")
async def asset(fname: str):
    # basic path-traversal guard
    if "/" in fname or ".." in fname:
        raise HTTPException(400, "Invalid asset name")
    path = os.path.join(re_engine.ASSET_DIR, fname)
    if not os.path.exists(path):
        raise HTTPException(404, "Asset not found")
    media = "application/pdf" if fname.endswith(".pdf") else "image/png"
    return FileResponse(path, media_type=media)
