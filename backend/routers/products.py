from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean
from ai_service import llm_generate, parse_json
from org_activity import log_org

router = APIRouter(prefix="/api/products", tags=["products"])

PRODUCT_TYPES = [
    "Book", "Poster", "Infographic", "Presentation", "Teacher Guide", "Caregiver Guide",
    "Workbook", "Lesson Plan", "Video Script", "Podcast Script", "Short-form Content",
    "Interactive Lesson", "AI Tutor", "Course", "Certificate", "Flash Cards", "Quiz", "Printable PDF",
]


class GenerateInput(BaseModel):
    knowledge_record_id: Optional[str] = None
    topic: Optional[str] = None
    product_type: str
    audience: Optional[str] = "General public"
    learning_level: Optional[str] = "Introductory"
    asset_mode: Optional[str] = "director"       # MT-029: use_imported | generate | director
    asset_vault_id: Optional[str] = None


def product_system(ptype: str) -> str:
    return (
        f"You are the QRU Manufacturing Director producing a publication-ready {ptype}. "
        "QRU manufactures understanding from verified knowledge without simplifying the truth. "
        f"Generate complete, well-structured, professional {ptype} content in clean Markdown. "
        "Include a title, clear sections, and where relevant an everyday analogy and a memorable takeaway. "
        "Return ONLY the Markdown content."
    )


@router.get("")
async def list_products(product_type: Optional[str] = None, status: Optional[str] = None,
                        family: Optional[str] = None, user=Depends(get_current_user)):
    query = {}
    if product_type:
        query["product_type"] = product_type
    if status:
        query["status"] = status
    if family:
        query["family"] = family
    products = await db.products.find(query, {"content": 0}).sort("created_at", -1).to_list(500)
    return clean(products)


CREATIVE_BRIEF_SYSTEM = """You are the QRU Creative Studio Director. For the given educational product, write the product-page brief that helps a learner decide with confidence.
Return ONLY JSON with EXACTLY these keys:
{
 "who_for": "who this product is for (1 sentence)",
 "problem_solved": "what problem it solves (1 sentence)",
 "will_understand": "what the learner will understand (1-2 sentences)",
 "skills_gained": ["skill 1", "skill 2", "skill 3"],
 "whats_included": ["item 1", "item 2", "item 3"],
 "reading_level": "e.g. Beginner / Intermediate / Advanced",
 "completion_time": "e.g. 20 minutes",
 "next_path": "suggested next learning step (1 sentence)"
}
Keep it warm, empowering, and honest."""


class BriefInput(BaseModel):
    pass


@router.post("/{pid}/creative-brief")
async def creative_brief(pid: str, user=Depends(get_current_user)):
    """Creative Studio enhances the product page with a decision-ready brief.

    Stage-aware: if the AI Brief Writer™ stage is unavailable (provider capped), we fall back
    to a deterministic on-brand brief so the enhancement still COMPLETES, and report the source.
    """
    # Stage 1 — Load Product
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")

    # Stage 2 — AI Brief Writer™ (degrades gracefully)
    brief, brief_source, stage_note = {}, "ai", None
    prompt = f"Product: {p['title']}\nType: {p['product_type']}\nTopic: {p.get('topic','')}\nAudience: {p.get('audience','')}"
    try:
        raw = await llm_generate(CREATIVE_BRIEF_SYSTEM, prompt, f"brief-{pid}")
        brief = parse_json(raw) or {}
        if not brief:
            raise ValueError("empty brief from provider")
    except Exception as e:
        msg = str(getattr(e, "detail", e))
        if "spend limit" in msg.lower() or "quota" in msg.lower():
            stage_note = "AI Brief Writer™: provider quota exceeded — used a deterministic on-brand brief."
        elif "budget" in msg.lower():
            stage_note = "AI Brief Writer™: provider budget exceeded — used a deterministic on-brand brief."
        elif "unavailable" in msg.lower() or "503" in msg:
            stage_note = "AI Brief Writer™: provider temporarily unavailable — used a deterministic on-brand brief."
        else:
            stage_note = f"AI Brief Writer™: {msg[:120]} — used a deterministic on-brand brief."
        brief, brief_source = _fallback_brief(p), "deterministic"

    # Stage 3 — Related Products
    related = await db.products.find(
        {"family": p.get("family"), "id": {"$ne": pid}}, {"id": 1, "title": 1, "product_type": 1, "product_code": 1}
    ).to_list(4)

    # Stage 4 — Persist enhancement
    await db.products.update_one({"id": pid}, {"$set": {
        "creative_brief": brief,
        "creative_brief_source": brief_source,
        "related_products": clean(related),
        "creative_status": "Reviewed",
        "updated_at": now_iso(),
    }})
    await log_org("Creative Studio Director™", "Creative Studio",
                  "enhanced the product page for", p["product_code"], "success")
    result = clean(await db.products.find_one({"id": pid}, {"content": 0}))
    result["enhancement_stage_note"] = stage_note
    result["enhancement_source"] = brief_source
    return result


