import asyncio
import logging

from database import db
from models import gen_id, now_iso
from ai_service import llm_generate, parse_json, QRU_METHODOLOGY_SYSTEM
from org_activity import log_org

logger = logging.getLogger("qru.mfg")

# Which board department/agent voices each manufacturing batch (live activity feed).
BATCH_VOICE = {
    "Core Understanding": ("Legacy Bear™", "Education"),
    "Comprehension Aids": ("Legacy Bear™", "Education"),
    "Vocabulary & FAQ": ("Legacy Eagle™", "Strategy"),
    "Assessment": ("Kingdom Lion™", "Verification"),
    "Audience Versions": ("Consumer Advocate™", "Customer Experience"),
    "Guidance Notes": ("Legacy Bear™", "Education"),
    "Media & Product Assets": ("Creative Studio Director™", "Creative Studio"),
}

QRU_VOICE = (
    "You are the QRU Manufacturing Engine. QRU helps people become the best version of themselves "
    "through understanding. Your voice is empowering, hopeful, respectful, and intellectually honest. "
    "Never shame the learner; assume everyone is capable of growth. Teach HOW to think, not WHAT to think. "
    "Preserve truth — never present speculation as verified fact. Ground everything in the provided verified knowledge."
)

METHODOLOGY_FIELDS = [
    "the_question", "simple_answer", "why_it_matters", "real_world_example", "qru_translation",
    "everyday_analogy", "memory_sentence", "practice_application", "key_vocabulary", "deep_roots",
]

# (label, kind, spec)  kind: "methodology" | "generic"
BATCHES = [
    ("Core Understanding", "methodology", None),
    ("Comprehension Aids", "generic", {
        "summary": "string (2-3 sentence overview)",
        "conversation_starter": "string (one engaging question to spark a conversation)",
        "cheat_sheet": "string (a concise cheat sheet in markdown bullet form)",
        "common_misconceptions": "array of strings",
        "step_by_step": "array of strings (ordered explanation steps)",
        "applications": "array of strings",
        "benefits": "array of strings",
        "risks": "array of strings",
    }),
    ("Vocabulary & FAQ", "generic", {
        "vocabulary_decoder": "array of objects each with keys term and definition",
        "faq": "array of objects each with keys question and answer",
    }),
    ("Assessment", "generic", {
        "practice_questions": "array of strings",
        "reflection_questions": "array of strings",
        "kingdom_lion_questions": "array of strings (rigorous questions that test genuine understanding)",
        "quiz": "array of objects each with keys question, options (array of 4 strings), answer (the correct option text)",
        "certification_questions": "array of objects each with keys question, options (array of 4 strings), answer",
    }),
    ("Audience Versions", "generic", {
        "story_version": "string (a short narrative that teaches the concept)",
        "children_version": "string (for ages 6-10)",
        "teen_version": "string (for ages 13-17)",
        "adult_version": "string (for general adults)",
        "professional_version": "string (for domain professionals)",
    }),
    ("Guidance Notes", "generic", {
        "teacher_notes": "string", "parent_notes": "string", "student_notes": "string",
        "call_to_action": "string (an inspiring, concrete next step for the learner)",
    }),
    ("Media & Product Assets", "generic", {
        "visual_description": "string", "image_prompt": "string (a prompt for an image generator)",
        "infographic_text": "string", "poster_text": "string",
        "presentation_outline": "string (markdown outline)", "presentation_script": "string",
        "podcast_script": "string", "video_script": "string",
        "social_media_pack": "string (3-5 short posts)",
        "lesson_plan": "string (markdown)", "workbook_activities": "string (markdown)",
    }),
]

LIST_FIELDS = {
    "practice_application", "key_vocabulary", "common_misconceptions", "step_by_step",
    "applications", "benefits", "risks", "vocabulary_decoder", "faq", "practice_questions",
    "reflection_questions", "kingdom_lion_questions", "quiz", "certification_questions",
}

ALL_FIELDS = list(METHODOLOGY_FIELDS)
FIELD_HINTS = {}
for _label, _kind, _spec in BATCHES:
    if _spec:
        for _k, _v in _spec.items():
            ALL_FIELDS.append(_k)
            FIELD_HINTS[_k] = _v


def _is_filled(v):
    if isinstance(v, list):
        return len(v) > 0
    return bool(v and str(v).strip())


def _build_system(spec):
    keys = "\n".join(f'  "{k}": {v}' for k, v in spec.items())
    return QRU_VOICE + f"\nReturn ONLY valid JSON with EXACTLY these keys:\n{{\n{keys}\n}}\nDo not add markdown fences."


def _context(rec):
    return (
        f"Title: {rec.get('title','')}\nCategory: {rec.get('category','')}\n"
        f"Verified Truth: {rec.get('verified_truth','')}\n"
        f"QRU Translation: {rec.get('qru_translation','')}\n"
        f"Summary: {rec.get('summary','')}"
    )


async def _generate_batch(context, kind, spec, session):
    if kind == "methodology":
        raw = await llm_generate(QRU_METHODOLOGY_SYSTEM, context, session)
    else:
        raw = await llm_generate(_build_system(spec), context, session)
    return parse_json(raw) or {}


