"""QRU Enterprise Architecture Foundation (STD-EIP-0002 — Enterprise Foundation Sprint A™).

The permanent architectural bedrock every future capability inherits: 8 Factory Domains + Domain
Registry™, 7 Enterprise Layers, 6 user Intentions (with Simple/Standard/Enterprise views), the
Architecture Explorer™ catalog, and the Why-Am-I-Here™ / Manufacturing GPS™ intelligence content.
Every module belongs to exactly one Domain and one Layer (constitutional acceptance criterion).
Governed by STD-EIP-0002 + STD-EIP-0001 + STD-MFG-0001 + QRU-CON-0001.
"""
from database import db
from models import gen_id, now_iso

DOC_ID = "STD-EIP-0002"
VERSION = "1.0"
EFFECTIVE = "2026-07-12"

DOMAINS = [
    {"id": "discovery", "name": "Discovery Domain™", "purpose": "Discover questions, opportunities, evidence and trends before manufacturing.", "output": "Approved opportunity / research request."},
    {"id": "knowledge", "name": "Knowledge Domain™", "purpose": "Create, verify, govern, relate and preserve enterprise knowledge.", "output": "Verified Knowledge Record eligible for production."},
    {"id": "manufacturing", "name": "Manufacturing Domain™", "purpose": "Transform approved knowledge into structured product artifacts.", "output": "Structured product artifact for design & QA."},
    {"id": "design_experience", "name": "Design & Experience Domain™", "purpose": "Turn artifacts into understandable, premium, accessible experiences.", "output": "Treasure-Standard-ready designed product."},
    {"id": "quality_governance", "name": "Quality & Governance Domain™", "purpose": "Verify quality, compliance, authenticity, safety and readiness.", "output": "Gold Master, revision order, block, or authorized exception."},
    {"id": "publishing_distribution", "name": "Publishing & Distribution Domain™", "purpose": "Publish, distribute, maintain and track products across channels.", "output": "Released product with traceable channel & record."},
    {"id": "learning_human_dev", "name": "Learning & Human Development Domain™", "purpose": "Measure and improve learner understanding, application and capability.", "output": "Evidence of understanding, application and growth."},
    {"id": "enterprise_operations", "name": "Enterprise Operations Domain™", "purpose": "Operate, observe, secure, administer and improve the Factory.", "output": "Reliable, observable, governed operation."},
]
_DOMAIN_IDS = {d["id"] for d in DOMAINS}

LAYERS = [
    {"id": "mission", "n": 1, "name": "Mission & Philosophy™"},
    {"id": "governance", "n": 2, "name": "Governance & Constitution™"},
    {"id": "intelligence", "n": 3, "name": "Enterprise Intelligence™"},
    {"id": "manufacturing", "n": 4, "name": "Manufacturing™"},
    {"id": "experience", "n": 5, "name": "Experience™"},
    {"id": "distribution", "n": 6, "name": "Distribution & Ecosystem™"},
    {"id": "measurement", "n": 7, "name": "Measurement & Evolution™"},
]

INTENTIONS = [
    {"id": "discover", "name": "Discover™", "desc": "Find questions, opportunities and evidence."},
    {"id": "plan", "name": "Plan™", "desc": "Shape the work before manufacturing begins."},
    {"id": "build", "name": "Build™", "desc": "Manufacture knowledge and products."},
    {"id": "launch", "name": "Launch™", "desc": "Certify, publish and distribute."},
    {"id": "improve", "name": "Improve™", "desc": "Measure, learn and evolve."},
    {"id": "learn", "name": "Learn™", "desc": "Understand the Factory and grow capability."},
]

