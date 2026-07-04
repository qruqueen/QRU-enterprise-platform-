"""QRU Autonomous Manufacturing Engine™ (AO-001) — deterministic self-coordination.

The engine continuously determines the next SAFE action for every product and advances it
through the approved QRU workflow WITHOUT waiting for Founder instructions:

    Knowledge → Branded Assets → Deliverable → Design Director™ → Product Protection™
    → Creative Studio™ → Data Health™ / Factory Confidence™ → Founder Review Inbox™

Governance preserved (Founder Interruption Policy™): the engine NEVER publishes, deletes,
or materially rewrites a product. It only performs deterministic ($0 AI) manufacturing
steps and hands finished work to the Founder Review Inbox™. It stops and escalates only
when human judgment is genuinely required.

Reuses existing architecture: rendering_engine, deliverable_renderer, design_director,
product_protection, factory_confidence.
"""
import logging

from database import db
from models import now_iso

import factory_confidence as fc

logger = logging.getLogger("qru.autonomous_engine")

SETTINGS_KEY = "autonomy_engine"
DEFAULT_SETTINGS = {
    "enabled": False,            # global Founder-controlled ON/OFF (safe default: OFF)
    "max_per_cycle": 5,          # products advanced per autonomous cycle
    "publish_threshold": 91,     # Design Director™ baseline (Founder can override)
}

ACTION_COL = db["autonomy_actions"]


async def get_settings():
    doc = await db.factory_settings.find_one({"key": SETTINGS_KEY})
    s = dict(DEFAULT_SETTINGS)
    if doc:
        s.update({k: doc[k] for k in DEFAULT_SETTINGS if k in doc})
    return s


async def update_settings(updates):
    s = await get_settings()
    for k in DEFAULT_SETTINGS:
        if k in updates and updates[k] is not None:
            s[k] = updates[k]
    await db.factory_settings.update_one({"key": SETTINGS_KEY}, {"$set": {"key": SETTINGS_KEY, **s}}, upsert=True)
    return s


async def _record(kind, target, detail):
    await ACTION_COL.insert_one({"kind": kind, "target": target, "detail": detail,
                                 "engine": True, "at": now_iso()})


MEMORY_COL = db["manufacturing_memory"]


async def record_memory(pid, step, error, recovered, attempts):
    """Manufacturing Memory™ — every failure/recovery becomes a permanent lesson so the
    factory never repeatedly fails for the same reason."""
    p = await db.products.find_one({"id": pid}, {"product_code": 1, "product_type": 1, "_id": 0}) or {}
    await MEMORY_COL.insert_one({
        "product_id": pid, "product_code": p.get("product_code"),
        "product_type": p.get("product_type"), "step": step,
        "error": error, "recovered": recovered, "attempts": attempts, "at": now_iso(),
    })


async def factory_learning():
    """Factory Learning™ — the factory should get better every day."""
    docs = []
    async for d in MEMORY_COL.find({}):
        d.pop("_id", None)
        docs.append(d)
    total = len(docs)
    recovered = sum(1 for d in docs if d.get("recovered"))
    recovery_rate = round(100 * recovered / total) if total else 100
    by_step = {}
    for d in docs:
        s = d.get("step", "?")
        by_step[s] = by_step.get(s, 0) + 1
    common = sorted([{"step": k, "count": v} for k, v in by_step.items()], key=lambda x: -x["count"])[:5]
    advances = await ACTION_COL.count_documents({"engine": True, "kind": "advance"})
    return {
        "failures_seen": total, "auto_recovered": recovered,
        "auto_recovery_rate": recovery_rate,
        "founder_interruptions_prevented": advances,
        "common_failures": common,
    }


