"""QRU QuickStart™ Book + Founder Review Shelf™ + Enterprise Shelving System™ (Stabilization Sprint).

Mission: manufacture ONE excellent product consistently. The founder selects a governed
Knowledge Record, chooses Book → QuickStart™, presses Manufacture, and reviews the rendered
book IN-FACTORY (no download) on the Founder Review Shelf™ — then approves, requests revision,
archives, publishes, or exports on demand.

Principles: Optimize for Understanding not Complexity™ · Meaning Before Metadata™ ·
Manufacturing Should Be Easier Than Making Mistakes™.
"""
import logging
from database import db
from models import gen_id, now_iso, clean
from ai_service import llm_generate, parse_json
import deliverable_renderer as dr
from media_division import _resolve_kr, _is_verified, _promise_manifest
from org_activity import log_org

logger = logging.getLogger("qru.quickstart")

# The QuickStart™ Recipe — a fixed, concise, high-understanding-density structure.
QUICKSTART_SECTIONS = [
    ("what_it_is", "What It Is", "One clear, plain-language definition anyone can grasp."),
    ("why_it_matters", "Why It Matters", "Why this genuinely helps the reader's life."),
    ("core_idea", "The Core Idea", "The single most important thing to understand, explained simply."),
    ("simple_analogy", "A Simple Analogy", "An everyday comparison that makes it click."),
    ("try_today", "Try It Today", "One concrete, doable action the reader can take now."),
    ("remember_this", "Remember This", "A memorable one-sentence takeaway."),
]
QS_KEYS = [k for k, _, _ in QUICKSTART_SECTIONS]

QS_SYSTEM = (
    "You are the QRU QuickStart™ author. Optimize for UNDERSTANDING, not length. Govern the voice by the "
    "Approved Knowledge Record Manufacturing Standard™: begin with hope and possibility, preserve dignity, "
    "teach capability first, warm and encouraging yet fully truthful. Use ONLY the verified knowledge provided "
    "— never invent facts. Every sentence must earn its place; no padding, no filler. Write for a curious "
    "beginner. Return STRICT JSON with these keys (each a concise paragraph, 'try_today' as a paragraph, "
    "'remember_this' as ONE sentence): what_it_is, why_it_matters, core_idea, simple_analogy, try_today, "
    "remember_this. No markdown fences."
)


def shelf_location(p):
    """Enterprise Shelving System™ — deterministic governed location for any artifact."""
    division = p.get("division") or "Publishing"
    ptype = p.get("product_type", "Artifact")
    family = p.get("family") or "General"
    status = p.get("status", "Draft")
    stage = ("Review Shelf" if status in ("In Review", "Draft")
             else "Published Shelf" if status == "Published"
             else "Archive" if status == "Archived"
             else "Approved Shelf" if status == "Approved"
             else "Revision Shelf" if status == "Needs Revision"
             else "Shelf")
    return f"{division} › {ptype} › {family} › {stage}"


def _content_md(fields):
    out = []
    for key, heading, _ in QUICKSTART_SECTIONS:
        body = fields.get(key)
        if isinstance(body, list):
            body = "\n".join(f"- {x}" for x in body)
        out.append(f"## {heading}\n\n{(body or '').strip()}")
    return "\n\n".join(out)


