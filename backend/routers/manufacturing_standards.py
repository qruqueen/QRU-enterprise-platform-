"""QRU Manufacturing Standards™ API — the constitutional spine.
UKR™ (Truth) → PMS™ (Instructions) → PMF™ (Evidence). Deterministic ($0 AI)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import db
from auth import get_current_user, require_super_admin
import ukr_standard as ukr
import ukr_lifecycle as ukrlife
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


# ---- Canonical UKR™ Standard v1.1 (full 24-section spec — the approved document) ----

@router.get("/ukr/canonical-spec")
async def ukr_canonical_spec(user=Depends(get_current_user)):
    """The single canonical UKR specification (the Founder-approved document as implemented)."""
    return ukr.canonical_spec()


@router.get("/ukr/migration-status")
async def ukr_migration_status(user=Depends(get_current_user)):
    """Factory-wide canonical migration status (read-only, backward-compatibility report)."""
    return await ukr.migration_status()


@router.post("/ukr/migrate-canonical")
async def ukr_migrate_canonical(dry_run: bool = False, user=Depends(require_super_admin)):
    """Phase-1 NON-DESTRUCTIVE migration: attach the full 24-section canonical `ukr` object to every
    record (legacy flat fields preserved). Idempotent. Returns the migration/compatibility report."""
    return await ukr.migrate_to_canonical(actor=user.get("name", "Founder"), dry_run=dry_run)


@router.get("/ukr/record/{rid}/canonical")
async def ukr_record_canonical(rid: str, user=Depends(get_current_user)):
    """Return one record's canonical `ukr` object (built on-demand if not yet migrated)."""
    rec = await db[ukr.CANONICAL_COLLECTION].find_one({"id": rid}, {"_id": 0}) \
        or await db[ukr.CANONICAL_COLLECTION].find_one({"kr_code": rid}, {"_id": 0})
    if not rec:
        raise HTTPException(404, "Knowledge Record not found.")
    canonical = rec.get("ukr") or ukr.build_canonical(rec)
    return {"kr_code": rec.get("kr_code"), "id": rec.get("id"),
            "migrated": bool(rec.get("ukr")), "ukr": canonical}


# ---- UKR™ Governance Engine: Lifecycle (S18) + Gold Standard Review (S17) ----

@router.get("/ukr/lifecycle/states")
async def ukr_lifecycle_states(user=Depends(get_current_user)):
    return {"states": ukr.LIFECYCLE_STATES, "transitions": ukrlife.TRANSITIONS,
            "founder_only_states": sorted(ukrlife.FOUNDER_ONLY_STATES)}


@router.get("/ukr/governance-overview")
async def ukr_governance_overview(user=Depends(get_current_user)):
    return await ukrlife.governance_overview()


@router.get("/ukr/record/{rid}/lifecycle")
async def ukr_record_lifecycle(rid: str, user=Depends(get_current_user)):
    return await ukrlife.lifecycle_state(rid)


class TransitionInput(BaseModel):
    to_state: str
    trigger: str = "manual"
    note: str = ""


@router.post("/ukr/record/{rid}/transition")
async def ukr_record_transition(rid: str, data: TransitionInput, user=Depends(get_current_user)):
    """Apply a governed lifecycle transition. Founder-only states require super-admin."""
    is_super = user.get("role") in ("Founder & CEO", "Administrator")
    return await ukrlife.transition(rid, data.to_state, actor=user.get("name", "Founder"),
                                    trigger=data.trigger, note=data.note, is_super=is_super)


@router.get("/ukr/record/{rid}/gold-review")
async def ukr_record_gold_review(rid: str, user=Depends(get_current_user)):
    return await ukrlife.gold_review(rid)


class DimensionReviewInput(BaseModel):
    dimension: str
    score: float = 0
    passed: bool = False
    deficiencies: str = ""
    severity: str = ""
    corrective_action: str = ""
    department: str = ""
    due_date: str = ""
    resolution: str = ""


@router.post("/ukr/record/{rid}/gold-review")
async def ukr_record_review_dimension(rid: str, data: DimensionReviewInput, user=Depends(get_current_user)):
    """Review a SINGLE Gold Standard dimension (individually). Never auto-certifies."""
    return await ukrlife.review_dimension(
        rid, data.dimension, data.score, data.passed, reviewer=user.get("name", "Founder"),
        reviewer_type=user.get("role", "Founder"), deficiencies=data.deficiencies, severity=data.severity,
        corrective_action=data.corrective_action, department=data.department, due_date=data.due_date,
        resolution=data.resolution)


@router.post("/ukr/record/{rid}/certify-gold")
async def ukr_record_certify_gold(rid: str, user=Depends(require_super_admin)):
    """Founder-only final Gold certification. Blocked unless ALL 15 dimensions pass."""
    return await ukrlife.certify_gold(rid, actor=user.get("name", "Founder"))


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
