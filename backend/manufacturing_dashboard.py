"""QRU Enterprise Manufacturing Dashboard™ — each verified Knowledge Record as a living dashboard
of everything manufactured from it (Knowledge-first, not product-first). Honest status only.
"""
from database import db
import project_zero as pz
import manufacturing_foundation as mf

# Canonical product lifecycle for a Knowledge Record.
#  - route     → opens the studio that manufactures it (multi-step / approval driven)
#  - recipe    → a KR-inheriting PDF recipe manufacturable in-place (one click, no data entry)
#  - coming_soon → declared archetype with no builder yet (honestly surfaced, never faked)
PRODUCT_SPEC = [
    {"type": "Storyboard Master™", "key": "storyboard", "route": "/storyboard-studio"},
    {"type": "Knowledge Card™", "key": "knowledge_card", "route": "/poster-studio"},
    {"type": "Poster", "key": "poster", "route": "/poster-studio"},
    {"type": "Data Poster", "key": "data_poster", "route": "/poster-studio"},
    {"type": "Video", "key": "video", "route": "/storyboard-studio"},
    {"type": "Audio Lesson", "key": "audio", "route": "/storyboard-studio"},
    {"type": "Presentation", "key": "presentation", "route": "/storyboard-studio"},
    {"type": "Book / Publication", "key": "publication", "route": "/manufacture"},
    {"type": "Workbook", "key": "workbook", "recipe": "workbook"},
    {"type": "Student Workbook", "key": "student_workbook", "recipe": "student_workbook"},
    {"type": "Instructor Guide", "key": "instructor_guide", "recipe": "instructor_guide"},
    {"type": "Assessment Pack", "key": "assessment_pack", "recipe": "assessment_pack"},
    {"type": "Podcast", "key": "podcast", "route": "/storyboard-studio"},
    {"type": "Course", "key": "course", "coming_soon": True},
    {"type": "Audiobook", "key": "audiobook", "coming_soon": True},
    {"type": "Marketing Assets", "key": "marketing", "coming_soon": True},
    {"type": "Product Bundle", "key": "bundle", "coming_soon": True},
]
INHERITED_KEYS = ("workbook", "student_workbook", "instructor_guide", "assessment_pack")
DATA_TEMPLATES = {"data-comparison-v1", "scorecard-grid-v1", "decoder-v1"}


async def _kr(kr_id):
    for coll in (db.knowledge_engine_records, db.knowledge_records):
        d = await coll.find_one({"id": kr_id}, {"_id": 0})
        if d:
            return d
    return None


async def _collect(kr_id):
    posters = [p async for p in db.poster_assets.find({"kr_id": kr_id}, {"_id": 0})]
    media = [m async for m in db.media_products.find({"kr_id": kr_id}, {"_id": 0})]
    storyboards = [s async for s in db.storyboard_masters.find({"kr_id": kr_id}, {"_id": 0})]
    products = [p async for p in db.products.find({"knowledge_record_id": kr_id}, {"_id": 0})]
    inherited = [i async for i in db.inherited_products.find({"kr_id": kr_id}, {"_id": 0})]
    return posters, media, storyboards, products, inherited


def _poster_item(p):
    return {"id": p["id"], "label": p.get("title") or p.get("family"), "status": p.get("status"),
            "thumb": f"/api/publishing/poster/{p['id']}/file?format=thumb"}


def _media_item(m):
    return {"id": m["id"], "label": m.get("label"), "status": m.get("status"),
            "render_status": m.get("render_status")}


def _inherited_item(i):
    f = (i.get("files") or [{}])[0]
    return {"id": i["id"], "label": i.get("label"), "status": i.get("status"),
            "download": f.get("url"), "treasure_status": i.get("treasure_status")}


