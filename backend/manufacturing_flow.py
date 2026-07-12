"""QRU Universal Manufacturing Flow Engine™ (STD-MFG-0001) — the constitutional orchestration layer.

The QRU Factory™ is one continuous Knowledge Manufacturing Execution System™ (KMES), not isolated
modules. This engine defines the canonical Universal Production Lifecycle, the Module Responsibility
Registry, Next-Stage Intelligence, the Production Blueprint, Production Cards, Smart Handoffs recorded
into Enterprise Memory, Blocker Management, and the Enterprise Dashboard. It sits on top of the Product
Continuity Engine (per-project stage chains) and never fakes states. AI recommends; humans authorize.
Governed by STD-MFG-0001 + QRU-CON-0001 (§4/§9/§10) + QRU-CON-0002 (Treasure Standard Pre-Ship Gate).
"""
from database import db
from models import gen_id, now_iso
import continuity as cont

DOC_ID = "STD-MFG-0001"
VERSION = "1.0"
STATUS = "Founder Approved"
EFFECTIVE = "2026-07-12"

# ---------------------------------------------------------------- UNIVERSAL PRODUCTION LIFECYCLE (18)
LIFECYCLE = [
    {"n": 1, "id": "idea", "name": "Idea", "module": "Create™", "route": "/create", "department": "Founder", "approval": False, "gate": False},
    {"n": 2, "id": "create", "name": "Create™", "module": "Factory OS", "route": "/create", "department": "Factory OS", "approval": False, "gate": False},
    {"n": 3, "id": "concierge", "name": "Factory Concierge™", "module": "Concierge", "route": "/concierge", "department": "Concierge", "approval": False, "gate": False},
    {"n": 4, "id": "innovation", "name": "Innovation Observatory™", "module": "Innovation Observatory", "route": "/autonomy", "department": "Innovation", "approval": False, "gate": False, "conditional": True},
    {"n": 5, "id": "research", "name": "Research Center™", "module": "Research", "route": "/research", "department": "Research", "approval": False, "gate": False, "conditional": True},
    {"n": 6, "id": "verification", "name": "Verification Center™", "module": "Verification", "route": "/verification", "department": "Verification", "approval": False, "gate": False, "conditional": True},
    {"n": 7, "id": "knowledge_record", "name": "Knowledge Records™", "module": "Knowledge Architecture", "route": "/kr2", "department": "Knowledge", "approval": True, "gate": False},
    {"n": 8, "id": "manufacturing", "name": "Product Manufacturing™", "module": "Manufacturing", "route": "/manufacture", "department": "Manufacturing", "approval": False, "gate": False},
    {"n": 9, "id": "design", "name": "Design Intelligence Studio™", "module": "Design Intelligence", "route": "/publishing", "department": "Design", "approval": False, "gate": False},
    {"n": 10, "id": "quality", "name": "Quality Gates™", "module": "Inspection", "route": "/inspection", "department": "Quality", "approval": False, "gate": True},
    {"n": 11, "id": "director", "name": "Manufacturing Director™", "module": "Director", "route": "/director", "department": "Governance", "approval": True, "gate": False},
    {"n": 12, "id": "gold_master", "name": "Gold Master™", "module": "Flagship Showcase", "route": "/flagship-showcase", "department": "Quality", "approval": True, "gate": True},
    {"n": 13, "id": "publishing", "name": "Publishing™", "module": "Distribution", "route": "/distribution", "department": "Publishing", "approval": True, "gate": False},
    {"n": 14, "id": "distribution", "name": "Distribution Center™", "module": "Distribution", "route": "/distribution", "department": "Distribution", "approval": False, "gate": False},
    {"n": 15, "id": "analytics", "name": "Analytics™", "module": "Analytics", "route": "/evidence", "department": "Analytics", "approval": False, "gate": False},
    {"n": 16, "id": "improvement", "name": "Continuous Improvement™", "module": "Continuous Improvement", "route": "/enterprise-autonomy", "department": "Innovation", "approval": False, "gate": False},
    {"n": 17, "id": "memory", "name": "Enterprise Memory™", "module": "Institutional Knowledge", "route": "/qiks", "department": "Memory", "approval": False, "gate": False},
    {"n": 18, "id": "observe", "name": "Innovation Observatory™ (loop)", "module": "Innovation Observatory", "route": "/autonomy", "department": "Innovation", "approval": False, "gate": False},
]

