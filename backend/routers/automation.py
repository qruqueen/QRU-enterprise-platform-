"""QRU Product Automation Engine™ + Meditation & Inspiration Studio™ — API surface."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database import db
from auth import get_current_user, require_super_admin
from models import clean, now_iso
import product_automation as pa
import product_protection as pp

router = APIRouter(prefix="/api/automation", tags=["automation"])


@router.get("/recipes")
async def recipes(user=Depends(get_current_user)):
    return {"recipes": [{"product_type": k, **v} for k, v in pa.RECIPES.items()],
            "meditation_content_types": pa.MEDITATION_CONTENT_TYPES}


@router.get("/agents")
async def agents(user=Depends(get_current_user)):
    return {"agents": pa.AGENT_REGISTRY}


@router.get("/packages")
async def packages(user=Depends(get_current_user)):
    return {"packages": pa.PACKAGE_PRESETS}


@router.get("/meditation/profiles")
async def profiles(user=Depends(get_current_user)):
    return {"profiles": pa.INSPIRATION_PROFILES, "frequencies": pa.FREQUENCY_LIBRARY}


class ManufactureInput(BaseModel):
    product_types: Optional[List[str]] = None
    preset: Optional[str] = None
    inspiration_profile: Optional[str] = None
    frequency: Optional[str] = None


@router.post("/manufacture/{kr_id}")
async def manufacture(kr_id: str, data: ManufactureInput, user=Depends(require_super_admin)):
    types = data.product_types or pa.PACKAGE_PRESETS.get(data.preset or "", [])
    if not types:
        raise HTTPException(400, "Provide product_types or a valid preset")
    config = {"inspiration_profile": data.inspiration_profile, "frequency": data.frequency}
    order, err = await pa.manufacture_package(kr_id, types, user["id"], user["name"], config)
    if err:
        raise HTTPException(400, err)
    return clean(order)


class ProductionLineInput(BaseModel):
    topic: str
    product_types: Optional[List[str]] = None
    preset: Optional[str] = "Core Package"
    division: Optional[str] = "Health"
    audience: Optional[str] = None
    language: Optional[str] = None
    difficulty: Optional[str] = None
    inspiration_profile: Optional[str] = None
    frequency: Optional[str] = None


@router.post("/production-line")
async def production_line(data: ProductionLineInput, user=Depends(require_super_admin)):
    """What do you want to teach today? — one command → verified knowledge → full product collection."""
    types = data.product_types or pa.PACKAGE_PRESETS.get(data.preset or "Core Package", [])
    if not types:
        raise HTTPException(400, "Provide product_types or a valid preset")
    config = {"inspiration_profile": data.inspiration_profile, "frequency": data.frequency,
              "audience": data.audience, "language": data.language, "difficulty": data.difficulty}
    run, err = await pa.run_production_line(data.topic, types, config, user["id"], user["name"], data.division or "Health")
    if err:
        raise HTTPException(400, err)
    return clean(run)


@router.get("/production-line/runs")
async def production_runs(user=Depends(get_current_user)):
    return clean(await db.production_line_runs.find().sort("created_at", -1).to_list(100))


@router.get("/production-line/runs/{rid}")
async def production_run(rid: str, user=Depends(get_current_user)):
    r = await db.production_line_runs.find_one({"id": rid})
    if not r:
        raise HTTPException(404, "Run not found")
    return clean(r)


@router.get("/orders")
async def orders(user=Depends(get_current_user)):
    return clean(await db.production_orders.find().sort("created_at", -1).to_list(100))


@router.get("/orders/{oid}")
async def order(oid: str, user=Depends(get_current_user)):
    o = await db.production_orders.find_one({"id": oid})
    if not o:
        raise HTTPException(404, "Order not found")
    return clean(o)


class ReviewInput(BaseModel):
    decision: str  # approve | request_revision | reject


@router.post("/products/{pid}/review")
async def review_product(pid: str, data: ReviewInput, user=Depends(require_super_admin)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    if data.decision == "approve":
        if not p.get("verified"):
            res = await pp.ai_verify_product(pid, user["name"])
            if not res.get("verified"):
                await db.products.update_one({"id": pid}, {"$set": {"verified": True}})
        if not p.get("protected"):
            await pp.apply_protection(pid, p.get("license_type") or "Personal Use", True, "account_required", user["name"])
        await db.products.update_one({"id": pid}, {"$set": {"status": "Published", "published_at": now_iso(),
                                                            "ip.publication_date": now_iso(), "updated_at": now_iso()}})
        import integration_hub as ihub
        await ihub.auto_distribute(pid, user["name"])
        return {"status": "Published"}
    if data.decision == "reject":
        await db.products.update_one({"id": pid}, {"$set": {"status": "Rejected", "updated_at": now_iso()}})
        return {"status": "Rejected"}
    await db.products.update_one({"id": pid}, {"$set": {"status": "Revision Requested", "updated_at": now_iso()}})
    return {"status": "Revision Requested"}
