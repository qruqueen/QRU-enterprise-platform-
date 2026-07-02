from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean, QRU_SECTIONS
from ai_service import llm_generate, parse_json, TRANSLATION_SYSTEM, QRU_METHODOLOGY_SYSTEM
from manufacturing_engine import start_manufacturing_job, regenerate_field, ALL_FIELDS
from org_activity import log_org

router = APIRouter(prefix="/api/knowledge-records", tags=["knowledge"])


class KRInput(BaseModel):
    title: str
    subtitle: Optional[str] = ""
    category: str
    division: Optional[str] = "Health"
    verified_truth: str
    the_question: Optional[str] = ""
    simple_answer: Optional[str] = ""
    why_it_matters: Optional[str] = ""
    real_world_example: Optional[str] = ""
    qru_translation: Optional[str] = ""
    everyday_analogy: Optional[str] = ""
    memory_sentence: Optional[str] = ""
    practice_application: Optional[List[str]] = []
    key_vocabulary: Optional[List[dict]] = []
    deep_roots: Optional[str] = ""
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


def _section_value(data, section):
    return data.get(section, [] if section in ("practice_application", "key_vocabulary") else "")


def _is_filled(value):
    if isinstance(value, list):
        return len(value) > 0
    return bool(value and str(value).strip())


