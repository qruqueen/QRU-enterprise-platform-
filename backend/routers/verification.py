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


# Statuses that mean a legacy record still needs a Founder verification decision.
_LEGACY_NEEDS = ["Draft", "In Review", "Revision Requested", "Not Manufactured",
                 "Extracted — Needs Founder Review", "Verification Required", "Internal Review"]
_LEGACY_VERIFIED = ["Verified"]
_AWAITING_MFG = ["Topic Seed"]


def _kr2_verified(status):
    s = str(status or "")
    return "Verified External" in s or "Gold Standard" in s


@router.get("/queue")
async def verification_queue(user=Depends(get_current_user)):
    """Unified, honest verification queue across BOTH knowledge collections. Surfaces every record
    that still needs a decision (previously hidden 'Extracted — Needs Founder Review' + KR 2.0), and
    reports true counts so the screen can never falsely claim 'all verified'."""
    needs, awaiting = [], []
    verified_count = 0
    # Legacy knowledge_records
    proj = {"id": 1, "kr_code": 1, "title": 1, "verified_truth": 1, "verification_status": 1, "category": 1}
    async for r in db.knowledge_records.find({}, proj):
        vs = r.get("verification_status")
        item = {"id": r["id"], "code": r.get("kr_code"), "title": r.get("title") or "Untitled",
                "summary": (r.get("verified_truth") or "")[:220], "status": vs,
                "category": r.get("category"), "collection": "legacy"}
        if vs in _LEGACY_VERIFIED:
            verified_count += 1
        elif vs in _AWAITING_MFG:
            awaiting.append(item)
        elif vs == "Rejected":
            continue
        else:
            needs.append(item)
    # KR 2.0 knowledge_engine_records
    proj2 = {"id": 1, "kr_code": 1, "topic": 1, "single_source_of_truth": 1, "status": 1}
    async for r in db.knowledge_engine_records.find({}, proj2):
        st = r.get("status")
        if _kr2_verified(st):
            verified_count += 1
            continue
        needs.append({"id": r["id"], "code": r.get("kr_code"), "title": r.get("topic") or "Untitled",
                      "summary": (str(r.get("single_source_of_truth") or ""))[:220], "status": st,
                      "category": "KR 2.0", "collection": "kr2"})
    total = verified_count + len(needs) + len(awaiting)
    return {"needs_verification": clean(needs), "awaiting_manufacturing": clean(awaiting),
            "counts": {"verified": verified_count, "pending": len(needs),
                       "awaiting_manufacturing": len(awaiting), "total": total}}


class KR2Verify(BaseModel):
    decision: str = "approve"  # approve | reject
    note: Optional[str] = ""


@router.post("/kr2/{rid}/verify")
async def verify_kr2(rid: str, data: KR2Verify, user=Depends(require_super_admin)):
    """Founder decision on a KR 2.0 record → mark it Verified External™ (Gold Standard) so media built
    on it can render, or reject it."""
    rec = await db.knowledge_engine_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "KR 2.0 record not found")
    if data.decision == "approve":
        new_status = "Verified External™ · Gold Standard Knowledge Record™"
    else:
        new_status = "Rejected"
    await db.knowledge_engine_records.update_one({"id": rid}, {"$set": {
        "status": new_status, "verified_by": user["name"], "verified_at": now_iso(),
        "verification_note": data.note, "updated_at": now_iso()}})
    return {"ok": True, "status": new_status}



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