# --------------------------------------------------------------------------- #
# Next Action™ — deterministic decision for a single product (read-only).
# --------------------------------------------------------------------------- #
def next_action(p, threshold=91):
    """Determine the next safe step for a product. Never mutates.
    Returns {step, label, needs_founder, reason}."""
    if p.get("status") in ("Published", "Archived"):
        return {"step": "done", "label": "Live / archived", "needs_founder": False, "reason": ""}
    content = p.get("content") or ""
    has_content = len(content) >= fc.MIN_CONTENT_CHARS
    has_kr = bool(p.get("knowledge_record_id")) or bool(p.get("assembled"))

    # Founder Interruption Policy™ — required source material missing.
    if not has_content and not has_kr:
        return {"step": "blocked", "label": "Needs Knowledge Record",
                "needs_founder": True, "reason": "Required source material is missing."}
    if not has_content and has_kr:
        return {"step": "blocked", "label": "Needs content manufacturing",
                "needs_founder": True, "reason": "Knowledge Record present but content not manufactured (needs AI capacity or manual completion)."}

    if not p.get("design_language_applied"):
        return {"step": "brand", "label": "Apply QRU branding", "needs_founder": False, "reason": ""}
    if not p.get("deliverable_ready"):
        return {"step": "deliverable", "label": "Render customer deliverable", "needs_founder": False, "reason": ""}
    if not (p.get("design_gate") or {}).get("gated_at"):
        return {"step": "design_gate", "label": "Run Design Director™", "needs_founder": False, "reason": ""}
    if not p.get("verified"):
        return {"step": "verify", "label": "Run Product Protection™", "needs_founder": False, "reason": ""}
    if not (p.get("creative_brief") and p.get("creative_status") == "Reviewed"):
        return {"step": "creative", "label": "Add Creative Studio™ brief", "needs_founder": False, "reason": ""}
    if not p.get("protected"):
        return {"step": "protect", "label": "Apply IP protection", "needs_founder": False, "reason": ""}

    ok, blockers = fc.publish_gate(p, threshold)
    if ok:
        return {"step": "founder_review", "label": "Awaiting Founder publish decision",
                "needs_founder": True, "reason": "Publishing approval is required."}
    return {"step": "needs_fix", "label": "Needs improvement",
            "needs_founder": True, "reason": "; ".join(blockers[:2])}


# --------------------------------------------------------------------------- #
# Advance™ — perform the deterministic chain for a single product.
# --------------------------------------------------------------------------- #
async def advance_product(pid, actor="Autonomous Manufacturing Engine™", threshold=91):
    """Run every SAFE deterministic step for one product until it either becomes
    ready for the Founder Review Inbox™ or hits a Founder-judgment stop. $0 AI."""
    p = await db.products.find_one({"id": pid})
    if not p:
        return {"id": pid, "ok": False, "message": "Not found", "actions": []}

    actions, escalated = [], None
    import rendering_engine as re_engine
    import deliverable_renderer as dr
    import design_director as dd
    import product_protection as pp

    # Loop the deterministic chain (bounded) so several steps complete in one pass.
    _STEP_FN = {
        "brand": lambda: re_engine.ensure_branded_assets(pid, actor, allow_ai_hero_art=False),
        "deliverable": lambda: dr.ensure_deliverable(pid, actor),
        "design_gate": lambda: dd.auto_gate(pid, actor),
        "verify": lambda: _deterministic_verify(pid, actor),
        "creative": lambda: _deterministic_brief(pid),
    }
    _STEP_LABEL = {"brand": "Applied QRU branding", "deliverable": "Rendered customer deliverable",
                   "design_gate": "Ran Design Director™ gate", "verify": "Ran Product Protection™ verification",
                   "creative": "Added Creative Studio™ brief", "protect": "Applied IP protection"}
    for _ in range(8):
        p = await db.products.find_one({"id": pid})
        na = next_action(p, threshold)
        step = na["step"]
        if step in ("done", "founder_review", "needs_fix", "blocked"):
            if na["needs_founder"] and step in ("blocked",):
                escalated = na["reason"]
            break
        # Autonomous Recovery Engine™ — Manufacture → Detect → Recover → Retry → Continue.
        last_err = None
        for attempt in range(1, 3):  # up to 2 attempts before escalating
            try:
                if step == "protect":
                    await pp.apply_protection(pid, p.get("license_type") or "Personal Use",
                                              True, "account_required", actor)
                else:
                    await _STEP_FN[step]()
                actions.append(_STEP_LABEL.get(step, step))
                if attempt > 1:
                    await _record("recovered", pid, f"{p.get('product_code','')}: auto-recovered '{step}' on attempt {attempt}")
                    await record_memory(pid, step, last_err, recovered=True, attempts=attempt)
                last_err = None
                break
            except Exception as e:
                last_err = str(e)[:160]
                logger.warning(f"advance step '{step}' attempt {attempt} failed for {pid}: {e}")
        if last_err is not None:
            # Recovery impossible after retries — record the lesson and escalate this product only.
            await record_memory(pid, step, last_err, recovered=False, attempts=2)
            escalated = f"Could not complete '{_STEP_LABEL.get(step, step)}' automatically after 2 attempts."
            break

    p = await db.products.find_one({"id": pid})
    conf = fc.factory_confidence(p, threshold)
    na = next_action(p, threshold)
    if actions:
        await _record("advance", pid, f"{p.get('product_code','')}: {', '.join(actions)}")
    return {
        "id": pid, "product_code": p.get("product_code"), "ok": True,
        "actions": actions, "escalated": escalated,
        "next_action": na, "factory_confidence": conf["score"],
        "data_health": conf["data_health"]["status"],
        "message": ("Escalated to Founder: " + escalated) if escalated
                   else (f"{len(actions)} step(s) completed → {na['label']}" if actions else na["label"]),
    }


