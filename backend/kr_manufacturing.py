"""QRU Knowledge Record Manufacturing Engine™ (Inheritance-First™).

The Factory's FIRST manufacturing responsibility: manufacture governed Knowledge
Records™ from a source. One Knowledge Record™ → Many Products™.

Pipeline: Idea/Source → Research → Evidence → Verification → Knowledge Organization
→ Knowledge Record™ (Draft) → Founder Review → Enterprise Memory™ → Recipes → Products.

Knowledge-First Rule honored: AI DRAFTS and organizes; every claim carries cited
sources; the record is created as Draft / Partially Verified and NEVER auto-approved.
It becomes Verified truth (and enters Enterprise Memory™) only on explicit Founder
approval. Treasure Standard™: no fake "Verified" states, no silent failures.
"""
import logging
from datetime import datetime, timezone

from database import db
from models import gen_id, now_iso, QRU_SECTIONS, DIVISIONS
from ai_service import llm_generate, parse_json, RESEARCH_SYSTEM, QRU_METHODOLOGY_SYSTEM
from verification_engine import VERIFICATION_SYSTEM, _record_context, CONFIDENCE_THRESHOLD
import knowledge_record_v2 as kr2
import knowledge_extraction as kx
from org_activity import log_org

logger = logging.getLogger("qru.kr_manufacturing")

JOBS = "kr_manufacturing_jobs"
MEMORY = "kr_enterprise_memory"

