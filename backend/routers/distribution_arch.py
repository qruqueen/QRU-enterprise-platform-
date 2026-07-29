"""QRU Distribution Architecture™ — Phase 0 API (Founder/Admin)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import require_super_admin, get_current_user
import distribution_architecture as da

router = APIRouter(prefix="/api/distribution-architecture", tags=["distribution-architecture"])


class RegisterExperienceInput(BaseModel):
    id: str
    name: str
    description: str = ""
    icon: str = "boxes"
    audience: str = ""
    public: bool = True


@router.get("/experiences")
async def experiences(user=Depends(get_current_user)):
    return {"experiences": await da.list_experiences()}


@router.post("/experiences")
async def register(body: RegisterExperienceInput, user=Depends(require_super_admin)):
    return await da.register_experience(
        body.id, body.name, body.description, body.icon, body.audience, body.public,
        actor=user.get("name", "Founder"))


@router.get("/destinations-map")
async def destinations_map(user=Depends(get_current_user)):
    return await da.destinations_map()


@router.get("/resolve/{product_type}")
async def resolve(product_type: str, user=Depends(get_current_user)):
    return {"product_type": product_type,
            "recommended": da.recommend_destinations(product_type)}


_TARGET_COLL = {"product": "products", "book": "book_records"}


class OverrideInput(BaseModel):
    target: str            # "product" | "book"
    id: str
    experiences: list = [] # empty list clears the override (back to auto)


@router.get("/destinations")
async def destinations(target: str, id: str, user=Depends(get_current_user)):
    """Current + recommended destinations for one product/book, for the Publish screen preview."""
    from database import db
    coll = _TARGET_COLL.get(target)
    if not coll:
        return {"error": "unknown target"}
    doc = await db[coll].find_one({"id": id}, {"_id": 0})
    if not doc:
        return {"error": "not found"}
    ptype = "Book" if target == "book" else (doc.get("product_type") or "")
    override = ((doc.get("distribution") or {}).get("experiences")) or None
    recommended = da.recommend_destinations(ptype)
    exps = {e["id"]: e["name"] for e in await da.list_experiences()}
    return {"product_type": ptype, "recommended": recommended,
            "current": override or recommended, "overridden": bool(override),
            "experiences": [{"id": k, "name": v} for k, v in exps.items()]}


@router.post("/destinations")
async def set_destinations(body: OverrideInput, user=Depends(require_super_admin)):
    """Founder override of a product's/book's destinations (empty list = revert to auto)."""
    from database import db
    from models import now_iso
    coll = _TARGET_COLL.get(body.target)
    if not coll:
        return {"error": "unknown target"}
    if body.experiences:
        upd = {"$set": {"distribution.experiences": body.experiences,
                        "distribution.auto_assigned": False, "distribution.assigned_at": now_iso()}}
    else:
        upd = {"$unset": {"distribution.experiences": "", "distribution.auto_assigned": ""}}
    r = await db[coll].update_one({"id": body.id}, upd)
    if not r.matched_count:
        return {"error": "not found"}
    return {"ok": True, "overridden": bool(body.experiences)}
