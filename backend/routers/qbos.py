"""QRU Brand Operating System™ (QBOS) — governance API (read-only constitution + workflow)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
import qbos

router = APIRouter(prefix="/api/qbos", tags=["qbos"])


@router.get("/constitution")
async def constitution(user=Depends(get_current_user)):
    return await qbos.get_constitution()


@router.get("/version-history")
async def version_history(user=Depends(get_current_user)):
    return {"active": await qbos.active_version(), "history": await qbos.version_history()}


@router.get("/brand-asset-library")
async def brand_asset_library(user=Depends(get_current_user)):
    return await qbos.brand_asset_library()


@router.get("/product-test/{pid}")
async def product_test(pid: str, user=Depends(get_current_user)):
    res = await qbos.product_test(pid)
    if not res:
        raise HTTPException(404, "Product not found")
    return res


class ProposalInput(BaseModel):
    section: str
    proposed_change: str
    rationale: str


@router.post("/proposals")
async def propose(data: ProposalInput, user=Depends(get_current_user)):
    return await qbos.propose_change(data.section, data.proposed_change, data.rationale, user["name"])


@router.get("/proposals")
async def proposals(user=Depends(get_current_user)):
    return await qbos.list_proposals()
