"""
QRU ENTERPRISE AUTONOMY & CONTINUOUS IMPROVEMENT™

  • Capacity Probe™ — detects when AI capacity returns (daily cap / budget cleared).
  • Safe Auto-Resume™ — finishes paused/failed manufacturing automatically when it is safe,
    WITHOUT Founder intervention (Phase C completes itself when capacity returns).
  • After-Action Review™ — every completed batch produces lessons that feed QIKS.
  • Enterprise Diagnostics™ — every failed job gets root cause, recovery recommendation,
    retry status, dependency status, estimated resolution, and a confidence score.

Governance is preserved: high-impact / escalated items still require the Founder.
"""
import asyncio
import logging
from datetime import datetime, timezone

from database import db
from ai_service import EMERGENT_LLM_KEY
from models import now_iso
import qiks

logger = logging.getLogger("qru.continuous")

ACTION_COL = db["autonomy_actions"]
AAR_COL = db["after_action_reviews"]
SETTINGS_COL = db["settings"]
_SETTING_ID = "continuous_improvement"
_watcher_task = None

_capacity = {"available": False, "reason": "not yet probed", "checked_at": None}
_PROBE_TTL_SECONDS = 600  # retained for API compatibility (no longer gates any AI call)


# ---------------- Founder-controlled on/off switch (default OFF) ----------------
async def is_enabled():
    """Continuous Improvement is OFF unless the Founder has explicitly turned it on.
    Defaults to OFF in every environment (production and preview) — the flag lives in the
    database and is absent by default, so this returns False."""
    doc = await SETTINGS_COL.find_one({"id": _SETTING_ID})
    return bool(doc and doc.get("enabled"))


def watcher_running():
    return _watcher_task is not None and not _watcher_task.done()


def start_watcher():
    """Start the deterministic watcher task. Only ever invoked by an explicit Founder toggle —
    NEVER on server/preview startup."""
    global _watcher_task
    if watcher_running():
        return False
    _watcher_task = asyncio.create_task(watcher_loop())
    logger.info("Continuous Improvement watcher STARTED by Founder toggle.")
    return True


def stop_watcher():
    global _watcher_task
    if _watcher_task is not None and not _watcher_task.done():
        _watcher_task.cancel()
        logger.info("Continuous Improvement watcher STOPPED by Founder toggle.")
    _watcher_task = None
    return True


async def set_enabled(enabled, actor="Founder"):
    await SETTINGS_COL.update_one(
        {"id": _SETTING_ID},
        {"$set": {"id": _SETTING_ID, "enabled": bool(enabled), "updated_by": actor, "updated_at": now_iso()}},
        upsert=True)
    if enabled:
        start_watcher()
    else:
        stop_watcher()
    logger.info(f"Continuous Improvement set to {'ON' if enabled else 'OFF'} by {actor}.")
    return {"enabled": bool(enabled), "watcher_running": watcher_running()}


def _age_seconds(ts):
    if not ts:
        return 1e9
    try:
        d = datetime.fromisoformat(str(ts))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - d).total_seconds()
    except Exception:
        return 1e9


async def probe_capacity(force=False):
    """DETERMINISTIC capacity check — makes NO external AI call.

    Previously this sent a live LLM 'OK' probe to the provider, which spent credits and ran
    autonomously from the background watcher. That AI call has been removed: capacity is now
    reported purely from deterministic local state (whether a Universal Key is configured), so
    starting the server/preview or polling status never triggers a paid AI call."""
    available = bool(EMERGENT_LLM_KEY)
    reason = ("Universal Key configured (deterministic check — no AI call made)"
              if available else "No Universal Key configured")
    _capacity.update({"available": available, "reason": reason, "checked_at": now_iso(),
                      "deterministic": True})
    return dict(_capacity)


async def _record_action(kind, target, detail):
    await ACTION_COL.insert_one({"kind": kind, "target": target, "detail": detail, "at": now_iso()})


async def auto_resume_safe_jobs(force_probe=False):
    """When capacity is available, safely resume paused batches and retry failed batch items.
    Founder-escalated work is never auto-resumed."""
    cap = await probe_capacity(force=force_probe)
    if not cap["available"]:
        return {"resumed": [], "capacity": cap, "note": "AI capacity unavailable — jobs remain safely paused."}
    import orchestrator as orch
    resumed = []
    async for b in db.manufacturing_batches.find({"status": {"$in": ["paused"]}}):
        try:
            await orch.resume_batch(b["id"])
            resumed.append({"batch_id": b["id"], "name": b.get("name"), "action": "resumed"})
            await _record_action("auto_resume", b["id"], f"Resumed paused batch '{b.get('name')}'")
        except Exception as e:
            logger.warning(f"auto-resume failed for {b['id']}: {e}")
    async for b in db.manufacturing_batches.find({"failed": {"$gt": 0}, "status": {"$nin": ["running", "paused"]}}):
        try:
            await orch.retry_failed(b["id"])
            resumed.append({"batch_id": b["id"], "name": b.get("name"), "action": "retried_failed"})
            await _record_action("auto_retry", b["id"], f"Retried {b.get('failed')} failed topic(s) in '{b.get('name')}'")
        except Exception as e:
            logger.warning(f"auto-retry failed for {b['id']}: {e}")
    return {"resumed": resumed, "capacity": cap}


