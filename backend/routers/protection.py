"""QRU Product Protection & Verification Agent™ — API surface + Protection Dashboard."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from database import db
from auth import get_current_user, require_super_admin
from models import gen_id, now_iso, clean
import product_protection as pp

router = APIRouter(prefix="/api/protection", tags=["protection"])


@router.get("/licenses")
async def licenses(user=Depends(get_current_user)):
    return {"license_types": pp.LICENSE_TYPES, "copyright_notice": pp.copyright_notice(),
            "default_terms": pp.DEFAULT_LICENSE_TERMS}


@router.get("/dashboard")
async def dashboard(user=Depends(get_current_user)):
    products = await db.products.find({}, {"content": 0}).sort("created_at", -1).to_list(500)
    rows = [pp.dashboard_row(p) for p in products]
    summary = {
        "total": len(rows),
        "verified": sum(1 for r in rows if r["verified"]),
        "protected": sum(1 for r in rows if r["protected"]),
        "published": sum(1 for r in rows if r["publication_status"] == "Published"),
        "at_risk": sum(1 for r in rows if r["risk_flags"]),
    }
    return {"rows": rows, "summary": summary}


@router.post("/{pid}/verify")
async def verify_product(pid: str, user=Depends(get_current_user)):
    result = await pp.ai_verify_product(pid, user["name"])
    if result.get("error"):
        raise HTTPException(404, "Product not found")
    return result


class ProtectInput(BaseModel):
    license_type: str = "Personal Use"
    watermark: bool = True
    access_control: str = "account_required"


@router.post("/{pid}/apply-protection")
async def apply_protection(pid: str, data: ProtectInput, user=Depends(require_super_admin)):
    p = await pp.apply_protection(pid, data.license_type, data.watermark, data.access_control, user["name"])
    if not p:
        raise HTTPException(404, "Product not found")
    return clean({k: v for k, v in p.items() if k != "content"})


class SecureLinkInput(BaseModel):
    customer_id: Optional[str] = "self"
    minutes: Optional[int] = 60


@router.post("/{pid}/secure-link")
async def secure_link(pid: str, data: SecureLinkInput, user=Depends(get_current_user)):
    link, err = await pp.create_secure_link(pid, data.customer_id, min(int(data.minutes or 60), 1440), user["name"])
    if err:
        raise HTTPException(400, err)
    return link


@router.get("/download/{token}")
async def download(token: str):
    """Validate an expiring secure link and return the product (account/purchase gated
    upstream via link issuance). Tracks access for basic anti-sharing."""
    link = await db.product_access_links.find_one({"token": token})
    if not link or link.get("revoked"):
        raise HTTPException(404, "This link is invalid.")
    if datetime.now(timezone.utc).isoformat() > link["expires_at"]:
        raise HTTPException(410, "This download link has expired.")
    if link["access_count"] >= link["max_access"]:
        raise HTTPException(429, "This link has reached its access limit.")
    p = await db.products.find_one({"id": link["product_id"]})
    if not p:
        raise HTTPException(404, "Product not found")
    await db.product_access_links.update_one(
        {"token": token}, {"$inc": {"access_count": 1}, "$set": {"last_access": now_iso()}})
    watermark = (p.get("protection") or {}).get("watermark_applied")
    content = p.get("content") or ""
    footer = f"\n\n---\n{(p.get('protection') or {}).get('copyright_notice', pp.copyright_notice())}"
    if watermark:
        footer += f"\nLicensed via QRU · {p.get('license_type','Personal Use')} · {p.get('product_code')}"
    return {"product_code": p.get("product_code"), "title": p.get("title"),
            "content": content + footer, "license_type": p.get("license_type"),
            "access_number": link["access_count"] + 1, "max_access": link["max_access"]}


class GrantInput(BaseModel):
    product_id: str
    customer_id: str
    license_type: str = "Personal Use"


@router.post("/grant")
async def grant_license(data: GrantInput, user=Depends(require_super_admin)):
    p = await db.products.find_one({"id": data.product_id})
    if not p:
        raise HTTPException(404, "Product not found")
    lt = data.license_type if data.license_type in pp.LICENSE_TYPES else "Personal Use"
    doc = {"id": gen_id(), "product_id": data.product_id, "product_code": p.get("product_code"),
           "customer_id": data.customer_id, "license_type": lt, "rules": pp.LICENSE_TYPES[lt],
           "granted_by": user["name"], "status": "Active", "created_at": now_iso()}
    await db.product_licenses.insert_one(dict(doc))
    return clean(doc)


@router.get("/licenses/granted")
async def granted(user=Depends(get_current_user)):
    return clean(await db.product_licenses.find().sort("created_at", -1).to_list(500))
