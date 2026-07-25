"""PILOT-MFG-0001 — Manufacturing Operations Coordinator™ API (Shadow Mode, read-only)."""
from fastapi import APIRouter, Depends

from auth import require_super_admin
import pilot_coordinator as pilot

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