# route, name, domain, layer, intention, view (simple exposes only 'core')
_M = [
    ("/create", "Create™", "manufacturing", "experience", "build", "core"),
    ("/concierge", "Factory Concierge™", "design_experience", "experience", "plan", "core"),
    ("/flow", "Manufacturing Flow™", "quality_governance", "intelligence", "build", "core"),
    ("/projects", "My Projects", "manufacturing", "manufacturing", "build", "core"),
    ("/architecture", "Architecture Explorer™", "enterprise_operations", "intelligence", "learn", "core"),
    ("/constitution", "Factory Constitution™", "quality_governance", "governance", "learn", "std"),
    ("/publishing", "Publishing Standard™", "design_experience", "governance", "build", "std"),
    ("/cover-studio", "Cover Studio™", "design_experience", "experience", "build", "std"),
    ("/first-dollar", "First Dollar Mode™", "enterprise_operations", "mission", "plan", "std"),
    ("/factory-readiness", "Factory Readiness™", "quality_governance", "governance", "plan", "std"),
    ("/manufacturing-economics", "Manufacturing Economics™", "enterprise_operations", "measurement", "plan", "std"),
    ("/teach", "What to Teach Today", "discovery", "intelligence", "discover", "std"),
    ("/workflows", "Workflow Engine™", "manufacturing", "manufacturing", "build", "std"),
    ("/factory-monitor", "Factory Monitor™", "enterprise_operations", "measurement", "improve", "ent"),
    ("/failure-intelligence", "Failure Intelligence™", "enterprise_operations", "measurement", "improve", "ent"),
    ("/autonomy", "Autonomy Center™", "discovery", "intelligence", "discover", "ent"),
    ("/enterprise-autonomy", "Continuous Improvement™", "learning_human_dev", "measurement", "improve", "std"),
    ("/command-center", "Enterprise Command Center™", "enterprise_operations", "intelligence", "improve", "ent"),
    ("/governance", "Governance Center™", "quality_governance", "governance", "learn", "ent"),
    ("/blueprint", "Enterprise Blueprint™", "enterprise_operations", "intelligence", "plan", "ent"),
    ("/wis", "Character Library™", "design_experience", "experience", "build", "ent"),
    ("/qiks", "Institutional Knowledge™", "knowledge", "intelligence", "learn", "std"),
    ("/", "Founder Console", "enterprise_operations", "intelligence", "improve", "core"),
    ("/evidence", "Evidence Dashboard™", "discovery", "measurement", "discover", "std"),
    ("/mfg-command", "Manufacturing Command™", "manufacturing", "manufacturing", "build", "ent"),
    ("/inspection", "Quality Gates™", "quality_governance", "governance", "launch", "std"),
    ("/director", "Manufacturing Director™", "quality_governance", "governance", "launch", "ent"),
    ("/agents", "Factory Agents™", "enterprise_operations", "intelligence", "improve", "ent"),
    ("/kr2", "Knowledge Architecture™", "knowledge", "intelligence", "build", "std"),
    ("/command", "Command Console", "enterprise_operations", "intelligence", "improve", "ent"),
    ("/enterprise-health", "Enterprise Health", "enterprise_operations", "measurement", "improve", "std"),
    ("/organization", "Organization", "enterprise_operations", "governance", "improve", "ent"),
    ("/knowledge", "Knowledge Records", "knowledge", "intelligence", "build", "core"),
    ("/topic-registry", "Topic Registry™", "knowledge", "intelligence", "build", "std"),
    ("/promotion-pipeline", "Promotion Pipeline™", "knowledge", "intelligence", "build", "std"),
    ("/library-import", "Bulk Library Import™", "knowledge", "intelligence", "build", "ent"),
    ("/translation-engine", "Translation Engine™", "knowledge", "manufacturing", "build", "ent"),
    ("/research", "Research Center", "discovery", "intelligence", "discover", "std"),
    ("/verification", "Verification Center", "knowledge", "governance", "build", "std"),
    ("/verification-team", "Verification Team™", "knowledge", "governance", "build", "ent"),
    ("/memory-engineering", "Memory Engineering™", "knowledge", "intelligence", "improve", "ent"),
    ("/manufacturing", "Manufacturing Orders", "manufacturing", "manufacturing", "build", "std"),
    ("/orchestrator", "Bulk Orchestrator™", "manufacturing", "manufacturing", "build", "ent"),
    ("/manufacture", "Product Manufacturing", "manufacturing", "manufacturing", "build", "core"),
    ("/manufacturing-studio", "Manufacturing Studio", "manufacturing", "manufacturing", "build", "std"),
    ("/products", "Product Library", "manufacturing", "manufacturing", "build", "std"),
    ("/product-protection", "Product Protection™", "quality_governance", "governance", "launch", "ent"),
    ("/trust", "Trust & Authenticity™", "quality_governance", "governance", "launch", "ent"),
    ("/companion", "Companion System™", "design_experience", "experience", "launch", "ent"),
    ("/creative-studio", "Creative Studio™", "design_experience", "experience", "build", "std"),
    ("/asset-vault", "Asset Vault™", "design_experience", "manufacturing", "build", "std"),
    ("/media-studio", "Media Studio™", "design_experience", "experience", "build", "std"),
    ("/media-starter-kit", "Media Starter Kit™", "design_experience", "experience", "build", "ent"),
    ("/visual-studio", "Visual & Media Studio™", "design_experience", "experience", "build", "ent"),
    ("/media-library", "Stock Media Library™", "design_experience", "manufacturing", "build", "std"),
    ("/flagship-showcase", "Flagship Showcase™", "design_experience", "experience", "build", "core"),
    ("/design-intelligence", "Design Intelligence™", "design_experience", "experience", "build", "std"),
    ("/design-director", "Design Director™", "design_experience", "governance", "build", "ent"),
    ("/factory-health", "Factory Health™", "enterprise_operations", "measurement", "improve", "std"),
    ("/founder-inbox", "Founder Review Inbox™", "quality_governance", "governance", "launch", "core"),
    ("/experience-lab", "Experience Lab™", "learning_human_dev", "measurement", "learn", "std"),
    ("/workforce", "Digital Workforce", "enterprise_operations", "intelligence", "improve", "ent"),
    ("/colleges", "Understanding Colleges", "learning_human_dev", "measurement", "learn", "std"),
    ("/analytics", "Analytics", "learning_human_dev", "measurement", "improve", "std"),
    ("/customers", "Customers", "publishing_distribution", "distribution", "launch", "std"),
    ("/store", "QRU Store™", "publishing_distribution", "distribution", "launch", "std"),
    ("/connectors", "Publishing Connectors™", "publishing_distribution", "distribution", "launch", "std"),
    ("/youtube", "YouTube Publisher™", "publishing_distribution", "distribution", "launch", "std"),
    ("/distribution", "Distribution Center™", "publishing_distribution", "distribution", "launch", "core"),
    ("/integration-hub", "Integration Hub™", "enterprise_operations", "distribution", "improve", "ent"),
    ("/ai-services", "AI Services™", "enterprise_operations", "intelligence", "improve", "ent"),
    ("/users", "User Management", "enterprise_operations", "governance", "improve", "ent"),
    ("/portability", "Portability Center™", "publishing_distribution", "distribution", "improve", "ent"),
    ("/engineering-console", "Engineering Console", "enterprise_operations", "governance", "improve", "ent"),
    ("/settings", "Settings", "enterprise_operations", "governance", "improve", "std"),
]

