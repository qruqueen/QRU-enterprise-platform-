"""QRU Educational Design System™ (QEDS) — governance API (read-only + workflow)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
import qeds

router = APIRouter(prefix="/api/qeds", tags=["qeds"])


@router.get("/constitution")
async def constitution(user=Depends(get_current_user)):
    return await qeds.get_constitution()


@router.get("/version-history")
async def version_history(user=Depends(get_current_user)):
    return {"active": await qeds.active_version(), "history": await qeds.version_history()}


@router.get("/methodology-library")
async def methodology_library(user=Depends(get_current_user)):
    return await qeds.methodology_library()


@router.get("/educational-review/{pid}")
async def educational_review(pid: str, user=Depends(get_current_user)):
    res = await qeds.educational_review(pid)
    if not res:
        raise HTTPException(404, "Product not found")
    return res


class ProposalInput(BaseModel):
    section: str
    proposed_change: str
    rationale: str


@router.post("/proposals")
async def propose(data: ProposalInput, user=Depends(get_current_user)):
    return await qeds.propose_change(data.section, data.proposed_change, data.rationale, user["name"])


@router.get("/proposals")
async def proposals(user=Depends(get_current_user)):
    return await qeds.list_proposals()