# Governed production states — a product may occupy exactly one.
PRODUCTION_STATES = ["Draft", "Research", "Verification", "Knowledge", "Manufacturing", "Design",
                     "Quality Review", "Gold Master", "Publishing", "Released", "Archived", "Deprecated", "Retired"]

# ---------------------------------------------------------------- MODULE RESPONSIBILITY REGISTRY
MODULES = [
    {"id": "factory_os", "name": "Factory OS / Create™", "purpose": "Turn an outcome request into a governed plan.",
     "inputs": ["Founder intent"], "outputs": ["Governed plan", "Tracked project"], "standards": ["QRU-CON-0001 §7"],
     "departments": ["Factory OS"], "quality_gates": ["Knowledge-First check"], "duration": "~1 min",
     "dependencies": ["Knowledge Records"], "next_stage": "concierge", "failure_recovery": "Re-describe outcome.",
     "related_products": ["all"]},
    {"id": "concierge", "name": "Factory Concierge™", "purpose": "Coordinate the human experience & route work.",
     "inputs": ["Plain-language request"], "outputs": ["Routed workflow", "Production blueprint"], "standards": ["QRU-CON-0001 §7/§8"],
     "departments": ["Concierge"], "quality_gates": ["Knowledge-First"], "duration": "instant",
     "dependencies": ["Factory OS"], "next_stage": "knowledge_record", "failure_recovery": "Clarify intent.",
     "related_products": ["all"]},
    {"id": "knowledge", "name": "Knowledge Records™", "purpose": "Verified knowledge before any product.",
     "inputs": ["Topic", "Evidence"], "outputs": ["Verified Knowledge Record"], "standards": ["KR Master Spec", "QRU-CON-0001 §3.1"],
     "departments": ["Research", "Verification", "Knowledge"], "quality_gates": ["Verification"], "duration": "varies",
     "dependencies": ["Research", "Verification"], "next_stage": "manufacturing", "failure_recovery": "Promotion Pipeline™.",
     "related_products": ["all"]},
    {"id": "manufacturing", "name": "Product Manufacturing™", "purpose": "Manufacture the product from verified knowledge.",
     "inputs": ["Verified KR", "Recipe"], "outputs": ["Draft product"], "standards": ["QRU-CON-0002"],
     "departments": ["Manufacturing", "Media"], "quality_gates": ["Quality Gates"], "duration": "minutes",
     "dependencies": ["Knowledge Records"], "next_stage": "design", "failure_recovery": "Return to Knowledge.",
     "related_products": ["all"]},
    {"id": "design", "name": "Design Intelligence Studio™", "purpose": "Apply the Publishing Standard™ & Cover Standard™.",
     "inputs": ["Draft product"], "outputs": ["Treasure-Standard experience"], "standards": ["QRU-CON-0002"],
     "departments": ["Design"], "quality_gates": ["Pre-Ship Gate"], "duration": "minutes",
     "dependencies": ["Manufacturing"], "next_stage": "quality", "failure_recovery": "Re-render with governed tokens.",
     "related_products": ["all"]},
    {"id": "quality", "name": "Quality Gates™ + Pre-Ship", "purpose": "Deterministic Treasure Standard validation.",
     "inputs": ["Designed product"], "outputs": ["Pass / Return-to-production"], "standards": ["QRU-CON-0002 Pre-Ship Gate"],
     "departments": ["Quality"], "quality_gates": ["17 blocking rules"], "duration": "instant",
     "dependencies": ["Design"], "next_stage": "gold_master", "failure_recovery": "Auto-return to failed stage.",
     "related_products": ["all"]},
    {"id": "gold_master", "name": "Gold Master™", "purpose": "Authorized certification (never auto).",
     "inputs": ["Passed product", "Human approval"], "outputs": ["Gold Master Certified™"], "standards": ["QRU-CON-0001 §10"],
     "departments": ["Quality", "Governance"], "quality_gates": ["100% QA + human sign-off"], "duration": "human",
     "dependencies": ["Quality"], "next_stage": "publishing", "failure_recovery": "Return to Quality.",
     "related_products": ["all"]},
    {"id": "publishing", "name": "Publishing™ / Distribution", "purpose": "Publish everywhere; failure-isolated.",
     "inputs": ["Gold Master"], "outputs": ["Published destinations"], "standards": ["QRU-CON-0001 §4"],
     "departments": ["Publishing", "Distribution"], "quality_gates": ["Connector readiness"], "duration": "minutes",
     "dependencies": ["Gold Master"], "next_stage": "analytics", "failure_recovery": "Per-target retry (isolated).",
     "related_products": ["all"]},
]
_MODULE_BY_ID = {m["id"]: m for m in MODULES}


