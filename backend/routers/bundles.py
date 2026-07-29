"""QRU Bundles™ — Founder management API."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from auth import require_super_admin
import bundles as bundle_engine

router = APIRouter(prefix="/api/bundles", tags=["bundles"])


class BundleInput(BaseModel):
    title: str
    subtitle: str = ""
    description: str = ""
    imprint: Optional[str] = None
    cover_url: Optional[str] = None
    price: float = 0
    currency: str = "USD"
    item_ids: List[str] = []


class BundleUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    imprint: Optional[str] = None
    cover_url: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    item_ids: Optional[List[str]] = None


@router.get("/eligible-items")
async def eligible_items(user=Depends(require_super_admin)):
    return {"items": await bundle_engine.eligible_items()}


@router.get("")
async def list_bundles(user=Depends(require_super_admin)):
    return {"bundles": await bundle_engine.list_all()}


@router.post("")
async def create_bundle(body: BundleInput, user=Depends(require_super_admin)):
    res = await bundle_engine.create(body.dict(), user.get("name", "Founder"))
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.get("/{bundle_id}")
async def get_bundle(bundle_id: str, user=Depends(require_super_admin)):
    b = await bundle_engine.get_admin(bundle_id)
    if not b:
        raise HTTPException(404, "Bundle not found.")
    return b


@router.put("/{bundle_id}")
async def update_bundle(bundle_id: str, body: BundleUpdate, user=Depends(require_super_admin)):
    res = await bundle_engine.update(bundle_id, {k: v for k, v in body.dict().items() if v is not None})
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.post("/{bundle_id}/publish")
async def publish_bundle(bundle_id: str, user=Depends(require_super_admin)):
    res = await bundle_engine.publish(bundle_id, user.get("name", "Founder"))
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.post("/{bundle_id}/cover")
async def regenerate_cover(bundle_id: str, user=Depends(require_super_admin)):
    res = await bundle_engine.generate_cover(bundle_id)
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.post("/{bundle_id}/unpublish")
async def unpublish_bundle(bundle_id: str, user=Depends(require_super_admin)):
    return await bundle_engine.unpublish(bundle_id)


@router.delete("/{bundle_id}")
async def delete_bundle(bundle_id: str, user=Depends(require_super_admin)):
    return await bundle_engine.delete(bundle_id)
