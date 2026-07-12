"""QRU Universal Manufacturing Flow Engine™ API (STD-MFG-0001)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user
import manufacturing_flow as flow
import continuity as cont

router = APIRouter(prefix="/api/flow", tags=["manufacturing-flow"])


@router.get("/lifecycle")
async def lifecycle(user=Depends(get_current_user)):
    return flow.lifecycle_view()


@router.get("/modules")
async def modules(user=Depends(get_current_user)):
    return flow.modules_view()


@router.get("/module/{mid}")
async def module(mid: str, user=Depends(get_current_user)):
    m = flow._MODULE_BY_ID.get(mid)
    if not m:
        raise HTTPException(404, "Module not found.")
    return m


@router.get("/registry")
async def registry(user=Depends(get_current_user)):
    return await flow.constitutional_registry()


class BlueprintInput(BaseModel):
    outcome_id: str
    topic: Optional[str] = ""
    knowledge_ready: Optional[bool] = True


@router.post("/blueprint")
async def blueprint(data: BlueprintInput, user=Depends(get_current_user)):
    return flow.production_blueprint(data.outcome_id, data.topic, bool(data.knowledge_ready))


@router.get("/next-stage/{pid}")
async def next_stage(pid: str, user=Depends(get_current_user)):
    p = await cont.get_project(pid)
    if not p:
        raise HTTPException(404, "Project not found.")
    return flow.next_stage_intelligence(p)


@router.get("/card/{pid}")
async def card(pid: str, user=Depends(get_current_user)):
    p = await cont.get_project(pid)
    if not p:
        raise HTTPException(404, "Project not found.")
    return flow.production_card(p)


class TransitionInput(BaseModel):
    reason: Optional[str] = ""
    action: Optional[str] = "advance"  # advance | approve | complete_workflow


@router.post("/transition/{pid}")
async def transition(pid: str, data: TransitionInput, user=Depends(get_current_user)):
    before = await cont.get_project(pid)
    if not before:
        raise HTTPException(404, "Project not found.")
    from_stage = (before.get("summary") or {}).get("current_stage")
    actor = user.get("name", "Founder")
    if data.action == "approve":
        after = await cont.approve_gate(pid, actor)
    elif data.action == "complete_workflow":
        after = await cont.complete_workflow_stage(pid, actor, data.reason)
    else:
        after = await cont.advance(pid, actor)
    to_stage = (after.get("summary") or {}).get("current_stage")
    handoff = await flow.record_transition(pid, from_stage, to_stage, actor, data.reason,
                                           artifacts=[before.get("showcase_asset_id")] if before.get("showcase_asset_id") else [])
    return {"project": after, "handoff": handoff, "next_stage_intelligence": flow.next_stage_intelligence(after)}


@router.get("/transitions/{pid}")
async def get_transitions(pid: str, user=Depends(get_current_user)):
    return {"transitions": await flow.transitions(pid)}


@router.get("/dashboard")
async def dashboard(user=Depends(get_current_user)):
    return await flow.enterprise_dashboard()
