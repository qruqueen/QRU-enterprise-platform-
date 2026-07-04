"""QRU Autonomous Asset Manufacturing Engine™ (AO-002) — deterministic ($0 AI).

Transforms the Asset Vault™ from storage into an active manufacturing inventory. When a
Founder approves/imports an asset, the factory immediately determines:

    • the asset's classification,
    • every compatible QRU product type,
    • every compatible marketplace + its export spec,
    • an estimated manufacturing plan + recommended order.

Governance preserved: nothing is manufactured or published automatically. The Founder
Manufacturing Panel™ surfaces the plan; manufacturing runs only on Founder action, and a
completed-product asset is preserved as the hero visual (never redesigned).
"""
import logging

from database import db
from models import gen_id, now_iso, clean

logger = logging.getLogger("qru.asset_manufacturing")

# --------------------------------------------------------------------------- #
# Asset Classification™ — canonical class for an imported asset.
# --------------------------------------------------------------------------- #
ASSET_CLASSES = [
    "Poster", "Book Cover", "Workbook Interior", "Infographic", "Quick Card", "Flash Card",
    "Worksheet", "Logo", "Illustration", "Character", "Photo", "Chart", "Presentation",
    "Video", "Audio", "Brand Asset", "Knowledge Graphic", "Social Graphic", "Course Asset",
]

_CLASS_KEYWORDS = [
    ("Poster", ["poster"]),
    ("Book Cover", ["cover", "book"]),
    ("Workbook Interior", ["workbook", "interior"]),
    ("Infographic", ["infographic"]),
    ("Flash Card", ["flash"]),
    ("Quick Card", ["quick card", "cheat", "quick guide"]),
    ("Worksheet", ["worksheet", "printable"]),
    ("Logo", ["logo", "shield", "seal", "icon"]),
    ("Character", ["character", "mascot", "lion", "eagle", "bear", "phoenix", "fox", "beaver", "unity"]),
    ("Chart", ["chart", "diagram", "graph"]),
    ("Presentation", ["presentation", "slide", "deck", "pptx"]),
    ("Video", ["video", "mp4", "reel"]),
    ("Audio", ["audio", "music", "narration", "podcast", "mp3", "wav"]),
    ("Social Graphic", ["social", "instagram", "pinterest", "facebook", "linkedin", "tiktok"]),
    ("Knowledge Graphic", ["knowledge", "explainer"]),
    ("Brand Asset", ["brand", "banner", "template"]),
    ("Illustration", ["illustration", "art", "drawing"]),
    ("Photo", ["photo", "photograph", "image"]),
    ("Course Asset", ["course", "lesson", "module"]),
]


def classify_asset(asset):
    """Deterministic classification from asset_type + name + file ext."""
    hay = " ".join([str(asset.get("asset_type", "")), str(asset.get("name", "")),
                    str(asset.get("usage_notes", ""))]).lower()
    ext = ((asset.get("file") or {}).get("ext") or "").lower()
    if ext in ("mp3", "wav", "aac", "flac", "ogg"):
        return "Audio"
    if ext in ("mp4", "mov", "webm", "avi"):
        return "Video"
    if ext == "pptx":
        return "Presentation"
    for klass, kws in _CLASS_KEYWORDS:
        if any(k in hay for k in kws):
            return klass
    # image files with no strong signal default to Illustration; else Brand Asset.
    if ext in ("png", "jpg", "jpeg", "webp", "gif", "svg"):
        return "Illustration"
    return "Brand Asset"


def is_completed_product_asset(klass):
    """A finished, print/marketplace-ready visual → preserve as hero, don't redesign."""
    return klass in ("Poster", "Book Cover", "Infographic", "Quick Card", "Flash Card",
                     "Worksheet", "Knowledge Graphic", "Social Graphic", "Chart")


# --------------------------------------------------------------------------- #
# Product Compatibility™ — which QRU product types each class can manufacture.
# --------------------------------------------------------------------------- #
_SOCIAL_PACK = ["Social Media Pack", "Pinterest Graphic", "Instagram Post", "Facebook Graphic", "LinkedIn Graphic"]
_MARKETING = ["Marketplace Preview", "Email Banner", "Website Hero", "Marketing Graphic"]

