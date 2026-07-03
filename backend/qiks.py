"""
QRU INSTITUTIONAL KNOWLEDGE SYSTEM™ (QIKS) — the permanent enterprise memory,
standards library, governance repository, and knowledge base.

Principles enforced here:
  - Knowledge is NEVER overwritten. Every update creates a new version + change history.
  - Only Founder-approved knowledge enters the permanent Standards Registry.
  - Ideas are promoted through stages; everything is cross-linked as a Knowledge Graph.
  - AI agents RETRIEVE institutional knowledge (via these endpoints) rather than reinvent it.

Collections: `qiks_standards`, `qiks_lessons`
"""
from datetime import datetime, timezone

from database import db

STD_COL = db["qiks_standards"]
LESSON_COL = db["qiks_lessons"]


def _now():
    return datetime.now(timezone.utc).isoformat()


# 24 institutional knowledge collections
CATEGORIES = [
    "Enterprise Standards™", "Manufacturing Principles™", "Educational Methodologies™",
    "Brand Standards™", "Treasure Standard™", "Verification Principles™",
    "Leadership Principles™", "Marketing Principles™", "Consumer Experience™",
    "Creative Standards™", "Product Recipes™", "Character Bible™",
    "Workforce Identity™", "Automation Rules™", "Publishing Standards™",
    "Distribution Standards™", "Software Architecture™", "Database Architecture™",
    "Analytics Standards™", "Innovation History™", "Lessons Learned™",
    "Research Discoveries™", "Future Ideas™", "Archived Standards™",
]

# Knowledge Promotion™ pipeline
PROMOTION_STAGES = [
    "Conversation", "Working Idea", "Working Principle", "Framework Draft",
    "Verification Review", "Founder Approval", "QRU Standard™",
    "Enterprise Knowledge™", "Institutional Knowledge™",
]

# Divisions that contribute Enterprise Memory™
DIVISIONS = [
    "Manufacturing", "Publishing", "Creative Studio", "Verification", "Marketing",
    "Finance", "Distribution", "Customer Experience", "Research",
    "Software Engineering", "Enterprise Intelligence",
]


def _std(sid, name, category, desc, purpose, related=None, agents=None, colleges=None,
         products=None, recipes=None, impl="Implemented", refs=None, links=None):
    return {
        "id": sid, "standard_id": sid, "name": name, "category": category,
        "description": desc, "purpose": purpose,
        "status": "Active", "version": "1.0", "date_adopted": "2026-07-03",
        "founder_approval": True,
        "related_standards": related or [],
        "related_products": products or [],
        "related_recipes": recipes or [],
        "related_ai_agents": agents or [],
        "related_colleges": colleges or [],
        "implementation_status": impl,
        "promotion_stage": "Institutional Knowledge™",
        "change_history": [{
            "version": "1.0", "date": "2026-07-03",
            "reason": "Adopted as founding institutional standard.",
            "reviewer": "Kingdom Lion™", "founder_approval": True,
        }],
        "superseded_versions": [],
        "enterprise_references": refs or [],
        "graph_links": links or [],
        "created_at": _now(), "updated_at": _now(),
    }


