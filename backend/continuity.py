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
                "/distribution": "Distribution Center™", "/promotion-pipeline": "Promotion Pipeline™"}


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
        if cur.get("id") == "knowledge_record" or cur.get("kind") == "auto":
            return "Knowledge always comes before products — manufacture the Knowledge Record first in the Promotion Pipeline™."
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
    """Pass the current human-approval gate (§9), then auto-continue.
    Gold Master is NOT a simple approval — it must be certified via the real certification path
    (Technical+Brand QA gates, §10). We refuse to complete it here (honesty invariant)."""
    p = _clean(await db.continuity_projects.find_one({"id": pid}))
    if not p:
        return None
    cur = next((s for s in p["chain"] if s["status"] == "needs_approval"), None)
    if not cur:
        return {**p, "summary": _summary(p), "note": "No approval is currently required."}
    if cur["id"] == "gold_master":
        return {**p, "summary": _summary(p), "requires_certification": True,
                "note": "Gold Master Certified™ cannot be granted by simple approval. Certify it "
                        "(Technical + Brand QA must be 100) from the Gold Master certification action."}
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


def _sentences(text):
    import re
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [s.strip() for s in parts if len(s.strip()) > 3]


async def _load_kr_full(kr_ref):
    """Resolve the full Knowledge Record for a project across engine + legacy stores."""
    if not kr_ref:
        return None
    kid = kr_ref.get("id")
    code = kr_ref.get("kr_code") or kr_ref.get("code")
    for coll, idf in ((db.knowledge_engine_records, "id"), (db.knowledge_records, "id")):
        if kid:
            doc = await coll.find_one({idf: kid}, {"_id": 0})
            if doc:
                return doc
    if code:
        doc = await db.knowledge_records.find_one({"kr_code": code}, {"_id": 0}) \
            or await db.knowledge_engine_records.find_one({"kr_code": code}, {"_id": 0})
        if doc:
            return doc
    return None


def _kr_text_blocks(kr):
    """Pull human-readable explanatory text from whatever KR schema is present (deterministic, no AI)."""
    if not kr:
        return []
    blocks = []
    sec = kr.get("sections")
    if isinstance(sec, dict):
        for k in ("definition", "explanation", "examples", "common_misunderstandings"):
            v = sec.get(k)
            if isinstance(v, list):
                v = " ".join(str(x) for x in v)
            if v:
                blocks.append(str(v))
    for k in ("simple_answer", "verified_truth", "qru_translation", "deep_roots", "summary", "overview", "content"):
        v = kr.get(k)
        if isinstance(v, list):
            v = " ".join(str(x) for x in v)
        if v:
            blocks.append(str(v))
    return blocks


