"""QRU Enterprise Autonomy & Continuous Improvement™ endpoints."""
from fastapi import APIRouter, Depends

from auth import get_current_user, require_super_admin
import continuous_improvement as ci

router = APIRouter(prefix="/api/continuous", tags=["continuous-improvement"])


@router.get("/settings")
async def ci_settings(user=Depends(get_current_user)):
    """Founder on/off switch state. Continuous Improvement defaults to OFF (no autonomous AI)."""
    return {
        "label": "Continuous Improvement (Autonomy Watcher)",
        "enabled": await ci.is_enabled(),
        "watcher_running": ci.watcher_running(),
        "default": False,
        "description": "OFF by default. When ON, runs only deterministic After-Action Reviews — "
                       "no AI calls and no automatic resuming of manufacturing.",
    }


@router.post("/settings/enable")
async def ci_enable(user=Depends(require_super_admin)):
    return await ci.set_enabled(True, actor=user.get("name", "Founder"))


@router.post("/settings/disable")
async def ci_disable(user=Depends(require_super_admin)):
    return await ci.set_enabled(False, actor=user.get("name", "Founder"))


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await ci.overview()


@router.post("/probe")
async def probe(user=Depends(get_current_user)):
    return await ci.probe_capacity(force=True)


@router.get("/capacity")
async def capacity(user=Depends(get_current_user)):
    """Cheap, cached capacity status for UI polling (auto-resume). Probes at most every 10 min."""
    cap = await ci.probe_capacity(force=False)
    return {**cap, "retry_interval_seconds": 20,
            "next_probe_seconds": ci._PROBE_TTL_SECONDS}


@router.get("/resilience")
async def resilience(user=Depends(get_current_user)):
    return await ci.resilience()


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
