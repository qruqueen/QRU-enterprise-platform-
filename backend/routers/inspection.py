"""QRU Manufacturing Inspection System™ (MO-001 / P4) — API surface. Deterministic ($0 AI)."""
from fastapi import APIRouter, Depends, HTTPException

from database import db
from auth import get_current_user
import inspection_system as insp
import connectors as cx

router = APIRouter(prefix="/api/inspection", tags=["inspection"])


async def _operational_count():
    connectors = await cx.list_connectors()
    return sum(1 for c in connectors if c["operational"])


@router.get("/gates")
async def gates(user=Depends(get_current_user)):
    return {"gates": insp.GATES}


@router.get("/summary")
async def summary(user=Depends(get_current_user)):
    ops = await _operational_count()
    products = await db.products.find().sort("created_at", -1).to_list(500)
    cleared = paused = 0
    rows = []
    for p in products:
        r = insp.inspect_product(p, ops)
        if r["manufacturing_allowed"]:
            cleared += 1
        else:
            paused += 1
        rows.append({
            "id": p.get("id"), "product_code": p.get("product_code"), "title": p.get("title"),
            "status": p.get("status"), "overall_score": r["overall_score"],
            "gate_status": r["status"], "blocking_failures": r["blocking_failures"],
        })
    return {"total": len(products), "cleared": cleared, "paused": paused,
            "operational_connectors": ops, "products": rows}


@router.get("/product/{product_id}")
async def inspect_product(product_id: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": product_id})
    if not p:
        raise HTTPException(404, "Product not found")
    ops = await _operational_count()
    return insp.inspect_product(p, ops)


@router.get("/knowledge-record/{kr_id}")
async def inspect_kr(kr_id: str, user=Depends(get_current_user)):
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    import product_automation as pa
    return insp.inspect_kr_for_manufacture(kr, None, pa.RECIPES)
