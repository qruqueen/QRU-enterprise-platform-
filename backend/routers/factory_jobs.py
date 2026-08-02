"""Factory Jobs API — the observability + control surface for the Orchestration Spine™."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from auth import get_current_user, require_super_admin
import job_engine

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
