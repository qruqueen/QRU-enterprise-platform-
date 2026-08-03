"""QRU Intelligent Bulk Manufacturing Orchestrator™.

Governs large manufacturing runs in batches of 25-50 topics with queue management,
pause/resume, retry, dependency tracking, progress, logs, and token-cost estimation.

Per-topic workflow:
    Topic Registry → Manufacturing Order → Knowledge Record → AI Manufacture (core)
    → AI Verification Team → (auto-approve / escalate) → mark Treasure Standard™.
"""
import asyncio
import logging

from database import db
from models import gen_id, now_iso, QRU_SECTIONS
from ai_service import llm_generate, parse_json, RESEARCH_SYSTEM, QRU_METHODOLOGY_SYSTEM
from verification_engine import ai_verify_record
import product_protection as pp
from org_activity import log_org
import job_engine

logger = logging.getLogger("qru.orchestrator")


async def get_settings():
    s = await db.factory_settings.find_one({"id": "factory"})
    if not s:
        s = {"id": "factory", "hands_free_mode": True}
        await db.factory_settings.insert_one(dict(s))
        s = await db.factory_settings.find_one({"id": "factory"})
    from models import clean as _clean
    return _clean(s)

# Rough token estimate (chars / 4) for cost visibility.
def _est_tokens(*texts):
    return sum(len(t or "") for t in texts) // 4


async def _llm(system, prompt, session, batch_id):
    raw = await llm_generate(system, prompt, session)
    await db.manufacturing_batches.update_one(
        {"id": batch_id}, {"$inc": {"est_tokens": _est_tokens(system, prompt, raw)}})
    return raw


async def _log(batch_id, level, message):
    await db.manufacturing_batches.update_one(
        {"id": batch_id},
        {"$push": {"logs": {"at": now_iso(), "level": level, "message": message}}})


def _is_filled(v):
    if isinstance(v, list):
        return len(v) > 0
    return bool(v and str(v).strip())