_STANDARD_BY_DOMAIN = {
    "knowledge": ["QRU-CON-0001 §3.1", "KR Master Spec"],
    "design_experience": ["QRU-CON-0002"],
    "quality_governance": ["QRU-CON-0001 §9/§10", "QRU-CON-0002 Pre-Ship Gate"],
    "manufacturing": ["STD-MFG-0001", "QRU-CON-0002"],
    "publishing_distribution": ["QRU-CON-0001 §4"],
    "discovery": ["QRU-CON-0001 §7"],
    "learning_human_dev": ["STD-EIP-0001"],
    "enterprise_operations": ["STD-MFG-0001", "STD-EIP-0002"],
}


def _module(route, name, domain, layer, intention, view):
    return {
        "route": route, "name": name, "domain": domain, "layer": layer, "intention": intention, "view": view,
        "domain_name": next(d["name"] for d in DOMAINS if d["id"] == domain),
        "layer_name": next(l["name"] for l in LAYERS if l["id"] == layer),
        "standards": _STANDARD_BY_DOMAIN.get(domain, ["QRU-CON-0001"]),
        "mission_contribution": _mission_contrib(intention),
        "treasure_contribution": "Every output passes the Treasure Standard™ before release.",
        "human_capability_contribution": _capability_contrib(domain),
    }


