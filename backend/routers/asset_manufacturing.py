"""QRU Autonomous Asset Manufacturing Engine™ (AO-002) — API surface."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from database import db
from auth import get_current_user
from models import clean
import asset_manufacturing as am

router = APIRouter(prefix="/api/asset-manufacturing", tags=["asset-manufacturing"])


@router.get("/marketplaces")
async def marketplaces(user=Depends(get_current_user)):
    return {"marketplaces": am.MARKETPLACES, "asset_classes": am.ASSET_CLASSES}


@router.get("/plan/{asset_id}")
async def plan(asset_id: str, user=Depends(get_current_user)):
    asset = await db.asset_vault.find_one({"id": asset_id})
    if not asset:
        raise HTTPException(404, "Asset not found")
    return am.manufacturing_plan(clean(asset))


class ManufactureInput(BaseModel):
    product_labels: List[str]


@router.post("/manufacture/{asset_id}")
async def manufacture(asset_id: str, data: ManufactureInput, user=Depends(get_current_user)):
    if not data.product_labels:
        raise HTTPException(400, "Select at least one product to manufacture")
    res = await am.manufacture_from_asset(asset_id, data.product_labels, user["name"])
    if res is None:
        raise HTTPException(404, "Asset not found")
    return res
