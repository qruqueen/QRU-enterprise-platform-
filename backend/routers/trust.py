"""QRU Trust & Authenticity System™ — API surface (MO-015 / MO-016 / MO-017 + FR-095)."""
from fastapi import APIRouter, Depends, HTTPException, Request

from database import db
from auth import get_current_user, require_super_admin
from models import gen_id, now_iso
import trust_authenticity as ta

router = APIRouter(prefix="/api/trust", tags=["trust"])


def _clean(doc):
    doc.pop("_id", None)
    return doc


def _base_url(request: Request):
    return str(request.base_url).rstrip("/")


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return ta.config()


async def _load(product_id):
    p = await db.products.find_one({"id": product_id}) or await db.products.find_one({"product_code": product_id})
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@router.get("/certificate/{product_id}")
async def certificate(product_id: str, request: Request, user=Depends(get_current_user)):
    p = await _load(product_id)
    return await ta.authenticity_certificate(p, _base_url(request))


@router.post("/register/{product_id}")
async def register(product_id: str, request: Request, user=Depends(require_super_admin)):
    p = await _load(product_id)
    cert = await ta.authenticity_certificate(p, _base_url(request))
    rec = await ta.registry_record(p)
    doc = {
        "id": gen_id(), "product_id": p["id"], "product_code": p.get("product_code"),
        "title": p.get("title"), "registry": rec, "certificate_id": cert["authenticity_certificate"],
        "verify_url": cert["verify_url"], "registered_by": user["name"], "registered_at": now_iso(),
    }
    await db.trust_registry.update_one({"product_id": p["id"]}, {"$set": doc}, upsert=True)
    return _clean(doc)


@router.get("/registry")
async def registry(user=Depends(get_current_user)):
    rows = await db.trust_registry.find({}).sort("registered_at", -1).to_list(500)
    return {"records": [_clean(r) for r in rows]}


@router.get("/verify/{qru_product_id}")
async def verify(qru_product_id: str):
    """PUBLIC authenticity lookup (MO-016 public_lookup) — returns certificate summary, never content."""
    p = await db.products.find_one({"product_code": qru_product_id}, {"content": 0})
    if not p:
        return {"found": False, "qru_product_id": qru_product_id,
                "message": "No QRU product is registered under this ID. It may be counterfeit or unpublished."}
    registered = await db.trust_registry.find_one({"product_id": p["id"]})
    return {
        "found": True, "qru_product_id": qru_product_id, "title": p.get("title"),
        "author": ta.COPYRIGHT_HOLDER, "qruseal": ta.QRU_SEAL,
        "treasure_standard_status": ta.treasure_status(p),
        "gold_standard_status": ta.gold_status(p),
        "version": ta._version(p), "release_date": ta._release_date(p),
        "authentic": bool(p.get("verified")),
        "registered": bool(registered),
        "active_status": "Active" if p.get("status") in ("Published", "Listed") else (p.get("status") or "In Manufacturing"),
        "message": "Verified authentic QRU product." if p.get("verified") else "Product exists but has not completed QRU verification.",
    }


@router.get("/platform-plan/{platform}")
async def platform_plan(platform: str, security_level: str = "standard", user=Depends(get_current_user)):
    return ta.platform_protection_plan(platform, security_level)


@router.get("/audit/{product_id}")
async def audit(product_id: str, user=Depends(get_current_user)):
    p = await _load(product_id)
    return await ta.audit_log(p["id"], p.get("product_code"))
