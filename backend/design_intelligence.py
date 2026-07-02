"""QRU Design Intelligence™ — the permanent visual foundation of Creative Studio™.

Creative Studio does not copy previous designs; it LEARNS the QRU Design Language™ and
consistently produces original products that feel unmistakably like QRU.

Libraries (Mongo collections):
- brand_library    : the canonical QRU brand standards (colors, typography, shield, badge, spacing, components, templates)
- design_library   : approved design references — grows as products earn Treasure Standard™
- master_assets    : the Master Asset Library™ (searchable, reusable assets with full metadata)
- design_language  : learned, evolving design principles
"""
import logging
from database import db
from models import gen_id, now_iso, clean

logger = logging.getLogger("qru.design")

SHIELD = "/qru-shield-light.png"

# Canonical QRU brand standards (the source of truth for every product).
BRAND_STANDARDS = {
    "colors": [
        {"name": "Royal Purple", "role": "Primary", "hsl": "266 74% 24%", "hex": "#35106A"},
        {"name": "QRU Gold", "role": "Accent", "hsl": "42 91% 53%", "hex": "#F5B21A"},
        {"name": "Deep Navy", "role": "Depth", "hsl": "252 45% 18%", "hex": "#221A42"},
        {"name": "White", "role": "Space", "hsl": "0 0% 100%", "hex": "#FFFFFF"},
        {"name": "Success Green", "role": "Verified", "hsl": "160 84% 34%", "hex": "#0E9F6E"},
    ],
    "typography": [
        {"name": "Outfit", "role": "Headings", "weights": [600, 700, 800]},
        {"name": "IBM Plex Sans", "role": "Body", "weights": [400, 500, 600]},
    ],
    "spacing": {"principle": "Generous — 2-3x breathing room reduces cognitive load", "unit": 4, "scale": [4, 8, 12, 16, 24, 32, 48, 64]},
    "shield": {"name": "QRU Shield™", "asset": SHIELD, "placement": "Top-left of every product"},
    "treasure_badge": {"name": "Treasure Standard™ Badge", "placement": "Displayed only on certified products"},
    "principles": [
        "Unmistakably QRU — brand recognizable at a glance",
        "Clarity over decoration — design supports understanding",
        "Warm, premium, trustworthy, hopeful",
        "Left-aligned reading flow with clear information hierarchy",
        "Memory Sentence™ always in a Royal Purple callout",
        "Verified status always visible; references expand on request",
    ],
    "components": [
        {"name": "QRU Callout Box", "use": "Memory Sentence™ and key takeaways"},
        {"name": "Verification Card", "use": "Kingdom Lion™ status + evidence level"},
        {"name": "Layer Selector", "use": "Layered Understanding depth control"},
        {"name": "Treasure Ribbon", "use": "Treasure Standard™ certification marker"},
        {"name": "QRU Product Card", "use": "Catalog and related products"},
    ],
    "templates": [
        {"name": "Master Cover Template™", "for": ["Book", "Course", "Workbook"]},
        {"name": "Poster Template™", "for": ["Poster", "Infographic"]},
        {"name": "Workbook Layout™", "for": ["Workbook", "Lesson Plan"]},
        {"name": "Presentation Layout™", "for": ["Presentation"]},
        {"name": "Interactive Lesson Template™", "for": ["Interactive Lesson", "Quiz", "Flash Cards"]},
        {"name": "Guide Template™", "for": ["Teacher Guide", "Caregiver Guide"]},
    ],
}

