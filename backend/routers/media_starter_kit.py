"""QRU Media Starter Kit™ (MO-011) — API surface.

Assembles the standardized production package once a product has passed the Treasure/Gold Standard.
Treasure Standard™: components are reported ready only when their real source exists.
"""
from fastapi import APIRouter, Depends, HTTPException

from database import db
from auth import get_current_user, require_super_admin
from models import gen_id, now_iso
import media_starter_kit as msk
import visual_studio as vs

router = APIRouter(prefix="/api/media-starter-kit", tags=["media-starter-kit"])


def _clean(doc):
    doc.pop("_id", None)
    return doc


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return {"config": msk.CONFIG, "component_labels": msk.COMPONENT_LABELS, "output_labels": msk.OUTPUT_LABELS}


async def _load(product_id):
    p = await db.products.find_one({"id": product_id})
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@router.get("/kit/{product_id}")
async def kit(product_id: str, user=Depends(get_current_user)):
    p = await _load(product_id)
    gold = vs.gold_standard_review(p)
    return msk.build_kit(p, gold)


@router.post("/generate/{product_id}")
async def generate(product_id: str, user=Depends(require_super_admin)):
    p = await _load(product_id)
    gold = vs.gold_standard_review(p)
    kit_data = msk.build_kit(p, gold)
    if not kit_data["gate"]["passed"]:
        raise HTTPException(400, kit_data["gate"]["blocked_reason"] or "Product has not passed the required standards.")
    record = {
        "id": gen_id(), "product_id": product_id, "product_code": p.get("product_code"),
        "title": p.get("title"), "kit": kit_data,
        "generated_by": user["name"], "generated_at": now_iso(),
    }
    await db.media_starter_kits.update_one({"product_id": product_id}, {"$set": record}, upsert=True)
    return _clean(record)


@router.get("/kits")
async def kits(user=Depends(get_current_user)):
    rows = await db.media_starter_kits.find({}).sort("generated_at", -1).to_list(200)
    return {"kits": [_clean(r) for r in rows]}