SEED_STANDARDS = [
    _std("STD-00001", "Treasure Standard™", "Treasure Standard™",
         "The master quality constitution. Every product must pass THE QRU QUESTION™ ('Would the Founder be proud to put her name on this?') and the 16-point Treasure Standard™ Test.",
         "Guarantee that nothing leaves QRU unless it is true, understandable, useful, complete, beautiful, memorable, and on-brand.",
         related=["STD-00002", "STD-00008", "STD-00010"], agents=["Kingdom Lion™"],
         refs=["constitution.py", "product_protection.treasure_finalize"],
         links=[{"to": "STD-00008", "relation": "verified by"}, {"to": "STD-00003", "relation": "requires brand compliance"}]),
    _std("STD-00002", "The One Question Test™", "Enterprise Standards™",
         "Every department must answer ONE clear Primary Question. If the question cannot be stated clearly, the department is not yet defined and must not be added.",
         "Keep the enterprise focused: no feature exists without a clear business reason.",
         related=["STD-00013"], agents=["Enterprise Librarian™"],
         refs=["department_registry.py", "/api/departments"]),
    _std("STD-00003", "QRU Brand Operating System™ (QBOS)", "Brand Standards™",
         "The visual constitution: color system, typography, QRU Shield™, layout and asset standards governing every visual QRU produces.",
         "Ensure visual consistency and premium brand quality across all products and platforms.",
         related=["STD-00016", "STD-00006"], agents=["Creative Studio Director™"],
         refs=["qbos.py", "design_language.py"]),
    _std("STD-00004", "QRU Educational Design System™ (QEDS)", "Educational Methodologies™",
         "The educational constitution defining how understanding is structured, layered, and made memorable for every audience.",
         "Ensure every product teaches effectively across child/consumer/student/professional/scientific modes.",
         related=["STD-00007"], agents=["College Deans™"], colleges=["Health", "Faith"],
         refs=["qeds.py"]),
    _std("STD-00005", "QRU Master Constitution™", "Enterprise Standards™",
         "The supreme governing document. All standards, departments, and AI agents are subordinate to the Constitution.",
         "Provide a single, protected authority for QRU's laws, mission, and values.",
         related=["STD-00001", "STD-00002"], agents=["Constitution Keeper™"],
         refs=["constitution.py", "/api/governance"]),
    _std("STD-00006", "Workforce Identity System™ / Character Bible™", "Character Bible™",
         "Permanent Character Records for every QRU Director, mascot, reviewer, and guide. Apps retrieve approved characters; they are never replaced with generic AI portraits.",
         "Guarantee visual, personality, and educational consistency of QRU characters across all products and generations.",
         related=["STD-00003"], agents=["Kingdom Lion™", "Legacy Eagle™", "Royal Phoenix™"],
         refs=["character_registry.py", "/api/wis"]),
    _std("STD-00007", "QRU Teaching Methodology™ (11-part)", "Educational Methodologies™",
         "The 11-part understanding structure: The Question, Simple Answer, Why It Matters, Real-World Example, QRU Translation™, Everyday Analogy, Memory Sentence™, Practice, Key Vocabulary, Deep Roots™, Verification Status.",
         "Make complex truth understandable without simplifying the truth itself.",
         related=["STD-00004"], agents=["Translation Engine™"],
         refs=["Knowledge Records™ structure"]),
    _std("STD-00008", "Verification Principles™ (Kingdom Lion™)", "Verification Principles™",
         "Every published statement must be accurate and evidence-based. Reviews weigh evidence, sources, confidence, and conflicting evidence; escalate true exceptions only.",
         "Protect QRU's credibility — understanding is worthless if it is wrong.",
         related=["STD-00001"], agents=["Kingdom Lion™", "AI Verification Team™"],
         refs=["verification_engine.py"]),
    _std("STD-00009", "Manufacturing Recipes™", "Product Recipes™",
         "Reusable recipes (44+ product types) defining required Knowledge Record fields, stages, and deliverables for each product.",
         "Assemble products from verified fields consistently — research once, manufacture forever.",
         related=["STD-00010"], agents=["Manufacturing Director™"],
         refs=["product_automation.py", "manufacturing2.py"]),
    _std("STD-00010", "The QRU Thinking Model™ (8-point)", "Manufacturing Principles™",
         "Every product must be True, Understandable, Useful, Complete, Beautiful, Memorable, On-brand, and Treasure Standard™.",
         "A single mental checklist that encodes QRU quality into every AI generation prompt.",
         related=["STD-00001"], agents=["Product Manufacturer™"],
         refs=["The QRU Mind™ prompts"]),
    _std("STD-00011", "Hands-Free Manufacturing™ / Automation Rules™", "Automation Rules™",
         "The Orchestrator auto-advances Manufacture → Verify → QC → Treasure Standard → Publish; the Founder governs, AI manufactures.",
         "Scale production while keeping the Founder in control of exceptions only.",
         related=["STD-00009"], agents=["Orchestration Director™"],
         refs=["orchestrator.py", "workflow_engine.py"]),
    _std("STD-00012", "Multi-Format Output™ Standards", "Publishing Standards™",
         "10 branded renditions (KDP eBook/Print, Etsy, TpT, Poster @300dpi, Social, Pinterest, Web, Banner), each preserving the QRU frame.",
         "Publish one verified product to every platform without losing brand fidelity.",
         related=["STD-00003"], agents=["Media Producer™"],
         refs=["design_language.export_formats"]),
    _std("STD-00013", "Software Architecture™ (Modular Routers)", "Software Architecture™",
         "FastAPI with modular routers under /api, Bearer JWT auth with role dependency, React + Tailwind + shadcn/ui frontend using REACT_APP_BACKEND_URL.",
         "Keep the platform scalable, testable, and production-ready.",
         related=["STD-00014"], agents=["Software Architect™"],
         refs=["server.py", "routers/"]),
    _std("STD-00014", "Database Architecture™ (MongoDB)", "Database Architecture™",
         "MongoDB via motor; documents never return raw ObjectId; datetimes use timezone-aware UTC ISO strings.",
         "Reliable, JSON-safe persistence across the enterprise.",
         related=["STD-00013"], agents=["Software Architect™"],
         refs=["database.py"]),
    _std("STD-00015", "Extend Before Expand™", "Leadership Principles™",
         "Prefer extending existing capabilities over creating new departments. Bias to elegant simplicity; new departments must pass the One Question Test™.",
         "Prevent sprawl and keep the enterprise coherent as it grows.",
         related=["STD-00002"], agents=["Organizational Health Director™"],
         refs=["evolution.py"]),
    _std("STD-00016", "QRU Design Language™ / Creative Standards™", "Creative Standards™",
         "Deterministic premium covers (Pillow), a 15-palette Dynamic Color System™, and a Design Library™ that learns from every certified product.",
         "Compound design quality so every product is more beautiful than the last.",
         related=["STD-00003"], agents=["Design Intelligence™", "Creative Studio Director™"],
         refs=["design_language.py", "design_intelligence.py"]),
]

