"""QRU Enterprise Refinement Initiative™ API (STD-RFN-0001)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user
import refinement_engine as rf

router = APIRouter(prefix="/api/refinement", tags=["refinement"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return rf.overview()


@router.get("/learning")
async def learning(user=Depends(get_current_user)):
    return await rf.learning_summary()


class KnowledgeOrder(BaseModel):
    topic: str


@router.post("/knowledge")
async def knowledge(data: KnowledgeOrder, user=Depends(get_current_user)):
    if not data.topic.strip():
        raise HTTPException(400, "Topic required.")
    return await rf.manufacture_knowledge(data.topic.strip(), user.get("name", "Founder"))


@router.get("/knowledge")
async def list_knowledge(user=Depends(get_current_user)):
    rows = [r async for r in rf.db.knowledge_engine_records.find({}, {"_id": 0}).sort("created_at", -1).limit(50)]
    return {"records": rows}


class ProductOrder(BaseModel):
    kr_id: str
    product_type: str


@router.post("/product")
async def product(data: ProductOrder, user=Depends(get_current_user)):
    p = await rf.manufacture_product(data.kr_id, data.product_type, user.get("name", "Founder"))
    if p is None:
        raise HTTPException(404, "Knowledge Record not found.")
    return p


@router.get("/products")
async def list_products(user=Depends(get_current_user)):
    rows = [r async for r in rf.db.engine_products.find({}, {"_id": 0}).sort("created_at", -1).limit(80)]
    return {"products": rows}


@router.post("/benchmark")
async def benchmark(user=Depends(get_current_user)):
    return await rf.run_benchmark(user.get("name", "Founder"))


# ── QRU Verify & Promote™ Workflow ──────────────────────────────────────────
@router.get("/kr/{kr_id}/claims")
async def kr_claims(kr_id: str, user=Depends(get_current_user)):
    res = await rf.kr_claims(kr_id)
    if res is None:
        raise HTTPException(404, "Knowledge Record not found.")
    return res


@router.get("/kr/{kr_id}/lineage")
async def kr_lineage(kr_id: str, user=Depends(get_current_user)):
    return await rf.kr_lineage(kr_id)


class ClaimSource(BaseModel):
    source_id: Optional[str] = None
    claim_id: Optional[str] = None
    title: Optional[str] = ""
    url: Optional[str] = ""
    publisher: Optional[str] = ""
    approved: bool = False


class VerifyPromoteOrder(BaseModel):
    kr_id: str
    sources: list[ClaimSource] = []
    human_approved: bool = False


@router.post("/verify-promote")
async def verify_promote(data: VerifyPromoteOrder, user=Depends(get_current_user)):
    res = await rf.verify_and_promote(
        data.kr_id, [s.dict() for s in data.sources], data.human_approved, user.get("name", "Founder"))
    if res is None:
        raise HTTPException(404, "Knowledge Record not found.")
    return res
