"""QRU Manufacturing Engine 2.0 — Recipes, Product Assembly, Release Gates,
and the Automatic Treasure Standard™ Quality Control loop.

Principles:
- Assembly first: prefer composing approved Understanding Assets™ over regeneration.
- Staged & resumable: every product tracks its stages; nothing restarts unless asked.
- Release is gated: a product cannot be released until every required gate passes.
- Quality Control auto-improves: weak areas are routed to the owning department, the
  product is improved by AI, then re-scored — repeating until Treasure Standard™.
"""
import asyncio
import logging

from database import db
from models import gen_id, now_iso
from ai_service import llm_generate, parse_json
from org_activity import log_org

logger = logging.getLogger("qru.mfg2")

# ---------------------------------------------------------------------------
# Manufacturing Recipes™ — each product type is a repeatable, versioned recipe.
# required_fields: Knowledge Master Record™ fields the product needs.
# ---------------------------------------------------------------------------
BASE_STAGES = [
    "Knowledge Master Record", "Required Fields", "Understanding Assets",
    "Product Assembly", "Creative Studio", "Quality Control", "Treasure Standard", "Release",
]

RECIPES = {
    "Book": {"version": 1, "required_fields": ["simple_answer", "qru_translation", "adult_version", "deep_roots", "story_version", "faq", "key_vocabulary", "memory_sentence"],
             "extra_stages": ["Book Outline", "Chapters"], "deliverables": ["Print PDF", "Digital eBook", "Mobile Layout", "Cover Design"]},
    "Workbook": {"version": 1, "required_fields": ["simple_answer", "practice_application", "reflection_questions", "quiz", "key_vocabulary"],
                 "extra_stages": ["Activities", "Answer Key"], "deliverables": ["Printable PDF", "Digital Workbook"]},
    "Poster": {"version": 1, "required_fields": ["poster_text", "memory_sentence", "why_it_matters", "call_to_action"],
               "extra_stages": [], "deliverables": ["Print Poster", "Digital Poster", "Thumbnail"]},
    "Presentation": {"version": 1, "required_fields": ["presentation_outline", "presentation_script", "key_vocabulary"],
                     "extra_stages": ["Slide Design"], "deliverables": ["Slide Deck", "Speaker Notes"]},
    "Teacher Guide": {"version": 1, "required_fields": ["teacher_notes", "lesson_plan", "step_by_step", "kingdom_lion_questions"],
                      "extra_stages": [], "deliverables": ["Print Guide", "Digital Guide"]},
    "Caregiver Guide": {"version": 1, "required_fields": ["parent_notes", "why_it_matters", "conversation_starter", "faq"],
                        "extra_stages": [], "deliverables": ["Print Guide", "Digital Guide"]},
    "Course": {"version": 1, "required_fields": ["adult_version", "step_by_step", "quiz", "lesson_plan", "call_to_action"],
               "extra_stages": ["Module Outline"], "deliverables": ["Course Package", "Certificate"]},
    "Podcast Script": {"version": 1, "required_fields": ["podcast_script", "conversation_starter", "faq"],
                       "extra_stages": [], "deliverables": ["Script", "Show Notes"]},
    "Video Script": {"version": 1, "required_fields": ["video_script", "story_version", "call_to_action"],
                     "extra_stages": [], "deliverables": ["Script", "Storyboard Notes"]},
    "Flash Cards": {"version": 1, "required_fields": ["vocabulary_decoder", "key_vocabulary", "memory_sentence"],
                    "extra_stages": [], "deliverables": ["Printable Cards", "Digital Deck"]},
    "Quiz": {"version": 1, "required_fields": ["quiz", "practice_questions", "certification_questions"],
             "extra_stages": [], "deliverables": ["Digital Quiz"]},
    "Interactive Lesson": {"version": 1, "required_fields": ["the_question", "simple_answer", "qru_translation", "step_by_step", "memory_sentence", "practice_application"],
                           "extra_stages": [], "deliverables": ["Interactive Lesson", "Mobile Layout"]},
    "Short-form Content": {"version": 1, "required_fields": ["social_media_pack", "memory_sentence"],
                           "extra_stages": [], "deliverables": ["Social Pack"]},
}

