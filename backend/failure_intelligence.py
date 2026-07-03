"""MT-034 — QRU Production Failure Intelligence™.

The QRU Factory™ must never simply report "Failed." Every Production Run records and
explains exactly WHY it failed, WHAT it means, and WHAT to do next — with a one-click
fix when possible. Deterministic — needs no LLM budget.

Scans the existing manufacturing_batches (Orchestrator) and workflow_jobs (Workflow
Engine) — no new run store; this is a read/diagnose + checkpoint-retry layer.
"""
import logging

from database import db
from models import now_iso, clean

logger = logging.getLogger("qru.failure_intel")

# Dashboard "waiting on…" buckets.
BUCKET_FOUNDER = "waiting_on_founder"
BUCKET_ASSETS = "waiting_on_assets"
BUCKET_KNOWLEDGE = "waiting_on_knowledge"
BUCKET_AI = "waiting_on_ai"
BUCKET_EXTERNAL = "waiting_on_external"
BUCKET_NONE = "actionable"

# Root-cause catalog. Each entry: label, bucket, explanation, resolution, action(one-click fix).
FAILURE_CLASSES = {
    "TOPIC_SEED_ONLY": {
        "label": "Topic Seed Only",
        "bucket": BUCKET_KNOWLEDGE,
        "explanation": "The required Knowledge Record is still a Topic Seed and has no verified content to manufacture from.",
        "resolution": "Upload the Founder source document, then promote the Topic Seed to a Verified Knowledge Record™.",
        "action": {"label": "Open Promotion Pipeline™", "route": "/promotion-pipeline", "testid": "fix-open-promotion"},
    },
    "KR_NOT_READY": {
        "label": "Knowledge Record Not Ready",
        "bucket": BUCKET_KNOWLEDGE,
        "explanation": "The Knowledge Record exists but is not verified / not ready for manufacturing.",
        "resolution": "Verify the Knowledge Record in the Verification Center, or promote/complete it first.",
        "action": {"label": "Open Verification Center", "route": "/verification", "testid": "fix-open-verification"},
    },
    "MISSING_KNOWLEDGE_RECORD": {
        "label": "Missing Knowledge Record",
        "bucket": BUCKET_KNOWLEDGE,
        "explanation": "No Knowledge Record is linked to this run — there is nothing verified to manufacture.",
        "resolution": "Create or select a Verified Knowledge Record before manufacturing.",
        "action": {"label": "Open Knowledge Records", "route": "/knowledge", "testid": "fix-open-knowledge"},
    },
    "MISSING_SOURCE_FILE": {
        "label": "Missing Source File",
        "bucket": BUCKET_ASSETS,
        "explanation": "A required Founder source document has not been uploaded.",
        "resolution": "Upload the source document, then promote the Topic Seed to a Verified Knowledge Record™.",
        "action": {"label": "Open Promotion Pipeline™", "route": "/promotion-pipeline", "testid": "fix-open-promotion"},
    },
    "MISSING_FOUNDER_ASSET": {
        "label": "Missing Founder Asset",
        "bucket": BUCKET_ASSETS,
        "explanation": "The run required a Founder-selected imported asset that is not available.",
        "resolution": "Import or select the asset in the Asset Vault™, or switch the run to generate a new asset.",
        "action": {"label": "Open Asset Vault™", "route": "/asset-vault", "testid": "fix-open-vault"},
    },
    "MISSING_ASSET_VAULT": {
        "label": "Missing Asset Vault Resource",
        "bucket": BUCKET_ASSETS,
        "explanation": "A referenced Asset Vault™ resource could not be found.",
        "resolution": "Re-import the asset into the Asset Vault™ or choose a different approved asset.",
        "action": {"label": "Open Asset Vault™", "route": "/asset-vault", "testid": "fix-open-vault"},
    },
    "LLM_DAILY_LIMIT": {
        "label": "LLM Daily Spend Limit Reached",
        "bucket": BUCKET_AI,
        "explanation": "The Universal LLM key hit its daily spend limit, so AI generation could not run.",
        "resolution": "Wait for the daily reset or increase the Universal LLM daily spending limit. Auto-Resume™ will finish this automatically when capacity returns.",
        "action": {"label": "Retry Manufacturing", "route": "__retry__", "testid": "fix-retry"},
    },
    "BUDGET_EXCEEDED": {
        "label": "LLM Budget Exceeded",
        "bucket": BUCKET_AI,
        "explanation": "The Universal LLM key balance is exhausted.",
        "resolution": "Add balance in Profile → Universal Key → Add Balance, then retry.",
        "action": {"label": "Retry Manufacturing", "route": "__retry__", "testid": "fix-retry"},
    },
    "AI_PROVIDER_ERROR": {
        "label": "AI Provider Error",
        "bucket": BUCKET_AI,
        "explanation": "The AI provider returned a transient error (rate limit / 503 / timeout).",
        "resolution": "Automatic retry with backoff usually clears this. Retry now if needed.",
        "action": {"label": "Retry Manufacturing", "route": "__retry__", "testid": "fix-retry"},
    },
    "MISSING_API_KEY": {
        "label": "Missing API Key",
        "bucket": BUCKET_EXTERNAL,
        "explanation": "A required API key/credential is missing or invalid for an external service.",
        "resolution": "Add the missing credential in the Integration Hub™, then retry.",
        "action": {"label": "Open Integration Hub™", "route": "/integration-hub", "testid": "fix-open-integrations"},
    },
    "NETWORK_ERROR": {
        "label": "Network Error",
        "bucket": BUCKET_EXTERNAL,
        "explanation": "A network/connection error prevented the run from completing.",
        "resolution": "Check connectivity to the external service and retry.",
        "action": {"label": "Retry Manufacturing", "route": "__retry__", "testid": "fix-retry"},
    },
    "RENDERING_FAILURE": {
        "label": "Rendering Failure",
        "bucket": BUCKET_NONE,
        "explanation": "The deliverable renderer could not produce a customer-ready file.",
        "resolution": "Re-render the deliverable; if it persists, review the Manufacturing Recipe™ for this product type.",
        "action": {"label": "Retry Manufacturing", "route": "__retry__", "testid": "fix-retry"},
    },
    "DESIGN_REVIEW_FAILED": {
        "label": "Design Review Failed",
        "bucket": BUCKET_NONE,
        "explanation": "The rendered product did not meet the Treasure Standard™ design threshold.",
        "resolution": "Return to Creative Studio™ to improve the design, then re-render.",
        "action": {"label": "Open Creative Studio™", "route": "/creative-studio", "testid": "fix-open-creative"},
    },
    "PUBLICATION_GATE_FAILED": {
        "label": "Publication Gate Failed",
        "bucket": BUCKET_NONE,
        "explanation": "A release gate (verification, protection, deliverable, or content review) blocked publication.",
        "resolution": "Resolve the failing gate in Manufacturing Studio / Product Protection™, then republish.",
        "action": {"label": "Open Manufacturing Studio", "route": "/manufacturing-studio", "testid": "fix-open-mfg-studio"},
    },
    "MISSING_RECIPE": {
        "label": "Missing Manufacturing Recipe",
        "bucket": BUCKET_NONE,
        "explanation": "No Product Manufacturing Recipe™ was found for this product type.",
        "resolution": "Select a supported product type, or add a Recipe™ for this type.",
        "action": {"label": "Open Product Manufacturing", "route": "/manufacture", "testid": "fix-open-manufacture"},
    },
    "VERIFICATION_FAILED": {
        "label": "Verification Failed",
        "bucket": BUCKET_FOUNDER,
        "explanation": "The AI Verification Team could not verify the content and escalated it.",
        "resolution": "Review in the Verification Center — a Founder judgment is required.",
        "action": {"label": "Open Verification Center", "route": "/verification", "testid": "fix-open-verification"},
    },
    "WAITING_ON_FOUNDER": {
        "label": "Escalated to Founder",
        "bucket": BUCKET_FOUNDER,
        "explanation": "This item was escalated for a governance / quality judgment.",
        "resolution": "Review the escalation and decide — the factory holds this item safely.",
        "action": {"label": "Open Verification Team™", "route": "/verification-team", "testid": "fix-open-verification-team"},
    },
    "UNKNOWN_ERROR": {
        "label": "Unknown Error",
        "bucket": BUCKET_NONE,
        "explanation": "The run failed without a recognized root cause.",
        "resolution": "Retry with logging; if it persists, inspect the run logs.",
        "action": {"label": "Retry Manufacturing", "route": "__retry__", "testid": "fix-retry"},
    },
}