async def kr_manufacturing(kr_id):
    kr = await _kr(kr_id)
    if not kr:
        return None
    posters, media, storyboards, products, inherited = await _collect(kr_id)
    verif = kr.get("verification") or {}
    verified = bool(verif.get("evidence_sufficient_for_external_publication") or kr.get("verified_external"))

    built = {
        "storyboard": [{"id": s["id"], "label": s["sb_code"], "status": "READY"} for s in storyboards],
        "knowledge_card": [_poster_item(p) for p in posters if p.get("template_id") == "knowledge-card-v1"],
        "poster": [_poster_item(p) for p in posters if p.get("template_id") not in DATA_TEMPLATES and p.get("template_id") != "knowledge-card-v1"],
        "data_poster": [_poster_item(p) for p in posters if p.get("template_id") in DATA_TEMPLATES],
        "video": [_media_item(m) for m in media if m.get("format") in ("youtube_video", "promo_short")],
        "audio": [_media_item(m) for m in media if m.get("format") == "audio_lesson"],
        "presentation": [_media_item(m) for m in media if m.get("format") in ("teacher_presentation", "student_presentation")],
        "publication": [{"id": p["id"], "label": p.get("title"), "status": p.get("status")} for p in products],
    }
    for key in INHERITED_KEYS:
        built[key] = [_inherited_item(i) for i in inherited if i.get("type") == key]

    matrix = []
    for spec in PRODUCT_SPEC:
        items = built.get(spec["key"], [])
        published = any((i.get("status") or "").upper().startswith(("PUBLISH", "GOLD")) for i in items)
        if spec.get("coming_soon"):
            state = "coming_soon"
        elif items:
            state = "published" if published else "manufactured"
        else:
            state = "available"
        matrix.append({**spec, "count": len(items), "items": items, "state": state})

    manufactured_types = sum(1 for m in matrix if m["count"] > 0)
    available_recipes = [m["recipe"] for m in matrix if m.get("recipe") and m["count"] == 0]
    pz_loop = await pz.loop(kr_id)

    return {
        "kr": {"id": kr["id"], "kr_code": kr.get("kr_code"), "topic": kr.get("topic"),
               "version": kr.get("version", 1), "status": kr.get("status"),
               "verified_external": verified, "single_source_of_truth": True},
        "matrix": matrix,
        "summary": {"product_types_manufactured": manufactured_types, "product_types_total": len(PRODUCT_SPEC),
                    "total_assets": sum(m["count"] for m in matrix),
                    "available_recipes": available_recipes},
        "project_zero": {"feedback_count": pz_loop["aggregate"].get("feedback_count", 0),
                         "feedback": pz_loop["feedback"], "aggregate": pz_loop["aggregate"],
                         "note": ("Customer feedback and learning metrics will flow back here after publication, "
                                  "improving this Knowledge Record and every future product it manufactures."
                                  if pz_loop["aggregate"].get("feedback_count", 0) == 0
                                  else "Feedback is improving this Knowledge Record.")},
        "philosophy": "Understand Once. Manufacture Forever.",
    }


async def kr_manufacturing_list():
    seen, krs = set(), []
    for coll in (db.knowledge_engine_records, db.knowledge_records):
        async for k in coll.find({}, {"_id": 0, "id": 1, "kr_code": 1, "topic": 1, "title": 1,
                                       "the_question": 1, "subtitle": 1, "version": 1,
                                       "verification": 1, "status": 1, "verified_external": 1,
                                       "verification_status": 1, "approval_status": 1,
                                       "created_at": 1}).sort("created_at", -1).limit(200):
            if k.get("id") and k["id"] not in seen:
                seen.add(k["id"])
                krs.append(k)
    # Asset counts per KR — computed with 5 grouped aggregations instead of
    # 5 count_documents() per record. On remote/production Mongo the per-record
    # loop stacked hundreds of round-trips and timed out; this is constant-query.
    async def _count_map(coll, field):
        m = {}
        async for row in coll.aggregate([{"$group": {"_id": f"${field}", "n": {"$sum": 1}}}]):
            if row["_id"]:
                m[row["_id"]] = row["n"]
        return m

    poster_c = await _count_map(db.poster_assets, "kr_id")
    media_c = await _count_map(db.media_products, "kr_id")
    story_c = await _count_map(db.storyboard_masters, "kr_id")
    inherit_c = await _count_map(db.inherited_products, "kr_id")
    product_c = await _count_map(db.products, "knowledge_record_id")

    out = []
    for k in krs:
        kr_id = k["id"]
        # Topic lives under different keys across the two KR schemas — derive a real display name.
        topic = (k.get("topic") or k.get("title") or k.get("the_question") or k.get("subtitle") or "").strip()
        if not topic:
            continue  # skip empty/incomplete shells (no knowledge to manufacture from)
        counts = (poster_c.get(kr_id, 0) + media_c.get(kr_id, 0) + story_c.get(kr_id, 0)
                  + inherit_c.get(kr_id, 0) + product_c.get(kr_id, 0))
        verif = k.get("verification") or {}
        # Verified across BOTH schemas: engine evidence flag OR legacy Verified/Approved status.
        verified = bool(
            verif.get("evidence_sufficient_for_external_publication")
            or k.get("verified_external")
            or str(k.get("verification_status", "")).lower() == "verified"
            or str(k.get("approval_status", "")).lower() == "approved"
        )
        out.append({"id": kr_id, "kr_code": k.get("kr_code"), "topic": topic,
                    "version": k.get("version", 1), "verified_external": verified,
                    "asset_count": counts})
    out.sort(key=lambda x: (not x["verified_external"], (x["topic"] or "").lower()))
    return {"knowledge_records": out, "philosophy": "Understand Once. Manufacture Forever."}



# ── My Products™ — one unified shelf of everything the Factory has manufactured ──
async def _kr_topic_map():
    m = {}
    for coll in (db.knowledge_engine_records, db.knowledge_records):
        async for k in coll.find({}, {"_id": 0, "id": 1, "topic": 1}):
            if k.get("id"):
                m[k["id"]] = k.get("topic")
    return m


