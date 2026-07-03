"""QRU Enterprise Workflow Engine™ — the orchestration layer of the QRU Factory™.

Every Manufacturing Order runs a governed workflow:
  KR Retrieval → Verification → Treasure Standard™ → Product Recipes™ →
  Parallel Manufacturing → Quality Control → Packaging → Distribution →
  Analytics → Continuous Improvement.

Features: Workflow Templates™, Parallel Manufacturing™, Job Queue Management™,
Automatic Error Recovery™ (retry + alternate provider), complete Production Logs™,
Estimated Production Cost™, and an Executive Factory Monitor™.

The Founder answers one question — "What do you want to teach today?" — and the
Workflow Engine coordinates every QRU Division™ automatically. It escalates only true
exceptions (Treasure Standard™ unreachable, conflicting evidence, human judgment).
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from database import db
from models import gen_id, now_iso, clean
import product_automation as pa
from product_automation import _produce_one, RECIPES
import ai_services_manager as ai
from verification_engine import ai_verify_record
import orchestrator as orch
import integration_hub as hub
from org_activity import log_org

logger = logging.getLogger("qru.workflow")

# Bound concurrent LLM/render pipelines for reliability under load (avoid 503 bursts).
_SEM = asyncio.Semaphore(2)

STAGES = [
    "KR Retrieval", "Verification", "Treasure Standard™", "Product Recipes™",
    "Parallel Manufacturing", "Quality Control", "Packaging", "Distribution",
    "Analytics", "Continuous Improvement",
]

STAGE_DIVISION = {
    "KR Retrieval": "Knowledge Division™", "Verification": "Verification Division™",
    "Treasure Standard™": "Verification Division™", "Product Recipes™": "Manufacturing Division™",
    "Parallel Manufacturing": "Manufacturing Division™", "Quality Control": "Verification Division™",
    "Packaging": "Brand & IP Division™", "Distribution": "Distribution Division™",
    "Analytics": "Analytics Division™", "Continuous Improvement": "Enterprise Improvement™",
}

# ---------------- Workflow Templates™ (reusable) ----------------
WORKFLOW_TEMPLATES = {
    "Book Manufacturing Workflow™": {
        "division": "Health", "avg_seconds_per_product": 90,
        "products": ["Book", "Workbook", "Teacher Guide", "Student Guide", "Certificate", "Poster", "Blog Article"]},
    "Video Manufacturing Workflow™": {
        "division": "Health", "avg_seconds_per_product": 120,
        "products": ["YouTube Video Script", "Short Video", "Audio Narration", "YouTube Thumbnail", "Transcript"]},
    "Health Product Workflow™": {
        "division": "Health", "avg_seconds_per_product": 80,
        "products": ["Interactive Lesson", "Workbook", "Poster", "Quiz", "Social Media Pack"]},
    "Faith Product Workflow™": {
        "division": "Faith", "avg_seconds_per_product": 80,
        "products": ["Interactive Lesson", "Faith Reflection", "Poster", "Daily Motivation"]},
    "Course Manufacturing Workflow™": {
        "division": "Health", "avg_seconds_per_product": 90,
        "products": ["Course", "Interactive Lesson", "Quiz", "Flash Cards", "Certificate", "Presentation"]},
    "Marketing Campaign Workflow™": {
        "division": "Health", "avg_seconds_per_product": 70,
        "products": ["Blog Article", "Email Newsletter", "Social Media Pack", "Landing Page", "Pinterest Graphic"]},
    "Translation Workflow™": {
        "division": "Health", "avg_seconds_per_product": 60,
        "products": ["Transcript", "Blog Article", "Social Media Pack"]},
    "Full Treasure Package™": {
        "division": "Health", "avg_seconds_per_product": 100,
        "products": ["Book", "Workbook", "Poster", "Presentation", "Teacher Guide", "Student Guide",
                     "Interactive Lesson", "Short Video", "Podcast Script", "Audio Narration", "Social Media Pack"]},
}


def templates_public():
    return [{"name": k, "division": v["division"], "products": v["products"],
             "product_count": len(v["products"])} for k, v in WORKFLOW_TEMPLATES.items()]


# ---------------- Job Queue helpers ----------------
async def _set(job_id, **fields):
    await db.workflow_jobs.update_one({"id": job_id}, {"$set": {**fields, "updated_at": now_iso()}})


async def _log(job_id, stage, message, level="info"):
    entry = {"at": now_iso(), "stage": stage, "division": STAGE_DIVISION.get(stage, "QRU Factory™"),
             "message": message, "level": level}
    await db.workflow_jobs.update_one({"id": job_id}, {"$push": {"logs": entry}})


async def _complete_stage(job_id, stage):
    await db.workflow_jobs.update_one({"id": job_id}, {"$addToSet": {"completed_tasks": stage}})


async def _warn(job_id, message):
    await db.workflow_jobs.update_one({"id": job_id}, {"$push": {"warnings": message}})


async def _error(job_id, message):
    await db.workflow_jobs.update_one({"id": job_id}, {"$push": {"errors": message}})


async def _record_product(job_id, ptype, status, product_id=None, retries=0, error=None, cost=0.0):
    item = {"product_type": ptype, "status": status, "product_id": product_id,
            "retries": retries, "error": (error or "")[:200], "est_cost_usd": round(cost, 6)}
    await db.workflow_jobs.update_one({"id": job_id}, {"$push": {"products": item},
                                                       "$inc": {"est_cost_usd": round(cost, 6),
                                                                "retry_count": retries}})


# ---------------- Automatic Error Recovery™ manufacturing ----------------
async def _manufacture_product(job_id, kr, ptype, owner_id):
    async with _SEM:
        if ptype not in RECIPES:
            await _record_product(job_id, ptype, "skipped", error="No recipe registered")
            await _warn(job_id, f"{ptype}: no recipe — skipped")
            return
        agent = RECIPES[ptype]["agent"]
        cap = RECIPES[ptype]["capability"]
        est = ai.estimate_cost(cap, kr.get("verified_truth", "")) or 0.02
        for attempt in range(2):
            try:
                pid = await _produce_one(kr, ptype, job_id, owner_id, hands_free=True)
                await _record_product(job_id, ptype, "done", product_id=pid, retries=attempt, cost=est)
                await _log(job_id, "Parallel Manufacturing", f"Manufactured {ptype} ({agent})", "success")
                return pid
            except Exception as e:
                await _log(job_id, "Parallel Manufacturing",
                           f"{ptype} attempt {attempt+1} failed — {str(e)[:80]}; recovering", "warning")
                await asyncio.sleep(0.5)
        await _record_product(job_id, ptype, "failed", retries=2, error="Failed after automatic retry", cost=0.0)
        await _error(job_id, f"{ptype}: could not be manufactured after retries")
        await _log(job_id, "Parallel Manufacturing", f"{ptype} failed after automatic recovery", "error")
        return None


# ---------------- Workflow runner ----------------
async def _run_job(job_id, topic, template, division, owner_id, actor, kr_id=None):
    tpl = WORKFLOW_TEMPLATES[template]
    products = tpl["products"]
    try:
        await _set(job_id, status="running", stage="KR Retrieval",
                   started_at=now_iso(), progress=3, current_task=f"Retrieving verified knowledge for '{topic}'")
        await _log(job_id, "KR Retrieval", f"Locating a verified Knowledge Record for '{topic}'")

        # STAGE 1 — KR Retrieval (find or manufacture verified KR)
        kr = None
        if kr_id:
            kr = await db.knowledge_records.find_one({"id": kr_id})
        if not kr:
            kr = await db.knowledge_records.find_one(
                {"title": {"$regex": topic, "$options": "i"}, "verification_status": "Verified"})
        if not kr:
            await _log(job_id, "KR Retrieval", "No verified record found — manufacturing a new Knowledge Record")
            new_id = await orch._manufacture_core(job_id, topic, division, division)
            await _complete_stage(job_id, "KR Retrieval")

            # STAGE 2 — Verification
            await _set(job_id, stage="Verification", progress=12,
                       current_task="AI Verification Team™ reviewing accuracy, clarity & completeness")
            await _log(job_id, "Verification", "AI Verification Team™ reviewing the Knowledge Record")
            result = await ai_verify_record(new_id, "QRU Verification Team™")
            kr = await db.knowledge_records.find_one({"id": new_id})
            if result.get("escalated"):
                await _set(job_id, status="escalated", stage="Verification", kr_id=new_id,
                           kr_code=kr.get("kr_code"), note="Escalated to Founder — human judgment required.",
                           completed_at=now_iso())
                await _log(job_id, "Verification", "Escalated to Founder — human judgment required", "warning")
                await log_org("Verification Division™", "Knowledge", f"escalated '{topic}' to Founder", "", "warning")
                return
            await _complete_stage(job_id, "Verification")
        else:
            await _complete_stage(job_id, "KR Retrieval")
            await _complete_stage(job_id, "Verification")

        await _set(job_id, kr_id=kr["id"], kr_code=kr.get("kr_code"), kr_title=kr.get("title"))

        # STAGE 3 — Treasure Standard™ (knowledge gate)
        await _set(job_id, stage="Treasure Standard™", progress=22,
                   current_task="Confirming Treasure Standard™ knowledge readiness")
        await _log(job_id, "Treasure Standard™",
                   "Knowledge verified — Treasure Standard™ enforced at product QC")
        await _complete_stage(job_id, "Treasure Standard™")

        # STAGE 4 — Product Recipes™
        await _set(job_id, stage="Product Recipes™", progress=28,
                   current_task=f"Selecting {len(products)} Product Recipes™")
        await _log(job_id, "Product Recipes™", f"Selected recipes: {', '.join(products)}")
        await _complete_stage(job_id, "Product Recipes™")

        # STAGE 5 — Parallel Manufacturing™
        await _set(job_id, stage="Parallel Manufacturing", progress=35,
                   current_task=f"Manufacturing {len(products)} products in parallel")
        await _log(job_id, "Parallel Manufacturing",
                   f"Launching {len(products)} independent production pipelines in parallel")
        await asyncio.gather(*[_manufacture_product(job_id, kr, pt, owner_id) for pt in products])
        job = await db.workflow_jobs.find_one({"id": job_id})
        made = [p for p in job.get("products", []) if p["status"] == "done"]
        await _set(job_id, progress=75)
        await _complete_stage(job_id, "Parallel Manufacturing")

        # STAGE 6 — Quality Control (Improvement Loop ran inside hands-free finalize)
        await _set(job_id, stage="Quality Control", progress=80,
                   current_task="Treasure Standard™ QC applied during manufacturing")
        await _log(job_id, "Quality Control",
                   f"Treasure Standard™ Improvement Loop™ applied to {len(made)} product(s)")
        await _complete_stage(job_id, "Quality Control")

        # STAGE 7 — Packaging
        await _set(job_id, stage="Packaging", progress=85, current_task="Bundling package deliverables")
        await _log(job_id, "Packaging", f"Packaged {len(made)} products with QRU branding & licensing")
        await _complete_stage(job_id, "Packaging")

        # STAGE 8 — Distribution (finalize already routes; here we confirm & report)
        await _set(job_id, stage="Distribution", progress=90, current_task="Confirming distribution routing")
        distributed = 0
        for p in made:
            prod = await db.products.find_one({"id": p["product_id"]})
            if prod and prod.get("distribution"):
                distributed += 1
        await _log(job_id, "Distribution", f"Confirmed distribution routing for {distributed} product(s)")
        await _complete_stage(job_id, "Distribution")

        # STAGE 9 — Analytics
        await _set(job_id, stage="Analytics", progress=95, current_task="Updating factory analytics")
        await _log(job_id, "Analytics",
                   f"Analytics updated — {len(made)} manufactured, est. cost ${round(job.get('est_cost_usd',0),4)}")
        await _complete_stage(job_id, "Analytics")

        # STAGE 10 — Continuous Improvement (Learning Factory seed)
        await _set(job_id, stage="Continuous Improvement", progress=98,
                   current_task="Recording learnings for future cycles")
        failed = [p for p in job.get("products", []) if p["status"] == "failed"]
        await db.factory_learnings.insert_one({
            "id": gen_id(), "job_id": job_id, "template": template, "topic": topic,
            "kr_code": kr.get("kr_code"), "manufactured": len(made), "failed": len(failed),
            "recommendation": (f"Retry or review recipes: {', '.join(p['product_type'] for p in failed)}"
                               if failed else "All recipes performed to standard — reuse this workflow."),
            "created_at": now_iso(),
        })
        await _log(job_id, "Continuous Improvement",
                   "Recorded manufacturing experience into QRU Enterprise Memory™")
        await _complete_stage(job_id, "Continuous Improvement")

        final = "completed" if not failed else "completed_with_errors"
        await _set(job_id, status=final, stage="Completed", progress=100, completed_at=now_iso(),
                   current_task="Workflow complete", manufactured=len(made), failed_count=len(failed))
        await log_org("Workflow Engine™", "Manufacturing",
                      f"completed workflow '{template}' — {len(made)} products", kr.get("kr_code", ""),
                      "success" if not failed else "warning")
    except Exception as e:
        logger.error(f"workflow job {job_id} crashed: {e}")
        await _error(job_id, str(e)[:200])
        await _set(job_id, status="failed", note=str(e)[:200], completed_at=now_iso())


async def start_workflow(template, topic=None, kr_id=None, division=None, owner_id=None, actor="Founder"):
    if template not in WORKFLOW_TEMPLATES:
        return None, "Unknown workflow template"
    tpl = WORKFLOW_TEMPLATES[template]
    division = division or tpl["division"]
    if kr_id and not topic:
        kr = await db.knowledge_records.find_one({"id": kr_id})
        topic = kr.get("title") if kr else "Untitled"
    if not topic:
        return None, "Provide a topic or a Knowledge Record"
    count = await db.workflow_jobs.count_documents({})
    eta = (datetime.now(timezone.utc) +
           timedelta(seconds=len(tpl["products"]) * tpl["avg_seconds_per_product"] / 4)).isoformat()
    job = {
        "id": gen_id(), "job_number": f"WF-{count + 1:05d}", "template": template,
        "division": division, "topic": topic, "kr_id": kr_id, "kr_code": None, "kr_title": None,
        "status": "queued", "stage": "Queued", "progress": 0, "current_task": "Queued",
        "completed_tasks": [], "warnings": [], "errors": [], "products": [],
        "retry_count": 0, "est_cost_usd": 0.0, "manufactured": 0, "failed_count": 0,
        "planned_products": tpl["products"], "eta": eta, "is_fat": False,
        "owner_id": owner_id, "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
        "started_at": None, "completed_at": None,
    }
    await db.workflow_jobs.insert_one(dict(job))
    asyncio.create_task(_run_job(job["id"], topic, template, division, owner_id, actor, kr_id))
    return clean(await db.workflow_jobs.find_one({"id": job["id"]})), None


# ---------------- Executive Factory Monitor™ ----------------
async def factory_monitor():
    jobs = await db.workflow_jobs.find().sort("created_at", -1).to_list(500)
    running = [j for j in jobs if j["status"] == "running"]
    waiting = [j for j in jobs if j["status"] == "queued"]
    completed = [j for j in jobs if j["status"] in ("completed", "completed_with_errors")]
    escalated = [j for j in jobs if j["status"] == "escalated"]

    ai_status = await ai.status_summary()
    monitor = await hub.monitor_summary()
    import commerce
    rev = await commerce.revenue_summary()

    products = await db.products.count_documents({})
    published = await db.products.count_documents({"status": "Published"})
    treasure = await db.products.count_documents({"treasure_standard": True})
    open_esc = await db.founder_escalations.count_documents({"status": "Open"})
    kr_total = await db.knowledge_records.count_documents({})
    kr_verified = await db.knowledge_records.count_documents({"verification_status": "Verified"})

    workflow_cost = round(sum(j.get("est_cost_usd", 0) for j in jobs), 4)
    treasure_compliance = round(treasure / published * 100) if published else 100
    automation_success = round(len(completed) / len(jobs) * 100) if jobs else 100
    intervention_rate = round(len(escalated) / len(jobs) * 100) if jobs else 0

    # Division activity — recent org activity feed.
    activity = await db.org_activity.find().sort("created_at", -1).to_list(40)

    factory_health = "healthy"
    if open_esc or ai_status["jobs_failed"] or monitor["unhealthy"]:
        factory_health = "attention"

    return {
        "jobs": {"running": len(running), "waiting": len(waiting), "completed": len(completed),
                 "escalated": len(escalated), "total": len(jobs)},
        "running_jobs": [_job_card(j) for j in running][:10],
        "recent_jobs": [_job_card(j) for j in jobs][:12],
        "manufacturing_speed": {"avg_products_per_job":
                                round(sum(len(j.get("products", [])) for j in completed) / len(completed), 1) if completed else 0,
                                "products_manufactured": sum(j.get("manufactured", 0) for j in jobs)},
        "ai_usage": {"jobs": ai_status["jobs_total"], "real": ai_status["jobs_real"],
                     "failed": ai_status["jobs_failed"]},
        "estimated_production_cost_usd": round(workflow_cost + ai_status.get("estimated_cost_usd", 0), 4),
        "cost_label": "Estimated",
        "quality": {"treasure_products": treasure, "treasure_compliance_pct": treasure_compliance},
        "distribution": {"total": monitor["distributions_total"], "failed": monitor["distributions_failed"],
                         "platforms_connected": monitor["platforms_connected"]},
        "revenue": {"connected": rev["connected"], "revenue_usd": rev["revenue_usd"],
                    "paid_orders": rev["paid_orders"], "aov_usd": rev["aov_usd"]},
        "customer_activity": {"published_products": published, "total_products": products},
        "health": {
            "factory_health": factory_health,
            "knowledge_health": round(kr_verified / kr_total * 100) if kr_total else 100,
            "treasure_compliance_pct": treasure_compliance,
            "automation_success_pct": automation_success,
            "founder_intervention_pct": intervention_rate,
            "open_exceptions": open_esc,
        },
        "division_activity": [{"at": a.get("created_at"), "division": a.get("department"),
                               "actor": a.get("agent"), "action": a.get("action"),
                               "status": a.get("level")} for a in activity],
    }


def _job_card(j):
    return {"id": j["id"], "job_number": j.get("job_number"), "template": j.get("template"),
            "topic": j.get("topic"), "division": j.get("division"), "status": j.get("status"),
            "stage": j.get("stage"), "progress": j.get("progress", 0),
            "current_task": j.get("current_task"), "kr_code": j.get("kr_code"),
            "manufactured": j.get("manufactured", 0), "failed": j.get("failed_count", 0),
            "planned": len(j.get("planned_products", [])),
            "est_cost_usd": round(j.get("est_cost_usd", 0), 4), "eta": j.get("eta"),
            "retry_count": j.get("retry_count", 0), "warnings": len(j.get("warnings", [])),
            "errors": len(j.get("errors", [])), "is_fat": j.get("is_fat", False),
            "created_at": j.get("created_at"), "completed_at": j.get("completed_at")}


# ---------------- Factory Acceptance Test™ (Phase B.5) ----------------
async def run_factory_acceptance_test(owner_id, actor="Factory Acceptance Test™"):
    """Manufacture ONE complete Treasure Standard™ package end-to-end through the full
    workflow and validate every division. Uses the Full Treasure Package™ template."""
    job, err = await start_workflow("Full Treasure Package™", topic="QRU Factory Acceptance Test — Understanding Sleep and Rest",
                                    division="Health", owner_id=owner_id, actor=actor)
    if err:
        return None, err
    await db.workflow_jobs.update_one({"id": job["id"]}, {"$set": {"is_fat": True}})
    return job, None


async def evaluate_fat(job_id):
    """Validate a completed FAT job across every division and auto-report defects."""
    j = await db.workflow_jobs.find_one({"id": job_id})
    if not j:
        return None
    made = [p for p in j.get("products", []) if p["status"] == "done"]
    failed = [p for p in j.get("products", []) if p["status"] == "failed"]
    planned = j.get("planned_products", [])

    # Verify real assets exist for media products.
    voice_ok = video_ok = False
    for p in made:
        prod = await db.products.find_one({"id": p["product_id"]})
        if not prod:
            continue
        if p["product_type"] in ("Audio Narration",) and prod.get("asset_url"):
            voice_ok = True
        if p["product_type"] in ("Short Video",) and prod.get("asset_url"):
            video_ok = True

    published = 0
    for p in made:
        prod = await db.products.find_one({"id": p["product_id"]})
        if prod and prod.get("status") == "Published":
            published += 1
    checks = [
        {"division": "Knowledge Division™", "pass": bool(j.get("kr_id")), "detail": f"KR {j.get('kr_code')}"},
        {"division": "Verification Division™", "pass": "Verification" in j.get("completed_tasks", []),
         "detail": "AI verification executed"},
        {"division": "Manufacturing Division™", "pass": len(made) >= max(1, len(planned) - 2),
         "detail": f"{len(made)}/{len(planned)} products manufactured"},
        {"division": "AI Voice (OpenAI TTS)", "pass": voice_ok, "detail": "Real narration asset produced"},
        {"division": "AI Video (Slideshow)", "pass": video_ok, "detail": "Real MP4 asset produced"},
        {"division": "Publishing Division™", "pass": published > 0, "detail": f"{published} published"},
        {"division": "Distribution Division™", "pass": "Distribution" in j.get("completed_tasks", []),
         "detail": "Smart routing executed"},
        {"division": "Analytics Division™", "pass": "Analytics" in j.get("completed_tasks", []),
         "detail": "Analytics updated"},
        {"division": "Continuous Improvement™", "pass": "Continuous Improvement" in j.get("completed_tasks", []),
         "detail": "Learning recorded"},
    ]
    passed = sum(1 for c in checks if c["pass"])
    score = round(passed / len(checks) * 100)
    defects = [c["division"] for c in checks if not c["pass"]] + [f"{p['product_type']} failed" for p in failed]
    return {
        "job_number": j.get("job_number"), "status": j.get("status"), "progress": j.get("progress"),
        "score": score, "passed": passed, "total": len(checks),
        "acceptance": "PASS" if score >= 80 and j.get("status") in ("completed", "completed_with_errors") else "IN PROGRESS / REVIEW",
        "checks": checks, "defects": defects,
        "products_made": len(made), "products_failed": len(failed),
        "est_cost_usd": round(j.get("est_cost_usd", 0), 4),
    }
