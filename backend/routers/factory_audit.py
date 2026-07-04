"""MO-036 — QRU Factory Health Audit™ API (deterministic, read-only)."""
from fastapi import APIRouter, Depends

from auth import get_current_user
import factory_audit as fa

router = APIRouter(prefix="/api/factory-audit", tags=["factory-audit"])


@router.post("/run")
async def run(user=Depends(get_current_user)):
    return await fa.run_audit(user["name"])


@router.get("/latest")
async def latest(user=Depends(get_current_user)):
    return await fa.latest_audit()


@router.get("/learning-report")
async def learning_report(user=Depends(get_current_user)):
    return await fa.learning_report()


@router.post("/gate-library")
async def gate_library(user=Depends(get_current_user)):
    """QRU Library Auto-Gate™ — start the $0 deterministic gate across the whole library."""
    return await fa.start_library_gate(user["name"])


@router.get("/gate-library/{run_id}")
async def gate_library_status(run_id: str, user=Depends(get_current_user)):
    return await fa.library_gate_status(run_id)