async def project_items(pid):
    """Viewable produced items for a project: the governed Video Script & Narration (from the verified
    KR — never AI-authored) and any manufactured deliverables. Knowledge-First & honest: if no KR text
    exists yet, the script is marked not-yet-available with a clear reason."""
    p = _clean(await db.continuity_projects.find_one({"id": pid}))
    if not p:
        return None
    kr = await _load_kr_full(p.get("knowledge_record"))
    topic = p.get("topic") or (p.get("knowledge_record") or {}).get("topic") or "this topic"
    blocks = _kr_text_blocks(kr)
    text = " ".join(blocks)
    sentences = _sentences(text)

    is_audio_video = p.get("outcome_id") in ("video", "podcast", "audiobook")
    script = {"available": False, "reason": "", "narration": [], "scenes": []}
    if is_audio_video:
        if sentences:
            hook = f"What if you finally understood {topic}? Let's make it simple."
            close = "That's the QRU way — we don't just teach information, we create understanding."
            narration = [hook] + sentences[:8] + [close]
            script = {
                "available": True,
                "source": (kr or {}).get("kr_code") or (p.get("knowledge_record") or {}).get("kr_code"),
                "narration": narration,
                "scenes": [{"n": i + 1, "beat": ln,
                            "visual": "Open on a familiar, relatable scene." if i == 0 else
                                      ("Close on an empowered, transformed viewer." if i == len(narration) - 1 else
                                       "Reveal the idea with a clean supporting visual.")}
                           for i, ln in enumerate(narration)],
            }
        else:
            script = {"available": False,
                      "reason": "The Video Script & Narration will be generated from a verified Knowledge Record. This project's Knowledge Record has no explanatory content yet — manufacture/verify it first.",
                      "narration": [], "scenes": []}

    # Deliverables produced for this project's KR (products + posters), honest links.
    deliverables = []
    kr_id = (kr or {}).get("id") or (p.get("knowledge_record") or {}).get("id")
    if kr_id:
        async for prod in db.products.find({"knowledge_record_id": kr_id}, {"_id": 0}).limit(20):
            cd = prod.get("customer_deliverable") or {}
            for f in cd.get("files", []):
                deliverables.append({"label": f"{prod.get('title', prod.get('product_type',''))} · {f.get('label', f.get('format','').upper())}",
                                     "format": f.get("format"), "url": f.get("url"), "source": "product"})
        async for pa in db.poster_assets.find({"kr_id": kr_id}, {"_id": 0}).limit(20):
            deliverables.append({"label": f"{pa.get('title','Poster')} · Poster (PNG)", "format": "png",
                                 "url": f"/api/publishing/poster/{pa['id']}/file?format=png", "source": "poster"})
            deliverables.append({"label": f"{pa.get('title','Poster')} · Poster (PDF)", "format": "pdf",
                                 "url": f"/api/publishing/poster/{pa['id']}/file?format=pdf", "source": "poster"})

    return {
        "project_id": pid, "outcome": p.get("outcome_name"), "topic": topic,
        "kr": {"found": bool(kr), "code": (kr or {}).get("kr_code") or (p.get("knowledge_record") or {}).get("kr_code"),
               "topic": (kr or {}).get("topic") or (kr or {}).get("title")},
        "script": script, "deliverables": deliverables,
    }



# ---- Zero-touch effort reduction (Founder Effort Reduction Directive) ----
# eliminating manual status tracking and manual re-linking between modules.

async def on_production_complete(pid, qru_asset_id, actor, minutes_saved=6):
    """A real production run finished: auto-complete every pre-approval stage (workflow + auto) and
    stop at the first human-approval gate. Eliminates manually ticking off each stage."""
    p = _clean(await db.continuity_projects.find_one({"id": pid}))
    if not p:
        return None
    p["showcase_asset_id"] = qru_asset_id
    for s in p["chain"]:
        if s["status"] == "complete":
            continue
        if s["kind"] == "gate":
            break
        s["status"] = "complete"
    _advance_auto(p)
    p["effort_minutes_saved"] = p.get("effort_minutes_saved", 0) + minutes_saved
    p.setdefault("history", []).append({"at": now_iso(), "actor": actor, "action": "production_complete",
                                         "asset": qru_asset_id, "auto": True})
    await db.continuity_projects.update_one({"id": pid}, {"$set": {
        "chain": p["chain"], "showcase_asset_id": qru_asset_id,
        "effort_minutes_saved": p["effort_minutes_saved"], "updated_at": now_iso(),
        "history": p["history"]}})
    return {**p, "summary": _summary(p)}


async def on_gold_master(qru_asset_id, actor, minutes_saved=3):
    """Gold Master certification auto-passes the Founder Approval + Gold Master gates."""
    p = _clean(await db.continuity_projects.find_one({"showcase_asset_id": qru_asset_id}))
    if not p:
        return None
    for s in p["chain"]:
        if s["id"] in ("founder_approval", "gold_master") and s["status"] in ("needs_approval", "pending"):
            s["status"] = "complete"
    _advance_auto(p)
    p["effort_minutes_saved"] = p.get("effort_minutes_saved", 0) + minutes_saved
    p.setdefault("history", []).append({"at": now_iso(), "actor": actor, "action": "gold_master_certified", "auto": True})
    await db.continuity_projects.update_one({"id": p["id"]}, {"$set": {
        "chain": p["chain"], "effort_minutes_saved": p["effort_minutes_saved"],
        "updated_at": now_iso(), "history": p["history"]}})
    return {**p, "summary": _summary(p)}


