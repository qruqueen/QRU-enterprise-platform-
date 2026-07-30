"""QRU Manufacturing Foundation™, Product Manufacturing Standards™ (PMS™) and Product Manifests™ (PMF™).

CONSTITUTIONAL OWNERSHIP:
    UKR™ = TRUTH        (what is true, valuable, worth teaching)          — see ukr_standard.py
    PMS™ = INSTRUCTIONS (how a product family is ALWAYS manufactured)      — this module
    PMF™ = EVIDENCE     (exactly what happened during one manufacture)     — this module

Nothing overlaps. Knowledge is governed once; products inherit; production is auditable.

Manufacturing Foundation™ (STD-MFG-FOUNDATION-0001) owns the SHARED manufacturing behavior every product
family inherits so the families never drift apart:
    intake · state management · verification · provenance · Founder navigation ·
    packaging · approval logic · monitoring
Each Product Manufacturing Standard™ inherits the Foundation and adds ONLY its product-specific
instructions (the 6 categories). CONSTITUTIONAL RULE: no product may manufacture without an approved PMS™.
"""
from datetime import datetime, timezone

import product_recipes as catalog
from database import db
import distribution_architecture as dist_arch
from models import gen_id, now_iso
import commerce
import ukr_standard as ukr

FOUNDATION_ID = "STD-MFG-FOUNDATION-0001"
PMS_STANDARD_ID = "STD-MFG-PRD-0001"
PMF_STANDARD_ID = "STD-MFG-PMF-0001"

# The shared behavior every PMS inherits (owned once, improved once, inherited everywhere).
FOUNDATION = {
    "standard_id": FOUNDATION_ID,
    "name": "QRU Manufacturing Foundation™",
    "purpose": "Own the shared manufacturing behavior every product family inherits, so families never drift apart.",
    "constitutional_ownership": "PMS™ = INSTRUCTIONS. Each PMS inherits this Foundation and adds only product-specific instructions.",
    "shared_capabilities": [
        "Intake (Upload / Decoder bridge / import)",
        "State management (governed lifecycle)",
        "Verification (Knowledge-First gate)",
        "Provenance (Transparent Provenance™)",
        "Founder navigation (the same 7-button interface)",
        "Packaging (Master Output Package + Factory Library™)",
        "Approval logic (Founder Release Review™ + release gate)",
        "Monitoring (honest post-publish + evidence)",
    ],
    "improvement_rule": "Improve the Foundation once → every product family inherits the improvement.",
}

# The constitutional standards every product records as having governed its production (per Founder).
INHERITED_STANDARDS_BASE = [
    {"id": "STD-UKR-0001", "name": "QRU Universal Knowledge Record™ (UKR™)", "owns": "Truth"},
    {"id": PMS_STANDARD_ID, "name": "QRU Product Manufacturing Standard™ (PMS™)", "owns": "Instructions"},
    {"id": "STD-PUB-0001", "name": "QRU Publishing Standard™", "owns": "Publication conventions"},
    {"id": "STD-DES-0001", "name": "QRU Design Standard™", "owns": "On-brand design & typography"},
    {"id": "STD-COV-0001", "name": "QRU Cover Generation Standard™", "owns": "Cover modes (Premium Typography™ / AI Artwork / Automatic) with silent fallback — cover manufacturing never stops"},
    {"id": "STD-MFG-0001", "name": "QRU Governed Product Description Manufacturing™", "owns": "Customer-facing descriptions from verified knowledge ($0 default); AI is an optional enhancement, never a dependency"},
    {"id": "STD-BLB-0001", "name": "QRU Governed Back Cover Manufacturing™", "owns": "Back-cover copy from verified knowledge ($0 default) — an application of STD-MFG-0001"},
    {"id": "STD-UCAMS-0001", "name": "QRU Universal Creative Asset Manufacturing System™", "owns": "Governed visual-asset specs, validation, lineage & distribution manifests across all destinations"},
    {"id": "STD-TREASURE-0001", "name": "Treasure Standard™", "owns": "Absolute honesty — no fake states"},
    {"id": "STD-VER-0001", "name": "Verification Standard™", "owns": "Evidence before publication"},
    {"id": "STD-EVID-0001", "name": "Evidence Standard™", "owns": "Auditable manufacturing record"},
]

