"""QRU Consumer Learning Platform — the finished, customer-facing experience.

Consumer products are ASSEMBLED from the verified Knowledge Master Record™ and its
manufactured Understanding Assets™. Nothing here regenerates knowledge; it composes
the QRU educational structure (branded sections, layered understanding, learning modes,
Kingdom Lion™ verification) into a beautiful learning experience.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean

router = APIRouter(prefix="/api/consumer", tags=["consumer"])


def _filled(v):
    if isinstance(v, list):
        return len(v) > 0
    return bool(v and str(v).strip())


# The standard QRU educational structure — ordered branded sections, each mapped to a
# verified Knowledge Record field. Only filled sections are shown to the learner.
QRU_SECTION_MAP = [
    ("the_question", "The Question™", "text"),
    ("simple_answer", "Simple Answer™", "text"),
    ("why_it_matters", "Why It Matters™", "text"),
    ("qru_translation", "QRU Translation™", "text"),
    ("step_by_step", "What's Happening Inside?™", "list"),
    ("professional_version", "Scientific Explanation™", "text"),
    ("real_world_example", "Everyday Example™", "text"),
    ("deep_roots", "Deep Roots™", "text"),
    ("memory_sentence", "QRU Memory Sentence™", "highlight"),
    ("vocabulary_decoder", "Vocabulary Decoder™", "vocab"),
    ("key_vocabulary", "Key Vocabulary", "vocab"),
    ("common_misconceptions", "Common Misconceptions™", "list"),
    ("practice_application", "Quick Action Steps™", "list"),
    ("kingdom_lion_questions", "Questions to Consider™", "list"),
    ("conversation_starter", "Conversation Starters™", "text"),
    ("cheat_sheet", "Cheat Sheet™", "text"),
    ("call_to_action", "What's Next?", "text"),
]

# Layered Understanding — the same verified knowledge at four depths.
LAYERS = [
    ("Quick Understanding™", "Friendly, simple, consumer-focused.",
     ["simple_answer", "everyday_analogy", "memory_sentence"]),
    ("Understand It™", "The mechanism explained, still conversational.",
     ["qru_translation", "step_by_step", "real_world_example"]),
    ("Scientific Explanation™", "Professional terminology and technical concepts.",
     ["professional_version", "deep_roots"]),
    ("Professional Resources™", "Evidence, research and references.",
     ["references", "sources"]),
]

# Learning styles — presentation changes, the truth does not.
# Each mode lists candidate fields in priority order (first filled one is used).
LEARNING_MODES = [
    ("child", "Child Mode", ["children_version"]),
    ("consumer", "Consumer Mode", ["qru_translation"]),
    ("student", "Student Mode", ["student_version", "student_notes", "adult_version"]),
    ("professional", "Professional Mode", ["professional_version"]),
    ("scientific", "Scientific Mode", ["deep_roots"]),
    ("story", "Story Mode", ["story_version"]),
]


def build_understanding(kr):
    """Assemble the full QRU understanding package from a Knowledge Master Record."""
    if not kr:
        return None
    sections = []
    used = set()
    for field, label, kind in QRU_SECTION_MAP:
        if field in used:
            continue
        val = kr.get(field)
        if _filled(val):
            # Avoid two vocab sections
            if kind == "vocab" and any(s["kind"] == "vocab" for s in sections):
                continue
            sections.append({"id": field, "label": label, "kind": kind, "value": val})
            used.add(field)

    layers = []
    for title, subtitle, fields in LAYERS:
        parts = [{"field": f, "value": kr.get(f)} for f in fields if _filled(kr.get(f))]
        if parts:
            layers.append({"title": title, "subtitle": subtitle, "parts": parts})

    modes = []
    for key, label, fields in LEARNING_MODES:
        chosen = next((kr.get(f) for f in fields if _filled(kr.get(f))), None)
        if chosen:
            modes.append({"key": key, "label": label, "content": chosen})

    v = kr.get("verification") or {}
    verification = {
        "status": kr.get("verification_status", "Draft"),
        "confidence_score": kr.get("confidence_score", 0),
        "is_master_file": kr.get("is_master_file", False),
        "treasure_standard": kr.get("treasure_standard", False),
        "reviewer": v.get("reviewer") or kr.get("reviewer"),
        "reviewed_at": v.get("reviewed_at"),
        "evidence": v.get("evidence"),
        "references": kr.get("references", []),
        "sources": kr.get("sources", []),
        "evidence_level": "High" if kr.get("confidence_score", 0) >= 90 else (
            "Moderate" if kr.get("confidence_score", 0) >= 70 else "Emerging"),
    }
    return {"sections": sections, "layers": layers, "learning_modes": modes, "verification": verification}


async def _enrollment(user_id, product_id):
    return await db.consumer_enrollments.find_one({"user_id": user_id, "product_id": product_id})


def _catalog_projection():
    return {"content": 0}


@router.get("/catalog")
async def catalog(q: Optional[str] = None, category: Optional[str] = None, user=Depends(get_current_user)):
    query = {"status": "Published"}
    if category:
        query["family"] = category
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"topic": {"$regex": q, "$options": "i"}},
        ]
    prods = await db.products.find(query, _catalog_projection()).sort("updated_at", -1).to_list(300)
    prods = clean(prods)
    # attach the learner's enrollment state + a treasure flag from the source record
    enrolls = await db.consumer_enrollments.find({"user_id": user["id"]}).to_list(500)
    emap = {e["product_id"]: e for e in enrolls}
    for p in prods:
        e = emap.get(p["id"])
        p["progress"] = e.get("progress", 0) if e else 0
        p["favorite"] = e.get("favorite", False) if e else False
        p["enrolled"] = bool(e)
    families = sorted({p.get("family", "General") for p in prods})
    return {"products": prods, "categories": families}


@router.get("/pathways")
async def pathways(user=Depends(get_current_user)):
    prods = await db.products.find({"status": "Published"}, _catalog_projection()).to_list(300)
    prods = clean(prods)
    groups = {}
    for p in prods:
        fam = p.get("family", "General")
        groups.setdefault(fam, []).append({"id": p["id"], "title": p["title"], "product_type": p["product_type"]})
    return {"pathways": [{"name": k, "topic_count": len(v), "products": v} for k, v in sorted(groups.items())]}


@router.get("/my-learning")
async def my_learning(user=Depends(get_current_user)):
    enrolls = await db.consumer_enrollments.find({"user_id": user["id"]}).sort("updated_at", -1).to_list(300)
    out = []
    for e in enrolls:
        p = await db.products.find_one({"id": e["product_id"]}, _catalog_projection())
        if p:
            p = clean(p)
            p["progress"] = e.get("progress", 0)
            p["favorite"] = e.get("favorite", False)
            p["status_learn"] = e.get("status", "In Progress")
            p["last_section"] = e.get("last_section")
            out.append(p)
    return {"items": out}


@router.get("/favorites")
async def favorites(user=Depends(get_current_user)):
    enrolls = await db.consumer_enrollments.find({"user_id": user["id"], "favorite": True}).to_list(300)
    out = []
    for e in enrolls:
        p = await db.products.find_one({"id": e["product_id"]}, _catalog_projection())
        if p:
            p = clean(p)
            p["progress"] = e.get("progress", 0)
            p["favorite"] = True
            out.append(p)
    return {"items": out}


@router.get("/certificates")
async def certificates(user=Depends(get_current_user)):
    certs = await db.consumer_certificates.find({"user_id": user["id"]}).sort("issued_at", -1).to_list(200)
    return {"items": clean(certs)}


@router.get("/recommendations")
async def recommendations(user=Depends(get_current_user)):
    enrolls = await db.consumer_enrollments.find({"user_id": user["id"]}).to_list(500)
    done_ids = {e["product_id"] for e in enrolls}
    prods = await db.products.find(
        {"status": "Published", "id": {"$nin": list(done_ids)}}, _catalog_projection()
    ).sort("updated_at", -1).to_list(8)
    return {"items": clean(prods)}


@router.get("/products/{pid}")
async def consumer_product(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p or p.get("status") != "Published":
        raise HTTPException(404, "This product is not available.")
    p = clean(p)
    understanding = None
    if p.get("knowledge_record_id"):
        kr = await db.knowledge_records.find_one({"id": p["knowledge_record_id"]})
        understanding = build_understanding(kr) if kr else None
    e = await _enrollment(user["id"], pid)
    # related products in the same family
    related = await db.products.find(
        {"family": p.get("family"), "status": "Published", "id": {"$ne": pid}},
        {"id": 1, "title": 1, "product_type": 1, "family": 1}).to_list(4)
    return {
        "product": p,
        "understanding": understanding,
        "enrollment": clean(e) if e else None,
        "related": clean(related),
    }


class EnrollInput(BaseModel):
    product_id: str


@router.post("/enroll")
async def enroll(data: EnrollInput, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": data.product_id})
    if not p or p.get("status") != "Published":
        raise HTTPException(404, "Product not available")
    e = await _enrollment(user["id"], data.product_id)
    if e:
        return clean(e)
    doc = {
        "id": gen_id(), "user_id": user["id"], "product_id": data.product_id,
        "product_title": p["title"], "status": "In Progress", "progress": 0,
        "last_section": None, "favorite": False,
        "started_at": now_iso(), "updated_at": now_iso(), "completed_at": None,
    }
    await db.consumer_enrollments.insert_one(dict(doc))
    return clean(doc)


class ProgressInput(BaseModel):
    product_id: str
    progress: int
    last_section: Optional[str] = None


@router.post("/progress")
async def progress(data: ProgressInput, user=Depends(get_current_user)):
    e = await _enrollment(user["id"], data.product_id)
    if not e:
        await enroll(EnrollInput(product_id=data.product_id), user)
        e = await _enrollment(user["id"], data.product_id)
    pct = max(0, min(100, data.progress))
    upd = {"progress": pct, "updated_at": now_iso()}
    if data.last_section:
        upd["last_section"] = data.last_section
    cert = None
    if pct >= 100 and e.get("status") != "Completed":
        upd["status"] = "Completed"
        upd["completed_at"] = now_iso()
        cert = await _issue_certificate(user, data.product_id)
    await db.consumer_enrollments.update_one({"id": e["id"]}, {"$set": upd})
    return {"progress": pct, "completed": pct >= 100, "certificate": cert}


async def _issue_certificate(user, product_id):
    existing = await db.consumer_certificates.find_one({"user_id": user["id"], "product_id": product_id})
    if existing:
        return clean(existing)
    p = await db.products.find_one({"id": product_id})
    count = await db.consumer_certificates.count_documents({})
    doc = {
        "id": gen_id(), "user_id": user["id"], "product_id": product_id,
        "product_title": p["title"] if p else "QRU Product",
        "learner_name": user.get("name", "Learner"),
        "code": f"QRU-CERT-{count + 1:05d}", "issued_at": now_iso(),
    }
    await db.consumer_certificates.insert_one(dict(doc))
    return clean(doc)


class FavInput(BaseModel):
    product_id: str


@router.post("/favorite")
async def toggle_favorite(data: FavInput, user=Depends(get_current_user)):
    e = await _enrollment(user["id"], data.product_id)
    if not e:
        await enroll(EnrollInput(product_id=data.product_id), user)
        e = await _enrollment(user["id"], data.product_id)
    fav = not e.get("favorite", False)
    await db.consumer_enrollments.update_one({"id": e["id"]}, {"$set": {"favorite": fav, "updated_at": now_iso()}})
    return {"favorite": fav}