CLASS_TO_PRODUCTS = {
    "Poster": ["Poster", "Digital Download", "Classroom Poster", "Teacher Resource", "Presentation"] + _SOCIAL_PACK + _MARKETING,
    "Infographic": ["Infographic", "Digital Download", "Teacher Resource", "Presentation"] + _SOCIAL_PACK + _MARKETING,
    "Book Cover": ["Book", "Digital Download", "Marketplace Preview", "Website Hero"] + _SOCIAL_PACK,
    "Workbook Interior": ["Workbook", "Printable PDF", "Teacher Resource", "Digital Download"],
    "Quick Card": ["Quick Card", "Flash Cards", "Printable PDF", "Digital Download"] + _SOCIAL_PACK,
    "Flash Card": ["Flash Cards", "Quick Card", "Printable PDF", "Digital Download"],
    "Worksheet": ["Workbook", "Printable PDF", "Teacher Resource", "Digital Download"],
    "Chart": ["Infographic", "Poster", "Presentation", "Teacher Resource"] + _SOCIAL_PACK,
    "Knowledge Graphic": ["Infographic", "Poster", "Digital Download"] + _SOCIAL_PACK + _MARKETING,
    "Social Graphic": _SOCIAL_PACK + ["Marketing Graphic", "Digital Download"],
    "Presentation": ["Presentation", "Course", "Teacher Resource", "Digital Download"],
    "Character": ["Illustration Pack", "Sticker Pack"] + _SOCIAL_PACK + ["Website Hero", "Marketing Graphic"],
    "Illustration": ["Poster", "Digital Download"] + _SOCIAL_PACK + ["Website Hero", "Marketing Graphic"],
    "Photo": ["Website Hero", "Marketing Graphic", "Email Banner"] + _SOCIAL_PACK,
    "Logo": ["Website Hero", "Email Banner", "Brand Kit", "Marketing Graphic"],
    "Brand Asset": ["Website Hero", "Email Banner", "Marketing Graphic"] + _SOCIAL_PACK,
    "Audio": ["Podcast Script", "Audio Narration"],
    "Video": ["Video Script", "Short-form Content"] + _SOCIAL_PACK,
    "Course Asset": ["Course", "Interactive Lesson", "Presentation", "Teacher Resource"],
}


# --------------------------------------------------------------------------- #
# Marketplace Configuration™ — export specs per supported marketplace.
# --------------------------------------------------------------------------- #
MARKETPLACES = [
    {"id": "amazon_kdp", "name": "Amazon KDP", "kind": "print", "dimensions": "2560×1600", "dpi": 300, "bleed": "0.125in", "format": "PDF/JPG", "notes": "Kindle & paperback covers"},
    {"id": "tpt", "name": "Teachers Pay Teachers", "kind": "education", "dimensions": "8.5×11in", "dpi": 300, "bleed": "0.25in", "format": "PDF", "notes": "Printable classroom resource"},
    {"id": "etsy", "name": "Etsy", "kind": "digital", "dimensions": "2000×2000", "dpi": 300, "bleed": "0in", "format": "PDF/PNG", "notes": "Digital download"},
    {"id": "gumroad", "name": "Gumroad", "kind": "digital", "dimensions": "1280×720", "dpi": 150, "bleed": "0in", "format": "PDF/ZIP", "notes": "Cover + product files"},
    {"id": "payhip", "name": "Payhip", "kind": "digital", "dimensions": "1280×720", "dpi": 150, "bleed": "0in", "format": "PDF/ZIP", "notes": "Digital storefront"},
    {"id": "shopify", "name": "Shopify", "kind": "commerce", "dimensions": "2048×2048", "dpi": 72, "bleed": "0in", "format": "PNG/JPG", "notes": "Product image + preview"},
    {"id": "pinterest", "name": "Pinterest", "kind": "social", "dimensions": "1000×1500", "dpi": 72, "bleed": "0in", "format": "PNG", "notes": "2:3 vertical pin"},
    {"id": "instagram", "name": "Instagram", "kind": "social", "dimensions": "1080×1080", "dpi": 72, "bleed": "0in", "format": "PNG/JPG", "notes": "Square post"},
    {"id": "facebook", "name": "Facebook", "kind": "social", "dimensions": "1200×630", "dpi": 72, "bleed": "0in", "format": "PNG/JPG", "notes": "Link/share graphic"},
    {"id": "linkedin", "name": "LinkedIn", "kind": "social", "dimensions": "1200×627", "dpi": 72, "bleed": "0in", "format": "PNG/JPG", "notes": "Professional share"},
    {"id": "email", "name": "Email Marketing", "kind": "marketing", "dimensions": "600×200", "dpi": 72, "bleed": "0in", "format": "PNG/JPG", "notes": "Responsive email banner"},
    {"id": "qru_store", "name": "QRU Store™", "kind": "native", "dimensions": "1600×2000", "dpi": 150, "bleed": "0in", "format": "PDF/PNG/HTML", "notes": "Native QRU listing"},
]
_MK = {m["id"]: m for m in MARKETPLACES}

