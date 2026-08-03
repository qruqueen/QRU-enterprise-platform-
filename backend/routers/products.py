from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import asyncio

from database import db
from auth import get_current_user, require_super_admin
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


class BindInput(BaseModel):
    kr_id: str


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
    import ukr_governance
    kr = await ukr_governance.require_verified_ukr(data.knowledge_record_id, data.product_type)
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


# --- Publication Quality Standard™ (Phase 2) — production re-render batch (zero AI spend) ---
_RERENDER_JOB = "deliverable_rerender_jobs"
_DOC_CATS = {"book", "guide", "workbook", "card"}


async def _rerender_worker(actor, base_url=""):
    import product_recipes as pr
    import deliverable_renderer as dr
    prods = await db.products.find({"content": {"$exists": True, "$ne": ""}},
                                   {"id": 1, "product_type": 1, "title": 1}).to_list(10000)
    docs = [p for p in prods if pr.get_recipe(p.get("product_type", "")).get("category") in _DOC_CATS]
    ids = [p["id"] for p in docs]
    total = len(ids)
    done = ok = failed = 0
    failed_ids = []
    await db[_RERENDER_JOB].update_one({"id": "current"}, {"$set": {
        "id": "current", "status": "running", "total": total, "done": 0, "ok": 0, "failed": 0,
        "failed_ids": [], "started_at": now_iso(), "finished_at": None, "by": actor}}, upsert=True)
    for pid in ids:
        try:
            res = await dr.ensure_deliverable(pid, actor=actor, base_url=base_url,
                                              build_marketing=False, allow_ai_cover=False)
            if res and res.get("files"):
                ok += 1
            else:
                failed += 1; failed_ids.append(pid)
        except Exception:
            failed += 1; failed_ids.append(pid)
        done += 1
        if done % 5 == 0:
            await db[_RERENDER_JOB].update_one({"id": "current"},
                                               {"$set": {"done": done, "ok": ok, "failed": failed,
                                                         "failed_ids": failed_ids}})
    await db[_RERENDER_JOB].update_one({"id": "current"}, {"$set": {
        "status": "complete", "done": done, "ok": ok, "failed": failed, "failed_ids": failed_ids,
        "finished_at": now_iso()}})


async def _eligible_doc_count():
    import product_recipes as pr
    prods = await db.products.find({"content": {"$exists": True, "$ne": ""}},
                                   {"id": 1, "product_type": 1}).to_list(10000)
    return sum(1 for p in prods if pr.get_recipe(p.get("product_type", "")).get("category") in _DOC_CATS)


async def rerender_handler(job, progress):
    p = job.get("payload") or {}
    await _rerender_worker(p.get("actor", "Founder"), p.get("base_url", ""))
    return {"operation": "doc_rerender"}


async def reconcile_stale_rerender():
    """Resume a document re-render batch left 'running' by a pre-Spine restart ($0 AI, safe)."""
    import job_engine
    j = await db[_RERENDER_JOB].find_one({"id": "current"}, {"_id": 0})
    if not j or j.get("status") != "running":
        return False
    await job_engine.enqueue("doc_rerender_run",
                             payload={"actor": j.get("by", "System (resume)"), "base_url": ""},
                             title="Publication Quality re-render (resumed)",
                             dedupe_key="doc_rerender:current", max_attempts=3, created_by="System")
    return True


@router.post("/rerender-documents")
async def rerender_documents(request: Request, user=Depends(require_super_admin)):
    """Re-render EVERY document-family product so it inherits the QRU Publication Quality Standard™.
    Zero AI cover spend. Runs on the durable Spine; poll /rerender-documents/status."""
    import job_engine
    active = (await job_engine.list_jobs(status="running", job_type="doc_rerender_run", limit=1)
              or await job_engine.list_jobs(status="queued", job_type="doc_rerender_run", limit=1))
    if active:
        existing = await db[_RERENDER_JOB].find_one({"id": "current"}, {"_id": 0}) or {}
        return {"ok": True, "status": "running", "message": "A re-render batch is already running.",
                **{k: existing.get(k) for k in ("total", "done", "ok", "failed")}}
    base_url = str(request.base_url).rstrip("/")
    await job_engine.enqueue("doc_rerender_run",
                             payload={"actor": user.get("name", "Founder"), "base_url": base_url},
                             title="Publication Quality re-render", dedupe_key="doc_rerender:current",
                             max_attempts=3, created_by=user.get("name", "Founder"))
    return {"ok": True, "status": "started",
            "message": "Publication Quality re-render started (zero AI spend). Poll status to track."}