# Creative Studio autonomy — automatic template + style selection by product type.
TEMPLATE_RULES = {
    "Book": {"template": "Master Cover Template™", "layout": "Chaptered", "illustration": "Editorial"},
    "Workbook": {"template": "Workbook Layout™", "layout": "Activity Grid", "illustration": "Friendly"},
    "Poster": {"template": "Poster Template™", "layout": "Single Focal", "illustration": "Bold"},
    "Infographic": {"template": "Poster Template™", "layout": "Flow Diagram", "illustration": "Iconographic"},
    "Presentation": {"template": "Presentation Layout™", "layout": "Slide Deck", "illustration": "Minimal"},
    "Teacher Guide": {"template": "Guide Template™", "layout": "Structured", "illustration": "Editorial"},
    "Caregiver Guide": {"template": "Guide Template™", "layout": "Conversational", "illustration": "Warm"},
    "Course": {"template": "Master Cover Template™", "layout": "Modular", "illustration": "Editorial"},
    "Interactive Lesson": {"template": "Interactive Lesson Template™", "layout": "Progressive", "illustration": "Friendly"},
    "Quiz": {"template": "Interactive Lesson Template™", "layout": "Question Cards", "illustration": "Playful"},
    "Flash Cards": {"template": "Interactive Lesson Template™", "layout": "Card Deck", "illustration": "Playful"},
    "Podcast Script": {"template": "Guide Template™", "layout": "Script", "illustration": "Minimal"},
    "Video Script": {"template": "Guide Template™", "layout": "Storyboard", "illustration": "Cinematic"},
    "Short-form Content": {"template": "Poster Template™", "layout": "Social Tile", "illustration": "Bold"},
}

AUDIENCE_STYLE = {
    "Children": {"palette": "Bright QRU (Gold-forward)", "typography": "Outfit rounded", "tone": "Playful & encouraging"},
    "Teens": {"palette": "Modern QRU (Purple-forward)", "typography": "Outfit bold", "tone": "Confident & energetic"},
    "General public": {"palette": "Core QRU", "typography": "Outfit + IBM Plex", "tone": "Warm & clear"},
    "Professionals": {"palette": "Navy-forward QRU", "typography": "IBM Plex refined", "tone": "Precise & trusted"},
    "Caregivers": {"palette": "Warm QRU", "typography": "IBM Plex", "tone": "Reassuring"},
    "Teachers": {"palette": "Core QRU", "typography": "Outfit + IBM Plex", "tone": "Structured & supportive"},
}

# The QRU Design Checklist™ — must all pass before a design is approved.
CHECKLIST_QUESTIONS = [
    "Is this unmistakably QRU?",
    "Would someone recognize the brand immediately?",
    "Does it follow QRU typography?",
    "Does it follow QRU colors?",
    "Does it support understanding?",
    "Does it reduce confusion?",
    "Does it feel premium?",
    "Does it create emotional trust?",
    "Does it reinforce the QRU mission?",
    "Would someone proudly share this product?",
]

BASELINE_PRINCIPLES = [
    {"principle": "QRU Shield™ anchors the top-left of every product", "source": "Brand Standard", "category": "Branding"},
    {"principle": "Memory Sentence™ lives in a Royal Purple callout", "source": "Brand Standard", "category": "Layout"},
    {"principle": "Headings in Outfit, body in IBM Plex Sans", "source": "Brand Standard", "category": "Typography"},
    {"principle": "Generous spacing reduces cognitive load", "source": "Brand Standard", "category": "Spacing"},
    {"principle": "Verified status is always visible; references expand on request", "source": "Brand Standard", "category": "Trust"},
]


async def seed_design_intelligence():
    if await db.brand_library.count_documents({}) == 0:
        await db.brand_library.insert_one({"id": gen_id(), "kind": "standards", **BRAND_STANDARDS, "created_at": now_iso()})
    if await db.design_language.count_documents({}) == 0:
        for p in BASELINE_PRINCIPLES:
            await db.design_language.insert_one({"id": gen_id(), **p, "created_at": now_iso()})
    # seed master assets with the core brand assets
    if await db.master_assets.count_documents({}) == 0:
        core = [
            ("QRU Shield™", "Logo", "QRU Brand", ["shield", "logo", "brand"], SHIELD),
            ("Treasure Standard™ Badge", "Badge", "QRU Brand", ["treasure", "badge", "quality"], SHIELD),
            ("Master Cover Template™", "Template", "QRU Brand", ["cover", "template", "book"], SHIELD),
        ]
        for title, cat, fam, kw, preview in core:
            await db.master_assets.insert_one({
                "id": gen_id(), "asset_id": f"QRU-ASSET-{gen_id()[:6].upper()}", "title": title,
                "category": cat, "product_family": fam, "knowledge_record_id": None, "keywords": kw,
                "version": 1, "treasure_standard": True, "creator": "Creative Studio Director™",
                "related_products": [], "preview": preview, "editable_source": None, "export_files": [],
                "license_status": "QRU Owned", "created_at": now_iso(),
            })
    # learn from any existing Treasure Standard™ products so the library isn't empty
    if await db.design_library.count_documents({}) == 0:
        approved = await db.products.find({"treasure_standard": True, "status": "Published"}).to_list(50)
        for p in approved:
            await learn_from_product(p)