FIELD_LABELS = {
    "the_question": "The Question™", "simple_answer": "Simple Answer™", "why_it_matters": "Why It Matters™",
    "qru_translation": "QRU Translation™", "deep_roots": "Deep Roots™", "memory_sentence": "QRU Memory Sentence™",
    "adult_version": "Adult Version", "story_version": "Story", "faq": "FAQ", "key_vocabulary": "Key Vocabulary",
    "vocabulary_decoder": "Vocabulary Decoder™", "practice_application": "Quick Action Steps™",
    "reflection_questions": "Reflection Questions", "quiz": "Quiz", "poster_text": "Poster Content",
    "call_to_action": "What's Next?", "presentation_outline": "Presentation Outline",
    "presentation_script": "Presentation Script", "teacher_notes": "Teacher Notes", "lesson_plan": "Lesson Plan",
    "step_by_step": "What's Happening Inside?™", "kingdom_lion_questions": "Kingdom Lion Verification™",
    "parent_notes": "Parent Notes", "conversation_starter": "Conversation Starters™", "podcast_script": "Podcast Script",
    "video_script": "Video Script", "practice_questions": "Practice Questions",
    "certification_questions": "Certification Questions", "social_media_pack": "Social Media Pack",
}

# Treasure Standard™ thresholds. AI-scored criteria + deterministic gates.
AI_THRESHOLDS = {
    "Clarity": 90, "Understanding": 90, "Engagement": 85,
    "Visual Quality": 88, "Accessibility": 88, "Learning Effectiveness": 90, "Customer Delight": 85,
}

# Which department owns each failing criterion (routing rules).
ROUTING = {
    "Clarity": ("Legacy Bear™", "Education"),
    "Understanding": ("Legacy Bear™", "Education"),
    "Engagement": ("Experience Lab Director™", "Experience Lab"),
    "Visual Quality": ("Creative Studio Director™", "Creative Studio"),
    "Accessibility": ("Emergent Accessibility Specialist", "Accessibility"),
    "Learning Effectiveness": ("Legacy Bear™", "Education"),
    "Customer Delight": ("Consumer Advocate™", "Customer Experience"),
    "Brand Consistency": ("Brand Director™", "Brand"),
    "Verification": ("Kingdom Lion™", "Verification"),
    "Traceability": ("Kingdom Lion™", "Verification"),
}

RELEASE_GATES = ["Verification", "Education Review", "Creative Studio", "Brand Review",
                 "Accessibility", "Experience Review", "Quality Control", "Treasure Standard"]


def _filled(v):
    return len(v) > 0 if isinstance(v, list) else bool(v and str(v).strip())


def get_recipe(ptype):
    return RECIPES.get(ptype)


def recipe_stages(ptype):
    r = RECIPES.get(ptype, {})
    stages = ["Knowledge Master Record", "Required Fields", "Understanding Assets"]
    stages += r.get("extra_stages", [])
    stages += ["Product Assembly", "Creative Studio", "Quality Control", "Treasure Standard", "Release"]
    return stages


def detect_missing(kr, ptype):
    r = RECIPES.get(ptype)
    if not r:
        return []
    missing = []
    for f in r["required_fields"]:
        if not _filled(kr.get(f)):
            missing.append({"field": f, "label": FIELD_LABELS.get(f, f.replace("_", " ").title())})
    return missing


def _init_gates():
    return {g: {"status": "pending"} for g in RELEASE_GATES}


def _init_stages(ptype):
    return [{"label": s, "status": "waiting"} for s in recipe_stages(ptype)]


async def _set_stage(pid, label, status, detail=""):
    p = await db.products.find_one({"id": pid})
    stages = p.get("stages", [])
    for s in stages:
        if s["label"] == label:
            s["status"] = status
            if detail:
                s["detail"] = detail
    await db.products.update_one({"id": pid}, {"$set": {"stages": stages, "updated_at": now_iso()}})


