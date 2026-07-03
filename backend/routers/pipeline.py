"""QRU Manufacturing Engine 2.0 — API surface for recipes, assembly, missing-content
detection, the Quality Control loop, and gated release."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import asyncio

from database import db
from auth import get_current_user
from models import clean
import manufacturing2 as m2

router = APIRouter(prefix="/api/manufacturing2", tags=["manufacturing2"])


@router.get("/recipes")
async def list_recipes(user=Depends(get_current_user)):
    out = []
    for ptype, r in m2.RECIPES.items():
        out.append({
            "product_type": ptype, "version": r["version"],
            "required_fields": [{"field": f, "label": m2.FIELD_LABELS.get(f, f)} for f in r["required_fields"]],
            "stages": m2.recipe_stages(ptype), "deliverables": r.get("deliverables", []),
        })
    return {"recipes": out}


@router.get("/recipes/{ptype}")
async def get_recipe(ptype: str, user=Depends(get_current_user)):
    r = m2.get_recipe(ptype)
    if not r:
        raise HTTPException(404, "No recipe for this product type")
    return {"product_type": ptype, "version": r["version"],
            "required_fields": [{"field": f, "label": m2.FIELD_LABELS.get(f, f)} for f in r["required_fields"]],
            "stages": m2.recipe_stages(ptype), "deliverables": r.get("deliverables", [])}


class DetectInput(BaseModel):
    knowledge_record_id: str
    product_type: str


@router.post("/detect-missing")
async def detect_missing(data: DetectInput, user=Depends(get_current_user)):
    kr = await db.knowledge_records.find_one({"id": data.knowledge_record_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    if not m2.get_recipe(data.product_type):
        raise HTTPException(400, "No recipe for this product type")
    missing = m2.detect_missing(kr, data.product_type)
    return {"missing": missing, "ready": len(missing) == 0,
            "required_count": len(m2.get_recipe(data.product_type)["required_fields"])}


class AssembleInput(BaseModel):
    knowledge_record_id: str
    product_type: str


@router.post("/assemble")
async def assemble(data: AssembleInput, user=Depends(get_current_user)):
    kr = await db.knowledge_records.find_one({"id": data.knowledge_record_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    product = await m2.assemble_product(kr, data.product_type, user["name"])
    return product


@router.get("/{pid}/pipeline")
async def pipeline(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    p = clean(p)
    return {
        "id": p["id"], "product_code": p.get("product_code"), "title": p["title"],
        "product_type": p["product_type"], "status": p.get("status"),
        "recipe_type": p.get("recipe_type"), "stages": p.get("stages", []),
        "gates": p.get("gates", {}), "deliverables": p.get("deliverables", []),
        "missing_fields": p.get("missing_fields", []), "qc": p.get("qc", {}),
        "treasure_standard": p.get("treasure_standard", False),
        "cover_url": p.get("cover_url"), "thumbnail_url": p.get("thumbnail_url"),
        "customer_deliverable": p.get("customer_deliverable"),
        "deliverable_ready": p.get("deliverable_ready", False),
    }


@router.post("/{pid}/render-deliverable")
async def render_deliverable(pid: str, user=Depends(get_current_user)):
    """MT-024 — (re)render the exact customer-ready deliverable set. Deterministic."""
    import deliverable_renderer as dr
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    dv = await dr.ensure_deliverable(pid, user["name"])
    if dv is None:
        raise HTTPException(404, "Product not found")
    return dv


@router.post("/{pid}/manufacture-missing")
async def manufacture_missing(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    asyncio.create_task(m2.manufacture_missing_job(pid, user["name"]))
    return {"message": "Manufacturing missing fields", "pid": pid}


@router.post("/{pid}/quality-control")
async def quality_control(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    asyncio.create_task(m2.quality_control_job(pid, user["name"]))
    return {"message": "Quality Control started", "pid": pid}


@router.post("/{pid}/release")
async def release(pid: str, user=Depends(get_current_user)):
    product, err = await m2.release_product(pid)
    if err:
        raise HTTPException(400, err)
    return product
