"""QRU Memory Engineering™ API — manufactures and serves memory assets on the Knowledge Record."""
from fastapi import APIRouter, Depends, HTTPException
import asyncio

from database import db
from auth import get_current_user
from models import clean
import memory_engineering as me

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/characters")
async def characters(user=Depends(get_current_user)):
    return {"characters": me.CHARACTERS}


@router.get("/records")
async def memory_records(user=Depends(get_current_user)):
    """Verified records with their memory-engineering status (for the Memory Engineering board)."""
    recs = await db.knowledge_records.find(
        {"verification_status": "Verified"},
        {"id": 1, "kr_code": 1, "title": 1, "category": 1, "memory_status": 1, "memory_sentence": 1}
    ).sort("updated_at", -1).to_list(200)
    return {"records": clean(recs)}


@router.get("/{kr_id}")
async def get_memory(kr_id: str, user=Depends(get_current_user)):
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    kr = clean(kr)
    return {
        "id": kr["id"], "kr_code": kr.get("kr_code"), "title": kr.get("title"),
        "memory_status": kr.get("memory_status", "not_started"),
        "memory_assets": kr.get("memory_assets"),
        "characters": me.CHARACTERS,
    }


@router.post("/manufacture/{kr_id}")
async def manufacture_memory(kr_id: str, user=Depends(get_current_user)):
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    if kr.get("verification_status") != "Verified":
        raise HTTPException(400, "Only verified records can have memory assets manufactured.")
    asyncio.create_task(me.manufacture_memory_job(kr_id, user["name"]))
    return {"message": "Memory Engineering started", "kr_id": kr_id}