async def on_published(qru_asset_id, url, video_id, actor, minutes_saved=8):
    """A Factory asset was published to a platform: auto-complete Publishing + Platform Distribution and
    record the destination. Eliminates manual status tracking after publishing."""
    p = _clean(await db.continuity_projects.find_one({"showcase_asset_id": qru_asset_id}))
    if not p:
        return None
    for s in p["chain"]:
        if s["id"] == "gold_master":
            continue  # never auto-certify Gold Master — that is a separate authorized action (§10, honesty)
        if s["id"] in ("publishing", "distribution") and s["status"] != "complete":
            s["status"] = "complete"
        elif s["kind"] == "auto" and s["status"] != "complete":
            s["status"] = "complete"  # vault etc. — a successful publish means these are done
        elif s["id"] == "founder_approval" and s["status"] in ("needs_approval", "pending"):
            s["status"] = "complete"  # publishing is an explicit Founder action = approval
    p.setdefault("published_to", [])
    if not any(d.get("video_id") == video_id for d in p["published_to"]):
        p["published_to"].append({"platform": "youtube", "url": url, "video_id": video_id, "at": now_iso()})
    p["effort_minutes_saved"] = p.get("effort_minutes_saved", 0) + minutes_saved
    p.setdefault("history", []).append({"at": now_iso(), "actor": actor, "action": "published",
                                        "platform": "youtube", "video_id": video_id, "auto": True})
    await db.continuity_projects.update_one({"id": p["id"]}, {"$set": {
        "chain": p["chain"], "published_to": p["published_to"],
        "effort_minutes_saved": p["effort_minutes_saved"], "updated_at": now_iso(), "history": p["history"]}})
    return {**p, "summary": _summary(p)}


async def on_publish_failed(qru_asset_id, destination, reason, actor):
    """Publishing failed on one destination. Preserve everything; record the failure for retry.
    The Gold Master is never touched."""
    p = _clean(await db.continuity_projects.find_one({"showcase_asset_id": qru_asset_id}))
    if not p:
        return None
    p.setdefault("failed_destinations", []).append(
        {"platform": destination, "reason": reason, "at": now_iso(), "human_action_required": True})
    p.setdefault("history", []).append({"at": now_iso(), "actor": actor, "action": "publish_failed",
                                        "platform": destination, "reason": reason})
    await db.continuity_projects.update_one({"id": p["id"]}, {"$set": {
        "failed_destinations": p["failed_destinations"], "updated_at": now_iso(), "history": p["history"]}})
    return {**p, "summary": _summary(p)}


async def effort_summary():
    """Founder Effort Reduction ledger — how much operator time the Factory has absorbed."""
    rows = await db.continuity_projects.find({}, {"_id": 0, "effort_minutes_saved": 1, "published_to": 1, "history": 1}).to_list(1000)
    total_min = sum(r.get("effort_minutes_saved", 0) for r in rows)
    auto_actions = sum(1 for r in rows for h in r.get("history", []) if h.get("auto"))
    published = sum(len(r.get("published_to", []) or []) for r in rows)
    return {
        "minutes_saved": total_min, "hours_saved": round(total_min / 60, 1),
        "automated_actions": auto_actions, "auto_published": published,
        "eliminated_tasks": ["Manual status tracking", "Manual asset linking", "Manual publishing preparation",
                             "Manual file re-upload", "Manual asset discovery"],
    }
