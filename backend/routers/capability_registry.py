"""QRU Factory™ — Capability Registry™ & Manufacturing Map™ API (Phases 1/6/7)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user, require_super_admin
import capability_registry as cr

router = APIRouter(prefix="/api/capability-registry", tags=["capability-registry"])


@router.get("")
async def list_capabilities(layer: Optional[str] = None, status: Optional[str] = None, user=Depends(get_current_user)):
    return {
        "capabilities": await cr.list_capabilities(layer, status),
        "statuses": [{"value": s, "label": cr.STATUS_LABEL[s]} for s in cr.STATUSES],
        "layers": [{"value": k, "name": n} for k, n, _ in cr.LAYERS],
    }


@router.get("/summary")
async def summary(user=Depends(get_current_user)):
    return await cr.summary()


@router.get("/map")
async def manufacturing_map(user=Depends(get_current_user)):
    return await cr.manufacturing_map()


@router.get("/promise")
async def promise(user=Depends(get_current_user)):
    return cr.MANUFACTURING_PROMISE


class StatusInput(BaseModel):
    status: str


@router.patch("/{cap_id}/status")
async def set_status(cap_id: str, data: StatusInput, user=Depends(require_super_admin)):
    cap = await cr.set_status(cap_id, data.status, user.get("name", "Founder"))
    if cap is None:
        raise HTTPException(404, "Capability not found or invalid status.")
    return cap
