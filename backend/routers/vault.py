"""QRU Asset Vault™ API (MT-027) — Founder upload/import, classification, versioning,
reuse-lookup, and file serving."""
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user
import vault

router = APIRouter(prefix="/api/vault", tags=["vault"])


@router.get("/meta")
async def meta(user=Depends(get_current_user)):
    return vault.meta()


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    name: str = Form(...),
    asset_type: str = Form("Image"),
    source: str = Form("Founder Imported"),
    approval_status: str = Form("Founder Approved"),
    product_family: Optional[str] = Form(None),
    knowledge_record_id: Optional[str] = Form(None),
    character: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    user=Depends(get_current_user),
):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    ext = (file.filename or "").rsplit(".", 1)[-1] if "." in (file.filename or "") else "bin"
    file_info = vault.save_bytes(data, ext)
    asset = await vault.create_asset(
        name=name, asset_type=asset_type, file_info=file_info, source=source,
        approval_status=approval_status, created_by=user["name"],
        knowledge_record_id=knowledge_record_id or None, product_family=product_family or None,
        character=character or None, department=department or None, notes=notes or None)
    return asset


@router.get("/assets")
async def assets(q: str = None, asset_type: str = None, source: str = None,
                 approval_status: str = None, product_family: str = None,
                 character: str = None, knowledge_record_id: str = None,
                 include_archived: bool = False, user=Depends(get_current_user)):
    rows = await vault.list_assets(q=q, asset_type=asset_type, source=source,
                                   approval_status=approval_status, product_family=product_family,
                                   character=character, knowledge_record_id=knowledge_record_id,
                                   include_archived=include_archived)
    return {"assets": rows, "count": len(rows)}


@router.get("/lookup")
async def lookup(asset_type: str = None, product_family: str = None, character: str = None,
                 knowledge_record_id: str = None, department: str = None,
                 user=Depends(get_current_user)):
    hit = await vault.find_reusable(asset_type=asset_type, product_family=product_family,
                                    character=character, knowledge_record_id=knowledge_record_id,
                                    department=department)
    return {"reusable": hit, "found": hit is not None}


class UpdateInput(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    source: Optional[str] = None
    approval_status: Optional[str] = None
    knowledge_record_id: Optional[str] = None
    product_family: Optional[str] = None
    character: Optional[str] = None
    department: Optional[str] = None
    usage_notes: Optional[str] = None
    archived: Optional[bool] = None


@router.patch("/{aid}")
async def update(aid: str, data: UpdateInput, user=Depends(get_current_user)):
    a = await vault.update_asset(aid, {k: v for k, v in data.dict().items() if v is not None})
    if not a:
        raise HTTPException(404, "Asset not found")
    return a


class LinkInput(BaseModel):
    product_id: str


@router.post("/{aid}/link-product")
async def link_product(aid: str, data: LinkInput, user=Depends(get_current_user)):
    a = await vault.link_product(aid, data.product_id)
    if not a:
        raise HTTPException(404, "Asset or product not found")
    return a


@router.post("/{aid}/new-version")
async def new_version(aid: str, file: UploadFile = File(...), reason: str = Form("New version"),
                      approval_status: str = Form("Draft"), user=Depends(get_current_user)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    ext = (file.filename or "").rsplit(".", 1)[-1] if "." in (file.filename or "") else "bin"
    file_info = vault.save_bytes(data, ext)
    a = await vault.add_version(aid, file_info, user["name"], reason, approval_status)
    if not a:
        raise HTTPException(404, "Asset not found")
    return a


@router.get("/{aid}")
async def get_one(aid: str, user=Depends(get_current_user)):
    a = await vault.get_asset(aid)
    if not a:
        raise HTTPException(404, "Asset not found")
    return a


@router.get("/asset/{fname}")
async def serve(fname: str, download: bool = False, name: str = None):
    if "/" in fname or ".." in fname:
        raise HTTPException(400, "Invalid asset name")
    path = os.path.join(vault.VAULT_DIR, fname)
    if not os.path.exists(path):
        raise HTTPException(404, "Asset not found")
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    media = vault.MEDIA_TYPE.get(ext, "application/octet-stream")
    if download:
        safe = "".join(ch for ch in (name or fname) if ch.isalnum() or ch in " ._-").strip() or fname
        if not safe.lower().endswith("." + ext):
            safe = f"{safe}.{ext}"
        return FileResponse(path, media_type=media, filename=safe,
                            headers={"Content-Disposition": f'attachment; filename="{safe}"'})
    return FileResponse(path, media_type=media)
