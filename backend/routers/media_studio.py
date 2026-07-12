"""QRU Media Manufacturing™ API — Storyboard Master™ inside the Product Manufacturing Engine™."""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

from auth import get_current_user
from database import db
import storyboard_master as sm

router = APIRouter(prefix="/api/media-studio", tags=["media-studio"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return sm.overview()


@router.get("/storyboards")
async def list_storyboards(user=Depends(get_current_user)):
    rows = [r async for r in db.storyboard_masters.find({}, {"_id": 0}).sort("created_at", -1).limit(40)]
    return {"storyboards": rows}


@router.get("/products")
async def list_media_products(user=Depends(get_current_user)):
    rows = [r async for r in db.media_products.find({}, {"_id": 0}).sort("created_at", -1).limit(80)]
    return {"products": rows}


class MediaOrder(BaseModel):
    kr_id: str
    formats: List[str]


@router.post("/order")
async def media_order(data: MediaOrder, user=Depends(get_current_user)):
    if not data.formats:
        raise HTTPException(400, "Select at least one media format.")
    res = await sm.run_media_order(data.kr_id, data.formats, user.get("name", "Founder"))
    if res is None:
        raise HTTPException(404, "Knowledge Record not found.")
    return res


@router.post("/pilot")
async def media_pilot(kr_id: str, user=Depends(get_current_user)):
    """Pilot: one KR → one Storyboard Master → five media outputs."""
    formats = ["youtube_video", "promo_short", "audio_lesson", "teacher_presentation", "student_presentation"]
    res = await sm.run_media_order(kr_id, formats, user.get("name", "Founder"))
    if res is None:
        raise HTTPException(404, "Knowledge Record not found.")
    return res


@router.post("/media-kit")
async def media_kit(kr_id: str, user=Depends(get_current_user)):
    """One approved KR → the complete governed media kit (all formats + thumbnails), one approval."""
    res = await sm.run_full_media_kit(kr_id, user.get("name", "Founder"))
    if res is None:
        raise HTTPException(404, "Knowledge Record not found.")
    return res


@router.post("/product/{product_id}/render-audio")
async def render_audio(product_id: str, model: str = "tts-1", user=Depends(get_current_user)):
    res = await sm.render_audio_mp3(product_id, model, user.get("name", "Founder"))
    if res is None:
        raise HTTPException(404, "Media product not found.")
    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.post("/product/{product_id}/render-video")
async def render_video(product_id: str, user=Depends(get_current_user)):
    res = await sm.trigger_video_render(product_id, user.get("name", "Founder"))
    if res is None:
        raise HTTPException(404, "Media product not found.")
    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.get("/product/{product_id}")
async def get_product(product_id: str, user=Depends(get_current_user)):
    doc = await db.media_products.find_one({"id": product_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Media product not found.")
    return doc


@router.get("/file/{sid}/{fmt}/{ext}")
async def media_file(sid: str, fmt: str, ext: str):
    path = sm.media_file_path(sid, fmt, ext)
    if not os.path.exists(path):
        raise HTTPException(404, "Media file not found.")
    media = {"pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
             "png": "image/png", "txt": "text/plain", "mp3": "audio/mpeg", "mp4": "video/mp4"}.get(ext, "application/octet-stream")
    return FileResponse(str(path), media_type=media, filename=f"{fmt}.{ext}")
