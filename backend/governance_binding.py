"""QRU Governance Binding Layer™ (MO-008) — turns institutional standards into the ACTIVE
operating rules of the factory. Closes the governance loop:

    Standards → Processes → Agents → Outputs → Verification → Published Products

Every manufacturing stage has a Responsible Agent and a Governing Standard (a QIKS founding
document). Traceability is surfaced everywhere via a "Governed by" record. Treasure Standard™:
if a governing standard is not yet adopted, we say so honestly (never fake compliance).
"""
import logging
from database import db
import qiks

logger = logging.getLogger("qru.governance")

# ------------------------------------------------------------------ AGENT REGISTRY
# Each factory agent is a governed member of the operating system, bound to a founding standard.
AGENTS = [
    {"id": "knowledge_architect", "name": "Knowledge Architect™", "role": "Builds Knowledge Record structures",
     "mandate": "Preserve knowledge integrity", "governed_by": "KR Master Specification", "system": "Knowledge"},
    {"id": "verification_lion", "name": "Verification Lion™", "role": "Truth verification",
     "mandate": "Prevent unsupported claims", "governed_by": "Intelligence Governance Charter", "system": "Verification"},
    {"id": "manufacturing_director", "name": "Manufacturing Director™", "role": "Controls production flow",
     "mandate": "Protect factory standards", "governed_by": "Factory Operations Blueprint", "system": "Manufacturing"},
    {"id": "assembly_master", "name": "Assembly Master™", "role": "Assembles finished products",
     "mandate": "Every product is customer-ready", "governed_by": "Product Assembly Blueprint", "system": "Assembly"},
    {"id": "design_director", "name": "Design Director™", "role": "Protects experience quality",
     "mandate": "Maintain visual & experience standards", "governed_by": "QRU Experience Design Architecture", "system": "Design"},
    {"id": "research_analyst", "name": "Trend Fox™", "role": "Market & research intelligence",
     "mandate": "Detect opportunities from verified signals", "governed_by": "Research Intelligence", "system": "Research"},
    {"id": "distribution_director", "name": "Distribution Director™", "role": "Publishes & delivers everywhere",
     "mandate": "Manufacture once, publish everywhere — verified", "governed_by": "Factory Operations Blueprint", "system": "Distribution"},
    {"id": "visual_director", "name": "Visual Intelligence Director™", "role": "Owns product visual strategy",
     "mandate": "Make understanding visible, memorable & premium", "governed_by": "QRU Visual Intelligence Studio", "system": "Visual"},
    {"id": "layout_agent", "name": "Layout Intelligence Agent™", "role": "Composes page rhythm & hierarchy",
     "mandate": "Every page earns its place; no rendering failures", "governed_by": "QRU Visual Intelligence Studio", "system": "Visual"},
    {"id": "neurodesign_reviewer", "name": "NeuroDesign Reviewer™", "role": "Protects learnability",
     "mandate": "Design for the brain — reduce cognitive friction", "governed_by": "QRU Visual Intelligence Studio", "system": "Visual"},
    {"id": "gold_reviewer", "name": "Gold Standard Experience Reviewer™", "role": "Final experiential approval",
     "mandate": "Only Gold Standard experiences ship", "governed_by": "QRU Visual Intelligence Studio", "system": "Visual"},
    {"id": "kingdom_lion", "name": "Kingdom Lion™", "role": "Institutional governance",
     "mandate": "Only approved knowledge enters the permanent registry", "governed_by": "Standard Registry", "system": "Governance"},
]

# ------------------------------------------------------------------ MANUFACTURING STAGE BINDINGS
# The governed manufacturing lifecycle: stage → responsible agent → governing standard → verification.
STAGE_BINDINGS = [
    {"stage": "Knowledge Manufacturing", "agent": "Knowledge Architect™", "standard": "KR Master Specification", "verification": "Verification Lion™"},
    {"stage": "Research Intelligence", "agent": "Trend Fox™", "standard": "Research Intelligence", "verification": "Verification Lion™"},
    {"stage": "Verification", "agent": "Verification Lion™", "standard": "Intelligence Governance Charter", "verification": "Verification Lion™"},
    {"stage": "Visual Intelligence & Layout", "agent": "Visual Intelligence Director™", "standard": "QRU Visual Intelligence Studio", "verification": "Gold Standard Experience Reviewer™"},
    {"stage": "Product Assembly", "agent": "Assembly Master™", "standard": "Product Assembly Blueprint", "verification": "Manufacturing Director™"},
    {"stage": "Quality Control", "agent": "Manufacturing Director™", "standard": "Factory Operations Blueprint", "verification": "Verification Lion™"},
    {"stage": "Design & Rendering", "agent": "Design Director™", "standard": "QRU Experience Design Architecture", "verification": "Design Director™"},
    {"stage": "Distribution", "agent": "Distribution Director™", "standard": "Factory Operations Blueprint", "verification": "Distribution Director™"},
]

