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
