"""QRU Constitution™ — the permanent, version-controlled foundational operating manual.

The highest-level governing authority for every division, workflow, AI agent, recipe,
design system, publishing pipeline, analytics engine, and future capability. It sits above
QBOS (how QRU looks) and QEDS (how QRU teaches). READ-ONLY; changes require governance.
"""
from database import db
from models import gen_id, now_iso, clean

CONSTITUTION_VERSION = "1.0"
CONSTITUTION_EFFECTIVE = "2026-07-03"

ARTICLES = [
    {"article": "I", "title": "Mission",
     "text": "QRU exists to manufacture understanding. Knowledge → understanding → wisdom → better decisions → better lives. Every product must contribute to that mission."},
    {"article": "II", "title": "The Treasure Standard™",
     "text": "The governing quality system. Every product must satisfy: Truth, Clarity, Beauty, Educational Value, Professional Quality, Accessibility, Consistency, Consumer Readiness, Long-term usefulness. Failing any gate returns it to manufacturing automatically."},
    {"article": "III", "title": "The QRU Factory™",
     "text": "QRU is a manufacturing enterprise that manufactures understanding, not merely files. Every Manufacturing Order begins with verified knowledge and ends with measurable educational impact. Build the Factory once, improve it forever."},
    {"article": "IV", "title": "Knowledge First",
     "text": "Knowledge Records are the foundation. Every product is manufactured from verified Knowledge Records rather than independently authored. One verified understanding may produce many products."},
    {"article": "V", "title": "Divisions",
     "text": "Every Division improves one part of the manufacturing system: Verification, Research, Knowledge, Creative Studio, Manufacturing, Publishing, Distribution, Analytics, Marketing, Customer Experience, Finance, Innovation, Automation, Brand, Governance, Licensing, Legal, Technology, Education, Community. Future divisions inherit these principles."},
    {"article": "VI", "title": "Autonomy",
     "text": "Automation reduces repetitive Founder work. QRU prepares, coordinates, recovers from failures, learns continuously, recommends improvements, and escalates only where human judgment is genuinely required."},
    {"article": "VII", "title": "Self-Improvement",
     "text": "Every division continuously asks: How can we reduce friction? Improve quality? Automate responsibly? Improve understanding? Better serve learners?"},
    {"article": "VIII", "title": "Brand Operating System™",
     "text": "Every product inherits QBOS: QRU Shield™, Treasure Standard™, typography, color/layout systems, design language, illustration & photography standards, interior/cover/poster/presentation architecture, video/animation/social branding, packaging, copyright, licensing, watermarks, seals, templates. No independent visual asset bypasses QBOS."},
    {"article": "IX", "title": "Executive Intelligence™",
     "text": "QRU continuously monitors Factory Health, Division Health, Manufacturing, Publishing, Distribution, Revenue, Customer & Educational outcomes, efficiency, AI usage, and automation opportunities. Recommendations must explain WHY, not merely WHAT."},
    {"article": "X", "title": "Continuous Improvement",
     "text": "Every completed Manufacturing Order teaches the factory. Failures improve workflows; success improves templates; feedback improves products; analytics improve strategy. QRU becomes progressively more autonomous while maintaining or improving Treasure Standard™ quality."},
    {"article": "XI", "title": "Founder Principle",
     "text": "The Founder owns vision, priorities, ethics, and final judgment. QRU owns manufacturing excellence. The enterprise requires fewer Founder actions over time while increasing quality, reliability, consistency, and educational impact."},
    {"article": "XII", "title": "The QRU Promise™",
     "text": "Success is not measured by how many products we manufacture, but by how many people genuinely understand because of them."},
]

CONSTITUTION = {
    "version": CONSTITUTION_VERSION,
    "title": "QRU Constitution™ — Foundational Operating Manual",
    "effective_date": CONSTITUTION_EFFECTIVE,
    "preamble": "The permanent governing constitution of the QRU Enterprise and the highest-level reference "
                "document for every AI agent, workflow, manufacturing process, design system, automation, "
                "publishing pipeline, analytics engine, integration, and future capability.",
    "articles": ARTICLES,
    "governs": ["QBOS — QRU Brand Operating System™ (how QRU looks)",
                "QEDS — QRU Educational Design System™ (how QRU teaches)"],
}


async def seed_constitution():
    if not await db.constitution_versions.find_one({"version": CONSTITUTION_VERSION}):
        await db.constitution_versions.insert_one({
            "id": gen_id(), "version": CONSTITUTION_VERSION, "status": "Active", "read_only": True,
            "constitution": CONSTITUTION, "effective_date": CONSTITUTION_EFFECTIVE,
            "approved_by": "Founder & CEO", "created_at": now_iso(),
            "changelog": "Initial ratification of the QRU Constitution (v1.0)."})


async def active_version():
    doc = await db.constitution_versions.find_one({"status": "Active"})
    return (doc or {}).get("version", CONSTITUTION_VERSION)


async def get_constitution():
    doc = await db.constitution_versions.find_one({"status": "Active"})
    return clean(doc) if doc else {"version": CONSTITUTION_VERSION, "constitution": CONSTITUTION}


async def version_history():
    docs = await db.constitution_versions.find().sort("created_at", -1).to_list(50)
    return [{"version": d["version"], "status": d.get("status"), "effective_date": d.get("effective_date"),
             "approved_by": d.get("approved_by"), "changelog": d.get("changelog"),
             "created_at": d.get("created_at")} for d in docs]


async def propose_change(article, proposed_change, rationale, actor):
    doc = {"id": gen_id(), "current_version": await active_version(), "article": article,
           "proposed_change": proposed_change, "rationale": rationale, "status": "Proposed",
           "stage": "Governance Review", "proposed_by": actor, "created_at": now_iso()}
    await db.constitution_change_proposals.insert_one(dict(doc))
    return clean(doc)


async def list_proposals():
    return clean(await db.constitution_change_proposals.find().sort("created_at", -1).to_list(100))


async def governance_overview():
    import qbos
    import qeds
    return {
        "documents": [
            {"key": "constitution", "name": "QRU Constitution™", "scope": "Foundational operating manual",
             "version": await active_version(), "api": "/api/governance/constitution"},
            {"key": "qbos", "name": "QRU Brand Operating System™ (QBOS)", "scope": "How QRU looks",
             "version": await qbos.active_version(), "api": "/api/qbos/constitution"},
            {"key": "qeds", "name": "QRU Educational Design System™ (QEDS)", "scope": "How QRU teaches",
             "version": await qeds.active_version(), "api": "/api/qeds/constitution"},
        ],
        "principle": "Future improvements modify these documents through version-controlled governance rather than scattered prompts.",
    }