# ---------------------------------------------------------------- NEXT-STAGE INTELLIGENCE
def _canon_index(stage_id):
    for s in LIFECYCLE:
        if s["id"] == stage_id or s["id"].startswith(stage_id) or stage_id.startswith(s["id"]):
            return s["n"]
    return None


def next_stage_intelligence(project):
    """Current / previous / next / remaining + approvals + blockers + production health for a project."""
    chain = project.get("chain", [])
    summ = project.get("summary") or cont._summary(project)
    idx = next((i for i, s in enumerate(chain) if s["status"] in ("in_progress", "needs_approval", "blocked")), None)
    if idx is None:
        idx = next((i for i, s in enumerate(chain) if s["status"] == "pending"), None)
    current = chain[idx] if idx is not None else None
    previous = next((chain[i] for i in range(((idx or 0) - 1), -1, -1) if chain[i]["status"] == "complete"), None) if idx else None
    nxt = None
    if idx is not None:
        nxt = next((chain[i] for i in range(idx + 1, len(chain))), None)
    remaining = [s["name"] for s in chain if s["status"] not in ("complete",)]
    approvals = [s["name"] for s in chain if s["status"] == "needs_approval"]
    blockers = [{"stage": s["name"], "reason": cont._recommended(project), "route": s.get("route")}
                for s in chain if s["status"] == "blocked"]
    health = "Blocked" if blockers else ("Awaiting Approval" if approvals else ("Complete" if summ["percent"] == 100 else "On Track"))
    return {
        "current_stage": current["name"] if current else summ["current_stage"],
        "current_status": current["status"] if current else summ["current_stage_status"],
        "current_route": (current or {}).get("route"),
        "previous_stage": previous["name"] if previous else None,
        "next_stage": nxt["name"] if nxt else ("Complete" if summ["percent"] == 100 else None),
        "remaining_stages": remaining, "approvals_required": approvals, "blockers": blockers,
        "estimated_completion": "Awaiting human action" if (approvals or blockers) else "Auto-continuing",
        "production_health": health, "percent": summ["percent"],
        "recommended_next_action": summ["recommended_next_action"],
        "governed_by": [DOC_ID, "QRU-CON-0001 §4"],
    }


def production_card(project):
    summ = project.get("summary") or cont._summary(project)
    chain = project.get("chain", [])
    gold = any(s["id"] == "gold_master" and s["status"] == "complete" for s in chain)
    blocked = any(s["status"] == "blocked" for s in chain)
    approval = any(s["status"] == "needs_approval" for s in chain)
    return {
        "project_id": project["id"], "name": f"{project.get('outcome_name','Product')} — {project.get('topic','')}".strip(" —"),
        "current_stage": summ["current_stage"], "owner": project.get("created_by", "Founder"),
        "departments": sorted({m for s in chain for m in [_stage_department(s["id"])] if m}),
        "progress": summ["percent"], "treasure_status": "Gold Master Certified™" if gold else ("In Production"),
        "risk_level": "High" if blocked else ("Medium" if approval else "Low"),
        "priority": project.get("priority", "Normal"),
        "next_action": summ["recommended_next_action"],
        "production_state": _infer_state(chain, summ, gold),
        "estimated_completion": "Awaiting human action" if (blocked or approval) else "Auto-continuing",
        "published_to": project.get("published_to", []),
    }