CLASS_TO_MARKETPLACES = {
    "Poster": ["qru_store", "etsy", "tpt", "amazon_kdp", "pinterest", "instagram", "facebook"],
    "Infographic": ["qru_store", "etsy", "tpt", "pinterest", "instagram", "linkedin"],
    "Book Cover": ["qru_store", "amazon_kdp", "gumroad", "payhip", "shopify"],
    "Workbook Interior": ["qru_store", "tpt", "etsy", "gumroad", "payhip"],
    "Quick Card": ["qru_store", "etsy", "tpt", "pinterest"],
    "Flash Card": ["qru_store", "etsy", "tpt"],
    "Worksheet": ["qru_store", "tpt", "etsy"],
    "Chart": ["qru_store", "tpt", "pinterest", "linkedin"],
    "Knowledge Graphic": ["qru_store", "pinterest", "instagram", "linkedin", "facebook"],
    "Social Graphic": ["pinterest", "instagram", "facebook", "linkedin"],
    "Presentation": ["qru_store", "gumroad", "payhip", "linkedin"],
    "Character": ["qru_store", "etsy", "instagram", "pinterest"],
    "Illustration": ["qru_store", "etsy", "pinterest", "instagram"],
    "Photo": ["qru_store", "shopify", "email", "facebook"],
    "Logo": ["qru_store", "shopify", "email"],
    "Brand Asset": ["qru_store", "email", "facebook", "linkedin"],
    "Audio": ["qru_store", "gumroad", "payhip"],
    "Video": ["qru_store", "instagram", "facebook"],
    "Course Asset": ["qru_store", "gumroad", "payhip"],
}

# Rough deterministic manufacturing time per product (minutes) for planning.
_MINUTES = {"Poster": 2, "Infographic": 2, "Book": 4, "Workbook": 4, "Printable PDF": 3,
            "Presentation": 3, "Course": 5, "Flash Cards": 3, "Quick Card": 2}


def _product_minutes(ptype):
    return _MINUTES.get(ptype, 2)


def manufacturing_plan(asset):
    """Deterministic Founder Manufacturing Panel™ plan for an asset."""
    klass = classify_asset(asset)
    products = CLASS_TO_PRODUCTS.get(klass, ["Digital Download"])
    market_ids = CLASS_TO_MARKETPLACES.get(klass, ["qru_store"])
    marketplaces = [_MK[m] for m in market_ids if m in _MK]
    completed = is_completed_product_asset(klass)
    # Recommended order: the hero product first (matches the asset class), then supporting.
    hero = products[0] if products else None
    recommended = products[:5]
    est_minutes = sum(_product_minutes(p) for p in recommended)
    return {
        "asset_id": asset.get("id"), "asset_code": asset.get("asset_code"),
        "asset_name": asset.get("name"), "asset_type": asset.get("asset_type"),
        "classification": klass,
        "is_completed_product": completed,
        "hero_handling": ("Preserve as hero visual — manufacture supporting products around it."
                          if completed else "Use as source art for branded manufacturing."),
        "compatible_products": products,
        "recommended_products": recommended,
        "compatible_marketplaces": marketplaces,
        "estimated_minutes": est_minutes,
        "product_count": len(products),
    }


