"""QRU Governance™ — master Constitution + governance aggregator (read-only + workflow)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
import constitution as const

router = APIRouter(prefix="/api/governance", tags=["governance"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await const.governance_overview()


@router.get("/constitution")
async def get_constitution(user=Depends(get_current_user)):
    return await const.get_constitution()


@router.get("/constitution/version-history")
async def version_history(user=Depends(get_current_user)):
    return {"active": await const.active_version(), "history": await const.version_history()}


class ProposalInput(BaseModel):
    article: str
    proposed_change: str
    rationale: str


@router.post("/constitution/proposals")
async def propose(data: ProposalInput, user=Depends(get_current_user)):
    return await const.propose_change(data.article, data.proposed_change, data.rationale, user["name"])


@router.get("/constitution/proposals")
async def proposals(user=Depends(get_current_user)):
    return await const.list_proposals()