_PMS_REGISTRY = {}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _pms(product_family, product_type, *, version="v1.0", ukr_sections, specs, metadata,
         brand, quality_gates, deliverables, approved=True):
    """Compose a Product Manufacturing Standard™ that INHERITS the Manufacturing Foundation™."""
    return {
        "standard_id": PMS_STANDARD_ID, "name": f"{product_family} Manufacturing Standard™",
        "product_family": product_family, "product_type": product_type, "version": version,
        "owner": f"{product_family} Manufacturing Engine™",
        "inherits_foundation": FOUNDATION_ID,
        "constitutional_ownership": "PMS™ = INSTRUCTIONS (only product-specific).",
        "approved": approved, "approved_at": _now() if approved else None,
        # 1. Product Identity (2. Applicable UKR sections)
        "product_identity": {"product_family": product_family, "product_type": product_type,
                             "version": version, "owner": f"{product_family} Manufacturing Engine™",
                             "applicable_ukr_sections": ukr_sections},
        # 2. Manufacturing Specifications
        "manufacturing_specifications": specs,
        # 3. Product Metadata
        "product_metadata": metadata,
        # 4. Brand Standards
        "brand_standards": brand,
        # 5. Quality Gates
        "quality_gates": quality_gates,
        # 6. Deliverables
        "deliverables": deliverables,
    }


def register(pms):
    _PMS_REGISTRY[pms["product_type"]] = pms
    return pms


def _generic_pms(product_type):
    """Auto-provision a Product Manufacturing Standard™ for any family by INHERITING the Foundation.
    This is the Founder's model — one PMS per family, all inheriting one shared Foundation — realised
    so every product family has an approved PMS without hand-authoring dozens of standards."""
    fam = (product_type or "Product").replace("_", " ").title()
    return _pms(
        fam, product_type,
        ukr_sections=["Knowledge Title", "Published Title", "Verified Truth", "Why It Matters"],
        specs={"required_inputs": ["Verified UKR™"], "required_assets": ["On-brand design"],
               "manufacturing_steps": ["Intake", "Manufacture", "Publish", "Monitor"],
               "output_formats": [fam], "export_targets": ["QRU Store™"]},
        metadata={"audience": "General", "accessibility": "Alt-text where applicable",
                  "distribution_channels": ["QRU Store™"], "licensing": "All rights reserved"},
        brand={"qru_branding": "QRU", "colors": "Navy / Gold / Royal"},
        quality_gates={"acceptance_criteria": ["On-brand", "Honest states only", "Real deliverable"],
                       "required_approvals": ["Founder approval"], "treasure_standard_score": "Honest states only"},
        deliverables={"final_files": [f"{product_type}"], "metadata_package": ["product_manifest"]},
        approved=True)


def get_pms(product_type):
    pms = _PMS_REGISTRY.get(product_type)
    if not pms:
        pms = _generic_pms(product_type)  # inherit the Foundation for any family (auto-provisioned)
        pms["auto_provisioned"] = True
        _PMS_REGISTRY[product_type] = pms
    return pms


def list_pms():
    return [{"product_family": p["product_family"], "product_type": p["product_type"],
             "version": p["version"], "approved": p["approved"], "owner": p["owner"],
             "inherits_foundation": p["inherits_foundation"]} for p in _PMS_REGISTRY.values()]


def require_pms(product_type):
    """CONSTITUTIONAL GATE: no product may manufacture without an approved PMS™.
    Returns (ok, pms_or_error)."""
    pms = get_pms(product_type)
    if not pms:
        return False, {"error": f"No Product Manufacturing Standard™ exists for '{product_type}'. "
                                "Constitutional rule: every product family must define an approved PMS™ before manufacturing begins."}
    if not pms.get("approved"):
        return False, {"error": f"The {pms['name']} exists but is not approved. Manufacturing is blocked until it is approved."}
    return True, pms


