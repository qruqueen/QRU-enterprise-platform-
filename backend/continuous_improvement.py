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

from emergentintegrations.llm.chat import LlmChat, UserMessage

from database import db
from ai_service import EMERGENT_LLM_KEY, MODEL
from models import now_iso
import qiks

logger = logging.getLogger("qru.continuous")

ACTION_COL = db["autonomy_actions"]
AAR_COL = db["after_action_reviews"]

_capacity = {"available": False, "reason": "not yet probed", "checked_at": None}
_PROBE_TTL_SECONDS = 600  # re-probe at most every 10 minutes


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
    """Cheap check: is AI text capacity available right now?"""
    if not force and _age_seconds(_capacity["checked_at"]) < _PROBE_TTL_SECONDS:
        return dict(_capacity)
    available, reason = False, "unknown"
    try:
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id="capacity-probe",
                       system_message="Reply with the single word OK.").with_model(*MODEL)
        resp = await chat.send_message(UserMessage(text="OK"))
        available, reason = True, "AI capacity available"
        logger.info("Capacity probe: AVAILABLE")
    except Exception as e:
        msg = str(e)
        if "spend limit" in msg.lower():
            reason = "Daily spend limit reached (resets on daily cycle)"
        elif "Budget has been exceeded" in msg:
            reason = "Budget exceeded — add balance"
        else:
            reason = f"Transient/unknown: {msg[:120]}"
        logger.info(f"Capacity probe: BLOCKED — {reason}")
    _capacity.update({"available": available, "reason": reason, "checked_at": now_iso()})
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


ENTERPRISE_FIRST_CHECKLIST = [
    "What is my objective?",
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
        "watcher": {"interval_seconds": 180, "running": True,
                    "policy": "Auto-resume safe jobs when capacity returns; escalated/high-impact work always requires the Founder."},
    }


# ---------------- Background watcher ----------------
async def watcher_loop():
    """Periodically probe capacity, auto-resume safe jobs, and review completed batches."""
    await asyncio.sleep(20)  # let startup settle
    while True:
        try:
            await auto_resume_safe_jobs()
            await review_completed_batches()
        except Exception as e:
            logger.warning(f"watcher loop error: {e}")
        await asyncio.sleep(180)
