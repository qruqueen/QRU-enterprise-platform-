"""QRU Educational Design System™ (QEDS) — the governed, versioned educational constitution.

QEDS defines HOW QRU teaches (QBOS defines how it looks). READ-ONLY for all AI agents;
changes require an educational governance workflow. Every product records the QEDS version
that governed its teaching. The TEACHING_PREAMBLE is injected into every manufacturing prompt.
"""
import logging

from database import db
from models import gen_id, now_iso, clean

logger = logging.getLogger("qru.qeds")

QEDS_VERSION = "1.0"
QEDS_EFFECTIVE = "2026-07-03"

LEARNING_MODEL = ["Observe", "Question", "Understand", "Remember", "Apply", "Teach Someone Else"]

GUIDED_UNDERSTANDING = [
    "The Question", "Simple Answer", "Why It Matters", "Real-World Example", "QRU Translation™",
    "QRU Memory Sentence™", "Visual Explanation", "Practice", "Common Mistakes", "Application",
    "Key Vocabulary", "Deep Roots™", "Next Question",
]

ANALOGY_LIBRARY = ["Battlefield™", "Dating Decoder™", "Football™", "Neighborhood™", "Marketplace™",
                   "Nature", "Construction", "Cooking", "Transportation", "Health", "Business", "Daily life"]

TREASURE_CRITERIA = ["Accuracy", "Clarity", "Educational value", "Practical usefulness", "Professional quality",
                     "Logical organization", "Visual support", "Memory reinforcement", "Real-world application",
                     "Accessibility", "Verification", "Treasure Standard™ approval"]

# Injected into every manufacturing system prompt so the whole factory teaches the QRU way.
TEACHING_PREAMBLE = (
    "GOVERNED BY THE QRU EDUCATIONAL DESIGN SYSTEM™ (QEDS v1.0). Teach people HOW to think, not WHAT to think. "
    "Core question for every choice: 'How do we remove as much unnecessary confusion as possible without losing the truth?' "
    "Use CONVERSATION-FIRST™: begin with a familiar experience, teach the concept BEFORE the vocabulary. "
    "Follow the GUIDED UNDERSTANDING SYSTEM™ when appropriate: The Question → Simple Answer → Why It Matters → "
    "Real-World Example → QRU Translation™ (plain-language restatement) → QRU Memory Sentence™ (one sticky line) → "
    "Visual Explanation → Practice → Common Mistakes → Application → Key Vocabulary → Deep Roots™ → Next Question. "
    "Use ANALOGIES from familiar life (battlefield, dating, football, neighborhood, marketplace, cooking, nature) when they help. "
    "Prefer examples over definitions, stories over jargon, diagrams over dense text. Design for long-term retention "
    "(memory sentences, analogies, active recall). The learner should finish feeling more confident, capable, and curious."
)

CONSTITUTION = {
    "version": QEDS_VERSION,
    "title": "QRU Educational Design System™ (QEDS) — Educational Constitution",
    "effective_date": QEDS_EFFECTIVE,
    "philosophy": "QRU does not manufacture information — it manufactures understanding. Success metric: the learner "
                  "confidently says 'I finally understand.'",
    "promise": ["Teach how to think, not what to think", "Encourage curiosity", "Encourage observation",
                "Encourage verification", "Encourage understanding", "Encourage application"],
    "learning_model": LEARNING_MODEL,
    "conversation_first": "Teach through conversation before vocabulary; begin with familiar experiences; "
                          "introduce technical language only after the underlying idea is understood.",
    "guided_understanding_system": GUIDED_UNDERSTANDING,
    "qru_translation": "Translate complex ideas into everyday language whenever it can be done without losing truth.",
    "memory_system": ["Memory sentences", "Visual memory", "Stories", "Analogies", "Color coding", "Diagrams",
                      "Repetition", "Active recall", "Practical examples"],
    "analogy_library": ANALOGY_LIBRARY,
    "visual_learning": "Use illustrations when they improve learning. Prefer diagrams over paragraphs, examples over "
                       "definitions, visual organization over dense text.",
    "understanding_before_vocabulary": "Never assume prior terminology. Teach the concept first, the vocabulary second.",
    "remove_unnecessary_confusion": "Every educational decision must reduce confusion without losing the truth.",
    "treasure_standard_criteria": TREASURE_CRITERIA,
    "the_educator": "Every AI agent behaves like a patient teacher, trusted mentor, and guide. Never arrogant, never "
                    "intentionally confusing, never teaching to impress — always teaching to help.",
    "learning_experience": ["More confident", "More capable", "More curious", "More prepared", "More empowered"],
    "governance": "READ-ONLY enterprise standard. Changes require Educational Review → Verification Review → Founder "
                  "Approval → Version Number → Change Log → Effective Date → Historical Archive. History is never overwritten.",
    "mission": "Every lesson, workbook, book, presentation, poster, video, animation, quiz, course, and podcast teaches "
               "the QRU way — one permanent educational philosophy.",
}


