"""Emergent Object Storage™ — durable file storage that persists across redeploys.

The container filesystem is EPHEMERAL (wiped on every redeploy/restart), so all runtime-generated
binary files (currently videos) are stored here instead. MongoDB records reference the object
`storage_path`; the DB is the source of truth. Access is always brokered through the backend.
"""
import os
import time
import logging
import requests

logger = logging.getLogger("qru.storage")

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "qru-online"
_EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
_storage_key = None


def init_storage(force=False):
    global _storage_key
    if _storage_key and not force:
        return _storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": _EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    _storage_key = resp.json()["storage_key"]
    logger.info("object storage initialized")
    return _storage_key


def put_object(path: str, data: bytes, content_type: str) -> dict:
    for attempt in range(3):
        key = init_storage(force=(attempt > 0))
        resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": key, "Content-Type": content_type},
                            data=data, timeout=180)
        if resp.status_code == 403 and attempt < 2:
            continue
        if resp.status_code == 429 and attempt < 2:
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()


def get_object(path: str) -> bytes:
    for attempt in range(3):
        key = init_storage(force=(attempt > 0))
        resp = requests.get(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": key}, timeout=120)
        if resp.status_code == 403 and attempt < 2:
            continue
        if resp.status_code == 429 and attempt < 2:
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
        return resp.content
    resp.raise_for_status()


# Async wrappers (offload blocking requests to a thread so the event loop isn't blocked).
import asyncio


async def aput_object(path: str, data: bytes, content_type: str) -> dict:
    return await asyncio.to_thread(put_object, path, data, content_type)


async def aget_object(path: str) -> bytes:
    return await asyncio.to_thread(get_object, path)


# --------------------------------------------------------------------------- #
# Phase B — Durable rendered-asset mirror.
# The rendered-assets directory (/app/backend/rendered_assets) is EPHEMERAL. To
# survive redeploys every rendered file (cover / EPUB / PDF / deliverable / audio)
# is mirrored here under a durable `{APP_NAME}/assets/{fid}` object path. The
# filename (fid) is globally unique, so it doubles as the durable key.
# --------------------------------------------------------------------------- #
ASSET_PREFIX = f"{APP_NAME}/assets"

_MIME = {
    "pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "html": "text/html", "epub": "application/epub+zip", "mp4": "video/mp4", "mp3": "audio/mpeg",
    "zip": "application/zip", "json": "application/json", "txt": "text/plain",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def content_type_for(fid: str) -> str:
    ext = fid.rsplit(".", 1)[-1].lower() if "." in fid else ""
    return _MIME.get(ext, "application/octet-stream")


def asset_object_path(fid: str) -> str:
    return f"{ASSET_PREFIX}/{fid}"


def object_exists(fid: str) -> bool:
    """Cheap existence check for a durable asset (ranged 1-byte GET, no full download)."""
    for attempt in range(2):
        try:
            key = init_storage(force=(attempt > 0))
            resp = requests.get(f"{STORAGE_URL}/objects/{asset_object_path(fid)}",
                                headers={"X-Storage-Key": key, "Range": "bytes=0-0"}, timeout=30)
            if resp.status_code == 403 and attempt < 1:
                continue
            return resp.status_code in (200, 206)
        except Exception as e:
            logger.info("object_exists check failed for %s: %s", fid, e)
            return False
    return False


def mirror_file(fid: str, data: bytes, content_type: str = None) -> bool:
    """Best-effort durable mirror of a rendered asset. NEVER raises — a storage hiccup
    must not fail a render. Returns True on success."""
    try:
        put_object(asset_object_path(fid), data, content_type or content_type_for(fid))
        return True
    except Exception as e:
        logger.warning("asset mirror failed for %s: %s", fid, e)
        return False


def ensure_local(fid: str, dest_path: str) -> bool:
    """Guarantee a rendered asset exists on the local disk, re-downloading it from durable
    object storage if the ephemeral copy is gone. Returns True if the file is present locally."""
    if os.path.exists(dest_path):
        return True
    try:
        data = get_object(asset_object_path(fid))
    except Exception as e:
        logger.info("asset %s unavailable in durable storage: %s", fid, e)
        return False
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        logger.warning("failed to write materialized asset %s: %s", fid, e)
        return False


async def amirror_file(fid: str, data: bytes, content_type: str = None) -> bool:
    return await asyncio.to_thread(mirror_file, fid, data, content_type)


async def aensure_local(fid: str, dest_path: str) -> bool:
    return await asyncio.to_thread(ensure_local, fid, dest_path)


async def aobject_exists(fid: str) -> bool:
    return await asyncio.to_thread(object_exists, fid)