SEED_LESSONS = [
    {"id": "LES-00001", "title": "Degrade gracefully on LLM daily spend cap",
     "division": "Software Engineering", "category": "Lessons Learned™",
     "lesson": "The Emergent LLM key has a hard DAILY spend cap separate from balance. Endpoints must fail fast on hard limits and return deterministic branded data so the UI never crashes; batches pause instead of burning failed jobs.",
     "date": "2026-07-03", "source": "Iteration 15", "founder_approval": True, "created_at": _now()},
    {"id": "LES-00002", "title": "Server-side pricing for commerce",
     "division": "Finance", "category": "Lessons Learned™",
     "lesson": "The client must never send payment amounts. A server-side PRICE_TIERS catalog is the single source of truth for Stripe Checkout.",
     "date": "2026-07-03", "source": "Iteration 14", "founder_approval": True, "created_at": _now()},
    {"id": "LES-00003", "title": "Cap parallel manufacturing concurrency",
     "division": "Manufacturing", "category": "Lessons Learned™",
     "lesson": "Reducing parallel manufacturing concurrency from 4 to 2 eliminated transient 503 rate-limit bursts during heavy runs. Quality/reliability over raw speed.",
     "date": "2026-07-03", "source": "Iteration 15", "founder_approval": True, "created_at": _now()},
]


async def seed_qiks():
    for s in SEED_STANDARDS:
        if not await STD_COL.find_one({"id": s["id"]}):
            await STD_COL.insert_one({**s})
    for l in SEED_LESSONS:
        if not await LESSON_COL.find_one({"id": l["id"]}):
            await LESSON_COL.insert_one({**l})


def _clean(d):
    if d:
        d.pop("_id", None)
    return d


async def list_standards(category=None, status=None, q=None):
    query = {}
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    out = []
    async for d in STD_COL.find(query).sort("id", 1):
        d = _clean(d)
        if q:
            hay = " ".join([d["name"], d["description"], d["purpose"], d["category"], d["standard_id"]]).lower()
            if q.lower() not in hay:
                continue
        out.append(d)
    return out


async def get_standard(sid):
    return _clean(await STD_COL.find_one({"id": sid}))


async def next_id():
    n = await STD_COL.count_documents({})
    return f"STD-{n + 1:05d}"


async def create_standard(name, category, description, purpose, reviewer):
    sid = await next_id()
    doc = _std(sid, name, category, description, purpose, impl="Planned")
    # New submissions START as a Working Idea (not auto-approved).
    doc.update({
        "status": "Draft", "founder_approval": False,
        "promotion_stage": "Working Idea",
        "change_history": [{"version": "0.1", "date": _now()[:10],
                            "reason": "Submitted as a working idea.", "reviewer": reviewer, "founder_approval": False}],
    })
    await STD_COL.insert_one({**doc})
    return _clean(doc)


