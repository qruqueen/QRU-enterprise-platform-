"""Factory Jobs API — the observability + control surface for the Orchestration Spine™."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from auth import get_current_user, require_super_admin
import job_engine
from database import db

router = APIRouter(prefix="/api/factory-jobs", tags=["factory-jobs"])


@router.get("")
async def list_jobs(status: Optional[str] = None, job_type: Optional[str] = None,
                    limit: int = 100, user=Depends(get_current_user)):
    jobs = await job_engine.list_jobs(status=status, job_type=job_type, limit=min(limit, 300))
    # lightweight summary counts for the dashboard header
    all_jobs = await job_engine.list_jobs(limit=500)
    counts = {}
    for j in all_jobs:
        counts[j["status"]] = counts.get(j["status"], 0) + 1
    return {"jobs": jobs, "counts": counts, "total": len(all_jobs)}


@router.get("/attention")
async def needs_attention(user=Depends(get_current_user)):
    """One place to see everything stalled across the whole factory — paused bulk batches,
    interrupted upgrades/re-renders, failed workflows and Spine jobs — each with a one-tap resume,
    so nothing is ever a silent frozen bar."""
    items = []
    async for b in db.manufacturing_batches.find(
            {"status": "paused"}, {"_id": 0, "id": 1, "name": 1, "total": 1, "completed": 1, "failed": 1}).limit(50):
        items.append({
            "kind": "batch", "id": b["id"], "title": b.get("name") or f"Batch {b['id'][:8]}",
            "detail": f"Bulk manufacturing paused by a restart · {b.get('completed', 0)}/{b.get('total', 0)} done.",
            "resume_path": f"/orchestrator/batches/{b['id']}/resume", "resume_label": "Resume",
        })
    au = await db.asset_upgrade_jobs.find_one({"id": "current"}, {"_id": 0})
    if au and au.get("status") == "interrupted":
        items.append({
            "kind": "asset_upgrade", "id": "asset_upgrade", "title": "Batch Upgrade Assets™",
            "detail": au.get("note", "Interrupted — re-run to finish the remaining products."),
            "resume_path": "/admin/migrations/assets-upgrade", "resume_label": "Re-run",
        })
    rr = await db.deliverable_rerender_jobs.find_one({"id": "current"}, {"_id": 0})
    if rr and rr.get("status") == "interrupted":
        items.append({
            "kind": "rerender", "id": "rerender", "title": "Publication Quality re-render",
            "detail": rr.get("note", "Interrupted — re-run to finish."),
            "resume_path": "/products/rerender-documents", "resume_label": "Re-run",
        })
    async for w in db.workflow_jobs.find(
            {"status": "failed"}, {"_id": 0, "id": 1, "job_number": 1, "template": 1, "note": 1}
    ).sort("created_at", -1).limit(20):
        items.append({
            "kind": "workflow", "id": w["id"],
            "title": f"{w.get('job_number', '')} · {w.get('template', 'Workflow')}".strip(" ·"),
            "detail": w.get("note", "Interrupted by a restart — please retry."),
            "resume_path": None, "resume_label": None,
        })
    async for j in db.factory_jobs.find(
            {"status": "failed"}, {"_id": 0, "id": 1, "title": 1, "error": 1}
    ).sort("created_at", -1).limit(20):
        items.append({
            "kind": "job", "id": j["id"], "title": j.get("title", "Job"),
            "detail": j.get("error", "Failed."),
            "resume_path": f"/factory-jobs/{j['id']}/retry", "resume_label": "Retry",
        })
    return {"items": items, "count": len(items)}


@router.get("/{job_id}")
async def get_job(job_id: str, user=Depends(get_current_user)):
    j = await job_engine.get_job(job_id)
    if not j:
        raise HTTPException(404, "Job not found.")
    return j


@router.post("/{job_id}/retry")
async def retry_job(job_id: str, user=Depends(require_super_admin)):
    r = await job_engine.retry_job(job_id)
    if r is None:
        raise HTTPException(404, "Job not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, user=Depends(require_super_admin)):
    r = await job_engine.cancel_job(job_id)
    if r is None:
        raise HTTPException(404, "Job not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r