SOURCE_TYPES = {
    "founder_request": "Founder Request",
    "verified_research": "Verified Research",
    "library_import": "Existing QRU Library / Imported Document",
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _stage(name, status, detail=""):
    return {"stage": name, "status": status, "detail": detail, "at": _now()}


async def _research(source_type, topic, source_text):
    """Returns (verified_truth, sources[], confidence, suggested_category, key_points[])."""
    if source_type == "library_import":
        extracted = kx.extract_fields(source_text or "", topic)
        if not extracted["sufficient"]:
            raise ValueError(extracted["reason"])
        f = extracted["fields"]
        vt = f.get("verified_truth") or f.get("simple_answer") or (source_text or "")[:600]
        return {
            "verified_truth": vt,
            "sources": ["Imported source document (Founder-provided)"],
            "confidence": 70,
            "suggested_category": (f.get("tags") or ["General"])[0].title(),
            "key_points": [],
            "extracted": f,
        }
    # founder_request / verified_research → AI research brief (grounded, cited)
    raw = await llm_generate(RESEARCH_SYSTEM, f"Topic: {topic}", f"kr-research-{gen_id()}")
    brief = parse_json(raw) or {}
    if not brief.get("summary"):
        raise ValueError("Research produced no usable evidence summary.")
    return {
        "verified_truth": brief["summary"],
        "sources": brief.get("sources", []),
        "confidence": int(brief.get("confidence_score") or 60),
        "suggested_category": brief.get("suggested_category") or "General",
        "key_points": brief.get("key_points", []),
        "extracted": None,
    }


async def _organize(topic, verified_truth, key_points):
    """Organize verified content into the QRU teaching methodology fields."""
    ctx = f"Topic: {topic}\n\nVerified content:\n{verified_truth}"
    if key_points:
        ctx += "\n\nKey points:\n- " + "\n- ".join(str(k) for k in key_points)
    raw = await llm_generate(QRU_METHODOLOGY_SYSTEM, ctx, f"kr-organize-{gen_id()}")
    return parse_json(raw) or {}


async def _advisory_review(rec):
    """Run the Verification Team as an ADVISORY review (scores only — never auto-approves)."""
    try:
        raw = await llm_generate(VERIFICATION_SYSTEM, _record_context(rec), f"kr-verify-{rec['id']}")
        review = parse_json(raw)
    except Exception as e:
        logger.warning(f"advisory verification unavailable: {e}")
        review = None
    if not review:
        return {"confidence_score": 0, "scores": {}, "issues": [],
                "reasons": "Advisory verification unavailable — Founder review required.",
                "decision": "request_revision", "advisory": True}
    review["advisory"] = True
    return review


async def manufacture(source_type, topic, category, division, source_text, goal, audience, actor):
    if source_type not in SOURCE_TYPES:
        raise ValueError("Unknown source type.")
    if not (topic or "").strip():
        raise ValueError("A topic or idea is required.")
    stages = [_stage("Idea", "complete", f"{SOURCE_TYPES[source_type]}: {topic}")]

    # 1) Research + 2) Evidence
    research = await _research(source_type, topic, source_text)
    stages.append(_stage("Research", "complete",
                         f"Evidence summary produced · confidence {research['confidence']}%"))
    stages.append(_stage("Evidence Collection", "complete",
                         f"{len(research['sources'])} source(s) cited"))

    # 3) Knowledge Organization (methodology fields)
    fields = {}
    org_status = "complete"
    try:
        if source_type == "library_import" and research.get("extracted"):
            fields.update({k: v for k, v in research["extracted"].items()
                           if k in QRU_SECTIONS and v})
        org = await _organize(topic, research["verified_truth"], research.get("key_points", []))
        for k in QRU_SECTIONS:
            if org.get(k):
                fields[k] = org[k]
    except Exception as e:
        org_status = "partial"
        logger.warning(f"organization partial: {e}")
    stages.append(_stage("Knowledge Organization", org_status,
                         f"{sum(1 for k in QRU_SECTIONS if fields.get(k))}/{len(QRU_SECTIONS)} methodology sections drafted"))

    # 4) Build the Knowledge Record™ (Draft — governed, never auto-verified)
    count = await db.knowledge_records.count_documents({})
    cat = category or research["suggested_category"] or "General"
    div = division if division in DIVISIONS else (DIVISIONS[0])
    section_status = {s: ("Draft" if fields.get(s) else "Empty") for s in QRU_SECTIONS}
    rec = {
        "id": gen_id(),
        "kr_code": f"KR-{count + 1:05d}",
        "title": topic.strip(),
        "subtitle": goal or "",
        "category": cat,
        "division": div,
        "verified_truth": research["verified_truth"],
        "the_question": fields.get("the_question", ""),
        "simple_answer": fields.get("simple_answer", ""),
        "why_it_matters": fields.get("why_it_matters", ""),
        "real_world_example": fields.get("real_world_example", ""),
        "qru_translation": fields.get("qru_translation", ""),
        "everyday_analogy": fields.get("everyday_analogy", ""),
        "memory_sentence": fields.get("memory_sentence", ""),
        "practice_application": fields.get("practice_application", []) or [],
        "key_vocabulary": fields.get("key_vocabulary", []) or [],
        "deep_roots": fields.get("deep_roots", ""),
        "references": research["sources"],
        "sources": research["sources"],
        "confidence_score": research["confidence"],
        "verification_status": "Draft",
        "approval_status": "Pending Founder Review",
        "reviewer": None, "verification": None,
        "section_status": section_status,
        "understanding_status": "Not Manufactured",
        "is_master_file": False, "treasure_standard": False,
        "products_created": 0, "version": 1,
        "manufactured": True, "manufacture_source": source_type,
        "target_audience": audience or "",
        "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    # KR 2.0 sections (non-destructive migration maps methodology → 36 sections)
    rec.update(kr2.migrate_kr(rec))
    await db.knowledge_records.insert_one(dict(rec))

    # 5) Advisory verification (scores only — Founder is the gate)
    review = await _advisory_review(rec)
    await db.knowledge_records.update_one(
        {"id": rec["id"]},
        {"$set": {"verification_status": "Under Review", "manufacturing_review": review,
                  "confidence_score": review.get("confidence_score") or research["confidence"],
                  "updated_at": now_iso()}})
    stages.append(_stage("Verification (Advisory)", "complete",
                         f"Confidence {review.get('confidence_score', 0)}% · decision: {review.get('decision', 'n/a')} · Founder approval required"))
    stages.append(_stage("Founder Review", "pending", "Awaiting Founder approval to become Verified truth."))

    job = {
        "id": gen_id(), "source_type": source_type, "topic": topic.strip(),
        "kr_id": rec["id"], "kr_code": rec["kr_code"], "category": cat, "division": div,
        "stages": stages, "review": review, "status": "Pending Founder Review",
        "created_by": actor, "created_at": now_iso(),
    }
    await db[JOBS].insert_one(dict(job))
    await db.knowledge_records.update_one({"id": rec["id"]}, {"$set": {"manufacturing_job_id": job["id"]}})
    await log_org("Knowledge Manufacturing™", "Knowledge",
                  f"manufactured Draft {rec['kr_code']} — pending Founder review", rec["kr_code"])
    from models import clean
    job.pop("_id", None)
    return {"job": clean(job), "kr_id": rec["id"], "kr_code": rec["kr_code"]}


def _filled(v):
    return len(v) > 0 if isinstance(v, list) else bool(v and str(v).strip())


async def approve(kr_id, actor):
    """Founder approval — the record becomes Verified truth and enters Enterprise Memory™."""
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        return None
    conf = kr.get("confidence_score") or 0
    treasure = all(_filled(kr.get(s)) for s in QRU_SECTIONS) and conf >= CONFIDENCE_THRESHOLD
    section_status = kr.get("section_status", {})
    for s in QRU_SECTIONS:
        if _filled(kr.get(s)):
            section_status[s] = "Verified"
    sections_v2 = kr.get("sections_v2") or {}
    for key, sec in sections_v2.items():
        if sec.get("content"):
            sec["status"] = "Verified"
            sec["verification_status"] = "Verified"
            sec["manufacturing_ready"] = True
    await db.knowledge_records.update_one(
        {"id": kr_id},
        {"$set": {"verification_status": "Verified", "approval_status": "Approved",
                  "is_master_file": True, "treasure_standard": treasure,
                  "section_status": section_status, "sections_v2": sections_v2,
                  "verification": {"reviewer": actor, "reviewed_at": now_iso(),
                                   "decision": "approve", "founder_approved": True,
                                   "confidence_score": conf},
                  "enterprise_memory": True, "memory_entered_at": now_iso(),
                  "updated_at": now_iso()}})
    await db[MEMORY].update_one(
        {"kr_id": kr_id},
        {"$set": {"kr_id": kr_id, "kr_code": kr.get("kr_code"), "title": kr.get("title"),
                  "category": kr.get("category"), "division": kr.get("division"),
                  "version": kr.get("version", 1), "entered_at": now_iso(), "entered_by": actor,
                  "treasure_standard": treasure, "confidence_score": conf}},
        upsert=True)
    await db[JOBS].update_one({"kr_id": kr_id}, {"$set": {"status": "Approved", "approved_by": actor, "approved_at": now_iso()}})
    await db.notifications.insert_one({
        "id": gen_id(), "level": "success", "read": False, "created_at": now_iso(),
        "message": f"{kr.get('kr_code')} approved — entered Enterprise Memory™. Ready to manufacture products."})
    await log_org("Founder", "Knowledge", f"approved {kr.get('kr_code')} → Enterprise Memory™", kr.get("kr_code"), "success")
    return await db.knowledge_records.find_one({"id": kr_id}, {"_id": 0})


async def reject(kr_id, actor, reason):
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        return None
    await db.knowledge_records.update_one(
        {"id": kr_id},
        {"$set": {"verification_status": "Rejected", "approval_status": "Rejected",
                  "rejection_reason": reason or "", "updated_at": now_iso()}})
    await db[JOBS].update_one({"kr_id": kr_id}, {"$set": {"status": "Rejected", "rejected_by": actor, "reject_reason": reason or ""}})
    await log_org("Founder", "Knowledge", f"rejected {kr.get('kr_code')}", kr.get("kr_code"), "warning")
    return await db.knowledge_records.find_one({"id": kr_id}, {"_id": 0})


async def list_jobs(limit=100):
    return await db[JOBS].find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def get_job(job_id):
    return await db[JOBS].find_one({"id": job_id}, {"_id": 0})


async def pending_review():
    from models import clean
    krs = await db.knowledge_records.find(
        {"manufactured": True, "approval_status": "Pending Founder Review",
         "verification_status": {"$in": ["Under Review", "Draft"]}}
    ).sort("created_at", -1).to_list(200)
    return clean(krs)


async def stats():
    total_jobs = await db[JOBS].count_documents({})
    pending = await db.knowledge_records.count_documents(
        {"manufactured": True, "approval_status": "Pending Founder Review"})
    in_memory = await db[MEMORY].count_documents({})
    manufactured = await db.knowledge_records.count_documents({"manufactured": True})
    return {"jobs": total_jobs, "pending_review": pending,
            "enterprise_memory": in_memory, "manufactured": manufactured,
            "confidence_threshold": CONFIDENCE_THRESHOLD}