def _mission_contrib(intention):
    return {
        "discover": "Surfaces what is worth understanding before effort is spent.",
        "plan": "Turns intent into a governed, resourced plan.",
        "build": "Manufactures verified understanding into durable products.",
        "launch": "Delivers understanding to people, with traceable trust.",
        "improve": "Feeds real outcomes back so the Factory keeps getting better.",
        "learn": "Grows the operator's mastery of the enterprise itself.",
    }[intention]


def _capability_contrib(domain):
    return {
        "knowledge": "Builds an evidence-based, verifiable knowledge base humans can trust.",
        "design_experience": "Makes understanding effortless and premium to consume.",
        "quality_governance": "Preserves human judgment as the final authority.",
        "learning_human_dev": "Measures and increases genuine human understanding.",
    }.get(domain, "Reduces operator effort while keeping humans in control.")


MODULES = [_module(*m) for m in _M]
_BY_ROUTE = {m["route"]: m for m in MODULES}

# ---- Why-Am-I-Here™ content, keyed by intention (page-level default) ----
WHY = {
    "build": {"why": "You are manufacturing verified knowledge into a product.",
              "objective": "Produce a draft that meets the Publishing Standard™.",
              "success": "The artifact passes the Treasure Standard™ Pre-Ship Gate.",
              "next": "Quality Gates™ → Founder approval → Gold Master™.",
              "common_questions": ["Do I need a verified Knowledge Record first?", "Which recipe applies?"],
              "common_mistakes": ["Manufacturing before the KR is verified", "Skipping design tokens"]},
    "plan": {"why": "You are shaping the work before manufacturing begins.",
             "objective": "Confirm outcome, knowledge dependency and the production blueprint.",
             "success": "A governed plan + tracked project exist.",
             "next": "Build™ — manufacture the Knowledge Record / product.",
             "common_questions": ["What will this cost in time?", "Is the knowledge ready?"],
             "common_mistakes": ["Planning a product with no verified knowledge"]},
    "discover": {"why": "You are finding what is worth understanding.",
                 "objective": "Capture an opportunity, question or evidence.",
                 "success": "An approved opportunity or research request is created.",
                 "next": "Plan™ — turn the opportunity into a blueprint.",
                 "common_questions": ["Is there evidence for this?"], "common_mistakes": ["Jumping to manufacturing"]},
    "launch": {"why": "You are certifying and delivering a finished product.",
               "objective": "Certify the Gold Master and publish to approved channels.",
               "success": "Released product with a traceable publication record.",
               "next": "Improve™ — measure outcomes and feed learning back.",
               "common_questions": ["Is a connector set up?"], "common_mistakes": ["Publishing before Gold Master approval"]},
    "improve": {"why": "You are turning outcomes into a better Factory.",
                "objective": "Review metrics, capture lessons, approve improvements.",
                "success": "Approved improvements enter the Innovation Observatory™.",
                "next": "Discover™ — the loop continues.",
                "common_questions": ["What should become a new standard?"], "common_mistakes": ["Losing lessons learned"]},
    "learn": {"why": "You are building mastery of the Factory itself.",
              "objective": "Understand how domains, standards and workflows connect.",
              "success": "You can navigate and explain the enterprise architecture.",
              "next": "Apply it — return to Build™ or Plan™ with more capability.",
              "common_questions": ["Which domain owns this?"], "common_mistakes": ["Treating modules as isolated tools"]},
}


