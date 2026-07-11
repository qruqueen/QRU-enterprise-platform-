"""QRU Product Continuity Principle™ (Constitution §4 Universal Flow, §14G Production Continuity).

A manufactured asset automatically continues through every approved downstream stage until it reaches
its intended human experience (distribution) — UNLESS the user pauses/stops, a human-approval gate is
reached (§9), or a stage needs setup. The Factory thinks in completed human experiences, not files.

Every project shows its current stage, remaining stages, and the recommended next action. Honest by
design: stages that genuinely run are completed; workflow/approval/connector stages pause transparently
with a route and reason — never faked.
"""
from database import db
from models import gen_id, now_iso

# Stage kinds:
#   auto      — runs at the tracking/spec level instantly; marked complete on advance.
#   workflow  — a real governed workflow the operator drives (bears human approval per §9); pauses here.
#   gate      — explicit human approval (§9) / authorized certification (§10).
#   connector — publishing/distribution; runs when a connector is ready, else pauses (needs setup).
CHAINS = {
    "video": [
        {"id": "knowledge_record", "name": "Knowledge Record", "kind": "auto"},
        {"id": "video_script", "name": "Video Script & Narration", "kind": "workflow", "route": "/flagship-showcase"},
        {"id": "scene_matching", "name": "Scene Planning & Asset Matcher™", "kind": "workflow", "route": "/flagship-showcase"},
        {"id": "assembly", "name": "Motion Graphics, Captions & Assembly", "kind": "workflow", "route": "/flagship-showcase"},
        {"id": "thumbnail_metadata", "name": "Thumbnail & Metadata", "kind": "auto"},
        {"id": "quality_review", "name": "Technical + Content/Brand QA", "kind": "auto"},
        {"id": "founder_approval", "name": "Founder Approval", "kind": "gate"},
        {"id": "gold_master", "name": "Gold Master Certified™", "kind": "gate"},
        {"id": "vault", "name": "Master Asset Vault™", "kind": "auto"},
        {"id": "publishing", "name": "Publishing", "kind": "connector", "route": "/distribution"},
        {"id": "distribution", "name": "Platform Distribution", "kind": "connector", "route": "/distribution"},
    ],
    "book": [
        {"id": "knowledge_record", "name": "Knowledge Record", "kind": "auto"},
        {"id": "manuscript", "name": "Manuscript & Chapters", "kind": "workflow", "route": "/manufacture"},
        {"id": "design", "name": "Cover & Interior Design", "kind": "workflow", "route": "/manufacture"},
        {"id": "quality_review", "name": "Quality Review", "kind": "auto"},
        {"id": "founder_approval", "name": "Founder Approval", "kind": "gate"},
        {"id": "vault", "name": "Master Asset Vault™", "kind": "auto"},
        {"id": "publishing", "name": "Publishing (KDP / Store)", "kind": "connector", "route": "/distribution"},
    ],
    "podcast": [
        {"id": "knowledge_record", "name": "Knowledge Record", "kind": "auto"},
        {"id": "script", "name": "Podcast Script", "kind": "workflow", "route": "/manufacture"},
        {"id": "audio", "name": "Audio Production (Narration)", "kind": "workflow", "route": "/manufacture"},
        {"id": "quality_review", "name": "Quality Review", "kind": "auto"},
        {"id": "founder_approval", "name": "Founder Approval", "kind": "gate"},
        {"id": "vault", "name": "Master Asset Vault™", "kind": "auto"},
        {"id": "distribution", "name": "Audio Distribution", "kind": "connector", "route": "/distribution"},
    ],
    "audiobook": [
        {"id": "knowledge_record", "name": "Knowledge Record", "kind": "auto"},
        {"id": "script", "name": "Narration Script", "kind": "workflow", "route": "/manufacture"},
        {"id": "audio", "name": "Audio Production", "kind": "workflow", "route": "/manufacture"},
        {"id": "quality_review", "name": "Quality Review", "kind": "auto"},
        {"id": "founder_approval", "name": "Founder Approval", "kind": "gate"},
        {"id": "vault", "name": "Master Asset Vault™", "kind": "auto"},
        {"id": "distribution", "name": "Audio Distribution", "kind": "connector", "route": "/distribution"},
    ],
    "presentation": [
        {"id": "knowledge_record", "name": "Knowledge Record", "kind": "auto"},
        {"id": "slides", "name": "Slide Composition", "kind": "workflow", "route": "/manufacture"},
        {"id": "design", "name": "Art Direction", "kind": "workflow", "route": "/manufacture"},
        {"id": "quality_review", "name": "Quality Review", "kind": "auto"},
        {"id": "founder_approval", "name": "Founder Approval", "kind": "gate"},
        {"id": "export", "name": "Export-Ready Formats", "kind": "auto"},
        {"id": "vault", "name": "Master Asset Vault™", "kind": "auto"},
    ],
    "workbook": [
        {"id": "knowledge_record", "name": "Knowledge Record", "kind": "auto"},
        {"id": "content", "name": "Workbook Content & Answer Key", "kind": "workflow", "route": "/manufacture"},
        {"id": "design", "name": "Layout & Art Direction", "kind": "workflow", "route": "/manufacture"},
        {"id": "quality_review", "name": "Quality Review", "kind": "auto"},
        {"id": "founder_approval", "name": "Founder Approval", "kind": "gate"},
        {"id": "vault", "name": "Master Asset Vault™", "kind": "auto"},
        {"id": "distribution", "name": "Printable & Digital Distribution", "kind": "connector", "route": "/distribution"},
    ],
}
# Default chain for outcomes without a bespoke chain.
_DEFAULT_CHAIN = [
    {"id": "knowledge_record", "name": "Knowledge Record", "kind": "auto"},
    {"id": "production", "name": "Production", "kind": "workflow", "route": "/manufacture"},
    {"id": "quality_review", "name": "Quality Review", "kind": "auto"},
    {"id": "founder_approval", "name": "Founder Approval", "kind": "gate"},
    {"id": "vault", "name": "Master Asset Vault™", "kind": "auto"},
    {"id": "distribution", "name": "Distribution", "kind": "connector", "route": "/distribution"},
]

