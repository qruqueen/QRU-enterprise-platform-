"""QRU Enterprise Manufacturing Dashboard™ — each verified Knowledge Record as a living dashboard
of everything manufactured from it (Knowledge-first, not product-first). Honest status only.
"""
from database import db

# Canonical product lifecycle for a Knowledge Record (built ones are detected; the rest are "available").
PRODUCT_SPEC = [
    {"type": "Storyboard Master™", "key": "storyboard", "route": "/storyboard-studio"},
    {"type": "Knowledge Card™", "key": "knowledge_card", "route": "/poster-studio"},
    {"type": "Poster", "key": "poster", "route": "/poster-studio"},
    {"type": "Data Poster", "key": "data_poster", "route": "/poster-studio"},
    {"type": "Video", "key": "video", "route": "/storyboard-studio"},
    {"type": "Audio Lesson", "key": "audio", "route": "/storyboard-studio"},
    {"type": "Presentation", "key": "presentation", "route": "/storyboard-studio"},
    {"type": "Book / Workbook / PDF", "key": "publication", "route": "/manufacture"},
    {"type": "Podcast", "key": "podcast", "route": "/storyboard-studio"},
    {"type": "Course", "key": "course", "route": None},
    {"type": "Audiobook", "key": "audiobook", "route": None},
    {"type": "Instructor Guide", "key": "instructor_guide", "route": None},
    {"type": "Assessment Pack", "key": "assessment", "route": None},
    {"type": "Marketing Assets", "key": "marketing", "route": None},
    {"type": "Product Bundle", "key": "bundle", "route": None},
]
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
    return posters, media, storyboards, products


def _poster_item(p):
    return {"id": p["id"], "label": p.get("title") or p.get("family"), "status": p.get("status"),
            "thumb": f"/api/publishing/poster/{p['id']}/file?format=thumb"}


def _media_item(m):
    return {"id": m["id"], "label": m.get("label"), "status": m.get("status"),
            "render_status": m.get("render_status")}


async def kr_manufacturing(kr_id):
    kr = await _kr(kr_id)
    if not kr:
        return None
    posters, media, storyboards, products = await _collect(kr_id)
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

    matrix = []
    for spec in PRODUCT_SPEC:
        items = built.get(spec["key"], [])
        published = any((i.get("status") or "").upper().startswith(("PUBLISH", "GOLD")) for i in items)
        matrix.append({**spec, "count": len(items), "items": items,
                       "state": ("published" if published else "manufactured") if items else "available"})

    manufactured_types = sum(1 for m in matrix if m["count"] > 0)
    # Project Zero™ feedback loop — honest: only shows real feedback if it exists.
    feedback = [f async for f in db.project_zero_feedback.find({"kr_id": kr_id}, {"_id": 0}).limit(20)]

    return {
        "kr": {"id": kr["id"], "kr_code": kr.get("kr_code"), "topic": kr.get("topic"),
               "version": kr.get("version", 1), "status": kr.get("status"),
               "verified_external": verified, "single_source_of_truth": True},
        "matrix": matrix,
        "summary": {"product_types_manufactured": manufactured_types, "product_types_total": len(PRODUCT_SPEC),
                    "total_assets": sum(m["count"] for m in matrix)},
        "project_zero": {"feedback_count": len(feedback), "feedback": feedback,
                         "note": ("Customer feedback and learning metrics will flow back here after publication, "
                                  "improving this Knowledge Record and every future product it manufactures."
                                  if not feedback else "Feedback is improving this Knowledge Record.")},
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
                  + await db.products.count_documents({"knowledge_record_id": kr_id}))
        verif = k.get("verification") or {}
        out.append({"id": kr_id, "kr_code": k.get("kr_code"), "topic": k.get("topic"),
                    "version": k.get("version", 1),
                    "verified_external": bool(verif.get("evidence_sufficient_for_external_publication")),
                    "asset_count": counts})
    return {"knowledge_records": out, "philosophy": "Understand Once. Manufacture Forever."}
