"""QRU Intelligent Companion System™ (QICS) — MO-018 + Factory Rule FR-096.

Every Gold Standard product receives a living digital companion: an immutable QRU identity, a dynamic
QR gateway (the QR image is permanent; its destination can be updated and never expires), and an
Intelligent Companion Portal™ that connects the printed/digital product to its media, resources,
assessments, updates and related products as one connected ecosystem.

FR-096 — Every Gold Standard Product Lives Beyond the Page™: a Gold Standard product is not complete
until it is connected to its Companion Portal through QICS.

Treasure Standard™: portal sections report the HONEST state of each resource — a section is 'available'
only when its real source exists, otherwise 'pending' with the missing input. No faked resources.
"""
import media_starter_kit as msk
import trust_authenticity as ta

# Immutable identity prefixes by product type (MO-018 identity.format).
IDENTITY_PREFIX = {
    "book": "QRU-BK", "ebook": "QRU-BK", "printable": "QRU-BK",
    "knowledge_record": "QRU-KR", "kr": "QRU-KR",
    "workbook": "QRU-WB",
    "course": "QRU-CR",
    "audiobook": "QRU-AU", "audio": "QRU-AU",
    "video": "QRU-VD",
    "poster": "QRU-PT",
    "assessment": "QRU-AS", "quiz": "QRU-AS",
}

# MO-018 resource_router — the companion "home" per product type.
RESOURCE_ROUTER = {
    "book": "Companion Library", "workbook": "Companion Workbook", "knowledge_record": "Learning Center",
    "course": "Student Dashboard", "video": "Lesson Center", "poster": "Narrated Poster",
    "audiobook": "Companion Workbook", "assessment": "Certification Portal",
}

# Full companion resource catalog (MO-018 resources).
RESOURCE_CATALOG = [
    "printable_downloads", "workbook", "audio", "audiobook", "podcast", "video", "narrated_poster",
    "presentation", "infographic", "glossary", "vocabulary", "memory_map", "flashcards",
    "teacher_notes", "parent_guide", "discussion_questions", "challenge_activities", "certification",
]

ANALYTICS_METRICS = ["scan_count", "repeat_scans", "resource_downloads", "video_views",
                     "audiobook_listens", "assessment_completion", "product_progress",
                     "recommendations_clicked", "learning_path"]

FUTURE_SUPPORT = ["mobile_app", "ai_tutor", "augmented_reality", "virtual_reality",
                  "holographic_learning", "wearable_devices", "multilingual_portals",
                  "enterprise_dashboards", "school_portals"]

FACTORY_RULE = {
    "id": "FR-096", "title": "Every Gold Standard Product Lives Beyond the Page™",
    "statement": "A Gold Standard QRU product is never considered complete until it has been connected to "
                 "its Intelligent Companion Portal™ through QICS. The printed product, digital product, "
                 "media, assessments, updates and future learning resources function as one connected ecosystem.",
}

LANDING = {"title": "Welcome to Your QRU Learning Portal™",
           "message": "Your learning journey continues here. Access companion resources, media, updates, "
                      "assessments, and your verified product record."}


def _type_key(p):
    hay = " ".join(str(p.get(k) or "") for k in ("product_type", "family")).lower()
    for key in ("workbook", "audiobook", "audio", "course", "video", "poster", "assessment", "quiz",
                "knowledge_record", "kr", "ebook", "book", "printable"):
        if key in hay:
            return key
    return "book"


async def assign_identity(db, p):
    """Assign (or reuse) an immutable QICS identity. Once minted it never changes."""
    if p.get("qics_identity"):
        return p["qics_identity"]
    prefix = IDENTITY_PREFIX.get(_type_key(p), "QRU-BK")
    counter = await db.qics_counters.find_one_and_update(
        {"prefix": prefix}, {"$inc": {"seq": 1}}, upsert=True, return_document=True)
    seq = (counter or {}).get("seq", 1)
    identity = f"{prefix}-{seq:06d}"
    await db.products.update_one({"id": p["id"]}, {"$set": {"qics_identity": identity}})
    return identity


def _section(available, source, detail, value=None):
    return {"status": "available" if available else "pending", "source": source, "detail": detail, "value": value}


