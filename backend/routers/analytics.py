from fastapi import APIRouter, Depends
from database import db
from auth import get_current_user
from models import clean

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/dashboard/stats")
async def dashboard_stats(user=Depends(get_current_user)):
    kr_total = await db.knowledge_records.count_documents({})
    kr_verified = await db.knowledge_records.count_documents({"verification_status": "Verified"})
    mo_total = await db.manufacturing_orders.count_documents({})
    mo_active = await db.manufacturing_orders.count_documents({"status": {"$nin": ["Published"]}})
    prod_total = await db.products.count_documents({})
    prod_published = await db.products.count_documents({"status": "Published"})
    employees = await db.digital_employees.count_documents({})
    customers = await db.customers.count_documents({})

    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    mo_by_stage = await db.manufacturing_orders.aggregate(pipeline).to_list(50)
    stage_map = {r["_id"]: r["count"] for r in mo_by_stage}

    recent = await db.activities.find().sort("created_at", -1).to_list(8)

    return {
        "knowledge_records": kr_total,
        "verified_records": kr_verified,
        "manufacturing_orders": mo_total,
        "active_orders": mo_active,
        "products": prod_total,
        "published_products": prod_published,
        "digital_employees": employees,
        "customers": customers,
        "pipeline": stage_map,
        "recent_activity": clean(recent),
    }


@router.get("/analytics/overview")
async def analytics_overview(user=Depends(get_current_user)):
    kr_by_cat = await db.knowledge_records.aggregate(
        [{"$group": {"_id": "$category", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]).to_list(20)
    prod_by_type = await db.products.aggregate(
        [{"$group": {"_id": "$product_type", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]).to_list(30)
    mo_by_stage = await db.manufacturing_orders.aggregate(
        [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]).to_list(20)
    employees = await db.digital_employees.find({}, {"name": 1, "tasks_completed": 1, "performance": 1}).to_list(50)

    # synthetic knowledge growth trend
    total = await db.knowledge_records.count_documents({})
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    base = max(total - 5, 1)
    growth = [{"month": m, "records": base + i * 3 + (total if i == 5 else 0) // 2} for i, m in enumerate(months)]

    return {
        "knowledge_by_category": [{"name": r["_id"], "value": r["count"]} for r in kr_by_cat],
        "products_by_type": [{"name": r["_id"], "value": r["count"]} for r in prod_by_type],
        "orders_by_stage": [{"name": r["_id"], "value": r["count"]} for r in mo_by_stage],
        "employee_performance": [
            {"name": e["name"], "tasks": e.get("tasks_completed", 0), "performance": e.get("performance", 100)}
            for e in clean(employees)
        ],
        "knowledge_growth": growth,
    }
