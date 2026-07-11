"""QRU Factory Operating System™ — API surface (Constitution §7/§8). Outcome-first Create experience."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user
import factory_os as fos

router = APIRouter(prefix="/api/factory-os", tags=["factory-os"])


@router.get("/outcomes")
async def outcomes(user=Depends(get_current_user)):
    return fos.outcomes_view()


class GapInput(BaseModel):
    topic: str
    audience: Optional[str] = ""
    goal: Optional[str] = ""


@router.post("/knowledge-gap-check")
async def knowledge_gap_check(data: GapInput, user=Depends(get_current_user)):
    return await fos.knowledge_gap_check(data.topic, data.audience or "", data.goal or "")


class PlanInput(BaseModel):
    outcome_id: str
    topic: str
    audience: Optional[str] = ""
    goal: Optional[str] = ""


@router.post("/plan")
async def plan(data: PlanInput, user=Depends(get_current_user)):
    return await fos.build_plan(data.outcome_id, data.topic, data.audience or "", data.goal or "")