async def start_manufacturing_job(kr_id, actor):
    """Create a job record, kick off async processing, return the job id."""
    rec = await db.knowledge_records.find_one({"id": kr_id})
    if not rec:
        return None
    await log_org("Manufacturing Director™", "Manufacturing", "started full manufacturing for", rec.get("kr_code", ""))
    steps = [{"label": b[0], "status": "pending"} for b in BATCHES]
    steps.append({"label": "Understanding Manufactured", "status": "pending"})
    job = {
        "id": gen_id(),
        "kr_id": kr_id,
        "kr_code": rec.get("kr_code"),
        "title": rec.get("title"),
        "status": "running",
        "progress": 0,
        "current_step": steps[0]["label"],
        "steps": steps,
        "fields_manufactured": 0,
        "actor": actor,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.manufacturing_jobs.insert_one(dict(job))
    asyncio.create_task(_process_job(job["id"], kr_id, actor))
    return job["id"]


async def _process_job(job_id, kr_id, actor):
    try:
        total = len(BATCHES) + 1
        manufactured = 0
        for i, (label, kind, spec) in enumerate(BATCHES):
            job = await db.manufacturing_jobs.find_one({"id": job_id})
            if not job:
                return
            steps = job["steps"]
            steps[i]["status"] = "running"
            await db.manufacturing_jobs.update_one(
                {"id": job_id}, {"$set": {"steps": steps, "current_step": label, "updated_at": now_iso()}})
            voice = BATCH_VOICE.get(label, ("Manufacturing Director™", "Manufacturing"))
            await log_org(voice[0], voice[1], f"is manufacturing {label.lower()}", job.get("kr_code", ""))

            rec = await db.knowledge_records.find_one({"id": kr_id})
            field_status = rec.get("field_status", {})
            try:
                data = await _generate_batch(_context(rec), kind, spec, f"mfg-{kr_id}-{i}")
                fields = METHODOLOGY_FIELDS if kind == "methodology" else list(spec.keys())
                upd = {}
                for f in fields:
                    val = data.get(f)
                    if _is_filled(val) and not _is_filled(rec.get(f)):
                        upd[f] = val
                        field_status[f] = "Draft"
                        manufactured += 1
                upd["field_status"] = field_status
                upd["updated_at"] = now_iso()
                await db.knowledge_records.update_one({"id": kr_id}, {"$set": upd})
                steps[i]["status"] = "done"
            except Exception as e:
                logger.error(f"batch {label} failed: {e}")
                steps[i]["status"] = "failed"

            progress = round((i + 1) / total * 100)
            await db.manufacturing_jobs.update_one(
                {"id": job_id},
                {"$set": {"steps": steps, "progress": progress, "fields_manufactured": manufactured, "updated_at": now_iso()}})

        # finalize
        job = await db.manufacturing_jobs.find_one({"id": job_id})
        steps = job["steps"]
        steps[-1]["status"] = "done"
        final_status = "failed" if (manufactured == 0 and any(s["status"] == "failed" for s in steps)) else "complete"
        await db.manufacturing_jobs.update_one(
            {"id": job_id},
            {"$set": {"steps": steps, "progress": 100, "status": final_status,
                      "current_step": "Understanding Manufactured", "updated_at": now_iso()}})

        rec = await db.knowledge_records.find_one({"id": kr_id})
        history = rec.get("manufacturing_history", [])
        history.append({"job_id": job_id, "at": now_iso(), "by": actor, "fields": manufactured})
        await db.knowledge_records.update_one(
            {"id": kr_id}, {"$set": {"understanding_status": "Draft", "manufacturing_history": history}})
        await log_org("Manufacturing Director™", "Manufacturing", f"completed manufacturing — {manufactured} fields ready", rec.get("kr_code", ""), "success")
        await db.notifications.insert_one({
            "id": gen_id(), "message": f"Understanding manufactured for {rec.get('kr_code')} — {manufactured} fields ready for review",
            "level": "success", "read": False, "created_at": now_iso(),
        })
    except Exception as e:
        logger.error(f"job {job_id} crashed: {e}")
        await db.manufacturing_jobs.update_one({"id": job_id}, {"$set": {"status": "failed", "updated_at": now_iso()}})


async def regenerate_field(kr_id, field, actor):
    rec = await db.knowledge_records.find_one({"id": kr_id})
    if not rec or field not in ALL_FIELDS:
        return None
    if field in METHODOLOGY_FIELDS:
        data = await _generate_batch(_context(rec), "methodology", None, f"regen-{kr_id}-{field}")
    else:
        data = await _generate_batch(_context(rec), "generic", {field: FIELD_HINTS.get(field, "string")}, f"regen-{kr_id}-{field}")
    new_val = data.get(field)
    if not _is_filled(new_val):
        return rec
    # push previous value to version history
    versions = rec.get("field_versions", {})
    hist = versions.get(field, [])
    if _is_filled(rec.get(field)):
        hist.append({"value": rec.get(field), "at": now_iso()})
    versions[field] = hist
    field_status = rec.get("field_status", {})
    field_status[field] = "Draft"
    await db.knowledge_records.update_one(
        {"id": kr_id},
        {"$set": {field: new_val, "field_versions": versions, "field_status": field_status, "updated_at": now_iso()}})
    return await db.knowledge_records.find_one({"id": kr_id})
