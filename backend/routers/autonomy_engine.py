"""QRU Autonomous Manufacturing Engine™ (AO-001) — API surface."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user
import autonomous_engine as ae

router = APIRouter(prefix="/api/autonomy-engine", tags=["autonomy-engine"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await ae.overview()


@router.get("/founder-beta")
async def founder_beta(user=Depends(get_current_user)):
    return await ae.founder_beta_summary()


@router.get("/settings")
async def get_settings(user=Depends(get_current_user)):
    return await ae.get_settings()


class SettingsInput(BaseModel):
    enabled: Optional[bool] = None
    max_per_cycle: Optional[int] = None
    publish_threshold: Optional[int] = None


@router.put("/settings")
async def update_settings(data: SettingsInput, user=Depends(get_current_user)):
    return await ae.update_settings({k: v for k, v in data.model_dump().items() if v is not None})


@router.get("/priority-queue")
async def priority_queue(user=Depends(get_current_user)):
    s = await ae.get_settings()
    rows = await ae.priority_queue(threshold=s["publish_threshold"])
    return {"queue": rows, "count": len(rows)}


@router.post("/run-cycle")
async def run_cycle(user=Depends(get_current_user)):
    # Manual "Run one cycle" — always allowed regardless of the ON/OFF switch.
    # Runs in the background (rendering several products can exceed the request timeout);
    # the Founder polls /overview to watch progress.
    import asyncio
    asyncio.create_task(ae.run_cycle(actor=user["name"], force=True))
    return {"ran": True, "queued": True,
            "message": "Autonomous cycle started — advancing top products in the background."}


@router.post("/advance/{pid}")
async def advance(pid: str, user=Depends(get_current_user)):
    s = await ae.get_settings()
    res = await ae.advance_product(pid, actor=user["name"], threshold=s["publish_threshold"])
    if not res.get("ok"):
        raise HTTPException(404, res.get("message", "Not found"))
    return res


@router.get("/ladder/{pid}")
async def ladder(pid: str, user=Depends(get_current_user)):
    from database import db
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    s = await ae.get_settings()
    return ae.gate_ladder(p, s["publish_threshold"])
