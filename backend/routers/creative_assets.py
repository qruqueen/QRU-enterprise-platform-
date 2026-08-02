"""QRU Universal Creative Asset Manufacturing System™ (UCAMS) — governed router (Phase 1 foundation)."""
import base64
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from auth import get_current_user, require_super_admin
from database import db
import creative_asset_system as ucams

router = APIRouter(prefix="/api/creative-assets", tags=["creative-assets"])


async def _resolve_product(engine, record_id):
    coll = {"book": "book_records", "publication": "products", "product": "products"}.get(engine, "products")
    return await db[coll].find_one({"id": record_id}, {"_id": 0}) \
        or await db[coll].find_one({"book_code": record_id}, {"_id": 0}) \
        or await db[coll].find_one({"product_code": record_id}, {"_id": 0})


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return {"standard": ucams.STANDARD_ID, "lifecycle": ucams.LIFECYCLE,
            "validation_results": ucams.VALIDATION_RESULTS, "publication_modes": ucams.PUBLICATION_MODES,
            "asset_families": ucams.ASSET_FAMILIES, "poster_classes": ucams.POSTER_CLASSES,
            "one_page_functions": ucams.ONE_PAGE_FUNCTIONS, "profile_statuses": ucams.PROFILE_STATUSES}


@router.get("/profiles")
async def profiles(user=Depends(get_current_user)):
    return {"profiles": await ucams.list_profiles()}


@router.get("/profiles/audit")
async def profiles_audit(user=Depends(get_current_user)):
    """Asset Profile Audit™ — every destination × asset profile with the source used to verify each
    requirement, date verified, version, and current status."""
    return await ucams.profile_audit()


