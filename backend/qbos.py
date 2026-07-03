"""QRU Brand Operating System™ (QBOS) — the governed, versioned visual constitution.

QBOS is a READ-ONLY enterprise policy for all AI agents. Agents may reference it but may
not alter it. Changes require a formal governance workflow (propose → review → Founder
approval → new version). Complete version history is preserved (never overwritten), and
every manufactured product records which QBOS version governed its design.
"""
import logging

from database import db
from models import gen_id, now_iso, clean
import design_language as dl

logger = logging.getLogger("qru.qbos")

QBOS_VERSION = "1.0"
QBOS_EFFECTIVE = "2026-07-03"

# The Visual Constitution of QRU (v1.0) — structured, faithful to the master directive.
CONSTITUTION = {
    "version": QBOS_VERSION,
    "title": "QRU Enterprise Brand Operating System™ (QBOS) — Treasure Standard™ Master Directive",
    "effective_date": QBOS_EFFECTIVE,
    "core_question": "How do we remove as much unnecessary confusion as possible without losing the truth?",
    "purpose": "The purpose of QRU branding is not decoration — it is to make understanding easier. "
               "Every visual decision must answer: 'Does this help the learner understand?' If no, remove it.",
    "foundational_principles": ["Truth", "Understanding", "Clarity", "Professionalism", "Trust", "Hope", "Human Advancement"],
    "visual_philosophy": "The factory may manufacture millions of products; the learner should experience ONE brand. "
                         "Consistency means every page feels unmistakably QRU — not that every page looks identical. "
                         "Branding supports learning; learning never sacrifices itself for branding.",
    "color_system": {
        "enterprise": {"Royal Purple": "#35106A", "QRU Gold": "#F5B21A", "Deep Navy": "#1A1434", "White": "#FFFFFF"},
        "enterprise_scope": ["Covers", "Logos", "Enterprise dashboards", "Marketing", "Headers", "Navigation", "Major UI"],
        "interior_rule": "Interior educational content may freely use ANY appropriate palette that improves understanding "
                         "(scientific, medical, trading, mind-map, infographic, memory systems). Color must communicate meaning. "
                         "Teach first, brand second.",
    },
    "shield": {"policy": "The QRU Shield™ is permanent IP. Never redesign, recreate, reinterpret, or allow AI to invent "
                         "alternative shields. Every application retrieves the official shield from the Brand Asset Library™.",
               "canonical": "design_language.draw_shield (deterministic vector)"},
    "treasure_standard": "QRU's highest quality designation — verified understanding. Earned through full review; never decorative.",
    "cover_system": {"fixed": ["Official Shield™", "Publisher identity (QRU PRESS™)", "Series banner", "Typography hierarchy",
                               "Treasure Standard™ seal", "Edition", "Footer"],
                     "variable": ["Topic", "Artwork", "Subtitle", "Audience", "Division", "Accent color", "Edition"]},
    "interior_system": "Interior pages optimize learning with greater design flexibility: white space, readable typography, "
                       "large headings, icons, illustrations, memory graphics, conversation layouts, examples, practice, "
                       "comparison tables, step-by-step walkthroughs, educational color coding. Objective is understanding, not decoration.",
    "voice": "QRU communicates like a trusted teacher, patient mentor, knowledgeable guide. Never arrogant, confusing, or "
             "unnecessarily academic. Teach first, impress second.",
    "experience_standard": ["Professional", "Calm", "Premium", "Helpful", "Organized", "Encouraging", "Trustworthy",
                            "Simple", "Elegant", "Modern", "Human-centered"],
    "product_test": [
        "Does this look like QRU?", "Does this teach like QRU?", "Does this reduce confusion?",
        "Does this increase understanding?", "Does it meet Treasure Standard™?", "Would a learner trust this?",
        "Would a teacher recommend this?", "Would the Founder proudly place their name on this permanently?",
    ],
    "brand_review_divisions": ["Knowledge Division™", "Verification Lion™", "Legacy Bear™", "Consumer Advocate™",
                               "Brand Studio™", "Creative Studio™", "Accessibility Review™",
                               "Educational Psychology Review™", "Quality Control™", "Treasure Standard™"],
    "governance": "QBOS is a governed enterprise standard, not a prompt. READ-ONLY for all AI agents. Changes require: "
                  "Proposed Change → Impact Assessment → Brand Studio™ Review → Verification Review → Founder Approval → "
                  "Version Assignment → Change Log → Effective Date → Enterprise Notification. Version history is never overwritten.",
    "long_term_objective": "Anyone, years from now, should open any QRU book, video, course, poster, workbook, website, or app "
                           "and immediately recognize: 'This is unmistakably a QRU Treasure Standard™ product.'",
}