# ---------------- After-Action Review™ ----------------
async def after_action_review(batch):
    """Deterministic AAR for a completed batch → lessons that can feed QIKS."""
    items = batch.get("items", [])
    done = [i for i in items if i.get("status") == "done"]
    failed = [i for i in items if i.get("status") == "failed"]
    escalated = [i for i in items if i.get("status") == "escalated"]
    findings = {
        "what_succeeded": f"{len(done)}/{len(items)} topics manufactured to standard.",
        "what_failed": (f"{len(failed)} topic(s) failed: " + ", ".join(i.get("title", "?") for i in failed[:5])) if failed else "No failures.",
        "escalations": f"{len(escalated)} escalated to the Founder." if escalated else "No escalations.",
        "reusable_recipe": "This batch template performed well — reuse it." if not failed else "Review recipes for the failed topics before reuse.",
        "should_update_standards": bool(failed),
        "should_expand_knowledge": len(done) > 0,
    }
    review = {
        "id": f"AAR-{batch['id']}",
        "batch_id": batch["id"],
        "batch_name": batch.get("name"),
        "total": len(items), "done": len(done), "failed": len(failed), "escalated": len(escalated),
        "findings": findings,
        "reviewed_at": now_iso(),
    }
    await AAR_COL.update_one({"id": review["id"]}, {"$set": review}, upsert=True)
    # Feed a lesson to QIKS (pending Founder approval) when there is something to learn.
    if failed:
        await qiks.add_lesson(
            title=f"Batch '{batch.get('name')}' had {len(failed)} failure(s)",
            division="Manufacturing",
            lesson=f"Topics failed: {', '.join(i.get('title','?') for i in failed[:5])}. Recommend reviewing recipes/dependencies before reusing this template.",
            source=f"After-Action Review {review['id']}",
            reviewer="Factory Council™",
        )
    return review


async def review_completed_batches():
    """Run AAR on completed batches not yet reviewed."""
    reviewed = []
    async for b in db.manufacturing_batches.find({"status": {"$in": ["completed", "completed_with_errors"]}}):
        if await AAR_COL.find_one({"id": f"AAR-{b['id']}"}):
            continue
        r = await after_action_review(b)
        reviewed.append(r["id"])
    return reviewed


# ---------------- Enterprise Diagnostics™ ----------------
def _classify(error_text):
    e = (error_text or "").lower()
    if "spend limit" in e or "daily" in e:
        return ("AI daily spend limit reached", "Wait for the daily cap to reset; the auto-resume watcher will finish this automatically.", "Blocked (external)", 0.95, "On daily reset")
    if "budget" in e:
        return ("AI budget exceeded", "Add balance to the Universal Key, then auto-resume will retry.", "Blocked (external)", 0.95, "After balance top-up")
    if "503" in e or "unavailable" in e or "rate" in e:
        return ("Transient rate-limit / 503 burst", "Automatic retry with backoff at lower concurrency.", "Retryable", 0.8, "Minutes")
    if "verif" in e or "escalat" in e:
        return ("Verification exception requiring judgment", "Founder review required — governance decision.", "Escalated to Founder", 0.7, "Awaiting Founder")
    if not e:
        return ("Unknown / no error recorded", "Re-run with logging; monitor next attempt.", "Retryable", 0.5, "Unknown")
    return (f"Manufacturing error: {error_text[:80]}", "Automatic retry; if it persists, review the recipe.", "Retryable", 0.6, "Minutes")