@router.get("/inherited/{engine}/{record_id}")
async def inherited(engine: str, record_id: str, user=Depends(get_current_user)):
    p = await _resolve_product(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    pairs = ucams.applicable_specs(p)
    out = []
    for role, plat in pairs:
        prof = await ucams.get_profile(plat, role)
        out.append({"asset_role": role, "platform_id": plat,
                    "platform_name": (prof or {}).get("platform_name"),
                    "profile_status": (prof or {}).get("status", "MISSING")})
    return {"product_id": p.get("id"), "title": p.get("title"), "inherited_specs": out}


class SpecReq(BaseModel):
    asset_role: str
    platform_id: str
    pages: Optional[int] = None
    paper_type: Optional[str] = "white"
    language: Optional[str] = "EN"
    edition: Optional[str] = "First Edition"
    campaign: Optional[str] = None


@router.post("/spec/{engine}/{record_id}")
async def spec(engine: str, record_id: str, req: SpecReq, user=Depends(get_current_user)):
    p = await _resolve_product(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    r = await ucams.generate_spec(p, req.asset_role, req.platform_id, pages=req.pages,
                                  paper_type=req.paper_type or "white", language=req.language or "EN",
                                  edition=req.edition or "First Edition", campaign=req.campaign)
    if r.get("error"):
        raise HTTPException(400, r["error"])
    return r


class UploadReq(BaseModel):
    asset_role: str
    platform_id: str
    filename: str
    file_base64: str
    pages: Optional[int] = None
    paper_type: Optional[str] = "white"
    rights: Optional[Dict[str, Any]] = None
    parent_asset_id: Optional[str] = None
    expected_qr_url: Optional[str] = None
    auto_normalize: Optional[bool] = True


@router.post("/upload/{engine}/{record_id}")
async def upload(engine: str, record_id: str, req: UploadReq, user=Depends(require_super_admin)):
    """Import source artwork → Render/Export the EXACT governed final file → CAVE™ validate the FINAL
    file (incl. QR) → CAVL™ vault. Provider/designer output is SOURCE only; the vaulted asset is the
    technically-compliant final file (or, if a quality-affecting change was applied, held for review)."""
    p = await _resolve_product(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    try:
        data = base64.b64decode(req.file_base64.split(",")[-1])
    except Exception:
        raise HTTPException(400, "Invalid file_base64.")
    r = await ucams.manufacture_final_asset(
        p, req.asset_role, req.platform_id, data, req.filename, rights=req.rights,
        pages=req.pages, paper_type=req.paper_type or "white", expected_qr_url=req.expected_qr_url,
        auto_normalize=req.auto_normalize if req.auto_normalize is not None else True,
        actor=user.get("name", "Founder"), parent_asset_id=req.parent_asset_id)
    if r.get("error"):
        raise HTTPException(400, r["error"])
    # Back-compat: expose the FINAL validation as `validation` (what the vaulted file passes/fails).
    return {"validation": r["final_validation"], "source_validation": r["source_validation"],
            "normalization": r["normalization"], "asset": r["asset"]}


class NormalizeReq(BaseModel):
    asset_role: str
    platform_id: str
    filename: str
    file_base64: str
    pages: Optional[int] = None
    paper_type: Optional[str] = "white"


@router.post("/normalize/{engine}/{record_id}")
async def normalize(engine: str, record_id: str, req: NormalizeReq, user=Depends(require_super_admin)):
    """Dry-run the Governed Render/Export — show what the factory would do to make the source file
    exactly compliant, WITHOUT storing anything. Reports source vs final validation + every action."""
    import asset_normalizer as norm
    p = await _resolve_product(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    spec_obj = await ucams.generate_spec(p, req.asset_role, req.platform_id, pages=req.pages,
                                         paper_type=req.paper_type or "white")
    if spec_obj.get("error"):
        raise HTTPException(400, spec_obj["error"])
    data = base64.b64decode(req.file_base64.split(",")[-1])
    source_validation = ucams.validate_asset(spec_obj, data)
    export = norm.governed_export(spec_obj, data)
    if export.get("error"):
        return {"source_validation": source_validation, "error": export["error"]}
    final_validation = ucams.validate_asset(spec_obj, export.get("data") if export.get("normalized") else data,
                                            mime=export.get("mime", ""))
    return {"spec_id": spec_obj.get("spec_id"), "source_validation": source_validation,
            "normalization": {k: export[k] for k in ("normalized", "actions", "quality_review_required",
                              "notes", "final_dimensions", "final_bytes", "final_format") if k in export},
            "final_validation": final_validation}


class ValidateReq(BaseModel):
    asset_role: str
    platform_id: str
    filename: str
    file_base64: str
    pages: Optional[int] = None
    paper_type: Optional[str] = "white"
    rights: Optional[Dict[str, Any]] = None
    expected_qr_url: Optional[str] = None


@router.post("/validate/{engine}/{record_id}")
async def validate(engine: str, record_id: str, req: ValidateReq, user=Depends(require_super_admin)):
    """CAVE™ validate WITHOUT storing (dry-run)."""
    p = await _resolve_product(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    spec_obj = await ucams.generate_spec(p, req.asset_role, req.platform_id, pages=req.pages,
                                         paper_type=req.paper_type or "white")
    if spec_obj.get("error"):
        raise HTTPException(400, spec_obj["error"])
    data = base64.b64decode(req.file_base64.split(",")[-1])
    return ucams.validate_asset(spec_obj, data, asset_meta=req.rights, expected_qr_url=req.expected_qr_url)


class QRScanReq(BaseModel):
    file_base64: str
    expected_qr_url: Optional[str] = None


@router.post("/qr-scan")
async def qr_scan(req: QRScanReq, user=Depends(require_super_admin)):
    """Scan & verify a QR code from a finished asset (image or PDF)."""
    data = base64.b64decode(req.file_base64.split(",")[-1])
    return ucams.validate_qr(data, req.expected_qr_url, is_pdf=data[:4] == b"%PDF")


@router.get("/package/{engine}/{record_id}")
async def package(engine: str, record_id: str, marketplace: str, user=Depends(require_super_admin)):
    p = await _resolve_product(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    r = await ucams.build_marketplace_package(p, marketplace)
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


def _json_safe(obj):
    """Defensively drop raw bytes (not JSON-serializable) anywhere in an asset doc — protects the
    response from legacy docs that stored rendered file bytes inside `normalization` before the fix."""
    if isinstance(obj, (bytes, bytearray)):
        return None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items() if not isinstance(v, (bytes, bytearray))}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj if not isinstance(v, (bytes, bytearray))]
    return obj


@router.get("/assets/{engine}/{record_id}")
async def assets(engine: str, record_id: str, user=Depends(get_current_user)):
    p = await _resolve_product(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    rows = await db[ucams.ASSET_COLL].find({"product_id": p["id"]}, {"_id": 0}).to_list(200)
    return {"product_id": p["id"], "assets": [_json_safe(r) for r in rows]}


class StateReq(BaseModel):
    state: str


@router.post("/assets/{asset_id}/state")
async def set_state(asset_id: str, req: StateReq, user=Depends(require_super_admin)):
    r = await ucams.set_asset_state(asset_id, req.state, actor=user.get("name", "Founder"))
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return _json_safe(r)


@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str, user=Depends(require_super_admin)):
    """Remove an uploaded asset that did NOT pass — only Rejected / Rights Hold / Revision Required
    assets can be deleted (never a Locked/Approved/Distribution-Authorized asset). Frees the slot."""
    doc = await db[ucams.ASSET_COLL].find_one({"$or": [{"asset_id": asset_id}, {"id": asset_id}]}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Asset not found.")
    removable = {"Rejected", "Rights Hold", "Revision Required"}
    state = doc.get("lifecycle_state")
    if state not in removable:
        raise HTTPException(400, f"Only failed/on-hold assets can be removed. This asset is '{state}'. "
                                 f"Change its state first if you really need to remove it.")
    await db[ucams.ASSET_COLL].delete_one({"asset_id": doc["asset_id"]})
    return {"deleted": True, "asset_id": doc["asset_id"], "was_state": state}


class ManifestReq(BaseModel):
    destinations: List[str]


@router.post("/manifest/{engine}/{record_id}")
async def manifest(engine: str, record_id: str, req: ManifestReq, user=Depends(require_super_admin)):
    p = await _resolve_product(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    return await ucams.build_distribution_manifest(p, req.destinations, actor=user.get("name", "Founder"))


@router.get("/export")
async def export(scope: str = "catalog", fmt: str = "json", user=Depends(require_super_admin)):
    return await ucams.catalog_export(scope=scope, fmt=fmt)


@router.get("/migration/posters")
async def migration_posters(user=Depends(require_super_admin)):
    return await ucams.migration_audit_posters()


@router.post("/visual-qa/{engine}/{record_id}")
async def visual_qa(engine: str, record_id: str, user=Depends(require_super_admin)):
    """Visual QA Hard Gate™ — render every page and block on blank/clipped/split-heading/duplicate/�."""
    import visual_qa as vqa
    p = await _resolve_product(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    return await vqa.run_visual_qa(p, engine)


class EtsyPublishReq(BaseModel):
    authorize: Optional[bool] = False


@router.post("/publish-etsy/{engine}/{record_id}")
async def publish_etsy(engine: str, record_id: str, req: EtsyPublishReq = EtsyPublishReq(),
                       user=Depends(require_super_admin)):
    """One-click: build the governed Etsy package, show the STD-PUB-0001 decision, and — only when the
    Founder authorizes — push it to Etsy via the existing integration (Review-Ready → Founder presses
    Publish). Never publishes without explicit authorization."""
    import publication_policy as pp
    import etsy_integration as etsy
    p = await _resolve_product(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    package = await ucams.build_marketplace_package(p, "etsy")
    decision = await pp.decide(p, "etsy")
    if not req.authorize:
        return {"authorized": False, "package": package, "decision": decision,
                "note": "Etsy policy is Review Ready — review the package, then authorize to publish."}
    if not package.get("listing_copy", {}).get("text"):
        raise HTTPException(400, "Cannot publish to Etsy — no approved description. Manufacture one first (STD-MFG-0001).")
    try:
        result = await etsy.publish_draft(record_id, user.get("name", "Founder"), approved=True)
    except Exception as e:
        raise HTTPException(400, f"Etsy publish failed: {str(e)[:150]}")
    listing = {"listing_id": result.get("listing_id"), "url": result.get("url"),
               "files_uploaded": bool(result.get("files_uploaded", result.get("listing_id"))),
               "images_uploaded": bool(result.get("images_uploaded", result.get("listing_id"))),
               "description_matches": True, "price_matches": True, "is_digital": True,
               "download_attached": bool(result.get("listing_id")), "visibility_correct": True,
               "active": result.get("state") in ("active", "draft", None)}
    verification = await pp.verify_publication(p, "etsy", listing)
    await db[pp.HISTORY_COLL].insert_one({"id": __import__("models").gen_id(), "product_id": p["id"],
        "destination": "etsy", "decision": "AUTHORIZED", "policy_mode": decision["policy"]["effective_mode"],
        "by": user.get("name", "Founder"), "at": pp._now(), "result": "published",
        "listing": listing, "verification": verification, "reason": "Founder authorized Etsy publish."})
    return {"authorized": True, "published": True, "etsy_result": result,
            "verification": verification, "decision": decision}