def _stage_department(sid):
    m = {"knowledge_record": "Knowledge", "video_script": "Media", "scene_matching": "Media",
         "assembly": "Media", "manuscript": "Manufacturing", "content": "Manufacturing", "slides": "Manufacturing",
         "script": "Media", "audio": "Audio", "design": "Design", "quality_review": "Quality",
         "founder_approval": "Governance", "gold_master": "Quality", "vault": "Memory",
         "publishing": "Publishing", "distribution": "Distribution", "export": "Design",
         "thumbnail_metadata": "Design", "production": "Manufacturing"}
    return m.get(sid)


def _infer_state(chain, summ, gold):
    if summ["percent"] == 100:
        return "Released"
    if gold:
        return "Publishing"
    cur = summ["current_stage"].lower()
    for st in PRODUCTION_STATES:
        if st.lower() in cur:
            return st
    if "approval" in cur:
        return "Quality Review"
    if "knowledge" in cur:
        return "Knowledge"
    return "Manufacturing"


def production_blueprint(outcome_id, topic, kr_found=True):
    chain = cont._chain_for(outcome_id)
    stages = [{"name": s["name"], "kind": s["kind"], "route": s.get("route"),
               "checkpoint": s["kind"] in ("gate",), "department": _stage_department(s["id"])} for s in chain]
    return {
        "outcome_id": outcome_id, "topic": topic,
        "knowledge_dependency": "Verified Knowledge Record required" + ("" if kr_found else " — NOT yet manufactured (Knowledge-First)"),
        "knowledge_ready": kr_found,
        "stages": stages, "stage_count": len(stages),
        "treasure_checkpoints": [s["name"] for s in stages if s["checkpoint"]],
        "verification_checkpoints": ["Verification Center™"] if not kr_found else [],
        "departments_involved": sorted({s["department"] for s in stages if s["department"]}),
        "estimated_time": f"~{max(4, len(stages) * 2)}–{len(stages) * 4} min of governed manufacturing",
        "expected_deliverables": [f"1× {outcome_id} (Gold Master candidate)", "Master Asset Vault™ record", "Distribution-ready package"],
        "governed_by": [DOC_ID, "QRU-CON-0001 §4", "QRU-CON-0002"],
    }


# ---------------------------------------------------------------- SMART HANDOFF + ENTERPRISE MEMORY
async def record_transition(pid, from_stage, to_stage, actor, reason="", artifacts=None, approvals=None):
    entry = {"id": gen_id(), "project_id": pid, "from_stage": from_stage, "to_stage": to_stage,
             "actor": actor, "reason": reason, "artifacts": artifacts or [], "approvals": approvals or [],
             "standards": [DOC_ID], "at": now_iso()}
    await db.flow_transitions.insert_one(dict(entry))
    entry.pop("_id", None)
    return entry


async def transitions(pid):
    rows = [r async for r in db.flow_transitions.find({"project_id": pid}, {"_id": 0}).sort("at", 1)]
    return rows


# ---------------------------------------------------------------- ENTERPRISE DASHBOARD
async def enterprise_dashboard():
    projects = await cont.list_projects()
    by_stage, blocked, approvals, gold_masters, pub_queue = {}, [], [], 0, 0
    cards = []
    for p in projects:
        card = production_card(p)
        cards.append(card)
        by_stage[card["current_stage"]] = by_stage.get(card["current_stage"], 0) + 1
        chain = p.get("chain", [])
        if any(s["status"] == "blocked" for s in chain):
            blocked.append({"project": card["name"], "next_action": card["next_action"]})
        if any(s["status"] == "needs_approval" for s in chain):
            approvals.append({"project": card["name"], "stage": card["current_stage"]})
        if card["treasure_status"] == "Gold Master Certified™":
            gold_masters += 1
        if any(s["id"] in ("publishing", "distribution") and s["status"] == "blocked" for s in chain):
            pub_queue += 1
    total = len(projects)
    done = sum(1 for c in cards if c["progress"] == 100)
    health_score = round((done + gold_masters * 0.5) / total * 100) if total else 100
    return {
        "totals": {"projects": total, "gold_masters": gold_masters, "released": done,
                   "blocked": len(blocked), "awaiting_approval": len(approvals), "publishing_queue": pub_queue},
        "by_stage": by_stage, "blocked": blocked, "awaiting_approval": approvals,
        "factory_health": {"score": health_score, "label": "Healthy" if health_score >= 60 else "Attention needed"},
        "cards": cards, "governed_by": [DOC_ID],
    }