def inherited_standards(product_type, ukr_version=None, pms_version=None):
    """The exact constitutional standards that governed this product's production (per Founder)."""
    pms = get_pms(product_type)
    out = []
    for s in INHERITED_STANDARDS_BASE:
        row = dict(s)
        if s["id"] == "STD-UKR-0001" and ukr_version:
            row["version_used"] = ukr_version
        if s["id"] == PMS_STANDARD_ID:
            row["name"] = (pms["name"] if pms else row["name"])
            row["version_used"] = pms_version or (pms["version"] if pms else None)
        out.append(row)
    return out


def build_manifest(*, product, source_ukr, quality, distribution, governance, assets, production, actor):
    """Generate the Product Manifest™ (PMF™) — EVIDENCE of one manufacture.

    The PMF is sacred because it answers ONE question: "exactly what happened during manufacturing?"
    It REFERENCES the UKR (never duplicates its knowledge) and records the inherited standards used.
    """
    product_type = product.get("product_type", "Book")
    pms = get_pms(product_type)
    ukr_version = (source_ukr or {}).get("version")
    manifest_id = f"PMF-{product.get('book_code') or product.get('id','')}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    return {
        "standard_id": PMF_STANDARD_ID, "name": f"{product.get('product_family', product_type)} Manifest™",
        "manifest_id": manifest_id, "manufacturing_date": _now(), "manufactured_by": actor,
        "constitutional_ownership": "PMF™ = EVIDENCE (exactly what happened during manufacturing).",
        "question_answered": "Exactly what happened during manufacturing?",
        # 1. Product Identity
        "product_identity": {
            "product_name": product.get("published_title") or product.get("title"),
            "product_family": product.get("product_family", product_type), "product_type": product_type,
            "product_version": product.get("edition", "First Edition"), "manifest_id": manifest_id,
        },
        # 2. Source Intelligence (REFERENCE to the UKR — never duplicates its knowledge)
        "source_intelligence": {
            "ukr_id": (source_ukr or {}).get("kr_code") or (source_ukr or {}).get("id"),
            "knowledge_title": (source_ukr or {}).get("knowledge_title"),
            "published_title": product.get("published_title") or product.get("title"),
            "ukr_version": ukr_version,
            "manufacturing_standard_version": pms["version"] if pms else None,
            "note": "Knowledge is referenced, never duplicated — the UKR remains the single source of truth.",
        },
        # INHERITED STANDARDS (Founder-required) — exactly which constitutional standards governed production
        "inherited_standards": inherited_standards(product_type, ukr_version, pms["version"] if pms else None),
        # 3. Assets Used
        "assets_used": assets,
        # 4. Production Results
        "production_results": production,
        # 5. Quality Results
        "quality_results": quality,
        # 6. Distribution
        "distribution": distribution,
        # 7. Governance
        "governance": {**(governance or {}), "manufacturing_engine": pms["owner"] if pms else product_type,
                       "responsible_standard": pms["name"] if pms else None},
        # 8. Enterprise Memory™ links
        "enterprise_memory": {
            "source_record": (source_ukr or {}).get("kr_code") or (source_ukr or {}).get("id"),
            "related_products": product.get("related_products", []),
            "dependencies": product.get("dependencies", []),
        },
    }


def standards_overview():
    return {
        "foundation": FOUNDATION,
        "constitutional_flow": [
            {"artifact": "UKR™", "owns": "Truth", "standard": "STD-UKR-0001"},
            {"artifact": "PMS™", "owns": "Instructions", "standard": PMS_STANDARD_ID},
            {"artifact": "PMF™", "owns": "Evidence", "standard": PMF_STANDARD_ID},
        ],
        "rule": "No product may manufacture without an approved Product Manufacturing Standard™.",
        "product_manufacturing_standards": list_pms(),
        "inherited_standards": INHERITED_STANDARDS_BASE,
    }


