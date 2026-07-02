from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean
from ai_service import llm_generate, parse_json, TRANSLATION_SYSTEM

router = APIRouter(prefix="/api/knowledge-records", tags=["knowledge"])


class KRInput(BaseModel):
    title: str
    subtitle: Optional[str] = ""
    category: str
    verified_truth: str
    consumer_translation: Optional[str] = ""
    everyday_analogy: Optional[str] = ""
    story: Optional[str] = ""
    memory_sentence: Optional[str] = ""
    references: Optional[List[str]] = []
    sources: Optional[List[str]] = []


async def log_activity(actor, action, entity, entity_id, detail=""):
    await db.activities.insert_one({
        "id": gen_id(), "actor": actor, "action": action, "entity": entity,
        "entity_id": entity_id, "detail": detail, "created_at": now_iso(),
    })


@router.get("")
async def list_records(q: Optional[str] = None, status: Optional[str] = None,
                       category: Optional[str] = None, user=Depends(get_current_user)):
    query = {}
    if status:
        query["verification_status"] = status
    if category:
        query["category"] = category
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"verified_truth": {"$regex": q, "$options": "i"}},
        ]
    records = await db.knowledge_records.find(query).sort("created_at", -1).to_list(500)
    return clean(records)


@router.get("/{rid}")
async def get_record(rid: str, user=Depends(get_current_user)):
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Knowledge Record not found")
    return clean(rec)


@router.post("")
async def create_record(data: KRInput, user=Depends(get_current_user)):
    count = await db.knowledge_records.count_documents({})
    rec = {
        "id": gen_id(),
        "kr_code": f"KR-{count + 1:05d}",
        **data.model_dump(),
        "confidence_score": 0,
        "verification_status": "Draft",
        "approval_status": "Pending",
        "reviewer": None,
        "practice_activities": [],
        "products_created": 0,
        "version": 1,
        "created_by": user["name"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.knowledge_records.insert_one(dict(rec))
    await log_activity(user["name"], "created", "KnowledgeRecord", rec["id"], rec["title"])
    return clean(rec)


@router.put("/{rid}")
async def update_record(rid: str, data: KRInput, user=Depends(get_current_user)):
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Not found")
    upd = {**data.model_dump(), "updated_at": now_iso(), "version": rec.get("version", 1) + 1}
    await db.knowledge_records.update_one({"id": rid}, {"$set": upd})
    await log_activity(user["name"], "updated", "KnowledgeRecord", rid, data.title)
    return clean(await db.knowledge_records.find_one({"id": rid}))


@router.delete("/{rid}")
async def delete_record(rid: str, user=Depends(get_current_user)):
    await db.knowledge_records.delete_one({"id": rid})
    return {"message": "deleted"}


@router.post("/{rid}/translate")
async def translate_record(rid: str, user=Depends(get_current_user)):
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Not found")
    prompt = f"Title: {rec['title']}\nCategory: {rec['category']}\nVerified Truth: {rec['verified_truth']}"
    raw = await llm_generate(TRANSLATION_SYSTEM, prompt, f"translate-{rid}")
    data = parse_json(raw) or {}
    upd = {
        "consumer_translation": data.get("consumer_translation", rec.get("consumer_translation", "")),
        "everyday_analogy": data.get("everyday_analogy", ""),
        "story": data.get("story", ""),
        "memory_sentence": data.get("memory_sentence", ""),
        "practice_activities": data.get("practice_activities", []),
        "updated_at": now_iso(),
    }
    await db.knowledge_records.update_one({"id": rid}, {"$set": upd})
    await log_activity(user["name"], "translated", "KnowledgeRecord", rid, rec["title"])
    return clean(await db.knowledge_records.find_one({"id": rid}))


@router.post("/{rid}/verify")
async def verify_record(rid: str, user=Depends(get_current_user)):
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Not found")
    upd = {
        "verification_status": "Verified",
        "approval_status": "Approved",
        "confidence_score": max(rec.get("confidence_score", 0), 92),
        "reviewer": user["name"],
        "updated_at": now_iso(),
    }
    await db.knowledge_records.update_one({"id": rid}, {"$set": upd})
    await log_activity(user["name"], "verified", "KnowledgeRecord", rid, rec["title"])
    return clean(await db.knowledge_records.find_one({"id": rid}))
