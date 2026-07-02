from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user
from models import gen_id
from ai_service import llm_generate, parse_json, QRU_METHODOLOGY_SYSTEM

router = APIRouter(prefix="/api/translation-engine", tags=["translation"])


class TranslateInput(BaseModel):
    content: str
    title: Optional[str] = ""


@router.post("")
async def translate(data: TranslateInput, user=Depends(get_current_user)):
    """QRU Translation Engine™ — transform any technical content into the full QRU methodology."""
    prompt = f"Title: {data.title or 'Untitled'}\nTechnical content to transform:\n{data.content}"
    raw = await llm_generate(QRU_METHODOLOGY_SYSTEM, prompt, f"engine-{gen_id()}")
    result = parse_json(raw) or {}
    return {"result": result}
