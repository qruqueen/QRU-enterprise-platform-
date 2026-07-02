from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from database import db
from auth import get_current_user, require_roles, hash_password, public_user
from models import gen_id, now_iso, clean, ROLES

# ---------- Customers & Licensing ----------
customers_router = APIRouter(prefix="/api/customers", tags=["customers"])


class CustomerInput(BaseModel):
    name: str
    email: str
    organization: Optional[str] = ""
    type: Optional[str] = "Individual"
    license_tier: Optional[str] = "Standard"


@customers_router.get("")
async def list_customers(user=Depends(get_current_user)):
    return clean(await db.customers.find().sort("created_at", -1).to_list(500))


@customers_router.post("")
async def create_customer(data: CustomerInput, user=Depends(get_current_user)):
    c = {"id": gen_id(), **data.model_dump(), "status": "Active",
         "products_licensed": 0, "created_at": now_iso()}
    await db.customers.insert_one(dict(c))
    return clean(c)


@customers_router.delete("/{cid}")
async def delete_customer(cid: str, user=Depends(get_current_user)):
    await db.customers.delete_one({"id": cid})
    return {"message": "deleted"}


# ---------- Notifications ----------
notif_router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@notif_router.get("")
async def list_notifications(user=Depends(get_current_user)):
    return clean(await db.notifications.find().sort("created_at", -1).to_list(100))


@notif_router.patch("/{nid}/read")
async def mark_read(nid: str, user=Depends(get_current_user)):
    await db.notifications.update_one({"id": nid}, {"$set": {"read": True}})
    return {"message": "ok"}


# ---------- Health University ----------
health_router = APIRouter(prefix="/api/health-university", tags=["health"])


@health_router.get("/colleges")
async def colleges(user=Depends(get_current_user)):
    return clean(await db.health_colleges.find().to_list(50))


# ---------- Global Search ----------
search_router = APIRouter(prefix="/api/search", tags=["search"])


@search_router.get("")
async def global_search(q: str, user=Depends(get_current_user)):
    regex = {"$regex": q, "$options": "i"}
    krs = await db.knowledge_records.find(
        {"$or": [{"title": regex}, {"verified_truth": regex}, {"category": regex}]}).to_list(20)
    mos = await db.manufacturing_orders.find({"$or": [{"topic": regex}, {"mo_code": regex}]}).to_list(20)
    prods = await db.products.find({"$or": [{"title": regex}, {"topic": regex}]}, {"content": 0}).to_list(20)
    emps = await db.digital_employees.find({"$or": [{"name": regex}, {"title": regex}]}).to_list(20)
    return {
        "knowledge_records": clean(krs),
        "manufacturing_orders": clean(mos),
        "products": clean(prods),
        "digital_employees": clean(emps),
    }


# ---------- User Management ----------
users_router = APIRouter(prefix="/api/users", tags=["users"])


class UserInput(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str


@users_router.get("")
async def list_users(user=Depends(require_roles("Administrator", "Executive"))):
    users = await db.users.find({}, {"password_hash": 0}).to_list(500)
    return clean(users)


@users_router.get("/roles")
async def roles():
    return {"roles": ROLES}


@users_router.post("")
async def create_user(data: UserInput, user=Depends(require_roles("Administrator"))):
    if await db.users.find_one({"email": data.email.lower()}):
        raise HTTPException(400, "Email already registered")
    role = data.role if data.role in ROLES else "Customer"
    u = {"id": gen_id(), "email": data.email.lower(), "password_hash": hash_password(data.password),
         "name": data.name, "role": role, "avatar": None, "created_at": now_iso()}
    await db.users.insert_one(u)
    return public_user(u)


@users_router.delete("/{uid}")
async def delete_user(uid: str, user=Depends(require_roles("Administrator"))):
    target = await db.users.find_one({"id": uid})
    if target and target.get("role") == "Administrator":
        raise HTTPException(400, "Cannot delete an administrator")
    await db.users.delete_one({"id": uid})
    return {"message": "deleted"}