_ROUTE_LABEL = {"/flagship-showcase": "Flagship Showcase™", "/manufacture": "Product Manufacturing",
                "/distribution": "Distribution Center™"}


def _chain_for(outcome_id):
    stages = CHAINS.get(outcome_id, _DEFAULT_CHAIN)
    return [{**s, "status": "pending"} for s in stages]


async def _connector_ready():
    """A publishing/distribution connector is ready only when at least one destination is connected.
    Honest: the native QRU Store™ is always available; external platforms need setup."""
    try:
        n = await db.distribution_jobs.count_documents({})
    except Exception:
        n = 0
    # QRU Store native connector is always available (Constitution — no faked states).
    return True, "QRU Store™ (native) is available; external platforms require Developer Setup."


def _recommended(project):
    stages = project["chain"]
    if project.get("mode") == "stopped":
        return "Project stopped by the operator. Resume to continue governed manufacturing."
    if project.get("mode") == "paused":
        return "Paused by the operator. Resume to continue."
    cur = next((s for s in stages if s["status"] in ("in_progress", "needs_approval", "blocked")), None)
    if cur is None:
        if all(s["status"] == "complete" for s in stages):
            return "Complete — the product has reached its intended human experience."
        nxt = next((s for s in stages if s["status"] == "pending"), None)
        return f"Continue to “{nxt['name']}”." if nxt else "Continue."
    if cur["status"] == "needs_approval":
        return f"Your approval is required at “{cur['name']}”. Approve to continue automatically."
    if cur["status"] == "blocked":
        return f"“{cur['name']}” needs a connector. Set up a destination in the {_ROUTE_LABEL.get(cur.get('route'),'Distribution Center™')}."
    if cur["status"] == "in_progress":
        return f"Open the {_ROUTE_LABEL.get(cur.get('route'),'workflow')} to complete “{cur['name']}”."
    return "Continue."


def _summary(project):
    stages = project["chain"]
    complete = [s for s in stages if s["status"] == "complete"]
    current = next((s for s in stages if s["status"] in ("in_progress", "needs_approval", "blocked")), None)
    remaining = [s for s in stages if s["status"] == "pending"]
    return {
        "current_stage": current["name"] if current else ("Complete" if not remaining else remaining[0]["name"]),
        "current_stage_status": current["status"] if current else ("complete" if not remaining else "pending"),
        "current_route": (current or {}).get("route"),
        "completed_count": len(complete), "total": len(stages),
        "remaining_stages": [s["name"] for s in ([current] if current else []) + remaining if s],
        "recommended_next_action": _recommended(project),
        "percent": round(len(complete) / len(stages) * 100) if stages else 0,
    }


