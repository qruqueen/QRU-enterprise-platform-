"""QRU Intelligent Bulk Manufacturing Orchestrator™ — API surface."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database import db
from auth import get_current_user, require_super_admin
from models import clean, now_iso
import orchestrator as orch
import product_protection as pp

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


@router.get("/settings")
async def get_settings(user=Depends(get_current_user)):
    return await orch.get_settings()


class SettingsInput(BaseModel):
    hands_free_mode: bool


@router.post("/settings")
async def set_settings(data: SettingsInput, user=Depends(require_super_admin)):
    await db.factory_settings.update_one(
        {"id": "factory"}, {"$set": {"hands_free_mode": data.hands_free_mode}}, upsert=True)
    return await orch.get_settings()


async def _autopilot_job(actor):
    # AI Publishing Team advances eligible products with no Founder clicks.
    prods = await db.products.find(
        {"status": {"$in": ["Draft", "Ready", "In Review", "Needs Review"]},
         "is_demo": {"$ne": True}}, {"content": 0}).to_list(500)
    for p in prods:
        pid = p["id"]
        try:
            conf = (p.get("verification") or {}).get("confidence_score") or 0
            if not p.get("verified") and conf < pp.CONFIDENCE_THRESHOLD:
                res = await pp.ai_verify_product(pid, actor)
                if res.get("escalated"):
                    continue
                fresh0 = await db.products.find_one({"id": pid})
                conf = (fresh0.get("verification") or {}).get("confidence_score") or 0
            if conf < pp.CONFIDENCE_THRESHOLD:
                continue
            await db.products.update_one({"id": pid}, {"$set": {"verified": True}})
            if not p.get("protected"):
                await pp.apply_protection(pid, p.get("license_type") or "Personal Use", True, "account_required", actor)
            fresh = await db.products.find_one({"id": pid})
            if fresh.get("creative_status") == "Reviewed":
                await db.products.update_one(
                    {"id": pid}, {"$set": {"status": "Published", "published_at": now_iso(),
                                           "ip.publication_date": now_iso(), "updated_at": now_iso()}})
        except Exception:
            continue


@router.post("/autopilot")
async def autopilot(user=Depends(require_super_admin)):
    """Hands-Free: auto-verify, protect, and publish all eligible products."""
    import asyncio as _a
    _a.create_task(_autopilot_job(user["name"]))
    return {"message": "Autopilot running — AI teams are advancing eligible products."}


class CreateBatchInput(BaseModel):
    name: str
    college: Optional[str] = None
    division: Optional[str] = "Health"
    batch_size: Optional[int] = 25
    topic_registry_ids: Optional[List[str]] = None  # explicit topics
    # OR auto-select: pick queued topics from a college up to batch_size
    from_college: Optional[str] = None


@router.get("/stats")
async def stats(user=Depends(get_current_user)):
    total = await db.manufacturing_batches.count_documents({})
    running = await db.manufacturing_batches.count_documents({"status": "running"})
    completed = await db.manufacturing_batches.count_documents(
        {"status": {"$in": ["completed", "completed_with_errors"]}})
    escalations = await db.founder_escalations.count_documents({"status": "Open"})
    tokens = await db.manufacturing_batches.aggregate(
        [{"$group": {"_id": None, "t": {"$sum": "$est_tokens"}}}]).to_list(1)
    est_tokens = tokens[0]["t"] if tokens else 0
    settings = await orch.get_settings()
    return {"total_batches": total, "running": running, "completed": completed,
            "open_escalations": escalations, "est_tokens": est_tokens,
            "hands_free_mode": settings.get("hands_free_mode", True)}


@router.get("/batches")
async def list_batches(user=Depends(get_current_user)):
    batches = await db.manufacturing_batches.find({}, {"logs": 0}).sort("created_at", -1).to_list(200)
    return clean(batches)


@router.get("/batches/{bid}")
async def get_batch(bid: str, user=Depends(get_current_user)):
    b = await db.manufacturing_batches.find_one({"id": bid})
    if not b:
        raise HTTPException(404, "Batch not found")
    b = clean(b)
    b["logs"] = list(reversed(b.get("logs", [])))[:80]
    return b


@router.post("/batches")
async def create_batch(data: CreateBatchInput, user=Depends(require_super_admin)):
    size = max(1, min(int(data.batch_size or 25), 50))
    topic_ids = data.topic_registry_ids
    college = data.college or data.from_college
    if not topic_ids:
        if not data.from_college:
            raise HTTPException(400, "Provide topic_registry_ids or from_college.")
        q = {"college": data.from_college, "manufacturing_status": {"$in": ["Not Started", "Queued"]}}
        topics = await db.topic_registry.find(q).sort("priority_score", -1).limit(size).to_list(size)
        topic_ids = [t["id"] for t in topics]
        if topics and not data.division:
            data.division = topics[0].get("division", "Health")
    if not topic_ids:
        raise HTTPException(400, "No eligible topics found to batch.")
    topic_ids = topic_ids[:size]
    batch = await orch.create_batch(data.name, college, data.division or "Health",
                                    topic_ids, size, user["id"], user["name"])
    # mark topics queued
    await db.topic_registry.update_many(
        {"id": {"$in": topic_ids}}, {"$set": {"manufacturing_status": "Queued"}})
    return clean(batch)


@router.post("/batches/{bid}/start")
async def start(bid: str, user=Depends(require_super_admin)):
    b = await orch.start_batch(bid)
    if not b:
        raise HTTPException(404, "Batch not found")
    return clean({k: v for k, v in b.items() if k != "logs"})


@router.post("/batches/{bid}/pause")
async def pause(bid: str, user=Depends(require_super_admin)):
    b = await orch.pause_batch(bid)
    return clean({k: v for k, v in b.items() if k != "logs"})


@router.post("/batches/{bid}/resume")
async def resume(bid: str, user=Depends(require_super_admin)):
    b = await orch.resume_batch(bid)
    return clean({k: v for k, v in b.items() if k != "logs"})


@router.post("/batches/{bid}/retry")
async def retry(bid: str, user=Depends(require_super_admin)):
    b = await orch.retry_failed(bid)
    if not b:
        raise HTTPException(404, "Batch not found")
    return clean({k: v for k, v in b.items() if k != "logs"})


@router.post("/batches/{bid}/approve")
async def approve(bid: str, user=Depends(require_super_admin)):
    b = await orch.approve_batch(bid, user["name"])
    if not b:
        raise HTTPException(404, "Batch not found")
    return clean({k: v for k, v in b.items() if k != "logs"})
