"""QRU AI Usage & Cost Meter™ endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user
import cost_meter

router = APIRouter(prefix="/api/cost-meter", tags=["cost-meter"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await cost_meter.overview()


@router.get("/can-spend")
async def can_spend(user=Depends(get_current_user)):
    return await cost_meter.can_spend()


class BudgetInput(BaseModel):
    daily_budget_usd: Optional[float] = None
    override_100: Optional[bool] = None


@router.post("/budget")
async def set_budget(data: BudgetInput, user=Depends(get_current_user)):
    return await cost_meter.set_budget(data.daily_budget_usd, data.override_100)
