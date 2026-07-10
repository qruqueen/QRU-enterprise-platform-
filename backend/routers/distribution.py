"""QRU Universal Distribution Framework™ — API surface (MO-007).

One consistent workflow across every channel: distribute → verify → store external IDs → analytics.
Treasure Standard™: connectors never report success without a real external ID.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import os

from database import db
from auth import get_current_user, require_super_admin
from distribution import engines
from distribution.connectors import save_connector_credentials

router = APIRouter(prefix="/api/distribution", tags=["distribution"])

# Connectors that accept Founder-supplied credentials + the fields they require.
CONFIGURABLE = {
    "wordpress": {"fields": ["site_url", "username", "app_password"], "secret": ["app_password"]},
}

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rendered_assets", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/connectors")
async def connectors(user=Depends(get_current_user)):
    items = await engines.list_connectors()
    for c in items:
        c["configurable"] = c["id"] in CONFIGURABLE
        if c["id"] in CONFIGURABLE:
            c["config_fields"] = CONFIGURABLE[c["id"]]["fields"]
    return {"connectors": items}


class ConfigInput(BaseModel):
    credentials: dict


@router.post("/connectors/{connector_id}/config")
async def configure(connector_id: str, data: ConfigInput, user=Depends(require_super_admin)):
    if connector_id not in CONFIGURABLE:
        raise HTTPException(400, "This connector is not configurable via credentials.")
    spec = CONFIGURABLE[connector_id]
    missing = [f for f in spec["fields"] if not (data.credentials or {}).get(f)]
    if missing:
        raise HTTPException(400, f"Missing required fields: {', '.join(missing)}")
    await save_connector_credentials(connector_id, data.credentials, tuple(spec["secret"]))
    return {"configured": True, "connector_id": connector_id}


class Target(BaseModel):
    connector_id: str
    mode: str = "private"
    options: Optional[dict] = None


class DistributeInput(BaseModel):
    product_id: str
    targets: List[Target]


@router.post("/distribute")
async def distribute(data: DistributeInput, user=Depends(require_super_admin)):
    targets = [{"connector_id": t.connector_id, "mode": t.mode, "options": t.options or {}} for t in data.targets]
    result = await engines.distribute(data.product_id, targets, user["name"])
    if result.get("error"):
        raise HTTPException(400, result["error"])
    return result


@router.get("/jobs")
async def jobs(product_id: Optional[str] = None, user=Depends(get_current_user)):
    return {"jobs": await engines.list_jobs(product_id)}


@router.post("/jobs/{job_id}/retry")
async def retry(job_id: str, user=Depends(require_super_admin)):
    res = await engines.retry_job(job_id)
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.post("/jobs/{job_id}/verify")
async def verify(job_id: str, user=Depends(get_current_user)):
    res = await engines.verify_job(job_id)
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.get("/jobs/{job_id}/analytics")
async def analytics(job_id: str, user=Depends(get_current_user)):
    return await engines.job_analytics(job_id)


# --- File upload for file-based connectors (e.g. YouTube video) — chunked to bypass proxy limits.
class InitInput(BaseModel):
    filename: str
    kind: str = "video"


@router.post("/upload/init")
async def upload_init(data: InitInput, user=Depends(require_super_admin)):
    ext = os.path.splitext(data.filename or "")[1].lower() or (".mp4" if data.kind == "video" else ".bin")
    upload_id = f"{data.kind}_{os.urandom(8).hex()}{ext}"
    open(os.path.join(UPLOAD_DIR, upload_id), "wb").close()
    return {"upload_id": upload_id}


@router.post("/upload/chunk")
async def upload_chunk(request: Request, upload_id: str, user=Depends(require_super_admin)):
    path = os.path.join(UPLOAD_DIR, os.path.basename(upload_id))
    if not os.path.exists(path):
        raise HTTPException(404, "Upload session not found.")
    body = await request.body()
    with open(path, "ab") as f:
        f.write(body)
    return {"received": len(body), "total": os.path.getsize(path)}