def lifecycle_view():
    return {"doc_id": DOC_ID, "version": VERSION, "lifecycle": LIFECYCLE, "production_states": PRODUCTION_STATES}


def modules_view():
    return {"modules": MODULES}


# ---------------------------------------------------------------- CONSTITUTIONAL REGISTRY
async def constitutional_registry():
    """Small permanent registry of constitutional artifacts (never overwrite)."""
    seed = [
        {"id": "QRU-CON-0001", "name": "QRU Factory™ Constitution", "version": "1.0", "owner": "QRU",
         "category": "Foundational Governance", "implementation_status": "Production", "verification_status": "Verified"},
        {"id": "QRU-CON-0002", "name": "Enterprise Publishing & Presentation Standard™", "version": "1.0", "owner": "QRU Press™",
         "category": "Publishing / Design Governance", "implementation_status": "Production", "verification_status": "Verified"},
        {"id": DOC_ID, "name": "Universal Manufacturing Flow Engine™", "version": VERSION, "owner": "QRU",
         "category": "Production Orchestration", "implementation_status": "Production", "verification_status": "Verified"},
    ]
    stored = {d["id"]: d async for d in db.constitutional_registry.find({}, {"_id": 0})}
    out = []
    for s in seed:
        out.append(stored.get(s["id"], s))
    return {"registry": out}


async def seed_flow():
    if not await db.factory_constitution.find_one({"doc_id": DOC_ID, "version": VERSION}):
        await db.factory_constitution.insert_one({
            "id": gen_id(), "doc_id": DOC_ID, "name": "QRU Universal Manufacturing Flow Engine™",
            "version": VERSION, "status": STATUS, "authority_level": "Foundational", "effective_date": EFFECTIVE,
            "owner": "QRU", "read_only": True, "lifecycle": LIFECYCLE, "modules": MODULES,
            "created_at": now_iso(), "updated_at": now_iso()})
    if not await db.qiks_standards.find_one({"standard_id": DOC_ID}):
        await db.qiks_standards.insert_one({
            "id": gen_id(), "standard_id": DOC_ID, "name": "QRU Universal Manufacturing Flow Engine™",
            "category": "Production Orchestration", "status": "Active", "version": VERSION, "date_adopted": EFFECTIVE,
            "founder_approval": True, "description": "Constitutional orchestration layer: one continuous, auditable production lifecycle.",
            "purpose": "No product exists outside the governed production flow; the Factory always knows what's next.",
            "related_standards": ["QRU-CON-0001", "QRU-CON-0002"], "related_products": ["all"], "created_at": now_iso()})
    # Constitutional registry (never overwrite existing entries)
    for s in [
        {"id": "QRU-CON-0001", "name": "QRU Factory™ Constitution", "version": "1.0", "owner": "QRU",
         "category": "Foundational Governance", "implementation_status": "Production", "verification_status": "Verified"},
        {"id": "QRU-CON-0002", "name": "Enterprise Publishing & Presentation Standard™", "version": "1.0", "owner": "QRU Press™",
         "category": "Publishing / Design Governance", "implementation_status": "Production", "verification_status": "Verified"},
        {"id": DOC_ID, "name": "Universal Manufacturing Flow Engine™", "version": VERSION, "owner": "QRU",
         "category": "Production Orchestration", "implementation_status": "Production", "verification_status": "Verified"},
    ]:
        await db.constitutional_registry.update_one(
            {"id": s["id"]}, {"$setOnInsert": {**s, "created_at": now_iso()}}, upsert=True)