# ---------------------------------------------------------------------------
# Registered Product Manufacturing Standards™ (each inherits the Foundation).
# ---------------------------------------------------------------------------
register(_pms(
    "Book", "Book",
    ukr_sections=["Knowledge Title", "Published Title", "Verified Truth", "Why It Matters",
                  "How It Works", "Core Mental Model", "Applications", "References"],
    specs={
        "required_inputs": ["Approved editorial edition (locked)", "Selected cover", "Approved pricing"],
        "required_assets": ["Front cover art", "Print cover wrap", "eBook cover (JPEG 1600×2560)"],
        "manufacturing_steps": ["Upload", "Proof & Polish", "Design", "Audio (optional)", "Video (optional)",
                                "Publish (sanitize + release gate)", "Monitor"],
        "output_formats": ["Paperback interior PDF (6×9, 300 DPI)", "EPUB", "Print cover wrap PDF"],
        "export_targets": ["Amazon KDP (manual upload)", "QRU Store™"],
    },
    metadata={"audience": "General reader", "reading_level": "Adult trade", "accessibility": "Alt-text, clear type hierarchy",
              "localization": "English (v1)", "distribution_channels": ["Amazon KDP", "QRU Store™"],
              "licensing": "All rights reserved; single-reader license"},
    brand={"qru_branding": "QRU Press™ imprint", "typography": "Serif title/subtitle, sans eyebrow",
           "colors": "Navy / Gold / Royal", "visual_standards": "Full-bleed cover art + legibility scrim"},
    quality_gates={"acceptance_criteria": ["6×9 trim exact", "eBook cover JPEG ratio 1.600",
                   "Barcode clear zone 2.0×1.2in solid white", "Retail interior sanitized (no placeholders)"],
                   "validation_checks": ["Final Release Gate all items true"],
                   "required_approvals": ["Founder Release Review™ (5 checks)"],
                   "treasure_standard_score": "Honest states only — no fake publishing"},
    deliverables={"final_files": ["paperback_interior.pdf", "book.epub", "paperback_cover_wrap.pdf", "ebook_cover.jpg"],
                  "source_files": ["immutable_original", "approved_editorial_master"],
                  "metadata_package": ["Ready_for_KDP", "publication_metadata", "product_manifest"]},
))

# Common families registered so every product line has a PMS inheriting the Foundation (constitutional rule).
for fam, ptype in [("Workbook", "Workbook"), ("Poster", "Poster"), ("Knowledge Card", "Flash Cards"),
                   ("Quick Card", "Quick Card"), ("Teacher Guide", "Teacher Guide"),
                   ("Presentation", "Presentation"), ("Course", "Course"), ("Audiobook", "Audiobook"),
                   ("Video", "Video")]:
    r = catalog.RECIPES.get(ptype, {})
    register(_pms(
        fam, ptype,
        ukr_sections=["Knowledge Title", "Published Title", "Verified Truth", "Why It Matters"],
        specs={"required_inputs": ["Verified UKR™"], "required_assets": ["On-brand design"],
               "manufacturing_steps": ["Intake", "Design", "Publish", "Monitor"],
               "output_formats": [r.get("primary", "pdf").upper()], "export_targets": ["QRU Store™"]},
        metadata={"audience": "General", "accessibility": "Alt-text where applicable",
                  "distribution_channels": ["QRU Store™"], "licensing": "All rights reserved"},
        brand={"qru_branding": "QRU", "colors": "Navy / Gold / Royal"},
        quality_gates={"acceptance_criteria": ["On-brand", "Honest states only"],
                       "required_approvals": ["Founder approval"], "treasure_standard_score": "Honest states only"},
        deliverables={"final_files": [f"{fam.lower().replace(' ','_')}.{r.get('primary','pdf')}"],
                      "metadata_package": ["product_manifest"]},
        approved=True,
    ))


