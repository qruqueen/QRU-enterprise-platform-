"""QRU Enterprise Manufacturing Dashboard™ — each verified Knowledge Record as a living dashboard
of everything manufactured from it (Knowledge-first, not product-first). Honest status only.
"""
from database import db
import project_zero as pz

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
    krs = [k async for k in db.knowledge_engine_records.find({}, {"_id": 0, "id": 1, "kr_code": 1, "topic": 1, "version": 1, "verification": 1, "status": 1}).sort("created_at", -1).limit(60)]
    out = []
    for k in krs:
        kr_id = k["id"]
        counts = (await db.poster_assets.count_documents({"kr_id": kr_id})
                  + await db.media_products.count_documents({"kr_id": kr_id})
                  + await db.storyboard_masters.count_documents({"kr_id": kr_id})
                  + await db.inherited_products.count_documents({"kr_id": kr_id})
                  + await db.products.count_documents({"knowledge_record_id": kr_id}))
        verif = k.get("verification") or {}
        out.append({"id": kr_id, "kr_code": k.get("kr_code"), "topic": k.get("topic"),
                    "version": k.get("version", 1),
                    "verified_external": bool(verif.get("evidence_sufficient_for_external_publication")),
                    "asset_count": counts})
    return {"knowledge_records": out, "philosophy": "Understand Once. Manufacture Forever."}
