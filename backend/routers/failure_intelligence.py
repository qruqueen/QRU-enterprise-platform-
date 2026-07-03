"""MT-034 — QRU Production Failure Intelligence™ API."""
from fastapi import APIRouter, Depends

from auth import get_current_user
import failure_intelligence as fi

router = APIRouter(prefix="/api/failure-intelligence", tags=["failure-intelligence"])


@router.get("/dashboard")
async def dashboard(user=Depends(get_current_user)):
    return await fi.analyze()


@router.post("/run/{run_id}/retry")
async def retry(run_id: str, user=Depends(get_current_user)):
    return await fi.retry_run(run_id)