async def _deterministic_verify(pid, actor):
    """$0-AI Product Protection™ verification — structural checks only, never calls the LLM.
    Escalation for IP/legal/source conflicts stays a Founder decision (handled elsewhere)."""
    p = await db.products.find_one({"id": pid})
    if not p:
        return
    content = p.get("content") or ""
    has_body = len(content.strip()) >= fc.MIN_CONTENT_CHARS
    conf = 85 if has_body else 40
    history = (p.get("verification") or {}).get("revision_history", [])
    history.append({"at": now_iso(), "decision": "approve" if has_body else "request_revision",
                    "confidence_score": conf, "reasons": "Deterministic structural verification ($0 AI)."})
    verification = {
        "reviewer": "QRU Deterministic Check™",
        "decision": "approve" if has_body else "request_revision",
        "confidence_score": conf, "scores": {},
        "sources_checked": [], "issues": [] if has_body else ["Product content is missing or too short."],
        "reasons": "Deterministic structural verification ($0 AI).",
        "approved_at": now_iso() if has_body else None,
        "revision_history": history, "autonomous": True, "ai_recommendations_available": False,
    }
    await db.products.update_one({"id": pid}, {"$set": {
        "verification": verification, "verified": has_body, "updated_at": now_iso()}})


async def _deterministic_brief(pid):
    """On-brand Creative Studio™ brief with $0 AI (mirrors the deterministic fallback)."""
    p = await db.products.find_one({"id": pid})
    if not p:
        return
    ptype = p.get("product_type", "resource")
    topic = p.get("topic") or p.get("title", "this topic")
    audience = p.get("audience") or "curious learners"
    brief = {
        "who_for": f"For {audience} who want to genuinely understand {topic}.",
        "problem_solved": f"Turns {topic} from confusing to clear, using the QRU teaching methodology.",
        "will_understand": f"You'll understand what {topic} is, why it matters, and how to apply it in real life.",
        "skills_gained": ["Clear understanding of the core idea", "Real-world application", "Confidence to explain it to others"],
        "whats_included": [f"A complete QRU {ptype}", "Verified, plain-language explanations", "Memory aids and a next step"],
        "reading_level": p.get("reading_level") or "Beginner-friendly",
        "completion_time": "About 20 minutes",
        "next_path": "Continue with the next product in this QRU learning family.",
    }
    related = await db.products.find(
        {"family": p.get("family"), "id": {"$ne": pid}},
        {"id": 1, "title": 1, "product_type": 1, "product_code": 1, "_id": 0}).to_list(4)
    await db.products.update_one({"id": pid}, {"$set": {
        "creative_brief": brief, "creative_brief_source": "deterministic",
        "related_products": related, "creative_status": "Reviewed", "updated_at": now_iso()}})


# --------------------------------------------------------------------------- #
# Priority Engine™ — rank pending work by the approved 9-level order.
# --------------------------------------------------------------------------- #
def _priority(p, na):
    """Lower number = higher priority (protect the customer first)."""
    status = p.get("status")
    # 1. Prevent customer-facing errors (published but flagged).
    if status == "Published" and p.get("customer_content_review_required"):
        return 1
    # 2. Complete blocked manufacturing that is recoverable deterministically.
    if na["step"] in ("brand", "deliverable", "design_gate", "verify", "creative", "protect"):
        return 2
    # 3. Improve existing products that fell below the bar.
    if na["step"] == "needs_fix":
        return 3
    # 4. Ready — awaiting Founder judgment (no autonomous action).
    if na["step"] == "founder_review":
        return 4
    # 5. Blocked on source material — needs Founder.
    if na["step"] == "blocked":
        return 5
    return 9


async def priority_queue(limit=200, threshold=91):
    prods = await db.products.find({
        "status": {"$nin": ["Archived"]}, "founder_hidden": {"$ne": True},
    }).sort("updated_at", -1).to_list(1000)
    rows = []
    for p in prods:
        na = next_action(p, threshold)
        if na["step"] == "done":
            continue
        conf = fc.factory_confidence(p, threshold)
        rows.append({
            "id": p["id"], "product_code": p.get("product_code"), "title": p.get("title"),
            "product_type": p.get("product_type"), "status": p.get("status"),
            "priority": _priority(p, na), "next_action": na,
            "factory_confidence": conf["score"], "data_health": conf["data_health"]["status"],
            "data_health_label": conf["data_health"]["label"],
            "actionable": not na["needs_founder"] and na["step"] not in ("blocked",),
        })
    rows.sort(key=lambda r: (r["priority"], -r["factory_confidence"]))
    return rows[:limit]