def _fallback_brief(p):
    """Deterministic, on-brand Creative Studio brief built from existing product data."""
    ptype = p.get("product_type", "resource")
    topic = p.get("topic") or p.get("title", "this topic")
    audience = p.get("audience") or "curious learners"
    return {
        "who_for": f"For {audience} who want to genuinely understand {topic}.",
        "problem_solved": f"Turns {topic} from confusing to clear, using the QRU teaching methodology.",
        "will_understand": f"You'll understand what {topic} is, why it matters, and how to apply it in real life.",
        "skills_gained": ["Clear understanding of the core idea", "Real-world application", "Confidence to explain it to others"],
        "whats_included": [f"A complete QRU {ptype}", "Verified, plain-language explanations", "Memory aids and a next step"],
        "reading_level": p.get("reading_level") or "Beginner-friendly",
        "completion_time": "About 20 minutes",
        "next_path": "Continue with the next product in this QRU learning family.",
    }


@router.get("/creative-queue")
async def creative_queue(user=Depends(get_current_user)):
    q = await db.products.find(
        {"$or": [{"creative_status": {"$exists": False}}, {"creative_status": "Pending"}]},
        {"content": 0}).sort("created_at", -1).to_list(200)
    return clean(q)


@router.get("/types")
async def get_types():
    return {"types": PRODUCT_TYPES}


# Manufacturing recipes: which Knowledge Record fields compose each product (assembled, not re-generated).
RECIPES = {
    "Poster": ["poster_text", "memory_sentence", "why_it_matters", "call_to_action"],
    "Infographic": ["infographic_text", "step_by_step", "key_vocabulary"],
    "Workbook": ["workbook_activities", "practice_questions", "reflection_questions", "quiz"],
    "Teacher Guide": ["teacher_notes", "lesson_plan", "step_by_step", "kingdom_lion_questions"],
    "Caregiver Guide": ["parent_notes", "why_it_matters", "conversation_starter", "faq"],
    "Presentation": ["presentation_outline", "presentation_script", "key_vocabulary"],
    "Video Script": ["video_script", "story_version", "call_to_action"],
    "Podcast Script": ["podcast_script", "conversation_starter", "faq"],
    "Quiz": ["quiz", "practice_questions", "certification_questions"],
    "Flash Cards": ["vocabulary_decoder", "key_vocabulary", "memory_sentence"],
    "Course": ["adult_version", "step_by_step", "quiz", "lesson_plan", "call_to_action"],
    "Book": ["adult_version", "deep_roots", "story_version", "faq", "applications"],
    "Certificate": ["certification_questions", "kingdom_lion_questions"],
    "Lesson Plan": ["lesson_plan", "student_notes", "practice_application"],
    "Short-form Content": ["social_media_pack", "memory_sentence"],
}

