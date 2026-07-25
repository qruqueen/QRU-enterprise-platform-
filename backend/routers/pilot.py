"""PILOT-MFG-0001 — Manufacturing Operations Coordinator™ API (Shadow Mode, read-only)."""
from fastapi import APIRouter, Depends

from auth import require_super_admin
import pilot_coordinator as pilot
from database import db

router = APIRouter(prefix="/api/pilot", tags=["pilot-mfg-coordinator"])


@router.get("/mfg-coordinator")
async def charter(user=Depends(require_super_admin)):
    """The role charter — purpose, mode, and the may / may-not authority boundaries."""
    return pilot.CHARTER


@router.get("/mfg-coordinator/readiness-report")
async def readiness_report(user=Depends(require_super_admin)):
    """RI-MFG-0001 first workstream — consolidated store re-render readiness (read-only, $0 AI)."""
    return await pilot.store_rerender_readiness_report(record=False)


@router.post("/mfg-coordinator/readiness-report/run")
async def run_readiness_report(user=Depends(require_super_admin)):
    """Run the responsibility and file the report to the pilot's own evidence journal.
    Still read-only w.r.t. Factory records — nothing in the store is modified."""
    return await pilot.store_rerender_readiness_report(record=True, actor=user.get("email", "founder"))


@router.post("/mfg-coordinator/batch-rerender")
async def batch_rerender(user=Depends(require_super_admin)):
    """RI-MFG-0002 — execute the Founder-authorized governed batch re-render of the 8 books and
    return the Post-Render Validation Report. Reuses cover art ($0 AI). Never publishes/deploys."""
    return await pilot.batch_rerender(actor=user.get("email", "founder"))


@router.get("/mfg-coordinator/post-render-report")
async def latest_post_render_report(user=Depends(require_super_admin)):
    """Fetch the most recent Post-Render Validation Report from the pilot journal (read-only)."""
    doc = await db.pilot_reports.find_one({"type": "post_render_validation"},
                                          {"_id": 0}, sort=[("recorded_at", -1)])
    return doc or {"empty": True}
