"""QRU Bulk Library Import™ — API surface."""
from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import List, Optional

from auth import get_current_user
import library_import as li

router = APIRouter(prefix="/api/library-import", tags=["library-import"])


@router.post("/analyze")
async def analyze(files: List[UploadFile] = File(...), user=Depends(get_current_user)):
    payload = [(f.filename, await f.read()) for f in files]
    report = await li.analyze(payload)
    return {
        "report": report,
        "new_count": sum(1 for r in report if r["status"] == "new"),
        "duplicate_count": sum(1 for r in report if r["status"] == "duplicate"),
        "skipped_count": sum(1 for r in report if r["status"] in ("empty", "unsupported")),
    }


@router.post("/commit")
async def commit(files: List[UploadFile] = File(...),
                 selected: Optional[str] = Form(None),
                 user=Depends(get_current_user)):
    payload = [(f.filename, await f.read()) for f in files]
    only = [s for s in selected.split("||") if s] if selected else None
    return await li.commit(payload, user["name"], only)