async def promote_standard(sid, reviewer, founder_approval=False):
    s = await get_standard(sid)
    if not s:
        return None
    cur = s.get("promotion_stage", "Working Idea")
    idx = PROMOTION_STAGES.index(cur) if cur in PROMOTION_STAGES else 0
    new_stage = PROMOTION_STAGES[min(idx + 1, len(PROMOTION_STAGES) - 1)]
    updates = {"promotion_stage": new_stage, "updated_at": _now()}
    if new_stage in ("Founder Approval", "QRU Standard™"):
        updates["founder_approval"] = founder_approval
    if new_stage == "QRU Standard™":
        updates["status"] = "Active"
    entry = {"version": s["version"], "date": _now()[:10],
             "reason": f"Promoted to {new_stage}.", "reviewer": reviewer, "founder_approval": founder_approval}
    await STD_COL.update_one({"id": sid}, {"$set": updates, "$push": {"change_history": entry}})
    return await get_standard(sid)


async def revise_standard(sid, changes, reason, reviewer, founder_approval=True):
    """Version governance: never overwrite. Archive the current version, bump, keep history."""
    s = await get_standard(sid)
    if not s:
        return None
    old_snapshot = {"version": s["version"], "name": s["name"], "description": s["description"],
                    "purpose": s["purpose"], "archived_at": _now()}
    major, minor = s["version"].split(".")
    new_version = f"{major}.{int(minor) + 1}"
    entry = {"version": new_version, "date": _now()[:10], "reason": reason,
             "reviewer": reviewer, "founder_approval": founder_approval}
    allowed = {k: v for k, v in changes.items() if k in ("name", "description", "purpose", "status", "implementation_status", "related_standards")}
    allowed.update({"version": new_version, "updated_at": _now()})
    await STD_COL.update_one(
        {"id": sid},
        {"$set": allowed, "$push": {"change_history": entry, "superseded_versions": old_snapshot}},
    )
    return await get_standard(sid)


async def list_lessons(division=None):
    query = {"division": division} if division else {}
    out = []
    async for d in LESSON_COL.find(query).sort("id", 1):
        out.append(_clean(d))
    return out


async def add_lesson(title, division, lesson, source, reviewer):
    n = await LESSON_COL.count_documents({})
    doc = {"id": f"LES-{n + 1:05d}", "title": title, "division": division,
           "category": "Lessons Learned™", "lesson": lesson, "date": _now()[:10],
           "source": source, "reviewer": reviewer, "founder_approval": False, "created_at": _now()}
    await LESSON_COL.insert_one({**doc})
    return _clean(doc)


async def knowledge_graph():
    """Nodes = standards; edges = related_standards + graph_links."""
    nodes, edges = [], []
    standards = await list_standards()
    ids = {s["id"] for s in standards}
    for s in standards:
        nodes.append({"id": s["id"], "label": s["name"], "category": s["category"], "status": s["status"]})
        for r in s.get("related_standards", []):
            if r in ids:
                edges.append({"from": s["id"], "to": r, "relation": "related"})
        for gl in s.get("graph_links", []):
            if gl.get("to") in ids:
                edges.append({"from": s["id"], "to": gl["to"], "relation": gl.get("relation", "linked")})
    return {"nodes": nodes, "edges": edges}


async def dashboard():
    standards = await list_standards()
    lessons = await list_lessons()
    by_cat = {}
    for s in standards:
        by_cat[s["category"]] = by_cat.get(s["category"], 0) + 1
    active = [s for s in standards if s["status"] == "Active"]
    awaiting = [s for s in standards if not s.get("founder_approval")]
    recipes = [s for s in standards if s["category"] == "Product Recipes™"]
    methodologies = [s for s in standards if s["category"] == "Educational Methodologies™"]
    frameworks = [s for s in standards if s["category"] in ("Enterprise Standards™", "Manufacturing Principles™", "Leadership Principles™")]
    total_versions = sum(len(s.get("change_history", [])) for s in standards)
    # Institutional Health™: share of standards that are Founder-approved & implemented.
    implemented = [s for s in standards if s.get("implementation_status") == "Implemented"]
    health = round(100 * len([s for s in active if s.get("founder_approval")]) / max(1, len(standards)))
    return {
        "standards": len(standards),
        "frameworks": len(frameworks),
        "methodologies": len(methodologies),
        "recipes": len(recipes),
        "character_assets": 6,
        "lessons_learned": len(lessons),
        "ideas_awaiting_review": len(awaiting),
        "standards_updated_this_month": total_versions,
        "knowledge_growth": len(standards) + len(lessons),
        "institutional_health": health,
        "by_category": by_cat,
        "categories": CATEGORIES,
        "promotion_stages": PROMOTION_STAGES,
        "divisions": DIVISIONS,
        "implemented": len(implemented),
    }
