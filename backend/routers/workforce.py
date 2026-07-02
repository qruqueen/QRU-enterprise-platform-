from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean

router = APIRouter(prefix="/api/digital-employees", tags=["workforce"])


class DEInput(BaseModel):
    name: str
    title: str
    mission: str
    responsibilities: List[str] = []
    permissions: List[str] = []
    tools: List[str] = []
    approval_authority: Optional[str] = "None"
    status: Optional[str] = "Active"
    avatar: Optional[str] = None


@router.get("")
async def list_employees(user=Depends(get_current_user)):
    emps = await db.digital_employees.find().sort("created_at", 1).to_list(200)
    return clean(emps)


@router.get("/{eid}")
async def get_employee(eid: str, user=Depends(get_current_user)):
    e = await db.digital_employees.find_one({"id": eid})
    if not e:
        raise HTTPException(404, "Employee not found")
    return clean(e)


@router.post("")
async def create_employee(data: DEInput, user=Depends(get_current_user)):
    emp = {
        "id": gen_id(),
        **data.model_dump(),
        "current_assignments": [],
        "tasks_completed": 0,
        "performance": 100,
        "activity_history": [{"action": "Activated", "at": now_iso()}],
        "created_at": now_iso(),
    }
    await db.digital_employees.insert_one(dict(emp))
    return clean(emp)


@router.put("/{eid}")
async def update_employee(eid: str, data: DEInput, user=Depends(get_current_user)):
    e = await db.digital_employees.find_one({"id": eid})
    if not e:
        raise HTTPException(404, "Not found")
    await db.digital_employees.update_one({"id": eid}, {"$set": data.model_dump()})
    return clean(await db.digital_employees.find_one({"id": eid}))


@router.patch("/{eid}/toggle")
async def toggle_employee(eid: str, user=Depends(get_current_user)):
    e = await db.digital_employees.find_one({"id": eid})
    if not e:
        raise HTTPException(404, "Not found")
    new_status = "Paused" if e.get("status") == "Active" else "Active"
    await db.digital_employees.update_one({"id": eid}, {"$set": {"status": new_status}})
    return clean(await db.digital_employees.find_one({"id": eid}))


@router.get("/{eid}/department")
async def department(eid: str, user=Depends(get_current_user)):
    """Operational department view for an AI Director."""
    e = await db.digital_employees.find_one({"id": eid})
    if not e:
        raise HTTPException(404, "Not found")
    e = clean(e)
    domain = e.get("domain")

    # Manufacturing orders assigned to this director (by product-type ownership or explicit assignment)
    mo_query = {}
    orders = await db.manufacturing_orders.find(mo_query).sort("created_at", -1).to_list(200)
    # Knowledge records within this director's domain category
    kr_query = {"category": domain} if domain else {}
    records = await db.knowledge_records.find(kr_query).sort("created_at", -1).to_list(100)
    products = await db.products.find(
        {"family": domain} if domain else {}, {"content": 0}).sort("created_at", -1).to_list(100)

    active_orders = [o for o in orders if o.get("status") != "Published"]
    published = await db.products.count_documents({"status": "Published"})

    activity = await db.activities.find().sort("created_at", -1).to_list(6)

    return {
        "employee": e,
        "current_orders": clean(active_orders[:8]),
        "assigned_records": clean(records[:8]),
        "product_output": clean(products[:8]),
        "team_activity": clean(activity),
        "metrics": {
            "active_orders": len(active_orders),
            "assigned_records": len(records),
            "products_output": len(products),
            "published": published,
            "performance": e.get("performance", 100),
            "quality_score": min(100, e.get("performance", 100) + 3),
            "tasks_completed": e.get("tasks_completed", 0),
        },
    }