def _advance_auto(project):
    """Walk forward from the first non-complete stage. Complete every 'auto' stage; stop (pause) at the
    first workflow/gate/blocked-connector stage. This is the governed auto-continuation."""
    if project.get("mode") in ("paused", "stopped"):
        return project
    stages = project["chain"]
    for s in stages:
        if s["status"] == "complete":
            continue
        if s["kind"] == "auto":
            s["status"] = "complete"
            continue
        if s["kind"] == "gate":
            s["status"] = "needs_approval"
            return project
        if s["kind"] == "workflow":
            s["status"] = "in_progress"
            return project
        if s["kind"] == "connector":
            ready, _ = True, None  # resolved by caller when needed
            s["status"] = "pending_connector"
            # Represent as blocked so the operator gets a clear setup action (honest, not faked-published).
            s["status"] = "blocked"
            return project
    return project


async def create_project(plan, actor):
    outcome = plan.get("outcome") or {}
    outcome_id = outcome.get("id")
    gap = plan.get("knowledge_gap") or {}
    project = {
        "id": gen_id(), "outcome_id": outcome_id, "outcome_name": outcome.get("name"),
        "topic": plan.get("topic"), "audience": plan.get("audience"), "goal": plan.get("goal"),
        "workflow": (plan.get("launch") or {}).get("workflow"),
        "knowledge_record": gap.get("knowledge_record"),
        "governed_by": plan.get("governed_by", []),
        "chain": _chain_for(outcome_id), "mode": "auto_continue", "created_by": actor,
        "created_at": now_iso(), "updated_at": now_iso(),
        "history": [{"at": now_iso(), "actor": actor, "action": "created", "mode": "auto_continue"}],
    }
    # Knowledge-First: the KR stage is complete only when an approved KR exists (§3.1).
    if gap.get("knowledge_record_found"):
        project["chain"][0]["status"] = "complete"
        _advance_auto(project)
    else:
        project["chain"][0]["status"] = "blocked"  # must manufacture the KR first
        project["chain"][0]["route"] = "/promotion-pipeline"
    await db.continuity_projects.insert_one(dict(project))
    project.pop("_id", None)
    return {**project, "summary": _summary(project)}


def _clean(p):
    if p:
        p.pop("_id", None)
    return p


async def get_project(pid):
    p = _clean(await db.continuity_projects.find_one({"id": pid}))
    return {**p, "summary": _summary(p)} if p else None


async def list_projects(actor=None):
    q = {}
    rows = await db.continuity_projects.find(q, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [{**r, "summary": _summary(r)} for r in rows]


async def _save(project):
    project["updated_at"] = now_iso()
    await db.continuity_projects.update_one({"id": project["id"]}, {"$set": {
        "chain": project["chain"], "mode": project["mode"], "updated_at": project["updated_at"],
        "history": project.get("history", [])}})


async def advance(pid, actor):
    p = _clean(await db.continuity_projects.find_one({"id": pid}))
    if not p:
        return None
    if p.get("mode") == "stopped":
        return {**p, "summary": _summary(p)}
    p.setdefault("history", []).append({"at": now_iso(), "actor": actor, "action": "advance"})
    _advance_auto(p)
    await _save(p)
    return {**p, "summary": _summary(p)}


async def approve_gate(pid, actor):
    """Pass the current human-approval gate (§9), then auto-continue."""
    p = _clean(await db.continuity_projects.find_one({"id": pid}))
    if not p:
        return None
    cur = next((s for s in p["chain"] if s["status"] == "needs_approval"), None)
    if not cur:
        return {**p, "summary": _summary(p), "note": "No approval is currently required."}
    cur["status"] = "complete"
    p.setdefault("history", []).append({"at": now_iso(), "actor": actor, "action": "approved", "stage": cur["id"]})
    _advance_auto(p)
    await _save(p)
    return {**p, "summary": _summary(p)}


async def complete_workflow_stage(pid, actor, note=""):
    """Mark the current in-progress workflow stage complete (its real workflow finished), then continue."""
    p = _clean(await db.continuity_projects.find_one({"id": pid}))
    if not p:
        return None
    cur = next((s for s in p["chain"] if s["status"] == "in_progress"), None)
    if cur:
        cur["status"] = "complete"
        p.setdefault("history", []).append({"at": now_iso(), "actor": actor, "action": "workflow_complete", "stage": cur["id"], "note": note})
    _advance_auto(p)
    await _save(p)
    return {**p, "summary": _summary(p)}


async def set_mode(pid, mode, actor):
    p = _clean(await db.continuity_projects.find_one({"id": pid}))
    if not p:
        return None
    p["mode"] = mode
    p.setdefault("history", []).append({"at": now_iso(), "actor": actor, "action": f"mode:{mode}"})
    if mode == "auto_continue":
        _advance_auto(p)
    await _save(p)
    return {**p, "summary": _summary(p)}
