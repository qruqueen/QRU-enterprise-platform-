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


@router.get("/recipes")
async def recipes(user=Depends(get_current_user)):
    """Product Manufacturing Recipe™ catalog — the layout + primary format per product type."""
    import product_recipes as pr
    return {"recipes": pr.catalog()}


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
async def asset(fname: str, download: bool = False, name: str = None):
    # basic path-traversal guard
    if "/" in fname or ".." in fname:
        raise HTTPException(400, "Invalid asset name")
    path = os.path.join(re_engine.ASSET_DIR, fname)
    if not os.path.exists(path):
        raise HTTPException(404, "Asset not found")
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    media_map = {
        "pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "html": "text/html", "epub": "application/epub+zip", "mp4": "video/mp4", "mp3": "audio/mpeg",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    media = media_map.get(ext, "application/octet-stream")
    # MT-025 — force a real download (cross-origin `download` attr is ignored by browsers,
    # so we set Content-Disposition: attachment server-side). Reader/preview stays inline.
    if download:
        safe = "".join(ch for ch in (name or fname) if ch.isalnum() or ch in " ._-").strip() or fname
        if not safe.lower().endswith("." + ext):
            safe = f"{safe}.{ext}"
        return FileResponse(path, media_type=media, filename=safe,
                            headers={"Content-Disposition": f'attachment; filename="{safe}"'})
    return FileResponse(path, media_type=media)
