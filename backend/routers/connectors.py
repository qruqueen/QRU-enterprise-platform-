"""QRU Universal Connector Framework™ — API surface (one uniform lifecycle for all platforms)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from auth import get_current_user
import connectors as cx

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


@router.get("")
async def list_connectors(user=Depends(get_current_user)):
    items = await cx.list_connectors()
    return {"connectors": items, "lifecycle": cx.LIFECYCLE, "count": len(items)}


@router.get("/{platform_id}")
async def get_connector(platform_id: str, user=Depends(get_current_user)):
    c = await cx.get_connector(platform_id)
    if not c:
        raise HTTPException(404, "Unknown connector")
    return c


class ConnectInput(BaseModel):
    credentials: Optional[Dict[str, Any]] = None


@router.post("/{platform_id}/connect")
async def connect(platform_id: str, data: ConnectInput, user=Depends(get_current_user)):
    res, err = await cx.connect(platform_id, data.credentials or {}, user["name"])
    if err:
        raise HTTPException(400, err)
    return res


@router.post("/{platform_id}/verify")
async def verify(platform_id: str, user=Depends(get_current_user)):
    res, err = await cx.verify(platform_id)
    if err:
        raise HTTPException(404, err)
    return res


@router.get("/{platform_id}/manufacture-plan")
async def manufacture_plan(platform_id: str, user=Depends(get_current_user)):
    res, err = await cx.manufacture_plan(platform_id)
    if err:
        raise HTTPException(404, err)
    return res


class PublishInput(BaseModel):
    product_id: str


@router.post("/{platform_id}/publish")
async def publish(platform_id: str, data: PublishInput, user=Depends(get_current_user)):
    res, err = await cx.publish(platform_id, data.product_id, user["name"])
    if err:
        raise HTTPException(400, err)
    return res
