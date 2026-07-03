"""QRU Enterprise Blueprint™ — canonical Department Profiles + the One Question Test™."""
from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
import department_registry as reg

router = APIRouter(prefix="/api/departments", tags=["enterprise-blueprint"])


@router.get("")
async def list_departments(user=Depends(get_current_user)):
    return {
        "count": len(reg.get_departments()),
        "sections": reg.SECTIONS,
        "departments": reg.get_departments(),
        "one_question_rule": reg.ONE_QUESTION_RULE,
    }


@router.get("/questions")
async def questions(user=Depends(get_current_user)):
    """Lightweight map for navigation tooltips / help text."""
    return {"questions": reg.get_questions_map(), "rule": reg.ONE_QUESTION_RULE}


@router.get("/{key}")
async def department(key: str, user=Depends(get_current_user)):
    d = reg.get_department(key)
    if not d:
        raise HTTPException(404, "Department not found")
    return d