FIELD_LABELS = {
    "poster_text": "Poster", "memory_sentence": "Memory Sentence™", "why_it_matters": "Why It Matters",
    "call_to_action": "Call to Action", "infographic_text": "Infographic", "step_by_step": "Step by Step",
    "key_vocabulary": "Vocabulary", "workbook_activities": "Workbook Activities", "practice_questions": "Practice Questions",
    "reflection_questions": "Reflection Questions", "quiz": "Quiz", "teacher_notes": "Teacher Notes",
    "lesson_plan": "Lesson Plan", "kingdom_lion_questions": "Kingdom Lion Verification Questions™",
    "parent_notes": "Parent Notes", "conversation_starter": "Conversation Starter™", "faq": "FAQ",
    "presentation_outline": "Presentation Outline", "presentation_script": "Presentation Script",
    "video_script": "Video Script", "story_version": "Story", "podcast_script": "Podcast Script",
    "vocabulary_decoder": "Vocabulary Decoder™", "adult_version": "Adult Version", "deep_roots": "Deep Roots™",
    "applications": "Applications", "certification_questions": "Certification Questions", "student_notes": "Student Notes",
    "practice_application": "Practice", "social_media_pack": "Social Media Pack",
}


def _render_field(field, value):
    label = FIELD_LABELS.get(field, field.replace("_", " ").title())
    if not value:
        return ""
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                if "term" in item:
                    lines.append(f"- **{item.get('term')}** — {item.get('definition','')}")
                elif "question" in item:
                    opts = item.get("options")
                    q = f"- **{item.get('question')}**"
                    if opts:
                        q += "\n" + "\n".join(f"  - {o}" for o in opts)
                    if item.get("answer"):
                        q += f"\n  - _Answer: {item.get('answer')}_"
                    lines.append(q)
                else:
                    lines.append(f"- {item}")
            else:
                lines.append(f"- {item}")
        body = "\n".join(lines)
    else:
        body = str(value)
    return f"## {label}\n\n{body}\n"


class AssembleInput(BaseModel):
    knowledge_record_id: str
    product_type: str
    asset_mode: str = "director"          # MT-029: use_imported | generate | director
    asset_vault_id: str = None


