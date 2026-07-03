"""QRU Autonomous Enterprise™ (Level 5) — API surface."""
from fastapi import APIRouter, Depends

from auth import get_current_user
import autonomy

router = APIRouter(prefix="/api/autonomy", tags=["autonomy"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await autonomy.overview()


@router.get("/diagnostics")
async def diagnostics(user=Depends(get_current_user)):
    return await autonomy.self_diagnostics()


@router.post("/diagnostics/repair")
async def repair(user=Depends(get_current_user)):
    return await autonomy.auto_repair(user["name"])


@router.get("/health")
async def health(user=Depends(get_current_user)):
    return await autonomy.factory_health()


@router.get("/executive-brief")
async def executive_brief(user=Depends(get_current_user)):
    return await autonomy.executive_brief()


@router.get("/ai-scorecard")
async def ai_scorecard(user=Depends(get_current_user)):
    return await autonomy.ai_scorecard()


@router.get("/capacity")
async def capacity(user=Depends(get_current_user)):
    return await autonomy.capacity_planning()


@router.get("/knowledge-gaps")
async def knowledge_gaps(user=Depends(get_current_user)):
    return await autonomy.knowledge_gaps()


@router.get("/factory-council")
async def factory_council(user=Depends(get_current_user)):
    return await autonomy.factory_council()


@router.get("/enterprise-memory")
async def enterprise_memory(user=Depends(get_current_user)):
    return await autonomy.enterprise_memory()
