from fastapi import APIRouter, Depends, HTTPException

from database import db
from auth import get_current_user
from models import clean

router = APIRouter(prefix="/api/colleges", tags=["colleges"])


@router.get("")
async def list_colleges(division: str = None, user=Depends(get_current_user)):
    query = {"division": division} if division else {}
    colleges = await db.colleges.find(query).sort("name", 1).to_list(100)
    # attach live counts
    result = []
    for c in clean(colleges):
        c["records"] = await db.knowledge_records.count_documents({"category": c["name"]})
        c["products"] = await db.products.count_documents({"family": c["name"]})
        result.append(c)
    return result


@router.get("/divisions")
async def divisions(user=Depends(get_current_user)):
    pipeline = [{"$group": {"_id": "$division", "count": {"$sum": 1}}}, {"$sort": {"_id": 1}}]
    rows = await db.colleges.aggregate(pipeline).to_list(50)
    return [{"division": r["_id"], "colleges": r["count"]} for r in rows]


@router.get("/{cid}/workspace")
async def workspace(cid: str, user=Depends(get_current_user)):
    college = await db.colleges.find_one({"id": cid})
    if not college:
        raise HTTPException(404, "College not found")
    college = clean(college)
    name = college["name"]
    records = await db.knowledge_records.find({"category": name}).sort("created_at", -1).to_list(200)
    products = await db.products.find({"family": name}, {"content": 0}).sort("created_at", -1).to_list(200)
    orders = await db.manufacturing_orders.find(
        {"topic": {"$regex": name.split()[0], "$options": "i"}}).to_list(100)

    prod_by_type = {}
    for p in products:
        prod_by_type.setdefault(p.get("product_type", "Other"), 0)
        prod_by_type[p["product_type"]] += 1

    return {
        "college": college,
        "knowledge_records": clean(records),
        "products": clean(products),
        "manufacturing_orders": clean(orders),
        "product_breakdown": prod_by_type,
        "stats": {
            "records": len(records),
            "verified": sum(1 for r in records if r.get("verification_status") == "Verified"),
            "products": len(products),
            "orders": len(orders),
        },
    }