async def failed_job_diagnostics():
    """Every failed job/topic gets a full diagnostic record."""
    diags = []
    # Workflow job failed products
    async for j in db.workflow_jobs.find({"status": {"$in": ["failed", "completed_with_errors", "escalated"]}}):
        for p in j.get("products", []):
            if p.get("status") == "failed":
                rc, rec, retry, conf, eta = _classify(p.get("error"))
                diags.append({
                    "source": "Workflow", "job": j.get("job_number", j.get("id")),
                    "item": p.get("product_type"), "root_cause": rc, "recovery_recommendation": rec,
                    "retry_status": retry, "dependency_status": "KR verified" if j.get("kr_id") else "Missing verified KR",
                    "estimated_resolution": eta, "confidence": conf,
                })
    # Batch failed topics
    async for b in db.manufacturing_batches.find({"failed": {"$gt": 0}}):
        for it in b.get("items", []):
            if it.get("status") == "failed":
                rc, rec, retry, conf, eta = _classify(it.get("error"))
                diags.append({
                    "source": "Batch", "job": b.get("name", b.get("id")),
                    "item": it.get("topic"), "root_cause": rc, "recovery_recommendation": rec,
                    "retry_status": retry, "dependency_status": "In batch queue",
                    "estimated_resolution": eta, "confidence": conf,
                })
    return diags


async def resilience():
    """Factory Resilience™ — which workflows can run RIGHT NOW given current AI capacity.
    Deterministic and hybrid workflows always run; AI-required ones depend on capacity."""
    cap = await probe_capacity(force=False)
    ai_ok = bool(cap["available"])
    wf = [
        {"name": "Translation Engine™ — verified topics", "mode": "deterministic", "available": True},
        {"name": "Translation Engine™ — new topics (AI draft)", "mode": "ai", "available": ai_ok},
        {"name": "Creative Studio™ enhancement", "mode": "hybrid", "available": True, "note": "AI copy when available; on-brand fallback otherwise"},
        {"name": "Verification & Product Protection™", "mode": "hybrid", "available": True, "note": "Deterministic verification + protection always run"},
        {"name": "Product Rendering (covers, PDF, QR)", "mode": "deterministic", "available": True},
        {"name": "Voice narration (OpenAI TTS)", "mode": "ai", "available": ai_ok},
        {"name": "Slideshow video", "mode": "hybrid", "available": True, "note": "Silent branded slideshow when narration unavailable"},
        {"name": "Bulk manufacturing (Orchestrator)", "mode": "ai", "available": ai_ok},
    ]
    return {
        "capacity": cap,
        "workflows": wf,
        "runnable_now": sum(1 for w in wf if w["available"]),
        "total": len(wf),
        "message": "All core workflows operational — deterministic and hybrid flows keep manufacturing even during provider outages." if not ai_ok
                   else "Full capacity — every workflow is operational.",
    }


ENTERPRISE_FIRST_CHECKLIST = [    "What is my objective?",
    "What enterprise standards apply?",
    "What institutional knowledge already exists?",
    "What assets can be reused?",
    "Which departments should be involved?",
    "Which AI Directors should participate?",
    "Which workflows should execute?",
    "Which products should be manufactured?",
    "What lessons should be returned to Institutional Knowledge?",
    "How can this make the factory better for the next manufacturing order?",
]


async def overview():
    cap = dict(_capacity)
    actions = []
    async for a in ACTION_COL.find().sort("at", -1).limit(20):
        a.pop("_id", None)
        actions.append(a)
    aars = []
    async for r in AAR_COL.find().sort("reviewed_at", -1).limit(10):
        r.pop("_id", None)
        aars.append(r)
    diags = await failed_job_diagnostics()
    return {
        "capacity": cap,
        "auto_resume_actions": actions,
        "after_action_reviews": aars,
        "diagnostics": diags,
        "diagnostics_count": len(diags),
        "enterprise_first_checklist": ENTERPRISE_FIRST_CHECKLIST,
        "watcher": {"interval_seconds": 180, "running": watcher_running(), "enabled": await is_enabled(),
                    "policy": "OFF by default. When the Founder turns it ON, the watcher runs ONLY "
                              "deterministic After-Action Reviews — it makes no AI calls and never "
                              "resumes manufacturing automatically. Resuming jobs is Founder-controlled."},
    }


# ---------------- Background watcher (Founder-controlled; OFF by default) ----------------
async def watcher_loop():
    """Deterministic housekeeping loop. Started ONLY by an explicit Founder toggle — never on boot.
    It performs no external AI calls and NEVER auto-resumes paused/failed/interrupted manufacturing;
    it only runs After-Action Reviews on already-completed batches."""
    await asyncio.sleep(20)  # let startup settle
    while True:
        if not await is_enabled():
            logger.info("Continuous Improvement is OFF — watcher stopping.")
            return
        try:
            # Deterministic only. Auto-resume and the autonomous AI engine are intentionally
            # NOT invoked here: manufacturing is never resumed automatically.
            await review_completed_batches()
        except Exception as e:
            logger.warning(f"watcher loop error: {e}")
        await asyncio.sleep(180)
