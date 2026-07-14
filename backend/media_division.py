"""QRU Media Manufacturing Division™ (Stone 2 · Inheritance-First™).

One verified Knowledge Record™ → many governed products. Every output inherits from
the SAME verified source (Knowledge-First), reusing the existing manufacturing engines —
no independent workflows, no duplicated truth.

Documents & scripts → product generation + deliverable renderer (real PDF/EPUB/PPTX).
Posters/sl" visuals → Poster Studio™ (governed SVG).
Audio/video formats are declared here but manufactured by Cinema Studio™ / Podcast Studio™ (Stone 3).
"""
import logging
from database import db
from models import gen_id, now_iso
from ai_service import llm_generate
import deliverable_renderer as dr
import poster_studio as pstudio
from org_activity import log_org
from capability_registry import MANUFACTURING_PROMISE

logger = logging.getLogger("qru.media_division")

# The governed media catalog. Each output inherits verified knowledge, citations,
# branding, governance, Enterprise Memory™ and the Treasure Standard™.
CATALOG = [
    {"id": "book", "name": "Book", "kind": "document", "product_type": "Book", "division": "Publishing", "icon": "book"},
    {"id": "workbook", "name": "Workbook", "kind": "document", "product_type": "Workbook", "division": "Learning", "icon": "pencil"},
    {"id": "teacher_guide", "name": "Teacher Guide", "kind": "document", "product_type": "Teacher Guide", "division": "Learning", "icon": "graduation"},
    {"id": "family_guide", "name": "Parent / Family Guide", "kind": "document", "product_type": "Family Guide", "division": "Learning", "icon": "users"},
    {"id": "slides", "name": "Classroom Slides", "kind": "document", "product_type": "Presentation", "division": "Learning", "icon": "presentation"},
    {"id": "lesson_plan", "name": "Lesson Plan", "kind": "document", "product_type": "Lesson Plan", "division": "Learning", "icon": "clipboard"},
    {"id": "learning_poster", "name": "Learning Poster", "kind": "poster", "template": "illustrated-learning-v1", "division": "Marketing", "icon": "image"},
    {"id": "overview_poster", "name": "Overview Poster", "kind": "poster", "template": "give-credit-v1", "division": "Marketing", "icon": "layout"},
    {"id": "video_script", "name": "Video Script", "kind": "document", "product_type": "Video Script", "division": "Video", "icon": "clapperboard"},
    {"id": "podcast_script", "name": "Podcast Script", "kind": "document", "product_type": "Podcast Script", "division": "Audio", "icon": "mic"},
    {"id": "social", "name": "Social Media Clip Script", "kind": "document", "product_type": "Short-form Content", "division": "Marketing", "icon": "share"},
]
# Declared, manufactured by Stone 3 studios (shown as "coming from Cinema/Podcast Studio™").
FUTURE_CATALOG = [
    {"id": "audiobook", "name": "Audiobook", "division": "Audio", "by": "Podcast Studio™"},
    {"id": "podcast", "name": "Video Podcast", "division": "Audio", "by": "Podcast Studio™"},
    {"id": "motion_storybook", "name": "Motion Storybook™", "division": "Video", "by": "Cinema Studio™"},
    {"id": "animated_episode", "name": "Animated Episode", "division": "Video", "by": "Cinema Studio™"},
    {"id": "youtube_short", "name": "YouTube Short", "division": "Video", "by": "Cinema Studio™"},
    {"id": "promo_video", "name": "Promotional Video", "division": "Marketing", "by": "Cinema Studio™"},
]
CATALOG_BY_ID = {c["id"]: c for c in CATALOG}

RENDER_SYSTEM = (
    "You are the QRU Manufacturing Director producing a publication-ready {pt}. Use ONLY the verified "
    "knowledge provided — never invent facts. Govern the voice by the Approved Knowledge Record "
    "Manufacturing Standard™: begin with hope and possibility, preserve dignity, teach capability first, "
    "positive yet fully truthful. Structure the {pt} appropriately (clear title, sections/scenes/slides as "
    "fits the format) in clean Markdown. No production notes, no placeholders."
)