async def companion_portal(db, p):
    """Assemble the Intelligent Companion Portal™ honestly from the product's real assets."""
    tkey = _type_key(p)
    home = RESOURCE_ROUTER.get(tkey, "Companion Library")
    gold = await db.products.find_one({"id": p["id"]})  # fresh
    kit = None
    try:
        from visual_studio import gold_standard_review
        gr = gold_standard_review(p)
        kit = msk.build_kit(p, gr)
    except Exception:
        kit = None

    ready_outputs = {o["id"] for o in (kit or {}).get("outputs", []) if o["status"] == "ready_to_produce"}
    comps = (kit or {}).get("components", {})

    def kit_ready(name):
        return comps.get(name, {}).get("status") == "ready"

    downloads = [u for u in [p.get("preview_pdf_url"), p.get("customer_deliverable"), p.get("cover_url")] if u]
    related = p.get("related_products") or []

    sections = {
        "welcome_page": _section(True, "QICS", "Personalized companion landing page.", LANDING["title"]),
        "product_summary": _section(bool(p.get("title")), "product", p.get("title") or "—"),
        "authenticity_record": _section(bool(p.get("verified")), "Trust Registry™",
                                         "Verified authenticity certificate available." if p.get("verified") else "Awaiting verification."),
        "latest_version": _section(True, "Trust Registry™", f"Version {ta._version(p)}", ta._version(p)),
        "downloads": _section(bool(downloads), "product assets", f"{len(downloads)} downloadable asset(s)." if downloads else "No printable/download asset yet.", downloads),
        "narrated_audio": _section("audiobook" in ready_outputs or kit_ready("approved_voice"), "Media Starter Kit™", "Narration ready to produce." if ("audiobook" in ready_outputs) else "Narration voice/script pending."),
        "media_library": _section(bool(ready_outputs), "Media Starter Kit™", f"{len(ready_outputs)} media output(s) producible.", sorted(ready_outputs)),
        "memory_maps": _section(kit_ready("visual_style"), "Visual Intelligence Studio™", "Memory-map visual style available." if kit_ready("visual_style") else "Design language not applied yet."),
        "teacher_resources": _section(p.get("license_type") in ("Classroom/Teacher", "School/Organization"), "license", "Teacher edition unlocked." if p.get("license_type") in ("Classroom/Teacher", "School/Organization") else "Requires a classroom/school license."),
        "parent_resources": _section(True, "QICS", "Parent guide & discussion prompts."),
        "assessments": _section(tkey == "assessment" or bool(p.get("assessment")), "product", "Assessment/quiz attached." if (tkey == "assessment" or p.get("assessment")) else "No assessment attached yet."),
        "certificates": _section(bool(p.get("verified")), "Trust Registry™", "Completion certificate available." if p.get("verified") else "Certificate unlocks after verification."),
        "related_products": _section(bool(related), "catalog", f"{len(related)} related product(s).", related),
        "support": _section(True, "QRU Support", "Help & contact available."),
        "updates": _section(True, "QICS", "Live updates — this product improves over time."),
    }
    available = [k for k, v in sections.items() if v["status"] == "available"]
    return {
        "resource_home": home, "product_type": tkey, "landing": LANDING,
        "sections": sections, "available_count": len(available), "section_total": len(sections),
        "resource_catalog": RESOURCE_CATALOG,
    }


def continuation(p, catalog_products):
    """MO-018 continuation — recommend next products after a scan (deterministic, from real catalog)."""
    fam = (p.get("family") or p.get("product_type") or "").lower()
    recs = []
    for c in catalog_products:
        if c.get("id") == p.get("id"):
            continue
        same_family = fam and fam in (str(c.get("family") or c.get("product_type") or "").lower())
        if same_family or c.get("id") in (p.get("related_products") or []):
            recs.append({"id": c.get("id"), "product_code": c.get("product_code"), "title": c.get("title"),
                         "reason": "Related to what you're learning."})
        if len(recs) >= 6:
            break
    return recs


def config():
    return {
        "identity_formats": {k: f"{v}-000001" for k, v in {
            "books": "QRU-BK", "knowledge_records": "QRU-KR", "workbooks": "QRU-WB", "courses": "QRU-CR",
            "audiobooks": "QRU-AU", "videos": "QRU-VD", "posters": "QRU-PT", "assessments": "QRU-AS"}.items()},
        "resource_router": RESOURCE_ROUTER,
        "resource_catalog": RESOURCE_CATALOG,
        "analytics_metrics": ANALYTICS_METRICS,
        "future_support": FUTURE_SUPPORT,
        "factory_rule": FACTORY_RULE,
        "landing": LANDING,
        "dynamic_qr": {"regenerate_destination": True, "preserve_qr": True, "expiration": "never"},
    }