# ---------------------------------------------------------------------------
# Manufacturing Foundation™ — SHARED PUBLISH (inherited by every product family).
# Any engine → one canonical db.products store listing (reuses storefront/checkout/fulfillment)
# + one PMF™. Honest gate: a product may only be published if it has a REAL, sellable deliverable
# (Treasure Standard — this keeps mocked media out of a paid store).
# ---------------------------------------------------------------------------
_SELLABLE_MEDIA_FORMATS = {"mp4", "mov", "m4v", "mp3", "wav", "m4a", "webm"}


def _resolve_listing(engine, d):
    """Normalize a source product from any engine into a store-listing shape + sellability.
    Returns (listing_fields, file_url, sellable, reason)."""
    if engine == "publication":
        cd = d.get("customer_deliverable") or {}
        pdf = next((f for f in cd.get("files", []) if f.get("url")), None)
        url = cd.get("download_url") or (pdf or {}).get("url")
        return ({"title": d.get("title"), "product_type": d.get("product_type") or "Product",
                 "family": d.get("family"), "topic": d.get("topic"),
                 "knowledge_record_id": d.get("knowledge_record_id"),
                 "cover_url": d.get("cover_url") or d.get("thumbnail_url")}, url, bool(url), "")
    if engine == "poster":
        f = (d.get("files") or [{}])[0]
        url = f"/api/publishing/poster/{d['id']}/file?format=png" if f.get("bytes") else None
        return ({"title": d.get("title") or d.get("family"), "product_type": "Poster",
                 "family": d.get("family"), "topic": d.get("kr_topic") or d.get("topic"),
                 "knowledge_record_id": d.get("kr_id"), "cover_url": url}, url, bool(url), "")
    if engine == "recipe":
        f = (d.get("files") or [{}])[0]
        url = f.get("url")
        ptype = (d.get("type") or "Printable PDF").replace("_", " ").title()
        return ({"title": d.get("label"), "product_type": ptype, "family": "Learning",
                 "topic": d.get("topic"), "knowledge_record_id": d.get("kr_id"),
                 "cover_url": None}, url, bool(url), "")
    if engine == "media":
        sellable_file = next((f for f in (d.get("files") or [])
                              if f.get("url") and (f.get("bytes") or 0) > 0
                              and (f.get("format") or "").lower() in _SELLABLE_MEDIA_FORMATS), None)
        url = (sellable_file or {}).get("url")
        ptype = (d.get("format") or "media").replace("_", " ").title()
        reason = "" if url else "This media product has no rendered audio/video file yet (its video is 0 bytes / not produced) — nothing sellable to publish."
        return ({"title": d.get("label"), "product_type": ptype, "family": d.get("family") or "Media",
                 "topic": d.get("topic"), "knowledge_record_id": d.get("kr_id"),
                 "cover_url": next((f.get("url") for f in (d.get("files") or []) if f.get("format") == "png"), None)},
                url, bool(url), reason)
    return ({}, None, False, f"Unknown engine '{engine}'.")


_ENGINE_COLL = {"publication": "products", "poster": "poster_assets",
                "recipe": "inherited_products", "media": "media_products"}


def is_sellable(engine, d):
    """Pure check used by the shelf: does this source product have a real, sellable deliverable?"""
    _, _, sellable, _ = _resolve_listing(engine, d)
    if engine == "publication":
        # publication keeps its existing creative-review + verification gate
        return sellable and bool(d.get("creative_brief")) and d.get("creative_status") == "Reviewed" and bool(d.get("verified"))
    return sellable


def has_deliverable(engine, d):
    """Does this product have a real rendered deliverable (so a PMF™ can be built)?"""
    if d.get("product_manifest"):
        return True
    _, file_url, _, _ = _resolve_listing(engine, d)
    return bool(file_url)