def classify(error_text: str, kr_class: str = None, has_kr: bool = True, stage: str = "") -> str:
    """Return a FAILURE_CLASSES code from the failure context."""
    e = (error_text or "").lower()
    s = (stage or "").lower()
    # AI capacity / external first (most common right now).
    if "spend limit" in e or ("daily" in e and "limit" in e):
        return "LLM_DAILY_LIMIT"
    if "budget" in e:
        return "BUDGET_EXCEEDED"
    if "api key" in e or "unauthorized" in e or "401" in e or "invalid_api_key" in e or "authentication" in e:
        return "MISSING_API_KEY"
    if any(k in e for k in ("503", "rate limit", "ratelimit", "unavailable", "timeout", "timed out",
                            "connection", "network", "getaddrinfo", "econnreset")):
        return "AI_PROVIDER_ERROR" if any(k in e for k in ("503", "rate", "unavailable", "timeout")) else "NETWORK_ERROR"
    # Knowledge dependency.
    if kr_class == "Topic Seed":
        return "TOPIC_SEED_ONLY"
    if not has_kr and ("knowledge" in e or "kr" in s or not e):
        return "MISSING_KNOWLEDGE_RECORD"
    if "not ready" in e or "not verified" in e:
        return "KR_NOT_READY"
    if "source file" in e or "source document" in e or "manuscript" in e:
        return "MISSING_SOURCE_FILE"
    if "founder asset" in e:
        return "MISSING_FOUNDER_ASSET"
    if "vault" in e or "asset" in e and "missing" in e:
        return "MISSING_ASSET_VAULT"
    if "recipe" in e:
        return "MISSING_RECIPE"
    if "design review" in e or "design threshold" in e:
        return "DESIGN_REVIEW_FAILED"
    if "render" in e:
        return "RENDERING_FAILURE"
    if "gate" in e or "release" in e or "publish" in e:
        return "PUBLICATION_GATE_FAILED"
    if "escalat" in e or "escalat" in s:
        return "WAITING_ON_FOUNDER"
    if "verif" in e:
        return "VERIFICATION_FAILED"
    if not e:
        return "UNKNOWN_ERROR"
    return "UNKNOWN_ERROR"


