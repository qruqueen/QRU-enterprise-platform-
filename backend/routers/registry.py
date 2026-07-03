"""QRU Topic Registry™ — the authoritative source of every topic the factory will
manufacture. Also hosts AI topic-list generation (for review) and bulk college
seeding (creates Colleges, Topic Registry entries, and Manufacturing Orders — WITHOUT
manufacturing Knowledge Records yet)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database import db
from auth import get_current_user, require_super_admin
from models import gen_id, now_iso, clean
from ai_service import llm_generate, parse_json

router = APIRouter(prefix="/api/topic-registry", tags=["topic-registry"])


# ---------------- Models ----------------
class TopicInput(BaseModel):
    college: str
    department: str
    topic_name: str
    division: Optional[str] = "Health"
    priority_score: Optional[int] = 70
    public_need_score: Optional[int] = 70
    educational_value_score: Optional[int] = 70


class TopicUpdate(BaseModel):
    topic_name: Optional[str] = None
    college: Optional[str] = None
    department: Optional[str] = None
    priority_score: Optional[int] = None
    public_need_score: Optional[int] = None
    educational_value_score: Optional[int] = None
    manufacturing_status: Optional[str] = None
    verification_status: Optional[str] = None
    treasure_standard_status: Optional[str] = None


class GenerateInput(BaseModel):
    domain: str  # "Health" | "Faith"
    count: Optional[int] = 100


class BulkImportInput(BaseModel):
    college: str
    division: str
    topics: List[dict]  # each: {topic_name, department, priority_score, public_need_score, educational_value_score}
    create_orders: Optional[bool] = True


async def _next_topic_id():
    count = await db.topic_registry.count_documents({})
    return f"TOP-{count + 1:05d}"


def _serialize(t):
    t = clean(t)
    return t


# ---------------- Read ----------------
@router.get("")
async def list_topics(college: Optional[str] = None, department: Optional[str] = None,
                      division: Optional[str] = None, manufacturing_status: Optional[str] = None,
                      q: Optional[str] = None, user=Depends(get_current_user)):
    query = {}
    if college:
        query["college"] = college
    if department:
        query["department"] = department
    if division:
        query["division"] = division
    if manufacturing_status:
        query["manufacturing_status"] = manufacturing_status
    if q:
        query["topic_name"] = {"$regex": q, "$options": "i"}
    topics = await db.topic_registry.find(query).sort("created_at", -1).to_list(2000)
    return clean(topics)


@router.get("/stats")
async def stats(user=Depends(get_current_user)):
    total = await db.topic_registry.count_documents({})
    by_status = {}
    for s in ["Not Started", "Queued", "In Progress", "Manufactured"]:
        by_status[s] = await db.topic_registry.count_documents({"manufacturing_status": s})
    verified = await db.topic_registry.count_documents({"verification_status": "Verified"})
    certified = await db.topic_registry.count_documents({"treasure_standard_status": "Certified"})
    divisions = await db.topic_registry.distinct("division")
    colleges = await db.topic_registry.distinct("college")
    per_division = {}
    for d in divisions:
        per_division[d] = await db.topic_registry.count_documents({"division": d})
    return {"total": total, "by_status": by_status, "verified": verified, "certified": certified,
            "divisions": divisions, "colleges": colleges, "per_division": per_division}


@router.get("/{tid}")
async def get_topic(tid: str, user=Depends(get_current_user)):
    t = await db.topic_registry.find_one({"id": tid})
    if not t:
        raise HTTPException(404, "Topic not found")
    return clean(t)


# ---------------- Write ----------------
async def _create_topic_doc(data: dict, owner_id: str):
    topic_id = await _next_topic_id()
    now = now_iso()
    doc = {
        "id": gen_id(), "topic_id": topic_id,
        "college": data["college"], "department": data.get("department", "General"),
        "division": data.get("division", "Health"), "topic_name": data["topic_name"],
        "priority_score": int(data.get("priority_score", 70)),
        "public_need_score": int(data.get("public_need_score", 70)),
        "educational_value_score": int(data.get("educational_value_score", 70)),
        "manufacturing_status": "Not Started", "verification_status": "Unverified",
        "treasure_standard_status": "Not Certified", "assigned_manufacturing_order": None,
        "knowledge_record_id": None, "version_history": [{"version": 1, "action": "created", "at": now}],
        "owner_id": owner_id, "created_at": now, "updated_at": now,
    }
    await db.topic_registry.insert_one(dict(doc))
    return doc


@router.post("")
async def create_topic(data: TopicInput, user=Depends(get_current_user)):
    doc = await _create_topic_doc(data.model_dump(), user["id"])
    return clean(doc)


@router.put("/{tid}")
async def update_topic(tid: str, data: TopicUpdate, user=Depends(get_current_user)):
    t = await db.topic_registry.find_one({"id": tid})
    if not t:
        raise HTTPException(404, "Topic not found")
    upd = {k: v for k, v in data.model_dump().items() if v is not None}
    upd["updated_at"] = now_iso()
    history = t.get("version_history", [])
    history.append({"version": len(history) + 1, "action": "updated", "by": user["name"], "at": now_iso()})
    upd["version_history"] = history
    await db.topic_registry.update_one({"id": tid}, {"$set": upd})
    return clean(await db.topic_registry.find_one({"id": tid}))


@router.delete("/{tid}")
async def delete_topic(tid: str, user=Depends(require_super_admin)):
    await db.topic_registry.delete_one({"id": tid})
    return {"message": "deleted"}


# ---------------- AI topic generation (proposals for review) ----------------
HEALTH_TOPIC_SYSTEM = """You are the QRU Health University planning board. Propose the most important
health education topics for the general public, ranked by real-world impact. Organize them into
clinical departments (e.g., Heart Health, Brain & Mental Health, Metabolic Health, Cancer Understanding,
Kidney Health, Lung & Respiratory Health, Immune Health, Digestive Health, Bone & Joint Health,
Nutrition, Sleep, Preventive Care, Women's Health, Men's Health, Child Health, Aging & Longevity).