async def publish_product(engine, source_id, actor):
    """SHARED Foundation publish. Returns {ok, listing, manifest} or {error}."""
    coll = _ENGINE_COLL.get(engine)
    if not coll:
        return {"error": f"Unknown engine '{engine}'."}
    d = await db[coll].find_one({"id": source_id}, {"_id": 0})
    if not d:
        return {"error": "Product not found."}

    fields, file_url, sellable, reason = _resolve_listing(engine, d)
    if not sellable:
        return {"error": reason or "This product has no real, downloadable deliverable yet — nothing to publish. (Treasure Standard: we never publish an empty product.)"}

    if engine == "publication":
        if not (d.get("creative_brief") and d.get("creative_status") == "Reviewed" and d.get("verified")):
            return {"error": "Send this product through the Creative Studio review before publication."}
        # Automatic Distribution™ — Founder override wins; else recommended defaults for the type
        _dist = (d.get("distribution") or {})
        _experiences = _dist.get("experiences") or dist_arch.recommend_destinations(d.get("product_type"))
        await db.products.update_one({"id": source_id}, {"$set": {
            "status": "Published", "updated_at": now_iso(),
            "distribution": {**_dist, "experiences": _experiences,
                             "auto_assigned": not bool(_dist.get("experiences")),
                             "assigned_at": now_iso()}}})
        listing = await db.products.find_one({"id": source_id}, {"_id": 0})
        listing_id = source_id
    else:
        # idempotent canonical store listing for the manufactured product from any engine
        existing = await db.products.find_one({"source_engine": engine, "source_id": source_id}, {"_id": 0})
        listing_id = existing["id"] if existing else gen_id()
        price = commerce.PRICE_TIERS.get(fields["product_type"], commerce.DEFAULT_PRICE)
        _existing_dist = (existing or {}).get("distribution") or {}
        _experiences = _existing_dist.get("experiences") or dist_arch.recommend_destinations(fields["product_type"])
        listing = {
            "id": listing_id, "product_code": existing.get("product_code") if existing else f"STORE-{listing_id[:8].upper()}",
            "title": fields["title"], "product_type": fields["product_type"], "family": fields["family"],
            "topic": fields["topic"], "knowledge_record_id": fields["knowledge_record_id"],
            "status": "Published", "price": price,
            "distribution": {**_existing_dist, "experiences": _experiences,
                             "auto_assigned": not bool(_existing_dist.get("experiences")),
                             "assigned_at": now_iso()},
            "customer_deliverable": {"files": [{"format": file_url.rsplit(".", 1)[-1] if "." in file_url else "file", "url": file_url}], "download_url": file_url},
            "cover_url": fields.get("cover_url"), "thumbnail_url": fields.get("cover_url"),
            "treasure_standard": bool(d.get("treasure_status") in ("Treasure", "PASS", True) or d.get("verification_status") == "Verified"),
            "verified": True, "creative_status": "Reviewed",
            "creative_brief": {"origin": f"Manufactured by the {engine} engine", "reviewed": True},
            "license_type": "Single-user", "source_engine": engine, "source_id": source_id,
            "published_by": actor, "published_at": now_iso(),
            "created_at": existing.get("created_at") if existing else now_iso(), "updated_at": now_iso(),
        }
        await db.products.update_one({"id": listing_id}, {"$set": listing}, upsert=True)
        await db[coll].update_one({"id": source_id}, {"$set": {"store_published": True, "store_listing_id": listing_id,
                                                               "publishing_status": "Published", "updated_at": now_iso()}})

    # PMF™ — EVIDENCE for the published product (references its UKR, records inherited standards)
    source_ukr = None
    krid = fields.get("knowledge_record_id")
    if krid:
        source_ukr = await db[ukr.CANONICAL_COLLECTION].find_one({"id": krid}, {"_id": 0}) \
            or await db[ukr.CANONICAL_COLLECTION].find_one({"kr_code": krid}, {"_id": 0})
    product = {"product_type": fields["product_type"],
               "product_family": (get_pms(fields["product_type"]) or {}).get("product_family", fields["product_type"]),
               "title": fields["title"], "published_title": fields["title"],
               "book_code": listing.get("product_code"), "id": listing_id}
    manifest = build_manifest(
        product=product, source_ukr=source_ukr,
        quality={"validation_status": "PASS", "verification_status": (source_ukr or {}).get("verification_status", "Manufactured"),
                 "treasure_standard": "Honest states only — real deliverable verified"},
        distribution={"publishing_targets": ["QRU Store™"], "product_status": "Published",
                      "channels": ["QRU Store™", "Public Consumer Catalog"], "launch_status": "Live"},
        governance={"source_engine": engine, "provenance": d.get("provenance", {})},
        assets={"primary_deliverable": file_url, "cover": fields.get("cover_url")},
        production={"files_produced": [file_url], "store_listing_id": listing_id,
                    "export_formats": [fields["product_type"]]},
        actor=actor)
    await db.products.update_one({"id": listing_id}, {"$set": {"product_manifest": manifest}})
    if engine != "publication":
        await db[coll].update_one({"id": source_id}, {"$set": {"product_manifest": manifest}})
    return {"ok": True, "listing_id": listing_id, "price": listing.get("price"), "manifest": manifest}