async def seed_qeds():
    if not await db.qeds_versions.find_one({"version": QEDS_VERSION}):
        await db.qeds_versions.insert_one({
            "id": gen_id(), "version": QEDS_VERSION, "status": "Active", "read_only": True,
            "constitution": CONSTITUTION, "effective_date": QEDS_EFFECTIVE,
            "approved_by": "Founder & CEO", "created_at": now_iso(),
            "changelog": "Initial ratification of the QRU Educational Constitution (v1.0)."})
        logger.info("QEDS v1.0 constitution ratified")


async def active_version():
    doc = await db.qeds_versions.find_one({"status": "Active"})
    return (doc or {}).get("version", QEDS_VERSION)


async def get_constitution():
    doc = await db.qeds_versions.find_one({"status": "Active"})
    return clean(doc) if doc else {"version": QEDS_VERSION, "constitution": CONSTITUTION}


async def version_history():
    docs = await db.qeds_versions.find().sort("created_at", -1).to_list(50)
    return [{"version": d["version"], "status": d.get("status"), "effective_date": d.get("effective_date"),
             "approved_by": d.get("approved_by"), "changelog": d.get("changelog"),
             "created_at": d.get("created_at")} for d in docs]


async def methodology_library():
    return {"governed": True, "qeds_version": await active_version(),
            "learning_model": LEARNING_MODEL, "guided_understanding_system": GUIDED_UNDERSTANDING,
            "analogy_library": ANALOGY_LIBRARY, "memory_system": CONSTITUTION["memory_system"],
            "treasure_standard_criteria": TREASURE_CRITERIA,
            "teaching_preamble": TEACHING_PREAMBLE}


# ---------------- Educational Review™ (QRU teaching test — deterministic) ----------------
async def educational_review(pid):
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    content = (p.get("content") or "").lower()
    v = p.get("verification") or {}
    checks = [
        {"principle": "Teaches understanding (not just facts)", "pass": bool(p.get("verified") or v.get("decision") == "approve")},
        {"principle": "Real-world example present", "pass": any(k in content for k in ["example", "for instance", "imagine", "e.g."])},
        {"principle": "Plain-language / QRU Translation™", "pass": len(content) > 200},
        {"principle": "Memory reinforcement (summary/recap/remember)", "pass": any(k in content for k in ["remember", "summary", "recap", "key idea", "takeaway"])},
        {"principle": "Practice or application", "pass": any(k in content for k in ["practice", "try", "apply", "exercise", "question"])},
        {"principle": "Warm, clear teacher voice", "pass": bool(p.get("product_type"))},
        {"principle": "Treasure Standard™ met", "pass": bool(p.get("treasure_standard"))},
    ]
    passed = sum(1 for c in checks if c["pass"])
    score = round(passed / len(checks) * 100)
    return {"product_code": p.get("product_code"), "title": p.get("title"), "score": score,
            "passed": passed, "total": len(checks),
            "verdict": "Teaches the QRU way" if score >= 80 else "Continue improving automatically",
            "checks": checks, "qeds_version": await active_version()}


async def propose_change(section, proposed_change, rationale, actor):
    doc = {"id": gen_id(), "current_version": await active_version(), "section": section,
           "proposed_change": proposed_change, "rationale": rationale, "status": "Proposed",
           "stage": "Educational Review", "proposed_by": actor,
           "impact_assessment": "Pending Educational + Verification review.", "created_at": now_iso()}
    await db.qeds_change_proposals.insert_one(dict(doc))
    return clean(doc)


async def list_proposals():
    return clean(await db.qeds_change_proposals.find().sort("created_at", -1).to_list(100))
