"""QRU Decoder Engine™ — API (Stone 1). Founder Review Shelf™ owns Decoder educational review."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from auth import get_current_user, require_super_admin
import decoder_engine as de
import media_division as md

router = APIRouter(prefix="/api/decoder", tags=["decoder"])


@router.get("/taxonomy")
async def taxonomy(user=Depends(get_current_user)):
    return de.TAXONOMY


@router.get("/stats")
async def stats(user=Depends(get_current_user)):
    return await de.stats()


@router.get("/verified-krs")
async def verified_krs(user=Depends(get_current_user)):
    return {"records": await md.verified_krs()}


@router.get("/shelf")
async def shelf(state: Optional[str] = None, user=Depends(get_current_user)):
    return {"decoders": await de.shelf(state)}


@router.get("/needs-attention")
async def needs_attention(user=Depends(get_current_user)):
    return {"decoders": await de.needs_attention()}


@router.get("/{did}")
async def get_one(did: str, user=Depends(get_current_user)):
    d = await de.get_decoder(did)
    if not d:
        raise HTTPException(404, "Decoder Record not found.")
    return d


class DecodeInput(BaseModel):
    kr_id: str
    audience: Optional[str] = ""
    level: Optional[str] = ""


@router.post("/decode")
async def decode(data: DecodeInput, user=Depends(get_current_user)):
    res = await de.decode(data.kr_id, data.audience or "", data.level or "", user["name"])
    if not res.get("ok"):
        raise HTTPException(400, res.get("error", "Decoding failed."))
    return res


class RevisionInput(BaseModel):
    notes: Optional[str] = ""


@router.post("/{did}/approve")
async def approve(did: str, user=Depends(require_super_admin)):
    r = await de.approve(did, user.get("name", "Founder"))
    if not r:
        raise HTTPException(404, "Decoder Record not found.")
    return r


@router.post("/{did}/request-revision")
async def request_revision(did: str, data: RevisionInput, user=Depends(require_super_admin)):
    r = await de.request_revision(did, user.get("name", "Founder"), data.notes or "")
    if not r:
        raise HTTPException(404, "Decoder Record not found.")
    return r


@router.post("/{did}/archive")
async def archive(did: str, user=Depends(require_super_admin)):
    r = await de.archive(did, user.get("name", "Founder"))
    if not r:
        raise HTTPException(404, "Decoder Record not found.")
    return r


@router.post("/{did}/certify-treasure")
async def certify_treasure(did: str, user=Depends(require_super_admin)):
    r = await de.certify_treasure(did, user.get("name", "Founder"))
    if not r:
        raise HTTPException(404, "Decoder Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r



class CreateProductInput(BaseModel):
    product_type: Optional[str] = "Book"


@router.get("/product-types/available")
async def product_types_available(user=Depends(get_current_user)):
    """Product families the Create-Product bridge can manufacture from an understanding."""
    return {"product_types": de.available_product_types()}


@router.post("/{did}/create-product")
async def create_product(did: str, request: Request, data: CreateProductInput = CreateProductInput(),
                         user=Depends(require_super_admin)):
    """Create Product — the single bridge from a Manufacturing Ready™ understanding into a product.
    Book → the 7-button Book Manufacturing line; every other document family → the shared products
    pipeline, inheriting the QRU Publication Quality Standard™ (Phase 2). Knowledge-First preserved."""
    d = await de.get_decoder(did)
    if not d:
        raise HTTPException(404, "Understanding record not found.")
    base_url = str(request.base_url).rstrip("/")
    res = await de.create_product_from_decoder(d, data.product_type or "Book",
                                               user.get("name", "Founder"), base_url)
    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(400, res["error"])
    return res
