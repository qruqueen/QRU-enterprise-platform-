"""QRU YouTube Publisher™ (MO-006) — API surface. Founder Upload Mode: chunked MP4 upload →
real YouTube publish via the Data API. Treasure Standard™: no fake states, explicit reasons.
"""
import os
import re
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List

from database import db
from models import now_iso
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


@router.get("/distribution-records")
async def distribution_records(user=Depends(get_current_user)):
    rows = await db.distribution_acceptance_records.find({}, {"_id": 0}).sort("published_at", -1).to_list(200)
    return {"records": rows, "count": len(rows)}


async def _write_distribution_record(factory_doc, pub, title, description, tags, thumb_set, actor):
    """Formal Distribution Acceptance Record (Founder directive) — full provenance from Gold Master to platform."""
    record = await db.production_acceptance_records.find_one({"final_asset_id": factory_doc.get("qru_asset_id")}) or {}
    doc = {
        "id": f"QRU-DIST-{os.urandom(4).hex().upper()}",
        "record_type": "distribution_acceptance_record",
        "platform": "youtube", "connected_channel": (await db.connectors.find_one({"platform_id": "youtube"}) or {}).get("account"),
        "distribution_edition_id": None,  # native YouTube edition uses the Vault master directly
        "vault_asset_id": factory_doc.get("qru_asset_id"),
        "gold_master_certified": bool(factory_doc.get("gold_master_certified")),
        "gold_master_version": factory_doc.get("production_status"),
        "project_id": record.get("project_id"), "job_id": record.get("job_id"),
        "platform_video_id": pub.get("video_id"), "publication_url": pub.get("url"),
        "studio_url": pub.get("studio_url"), "published_at": pub.get("published_at"),
        "title_used": title, "description_used": description, "tags_used": tags or [],
        "thumbnail_status": "set" if thumb_set else "auto (channel custom-thumbnail not verified)",
        "publishing_response": {k: pub.get(k) for k in ("video_id", "privacy", "thumbnail_set", "treasure_standard")},
        "qa_results": {"technical": factory_doc.get("technical_qa_score"), "brand_content": factory_doc.get("brand_content_qa_score")},
        "checksum": factory_doc.get("checksum"),
        "source_licensing": [{"provider": s.get("provider"), "creator_name": s.get("creator_name"),
                              "license_type": s.get("license_type"), "checksum": s.get("checksum")}
                             for s in record.get("scene_list", [])],
        "responsible_approver": actor, "status": "Published", "error_history": [], "retry_history": [],
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.distribution_acceptance_records.insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


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
    video_upload_id: Optional[str] = None
    thumbnail_upload_id: Optional[str] = None
    factory_asset_id: Optional[str] = None  # publish directly from a Factory-owned vault MP4 (no re-upload)
    product_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    privacy: str = "private"
    playlist_id: Optional[str] = None
    made_for_kids: Optional[bool] = None


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


async def _resolve_factory_asset(asset_id):
    """Resolve a Factory-owned vault video + its on-disk MP4 (validated inside the media root)."""
    import media_production as mp
    doc = await db.media_assets.find_one({"$or": [{"qru_asset_id": asset_id}, {"id": asset_id}]})
    if not doc or not doc.get("internal_storage_url"):
        return None, None
    path = os.path.abspath(doc["internal_storage_url"])
    if not path.startswith(os.path.abspath(mp.MEDIA_ROOT)) or not os.path.exists(path):
        return doc, None
    return doc, path


async def _metadata_from_factory_asset(doc):
    """Auto-fill title/description/tags from a Factory asset + its Production Acceptance Record."""
    # Little Legacy pilots carry an approved Publishing Package™ — prefer it (one-click publish, no re-entry).
    if doc.get("publish_title"):
        return {"title": doc["publish_title"], "description": doc.get("publish_description") or "",
                "tags": doc.get("publish_tags") or []}
    pkg = doc.get("publishing_package") or {}
    if pkg.get("youtube_title"):
        return {"title": pkg["youtube_title"], "description": pkg.get("seo_description") or "",
                "tags": pkg.get("keywords") or []}
    record = await db.production_acceptance_records.find_one({"final_asset_id": doc.get("qru_asset_id")}) or {}
    topic = record.get("topic") or ""
    title = doc.get("title") or record.get("product_title") or "QRU Educational Video"
    scenes = record.get("scene_list") or []
    creators = sorted({s.get("creator_name") for s in scenes if s.get("creator_name")})
    lines = [f"{record.get('product_title') or title}"]
    if topic:
        lines.append(f"\nTopic: {topic}")
    if scenes:
        lines.append(f"A {len(scenes)}-scene QRU Flagship Showcase™ manufactured from a governed Knowledge Record.")
    if creators:
        lines.append("\nLicensed footage by: " + ", ".join(creators) + " (Pixabay/Pexels Content License).")
    lines.append("\nCaptions are embedded in the file. Manufactured by QRU Factory™ (Quest for Real Understanding).")
    tag_src = re.findall(r"[A-Za-z]{3,}", f"{topic} {title}".lower())
    tags = []
    for t in tag_src:
        if t not in tags and t not in ("the", "and", "for", "with"):
            tags.append(t)
    tags = (tags[:8] + ["QRU", "education"])[:12]
    return {"title": title[:100], "description": "\n".join(lines)[:4900], "tags": tags}


def _extract_thumbnail(video_path):
    """Extract a real first-frame JPG thumbnail from the Factory MP4 (honest — no stock/placeholder)."""
    import subprocess
    import media_production as mp
    out = video_path + ".thumb.jpg"
    try:
        subprocess.run([mp.FFMPEG, "-y", "-ss", "1", "-i", video_path, "-vframes", "1", "-q:v", "3", out],
                       capture_output=True, timeout=60)
        return out if os.path.exists(out) and os.path.getsize(out) > 0 else None
    except Exception:
        return None


@router.get("/factory-assets")
async def factory_assets(user=Depends(get_current_user)):
    """Videos the Factory already owns (manufactured in-house) — ready to publish without re-upload."""
    rows = await db.media_assets.find(
        {"kind": "video", "provider": "qru_production", "internal_storage_url": {"$exists": True}},
        {"_id": 0}).sort("created_at", -1).to_list(100)
    out = []
    for a in rows:
        path = a.get("internal_storage_url")
        out.append({
            "qru_asset_id": a.get("qru_asset_id"), "title": a.get("title"),
            "duration_seconds": a.get("duration_seconds"), "width": a.get("width"), "height": a.get("height"),
            "production_status": a.get("production_status"), "distribution_ready": bool(a.get("distribution_ready")),
            "gold_master_certified": bool(a.get("gold_master_certified")),
            "is_draft_preview": bool(a.get("is_draft_preview")),
            "created_at": a.get("created_at"),
            "file_available": bool(path and os.path.exists(os.path.abspath(path))),
        })
    return {"assets": out, "count": len(out)}


@router.post("/publish")
async def publish(data: PublishInput, user=Depends(require_super_admin)):
    is_factory = bool(data.factory_asset_id)
    thumb_path, thumb_generated = None, False
    factory_doc = None

    if is_factory:
        factory_doc, video_path = await _resolve_factory_asset(data.factory_asset_id)
        if not factory_doc:
            raise HTTPException(404, "Factory asset not found.")
        if factory_doc.get("is_draft_preview"):
            raise HTTPException(400, "Draft previews cannot be published. Approve & certify the final asset first.")
        if not video_path:
            raise HTTPException(400, "The Factory asset's video file is not available on disk.")
    else:
        if not data.video_upload_id:
            raise HTTPException(400, "Provide a Factory asset or upload an MP4.")
        video_path = os.path.join(UPLOAD_DIR, os.path.basename(data.video_upload_id))
        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            raise HTTPException(400, "No uploaded video found. Upload the MP4 first.")

    title, description, tags = data.title, data.description, data.tags
    if is_factory and (not title or not description or not tags):
        meta = await _metadata_from_factory_asset(factory_doc)
        title = title or meta["title"]
        description = description or meta["description"]
        tags = tags or meta["tags"]
    if data.product_id and (not title or not description):
        meta = await _metadata_from_product(data.product_id)
        if meta:
            title = title or meta["title"]
            description = description or meta["description"]
            tags = tags or meta["tags"]
    if not title:
        raise HTTPException(400, "A title is required (or link a product / Factory asset to auto-fill it).")

    if data.thumbnail_upload_id:
        tp = os.path.join(UPLOAD_DIR, os.path.basename(data.thumbnail_upload_id))
        if os.path.exists(tp) and os.path.getsize(tp) > 0:
            thumb_path = tp
    if is_factory and not thumb_path:
        thumb_path = _extract_thumbnail(video_path)
        thumb_generated = bool(thumb_path)

    try:
        mfk = data.made_for_kids
        if mfk is None and is_factory:
            mfk = bool(factory_doc.get("made_for_kids"))
        pub = await yt.publish_video(
            file_path=video_path, title=title, description=description or "", tags=tags or [],
            privacy=data.privacy, thumbnail_path=thumb_path, playlist_id=data.playlist_id,
            product_id=data.product_id, actor=user["name"], made_for_kids=bool(mfk),
        )
    except yt.YouTubeError as e:
        # Failure isolation: preserve the Gold Master + record the failed destination for retry.
        if is_factory and factory_doc:
            try:
                import continuity as cont
                await cont.on_publish_failed(factory_doc["qru_asset_id"], "youtube", str(e), user["name"])
            except Exception:
                pass
        raise HTTPException(400, str(e))
    finally:
        # Never delete a Factory vault master. Clean up ONLY temp upload files + generated thumbnails.
        to_remove = []
        if thumb_generated and thumb_path:
            to_remove.append(thumb_path)
        if not is_factory:
            to_remove.append(video_path)
            if thumb_path and not thumb_generated:
                to_remove.append(thumb_path)
        for pth in to_remove:
            try:
                if pth and os.path.exists(pth):
                    os.remove(pth)
            except Exception:
                pass

    if is_factory and factory_doc:
        await db.media_assets.update_one({"qru_asset_id": factory_doc["qru_asset_id"]}, {"$set": {
            "youtube_video_id": pub.get("video_id"), "youtube_url": pub.get("url"),
            "published_to_youtube_at": pub.get("published_at") or None}})
        pub["source"] = "factory_asset"
        pub["qru_asset_id"] = factory_doc["qru_asset_id"]
        # Zero-touch continuity: auto-complete the project's Publishing + Distribution stages (Founder Freedom).
        try:
            import continuity as cont
            updated = await cont.on_published(factory_doc["qru_asset_id"], pub.get("url"), pub.get("video_id"), user["name"])
            pub["continuity_updated"] = bool(updated)
        except Exception:
            pub["continuity_updated"] = False
        # Formal Distribution Acceptance Record (preserve full provenance).
        try:
            rec = await _write_distribution_record(factory_doc, pub, title, description, tags, pub.get("thumbnail_set"), user["name"])
            pub["distribution_record_id"] = rec["id"]
        except Exception:
            pass
    return pub