def acceptance_criteria(product, fields):
    """Book Acceptance Criteria — understanding & clarity first, not page count."""
    content = product.get("content", "") or ""
    words = len(content.split())
    remember = str(fields.get("remember_this", "")).strip()
    all_sections = all(str(fields.get(k, "")).strip() for k in QS_KEYS)
    # crude clarity proxy: average sentence length (shorter = clearer)
    sentences = [s for s in content.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    avg_len = (words / max(1, len(sentences)))
    checks = [
        {"item": "Fulfills the QuickStart™ promise (all 6 understanding sections present)", "pass": all_sections},
        {"item": "Concise & high-density (250–1200 words, no padding)", "pass": 250 <= words <= 1200},
        {"item": "Clear language (avg sentence ≤ 26 words)", "pass": avg_len <= 26},
        {"item": "Leaves a memorable takeaway ('Remember This')", "pass": 6 <= len(remember.split()) <= 40},
        {"item": "Inherits a verified Knowledge Record™", "pass": bool(product.get("knowledge_record_id"))},
    ]
    passed = sum(1 for c in checks if c["pass"])
    return {"checks": checks, "passed": passed, "total": len(checks),
            "ready": passed == len(checks), "word_count": words}


async def manufacture_quickstart(kr_id, actor, base_url=""):
    kr = await _resolve_kr(kr_id)
    if not kr:
        return {"ok": False, "error": "Knowledge Record not found."}
    if not _is_verified(kr):
        return {"ok": False, "error": "This Knowledge Record is not yet Verified. Approve it first — "
                "a QuickStart™ Book must inherit from verified knowledge (Knowledge-First)."}
    context = (f"Topic: {kr.get('title')}\nAudience: {kr.get('target_audience') or 'A curious beginner'}\n"
               f"Verified Truth: {kr.get('verified_truth','')}\n"
               f"Why It Matters: {kr.get('why_it_matters','')}\n"
               f"Everyday Analogy: {kr.get('everyday_analogy','')}\n"
               f"Real-World Example: {kr.get('real_world_example','')}\n"
               f"Memorable Line: {kr.get('memory_sentence','')}")
    try:
        fields = parse_json(await llm_generate(QS_SYSTEM, context, f"quickstart-{kr_id}")) or {}
    except Exception:
        return {"ok": False, "error": "The QuickStart™ author is temporarily unavailable. Please try again shortly."}
    if not all(fields.get(k) for k in QS_KEYS):
        return {"ok": False, "error": "The draft was incomplete. Please try manufacturing again."}

    count = await db.products.count_documents({})
    product = {
        "id": gen_id(), "product_code": f"PRD-{count + 1:05d}",
        "title": f"{kr.get('title')} — QuickStart™", "product_type": "Book", "family": "QuickStart™",
        "division": "Publishing", "topic": kr.get("title"),
        "audience": kr.get("target_audience") or "A curious beginner", "learning_level": "QuickStart",
        "content": _content_md(fields), "quickstart_fields": fields,
        "status": "In Review", "knowledge_record_id": kr.get("id"), "kr_version": kr.get("version", 1),
        "assembled": False, "asset_mode": "director", "manufactured_by": "QuickStart™ Recipe",
        "manufacturing_promise": _promise_manifest(kr), "on_review_shelf": True,
        "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    product["shelf_location"] = shelf_location(product)
    await db.products.insert_one(dict(product))
    await db.knowledge_records.update_one({"id": kr.get("id")}, {"$inc": {"products_created": 1}})
    try:
        await dr.ensure_deliverable(product["id"], actor=actor, base_url=base_url, build_marketing=False)
    except Exception as e:
        logger.warning(f"quickstart render failed: {e}")
    product = clean(await db.products.find_one({"id": product["id"]}))
    crit = acceptance_criteria(product, fields)
    await db.products.update_one({"id": product["id"]}, {"$set": {"acceptance": crit}})
    files = (product.get("customer_deliverable") or {}).get("files", [])
    preview = next((f["url"] for f in files if f["format"] == "html"), None)
    await log_org("QuickStart™ Recipe", "Publishing",
                  f"manufactured {product['product_code']} → Founder Review Shelf™", product["product_code"], "success")
    return {"ok": True, "product": product, "acceptance": crit, "preview_url": preview,
            "shelf_location": product["shelf_location"]}


def _enrich(p):
    files = (p.get("customer_deliverable") or {}).get("files", [])
    return {
        "id": p["id"], "product_code": p.get("product_code"), "title": p.get("title"),
        "product_type": p.get("product_type"), "family": p.get("family"), "status": p.get("status"),
        "shelf_location": p.get("shelf_location") or shelf_location(p),
        "acceptance": p.get("acceptance"), "kr_code": None,
        "preview_url": next((f["url"] for f in files if f["format"] == "html"), None),
        "files": files, "cover_url": p.get("cover_url"), "revision_notes": p.get("revision_notes"),
        "created_at": p.get("created_at"), "updated_at": p.get("updated_at"),
    }


async def review_shelf():
    items = await db.products.find({"on_review_shelf": True}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [_enrich(p) for p in items]


async def shelves():
    """Enterprise Shelving System™ overview — every shelved artifact grouped by governed location."""
    items = await db.products.find({"on_review_shelf": True}, {"_id": 0}).to_list(500)
    grouped = {}
    for p in items:
        loc = p.get("shelf_location") or shelf_location(p)
        grouped.setdefault(loc, 0)
        grouped[loc] += 1
    return [{"location": k, "count": v} for k, v in sorted(grouped.items())]


async def _set_status(pid, status, extra=None):
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    upd = {"status": status, "updated_at": now_iso()}
    if extra:
        upd.update(extra)
    p2 = {**p, **upd}
    upd["shelf_location"] = shelf_location(p2)
    await db.products.update_one({"id": pid}, {"$set": upd})
    return clean(await db.products.find_one({"id": pid}, {"_id": 0}))


async def approve(pid, actor):
    return await _set_status(pid, "Approved", {"approved_by": actor, "approved_at": now_iso(),
                                               "founder_approved": True, "revision_notes": None})


async def request_revision(pid, actor, notes):
    return await _set_status(pid, "Needs Revision", {"revision_notes": notes or "Please revise.",
                                                     "revision_requested_by": actor})


async def archive(pid, actor):
    return await _set_status(pid, "Archived", {"archived_by": actor, "archived_at": now_iso()})


async def publish(pid, actor):
    p = await db.products.find_one({"id": pid})
    if not p:
        return {"ok": False, "error": "Not found."}
    if p.get("status") not in ("Approved",):
        return {"ok": False, "error": "Approve the book on the Founder Review Shelf™ before publishing."}
    kr = await db.knowledge_records.find_one({"id": p.get("knowledge_record_id")}, {"verification_status": 1, "approval_status": 1, "treasure_standard": 1})
    if kr and not _is_verified(kr):
        return {"ok": False, "error": "The source Knowledge Record must be Verified before publishing."}
    res = await _set_status(pid, "Published", {"published_by": actor, "published_at": now_iso()})
    await log_org("Founder", "Publishing", f"published {p.get('product_code')}", p.get("product_code"), "success")
    return {"ok": True, "product": res}


async def export_item(pid):
    p = await db.products.find_one({"id": pid}, {"_id": 0})
    if not p:
        return None
    await db.products.update_one({"id": pid}, {"$set": {"exported_at": now_iso()}})
    return {"product_code": p.get("product_code"), "title": p.get("title"),
            "files": (p.get("customer_deliverable") or {}).get("files", [])}


async def stats():
    def c(**q):
        return db.products.count_documents({"on_review_shelf": True, **q})
    return {
        "in_review": await c(status="In Review"),
        "approved": await c(status="Approved"),
        "needs_revision": await c(status="Needs Revision"),
        "published": await c(status="Published"),
        "archived": await c(status="Archived"),
    }