# Overall pipeline governed by the Methodology Manual.
PIPELINE_STANDARD = "Methodology Manual"

# Design decisions bound to the Experience Design Architecture standard (Phase 3).
DESIGN_BINDINGS = [
    {"decision": "Deep Navy foundation", "purpose": "Trust, structure, institutional authority"},
    {"decision": "QRU Gold accent", "purpose": "Signal verified excellence; premium recognition & emotional connection"},
    {"decision": "Royal Purple signature accent (sparing)", "purpose": "Discovery & distinction without overpowering trust"},
    {"decision": "Playfair Display headings + Manrope body", "purpose": "Museum-quality authority with maximum readability"},
    {"decision": "Treasure Standard™ badges & QRU Shield", "purpose": "Make verification and provenance visible in the product"},
]

# KR Master Specification enforcement is the #1 priority (atomic building block of the factory).
ENFORCEMENT_PRIORITY = [
    "KR Master Specification", "Factory Operations Blueprint", "Intelligence Governance Charter",
    "Product Assembly Blueprint", "QRU Experience Design Architecture",
]


async def _standard_index():
    """name (lowered) -> {standard_id, id, name, status} from QIKS founding standards."""
    idx = {}
    async for s in qiks.STD_COL.find({}, {"name": 1, "standard_id": 1, "id": 1, "status": 1, "category": 1}):
        idx[(s.get("name") or "").lower()] = {
            "standard_id": s.get("standard_id"), "id": s.get("id"), "name": s.get("name"),
            "status": s.get("status"), "category": s.get("category")}
    return idx


def _resolve(idx, name):
    s = idx.get((name or "").lower())
    if s:
        return {**s, "adopted": True}
    return {"standard_id": None, "id": None, "name": name, "status": "Not Adopted", "adopted": False}


async def agents():
    idx = await _standard_index()
    return [{**a, "standard": _resolve(idx, a["governed_by"])} for a in AGENTS]


async def design_governance():
    idx = await _standard_index()
    return {"standard": _resolve(idx, "QRU Experience Design Architecture"),
            "applies_to": ["MO-004 Design System", "Design Director™ decisions", "Product rendering pipeline"],
            "decisions": DESIGN_BINDINGS}


async def manufacturing_compliance(order):
    """Build the QRU Manufacturing Compliance Record™ for one order:
    stage → responsible agent → governing standard → verification authority → status."""
    idx = await _standard_index()
    kr_code = None
    if order.get("knowledge_record_id"):
        kr = await db.knowledge_records.find_one({"id": order["knowledge_record_id"]}, {"kr_code": 1})
        kr_code = (kr or {}).get("kr_code")
    stages = []
    for b in STAGE_BINDINGS:
        std = _resolve(idx, b["standard"])
        stages.append({
            "stage": b["stage"], "agent": b["agent"], "verification": b["verification"],
            "governing_standard": std,
            "status": "Treasure Standard™ Pending" if not std["adopted"] else "Governed",
        })
    return {
        "order_id": order.get("id"), "mo_code": order.get("mo_code"), "topic": order.get("topic"),
        "kr_code": kr_code, "current_status": order.get("status"),
        "pipeline_standard": _resolve(idx, PIPELINE_STANDARD),
        "stages": stages,
    }


async def governed_by(entity_type):
    """Return the governing-standard chips for a given entity type (for the visible 'Governed by' strip)."""
    idx = await _standard_index()
    mapping = {
        "knowledge_record": ["KR Master Specification"],
        "product": ["Product Assembly Blueprint", "QRU Experience Design Architecture"],
        "manufacturing_order": [PIPELINE_STANDARD, "Factory Operations Blueprint"],
        "command_center": [PIPELINE_STANDARD, "Factory Operations Blueprint", "Standard Registry"],
        "design": ["QRU Experience Design Architecture"],
        "distribution": ["Factory Operations Blueprint"],
    }
    return [_resolve(idx, n) for n in mapping.get(entity_type, [])]


async def overview():
    idx = await _standard_index()
    adopted = [s for s in idx.values() if s.get("status") == "Active"]
    priority = [_resolve(idx, n) for n in ENFORCEMENT_PRIORITY]
    bound = sum(1 for p in priority if p["adopted"])
    return {
        "total_standards": len(idx),
        "agents": len(AGENTS),
        "manufacturing_stages": len(STAGE_BINDINGS),
        "enforcement_priority": priority,
        "priority_bound": bound,
        "priority_total": len(priority),
        "loop": ["Standards", "Processes", "Agents", "Outputs", "Verification", "Published Products"],
    }
