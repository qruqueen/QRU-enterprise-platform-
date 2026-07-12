"""QRU Factory Operating System™ — API surface (Constitution §7/§8). Outcome-first Create experience."""
from fastapi import APIRouter, Depends, HTTPException
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


# --- Product Continuity Principle™ (Constitution §4/§14G) ---
import continuity as cont


class LaunchInput(BaseModel):
    outcome_id: str
    topic: str
    audience: Optional[str] = ""
    goal: Optional[str] = ""


@router.post("/projects")
async def create_project(data: LaunchInput, user=Depends(get_current_user)):
    plan = await fos.build_plan(data.outcome_id, data.topic, data.audience or "", data.goal or "")
    if not plan.get("ok"):
        return plan
    return await cont.create_project(plan, user["name"])


@router.get("/projects")
async def list_projects(user=Depends(get_current_user)):
    return {"projects": await cont.list_projects(user["name"])}


@router.get("/effort-summary")
async def effort_summary(user=Depends(get_current_user)):
    return await cont.effort_summary()


@router.get("/projects/{pid}")
async def get_project(pid: str, user=Depends(get_current_user)):
    p = await cont.get_project(pid)
    if not p:
        raise HTTPException(404, "Project not found.")
    return p


@router.get("/projects/{pid}/items")
async def project_items(pid: str, user=Depends(get_current_user)):
    res = await cont.project_items(pid)
    if res is None:
        raise HTTPException(404, "Project not found.")
    return res




@router.post("/projects/{pid}/advance")
async def advance_project(pid: str, user=Depends(get_current_user)):
    p = await cont.advance(pid, user["name"])
    if not p:
        raise HTTPException(404, "Project not found.")
    return p


@router.post("/projects/{pid}/approve")
async def approve_project(pid: str, user=Depends(get_current_user)):
    p = await cont.approve_gate(pid, user["name"])
    if not p:
        raise HTTPException(404, "Project not found.")
    return p


@router.post("/projects/{pid}/complete-stage")
async def complete_stage(pid: str, user=Depends(get_current_user)):
    p = await cont.complete_workflow_stage(pid, user["name"])
    if not p:
        raise HTTPException(404, "Project not found.")
    return p


class ModeInput(BaseModel):
    mode: str  # auto_continue | paused | stopped


@router.post("/projects/{pid}/mode")
async def set_mode(pid: str, data: ModeInput, user=Depends(get_current_user)):
    if data.mode not in ("auto_continue", "paused", "stopped"):
        raise HTTPException(400, "Invalid mode.")
    p = await cont.set_mode(pid, data.mode, user["name"])
    if not p:
        raise HTTPException(404, "Project not found.")
    return p


# --- Factory Concierge™ (Phase B, Constitution §7/§8) — conversational guide over Factory OS ---
import factory_concierge as concierge


class ConciergeInput(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_ai: Optional[bool] = False


@router.post("/concierge/message")
async def concierge_message(data: ConciergeInput, user=Depends(get_current_user)):
    return await concierge.handle_message(data.session_id, data.message, bool(data.use_ai), user.get("name", "Founder"))


@router.get("/concierge/session/{sid}")
async def concierge_session(sid: str, user=Depends(get_current_user)):
    s = await concierge.get_history(sid)
    if not s:
        raise HTTPException(404, "Session not found.")
    return s
