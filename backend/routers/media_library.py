"""QRU Media Acquisition Foundation™ — API surface (MO-021 Stock Video + MO-023 Audio)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import db
from auth import get_current_user, require_super_admin
import media_library as ml

router = APIRouter(prefix="/api/media-library", tags=["media-library"])


def _clean(doc):
    doc.pop("_id", None)
    return doc


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return ml.config()


@router.get("/providers")
async def providers(user=Depends(get_current_user)):
    return {"providers": await ml.provider_status()}


class KeyInput(BaseModel):
    api_key: str


@router.post("/providers/{provider_id}/config")
async def configure(provider_id: str, data: KeyInput, user=Depends(require_super_admin)):
    ok, err, code = await ml.save_provider_key(provider_id, data.api_key, user["name"])
    if not ok:
        # err is a TEST_CODE (INVALID_KEY/RATE_LIMITED/...) or a message — surface it, never the key.
        raise HTTPException(400, f"Connection not validated: {err}. The key was NOT saved.")
    return {"configured": True, "provider_id": provider_id, "status": "ACTIVE", "test_code": code}


@router.post("/providers/{provider_id}/test")
async def test(provider_id: str, user=Depends(require_super_admin)):
    return {"provider_id": provider_id, "test_code": await ml.retest_provider(provider_id, user["name"])}


@router.delete("/providers/{provider_id}/config")
async def revoke(provider_id: str, user=Depends(require_super_admin)):
    await ml.revoke_provider_key(provider_id, user["name"])
    return {"revoked": True, "provider_id": provider_id}


@router.get("/providers/{provider_id}/logs")
async def logs(provider_id: str, user=Depends(require_super_admin)):
    rows = await db.credential_logs.find({"provider_id": provider_id}, {"_id": 0}).sort("at", -1).to_list(100)
    return {"logs": rows}


class SearchInput(BaseModel):
    provider_id: str
    query: str
    per_page: Optional[int] = 12


@router.post("/search")
async def search(data: SearchInput, user=Depends(get_current_user)):
    return await ml.search(data.provider_id, data.query, min(int(data.per_page or 12), 30))


class RegisterInput(BaseModel):
    item: dict
    collection: Optional[str] = None
    listening_purpose: Optional[str] = None


@router.post("/register")
async def register(data: RegisterInput, user=Depends(require_super_admin)):
    return await ml.register_asset(data.item, data.collection, data.listening_purpose, user["name"])


@router.get("/assets")
async def assets(kind: Optional[str] = None, user=Depends(get_current_user)):
    q = {"kind": kind} if kind else {}
    rows = await db.media_assets.find(q).sort("created_at", -1).to_list(500)
    return {"assets": [_clean(r) for r in rows], "count": len(rows)}


@router.get("/collections")
async def collections(user=Depends(get_current_user)):
    return {"video_collections": ml.VIDEO_COLLECTIONS, "audio_collections": ml.AUDIO_COLLECTIONS}