async def seed_qbos():
    existing = await db.qbos_versions.find_one({"version": QBOS_VERSION})
    if not existing:
        await db.qbos_versions.insert_one({
            "id": gen_id(), "version": QBOS_VERSION, "status": "Active", "read_only": True,
            "constitution": CONSTITUTION, "effective_date": QBOS_EFFECTIVE,
            "approved_by": "Founder & CEO", "created_at": now_iso(),
            "changelog": "Initial ratification of the QRU Visual Constitution (v1.0).",
        })
        logger.info("QBOS v1.0 constitution ratified")


async def active_version():
    doc = await db.qbos_versions.find_one({"status": "Active"})
    return (doc or {}).get("version", QBOS_VERSION)


async def get_constitution():
    doc = await db.qbos_versions.find_one({"status": "Active"})
    return clean(doc) if doc else {"version": QBOS_VERSION, "constitution": CONSTITUTION}


async def version_history():
    docs = await db.qbos_versions.find().sort("created_at", -1).to_list(50)
    return [{"version": d["version"], "status": d.get("status"), "effective_date": d.get("effective_date"),
             "approved_by": d.get("approved_by"), "changelog": d.get("changelog"),
             "created_at": d.get("created_at")} for d in docs]


# ---------------- Brand Asset Library™ (governed, retrieved — never AI-invented) ----------------
async def brand_asset_library():
    palettes = [{"key": k, "label": v["label"], "accent": "#%02X%02X%02X" % v["accent"],
                 "top": "#%02X%02X%02X" % v["top"], "bottom": "#%02X%02X%02X" % v["bottom"]}
                for k, v in dl.PALETTES.items()]
    return {
        "governed": True, "qbos_version": await active_version(),
        "note": "Canonical assets are retrieved from this library. No AI agent may invent replacements.",
        "shield": {"name": "QRU Shield™", "source": "design_language.draw_shield", "editable": False},
        "logos": {"wordmark": "QRU", "publisher": "QRU PRESS™", "editable": False},
        "treasure_standard_seal": {"name": "Treasure Standard™", "rule": "Earned, never decorative", "editable": False},
        "enterprise_colors": CONSTITUTION["color_system"]["enterprise"],
        "subject_palettes": palettes,
        "typography": {"titles": "Liberation Serif Bold", "labels": "Liberation Sans", "body": "Liberation Serif"},
        "cover_templates": {"fixed_elements": CONSTITUTION["cover_system"]["fixed"],
                            "variable_elements": CONSTITUTION["cover_system"]["variable"]},
        "export_formats": [{"key": k, **v} for k, v in dl.EXPORT_SPECS.items()],
    }


# ---------------- QRU Product Test™ / Enterprise Brand Review™ ----------------
async def product_test(pid):
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    v = p.get("verification") or {}
    title = p.get("title", "")
    visual = dl.visual_review(clean(p))
    checks = [
        {"q": "Does this look like QRU?", "pass": bool(p.get("design_language_applied") and p.get("cover_url"))},
        {"q": "Does this teach like QRU?", "pass": bool(p.get("content"))},
        {"q": "Does this reduce confusion?", "pass": len(title) <= 120 and bool(p.get("product_type"))},
        {"q": "Does this increase understanding?", "pass": bool(p.get("verified") or v.get("decision") == "approve")},
        {"q": "Does it meet Treasure Standard™?", "pass": bool(p.get("treasure_standard"))},
        {"q": "Would a learner trust this?", "pass": bool(p.get("protected") or p.get("status") == "Published")},
        {"q": "Would a teacher recommend this?", "pass": visual["approved"]},
        {"q": "Would the Founder proudly sign this?", "pass": bool(v.get("founder_would_be_proud", p.get("treasure_standard")))},
    ]
    passed = sum(1 for c in checks if c["pass"])
    score = round(passed / len(checks) * 100)
    return {"product_code": p.get("product_code"), "title": title, "score": score,
            "passed": passed, "total": len(checks), "verdict": "QRU Treasure Standard™" if score == 100 else
            ("Approved" if score >= 80 else "Continue improving automatically"),
            "checks": checks, "visual_review": visual, "qbos_version": await active_version()}


# ---------------- Governance change workflow (propose only; Founder approves) ----------------
async def propose_change(section, proposed_change, rationale, actor):
    doc = {"id": gen_id(), "current_version": await active_version(), "section": section,
           "proposed_change": proposed_change, "rationale": rationale,
           "status": "Proposed", "stage": "Brand Studio™ Review", "proposed_by": actor,
           "impact_assessment": "Pending Brand Studio™ + Verification review.",
           "created_at": now_iso()}
    await db.qbos_change_proposals.insert_one(dict(doc))
    return clean(doc)


async def list_proposals():
    return clean(await db.qbos_change_proposals.find().sort("created_at", -1).to_list(100))
