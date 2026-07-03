"""QRU Media Manufacturing Engine™ API."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import asyncio

from database import db
from auth import get_current_user
from models import clean
import media_engine as me

router = APIRouter(prefix="/api/media", tags=["media"])


class ManufactureInput(BaseModel):
    knowledge_record_id: str
    media_type: str = "video"  # "video" | "meditation"


@router.post("/manufacture")
async def manufacture(data: ManufactureInput, user=Depends(get_current_user)):
    kr = await db.knowledge_records.find_one({"id": data.knowledge_record_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    if kr.get("verification_status") != "Verified":
        raise HTTPException(400, "Only verified records can manufacture media.")
    if data.media_type not in ("video", "meditation"):
        raise HTTPException(400, "media_type must be 'video' or 'meditation'")
    asyncio.create_task(me.manufacture_media_job(data.knowledge_record_id, data.media_type, user["name"]))
    return {"message": "Media manufacturing started", "media_type": data.media_type}


@router.get("/library")
async def library(user=Depends(get_current_user)):
    items = await db.media_assets.find({}, {"assets": 0}).sort("created_at", -1).to_list(200)
    return {"media": clean(items), "destinations": me.PUBLISHING_DESTINATIONS, "meditation_sessions": me.MEDITATION_SESSIONS}


@router.get("/{mid}")
async def get_media(mid: str, user=Depends(get_current_user)):
    m = await db.media_assets.find_one({"id": mid})
    if not m:
        raise HTTPException(404, "Media not found")
    return clean(m)


@router.post("/{mid}/quality-control")
async def quality_control(mid: str, user=Depends(get_current_user)):
    m = await db.media_assets.find_one({"id": mid})
    if not m:
        raise HTTPException(404, "Media not found")
    asyncio.create_task(me.media_qc_job(mid, user["name"]))
    return {"message": "Media Quality Control started", "mid": mid}


class PublishInput(BaseModel):
    destination: str


@router.post("/{mid}/publish")
async def publish(mid: str, data: PublishInput, user=Depends(get_current_user)):
    result, err = await me.publish_media(mid, data.destination)
    if err:
        raise HTTPException(400, err)
    return result