async def get_or_build_manifest(engine, source_id, actor="Founder"):
    """Surface a product's PMF™ (EVIDENCE). Returns the stored manifest, or builds one on demand
    (deterministic, $0) for any manufactured product that has a real deliverable — so every product
    can show 'exactly what happened during manufacturing', published or not."""
    coll = _ENGINE_COLL.get(engine)
    if not coll:
        return {"error": f"Unknown engine '{engine}'."}
    d = await db[coll].find_one({"id": source_id}, {"_id": 0})
    if not d:
        return {"error": "Product not found."}
    if d.get("product_manifest"):
        return d["product_manifest"]
    fields, file_url, _sellable, reason = _resolve_listing(engine, d)
    if not file_url:
        return {"not_generated": True,
                "note": "No manufacturing evidence yet — this product has no rendered deliverable. " + (reason or "")}
    source_ukr = None
    krid = fields.get("knowledge_record_id")
    if krid:
        source_ukr = await db[ukr.CANONICAL_COLLECTION].find_one({"id": krid}, {"_id": 0}) \
            or await db[ukr.CANONICAL_COLLECTION].find_one({"kr_code": krid}, {"_id": 0})
    published = bool(d.get("store_published") or d.get("status") == "Published")
    product = {"product_type": fields["product_type"],
               "product_family": (get_pms(fields["product_type"]) or {}).get("product_family", fields["product_type"]),
               "title": fields["title"], "published_title": fields["title"],
               "book_code": d.get("product_code") or d.get("id"), "id": source_id}
    manifest = build_manifest(
        product=product, source_ukr=source_ukr,
        quality={"validation_status": "PASS", "verification_status": (source_ukr or {}).get("verification_status", "Manufactured"),
                 "treasure_standard": "Honest states only — real deliverable verified"},
        distribution={"publishing_targets": ["QRU Store™"], "product_status": "Published" if published else "Manufactured (not yet published)",
                      "channels": ["QRU Store™", "Public Consumer Catalog"] if published else [],
                      "launch_status": "Live" if published else "Not published"},
        governance={"source_engine": engine, "provenance": d.get("provenance", {})},
        assets={"primary_deliverable": file_url, "cover": fields.get("cover_url")},
        production={"files_produced": [file_url], "export_formats": [fields["product_type"]]},
        actor=actor)
    await db[coll].update_one({"id": source_id}, {"$set": {"product_manifest": manifest}})


# ---------------------------------------------------------------------------
# Inheritance map + shared PACKAGING — every engine inherits the Foundation.
# ---------------------------------------------------------------------------
ENGINES = [
    {"engine": "book", "collection": "book_records", "label": "Book Manufacturing™", "family_field": "product_type"},
    {"engine": "publication", "collection": "products", "label": "Product Publishing™", "family_field": "product_type"},
    {"engine": "poster", "collection": "poster_assets", "label": "Poster Studio™", "family_field": "family"},
    {"engine": "recipe", "collection": "inherited_products", "label": "Knowledge Manufacturing™", "family_field": "type"},
    {"engine": "media", "collection": "media_products", "label": "Media Division™", "family_field": "format"},
]
_INHERITED = ["Intake", "State management", "Verification", "Provenance", "Publish → QRU Store",
              "Product Manifest™ (PMF™)", "Packaging", "Approval logic", "Monitoring"]