@router.get("/rerender-documents/status")
async def rerender_documents_status(user=Depends(get_current_user)):
    j = await db[_RERENDER_JOB].find_one({"id": "current"}, {"_id": 0})
    eligible = await _eligible_doc_count()
    base = {"status": "idle", "total": 0, "done": 0, "ok": 0, "failed": 0, "failed_ids": []}
    if j:
        base.update(j)
    base["eligible_count"] = eligible
    if base.get("status") in ("running", "complete"):
        base["remaining"] = max(0, (base.get("total", 0) or 0) - (base.get("done", 0) or 0))
    else:
        base["remaining"] = eligible
    return base


# --- Signed short-lived deliverable access tokens (Preview / Download) ---
class FileTokenIn(BaseModel):
    format: str = "pdf"
    action: str = "preview"  # "preview" | "download"


@router.post("/{pid}/file-token")
async def file_token(pid: str, data: FileTokenIn, user=Depends(get_current_user)):
    """Mint a signed, ~10-min token scoped to the EXACT file + user + action. Preview picks a
    browser-renderable representation (PDF for EPUB/PPTX/DOCX); download returns the requested original."""
    if data.action not in ("preview", "download"):
        raise HTTPException(400, "action must be preview or download")
    p = await db.products.find_one({"id": pid}, {"_id": 0, "customer_deliverable": 1, "title": 1})
    if not p:
        raise HTTPException(404, "Product not found.")
    files = (p.get("customer_deliverable") or {}).get("files") or []
    if not files:
        raise HTTPException(404, "This product has no rendered deliverable yet.")
    renderable = {"pdf", "png", "jpg", "jpeg", "html", "mp3", "mp4"}
    fmt = data.format
    requested = next((x for x in files if x.get("format") == fmt), None)
    if data.action == "preview":
        target = requested if (requested and fmt in renderable) else None
        if not target:
            target = (next((x for x in files if x.get("format") == "pdf"), None)
                      or next((x for x in files if x.get("format") == "html"), None)
                      or next((x for x in files if x.get("format") in renderable), None))
    else:
        target = requested or next((x for x in files if x.get("format") == "pdf"), None) or files[0]
    if not target:
        raise HTTPException(404, "No suitable deliverable file found.")
    fid = target.get("filename")
    if not fid or not str(fid).startswith("deliverable-"):
        raise HTTPException(400, "Deliverable file is not token-protected.")
    import deliverable_tokens as dt
    from urllib.parse import quote
    tok = dt.mint(fid, user["id"], data.action)
    url = f"/api/rendering/asset/{fid}?token={tok}"
    if data.action == "download":
        safe = f"{p.get('title', 'download')}"
        url += f"&download=1&name={quote(safe)}"
    return {"url": url, "format": target.get("format"), "media_type": target.get("media_type"),
            "action": data.action, "expires_in": 600,
            "is_representation": bool(data.action == "preview" and requested and target is not requested)}


class FidTokenIn(BaseModel):
    fid: str
    action: str = "preview"


@router.post("/file-token-by-fid")
async def file_token_by_fid(data: FidTokenIn, user=Depends(require_super_admin)):
    """Mint a token for a specific protected deliverable file id (super-admin Factory tools that hold
    raw asset ids, e.g. Founder Inbox). Only deliverable-* files are token-eligible."""
    if data.action not in ("preview", "download"):
        raise HTTPException(400, "action must be preview or download")
    fid = (data.fid or "").split("/")[-1].split("?")[0]
    if not fid.startswith("deliverable-"):
        raise HTTPException(400, "Only deliverable files are token-protected.")
    import deliverable_tokens as dt
    from urllib.parse import quote
    tok = dt.mint(fid, user["id"], data.action)
    url = f"/api/rendering/asset/{fid}?token={tok}"
    if data.action == "download":
        url += f"&download=1&name={quote(fid)}"
    return {"url": url, "action": data.action, "expires_in": 600}


# --- QA Cleanup™ (super-admin, soft-delete to Trash, audit-logged) ---
import qa_cleanup as qa


class QAMarkIn(BaseModel):
    qa_status: Optional[str] = None  # test | qa | preview | null


class QADeleteIn(BaseModel):
    reason: Optional[str] = "QA cleanup"


class QAPermanentIn(BaseModel):
    confirm_title: str


@router.post("/{pid}/qa-status")
async def qa_mark(pid: str, data: QAMarkIn, user=Depends(require_super_admin)):
    res = await qa.set_qa_status(pid, data.qa_status, user.get("name", "Founder"))
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.get("/qa-cleanup/eligible")
async def qa_eligible(user=Depends(require_super_admin)):
    return await qa.eligible_list()


@router.post("/{pid}/qa-cleanup")
async def qa_soft_delete(pid: str, data: QADeleteIn, user=Depends(require_super_admin)):
    res = await qa.soft_delete(pid, data.reason, user.get("name", "Founder"))
    if res.get("error"):
        raise HTTPException(400, res["error"] + (" " + "; ".join(res.get("blockers", [])) if res.get("blockers") else ""))
    return res


