"""QRU Story & Cinema Studio™ + Podcast Studio™ — API (Stone 3)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
import cinema_studio as cs
import media_division as md

router = APIRouter(prefix="/api/cinema-studio", tags=["cinema-studio"])


@router.get("/formats")
async def formats(user=Depends(get_current_user)):
    return {"formats": cs.FORMATS}


@router.get("/stats")
async def stats(user=Depends(get_current_user)):
    return await cs.stats()


@router.get("/verified-krs")
async def verified_krs(user=Depends(get_current_user)):
    return {"records": await md.verified_krs()}


@router.get("/productions")
async def productions(kr_id: Optional[str] = None, user=Depends(get_current_user)):
    return {"productions": await cs.list_productions(kr_id)}


class ManufactureInput(BaseModel):
    kr_id: str
    format: str


@router.post("/manufacture")
async def manufacture(data: ManufactureInput, user=Depends(get_current_user)):
    res = await cs.manufacture(data.kr_id, data.format, user["name"])
    if not res.get("ok"):
        raise HTTPException(400, res.get("error", "Production failed."))
    return res
