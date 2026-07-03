"""QRU Enterprise Workflow Engine™ — API surface (templates, jobs, monitor, FAT)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import db
from auth import get_current_user
from models import clean
import workflow_engine as wf

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


@router.get("/templates")
async def templates(user=Depends(get_current_user)):
    return {"templates": wf.templates_public(), "stages": wf.STAGES}


class RunInput(BaseModel):
    template: str
    topic: Optional[str] = None
    kr_id: Optional[str] = None
    division: Optional[str] = None


@router.post("/run")
async def run(data: RunInput, user=Depends(get_current_user)):
    job, err = await wf.start_workflow(data.template, topic=data.topic, kr_id=data.kr_id,
                                       division=data.division, owner_id=user["id"], actor=user["name"])
    if err:
        raise HTTPException(400, err)
    return job


@router.get("/jobs")
async def jobs(limit: int = 50, user=Depends(get_current_user)):
    return clean(await db.workflow_jobs.find().sort("created_at", -1).to_list(limit))


@router.get("/jobs/{job_id}")
async def job_detail(job_id: str, user=Depends(get_current_user)):
    j = await db.workflow_jobs.find_one({"id": job_id})
    if not j:
        raise HTTPException(404, "Job not found")
    return clean(j)


@router.get("/monitor")
async def monitor(user=Depends(get_current_user)):
    return await wf.factory_monitor()


@router.post("/factory-acceptance-test")
async def fat(user=Depends(get_current_user)):
    job, err = await wf.run_factory_acceptance_test(user["id"], user["name"])
    if err:
        raise HTTPException(400, err)
    return job


@router.get("/factory-acceptance-test/{job_id}")
async def fat_result(job_id: str, user=Depends(get_current_user)):
    res = await wf.evaluate_fat(job_id)
    if not res:
        raise HTTPException(404, "FAT job not found")
    return res
