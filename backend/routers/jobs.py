from fastapi import APIRouter, Depends, HTTPException

from database import db
from auth import get_current_user
from models import clean
from manufacturing_engine import ALL_FIELDS, METHODOLOGY_FIELDS, LIST_FIELDS, BATCHES

router = APIRouter(prefix="/api/manufacturing-jobs", tags=["jobs"])


@router.get("")
async def list_jobs(active: bool = False, user=Depends(get_current_user)):
    query = {"status": "running"} if active else {}
    jobs = await db.manufacturing_jobs.find(query).sort("created_at", -1).to_list(50)
    return clean(jobs)


@router.get("/schema")
async def schema(user=Depends(get_current_user)):
    """Field manufacturing schema for the frontend renderer."""
    groups = []
    groups.append({"label": "Core Understanding", "fields": METHODOLOGY_FIELDS})
    for label, kind, spec in BATCHES:
        if spec:
            groups.append({"label": label, "fields": list(spec.keys())})
    return {"groups": groups, "list_fields": list(LIST_FIELDS), "all_fields": ALL_FIELDS}


@router.get("/{jid}")
async def get_job(jid: str, user=Depends(get_current_user)):
    job = await db.manufacturing_jobs.find_one({"id": jid})
    if not job:
        raise HTTPException(404, "Job not found")
    return clean(job)