@router.post("")
async def create_record(data: KRInput, user=Depends(get_current_user)):
    count = await db.knowledge_records.count_documents({})
    payload = data.model_dump()
    section_status = {s: ("Verified" if _is_filled(payload.get(s)) else "Empty") for s in QRU_SECTIONS}
    rec = {
        "id": gen_id(),
        "kr_code": f"KR-{count + 1:05d}",
        **payload,
        "confidence_score": 0,
        "verification_status": "Draft",
        "approval_status": "Pending",
        "reviewer": None,
        "verification": None,
        "section_status": section_status,
        "understanding_status": "Not Manufactured",
        "is_master_file": False,
        "treasure_standard": False,
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
    new_version = rec.get("version", 1) + 1
    change_log = rec.get("change_log", [])
    change_log.append({"version": new_version, "by": user["name"], "at": now_iso(), "action": "edited"})
    upd = {**data.model_dump(), "updated_at": now_iso(), "version": new_version, "change_log": change_log}
    await db.knowledge_records.update_one({"id": rid}, {"$set": upd})
    # Traceability: mark dependent products for regeneration
    dependents = await db.products.update_many(
        {"knowledge_record_id": rid, "status": {"$nin": ["Archived"]}},
        {"$set": {"status": "Needs Regeneration", "updated_at": now_iso()}})
    if dependents.modified_count:
        await db.notifications.insert_one({
            "id": gen_id(),
            "message": f"{rec['kr_code']} changed — {dependents.modified_count} product(s) marked for regeneration",
            "level": "warning", "read": False, "created_at": now_iso(),
        })
    await log_activity(user["name"], "updated", "KnowledgeRecord", rid, data.title)
    return clean(await db.knowledge_records.find_one({"id": rid}))


@router.get("/{rid}/dependents")
async def dependents(rid: str, user=Depends(get_current_user)):
    prods = await db.products.find({"knowledge_record_id": rid}, {"content": 0}).to_list(200)
    return clean(prods)


@router.delete("/{rid}")
async def delete_record(rid: str, user=Depends(get_current_user)):
    await db.knowledge_records.delete_one({"id": rid})
    return {"message": "deleted"}


@router.post("/{rid}/manufacture-all")
async def manufacture_all(rid: str, user=Depends(get_current_user)):
    """Start the full AI Manufacturing Pipeline as a background job."""
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Not found")
    job_id = await start_manufacturing_job(rid, user["name"])
    await log_activity(user["name"], "started full manufacturing for", "KnowledgeRecord", rid, rec["title"])
    return {"job_id": job_id}


@router.post("/{rid}/fields/{field}/regenerate")
async def regenerate(rid: str, field: str, user=Depends(get_current_user)):
    if field not in ALL_FIELDS:
        raise HTTPException(400, "Unknown field")
    rec = await regenerate_field(rid, field, user["name"])
    if not rec:
        raise HTTPException(404, "Not found")
    return clean(rec)


class FieldApprove(BaseModel):
    status: str = "Approved"


@router.patch("/{rid}/fields/{field}/approve")
async def approve_field(rid: str, field: str, data: FieldApprove, user=Depends(get_current_user)):
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Not found")
    field_status = rec.get("field_status", {})
    field_status[field] = data.status
    await db.knowledge_records.update_one(
        {"id": rid}, {"$set": {"field_status": field_status, "updated_at": now_iso()}})
    return clean(await db.knowledge_records.find_one({"id": rid}))


def _treasure_check(rec):
    return all(_is_filled(rec.get(s)) for s in QRU_SECTIONS)


@router.post("/{rid}/manufacture-understanding")
async def manufacture_understanding(rid: str, user=Depends(get_current_user)):
    """Run the QRU Translation Engine™ to fill any EMPTY methodology sections.
    Never overwrites existing content. AI-added sections are marked Draft."""
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Not found")
    prompt = (
        f"Title: {rec['title']}\nCategory: {rec.get('category','')}\n"
        f"Verified Truth: {rec['verified_truth']}\n"
        f"Existing translation: {rec.get('qru_translation','')}"
    )
    raw = await llm_generate(QRU_METHODOLOGY_SYSTEM, prompt, f"qru-method-{rid}")
    ai = parse_json(raw) or {}
    section_status = rec.get("section_status", {})
    upd = {}
    for s in QRU_SECTIONS:
        current = rec.get(s)
        if not _is_filled(current) and _is_filled(_section_value(ai, s)):
            upd[s] = _section_value(ai, s)
            section_status[s] = "Draft"
    upd["section_status"] = section_status
    upd["understanding_status"] = "Draft"
    upd["updated_at"] = now_iso()
    merged = {**rec, **upd}
    upd["treasure_standard"] = _treasure_check(merged) and rec.get("verification_status") == "Verified"
    await db.knowledge_records.update_one({"id": rid}, {"$set": upd})
    await log_activity(user["name"], "manufactured understanding for", "KnowledgeRecord", rid, rec["title"])
    return clean(await db.knowledge_records.find_one({"id": rid}))


class ReviewInput(BaseModel):
    decision: str  # approve | reject | request_revision
    confidence_score: Optional[int] = None
    evidence: Optional[str] = ""
    sources: Optional[List[str]] = []
    observed_facts: Optional[str] = ""
    calculated_data: Optional[str] = ""
    analytical_judgment: Optional[str] = ""
    conflicting_evidence: Optional[str] = ""
    open_questions: Optional[str] = ""
    reviewer_comments: Optional[str] = ""


@router.post("/{rid}/review")
async def review_record(rid: str, data: ReviewInput, user=Depends(get_current_user)):
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Not found")
    verification = {
        "confidence_score": data.confidence_score,
        "evidence": data.evidence,
        "sources": data.sources,
        "observed_facts": data.observed_facts,
        "calculated_data": data.calculated_data,
        "analytical_judgment": data.analytical_judgment,
        "conflicting_evidence": data.conflicting_evidence,
        "open_questions": data.open_questions,
        "reviewer_comments": data.reviewer_comments,
        "reviewer": user["name"],
        "reviewed_at": now_iso(),
        "decision": data.decision,
    }
    upd = {"verification": verification, "reviewer": user["name"], "updated_at": now_iso()}
    if data.confidence_score is not None:
        upd["confidence_score"] = data.confidence_score

    section_status = rec.get("section_status", {})
    if data.decision == "approve":
        upd["verification_status"] = "Verified"
        upd["approval_status"] = "Approved"
        upd["is_master_file"] = True
        for s in QRU_SECTIONS:
            if section_status.get(s) == "Draft":
                section_status[s] = "Verified"
        upd["section_status"] = section_status
        merged = {**rec, **upd}
        upd["treasure_standard"] = _treasure_check(merged)
        if data.confidence_score is None:
            upd["confidence_score"] = max(rec.get("confidence_score", 0), 92)
    elif data.decision == "reject":
        upd["verification_status"] = "Rejected"
        upd["approval_status"] = "Rejected"
    else:
        upd["verification_status"] = "Revision Requested"
        upd["approval_status"] = "Pending"

    await db.knowledge_records.update_one({"id": rid}, {"$set": upd})
    await log_activity(user["name"], f"{data.decision.replace('_', ' ')}d", "KnowledgeRecord", rid, rec["title"])
    if data.decision == "approve":
        await log_org("Kingdom Lion™", "Verification", "verified & approved", rec["kr_code"], "success")
    # Research Once. Verify Once. Manufacture Forever — auto-start pipeline on approval.
    if data.decision == "approve" and rec.get("understanding_status", "Not Manufactured") == "Not Manufactured":
        await start_manufacturing_job(rid, "Manufacturing Director™ (auto)")
    return clean(await db.knowledge_records.find_one({"id": rid}))


@router.post("/{rid}/verify")
async def verify_record(rid: str, user=Depends(get_current_user)):
    return await review_record(rid, ReviewInput(decision="approve"), user)
