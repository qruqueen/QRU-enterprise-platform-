"""QRU Universal Distribution Framework™ — Engines (MO-007).

Four engines over the Connector SDK™, sharing one job ledger (db.distribution_jobs):
  • PublishingEngine™  — sends products to public platforms.
  • DeliveryEngine™    — sends products to customers / schools / storage.
  • VerificationEngine™— confirms delivery and stores canonical external IDs.
  • AnalyticsEngine™   — collects performance data from connected platforms.

One consistent workflow: Manufacture → QC → Render → DISTRIBUTE (publish/deliver) → VERIFY →
Store external IDs → Analytics. Every step is audited; nothing is marked done without a real ID.
"""
import logging

from database import db
from models import now_iso, gen_id
from .sdk import ConnectorKind, DistStatus
from .connectors import REGISTRY, get_connector

logger = logging.getLogger("qru.distribution")
MAX_ATTEMPTS = 3


def _clean(doc):
    doc.pop("_id", None)
    return doc


async def list_connectors():
    """All registered connectors with live connection status + capabilities."""
    out = []
    for cid, c in REGISTRY.items():
        try:
            status = await c.connection_status()
        except Exception as e:
            status = {"connected": False, "can_distribute": False, "reason": str(e)[:120]}
        cap = c.capability
        out.append({**cap.__dict__, **status})
    return out


async def _record_job(product, connector, mode, options, actor):
    job = {
        "id": gen_id(), "product_id": product["id"], "product_title": product.get("title"),
        "connector_id": connector.capability.id, "connector_name": connector.capability.name,
        "kind": connector.capability.kind, "mode": mode, "options": {k: v for k, v in (options or {}).items() if k != "actor"},
        "status": DistStatus.QUEUED.value, "attempts": 0, "external_id": None, "url": None,
        "verified": False, "detail": "", "last_error": None,
        "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.distribution_jobs.insert_one(dict(job))
    return job


async def _run_job(job_id):
    """Execute (or retry) a single distribution job through its connector."""
    job = await db.distribution_jobs.find_one({"id": job_id})
    if not job:
        return None
    connector = get_connector(job["connector_id"])
    product = await db.products.find_one({"id": job["product_id"]})
    if not connector or not product:
        await db.distribution_jobs.update_one({"id": job_id}, {"$set": {
            "status": DistStatus.FAILED.value, "last_error": "Connector or product missing.", "updated_at": now_iso()}})
        return await db.distribution_jobs.find_one({"id": job_id})

    meta = connector.map_metadata(product, (job.get("options") or {}).get("meta"))
    attempts = job.get("attempts", 0) + 1
    try:
        res = await connector.distribute(product, meta, job["mode"], {**(job.get("options") or {}), "actor": job.get("created_by")})
    except Exception as e:
        logger.exception("distribution job failed")
        res = None
        err = str(e)[:300]
    else:
        err = None if res.ok else res.detail

    update = {"attempts": attempts, "updated_at": now_iso()}
    if res and res.ok:
        update.update({"status": res.status, "external_id": res.external_id, "url": res.url,
                       "verified": res.verified, "detail": res.detail, "last_error": None,
                       "extra": res.extra})
    elif res and res.status == DistStatus.NEEDS_SETUP.value:
        update.update({"status": DistStatus.NEEDS_SETUP.value, "detail": res.detail, "last_error": None})
    else:
        update.update({"status": DistStatus.FAILED.value,
                       "last_error": err or "Unknown error", "detail": (res.detail if res else err) or ""})
    await db.distribution_jobs.update_one({"id": job_id}, {"$set": update})

    try:
        from org_activity import log_org
        ok = bool(res and res.ok)
        await log_org("QRU Distribution Framework™", "Distribution",
                      f"{'distributed' if ok else 'attempted distribution of'} via {job['connector_name']} —",
                      job.get("product_title") or "", "success" if ok else "warning")
    except Exception:
        pass
    return await db.distribution_jobs.find_one({"id": job_id})


async def distribute(product_id, targets, actor):
    """Create + run distribution jobs for a product across one or more connectors.
    `targets` = [{connector_id, mode, options?}]. Publishing vs Delivery is chosen by connector kind."""
    product = await db.products.find_one({"id": product_id})
    if not product:
        return {"error": "Product not found."}
    jobs = []
    for t in targets:
        connector = get_connector(t.get("connector_id"))
        if not connector:
            jobs.append({"connector_id": t.get("connector_id"), "status": "failed", "detail": "Unknown connector."})
            continue
        job = await _record_job(product, connector, t.get("mode", "private"), t.get("options"), actor)
        result = await _run_job(job["id"])
        jobs.append(_clean(result))
    published = sum(1 for j in jobs if j.get("status") in (DistStatus.PUBLISHED.value, DistStatus.DELIVERED.value, DistStatus.SCHEDULED.value))
    return {"product_id": product_id, "jobs": jobs,
            "distributed": published, "failed": sum(1 for j in jobs if j.get("status") == DistStatus.FAILED.value),
            "needs_setup": sum(1 for j in jobs if j.get("status") == DistStatus.NEEDS_SETUP.value)}


async def retry_job(job_id):
    """Retry a failed job (VerificationEngine/retry logic)."""
    job = await db.distribution_jobs.find_one({"id": job_id})
    if not job:
        return {"error": "Job not found."}
    if job.get("attempts", 0) >= MAX_ATTEMPTS:
        return {"error": f"Maximum retry attempts ({MAX_ATTEMPTS}) reached for this job."}
    return _clean(await _run_job(job_id))


async def verify_job(job_id):
    """VerificationEngine™ — confirm the distribution is live and store the canonical external ID."""
    job = await db.distribution_jobs.find_one({"id": job_id})
    if not job:
        return {"error": "Job not found."}
    if not job.get("external_id"):
        return {"error": "No external ID to verify — the job has not distributed yet."}
    connector = get_connector(job["connector_id"])
    res = await connector.verify(job["external_id"], job.get("options") or {})
    await db.distribution_jobs.update_one({"id": job_id}, {"$set": {
        "verified": res.verified, "url": res.url or job.get("url"),
        "detail": res.detail, "verified_at": now_iso(), "updated_at": now_iso()}})
    return {"verified": res.verified, "external_id": res.external_id, "url": res.url, "detail": res.detail}


async def job_analytics(job_id):
    """AnalyticsEngine™ — collect real performance data from the platform where supported."""
    job = await db.distribution_jobs.find_one({"id": job_id})
    if not job:
        return {"error": "Job not found."}
    if not job.get("external_id"):
        return {"supported": False, "note": "No external ID yet."}
    connector = get_connector(job["connector_id"])
    return await connector.fetch_analytics(job["external_id"], job.get("options") or {})


async def list_jobs(product_id=None, limit=200):
    q = {"product_id": product_id} if product_id else {}
    rows = await db.distribution_jobs.find(q).sort("created_at", -1).to_list(limit)
    return [_clean(r) for r in rows]
