"""QRU Standards Audit Exports™ — Founder-accessible download of the preserved read-only audit
(2026 baseline snapshot). Read-only file serving; no governance records touched."""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from auth import require_super_admin

router = APIRouter(prefix="/api/audit", tags=["audit-exports"])

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_exports")
_FILES = {
    "QRU_Standards_Full_Export.json": "application/json",
    "QRU_Standards_Inventory.csv": "text/csv",
    "QRU_Standards_Audit_Findings.md": "text/markdown",
}


@router.get("/exports")
async def list_exports(user=Depends(require_super_admin)):
    out = []
    for name, mime in _FILES.items():
        p = os.path.join(EXPORT_DIR, name)
        if os.path.exists(p):
            out.append({"filename": name, "mime": mime, "size_kb": round(os.path.getsize(p) / 1024, 1),
                        "download_url": f"/api/audit/exports/{name}"})
    return {"exports": out, "note": "Preserved read-only Standards Audit baseline snapshot (iteration 94)."}


@router.get("/exports/{filename}")
async def download_export(filename: str, user=Depends(require_super_admin)):
    if filename not in _FILES:
        raise HTTPException(404, "Unknown audit export.")
    p = os.path.join(EXPORT_DIR, filename)
    if not os.path.exists(p):
        raise HTTPException(404, "Export file not found.")
    return FileResponse(p, media_type=_FILES[filename], filename=filename)
