"""MT-031 — Knowledge Record Promotion Pipeline™.

Governed, Knowledge-First promotion of Topic Seeds into Verified Knowledge Records.
STRICT RULE: this pipeline NEVER generates or infers content with AI. Every field is
entered manually by the Founder or imported from a Founder source document. Promotion
requires provenance (a source note) so nothing is fabricated.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean

router = APIRouter(prefix="/api/promotion", tags=["promotion"])

# The Guided Understanding System™ — the only fields a Verified Knowledge Record needs.
GUS_FIELDS = [
    {"key": "the_question", "label": "The Question", "type": "text", "required": True,
     "help": "The exact learner question this record answers."},
    {"key": "simple_answer", "label": "Simple Answer", "type": "textarea", "required": True,
     "help": "The plain, direct answer a beginner can understand."},
    {"key": "why_it_matters", "label": "Why It Matters", "type": "textarea", "required": True,
     "help": "Why this understanding matters to a real person."},
    {"key": "real_world_example", "label": "Real-World Example", "type": "textarea", "required": False,
     "help": "A concrete example from real life."},
    {"key": "qru_translation", "label": "QRU Translation™", "type": "textarea", "required": False,
     "help": "The truth restated in the simplest faithful language."},
    {"key": "everyday_analogy", "label": "Everyday Analogy", "type": "textarea", "required": False,
     "help": "An analogy that makes the idea click."},
    {"key": "memory_sentence", "label": "Memory Sentence™", "type": "text", "required": False,
     "help": "One sentence the learner will remember forever."},
    {"key": "deep_roots", "label": "Deep Roots™", "type": "textarea", "required": False,
     "help": "The deeper principle beneath the surface answer."},
]
CONTENT_KEYS = [f["key"] for f in GUS_FIELDS]
REQUIRED = [f["key"] for f in GUS_FIELDS if f["required"]] + ["verified_truth"]


def _filled(v) -> bool:
    if isinstance(v, list):
        return len(v) > 0
    return bool(v and str(v).strip())


def _progress(rec: dict) -> dict:
    done = [k for k in REQUIRED if _filled(rec.get(k))]
    optional_done = [k for k in CONTENT_KEYS if k not in REQUIRED and _filled(rec.get(k))]
    return {
        "required_total": len(REQUIRED),
        "required_done": len(done),
        "optional_done": len(optional_done),
        "ready_to_promote": len(done) == len(REQUIRED),
        "missing_required": [k for k in REQUIRED if not _filled(rec.get(k))],
    }


@router.get("/schema")
async def schema(user=Depends(get_current_user)):
    return {"fields": GUS_FIELDS, "required": REQUIRED, "content_keys": CONTENT_KEYS}


@router.get("/seeds")
async def list_seeds(q: Optional[str] = None, curriculum: Optional[str] = None,
                     user=Depends(get_current_user)):
    query = {"record_class": "Topic Seed"}
    if curriculum:
        query["curriculum"] = curriculum
    if q:
        query["title"] = {"$regex": q, "$options": "i"}
    recs = await db.knowledge_records.find(query).sort([("curriculum", 1), ("curriculum_order", 1), ("kr_code", 1)]).to_list(500)
    out = []
    for r in clean(recs):
        r["promotion"] = _progress(r)
        out.append(r)
    return out


@router.get("/{rid}")
async def get_seed(rid: str, user=Depends(get_current_user)):
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Knowledge Record not found")
    rec = clean(rec)
    rec["promotion"] = _progress(rec)
    return rec


class FieldsInput(BaseModel):
    the_question: Optional[str] = None
    simple_answer: Optional[str] = None
    why_it_matters: Optional[str] = None
    real_world_example: Optional[str] = None
    qru_translation: Optional[str] = None
    everyday_analogy: Optional[str] = None
    memory_sentence: Optional[str] = None
    deep_roots: Optional[str] = None
    verified_truth: Optional[str] = None
    key_vocabulary: Optional[List[Dict[str, Any]]] = None
    subtitle: Optional[str] = None


@router.put("/{rid}/fields")
async def save_fields(rid: str, data: FieldsInput, user=Depends(get_current_user)):
    """Manually save Guided Understanding System™ fields. No AI — Founder/import content only."""
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Not found")
    payload = {k: v for k, v in data.model_dump().items() if v is not None}
    if not payload:
        raise HTTPException(400, "No fields provided")
    section_status = rec.get("section_status", {})
    for k, v in payload.items():
        if k in CONTENT_KEYS or k == "key_vocabulary":
            section_status[k] = "Draft" if _filled(v) else "Empty"
    payload["section_status"] = section_status
    payload["updated_at"] = now_iso()
    await db.knowledge_records.update_one({"id": rid}, {"$set": payload})
    updated = clean(await db.knowledge_records.find_one({"id": rid}))
    updated["promotion"] = _progress(updated)
    return updated


class PromoteInput(BaseModel):
    source_note: str            # provenance — required (Knowledge-First)
    source_document: Optional[str] = ""


@router.post("/{rid}/promote")
async def promote(rid: str, data: PromoteInput, user=Depends(get_current_user)):
    """Promote a Topic Seed → Imported Verified Knowledge Record. Requires all core
    Guided Understanding System™ fields + a provenance note. Never uses AI."""
    rec = await db.knowledge_records.find_one({"id": rid})
    if not rec:
        raise HTTPException(404, "Not found")
    if rec.get("record_class") != "Topic Seed":
        raise HTTPException(400, "Only Topic Seeds can be promoted through this pipeline")
    if not (data.source_note and data.source_note.strip()):
        raise HTTPException(400, "A source note (provenance) is required to promote — Knowledge-First Manufacturing")
    missing = [k for k in REQUIRED if not _filled(rec.get(k))]
    if missing:
        raise HTTPException(400, f"Cannot promote — required fields missing: {', '.join(missing)}")

    section_status = rec.get("section_status", {})
    for k in CONTENT_KEYS + ["key_vocabulary"]:
        if _filled(rec.get(k)):
            section_status[k] = "Verified"

    new_version = rec.get("version", 1) + 1
    change_log = rec.get("change_log", [])
    change_log.append({"version": new_version, "by": user["name"], "at": now_iso(),
                       "action": "promoted Topic Seed → Imported Verified Knowledge Record™"})
    promotion_history = rec.get("promotion_history", [])
    promotion_history.append({
        "at": now_iso(), "by": user["name"],
        "source_note": data.source_note.strip(),
        "source_document": (data.source_document or "").strip(),
        "from_class": "Topic Seed", "to_class": "Imported Verified",
    })

    upd = {
        "record_class": "Imported Verified",
        "verification_status": "Verified",
        "approval_status": "Founder Approved",
        "readiness": "Ready for Manufacturing",
        "treasure_standard_status": "Verified",
        "ai_content": "None",
        "promotion_ready": False,
        "is_master_file": True,
        "understanding_status": "Verified (Imported)",
        "confidence_score": max(rec.get("confidence_score", 0), 95),
        "reviewer": user["name"],
        "source_note": data.source_note.strip(),
        "source_document": (data.source_document or "").strip(),
        "section_status": section_status,
        "version": new_version,
        "change_log": change_log,
        "promotion_history": promotion_history,
        "promoted_by": user["name"],
        "promoted_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.knowledge_records.update_one({"id": rid}, {"$set": upd})
    await db.activities.insert_one({
        "id": gen_id(), "actor": user["name"], "action": "promoted to Verified Knowledge Record",
        "entity": "KnowledgeRecord", "entity_id": rid, "detail": rec.get("title", ""),
        "created_at": now_iso(),
    })
    result = clean(await db.knowledge_records.find_one({"id": rid}))
    result["promotion"] = _progress(result)
    return result
