"""QRU Product Family Assembly™ — API. One Verified source + one Manufacturing Intent™ → a product
family, orchestrated over the existing create-product bridge. Read-only preview + super-admin assemble."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from auth import get_current_user, require_super_admin
import family_assembly as fa
import manufacturing_intents as intents
import decoder_engine as de

router = APIRouter(prefix="/api/family", tags=["product-family"])


@router.get("/intents")
async def get_intents(user=Depends(get_current_user)):
    return {"intents": intents.list_intents(),
            "available_families": de.available_product_types()}


@router.get("/eligible-sources")
async def eligible_sources(user=Depends(get_current_user)):
    """Manufacturing-eligible understandings (trace to a Verified UKR) usable as a family source."""
    rows = await de.shelf(None)
    out = [{"decoder_id": d.get("decoder_id"), "title": d.get("title"),
            "review_state": d.get("review_state"), "domain": d.get("domain"),
            "audience": d.get("audience"), "source_kr_ids": d.get("source_kr_ids", [])}
           for d in rows if d.get("review_state") in de.MANUFACTURING_ELIGIBLE_STATES]
    return {"sources": out}


@router.get("/history")
async def history(user=Depends(get_current_user)):
    return {"families": await fa.list_families()}


@router.get("/preview")
async def preview(decoder_id: str, intent: str, user=Depends(get_current_user)):
    res = await fa.preview(decoder_id, intent)
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


class AssembleInput(BaseModel):
    decoder_id: str
    intent: str
    families: Optional[List[str]] = None
    override_source_gate: Optional[bool] = False


@router.post("/assemble")
async def assemble(data: AssembleInput, request: Request, user=Depends(require_super_admin)):
    base_url = str(request.base_url).rstrip("/")
    res = await fa.assemble(data.decoder_id, data.intent, data.families,
                            user.get("name", "Founder"), base_url,
                            override_source_gate=bool(data.override_source_gate))
    if res.get("error") == "source_verification_failed":
        raise HTTPException(409, detail=res)
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res