def _tone_for(status):
    s = (status or "").upper()
    if s.startswith(("PUBLISH", "GOLD", "QRU_GOLD")):
        return "gold"
    if s in ("MEDIA_APPROVED", "DESIGN_APPROVED", "PRINT_READY", "PUBLISHING_READY", "RENDERED", "READY", "APPROVED"):
        return "emerald"
    if s in ("RENDER_FAILED", "REVISION_REQUIRED", "BLOCKED", "FAILED"):
        return "rose"
    if s in ("VERIFICATION_REQUIRED", "NEEDS REVIEW", "NEEDS_REVIEW", "RENDERING", "IN_PRODUCTION"):
        return "amber"
    return "slate"


async def all_products():
    topics = await _kr_topic_map()
    items = []

    async for p in db.products.find({}, {"_id": 0}).sort("updated_at", -1).limit(400):
        if p.get("source_engine"):
            continue  # store-listing mirror of a poster/recipe/media row already shown under its own engine
        cd = p.get("customer_deliverable") or {}
        pdf = next((f for f in cd.get("files", []) if f.get("format") == "pdf"), None)
        published = (p.get("status") == "Published")
        publishable = (not published and bool(p.get("creative_brief"))
                       and p.get("creative_status") == "Reviewed" and bool(p.get("verified")))
        badges = []
        if published:
            badges.append("In QRU Store")
        if (p.get("audiobook") or {}).get("status") == "READY":
            badges.append("Audiobook")
        items.append({
            "id": p["id"], "name": p.get("title"), "kind": p.get("product_type") or "Product",
            "engine": "publication", "kr_id": p.get("knowledge_record_id"), "topic": topics.get(p.get("knowledge_record_id")) or p.get("topic"),
            "status": p.get("status") or "Draft", "tone": _tone_for(p.get("status")),
            "updated_at": p.get("updated_at") or p.get("created_at"),
            "download": (pdf or {}).get("url"), "badges": badges, "publishable": publishable,
            "has_manifest": mf.has_deliverable("publication", p),
            "route": "/cover-studio" if not published else "/store",
            "audiobook_url": (p.get("audiobook") or {}).get("url") if (p.get("audiobook") or {}).get("status") == "READY" else None,
        })

    async for m in db.media_products.find({}, {"_id": 0}).sort("created_at", -1).limit(400):
        rs = m.get("render_status")
        fmt = m.get("format")
        badges = []
        if rs == "RENDERED" and fmt in ("youtube_video", "promo_short"):
            badges.append("Ready for YouTube")
        if m.get("store_published"):
            badges.append("In QRU Store")
        items.append({
            "id": m["id"], "name": m.get("label"), "kind": (fmt or "media").replace("_", " ").title(),
            "engine": "media", "kr_id": m.get("kr_id"), "topic": topics.get(m.get("kr_id")),
            "status": "Published" if m.get("store_published") else (rs or m.get("status") or "STORYBOARD_READY"),
            "tone": _tone_for(rs or m.get("status")),
            "updated_at": m.get("created_at"), "download": None, "badges": badges,
            "publishable": mf.is_sellable("media", m) and not m.get("store_published"),
            "has_manifest": mf.has_deliverable("media", m),
            "route": "/storyboard-studio", "audiobook_url": None,
        })

    async for a in db.poster_assets.find({}, {"_id": 0}).sort("created_at", -1).limit(400):
        badges = ["In QRU Store"] if a.get("store_published") else []
        items.append({
            "id": a["id"], "name": a.get("title") or a.get("family"), "kind": "Poster",
            "engine": "poster", "kr_id": a.get("kr_id"), "topic": topics.get(a.get("kr_id")),
            "status": "Published" if a.get("store_published") else (a.get("status") or "DRAFT"),
            "tone": _tone_for(a.get("status")),
            "updated_at": a.get("created_at"),
            "download": f"/api/publishing/poster/{a['id']}/file?format=png", "badges": badges,
            "publishable": mf.is_sellable("poster", a) and not a.get("store_published"),
            "has_manifest": mf.has_deliverable("poster", a),
            "route": "/poster-studio", "audiobook_url": None,
        })

    async for i in db.inherited_products.find({}, {"_id": 0}).sort("created_at", -1).limit(400):
        f = (i.get("files") or [{}])[0]
        badges = ["In QRU Store"] if i.get("store_published") else []
        items.append({
            "id": i["id"], "name": i.get("label"), "kind": (i.get("type") or "recipe").replace("_", " ").title(),
            "engine": "recipe", "kr_id": i.get("kr_id"), "topic": topics.get(i.get("kr_id")),
            "status": "Published" if i.get("store_published") else (i.get("status") or "DRAFT"),
            "tone": _tone_for(i.get("status")),
            "updated_at": i.get("created_at"), "download": f.get("url"), "badges": badges,
            "publishable": mf.is_sellable("recipe", i) and not i.get("store_published"),
            "has_manifest": mf.has_deliverable("recipe", i),
            "route": "/knowledge-manufacturing", "audiobook_url": None,
        })

    items.sort(key=lambda x: (x.get("updated_at") or ""), reverse=True)
    by_engine = {}
    for it in items:
        by_engine[it["engine"]] = by_engine.get(it["engine"], 0) + 1
    return {"products": items, "total": len(items), "by_engine": by_engine,
            "philosophy": "Understand Once. Manufacture Forever."}
