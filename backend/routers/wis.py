"""QRU Workforce Identity System™ (WIS) — enterprise source of truth for character identity."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
import character_registry as wis

router = APIRouter(prefix="/api/wis", tags=["workforce-identity"])


@router.get("/characters")
async def characters(user=Depends(get_current_user)):
    chars = await wis.list_characters()
    return {
        "count": len(chars),
        "characters": chars,
        "rule": "Every QRU application must retrieve characters from the Character Library™ — never generate a new generic portrait for an approved character.",
    }


@router.get("/characters/{cid}")
async def character(cid: str, user=Depends(get_current_user)):
    c = await wis.get_character(cid)
    if not c:
        raise HTTPException(404, "Character not found")
    return c


@router.get("/resolve/{query}")
async def resolve(query: str, user=Depends(get_current_user)):
    """Retrieve the approved character for a role/department. Apps call this instead of generating."""
    c = await wis.get_by_role_or_department(query)
    if not c:
        raise HTTPException(404, "No approved character matches this role/department")
    return c


class VariationInput(BaseModel):
    kind: str            # pose | expression | full_body | video_avatar
    description: str
    asset_url: str | None = None


@router.post("/characters/{cid}/variations")
async def create_variation(cid: str, data: VariationInput, user=Depends(get_current_user)):
    """Create a pose/expression variation preserving the approved identity."""
    var = await wis.add_variation(cid, data.kind, data.description, data.asset_url)
    if var is None:
        raise HTTPException(404, "Character not found")
    return {"status": "created", "variation": var, "note": "Approved visual identity preserved."}
