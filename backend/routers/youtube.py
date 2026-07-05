"""QRU YouTube Publisher™ (MO-006) — API surface. Founder Upload Mode: chunked MP4 upload →
real YouTube publish via the Data API. Treasure Standard™: no fake states, explicit reasons.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List

from database import db
from auth import get_current_user, require_super_admin
import youtube_publisher as yt
import oauth_framework as oauth

router = APIRouter(prefix="/api/youtube", tags=["youtube"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "rendered_assets", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB safety cap


def _safe_ext(filename, allowed):
    ext = os.path.splitext(filename or "")[1].lower()
    return ext if ext in allowed else allowed[0]


@router.get("/status")
async def status(user=Depends(get_current_user)):
    state = await db.connectors.find_one({"platform_id": "youtube"}) or {}
    granted = state.get("granted_scopes") or ""
    connected = bool(state.get("access_token_enc")) and state.get("connected")
    return {
        "connected": bool(connected),
        "account": state.get("account"),
        "can_upload": bool(connected) and ("youtube.upload" in granted or not granted),
        "scopes": granted,
        "reason": None if connected else "Connect your YouTube channel in Publishing Connectors™ (Developer Setup → Connect).",
    }


@router.get("/playlists")
async def playlists(user=Depends(get_current_user)):
    try:
        return {"playlists": await yt.list_playlists()}
    except yt.YouTubeError as e:
        raise HTTPException(400, str(e))


@router.get("/publications")
async def publications(user=Depends(get_current_user)):
    return {"publications": await yt.list_publications()}


class InitInput(BaseModel):
    filename: str
    kind: str = "video"  # "video" | "thumbnail"


@router.post("/upload/init")
async def upload_init(data: InitInput, user=Depends(require_super_admin)):
    allowed = [".mp4", ".mov", ".webm"] if data.kind == "video" else [".jpg", ".jpeg", ".png"]
    ext = _safe_ext(data.filename, allowed)
    upload_id = f"{data.kind}_{os.urandom(8).hex()}{ext}"
    open(os.path.join(UPLOAD_DIR, upload_id), "wb").close()
    return {"upload_id": upload_id}


@router.post("/upload/chunk")
async def upload_chunk(request: Request, upload_id: str, user=Depends(require_super_admin)):
    path = os.path.join(UPLOAD_DIR, os.path.basename(upload_id))
    if not os.path.exists(path):
        raise HTTPException(404, "Upload session not found. Start again.")
    body = await request.body()
    if os.path.getsize(path) + len(body) > MAX_BYTES:
        raise HTTPException(413, "File exceeds the 2 GB limit.")
    with open(path, "ab") as f:
        f.write(body)
    return {"received": len(body), "total": os.path.getsize(path)}


class PublishInput(BaseModel):
    video_upload_id: str
    thumbnail_upload_id: Optional[str] = None
    product_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    privacy: str = "private"
    playlist_id: Optional[str] = None


async def _metadata_from_product(pid):
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    content = (p.get("content") or p.get("summary") or "")
    tags = []
    for k in ("category", "product_type", "family", "audience"):
        v = p.get(k)
        if v and isinstance(v, str):
            tags.append(v)
    return {
        "title": p.get("title") or p.get("product_code") or "QRU Educational Video",
        "description": (content[:4500] + "\n\n— Manufactured by QRU Factory™ (Quest for Real Understanding).").strip(),
        "tags": tags,
        "cover": p.get("cover_url"),
    }


@router.post("/publish")
async def publish(data: PublishInput, user=Depends(require_super_admin)):
    video_path = os.path.join(UPLOAD_DIR, os.path.basename(data.video_upload_id))
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        raise HTTPException(400, "No uploaded video found. Upload the MP4 first.")

    title, description, tags = data.title, data.description, data.tags
    if data.product_id and (not title or not description):
        meta = await _metadata_from_product(data.product_id)
        if meta:
            title = title or meta["title"]
            description = description or meta["description"]
            tags = tags or meta["tags"]
    if not title:
        raise HTTPException(400, "A title is required (or link a product to auto-fill it).")

    thumb_path = None
    if data.thumbnail_upload_id:
        tp = os.path.join(UPLOAD_DIR, os.path.basename(data.thumbnail_upload_id))
        if os.path.exists(tp) and os.path.getsize(tp) > 0:
            thumb_path = tp

    try:
        pub = await yt.publish_video(
            file_path=video_path, title=title, description=description or "", tags=tags or [],
            privacy=data.privacy, thumbnail_path=thumb_path, playlist_id=data.playlist_id,
            product_id=data.product_id, actor=user["name"],
        )
    except yt.YouTubeError as e:
        raise HTTPException(400, str(e))
    finally:
        # Clean up temp files regardless of outcome.
        for pth in (video_path, thumb_path):
            try:
                if pth and os.path.exists(pth):
                    os.remove(pth)
            except Exception:
                pass
    return pub
