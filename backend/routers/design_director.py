"""MT-032 — QRU Design Director™ API. Autonomous, deterministic-first design review."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import db
from auth import get_current_user
import design_director as dd

router = APIRouter(prefix="/api/design-director", tags=["design-director"])


@router.get("/settings")
async def get_settings(user=Depends(get_current_user)):
    return await dd.get_settings()


class Settings(BaseModel):
    passing_score: Optional[int] = None
    auto_improve: Optional[bool] = None
    max_iterations: Optional[int] = None
    allow_founder_override: Optional[bool] = None
    allow_ai_hero_art: Optional[bool] = None


@router.put("/settings")
async def put_settings(data: Settings, user=Depends(get_current_user)):
    return await dd.update_settings({k: v for k, v in data.model_dump().items() if v is not None})


@router.get("/queue")
async def queue(user=Depends(get_current_user)):
    return await dd.queue()


@router.get("/references")
async def references(user=Depends(get_current_user)):
    return {"references": await dd.references()}


@router.post("/auto-gate/{pid}")
async def auto_gate(pid: str, user=Depends(get_current_user)):
    """Run the deterministic Auto-Gate (score → improve → telemetry) before Founder Review."""
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    return await dd.auto_gate(pid, user["name"])


@router.get("/telemetry")
async def telemetry(user=Depends(get_current_user)):
    return {"telemetry": await dd.telemetry()}


@router.get("/factory-intelligence")
async def factory_intelligence(user=Depends(get_current_user)):
    return await dd.factory_intelligence()


@router.get("/score/{pid}")
async def score(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    sc = await dd.score_product(p, (p.get("customer_deliverable") or {}).get("files", []))
    await db.products.update_one({"id": pid}, {"$set": {"design_scorecard": sc}})
    return sc


@router.post("/review/{pid}")
async def review(pid: str, user=Depends(get_current_user)):
    """Run the autonomous improvement loop (re-render → re-score until it passes or plateaus)."""
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    result = await dd.fix_design_issues(pid, user["name"])
    if result.get("passed"):
        fresh = await db.products.find_one({"id": pid})
        await dd.record_reference(fresh)
    return result
