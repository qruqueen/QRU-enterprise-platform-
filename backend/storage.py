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
