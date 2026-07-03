"""QRU Institutional Knowledge System™ (QIKS) — enterprise memory & standards registry."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
import qiks

router = APIRouter(prefix="/api/qiks", tags=["institutional-knowledge"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await qiks.dashboard()


@router.get("/standards")
async def standards(category: str | None = None, status: str | None = None, q: str | None = None, user=Depends(get_current_user)):
    items = await qiks.list_standards(category, status, q)
    return {"count": len(items), "standards": items}


@router.get("/search")
async def search(q: str, user=Depends(get_current_user)):
    stds = await qiks.list_standards(q=q)
    lessons = [l for l in await qiks.list_lessons() if q.lower() in (l["title"] + l["lesson"] + l["division"]).lower()]
    return {"query": q, "standards": stds, "lessons": lessons, "total": len(stds) + len(lessons)}


@router.get("/graph")
async def graph(user=Depends(get_current_user)):
    return await qiks.knowledge_graph()


@router.get("/lessons")
async def lessons(division: str | None = None, user=Depends(get_current_user)):
    items = await qiks.list_lessons(division)
    return {"count": len(items), "lessons": items}


@router.get("/standards/{sid}")
async def standard(sid: str, user=Depends(get_current_user)):
    s = await qiks.get_standard(sid)
    if not s:
        raise HTTPException(404, "Standard not found")
    return s


class StandardInput(BaseModel):
    name: str
    category: str
    description: str
    purpose: str


@router.post("/standards")
async def create(data: StandardInput, user=Depends(get_current_user)):
    return await qiks.create_standard(data.name, data.category, data.description, data.purpose, user["name"])


class PromoteInput(BaseModel):
    founder_approval: bool = False


@router.post("/standards/{sid}/promote")
async def promote(sid: str, data: PromoteInput, user=Depends(get_current_user)):
    s = await qiks.promote_standard(sid, user["name"], data.founder_approval)
    if not s:
        raise HTTPException(404, "Standard not found")
    return s


class ReviseInput(BaseModel):
    changes: dict
    reason: str
    founder_approval: bool = True


@router.put("/standards/{sid}")
async def revise(sid: str, data: ReviseInput, user=Depends(get_current_user)):
    s = await qiks.revise_standard(sid, data.changes, data.reason, user["name"], data.founder_approval)
    if not s:
        raise HTTPException(404, "Standard not found")
    return s


class LessonInput(BaseModel):
    title: str
    division: str
    lesson: str
    source: str = "Manual entry"


@router.post("/lessons")
async def add_lesson(data: LessonInput, user=Depends(get_current_user)):
    return await qiks.add_lesson(data.title, data.division, data.lesson, data.source, user["name"])
