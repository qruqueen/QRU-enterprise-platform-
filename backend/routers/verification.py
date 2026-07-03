"""QRU Verification Team™ API — autonomous AI verification + Founder escalation queue."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

from database import db
from auth import get_current_user, require_super_admin
from models import clean, now_iso
from verification_engine import ai_verify_record, CONFIDENCE_THRESHOLD

router = APIRouter(prefix="/api/verification", tags=["verification-team"])


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return {"confidence_threshold": CONFIDENCE_THRESHOLD}


@router.post("/ai-review/{kr_id}")
async def ai_review(kr_id: str, user=Depends(get_current_user)):
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    result = await ai_verify_record(kr_id, user["name"])
    return result


async def _review_all_job(kr_ids, actor):
    for kid in kr_ids:
        try:
            await ai_verify_record(kid, actor)
        except Exception:
            pass


@router.post("/ai-review-all")
async def ai_review_all(user=Depends(require_super_admin)):
    """Autonomously verify every manufactured-but-unverified record in the background."""
    krs = await db.knowledge_records.find(
        {"understanding_status": {"$in": ["Draft", "Verified"]},
         "verification_status": {"$in": ["Draft", "In Review", "Revision Requested", "Not Manufactured"]}},
        {"id": 1}).to_list(1000)
    ids = [k["id"] for k in krs]
    asyncio.create_task(_review_all_job(ids, user["name"]))
    return {"queued": len(ids)}


@router.get("/log")
async def verification_log(limit: int = 100, user=Depends(get_current_user)):
    """Recent autonomous verification decisions across all records."""
    recs = await db.knowledge_records.find(
        {"verification_log": {"$exists": True, "$ne": []}},
        {"id": 1, "kr_code": 1, "title": 1, "verification_log": 1, "verification_status": 1, "confidence_score": 1}
    ).sort("updated_at", -1).to_list(300)
    entries = []
    for r in recs:
        for e in r.get("verification_log", []):
            entries.append({"kr_id": r["id"], "kr_code": r.get("kr_code"), "title": r.get("title"),
                            "verification_status": r.get("verification_status"), **e})
    entries.sort(key=lambda x: x.get("at", ""), reverse=True)
    return {"entries": clean(entries[:limit])}


@router.get("/escalations")
async def escalations(status: Optional[str] = None, user=Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    items = await db.founder_escalations.find(query).sort("created_at", -1).to_list(200)
    return clean(items)


class ResolveInput(BaseModel):
    decision: str  # approve | reject | acknowledge
    note: Optional[str] = ""


@router.post("/escalations/{eid}/resolve")
async def resolve_escalation(eid: str, data: ResolveInput, user=Depends(require_super_admin)):
    esc = await db.founder_escalations.find_one({"id": eid})
    if not esc:
        raise HTTPException(404, "Escalation not found")
    await db.founder_escalations.update_one(
        {"id": eid}, {"$set": {"status": "Resolved", "resolution": data.decision,
                               "resolution_note": data.note, "resolved_by": user["name"], "resolved_at": now_iso()}})
    kr_id = esc.get("kr_id")
    if kr_id:
        if data.decision == "approve":
            await db.knowledge_records.update_one(
                {"id": kr_id}, {"$set": {"verification_status": "Verified", "approval_status": "Approved",
                                         "is_master_file": True, "escalated": False, "updated_at": now_iso()}})
        elif data.decision == "reject":
            await db.knowledge_records.update_one(
                {"id": kr_id}, {"$set": {"verification_status": "Rejected", "approval_status": "Rejected",
                                         "escalated": False, "updated_at": now_iso()}})
    return {"message": "resolved"}