@router.post("/assemble")
async def assemble_product(data: AssembleInput, user=Depends(get_current_user)):
    """Assemble a product from EXISTING Knowledge Record fields (no regeneration)."""
    kr = await db.knowledge_records.find_one({"id": data.knowledge_record_id})
    if not kr:
        raise HTTPException(404, "Knowledge Record not found")
    recipe = RECIPES.get(data.product_type)
    if not recipe:
        raise HTTPException(400, f"No recipe for {data.product_type}. Use /generate for AI generation.")
    missing = [f for f in recipe if not kr.get(f)]
    parts = [f"# {kr['title']} — {data.product_type}\n"]
    for field in recipe:
        rendered = _render_field(field, kr.get(field))
        if rendered:
            parts.append(rendered)
    content = "\n".join(parts)

    count = await db.products.count_documents({})
    product = {
        "id": gen_id(),
        "product_code": f"PRD-{count + 1:05d}",
        "title": f"{kr['title']} — {data.product_type}",
        "product_type": data.product_type,
        "family": kr.get("category", "General"),
        "topic": kr["title"],
        "audience": "General",
        "learning_level": "Introductory",
        "content": content,
        "status": "Needs Review" if missing else "Ready",
        "knowledge_record_id": kr["id"],
        "kr_version": kr.get("version", 1),
        "recipe": recipe,
        "missing_fields": missing,
        "assembled": True,
        "asset_mode": data.asset_mode,
        "created_by": user["name"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.products.insert_one(dict(product))
    await db.knowledge_records.update_one({"id": kr["id"]}, {"$inc": {"products_created": 1}})
    # MT-029 — Founder Asset Selection™: manufacture using a chosen imported asset.
    if data.asset_mode == "use_imported" and data.asset_vault_id:
        import vault
        rel = await vault.apply_to_product(product["id"], data.asset_vault_id, user["name"])
        if rel:
            product["manufacturing_asset"] = rel
    return clean(await db.products.find_one({"id": product["id"]}))


@router.get("/recipes")
async def recipes(user=Depends(get_current_user)):
    return {"recipes": {k: v for k, v in RECIPES.items()}, "field_labels": FIELD_LABELS}


@router.get("/{pid}")
async def get_product(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    return clean(p)


@router.post("/generate")
async def generate_product(data: GenerateInput, user=Depends(get_current_user)):
    kr = None
    topic = data.topic
    family = "General"
    if data.knowledge_record_id:
        kr = await db.knowledge_records.find_one({"id": data.knowledge_record_id})
        if kr:
            topic = kr["title"]
            family = kr.get("category", "General")
    if not topic:
        raise HTTPException(400, "topic or knowledge_record_id required")

    context = ""
    if kr:
        context = (
            f"Verified Truth: {kr.get('verified_truth','')}\n"
            f"Consumer Translation: {kr.get('consumer_translation','')}\n"
            f"Analogy: {kr.get('everyday_analogy','')}\n"
        )
    prompt = (
        f"Topic: {topic}\nAudience: {data.audience}\nLearning Level: {data.learning_level}\n{context}\n"
        f"Produce the {data.product_type}."
    )
    content = await llm_generate(product_system(data.product_type), prompt, f"product-{gen_id()}")

    count = await db.products.count_documents({})
    product = {
        "id": gen_id(),
        "product_code": f"PRD-{count + 1:05d}",
        "title": f"{topic} — {data.product_type}",
        "product_type": data.product_type,
        "family": family,
        "topic": topic,
        "audience": data.audience,
        "learning_level": data.learning_level,
        "content": content,
        "status": "Draft",
        "knowledge_record_id": data.knowledge_record_id,
        "kr_version": kr.get("version", 1) if kr else None,
        "assembled": False,
        "asset_mode": data.asset_mode,
        "created_by": user["name"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.products.insert_one(dict(product))
    if kr:
        await db.knowledge_records.update_one(
            {"id": kr["id"]}, {"$inc": {"products_created": 1}})
    # MT-029 — Founder Asset Selection™: manufacture using a chosen imported asset.
    if data.asset_mode == "use_imported" and data.asset_vault_id:
        import vault
        rel = await vault.apply_to_product(product["id"], data.asset_vault_id, user["name"])
        if rel:
            product["manufacturing_asset"] = rel
    return clean(await db.products.find_one({"id": product["id"]}))


class StatusInput(BaseModel):
    status: str


@router.patch("/{pid}/status")
async def set_status(pid: str, data: StatusInput, user=Depends(get_current_user)):
    if data.status not in ["Draft", "Ready", "Generating", "In Review", "Needs Review", "Approved", "Published", "Archived", "Needs Regeneration"]:
        raise HTTPException(400, "Invalid status")
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Not found")
    if data.status == "Published":
        if not (p.get("creative_brief") and p.get("creative_status") == "Reviewed"):
            raise HTTPException(400, "Send this product through the Creative Studio before publication.")
        if not p.get("verified"):
            raise HTTPException(400, "This product must pass AI Verification (Product Protection) before it can be published or sold.")
    await db.products.update_one({"id": pid}, {"$set": {"status": data.status, "updated_at": now_iso()}})
    return clean(await db.products.find_one({"id": pid}))


@router.delete("/{pid}")
async def delete_product(pid: str, user=Depends(get_current_user)):
    await db.products.delete_one({"id": pid})
    return {"message": "deleted"}



@router.post("/{pid}/regenerate-cover")
async def regenerate_cover(pid: str, request: Request, user=Depends(get_current_user)):
    """Force-refresh a product's cover to the current Gold Standard (new hero art + wrap),
    then re-render its deliverables. Respects Founder-attached Cover Studio covers."""
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found.")
    base_url = str(request.base_url).rstrip("/")
    # Clear the old auto-cover so a fresh hero-art cover is generated (skip vault reuse).
    await db.products.update_one({"id": pid}, {"$set": {"asset_mode": "generate", "cover_has_hero_art": False},
                                               "$unset": {"cover_url": "", "customer_deliverable": ""}})
    import rendering_engine as _re
    import deliverable_renderer as _dr
    try:
        await _re.ensure_branded_assets(pid, actor=user["name"], allow_ai_hero_art=True)
        await _dr.ensure_deliverable(pid, actor=user["name"], base_url=base_url, build_marketing=False)
    except Exception as e:
        raise HTTPException(500, f"Cover regeneration failed: {str(e)[:160]}")
    prod = await db.products.find_one({"id": pid}, {"_id": 0})
    return {"ok": True, "cover_url": prod.get("cover_url"), "cover_has_hero_art": prod.get("cover_has_hero_art"),
            "deliverables": (prod.get("customer_deliverable") or {}).get("files", [])}