def _promise_manifest(kr):
    return {
        "inherits_from": {"kr_id": kr.get("id"), "kr_code": kr.get("kr_code"), "title": kr.get("title")},
        "pillars": [p["name"] for p in MANUFACTURING_PROMISE["pillars"]],
    }


async def _resolve_kr(kr_id):
    kr = await db.knowledge_records.find_one({"id": kr_id}, {"_id": 0})
    if not kr:
        kr = await db.knowledge_engine_records.find_one({"id": kr_id}, {"_id": 0})
        if kr:
            kr["title"] = kr.get("title") or kr.get("topic")
    return kr


def _is_verified(kr):
    if (kr.get("verification_status") == "Verified" or kr.get("approval_status") == "Approved"
            or bool(kr.get("treasure_standard")) or bool(kr.get("verified_external"))):
        return True
    # KR 2.0 (knowledge_engine_records): eligible only when externally verified (Knowledge-First honesty).
    st = str(kr.get("status") or "")
    return "Verified External" in st or "Gold Standard" in st


async def _manufacture_document(kr, spec, actor, base_url):
    pt = spec["product_type"]
    kr_id = kr.get("id")
    product = await db.products.find_one({"knowledge_record_id": kr_id, "product_type": pt})
    if not product:
        context = (
            f"Verified Truth: {kr.get('verified_truth','')}\n"
            f"QRU Translation: {kr.get('qru_translation') or kr.get('consumer_translation','')}\n"
            f"Why It Matters: {kr.get('why_it_matters','')}\n"
            f"Real-World Example: {kr.get('real_world_example','')}\n"
            f"Everyday Analogy: {kr.get('everyday_analogy','')}\n"
        )
        prompt = f"Topic: {kr.get('title')}\nAudience: {kr.get('target_audience') or 'General public'}\n{context}\nProduce the {pt}."
        try:
            content = await llm_generate(RENDER_SYSTEM.format(pt=pt), prompt, f"media-div-{kr_id}-{spec['id']}")
        except Exception:
            return {"format": spec["id"], "name": spec["name"], "ok": False,
                    "error": "AI writer temporarily unavailable — try again shortly."}
        count = await db.products.count_documents({})
        product = {
            "id": gen_id(), "product_code": f"PRD-{count + 1:05d}",
            "title": f"{kr.get('title')} — {spec['name']}", "product_type": pt,
            "family": kr.get("category", "General"), "topic": kr.get("title"),
            "audience": kr.get("target_audience") or "General public", "learning_level": "Introductory",
            "content": content, "status": "Draft", "knowledge_record_id": kr_id,
            "kr_version": kr.get("version", 1), "assembled": False, "asset_mode": "director",
            "manufactured_by": "Media Manufacturing Division™", "manufacturing_promise": _promise_manifest(kr),
            "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
        }
        await db.products.insert_one(dict(product))
        await db.knowledge_records.update_one({"id": kr_id}, {"$inc": {"products_created": 1}})
    try:
        await dr.ensure_deliverable(product["id"], actor=actor, base_url=base_url, build_marketing=False)
    except Exception as e:
        return {"format": spec["id"], "name": spec["name"], "ok": False, "error": f"Render failed: {str(e)[:120]}"}
    product = await db.products.find_one({"id": product["id"]}, {"_id": 0})
    files = (product.get("customer_deliverable") or {}).get("files", [])
    primary = (product.get("customer_deliverable") or {}).get("download_url")
    return {"format": spec["id"], "name": spec["name"], "kind": "document", "ok": True,
            "product_id": product["id"], "product_code": product.get("product_code"),
            "files": files, "primary": primary, "cover_url": product.get("cover_url")}


