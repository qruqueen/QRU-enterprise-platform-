"""QRU Governance Binding Layer™ — API surface (MO-008)."""
from fastapi import APIRouter, Depends, HTTPException

from database import db
from auth import get_current_user
import governance_binding as gb

router = APIRouter(prefix="/api/governance-binding", tags=["governance-binding"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await gb.overview()


@router.get("/agents")
async def agents(user=Depends(get_current_user)):
    return {"agents": await gb.agents()}


@router.get("/design")
async def design(user=Depends(get_current_user)):
    return await gb.design_governance()


@router.get("/strip/{entity_type}")
async def strip(entity_type: str, user=Depends(get_current_user)):
    return {"governed_by": await gb.governed_by(entity_type)}


@router.get("/manufacturing/{order_id}/compliance")
async def compliance(order_id: str, user=Depends(get_current_user)):
    o = await db.manufacturing_orders.find_one({"id": order_id})
    if not o:
        raise HTTPException(404, "Manufacturing order not found")
    return await gb.manufacturing_compliance(o)