# --------------------------------------------------------------------------- #
# Manufacture™ — Founder-triggered creation of products from an asset.
# --------------------------------------------------------------------------- #
# Map the plan's marketing/visual product labels to real QRU manufacturing recipes.
_PRODUCT_TYPE_MAP = {
    "Digital Download": "Poster", "Classroom Poster": "Poster", "Teacher Resource": "Teacher Guide",
    "Pinterest Graphic": "Poster", "Instagram Post": "Poster", "Facebook Graphic": "Poster",
    "LinkedIn Graphic": "Poster", "Social Media Pack": "Short-form Content", "Marketing Graphic": "Poster",
    "Marketplace Preview": "Poster", "Email Banner": "Poster", "Website Hero": "Poster",
    "Illustration Pack": "Poster", "Sticker Pack": "Poster", "Brand Kit": "Poster",
    "Audio Narration": "Podcast Script",
}


def _recipe_type(label):
    return _PRODUCT_TYPE_MAP.get(label, label)


def _seed_content(asset, label):
    """Deterministic, on-brand marketing description ($0 AI) so the deliverable renders.
    Knowledge-First: this is presentation copy about the asset, never fabricated facts."""
    name = asset.get("name", "QRU Asset")
    family = asset.get("product_family") or "General"
    notes = asset.get("usage_notes") or ""
    return (
        f"# {name} — {label}\n\n"
        f"## Overview\n"
        f"A QRU {label} manufactured from the approved Founder asset **{name}** "
        f"({family}). Preserves the original QRU artwork as the hero visual, framed to "
        f"the QRU brand standard.\n\n"
        f"## What's Included\n"
        f"- The original approved QRU visual, preserved at full quality\n"
        f"- QRU brand framing, palette, and Treasure Standard™ presentation\n"
        f"- Marketplace-ready export sizing and metadata\n\n"
        f"## Usage\n"
        f"{notes or 'Use across QRU classrooms, families, and marketplaces as an official QRU product.'}\n"
    )


async def manufacture_from_asset(asset_id, product_labels, actor="Founder"):
    """Create one product per selected label, preserving the asset as hero visual.
    Founder-triggered. Products are created immediately (fast response) and their
    deliverables/design gates render in the background so the request never times out."""
    import vault
    asset = await db.asset_vault.find_one({"id": asset_id})
    if not asset:
        return None
    klass = classify_asset(asset)
    created, pids = [], []
    for label in product_labels:
        ptype = _recipe_type(label)
        count = await db.products.count_documents({})
        pid = gen_id()
        product = {
            "id": pid, "product_code": f"PRD-{count + 1:05d}",
            "title": f"{asset.get('name','QRU Asset')} — {label}",
            "product_type": ptype, "marketplace_label": label,
            "family": asset.get("product_family") or "General",
            "topic": asset.get("name", ""), "audience": "General", "learning_level": "Introductory",
            "content": _seed_content(asset, label),
            "status": "Needs Review",
            "assembled": True,
            "asset_mode": "use_imported",
            "manufactured_from_asset": asset_id,
            "asset_classification": klass,
            "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
        }
        await db.products.insert_one(dict(product))
        # Preserve the asset as the hero visual (no regeneration/redesign).
        try:
            await vault.apply_to_product(pid, asset_id, actor)
        except Exception as e:
            logger.error(f"apply_to_product failed for {pid}: {e}")
        pids.append(pid)
        p = await db.products.find_one({"id": pid}, {"content": 0})
        created.append(clean(p))

    # Render deliverables + design gate in the background (deterministic, $0 AI) so the
    # Founder gets an instant response; finished products land in the Founder Review Inbox™.
    import asyncio
    asyncio.create_task(_finish_manufacturing(pids, actor))

    try:
        from org_activity import log_org
        await log_org("Manufacturing Director™", "Manufacturing",
                      f"manufactured {len(created)} product(s) from Asset Vault™ {asset.get('asset_code')} ({klass}) —",
                      asset.get("asset_code", ""), "success")
    except Exception:
        pass
    return {"asset_id": asset_id, "asset_code": asset.get("asset_code"),
            "classification": klass, "created": created, "count": len(created)}


async def _finish_manufacturing(pids, actor):
    """Background: render deliverable + run Design Director™ gate for each new product."""
    import deliverable_renderer as dr
    import design_director as dd
    for pid in pids:
        try:
            await dr.ensure_deliverable(pid, actor)
            await dd.auto_gate(pid, actor)
        except Exception as e:
            logger.error(f"background render/gate failed for {pid}: {e}")
        import asyncio
        await asyncio.sleep(0)