async def create_batch(name, college, division, topic_registry_ids, batch_size, owner_id, actor):
    topics = await db.topic_registry.find({"id": {"$in": topic_registry_ids}}).to_list(2000)
    items = [{
        "topic_registry_id": t["id"], "topic_id": t.get("topic_id"), "topic_name": t["topic_name"],
        "department": t.get("department"), "status": "pending", "stage": "Queued",
        "kr_id": None, "mo_id": t.get("assigned_manufacturing_order"), "retries": 0, "error": None,
    } for t in topics]
    batch = {
        "id": gen_id(), "name": name, "college": college, "division": division,
        "batch_size": int(batch_size), "topic_registry_ids": topic_registry_ids,
        "items": items, "total": len(items), "completed": 0, "failed": 0, "escalated": 0,
        "status": "queued", "progress": 0, "logs": [], "est_tokens": 0, "approved": False,
        "owner_id": owner_id, "actor": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.manufacturing_batches.insert_one(dict(batch))
    await _log(batch["id"], "info", f"Batch created with {len(items)} topics.")
    return batch


async def start_batch(batch_id):
    b = await db.manufacturing_batches.find_one({"id": batch_id})
    if not b:
        return None
    if b["status"] == "running":
        return b
    await db.manufacturing_batches.update_one(
        {"id": batch_id}, {"$set": {"status": "running", "updated_at": now_iso()}})
    await _log(batch_id, "info", "Batch started.")
    await _enqueue_worker(batch_id)
    return await db.manufacturing_batches.find_one({"id": batch_id})


async def pause_batch(batch_id):
    await db.manufacturing_batches.update_one(
        {"id": batch_id}, {"$set": {"status": "paused", "updated_at": now_iso()}})
    await _log(batch_id, "warning", "Pause requested — will stop after the current topic.")
    return await db.manufacturing_batches.find_one({"id": batch_id})


async def resume_batch(batch_id):
    b = await db.manufacturing_batches.find_one({"id": batch_id})
    if not b or b["status"] not in ("paused",):
        return b
    await db.manufacturing_batches.update_one(
        {"id": batch_id}, {"$set": {"status": "running", "updated_at": now_iso()}})
    await _log(batch_id, "info", "Batch resumed.")
    await _enqueue_worker(batch_id)
    return await db.manufacturing_batches.find_one({"id": batch_id})


async def retry_failed(batch_id):
    b = await db.manufacturing_batches.find_one({"id": batch_id})
    if not b:
        return None
    items = b["items"]
    reset = 0
    for it in items:
        if it["status"] in ("failed",):
            it["status"] = "pending"
            it["stage"] = "Queued (retry)"
            it["error"] = None
            reset += 1
    await db.manufacturing_batches.update_one(
        {"id": batch_id}, {"$set": {"items": items, "failed": 0, "status": "running", "updated_at": now_iso()}})
    await _log(batch_id, "info", f"Retrying {reset} failed topic(s).")
    await _enqueue_worker(batch_id)
    return await db.manufacturing_batches.find_one({"id": batch_id})


async def _update_item(batch_id, idx, **fields):
    b = await db.manufacturing_batches.find_one({"id": batch_id})
    if not b:
        return
    items = b["items"]
    items[idx].update(fields)
    completed = sum(1 for i in items if i["status"] == "done")
    failed = sum(1 for i in items if i["status"] == "failed")
    escalated = sum(1 for i in items if i["status"] == "escalated")
    total = len(items)
    progress = round((completed + failed + escalated) / total * 100) if total else 0
    await db.manufacturing_batches.update_one(
        {"id": batch_id},
        {"$set": {"items": items, "completed": completed, "failed": failed,
                  "escalated": escalated, "progress": progress, "updated_at": now_iso()}})


async def _manufacture_core(batch_id, topic_name, department, division):
    """Create a verified-truth-backed Knowledge Record with the full QRU methodology.
    Returns the new KR id."""
    # 1) Research the verified truth.
    research_raw = await _llm(RESEARCH_SYSTEM, f"Topic: {topic_name}\nDivision: {division}",
                              f"orch-research-{topic_name}", batch_id)
    research = parse_json(research_raw) or {}
    verified_truth = research.get("summary") or topic_name
    confidence = int(research.get("confidence_score", 80) or 80)
    sources = research.get("sources", []) if isinstance(research.get("sources"), list) else []

    count = await db.knowledge_records.count_documents({})
    kr_id = gen_id()
    now = now_iso()
    section_status = {s: "Empty" for s in QRU_SECTIONS}
    kr = {
        "id": kr_id, "kr_code": f"KR-{count + 1:05d}", "title": topic_name, "subtitle": "",
        "category": department or division, "division": division, "verified_truth": verified_truth,
        "confidence_score": confidence, "sources": sources, "references": research.get("key_points", []),
        "verification_status": "Draft", "approval_status": "Pending", "reviewer": None, "verification": None,
        "section_status": section_status, "understanding_status": "Not Manufactured",
        "is_master_file": False, "treasure_standard": False, "products_created": 0, "version": 1,
        "created_by": "Manufacturing Orchestrator™", "owner_id": None,
        "created_at": now, "updated_at": now,
    }
    for s in QRU_SECTIONS:
        kr[s] = [] if s in ("practice_application", "key_vocabulary") else ""
    await db.knowledge_records.insert_one(dict(kr))

    # 2) Manufacture the QRU methodology.
    method_raw = await _llm(QRU_METHODOLOGY_SYSTEM,
                            f"Title: {topic_name}\nCategory: {department}\nVerified Truth: {verified_truth}",
                            f"orch-method-{kr_id}", batch_id)
    method = parse_json(method_raw) or {}
    upd = {}
    for s in QRU_SECTIONS:
        val = method.get(s)
        if _is_filled(val):
            upd[s] = val
            section_status[s] = "Draft"
    upd["section_status"] = section_status
    upd["understanding_status"] = "Draft"
    upd["updated_at"] = now_iso()
    await db.knowledge_records.update_one({"id": kr_id}, {"$set": upd})
    return kr_id


def _kr_product_content(kr):
    parts = [f"# {kr.get('title','')}", ""]
    order = ["simple_answer", "why_it_matters", "qru_translation", "everyday_analogy",
             "real_world_example", "deep_roots", "memory_sentence"]
    labels = {"simple_answer": "Simple Answer", "why_it_matters": "Why It Matters",
              "qru_translation": "QRU Translation™", "everyday_analogy": "Everyday Analogy",
              "real_world_example": "Real-World Example", "deep_roots": "Deep Roots™",
              "memory_sentence": "Memory Sentence™"}
    for f in order:
        v = kr.get(f)
        if v:
            parts.append(f"## {labels[f]}\n\n{v}\n")
    return "\n".join(parts)


async def _auto_publish(kr_id, division, college, batch_id):
    """AI Publishing Team — hands-free: assemble → QC/verify product → protect →
    publish to Product Library (and Customer Library). Returns (status, escalated)."""
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        return "failed", False
    count = await db.products.count_documents({})
    pid = gen_id()
    now = now_iso()
    product = {
        "id": pid, "product_code": f"PRD-{count + 1:05d}",
        "title": kr["title"], "product_type": "Interactive Lesson",
        "family": kr.get("category", division), "topic": kr["title"],
        "audience": "General public", "learning_level": "Introductory",
        "content": _kr_product_content(kr), "status": "In Review",
        "knowledge_record_id": kr_id, "kr_version": kr.get("version", 1),
        "assembled": True, "division": division, "college": college,
        "creative_brief": {
            "who_for": "Anyone curious to truly understand this topic.",
            "problem_solved": "Replaces confusing jargon with clear, verified understanding.",
            "will_understand": f"You will understand {kr['title'].lower()} and why it matters.",
            "skills_gained": ["Clear mental model", "Everyday application"],
            "whats_included": ["Layered understanding", "Everyday analogy", "Memory sentence"],
            "reading_level": "Beginner", "completion_time": "15 minutes",
            "next_path": "Continue your pathway in this college.",
        },
        "creative_status": "Reviewed",
        "created_by": "AI Publishing Team™", "owner_id": kr.get("owner_id"),
        "created_at": now, "updated_at": now,
    }
    await db.products.insert_one(dict(product))
    await db.knowledge_records.update_one({"id": kr_id}, {"$inc": {"products_created": 1}})

    # Treasure Standard™ Improvement Loop™ → QC → protect → publish → distribute.
    outcome = await pp.treasure_finalize(pid, "AI Publishing Team™")
    if outcome == "escalated":
        return "escalated", True
    if outcome == "needs_review":
        return "needs_review", False
    return "published", False


async def _worker(batch_id):
    try:
        while True:
            b = await db.manufacturing_batches.find_one({"id": batch_id})
            if not b or b["status"] != "running":
                if b and b["status"] == "paused":
                    await _log(batch_id, "warning", "Batch paused.")
                return
            settings = await get_settings()
            hands_free = settings.get("hands_free_mode", True)
            items = b["items"]
            idx = next((i for i, it in enumerate(items) if it["status"] == "pending"), None)
            if idx is None:
                final = "completed" if b["failed"] == 0 else "completed_with_errors"
                await db.manufacturing_batches.update_one(
                    {"id": batch_id}, {"$set": {"status": final, "progress": 100, "updated_at": now_iso()}})
                await _log(batch_id, "success",
                           f"Batch finished — {b['completed']} done, {b['escalated']} escalated, {b['failed']} failed.")
                await log_org("Manufacturing Director™", "Manufacturing",
                              f"completed batch '{b['name']}' ({b['completed']} records)", "", "success")
                return

            it = items[idx]
            await _update_item(batch_id, idx, status="running", stage="Manufacturing")
            await _log(batch_id, "info", f"Manufacturing: {it['topic_name']}")
            try:
                kr_id = await _manufacture_core(batch_id, it["topic_name"], it.get("department"), b["division"])
                await _update_item(batch_id, idx, kr_id=kr_id, stage="Verifying")
                await _log(batch_id, "info", f"AI Verification Team reviewing: {it['topic_name']}")

                result = await ai_verify_record(kr_id, "QRU Verification Team™")
                kr = await db.knowledge_records.find_one({"id": kr_id})
                treasure = "Certified" if kr.get("treasure_standard") else "Not Certified"
                vstatus = kr.get("verification_status", "Draft")

                reg = it.get("topic_registry_id")
                if reg:
                    await db.topic_registry.update_one(
                        {"id": reg},
                        {"$set": {"manufacturing_status": "Manufactured", "verification_status": vstatus,
                                  "treasure_standard_status": treasure, "knowledge_record_id": kr_id,
                                  "updated_at": now_iso()}})

                if result.get("escalated"):
                    if it.get("mo_id"):
                        await db.manufacturing_orders.update_one(
                            {"id": it["mo_id"]}, {"$set": {"knowledge_record_id": kr_id, "status": "Escalated", "updated_at": now_iso()}})
                    await _update_item(batch_id, idx, status="escalated", stage="Escalated to Founder")
                    await _log(batch_id, "warning", f"Escalated to Founder: {it['topic_name']}")
                    await asyncio.sleep(0.2)
                    continue

                # Hands-Free Manufacturing Mode™ — auto QC → Treasure Standard → publish.
                if hands_free:
                    await _update_item(batch_id, idx, stage="Quality Control")
                    await _log(batch_id, "info", f"AI QC & Publishing: {it['topic_name']}")
                    pub_status, pub_esc = await _auto_publish(kr_id, b["division"], b["college"], batch_id)
                    mo_status = {"published": "Published", "escalated": "Escalated",
                                 "needs_review": "Quality Review", "failed": "Failed"}.get(pub_status, "Quality Review")
                    if it.get("mo_id"):
                        await db.manufacturing_orders.update_one(
                            {"id": it["mo_id"]}, {"$set": {"knowledge_record_id": kr_id, "status": mo_status, "updated_at": now_iso()}})
                    if pub_esc:
                        await _update_item(batch_id, idx, status="escalated", stage="Escalated (IP/QC)")
                        await _log(batch_id, "warning", f"Publishing escalated: {it['topic_name']}")
                    elif pub_status == "published":
                        await _update_item(batch_id, idx, status="done", stage="Published")
                        await _log(batch_id, "success", f"Published: {it['topic_name']}")
                    else:
                        await _update_item(batch_id, idx, status="done", stage="Verified (QC review)")
                        await _log(batch_id, "info", f"Verified, product held for QC review: {it['topic_name']}")
                else:
                    if it.get("mo_id"):
                        await db.manufacturing_orders.update_one(
                            {"id": it["mo_id"]}, {"$set": {"knowledge_record_id": kr_id, "status": "Quality Review", "updated_at": now_iso()}})
                    await _update_item(batch_id, idx, status="done", stage="Verified")
                    await _log(batch_id, "success", f"Verified (awaiting approval): {it['topic_name']}")
            except Exception as e:
                logger.error(f"topic failed: {e}")
                await _update_item(batch_id, idx, status="failed", stage="Failed",
                                   error=str(e)[:300], retries=it.get("retries", 0) + 1)
                await _log(batch_id, "error", f"Failed: {it['topic_name']} — {str(e)[:120]}")
            await asyncio.sleep(0.2)
    except Exception as e:
        logger.error(f"batch worker crashed: {e}")
        await db.manufacturing_batches.update_one(
            {"id": batch_id}, {"$set": {"status": "failed", "updated_at": now_iso()}})


async def _enqueue_worker(batch_id):
    """Run the batch worker on the durable Orchestration Spine™ (restart-proof). The worker is
    fully resumable — its per-topic state lives in the batch document — so a reclaimed job simply
    continues with the next pending topic."""
    await job_engine.enqueue("batch_manufacture_run", payload={"batch_id": batch_id},
                             title=f"Bulk Manufacturing · {batch_id[:8]}",
                             dedupe_key=f"batch:{batch_id}", max_attempts=5, created_by="System")


async def batch_manufacture_run_handler(job, progress):
    await _worker((job.get("payload") or {}).get("batch_id"))
    return {"batch_id": (job.get("payload") or {}).get("batch_id")}


async def reconcile_stale_batches():
    """Resume bulk-manufacturing batches left 'running' by a pre-Spine restart (idempotent —
    the worker picks up the next pending topic; already-done topics are untouched)."""
    n = 0
    async for b in db.manufacturing_batches.find({"status": "running"}, {"_id": 0, "id": 1}):
        await _enqueue_worker(b["id"])
        n += 1
    if n:
        logger.info(f"[orchestrator] resumed {n} interrupted batch(es) on the Spine")
    return n


async def approve_batch(batch_id, actor):
    """Batch approval before publishing — publishes verified records' products."""
    b = await db.manufacturing_batches.find_one({"id": batch_id})
    if not b:
        return None
    await db.manufacturing_batches.update_one(
        {"id": batch_id}, {"$set": {"approved": True, "approved_by": actor, "approved_at": now_iso()}})
    await _log(batch_id, "success", f"Batch approved for publication by {actor}.")
    return await db.manufacturing_batches.find_one({"id": batch_id})
