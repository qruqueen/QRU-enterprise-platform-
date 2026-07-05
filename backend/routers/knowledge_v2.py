"""QRU Knowledge Record 2.0™ (MO-003) — API surface. Deterministic ($0 AI)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from database import db
from auth import get_current_user, require_super_admin
from models import clean
import knowledge_record_v2 as kr2

router = APIRouter(prefix="/api/kr2", tags=["knowledge-record-2.0"])


@router.get("/registry")
async def registry(user=Depends(get_current_user)):
    groups = {}
    for k, title, group in kr2.SECTION_DEFS:
        groups.setdefault(group, []).append({"key": k, "title": title,
                                             "depended_on_by": kr2.products_depending_on(k)})
    return {"schema_version": kr2.SCHEMA_VERSION, "groups": groups,
            "section_count": len(kr2.SECTION_KEYS),
            "status_values": kr2.STATUS_VALUES, "source_values": kr2.SOURCE_VALUES,
            "verification_values": kr2.VERIFICATION_VALUES}


@router.get("/dependency-map")
async def dependency_map(user=Depends(get_current_user)):
    return {"dependency_map": {kw: [kr2.SECTION_TITLES[s] for s in secs]
                               for kw, secs in kr2.DEPENDENCY_MAP.items()},
            "default_required": [kr2.SECTION_TITLES[s] for s in kr2.DEFAULT_REQUIRED]}


@router.post("/migrate")
async def migrate_all(user=Depends(require_super_admin)):
    """Non-destructive migration of every Knowledge Record to KR 2.0. Idempotent."""
    krs = await db.knowledge_records.find().to_list(5000)
    migrated = 0
    for kr in krs:
        update = kr2.migrate_kr(kr)
        await db.knowledge_records.update_one({"id": kr["id"]}, {"$set": update})
        migrated += 1
    return {"migrated": migrated, "schema_version": kr2.SCHEMA_VERSION}


@router.get("/{kr_id}")
async def get_kr2(kr_id: str, user=Depends(get_current_user)):
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    if kr.get("schema_version") != kr2.SCHEMA_VERSION:
        await db.knowledge_records.update_one({"id": kr_id}, {"$set": kr2.migrate_kr(kr)})
        kr = await db.knowledge_records.find_one({"id": kr_id})
    sections = kr.get("sections_v2") or {}
    ordered = [sections.get(k, kr2.blank_section(k)) for k in kr2.SECTION_KEYS]
    for s in ordered:
        s["depended_on_by"] = kr2.products_depending_on(s["section_id"])
    return {
        "id": kr["id"], "kr_code": kr.get("kr_code"), "title": kr.get("title"),
        "category": kr.get("category"), "verification_status": kr.get("verification_status"),
        "schema_version": kr.get("schema_version"),
        "completeness": kr2.completeness(kr),
        "sections": ordered,
        "unmapped_legacy": kr.get("unmapped_legacy") or {},
    }


class SectionUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    verification_status: Optional[str] = None
    confidence_score: Optional[int] = None
    evidence_links: Optional[List[str]] = None
    reviewer: Optional[str] = None


@router.put("/{kr_id}/section/{section_id}")
async def update_section(kr_id: str, section_id: str, data: SectionUpdate, user=Depends(get_current_user)):
    if section_id not in kr2.SECTION_KEYS:
        raise HTTPException(400, "Unknown section")
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    sections = kr.get("sections_v2") or {}
    sec = sections.get(section_id) or kr2.blank_section(section_id)
    updates = data.dict(exclude_none=True)
    if "status" in updates and updates["status"] not in kr2.STATUS_VALUES:
        raise HTTPException(400, "Invalid status")
    if "source" in updates and updates["source"] not in kr2.SOURCE_VALUES:
        raise HTTPException(400, "Invalid source")
    if "verification_status" in updates and updates["verification_status"] not in kr2.VERIFICATION_VALUES:
        raise HTTPException(400, "Invalid verification status")
    sec.update(updates)
    sec["author"] = sec.get("author") or user["name"]
    sec["version"] = sec.get("version", 0) + 1
    from datetime import datetime, timezone
    sec["updated_at"] = datetime.now(timezone.utc).isoformat()
    sec["manufacturing_ready"] = bool(sec.get("content")) and sec.get("status") in kr2.COMPLETE_STATUSES
    sections[section_id] = sec
    await db.knowledge_records.update_one({"id": kr_id}, {"$set": {"sections_v2": sections}})
    return sec


@router.get("/{kr_id}/manufacturing-readiness")
async def readiness(kr_id: str, product_type: str, user=Depends(get_current_user)):
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    return kr2.manufacturing_readiness(kr, product_type)