async def _manufacture_poster(kr, spec, actor):
    try:
        res = await pstudio.generate_poster(spec["template"], content=None, kr_id=kr.get("id"),
                                            is_factual=False, actor=actor)
    except Exception as e:
        return {"format": spec["id"], "name": spec["name"], "ok": False, "error": f"Poster failed: {str(e)[:120]}"}
    if res.get("error"):
        return {"format": spec["id"], "name": spec["name"], "ok": False, "error": res["error"]}
    return {"format": spec["id"], "name": spec["name"], "kind": "poster", "ok": True,
            "poster_id": res["id"], "png_url": res.get("png_url"), "pdf_url": res.get("pdf_url"),
            "thumb_url": res.get("thumb_url"), "status": res.get("status")}


async def manufacture_catalog(kr_id, format_ids, actor="Founder", base_url=""):
    kr = await _resolve_kr(kr_id)
    if not kr:
        return {"ok": False, "error": "Knowledge Record not found."}
    if not _is_verified(kr):
        return {"ok": False, "error": "This Knowledge Record is not yet Verified. Approve it first — "
                "every product must inherit from verified knowledge (Knowledge-First)."}
    format_ids = [f for f in (format_ids or []) if f in CATALOG_BY_ID] or [c["id"] for c in CATALOG]
    results = []
    for fid in format_ids:
        spec = CATALOG_BY_ID[fid]
        if spec["kind"] == "poster":
            results.append(await _manufacture_poster(kr, spec, actor))
        else:
            results.append(await _manufacture_document(kr, spec, actor, base_url))
    ok = sum(1 for r in results if r.get("ok"))
    await db.knowledge_records.update_one({"id": kr.get("id")}, {"$set": {"media_division_run_at": now_iso()}})
    await log_org("Media Manufacturing Division™", "Publishing",
                  f"manufactured {ok}/{len(results)} media formats from {kr.get('kr_code') or kr.get('title')}",
                  kr.get("kr_code") or "", "success" if ok else "warning")
    return {"ok": True, "kr": {"id": kr.get("id"), "kr_code": kr.get("kr_code"), "title": kr.get("title")},
            "manufactured": ok, "total": len(results), "results": results,
            "promise": _promise_manifest(kr)}


async def verified_krs(limit=100):
    from models import clean
    krs = await db.knowledge_records.find(
        {"$or": [{"verification_status": "Verified"}, {"approval_status": "Approved"},
                 {"treasure_standard": True}, {"verified_external": True}]},
        {"_id": 0, "id": 1, "kr_code": 1, "title": 1, "category": 1, "products_created": 1,
         "verification_status": 1, "media_division_run_at": 1}
    ).sort("created_at", -1).to_list(limit)
    for k in krs:
        k["schema"] = "kr1"
    # KR 2.0 (knowledge_engine_records): only externally verified Gold Standard records are eligible.
    ker = await db.knowledge_engine_records.find(
        {"status": {"$regex": "Verified External|Gold Standard"}},
        {"_id": 0, "id": 1, "kr_code": 1, "topic": 1, "recipe": 1, "status": 1, "version": 1, "products_created": 1}
    ).sort("created_at", -1).to_list(limit)
    for k in ker:
        k["title"] = k.get("topic")
        k["category"] = (k.get("recipe") or "Knowledge Engine")
        k["verification_status"] = "Verified"
        k["schema"] = "kr2"
    return clean(krs) + clean(ker)


async def stats():
    verified = await db.knowledge_records.count_documents(
        {"$or": [{"verification_status": "Verified"}, {"approval_status": "Approved"}, {"treasure_standard": True}]})
    from_division = await db.products.count_documents({"manufactured_by": "Media Manufacturing Division™"})
    return {"verified_krs": verified, "formats": len(CATALOG), "future_formats": len(FUTURE_CATALOG),
            "products_from_division": from_division}
