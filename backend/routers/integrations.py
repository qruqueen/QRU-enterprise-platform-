"""QRU Integration Hub™ — API surface (connections, routing, distribution, monitoring)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database import db
from auth import get_current_user, require_super_admin
from models import clean
import integration_hub as hub

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/catalog")
async def catalog(user=Depends(get_current_user)):
    return {"catalog": hub.PLATFORM_CATALOG, "oauth_platforms": sorted(hub.OAUTH_PLATFORMS)}


@router.get("/connections")
async def list_connections(user=Depends(get_current_user)):
    conns = await db.integrations.find().sort("category", 1).to_list(200)
    return [hub.mask(c) for c in conns]


class ConnectionInput(BaseModel):
    platform: str
    account_name: Optional[str] = ""
    display_name: Optional[str] = ""
    channel_name: Optional[str] = ""
    store_name: Optional[str] = ""
    publisher_name: Optional[str] = ""
    credential: Optional[str] = None  # OAuth token / API key — encrypted, never returned
    default_pricing: Optional[str] = ""
    license_rules: Optional[str] = "Personal Use"
    default_categories: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    branding: Optional[str] = "QRU"
    publishing_rules: Optional[str] = ""


@router.post("/connections")
async def upsert_connection(data: ConnectionInput, user=Depends(require_super_admin)):
    if data.platform not in {p for ps in hub.PLATFORM_CATALOG.values() for p in ps}:
        raise HTTPException(400, "Unknown platform")
    return await hub.upsert_connection(data.model_dump(), user["id"])


@router.post("/connections/{cid}/test")
async def test_connection(cid: str, user=Depends(require_super_admin)):
    res = await hub.test_connection(cid)
    if not res:
        raise HTTPException(404, "Connection not found")
    return res


@router.delete("/connections/{cid}")
async def delete_connection(cid: str, user=Depends(require_super_admin)):
    await db.integrations.delete_one({"id": cid})
    return {"message": "deleted"}


@router.get("/routing")
async def get_routing(user=Depends(get_current_user)):
    return {"rules": await hub.get_routing()}


class RoutingInput(BaseModel):
    rules: dict


@router.post("/routing")
async def set_routing(data: RoutingInput, user=Depends(require_super_admin)):
    await db.integration_routing.update_one(
        {"id": "routing"}, {"$set": {"rules": data.rules}}, upsert=True)
    return {"rules": await hub.get_routing()}


@router.get("/distributions")
async def distributions(product_id: Optional[str] = None, user=Depends(get_current_user)):
    q = {"product_id": product_id} if product_id else {}
    return clean(await db.distributions.find(q).sort("published_at", -1).to_list(300))


@router.post("/distribute/{product_id}")
async def distribute(product_id: str, user=Depends(require_super_admin)):
    res = await hub.auto_distribute(product_id, user["name"])
    if res.get("error"):
        raise HTTPException(404, "Product not found")
    return res


@router.get("/monitor")
async def monitor(user=Depends(get_current_user)):
    return await hub.monitor_summary()
