"""QRU Media Manufacturing Division™ — API (Stone 2). One verified KR → many products."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from auth import get_current_user
import media_division as md

router = APIRouter(prefix="/api/media-division", tags=["media-division"])


@router.get("/catalog")
async def catalog(user=Depends(get_current_user)):
    return {"catalog": md.CATALOG, "future": md.FUTURE_CATALOG, "promise_pillars": [p["name"] for p in md.MANUFACTURING_PROMISE["pillars"]]}


@router.get("/stats")
async def stats(user=Depends(get_current_user)):
    return await md.stats()


@router.get("/verified-krs")
async def verified_krs(user=Depends(get_current_user)):
    return {"records": await md.verified_krs()}


class ManufactureInput(BaseModel):
    kr_id: str
    formats: Optional[List[str]] = None


@router.post("/manufacture")
async def manufacture(data: ManufactureInput, request: Request, user=Depends(get_current_user)):
    base_url = str(request.base_url).rstrip("/")
    res = await md.manufacture_catalog(data.kr_id, data.formats, user["name"], base_url)
    if not res.get("ok"):
        raise HTTPException(400, res.get("error", "Manufacturing failed."))
    return res