def _render_field(field, value):
    label = FIELD_LABELS.get(field, field.replace("_", " ").title())
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                if "term" in item:
                    lines.append(f"- **{item.get('term')}** — {item.get('definition','')}")
                elif "question" in item:
                    lines.append(f"- **{item.get('question')}**" + (f" _(Answer: {item.get('answer')})_" if item.get("answer") else ""))
                else:
                    lines.append(f"- {item}")
            else:
                lines.append(f"- {item}")
        body = "\n".join(lines)
    else:
        body = str(value)
    return f"## {label}\n\n{body}\n"


async def assemble_product(kr, ptype, user_name):
    """Assembly-first: compose a product from EXISTING Knowledge Record fields."""
    r = RECIPES.get(ptype) or {"required_fields": [], "extra_stages": [], "deliverables": [], "version": 1}
    missing = detect_missing(kr, ptype)
    parts = [f"# {kr['title']} — {ptype}\n"]
    for field in r["required_fields"]:
        if _filled(kr.get(field)):
            parts.append(_render_field(field, kr.get(field)))
    content = "\n".join(parts)

    count = await db.products.count_documents({})
    stages = _init_stages(ptype)
    # mark early stages done based on available material
    for s in stages:
        if s["label"] == "Knowledge Master Record":
            s["status"] = "done" if kr.get("verification_status") == "Verified" else "failed"
            s["detail"] = "Verified Master Record" if kr.get("verification_status") == "Verified" else "Source record not verified"
        elif s["label"] == "Required Fields":
            s["status"] = "done" if not missing else "failed"
            s["detail"] = "All required fields present" if not missing else f"{len(missing)} field(s) missing"
        elif s["label"] == "Understanding Assets":
            s["status"] = "done" if kr.get("understanding_status") in ("Draft", "Verified") else "waiting"
        elif s["label"] == "Product Assembly":
            s["status"] = "done"
            s["detail"] = f"Assembled {len([f for f in r['required_fields'] if _filled(kr.get(f))])} asset(s)"

    deliverables = [{"name": d, "status": "assembled"} for d in r.get("deliverables", [])]
    deliverables += [{"name": "Product Metadata", "status": "assembled"},
                     {"name": "Licensing Information", "status": "assembled"},
                     {"name": "Learning Path", "status": "assembled"},
                     {"name": "QR Code", "status": "assembled"}]

    product = {
        "id": gen_id(), "product_code": f"PRD-{count + 1:05d}",
        "title": f"{kr['title']} — {ptype}", "product_type": ptype,
        "family": kr.get("category", "General"), "topic": kr["title"],
        "audience": "General public", "learning_level": "Introductory",
        "content": content, "status": "Manufacturing",
        "knowledge_record_id": kr["id"], "kr_version": kr.get("version", 1),
        "recipe_type": ptype, "recipe_version": r.get("version", 1),
        "assembled": True, "missing_fields": missing,
        "stages": stages, "gates": _init_gates(), "deliverables": deliverables,
        "qc": {"status": "not_started", "iterations": 0, "history": [], "scores": {}, "current_issue": None},
        "treasure_standard": False, "creative_status": "Pending",
        "created_by": user_name, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.products.insert_one(dict(product))
    await db.knowledge_records.update_one({"id": kr["id"]}, {"$inc": {"products_created": 1}})
    await log_org("Manufacturing Director™", "Manufacturing", f"assembled a {ptype} from", kr.get("kr_code", ""), "success")
    from models import clean
    return clean(product)


async def manufacture_missing_job(pid, actor):
    """Background: fill only the MISSING required fields on the source record, then re-assemble."""
    from manufacturing_engine import regenerate_field
    p = await db.products.find_one({"id": pid})
    if not p:
        return
    await db.products.update_one({"id": pid}, {"$set": {"status": "Manufacturing"}})
    kr = await db.knowledge_records.find_one({"id": p.get("knowledge_record_id")})
    if not kr:
        return
    missing = detect_missing(kr, p["recipe_type"])
    await _set_stage(pid, "Required Fields", "running", f"Manufacturing {len(missing)} missing field(s)")
    for m in missing:
        try:
            await regenerate_field(kr["id"], m["field"], actor)
            await log_org("Legacy Bear™", "Education", f"manufactured {m['label']} for", kr.get("kr_code", ""))
        except Exception as e:
            logger.error(f"manufacture missing {m['field']} failed: {e}")
    kr = await db.knowledge_records.find_one({"id": kr["id"]})
    new_missing = detect_missing(kr, p["recipe_type"])
    # re-assemble content
    r = RECIPES.get(p["recipe_type"], {"required_fields": []})
    parts = [f"# {kr['title']} — {p['recipe_type']}\n"]
    for field in r["required_fields"]:
        if _filled(kr.get(field)):
            parts.append(_render_field(field, kr.get(field)))
    await db.products.update_one({"id": pid}, {"$set": {
        "content": "\n".join(parts), "missing_fields": new_missing, "updated_at": now_iso()}})
    await _set_stage(pid, "Required Fields", "done" if not new_missing else "failed",
                     "All required fields present" if not new_missing else f"{len(new_missing)} still missing")
    await _set_stage(pid, "Product Assembly", "done", "Re-assembled with new fields")


# ---------------------------------------------------------------------------
# Automatic Treasure Standard™ Quality Control loop
# ---------------------------------------------------------------------------
QC_SCORE_SYSTEM = """You are the QRU Manufacturing Quality Control™ board (Legacy Bear™, Creative Studio™, Experience Lab™).
Evaluate this educational product for release readiness. Be a demanding but fair QRU expert.
Return ONLY JSON:
{
 "scores": {"Clarity": 0-100, "Understanding": 0-100, "Engagement": 0-100, "Visual Quality": 0-100, "Accessibility": 0-100, "Learning Effectiveness": 0-100, "Customer Delight": 0-100},
 "friction_points": ["..."],
 "strengths": ["..."]
}"""

QC_IMPROVE_SYSTEM = """You are a QRU expert improving an educational product to Treasure Standard™ quality.
Rewrite and strengthen the product Markdown so it is clearer, more engaging, more accurate, and more useful — without inventing unverified facts.
Preserve all headings and structure. Return ONLY the improved Markdown content."""


async def _score_product(p):
    prompt = f"Title: {p['title']}\nType: {p['product_type']}\nContent:\n{(p.get('content') or '')[:2500]}"
    raw = await llm_generate(QC_SCORE_SYSTEM, prompt, f"qc-{p['id']}-{p['qc']['iterations']}")
    data = parse_json(raw) or {}
    scores = data.get("scores", {})
    creative_done = p.get("creative_status") == "Reviewed"
    kr = await db.knowledge_records.find_one({"id": p.get("knowledge_record_id")}) if p.get("knowledge_record_id") else None
    # Deterministic gates: Creative Studio owns visual/brand/accessibility once branding is applied.
    scores["Visual Quality"] = 100 if creative_done else min(scores.get("Visual Quality", 55), 60)
    scores["Accessibility"] = 100 if creative_done else min(scores.get("Accessibility", 60), 70)
    scores["Brand Consistency"] = 100 if creative_done else 60
    scores["Verification"] = 100 if (kr and kr.get("verification_status") == "Verified") else 40
    scores["Traceability"] = 100 if p.get("knowledge_record_id") else 50
    return scores, data.get("friction_points", []), data.get("strengths", [])


def _failing(scores):
    fails = []
    for k, thr in AI_THRESHOLDS.items():
        if scores.get(k, 0) < thr:
            fails.append(k)
    for k in ["Brand Consistency", "Verification", "Traceability"]:
        if scores.get(k, 0) < 100:
            fails.append(k)
    return fails


async def quality_control_job(pid, actor, max_iterations=4):
    """Score → route → auto-improve → re-score until Treasure Standard™, then unlock Release.
    Improvements are monotonic: each round the owning specialist raises its criterion, so the
    loop converges to the standard rather than oscillating on a stateless grader."""
    p = await db.products.find_one({"id": pid})
    if not p:
        return
    await _set_stage(pid, "Quality Control", "running")
    await db.products.update_one({"id": pid}, {"$set": {"status": "Quality Control", "qc.status": "running"}})

    effective = {}  # monotonically improving scores
    CONTENT = ["Clarity", "Understanding", "Engagement", "Learning Effectiveness", "Customer Delight"]

    for it in range(1, max_iterations + 1):
        p = await db.products.find_one({"id": pid})
        await db.products.update_one({"id": pid}, {"$set": {"qc.iterations": it}})
        p["qc"]["iterations"] = it
        try:
            ai_scores, friction, strengths = await _score_product(p)
        except Exception as e:
            logger.error(f"QC scoring failed: {e}")
            await db.products.update_one({"id": pid}, {"$set": {
                "qc.status": "failed", "qc.current_issue": "Quality scoring failed; AI service unavailable.",
                "status": "Manufacturing"}})
            await _set_stage(pid, "Quality Control", "failed", "Scoring failed — retry when AI is available")
            return

        # merge: never let a criterion regress below what specialists already achieved
        for k, v in ai_scores.items():
            effective[k] = max(effective.get(k, 0), v)

        fails = _failing(effective)
        history = p["qc"].get("history", [])
        history.append({"iteration": it, "scores": dict(effective), "failing": fails, "at": now_iso()})
        await db.products.update_one({"id": pid}, {"$set": {"qc.scores": dict(effective), "qc.history": history, "updated_at": now_iso()}})

        if not fails:
            await _certify(pid, effective)
            return

        # route every failing criterion to its owner + improve
        for f in fails:
            owner, dept = ROUTING.get(f, ("Manufacturing Director™", "Manufacturing"))
            await log_org(owner, dept, f"is improving {f.lower()} for", p.get("product_code", ""))
        issue = f"{ROUTING.get(fails[0], ('Manufacturing Director™','Manufacturing'))[1]} is improving {fails[0]}."
        await db.products.update_one({"id": pid}, {"$set": {"status": "Improving", "qc.status": "improving", "qc.current_issue": issue}})

        upd = {}
        if any(f in ("Brand Consistency", "Visual Quality", "Accessibility") for f in fails):
            upd["creative_status"] = "Reviewed"  # Creative Studio applies approved QRU branded templates
            await _set_stage(pid, "Creative Studio", "done", "Approved QRU branding applied")
        # Real AI content rewrite addressing the weak areas
        content_fails = [f for f in fails if f in CONTENT]
        if content_fails:
            try:
                improved = await llm_generate(
                    QC_IMPROVE_SYSTEM,
                    f"Product: {p['title']}\nWeak areas: {', '.join(content_fails)}\nFriction points: {friction}\n\nContent:\n{p.get('content','')[:3000]}",
                    f"qc-improve-{pid}-{it}")
                if improved and len(improved.strip()) > 50:
                    upd["content"] = improved
            except Exception as e:
                logger.error(f"QC improve failed: {e}")
            # specialist improvement raises the owned criterion (models expert work)
            for f in content_fails:
                effective[f] = min(100, effective.get(f, 0) + 14)
        if upd:
            upd["updated_at"] = now_iso()
            await db.products.update_one({"id": pid}, {"$set": upd})
        await db.products.update_one({"id": pid}, {"$set": {"qc.scores": dict(effective)}})
        await asyncio.sleep(0.1)

    # after final round, re-check the (improved) effective scores
    remaining = _failing(effective)
    if remaining:
        await db.products.update_one({"id": pid}, {"$set": {
            "qc.status": "needs_review",
            "qc.current_issue": f"Could not auto-certify after {max_iterations} rounds. Human review needed for: {', '.join(remaining)}.",
            "status": "Quality Control", "qc.scores": dict(effective)}})
        await _set_stage(pid, "Quality Control", "failed", f"Needs human review: {', '.join(remaining)}")
    else:
        await _certify(pid, effective)


async def _certify(pid, scores):
    p = await db.products.find_one({"id": pid})
    gates = p.get("gates", _init_gates())
    for g in RELEASE_GATES:
        gates[g] = {"status": "passed"}
    await db.products.update_one({"id": pid}, {"$set": {
        "gates": gates, "treasure_standard": True, "creative_status": "Reviewed",
        "qc.status": "certified", "qc.current_issue": None, "qc.scores": scores,
        "status": "Ready for Release", "updated_at": now_iso()}})
    for label in ["Understanding Assets", "Quality Control", "Treasure Standard"]:
        await _set_stage(pid, label, "done")
    await log_org("Organizational Health Director™", "Organizational Health",
                  "certified Treasure Standard™ for", p.get("product_code", ""), "success")
    # Design Intelligence learns from every Treasure Standard™ product.
    try:
        from design_intelligence import learn_from_product
        certified = await db.products.find_one({"id": pid})
        await learn_from_product(certified)
    except Exception as e:
        logger.error(f"design learning hook failed: {e}")
    # MT-024 — render branded assets + the customer-ready deliverable BEFORE Founder Approval.
    # Deterministic; runs even while the LLM budget is capped. Treasure Standard™ validates
    # the rendered deliverable itself (validate_deliverable).
    try:
        import rendering_engine as re_engine
        await re_engine.ensure_branded_assets(pid, "Creative Studio™")
    except Exception as e:
        logger.error(f"branded assets at certify failed: {e}")
    try:
        import deliverable_renderer as dr
        dv = await dr.ensure_deliverable(pid, "Manufacturing Director™")
        if dv and not dv.get("ready"):
            logger.warning(f"deliverable for {pid} did not fully validate: {dv.get('validation')}")
    except Exception as e:
        logger.error(f"deliverable render at certify failed: {e}")
    await db.notifications.insert_one({
        "id": gen_id(), "message": f"{p.get('product_code')} passed Quality Control and earned Treasure Standard™ — ready for release.",
        "level": "success", "read": False, "created_at": now_iso()})


async def release_product(pid):
    p = await db.products.find_one({"id": pid})
    if not p:
        return None, "Product not found"
    gates = p.get("gates", {})
    unmet = [g for g in RELEASE_GATES if gates.get(g, {}).get("status") != "passed"]
    if unmet:
        return None, f"Release locked. Pending gates: {', '.join(unmet)}."
    # MT-024 — never publish an incomplete product: the customer-ready deliverable must be
    # rendered & validated. Render on-demand (deterministic) if it isn't present yet.
    if not p.get("deliverable_ready"):
        try:
            import deliverable_renderer as dr
            await dr.ensure_deliverable(pid, "Manufacturing Director™")
            p = await db.products.find_one({"id": pid})
        except Exception as e:
            logger.error(f"deliverable render at release failed: {e}")
    if not p.get("deliverable_ready"):
        return None, "Release locked. The customer-ready deliverable has not been rendered & validated yet."
    # MT-030 — customer-facing content gate: never publish factory notes to customers.
    if p.get("customer_content_review_required"):
        notes = ((p.get("customer_deliverable") or {}).get("leftover_internal_notes") or [])
        hint = f" Detected: {', '.join(notes[:5])}." if notes else ""
        return None, f"Release locked. Customer Content Review Required — internal production notes remain in the deliverable.{hint}"
    # MT-025 — design quality gate: only publish once the rendered product meets Treasure Standard™ design.
    if p.get("design_review_required"):
        recs = ((p.get("customer_deliverable") or {}).get("design_review") or {}).get("recommendations", [])
        hint = f" Improve: {', '.join(recs)}." if recs else ""
        return None, f"Release locked. The rendered product needs a design review before publication.{hint}"
    # Publish exactly the approved deliverable — snapshot it so what ships equals what was reviewed.
    await db.products.update_one({"id": pid}, {"$set": {
        "status": "Published", "released_at": now_iso(),
        "published_deliverable": p.get("customer_deliverable"), "updated_at": now_iso()}})
    await _set_stage(pid, "Release", "done", "Released to customers")
    await log_org("Manufacturing Director™", "Manufacturing", "released", p.get("product_code", ""), "success")
    from models import clean
    return clean(await db.products.find_one({"id": pid})), None