def recommend_templates(product_type, audience="General public"):
    rule = TEMPLATE_RULES.get(product_type, {"template": "Master Cover Template™", "layout": "Standard", "illustration": "Editorial"})
    style = AUDIENCE_STYLE.get(audience, AUDIENCE_STYLE["General public"])
    return {
        "product_type": product_type, "audience": audience,
        "cover_template": rule["template"], "layout": rule["layout"], "illustration_style": rule["illustration"],
        "palette": style["palette"], "typography": style["typography"], "tone": style["tone"],
        "icon_set": "QRU Line Icons", "brand_elements": ["QRU Shield™", "Brand Footer", "Treasure Standard™ Badge"],
    }


async def run_design_checklist(product):
    """Automated Design Checklist™. For QRU-manufactured products these are deterministic,
    driven by whether Creative Studio branding + Treasure Standard™ are applied."""
    branded = product.get("creative_status") == "Reviewed"
    treasure = product.get("treasure_standard", False)
    traceable = bool(product.get("knowledge_record_id"))
    answers = []
    for q in CHECKLIST_QUESTIONS:
        # Understanding/mission questions rely on traceable verified knowledge; visual questions on branding.
        if q in ("Does it support understanding?", "Does it reduce confusion?", "Does it reinforce the QRU mission?"):
            passed = traceable
        elif q in ("Does it feel premium?", "Would someone proudly share this product?"):
            passed = branded and treasure
        else:
            passed = branded
        answers.append({"question": q, "pass": passed})
    all_pass = all(a["pass"] for a in answers)
    return {"passed": all_pass, "answers": answers,
            "verdict": "Approved — unmistakably QRU." if all_pass else "Revise — apply QRU branding before release."}


async def learn_from_product(product):
    """Called when a product earns Treasure Standard™. Grows the Design Library, registers a
    Master Asset, and extracts a reusable design principle — the system learns from itself."""
    try:
        pid = product["id"]
        if await db.design_library.find_one({"product_id": pid}):
            return
        rule = TEMPLATE_RULES.get(product.get("product_type"), {})
        # Design Library reference
        await db.design_library.insert_one({
            "id": gen_id(), "product_id": pid, "product_code": product.get("product_code"),
            "title": product.get("title"), "product_type": product.get("product_type"),
            "product_family": product.get("family"), "knowledge_record_id": product.get("knowledge_record_id"),
            "template": rule.get("template"), "layout": rule.get("layout"),
            "treasure_standard": True, "preview": SHIELD, "created_at": now_iso(),
        })
        # Master Asset entry
        await db.master_assets.insert_one({
            "id": gen_id(), "asset_id": f"QRU-ASSET-{gen_id()[:6].upper()}",
            "title": product.get("title"), "category": product.get("product_type"),
            "product_family": product.get("family"), "knowledge_record_id": product.get("knowledge_record_id"),
            "keywords": [product.get("product_type", ""), product.get("family", ""), "treasure standard"],
            "version": 1, "treasure_standard": True, "creator": "Creative Studio Director™",
            "related_products": [], "preview": SHIELD, "editable_source": None, "export_files": [],
            "license_status": "QRU Owned", "created_at": now_iso(),
        })
        # Extract a design principle (learning) — bounded, no duplicate spam
        ptype = product.get("product_type")
        existing = await db.design_language.find_one({"category": "Learned", "principle": {"$regex": ptype}})
        if not existing and rule.get("template"):
            await db.design_language.insert_one({
                "id": gen_id(),
                "principle": f"{ptype} products use the {rule.get('template')} with a {rule.get('layout','standard')} layout for QRU consistency.",
                "source": product.get("product_code", "Approved product"), "category": "Learned", "created_at": now_iso(),
            })
    except Exception as e:
        logger.error(f"design learning failed: {e}")


async def library_stats():
    return {
        "brand_standards": 1,
        "design_references": await db.design_library.count_documents({}),
        "master_assets": await db.master_assets.count_documents({}),
        "design_principles": await db.design_language.count_documents({}),
    }
