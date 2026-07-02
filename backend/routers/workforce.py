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