def _diagnosis(code: str, error_text: str, title: str):
    meta = FAILURE_CLASSES.get(code, FAILURE_CLASSES["UNKNOWN_ERROR"])
    return {
        "code": code,
        "title": title,
        "root_cause": meta["label"],
        "bucket": meta["bucket"],
        "explanation": meta["explanation"],
        "resolution": meta["resolution"],
        "action": meta["action"],
        "raw_error": (error_text or "")[:300],
    }


async def _kr_class_map(kr_ids):
    out = {}
    ids = [k for k in kr_ids if k]
    if not ids:
        return out
    async for k in db.knowledge_records.find({"id": {"$in": ids}}, {"id": 1, "record_class": 1, "verification_status": 1}):
        out[k["id"]] = k.get("record_class") or ("Imported Verified" if k.get("verification_status") == "Verified" else None)
    return out


async def analyze():
    """Full Production Failure Intelligence™ — dashboard counts + per-run diagnoses."""
    dashboard = {
        "total_runs": 0, "successful": 0, "failed": 0, "in_progress": 0, "paused": 0,
        BUCKET_FOUNDER: 0, BUCKET_ASSETS: 0, BUCKET_KNOWLEDGE: 0, BUCKET_AI: 0, BUCKET_EXTERNAL: 0,
    }
    runs = []

    batches = await db.manufacturing_batches.find().sort("created_at", -1).to_list(500)
    all_kr_ids = [it.get("kr_id") for b in batches for it in b.get("items", [])]
    kr_map = await _kr_class_map(all_kr_ids)

    for b in batches:
        dashboard["total_runs"] += 1
        status = b.get("status", "")
        if status == "running":
            dashboard["in_progress"] += 1
        elif status == "paused":
            dashboard["paused"] += 1
        elif status in ("completed",) and b.get("failed", 0) == 0 and b.get("escalated", 0) == 0:
            dashboard["successful"] += 1
        elif b.get("failed", 0) > 0 or status in ("failed", "completed_with_errors"):
            dashboard["failed"] += 1
        elif b.get("escalated", 0) > 0:
            pass

        failures = []
        seen_buckets = set()
        for it in b.get("items", []):
            st = it.get("status")
            if st not in ("failed", "escalated"):
                continue
            err = it.get("error")
            if st == "escalated":
                code = "WAITING_ON_FOUNDER"
            else:
                code = classify(err, kr_map.get(it.get("kr_id")), bool(it.get("kr_id")), it.get("stage"))
            diag = _diagnosis(code, err, it.get("topic_name", "?"))
            failures.append(diag)
            seen_buckets.add(diag["bucket"])
        for bkt in seen_buckets:
            if bkt in dashboard:
                dashboard[bkt] += 1

        if failures or status in ("failed", "completed_with_errors", "paused", "running"):
            runs.append({
                "run_id": b["id"], "source": "Orchestrator", "name": b.get("name"),
                "status": status, "total": b.get("total", 0), "done": b.get("completed", 0),
                "failed": b.get("failed", 0), "escalated": b.get("escalated", 0),
                "retryable": b.get("failed", 0) > 0,
                "primary_diagnosis": failures[0] if failures else None,
                "failures": failures,
            })

    # Workflow Engine jobs
    async for j in db.workflow_jobs.find({"status": {"$in": ["failed", "completed_with_errors", "escalated", "running"]}}).sort("created_at", -1):
        dashboard["total_runs"] += 1
        status = j.get("status", "")
        if status == "running":
            dashboard["in_progress"] += 1
        elif status in ("failed", "completed_with_errors"):
            dashboard["failed"] += 1
        failures = []
        seen_buckets = set()
        for p in j.get("products", []):
            if p.get("status") != "failed":
                continue
            code = classify(p.get("error"), None, bool(j.get("kr_id")), j.get("stage"))
            diag = _diagnosis(code, p.get("error"), p.get("product_type", "?"))
            failures.append(diag)
            seen_buckets.add(diag["bucket"])
        for e in j.get("errors", []) or []:
            code = classify(e if isinstance(e, str) else str(e), None, bool(j.get("kr_id")), j.get("stage"))
            failures.append(_diagnosis(code, e if isinstance(e, str) else str(e), "Workflow error"))
            seen_buckets.add(FAILURE_CLASSES[code]["bucket"])
        for bkt in seen_buckets:
            if bkt in dashboard:
                dashboard[bkt] += 1
        runs.append({
            "run_id": j["id"], "source": "Workflow", "name": j.get("job_number", j.get("id")),
            "status": status, "total": len(j.get("products", [])),
            "done": sum(1 for p in j.get("products", []) if p.get("status") in ("published", "done")),
            "failed": sum(1 for p in j.get("products", []) if p.get("status") == "failed"),
            "escalated": 0, "retryable": False,
            "primary_diagnosis": failures[0] if failures else None,
            "failures": failures,
        })

    return {"dashboard": dashboard, "runs": runs, "failure_classes": {k: v["label"] for k, v in FAILURE_CLASSES.items()}}


async def retry_run(run_id: str):
    """Checkpoint retry — re-run only the FAILED items (never restarts completed work)."""
    b = await db.manufacturing_batches.find_one({"id": run_id})
    if b:
        import orchestrator as orch
        res = await orch.retry_failed(run_id)
        return {"ok": True, "source": "Orchestrator", "message": "Retrying failed topics from the last checkpoint.",
                "status": res.get("status") if res else None}
    j = await db.workflow_jobs.find_one({"id": run_id})
    if j:
        return {"ok": False, "source": "Workflow",
                "message": "Workflow jobs auto-recover via the Safe Auto-Resume™ watcher when AI capacity returns."}
    return {"ok": False, "message": "Run not found."}
