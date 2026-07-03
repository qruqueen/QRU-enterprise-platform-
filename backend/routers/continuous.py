"""QRU Enterprise Autonomy & Continuous Improvement™ endpoints."""
from fastapi import APIRouter, Depends

from auth import get_current_user
import continuous_improvement as ci

router = APIRouter(prefix="/api/continuous", tags=["continuous-improvement"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await ci.overview()


@router.post("/probe")
async def probe(user=Depends(get_current_user)):
    return await ci.probe_capacity(force=True)


@router.post("/auto-resume")
async def auto_resume(user=Depends(get_current_user)):
    return await ci.auto_resume_safe_jobs(force_probe=True)


@router.get("/diagnostics")
async def diagnostics(user=Depends(get_current_user)):
    d = await ci.failed_job_diagnostics()
    return {"count": len(d), "diagnostics": d}


@router.post("/review-batches")
async def review_batches(user=Depends(get_current_user)):
    return {"reviewed": await ci.review_completed_batches()}


@router.get("/after-action-reviews")
async def aars(user=Depends(get_current_user)):
    o = await ci.overview()
    return {"reviews": o["after_action_reviews"]}
