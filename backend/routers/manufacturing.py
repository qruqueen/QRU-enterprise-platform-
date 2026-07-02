from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean

router = APIRouter(prefix="/api/manufacturing-orders", tags=["manufacturing"])

STAGES = ["Queued", "Research", "Manufacturing", "Quality Review", "Approved", "Published"]


class MOInput(BaseModel):
    topic: str
    audience: str
    learning_level: Optional[str] = "General"
    product_types: List[str] = []
    priority: Optional[str] = "Medium"
    due_date: Optional[str] = None
    verification_level: Optional[str] = "Standard"
    assigned_employees: Optional[List[str]] = []
    knowledge_record_id: Optional[str] = None


class StatusInput(BaseModel):
    status: str


@router.get("")
async def list_orders(user=Depends(get_current_user)):
    orders = await db.manufacturing_orders.find().sort("created_at", -1).to_list(500)
    return clean(orders)


@router.get("/{oid}")
async def get_order(oid: str, user=Depends(get_current_user)):
    o = await db.manufacturing_orders.find_one({"id": oid})
    if not o:
        raise HTTPException(404, "Order not found")
    return clean(o)


@router.post("")
async def create_order(data: MOInput, user=Depends(get_current_user)):
    count = await db.manufacturing_orders.count_documents({})
    order = {
        "id": gen_id(),
        "mo_code": f"MO-{count + 1:05d}",
        **data.model_dump(),
        "status": "Queued",
        "deliverables": [],
        "approval_history": [{"stage": "Created", "by": user["name"], "at": now_iso()}],
        "created_by": user["name"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.manufacturing_orders.insert_one(dict(order))
    return clean(order)


@router.put("/{oid}")
async def update_order(oid: str, data: MOInput, user=Depends(get_current_user)):
    o = await db.manufacturing_orders.find_one({"id": oid})
    if not o:
        raise HTTPException(404, "Not found")
    await db.manufacturing_orders.update_one({"id": oid}, {"$set": {**data.model_dump(), "updated_at": now_iso()}})
    return clean(await db.manufacturing_orders.find_one({"id": oid}))


@router.patch("/{oid}/status")
async def update_status(oid: str, data: StatusInput, user=Depends(get_current_user)):
    if data.status not in STAGES:
        raise HTTPException(400, "Invalid stage")
    o = await db.manufacturing_orders.find_one({"id": oid})
    if not o:
        raise HTTPException(404, "Not found")
    history = o.get("approval_history", [])
    history.append({"stage": data.status, "by": user["name"], "at": now_iso()})
    await db.manufacturing_orders.update_one(
        {"id": oid}, {"$set": {"status": data.status, "approval_history": history, "updated_at": now_iso()}})
    return clean(await db.manufacturing_orders.find_one({"id": oid}))


@router.delete("/{oid}")
async def delete_order(oid: str, user=Depends(get_current_user)):
    await db.manufacturing_orders.delete_one({"id": oid})
    return {"message": "deleted"}