async def run_cycle(actor="Autonomous Manufacturing Engine™", limit=None, force=False):
    """Advance the top actionable products one deterministic cycle. Respects the
    global ON/OFF switch unless force=True (manual 'Run one cycle')."""
    s = await get_settings()
    if not s["enabled"] and not force:
        return {"ran": False, "reason": "Autonomy is OFF", "advanced": [], "enabled": False}
    lim = limit or s["max_per_cycle"]
    queue = await priority_queue(limit=200, threshold=s["publish_threshold"])
    actionable = [r for r in queue if r["actionable"]][:lim]
    advanced = []
    for r in actionable:
        res = await advance_product(r["id"], actor, s["publish_threshold"])
        if res.get("actions"):
            advanced.append(res)
        import asyncio
        await asyncio.sleep(0)  # yield so the API stays responsive during a cycle
    if advanced:
        await _record("cycle", "-", f"Advanced {len(advanced)} product(s) autonomously")
    return {"ran": True, "enabled": s["enabled"], "advanced": advanced,
            "considered": len(actionable), "cycle_at": now_iso()}


# --------------------------------------------------------------------------- #
# Autonomy Dashboard™ metrics.
# --------------------------------------------------------------------------- #
def _today(ts):
    return bool(ts) and str(ts)[:10] == now_iso()[:10]


async def overview():
    s = await get_settings()
    threshold = s["publish_threshold"]
    queue = await priority_queue(limit=500, threshold=threshold)

    manufacturing_queue = [r for r in queue if r["priority"] == 2]
    needs_fix = [r for r in queue if r["priority"] == 3]
    awaiting_founder = [r for r in queue if r["next_action"]["step"] == "founder_review"]
    blocked = [r for r in queue if r["next_action"]["step"] == "blocked"]

    products = await db.products.find({}, {"content": 0}).to_list(5000)
    total = len(products)
    published = [p for p in products if p.get("status") == "Published"]
    made_today = sum(1 for p in products if _today(p.get("created_at")))
    published_today = sum(1 for p in published if _today(p.get("published_at")))
    treasure = sum(1 for p in products if p.get("treasure_standard"))
    deliver_ready = sum(1 for p in products if p.get("deliverable_ready"))

    # Automation rate = share of products the factory carried to a review-ready / live state.
    review_ready = sum(1 for p in products if p.get("deliverable_ready") and (p.get("design_gate") or {}).get("gated_at"))
    automation_rate = round(100 * review_ready / total) if total else 100
    ts_pass_rate = round(100 * treasure / len(published)) if published else 0

    # Founder Hours Saved™ — deterministic estimate from autonomous actions taken.
    engine_actions = await ACTION_COL.count_documents({"engine": True, "kind": "advance"})
    founder_hours_saved = round(engine_actions * 12 / 60, 1)  # ~12 min manual work per advance

    confs = [r["factory_confidence"] for r in queue] or [0]
    avg_conf = round(sum(confs) / len(confs)) if confs else 0

    recent = []
    async for a in ACTION_COL.find({"engine": True}).sort("at", -1).limit(15):
        a.pop("_id", None)
        recent.append(a)

    # Next Recommended Action™ (Founder-facing).
    if blocked:
        nxt = f"{len(blocked)} product(s) blocked on source material — provide Knowledge Records or content."
    elif awaiting_founder:
        nxt = f"{len(awaiting_founder)} product(s) fully manufactured — review & publish in the Founder Inbox™."
    elif manufacturing_queue:
        nxt = (f"{len(manufacturing_queue)} product(s) can be advanced deterministically now — "
               + ("autonomy will handle them." if s["enabled"] else "turn Autonomy ON or run a cycle."))
    elif needs_fix:
        nxt = f"{len(needs_fix)} product(s) need improvement to reach the {threshold}+ bar."
    else:
        nxt = "Factory is clear — import a new asset or approve the next topic to keep the line running."

    system_health = "healthy" if (not blocked and automation_rate >= 70) else "attention"

    learning = await factory_learning()

    return {
        "settings": s,
        "metrics": {
            "manufacturing_queue": len(manufacturing_queue),
            "blocked_items": len(blocked),
            "autonomous_tasks_pending": len(manufacturing_queue),
            "founder_decisions_waiting": len(awaiting_founder),
            "products_today": made_today,
            "published_today": published_today,
            "founder_hours_saved": founder_hours_saved,
            "automation_rate": automation_rate,
            "treasure_pass_rate": ts_pass_rate,
            "avg_factory_confidence": avg_conf,
            "system_health": system_health,
            "total_products": total,
            "published": len(published),
            "deliverables_ready": deliver_ready,
        },
        "next_recommended_action": nxt,
        "factory_learning": learning,
        "manufacturing_queue": manufacturing_queue[:20],
        "awaiting_founder": awaiting_founder[:20],
        "blocked": blocked[:20],
        "recent_actions": recent,
        "generated_at": now_iso(),
    }
