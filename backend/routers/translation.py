from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user
from models import gen_id
from ai_service import llm_generate, parse_json, QRU_METHODOLOGY_SYSTEM
import translation_pipeline as tp

router = APIRouter(prefix="/api/translation-engine", tags=["translation"])


class TranslateInput(BaseModel):
    content: str
    title: Optional[str] = ""


@router.post("")
async def translate(data: TranslateInput, user=Depends(get_current_user)):
    """Legacy: transform pasted technical content into the full QRU methodology (single prompt)."""
    prompt = f"Title: {data.title or 'Untitled'}\nTechnical content to transform:\n{data.content}"
    raw = await llm_generate(QRU_METHODOLOGY_SYSTEM, prompt, f"engine-{gen_id()}")
    result = parse_json(raw) or {}
    return {"result": result}


@router.get("/stages")
async def stages(user=Depends(get_current_user)):
    return {"stages": tp.STAGES, "audiences": list(tp.AUDIENCES.keys())}


class ManufactureInput(BaseModel):
    question: str
    audience: Optional[str] = None
    resume_from: Optional[str] = None
    context: Optional[dict] = None


@router.post("/manufacture")
async def manufacture(data: ManufactureInput, user=Depends(get_current_user)):
    """QRU Translation Engine™ manufacturing workflow — plain-language question → Treasure Standard™ understanding."""
    return await tp.run(data.question, audience=data.audience, resume_from=data.resume_from, context=data.context)