Return ONLY valid JSON (no markdown fences):
{"topics": [{"topic_name": "clear, specific topic title", "department": "department name",
  "priority_score": 0-100, "public_need_score": 0-100, "educational_value_score": 0-100}]}
Make each topic_name a concrete, teachable subject a person would want to truly understand."""

FAITH_TOPIC_SYSTEM = """You are the QRU College of Faith planning board. Propose foundational
Christian / biblical education topics for sincere learners. Organize them into departments
(e.g., Old Testament, New Testament, Life of Jesus, The Gospel, Christian Living, Prayer,
Theology & Doctrine, Church History, Biblical Characters, Apologetics, Spiritual Growth,
Bible Study Methods).

Return ONLY valid JSON (no markdown fences):
{"topics": [{"topic_name": "clear, specific topic title", "department": "department name",
  "priority_score": 0-100, "public_need_score": 0-100, "educational_value_score": 0-100}]}
Keep every topic grounded in Scripture and mainstream Christian understanding; teach clearly and respectfully."""


@router.post("/generate")
async def generate_topics(data: GenerateInput, user=Depends(require_super_admin)):
    """AI generates a proposed topic list for review. Nothing is saved until bulk-import."""
    domain = data.domain.strip().lower()
    count = max(10, min(int(data.count or 100), 120))
    if domain == "faith":
        system, college, division = FAITH_TOPIC_SYSTEM, "QRU College of Faith", "Faith"
    else:
        system, college, division = HEALTH_TOPIC_SYSTEM, "QRU Health University", "Health"
    prompt = f"Propose the top {count} topics. Return exactly {count} items if possible, ranked most important first."
    raw = await llm_generate(system, prompt, f"gen-topics-{domain}")
    parsed = parse_json(raw) or {}
    topics = parsed.get("topics", []) if isinstance(parsed, dict) else []
    # normalize
    clean_topics = []
    for t in topics:
        if not isinstance(t, dict) or not t.get("topic_name"):
            continue
        clean_topics.append({
            "topic_name": str(t.get("topic_name"))[:200],
            "department": str(t.get("department", "General"))[:80],
            "priority_score": int(t.get("priority_score", 70) or 70),
            "public_need_score": int(t.get("public_need_score", 70) or 70),
            "educational_value_score": int(t.get("educational_value_score", 70) or 70),
        })
    return {"domain": data.domain, "college": college, "division": division,
            "count": len(clean_topics), "topics": clean_topics}


@router.post("/bulk-import")
async def bulk_import(data: BulkImportInput, user=Depends(require_super_admin)):
    """Persist approved topics: creates the College, Topic Registry entries, and
    Manufacturing Orders (Queued). Does NOT manufacture Knowledge Records."""
    # Ensure the college exists in the unified colleges collection.
    existing_college = await db.colleges.find_one({"name": data.college})
    if not existing_college:
        await db.colleges.insert_one({
            "id": gen_id(), "name": data.college, "division": data.division,
            "description": f"{data.college} — governed by the QRU Topic Registry™.",
            "color": "#35106A", "status": "Active", "owner_id": user["id"], "created_at": now_iso(),
        })

    created_topics, created_orders = [], 0
    mo_base = await db.manufacturing_orders.count_documents({})
    for t in data.topics:
        if not t.get("topic_name"):
            continue
        doc = await _create_topic_doc({
            "college": data.college, "division": data.division,
            "department": t.get("department", "General"), "topic_name": t["topic_name"],
            "priority_score": t.get("priority_score", 70),
            "public_need_score": t.get("public_need_score", 70),
            "educational_value_score": t.get("educational_value_score", 70),
        }, user["id"])

        if data.create_orders:
            mo_base += 1
            mo_id = gen_id()
            await db.manufacturing_orders.insert_one({
                "id": mo_id, "mo_code": f"MO-{mo_base:05d}", "topic": t["topic_name"],
                "audience": "General public", "learning_level": "General",
                "product_types": ["Interactive Lesson"], "priority": "Medium",
                "due_date": None, "verification_level": "Standard", "assigned_employees": [],
                "knowledge_record_id": None, "status": "Queued", "deliverables": [],
                "topic_registry_id": doc["id"], "division": data.division, "college": data.college,
                "approval_history": [{"stage": "Created via Topic Registry", "by": user["name"], "at": now_iso()}],
                "created_by": user["name"], "owner_id": user["id"],
                "created_at": now_iso(), "updated_at": now_iso(),
            })
            await db.topic_registry.update_one(
                {"id": doc["id"]}, {"$set": {"assigned_manufacturing_order": mo_id, "manufacturing_status": "Queued"}})
            created_orders += 1
        created_topics.append(doc["topic_id"])

    return {"college": data.college, "division": data.division,
            "topics_created": len(created_topics), "orders_created": created_orders,
            "topic_ids": created_topics}