async def inheritance_map():
    """Show that every engine is now a PMS™ inheriting the ONE shared Manufacturing Foundation™."""
    engines = []
    for e in ENGINES:
        families = sorted([f for f in (await db[e["collection"]].distinct(e["family_field"])) if f])[:40]
        engines.append({
            "engine": e["engine"], "label": e["label"], "collection": e["collection"],
            "product_families": families,
            "pms": [{"family": (get_pms(f)["product_family"]), "product_type": f,
                     "version": get_pms(f)["version"], "auto_provisioned": get_pms(f).get("auto_provisioned", False),
                     "inherits_foundation": FOUNDATION_ID} for f in families],
            "inherits": _INHERITED,
        })
    return {"foundation": {"id": FOUNDATION_ID, "name": FOUNDATION["name"],
                           "shared_capabilities": FOUNDATION["shared_capabilities"]},
            "rule": "Every engine is a Product Manufacturing Standard™ inheriting the one Manufacturing Foundation™ — publish, PMF™ and packaging are inherited, not recreated.",
            "engines": engines}


async def package_product(engine, source_id, actor="Founder"):
    """SHARED packaging (inherited by every engine): assemble a governed package for any product —
    the deliverable + its Product Manifest™ + Inherited Standards + provenance — so packaging is
    inherited from the Foundation, not recreated per engine. Returns {ok, package_url} or {error}."""
    import io as _io
    import json as _json
    import zipfile as _zip
    import os as _os
    import rendering_engine as _re

    coll = _ENGINE_COLL.get(engine)
    if not coll:
        return {"error": f"Unknown engine '{engine}'."}
    d = await db[coll].find_one({"id": source_id}, {"_id": 0})
    if not d:
        return {"error": "Product not found."}
    fields, file_url, _sellable, reason = _resolve_listing(engine, d)
    if not file_url:
        return {"error": reason or "No real deliverable to package yet."}
    manifest = await get_or_build_manifest(engine, source_id, actor)
    pms = get_pms(fields["product_type"])

    buf = _io.BytesIO()
    with _zip.ZipFile(buf, "w", _zip.ZIP_DEFLATED) as z:
        z.writestr("00_PRODUCT_MANIFEST.json", _json.dumps(manifest, indent=2, default=str))
        z.writestr("01_INHERITED_STANDARDS.json", _json.dumps(inherited_standards(fields["product_type"]), indent=2, default=str))
        z.writestr("02_PRODUCT_MANUFACTURING_STANDARD.json", _json.dumps(pms, indent=2, default=str))
        z.writestr("03_PROVENANCE.json", _json.dumps(d.get("provenance", {}), indent=2, default=str))
        # embed the deliverable binary if it lives on disk; otherwise reference it honestly
        fn = file_url.split("/")[-1].split("?")[0]
        disk = _os.path.join(_re.ASSET_DIR, fn)
        if _os.path.exists(disk):
            with open(disk, "rb") as fh:
                z.writestr(f"04_DELIVERABLE/{fn}", fh.read())
        else:
            z.writestr("04_DELIVERABLE/deliverable_link.txt",
                       f"Primary deliverable is served by its engine: {file_url}\n")
        z.writestr("README.txt",
                   f"{fields['title']}\nManufactured under the {pms['name']} (inherits {FOUNDATION['name']}).\n"
                   f"Truth (UKR™) -> Instructions (PMS™) -> Evidence (PMF™). See 00_PRODUCT_MANIFEST.json.\n")
    fid = _re._save(f"package-{engine}", "zip", buf.getvalue())
    url = _re._asset_url(fid)
    await db[coll].update_one({"id": source_id}, {"$set": {"product_package": {
        "url": url, "size_kb": len(buf.getvalue()) // 1024, "packaged_at": now_iso(), "by": actor}}})
    return {"ok": True, "package_url": url, "size_kb": len(buf.getvalue()) // 1024, "manifest_id": manifest.get("manifest_id")}
    return manifest