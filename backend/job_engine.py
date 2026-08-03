"""QRU Factory Orchestration Spine™ — a durable, restart-proof job engine.

Why this exists: every long-running task in the factory (storybook renders, audiobook renders,
audiobook→video, bulk manufacturing) was previously a fire-and-forget `asyncio.create_task` that
DIED on any server restart/recycle — leaving jobs stuck "running" forever. This engine fixes that:

  • Jobs are PERSISTED in Mongo (`factory_jobs`), so they survive process death.
  • A single worker loop launches on backend startup, LEASES one job at a time with a heartbeat,
    executes its registered handler, and RETRIES with backoff on failure.
  • On startup (and continuously), it RECLAIMS orphaned jobs whose lease expired — i.e. jobs whose
    worker was killed mid-run — and re-queues them. This is what makes the factory restart-proof.
  • Supports scheduled jobs (`run_at`) and recurring jobs (`interval_seconds`) — the seed of
    cron-like autonomy.

Deploy-safe: no new infrastructure (no Redis/Celery). Runs inside the existing FastAPI process and
carries to production automatically.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from database import db
from models import gen_id

logger = logging.getLogger("qru.job_engine")

COLL = "factory_jobs"

POLL_INTERVAL_S = 3        # how often the worker looks for work
LEASE_SECONDS = 90         # a running job must heartbeat within this window or it's reclaimed
HEARTBEAT_S = 25           # how often a running job extends its lease
DEFAULT_MAX_ATTEMPTS = 3
MAX_CONCURRENCY = 2        # run a few durable jobs at once (durable + no unbounded-503/524 bursts)

# Registered handlers: job_type -> async fn(job: dict, progress: callable) -> dict | None
_HANDLERS = {}


def register(job_type, fn):
    _HANDLERS[job_type] = fn
    logger.info(f"[job_engine] registered handler: {job_type}")


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat()


def _now_iso():
    return _iso(_now())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def enqueue(job_type, payload=None, *, title=None, dedupe_key=None, run_at=None,
                  max_attempts=DEFAULT_MAX_ATTEMPTS, priority=0, interval_seconds=None,
                  created_by="System"):
    """Create a durable job. If `dedupe_key` matches an already active (queued/running) job, that
    existing job is returned instead of creating a duplicate."""
    if dedupe_key:
        existing = await db[COLL].find_one({"dedupe_key": dedupe_key,
                                            "status": {"$in": ["queued", "running"]}}, {"_id": 0})
        if existing:
            return existing
    job = {
        "id": gen_id(), "job_type": job_type, "title": title or job_type,
        "payload": payload or {}, "status": "queued", "priority": int(priority),
        "attempts": 0, "max_attempts": int(max_attempts),
        "dedupe_key": dedupe_key, "run_at": run_at or _now_iso(),
        "interval_seconds": interval_seconds,
        "progress": {"done": 0, "total": 0, "message": "Queued"},
        "result": None, "error": None, "logs": [{"at": _now_iso(), "level": "info", "message": "Enqueued"}],
        "lease_until": None, "worker_started_at": None, "finished_at": None,
        "created_by": created_by, "created_at": _now_iso(), "updated_at": _now_iso(),
    }
    await db[COLL].insert_one(job)
    job.pop("_id", None)
    return job


async def get_job(job_id):
    return await db[COLL].find_one({"id": job_id}, {"_id": 0})


async def list_jobs(status=None, job_type=None, limit=100):
    q = {}
    if status:
        q["status"] = status
    if job_type:
        q["job_type"] = job_type
    return await db[COLL].find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def retry_job(job_id):
    j = await db[COLL].find_one({"id": job_id})
    if not j:
        return None
    if j.get("status") == "running":
        return {"error": "Job is currently running."}
    await db[COLL].update_one({"id": job_id}, {"$set": {
        "status": "queued", "attempts": 0, "error": None, "run_at": _now_iso(),
        "lease_until": None, "finished_at": None, "updated_at": _now_iso(),
        "progress": {"done": 0, "total": j.get("progress", {}).get("total", 0), "message": "Re-queued"}},
        "$push": {"logs": {"at": _now_iso(), "level": "info", "message": "Manually re-queued."}}})
    return await db[COLL].find_one({"id": job_id}, {"_id": 0})


async def cancel_job(job_id):
    r = await db[COLL].update_one({"id": job_id, "status": {"$in": ["queued", "failed"]}},
                                  {"$set": {"status": "cancelled", "updated_at": _now_iso(),
                                            "finished_at": _now_iso()},
                                   "$push": {"logs": {"at": _now_iso(), "level": "info", "message": "Cancelled."}}})
    if r.modified_count == 0:
        return {"error": "Only queued or failed jobs can be cancelled."}
    return await db[COLL].find_one({"id": job_id}, {"_id": 0})


async def _log(job_id, message, level="info"):
    await db[COLL].update_one({"id": job_id}, {"$set": {"updated_at": _now_iso()},
        "$push": {"logs": {"$each": [{"at": _now_iso(), "level": level, "message": str(message)[:400]}],
                           "$slice": -60}}})


async def _progress(job_id, done=None, total=None, message=None):
    upd = {"updated_at": _now_iso()}
    if done is not None:
        upd["progress.done"] = done
    if total is not None:
        upd["progress.total"] = total
    if message is not None:
        upd["progress.message"] = str(message)[:200]
    await db[COLL].update_one({"id": job_id}, {"$set": upd})


# ---------------------------------------------------------------------------
# Worker internals
# ---------------------------------------------------------------------------
async def _reclaim_stale():
    """Re-queue jobs whose worker died mid-run (lease expired). This is the restart-proof core."""
    r = await db[COLL].update_many(
        {"status": "running", "lease_until": {"$lt": _now_iso()}},
        {"$set": {"status": "queued", "lease_until": None, "updated_at": _now_iso()},
         "$push": {"logs": {"$each": [{"at": _now_iso(), "level": "warn",
                    "message": "Lease expired (worker was interrupted) — re-queued for retry."}], "$slice": -60}}})
    if r.modified_count:
        logger.info(f"[job_engine] reclaimed {r.modified_count} orphaned job(s)")


async def _lease_next():
    """Atomically claim the next due queued job."""
    from pymongo import ReturnDocument
    return await db[COLL].find_one_and_update(
        {"status": "queued", "run_at": {"$lte": _now_iso()}},
        {"$set": {"status": "running", "worker_started_at": _now_iso(),
                  "lease_until": _iso(_now() + timedelta(seconds=LEASE_SECONDS)), "updated_at": _now_iso()},
         "$inc": {"attempts": 1}},
        sort=[("priority", -1), ("run_at", 1), ("created_at", 1)],
        return_document=ReturnDocument.AFTER, projection={"_id": 0})


async def _heartbeat(job_id, stop_event):
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=HEARTBEAT_S)
        except asyncio.TimeoutError:
            pass
        if stop_event.is_set():
            break
        await db[COLL].update_one({"id": job_id, "status": "running"},
            {"$set": {"lease_until": _iso(_now() + timedelta(seconds=LEASE_SECONDS)), "updated_at": _now_iso()}})


async def _run_job(job):
    job_id = job["id"]
    handler = _HANDLERS.get(job["job_type"])
    if not handler:
        await db[COLL].update_one({"id": job_id}, {"$set": {"status": "failed",
            "error": f"No handler registered for job_type '{job['job_type']}'.", "finished_at": _now_iso(),
            "updated_at": _now_iso()}})
        return
    stop = asyncio.Event()
    hb = asyncio.create_task(_heartbeat(job_id, stop))
    try:
        async def progress(done=None, total=None, message=None):
            await _progress(job_id, done, total, message)
        result = await handler(job, progress)
        await db[COLL].update_one({"id": job_id}, {"$set": {
            "status": "complete", "result": result, "error": None, "finished_at": _now_iso(),
            "lease_until": None, "updated_at": _now_iso(),
            "progress.message": "Complete"},
            "$push": {"logs": {"$each": [{"at": _now_iso(), "level": "info", "message": "Completed."}], "$slice": -60}}})
        # Recurring: schedule the next run.
        if job.get("interval_seconds"):
            await enqueue(job["job_type"], job.get("payload"), title=job.get("title"),
                          dedupe_key=job.get("dedupe_key"),
                          run_at=_iso(_now() + timedelta(seconds=int(job["interval_seconds"]))),
                          max_attempts=job.get("max_attempts", DEFAULT_MAX_ATTEMPTS),
                          interval_seconds=job["interval_seconds"], created_by=job.get("created_by", "Schedule"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        attempts = job.get("attempts", 1)
        max_attempts = job.get("max_attempts", DEFAULT_MAX_ATTEMPTS)
        if attempts < max_attempts:
            backoff = min(300, 10 * (2 ** (attempts - 1)))
            await db[COLL].update_one({"id": job_id}, {"$set": {
                "status": "queued", "run_at": _iso(_now() + timedelta(seconds=backoff)),
                "lease_until": None, "error": str(e)[:300], "updated_at": _now_iso()},
                "$push": {"logs": {"$each": [{"at": _now_iso(), "level": "warn",
                    "message": f"Attempt {attempts}/{max_attempts} failed: {str(e)[:200]}. Retrying in {backoff}s."}], "$slice": -60}}})
        else:
            await db[COLL].update_one({"id": job_id}, {"$set": {
                "status": "failed", "error": str(e)[:300], "finished_at": _now_iso(),
                "lease_until": None, "updated_at": _now_iso()},
                "$push": {"logs": {"$each": [{"at": _now_iso(), "level": "error",
                    "message": f"Failed after {attempts} attempt(s): {str(e)[:200]}"}], "$slice": -60}}})
    finally:
        stop.set()
        try:
            await hb
        except Exception:
            pass


async def worker_loop():
    logger.info("[job_engine] worker loop started")
    # Reclaim anything orphaned by the restart we just came out of.
    try:
        await _reclaim_stale()
    except Exception as e:
        logger.error(f"[job_engine] initial reclaim failed: {e}")
    active = set()
    while True:
        try:
            await _reclaim_stale()
            # Fill the worker pool up to MAX_CONCURRENCY with due jobs.
            while len(active) < MAX_CONCURRENCY:
                job = await _lease_next()
                if not job:
                    break
                logger.info(f"[job_engine] running job {job['id']} ({job['job_type']})")
                t = asyncio.create_task(_run_job(job))
                active.add(t)
                t.add_done_callback(active.discard)
        except Exception as e:
            logger.error(f"[job_engine] worker loop error: {e}")
        await asyncio.sleep(POLL_INTERVAL_S)


_started = False


def start():
    """Idempotently launch the worker loop as a background task on app startup."""
    global _started
    if _started:
        return
    _started = True
    asyncio.create_task(worker_loop())