@router.get("/qa-cleanup/trash")
async def qa_trash(user=Depends(require_super_admin)):
    return await qa.trash_list()


@router.post("/qa-cleanup/trash/{trash_id}/restore")
async def qa_restore(trash_id: str, user=Depends(require_super_admin)):
    res = await qa.restore(trash_id, user.get("name", "Founder"))
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.post("/qa-cleanup/trash/{trash_id}/permanent-delete")
async def qa_permanent(trash_id: str, data: QAPermanentIn, user=Depends(require_super_admin)):
    res = await qa.permanent_delete(trash_id, user.get("name", "Founder"), data.confirm_title)
    if res.get("error"):
        raise HTTPException(400, res["error"] + (" " + "; ".join(res.get("blockers", [])) if res.get("blockers") else ""))
    return res


@router.get("/qa-cleanup/audit")
async def qa_audit(user=Depends(require_super_admin)):
    return await qa.audit_log()


@router.get("/ukr-audit")
async def ukr_audit(user=Depends(get_current_user)):
    """UKR-traceability audit: green (verified UKR) / amber (unverified/dangling) / red (no UKR)."""
    import ukr_governance
    return await ukr_governance.audit_report()


@router.get("/ukr-audit/details")
async def ukr_audit_details(user=Depends(get_current_user)):
    """Red + amber products needing remediation (published-noncompliant surfaced first)."""
    import ukr_governance
    prods = await db.products.find({}, {"_id": 0}).to_list(5000)
    rows = []
    for p in prods:
        t = await ukr_governance.traceability(p)
        if t["status"] == "green":
            continue
        rows.append({"id": p.get("id"), "code": p.get("product_code"), "title": p.get("title"),
                     "product_type": p.get("product_type"), "topic": p.get("topic"),
                     "knowledge_record_id": p.get("knowledge_record_id"),
                     "status": p.get("status"), "trace_status": t["status"], "reason": t["reason"],
                     "published": str(p.get("status", "")).lower() == "published"})
    rows.sort(key=lambda r: (not r["published"], r["trace_status"] != "red"))
    return {"items": rows, "count": len(rows)}


@router.get("/{pid}/ukr-suggestions")
async def ukr_suggestions(pid: str, user=Depends(get_current_user)):
    import ukr_governance
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    return {"suggestions": await ukr_governance.suggest_krs(p)}


@router.post("/{pid}/ukr-bind")
async def ukr_bind(pid: str, data: BindInput, user=Depends(get_current_user)):
    """Bind a product to a chosen VERIFIED KR (validated). Never silent/automatic."""
    import ukr_governance
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    kr = await ukr_governance.require_verified_ukr(data.kr_id, p.get("product_type", ""))
    await db.products.update_one({"id": pid}, {"$set": {
        "knowledge_record_id": kr["id"], "governance_status": "governed",
        "governed_by": user.get("name", "Founder"), "updated_at": now_iso()}})
    return {"ok": True, "bound_to": {"id": kr["id"], "kr_code": kr.get("kr_code"), "title": kr.get("title")}}


@router.post("/{pid}/ukr-quarantine")
async def ukr_quarantine(pid: str, user=Depends(get_current_user)):
    """Quarantine a product that cannot be safely governed (non-destructive: unpublish + flag)."""
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    await db.products.update_one({"id": pid}, {"$set": {
        "governance_status": "quarantined", "status": "Archived",
        "quarantined_by": user.get("name", "Founder"), "updated_at": now_iso()}})
    return {"ok": True, "governance_status": "quarantined"}


@router.post("/{pid}/ukr-exception")
async def ukr_exception(pid: str, user=Depends(get_current_user)):
    """Classify a product as the governed Founder-authored manuscript exception."""
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    await db.products.update_one({"id": pid}, {"$set": {
        "founder_authored": True, "governance_status": "founder_exception",
        "classified_by": user.get("name", "Founder"), "updated_at": now_iso()}})
    return {"ok": True, "governance_status": "founder_exception"}


@router.get("/{pid}")
async def get_product(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    return clean(p)


@router.post("/generate")
async def generate_product(data: GenerateInput, user=Depends(get_current_user)):
    import ukr_governance
    # Knowledge-First™ enforcement — educational products must inherit from a Verified UKR.
    kr = await ukr_governance.require_verified_ukr(data.knowledge_record_id, data.product_type)
    topic = kr["title"]
    family = kr.get("category", "General")

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
        import ukr_governance
        trace = await ukr_governance.traceability(p)
        if trace["status"] != "green":
            raise HTTPException(422, f"Knowledge-First™ publish guard: {trace['reason']}. Bind this product "
                                     "to a Verified Knowledge Record before publishing.")
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