def why_am_i_here(route):
    m = _BY_ROUTE.get(route)
    intention = m["intention"] if m else "build"
    base = WHY.get(intention, WHY["build"])
    related = [x["name"] for x in MODULES if m and x["domain"] == m["domain"] and x["route"] != route][:5]
    return {"route": route, "module": (m or {}).get("name"), "domain": (m or {}).get("domain_name"),
            "layer": (m or {}).get("layer_name"), "standards": (m or {}).get("standards", []),
            "related_modules": related, "concierge_shortcut": "/concierge", **base}


def domains_view():
    counts = {}
    for m in MODULES:
        counts[m["domain"]] = counts.get(m["domain"], 0) + 1
    return {"domains": [{**d, "module_count": counts.get(d["id"], 0)} for d in DOMAINS]}


def layers_view():
    counts = {}
    for m in MODULES:
        counts[m["layer"]] = counts.get(m["layer"], 0) + 1
    return {"layers": [{**l, "module_count": counts.get(l["id"], 0)} for l in LAYERS]}


def intentions_view(view="ent"):
    order = {"simple": ["core"], "std": ["core", "std"], "ent": ["core", "std", "ent"]}
    allow = order.get(view, order["ent"])
    out = []
    for it in INTENTIONS:
        mods = [m for m in MODULES if m["intention"] == it["id"] and m["view"] in allow]
        out.append({**it, "modules": mods})
    return {"view": view, "intentions": out}


def explorer(route):
    m = _BY_ROUTE.get(route)
    if not m:
        return None
    siblings = [x for x in MODULES if x["domain"] == m["domain"] and x["route"] != route]
    return {**m, "why": why_am_i_here(route),
            "related_in_domain": [{"route": s["route"], "name": s["name"]} for s in siblings][:8],
            "governed_by": [DOC_ID] + m["standards"]}


async def seed_eip():
    if not await db.factory_constitution.find_one({"doc_id": DOC_ID, "version": VERSION}):
        await db.factory_constitution.insert_one({
            "id": gen_id(), "doc_id": DOC_ID, "name": "QRU Enterprise Foundation Sprint A™",
            "version": VERSION, "status": "Founder Approved", "authority_level": "Foundational",
            "effective_date": EFFECTIVE, "owner": "QRU", "read_only": True,
            "domains": DOMAINS, "layers": LAYERS, "intentions": INTENTIONS,
            "created_at": now_iso(), "updated_at": now_iso()})
    if not await db.qiks_standards.find_one({"standard_id": DOC_ID}):
        await db.qiks_standards.insert_one({
            "id": gen_id(), "standard_id": DOC_ID, "name": "QRU Enterprise Foundation Sprint A™",
            "category": "Enterprise Architecture", "status": "Active", "version": VERSION, "date_adopted": EFFECTIVE,
            "founder_approval": True, "description": "8 Domains, 7 Layers, 6 Intentions, Architecture Explorer, Manufacturing GPS, Why-Am-I-Here.",
            "purpose": "Every module belongs to a governed domain & layer; every page explains itself and knows its location.",
            "related_standards": ["QRU-CON-0001", "QRU-CON-0002", "STD-MFG-0001", "STD-EIP-0001"], "related_products": ["all"], "created_at": now_iso()})
    await db.constitutional_registry.update_one(
        {"id": DOC_ID}, {"$setOnInsert": {"id": DOC_ID, "name": "Enterprise Foundation Sprint A™", "version": VERSION,
                                          "owner": "QRU", "category": "Enterprise Architecture",
                                          "implementation_status": "Production", "verification_status": "Verified",
                                          "created_at": now_iso()}}, upsert=True)
