"""QRU Knowledge Record Manufacturing Engine™ — API surface.

Governed by the Approved Knowledge Record Manufacturing Standard™ (KR-STD-0001).
AI drafts; the Founder approves; only then does a record become Verified truth and
enter Enterprise Memory™.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user, require_super_admin
import kr_manufacturing as krm

router = APIRouter(prefix="/api/kr-manufacturing", tags=["kr-manufacturing"])


@router.get("/standard")
async def standard(user=Depends(get_current_user)):
    return {"standard": krm.MANUFACTURING_STANDARD,
            "sources": [{"value": k, "label": v} for k, v in krm.SOURCE_TYPES.items()]}


@router.get("/stats")
async def stats(user=Depends(get_current_user)):
    return await krm.stats()


@router.get("/jobs")
async def jobs(user=Depends(get_current_user)):
    return {"jobs": await krm.list_jobs()}


@router.get("/jobs/{job_id}")
async def job(job_id: str, user=Depends(get_current_user)):
    j = await krm.get_job(job_id)
    if not j:
        raise HTTPException(404, "Job not found.")
    return j


@router.get("/pending-review")
async def pending_review(user=Depends(get_current_user)):
    return {"records": await krm.pending_review()}


class ManufactureInput(BaseModel):
    source_type: str
    topic: str
    category: Optional[str] = ""
    division: Optional[str] = ""
    source_text: Optional[str] = ""
    goal: Optional[str] = ""
    audience: Optional[str] = ""


@router.post("/manufacture")
async def manufacture(data: ManufactureInput, user=Depends(get_current_user)):
    try:
        return await krm.manufacture(
            data.source_type, data.topic, data.category or "", data.division or "",
            data.source_text or "", data.goal or "", data.audience or "", user["name"])
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{kr_id}/approve")
async def approve(kr_id: str, user=Depends(require_super_admin)):
    kr = await krm.approve(kr_id, user.get("name", "Founder"))
    if not kr:
        raise HTTPException(404, "Knowledge Record not found.")
    return kr


class RejectInput(BaseModel):
    reason: Optional[str] = ""


@router.post("/{kr_id}/reject")
async def reject(kr_id: str, data: RejectInput, user=Depends(require_super_admin)):
    kr = await krm.reject(kr_id, user.get("name", "Founder"), data.reason or "")
    if not kr:
        raise HTTPException(404, "Knowledge Record not found.")
    return kr
