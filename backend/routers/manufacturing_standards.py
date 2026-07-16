"""QRU Manufacturing Standards™ API — the constitutional spine.
UKR™ (Truth) → PMS™ (Instructions) → PMF™ (Evidence). Deterministic ($0 AI)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import db
from auth import get_current_user, require_super_admin
import ukr_standard as ukr
import manufacturing_foundation as mf

router = APIRouter(prefix="/api/manufacturing", tags=["manufacturing-standards"])


@router.get("/standards")
async def standards(user=Depends(get_current_user)):
    return mf.standards_overview()


@router.get("/foundation")
async def foundation(user=Depends(get_current_user)):
    return mf.FOUNDATION


@router.get("/pms")
async def list_pms(user=Depends(get_current_user)):
    return {"count": len(mf.list_pms()), "standards": mf.list_pms()}


@router.get("/pms/{product_type}")
async def get_pms(product_type: str, user=Depends(get_current_user)):
    pms = mf.get_pms(product_type)
    if not pms:
        raise HTTPException(404, f"No Product Manufacturing Standard™ for '{product_type}'.")
    return pms


@router.get("/pms-gate/{product_type}")
async def pms_gate(product_type: str, user=Depends(get_current_user)):
    ok, res = mf.require_pms(product_type)
    return {"product_type": product_type, "can_manufacture": ok, "detail": res}


@router.get("/ukr/standard")
async def ukr_standard(user=Depends(get_current_user)):
    return ukr.standard()


@router.get("/ukr/registry")
async def ukr_registry(verified_only: bool = False, user=Depends(get_current_user)):
    rows = await ukr.registry(verified_only=verified_only)
    return {"count": len(rows), "schema_version": ukr.SCHEMA_VERSION, "records": rows}


@router.get("/ukr/validate")
async def ukr_validate(user=Depends(get_current_user)):
    docs = await db[ukr.CANONICAL_COLLECTION].find({}, {"_id": 0}).to_list(5000)
    flagged = []
    for d in docs:
        ok, issues = ukr.validate(d)
        if not ok:
            flagged.append({"kr_code": d.get("kr_code"), "knowledge_title": d.get("knowledge_title") or d.get("title"), "issues": issues})
    return {"total": len(docs), "valid": len(docs) - len(flagged), "flagged": len(flagged), "records": flagged[:50]}


@router.post("/ukr/migrate")
async def ukr_migrate(dry_run: bool = False, user=Depends(require_super_admin)):
    return await ukr.migrate_all(actor=user.get("name", "Founder"), dry_run=dry_run)


class PublishInput(BaseModel):
    engine: str
    id: str


@router.post("/publish")
async def publish(data: PublishInput, user=Depends(get_current_user)):
    """SHARED Foundation publish — any product family → QRU Store + PMF™ (one tap)."""
    res = await mf.publish_product(data.engine, data.id, user.get("name", "Founder"))
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.get("/manifest/{engine}/{product_id}")
async def product_manifest(engine: str, product_id: str, user=Depends(get_current_user)):
    """Surface a product's Product Manifest™ (PMF™ = EVIDENCE)."""
    res = await mf.get_or_build_manifest(engine, product_id, user.get("name", "Founder"))
    if res.get("error"):
        raise HTTPException(404, res["error"])
    return res


@router.get("/inheritance-map")
async def inheritance_map(user=Depends(get_current_user)):
    """Every engine as a PMS™ inheriting the one Manufacturing Foundation™."""
    return await mf.inheritance_map()


@router.post("/package/{engine}/{product_id}")
async def package(engine: str, product_id: str, user=Depends(get_current_user)):
    """Shared packaging inherited from the Foundation — deliverable + PMF™ + standards + provenance."""
    res = await mf.package_product(engine, product_id, user.get("name", "Founder"))
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res
