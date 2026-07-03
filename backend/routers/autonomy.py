"""QRU Autonomous Enterprise™ (Level 5) — API surface."""
from fastapi import APIRouter, Depends

from auth import get_current_user
import autonomy
import autonomy_ai
from pydantic import BaseModel
from fastapi import HTTPException

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


# ---------------- Enterprise Intelligence™ (LLM-narrated, degrades gracefully) ----------------
@router.get("/improvement-report")
async def improvement_report(user=Depends(get_current_user)):
    return await autonomy_ai.improvement_report()


@router.get("/predictive-manufacturing")
async def predictive_manufacturing(user=Depends(get_current_user)):
    return await autonomy_ai.predictive_manufacturing()


@router.get("/innovation-radar")
async def innovation_radar(user=Depends(get_current_user)):
    return await autonomy_ai.innovation_radar()


@router.get("/executive-brief/narrated")
async def narrated_brief(user=Depends(get_current_user)):
    return await autonomy_ai.narrated_brief(store=False)


@router.get("/product-evolution")
async def evolution_overview(user=Depends(get_current_user)):
    return await autonomy_ai.evolution_overview()


@router.get("/product-evolution/{product_id}")
async def product_evolution(product_id: str, user=Depends(get_current_user)):
    res, err = await autonomy_ai.product_evolution(product_id)
    if err:
        raise HTTPException(404, err)
    return res


class RatingInput(BaseModel):
    rating: int
    review: str = ""


@router.post("/products/{product_id}/rate")
async def rate_product(product_id: str, data: RatingInput, user=Depends(get_current_user)):
    res, err = await autonomy_ai.rate_product(product_id, user, data.rating, data.review)
    if err:
        raise HTTPException(404, err)
    return res
