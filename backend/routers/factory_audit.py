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
