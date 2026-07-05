"""QRU YouTube Publisher™ (MO-006, Phase 1 — Founder Upload Mode) — REAL publishing.

The Founder provides a finished MP4. QRU applies the manufactured metadata (title, description,
tags, category, thumbnail, playlist), uploads it to the connected YouTube channel via the
YouTube Data API v3 (resumable upload) using the existing OAuth access token, returns the REAL
YouTube Video ID, stores the publication, and marks it genuinely Published under the Treasure
Standard™. No fake states — if YouTube isn't connected with upload permission, it says so.

Architected to evolve: Phase 2 (AI video manufacturing) will hand a rendered MP4 path to
`publish_video()` through the same interface, so this becomes the publishing step of the unified
QRU Manufacturing Engine™ without an architectural change.
"""
import os
import logging
import httpx

from database import db
from models import now_iso, gen_id
import oauth_framework as oauth

logger = logging.getLogger("qru.youtube")

PLATFORM = "youtube"
EDUCATION_CATEGORY = "27"  # YouTube "Education" category
API = "https://www.googleapis.com/youtube/v3"
UPLOAD_API = "https://www.googleapis.com/upload/youtube/v3"


class YouTubeError(Exception):
    pass


async def _token_or_error():
    """Return a valid access token, or raise YouTubeError with a Founder-friendly reason."""
    state = await db.connectors.find_one({"platform_id": PLATFORM}) or {}
    if not state.get("access_token_enc"):
        raise YouTubeError("YouTube isn't connected yet. Connect your channel in Publishing Connectors™ first.")
    granted = (state.get("granted_scopes") or "")
    if "youtube.upload" not in granted and granted:
        raise YouTubeError("The connected YouTube account did not grant upload permission. Reconnect and approve the 'Manage your YouTube videos' scope.")
    access, _ = await oauth._valid_access_token(PLATFORM)
    if not access:
        raise YouTubeError("Could not obtain a valid YouTube access token — reconnect the channel in Publishing Connectors™.")
    return access


async def list_playlists():
    """List the connected channel's playlists (for the publish dropdown)."""
    token = await _token_or_error()
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{API}/playlists", params={"part": "snippet", "mine": "true", "maxResults": 50},
                             headers={"Authorization": f"Bearer {token}"})
    if r.status_code >= 400:
        raise YouTubeError(f"Could not list playlists: {r.text[:200]}")
    items = r.json().get("items", [])
    return [{"id": it["id"], "title": it["snippet"]["title"]} for it in items]


async def _resumable_upload(token, file_path, snippet, status):
    size = os.path.getsize(file_path)
    async with httpx.AsyncClient(timeout=900) as client:
        init = await client.post(
            f"{UPLOAD_API}/videos",
            params={"uploadType": "resumable", "part": "snippet,status"},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Length": str(size),
                "X-Upload-Content-Type": "video/*",
            },
            json={"snippet": snippet, "status": status},
        )
        if init.status_code >= 400:
            raise YouTubeError(f"YouTube rejected the upload initiation: {init.text[:300]}")
        location = init.headers.get("location") or init.headers.get("Location")
        if not location:
            raise YouTubeError("YouTube did not return a resumable upload URL.")
        with open(file_path, "rb") as f:
            content = f.read()
        put = await client.put(
            location,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "video/*", "Content-Length": str(size)},
            content=content,
        )
        if put.status_code >= 400:
            raise YouTubeError(f"YouTube rejected the video upload: {put.text[:300]}")
        return put.json()


async def _set_thumbnail(token, video_id, thumb_path):
    try:
        with open(thumb_path, "rb") as f:
            data = f.read()
        ctype = "image/png" if thumb_path.lower().endswith(".png") else "image/jpeg"
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{UPLOAD_API}/thumbnails/set", params={"videoId": video_id},
                                  headers={"Authorization": f"Bearer {token}", "Content-Type": ctype}, content=data)
        return r.status_code < 400
    except Exception as e:
        logger.warning(f"thumbnail set failed: {e}")
        return False


async def _add_to_playlist(token, video_id, playlist_id):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{API}/playlistItems", params={"part": "snippet"},
                                  headers={"Authorization": f"Bearer {token}"},
                                  json={"snippet": {"playlistId": playlist_id,
                                                    "resourceId": {"kind": "youtube#video", "videoId": video_id}}})
        return r.status_code < 400
    except Exception as e:
        logger.warning(f"playlist add failed: {e}")
        return False


async def publish_video(*, file_path, title, description, tags, privacy="private",
                        category_id=EDUCATION_CATEGORY, thumbnail_path=None, playlist_id=None,
                        product_id=None, actor="Founder"):
    """Upload a real MP4 to the connected YouTube channel. Returns the publication record.
    This is the single interface Phase 2 (AI-rendered video) will reuse."""
    if not file_path or not os.path.exists(file_path):
        raise YouTubeError("The video file could not be found on the server.")
    token = await _token_or_error()

    snippet = {"title": (title or "Untitled")[:100],
               "description": (description or "")[:5000],
               "tags": [t for t in (tags or []) if t][:15],
               "categoryId": category_id}
    status = {"privacyStatus": privacy if privacy in ("private", "unlisted", "public") else "private",
              "selfDeclaredMadeForKids": False}

    video = await _resumable_upload(token, file_path, snippet, status)
    video_id = video.get("id")
    if not video_id:
        raise YouTubeError("Upload completed but YouTube did not return a Video ID.")

    thumb_ok = await _set_thumbnail(token, video_id, thumbnail_path) if thumbnail_path else False
    playlist_ok = await _add_to_playlist(token, video_id, playlist_id) if playlist_id else False

    pub = {
        "id": gen_id(), "platform": "youtube", "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "studio_url": f"https://studio.youtube.com/video/{video_id}/edit",
        "title": snippet["title"], "privacy": status["privacyStatus"],
        "thumbnail_set": thumb_ok, "playlist_id": playlist_id if playlist_ok else None,
        "product_id": product_id, "published_by": actor, "published_at": now_iso(),
        "treasure_standard": "Verified — real upload confirmed by YouTube Video ID.",
    }
    await db.youtube_publications.insert_one(dict(pub))

    if product_id:
        await db.products.update_one({"id": product_id}, {"$set": {
            "youtube_video_id": video_id, "youtube_url": pub["url"],
            "youtube_privacy": status["privacyStatus"],
            "status": "Published", "published_at": now_iso(),
            "published_platform": "YouTube", "updated_at": now_iso()}})
    try:
        from org_activity import log_org
        await log_org("QRU YouTube Publisher™", "Distribution",
                      f"published real YouTube video {video_id} ({status['privacyStatus']}) for", title, "success")
    except Exception:
        pass
    return pub


async def list_publications(limit=100):
    rows = await db.youtube_publications.find().sort("published_at", -1).to_list(limit)
    for r in rows:
        r.pop("_id", None)
    return rows
