"""QRU AI Services Manager™ — API surface (AI Services Division™)."""
from fastapi import APIRouter, Depends

from database import db
from auth import get_current_user
from models import clean
import ai_services_manager as ai

router = APIRouter(prefix="/api/ai-services", tags=["ai-services"])


@router.get("/status")
async def status(user=Depends(get_current_user)):
    return await ai.status_summary()


@router.get("/jobs")
async def jobs(limit: int = 100, user=Depends(get_current_user)):
    return clean(await db.ai_service_jobs.find().sort("at", -1).to_list(limit))
