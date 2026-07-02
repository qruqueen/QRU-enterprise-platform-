"""QRU Memory Engineering™ (text-first) — transforms verified understanding into
long-term memory. EXTENDS the Knowledge Master Record™ (memory assets are stored ON the
record, not in a separate silo), honoring Extend Before Expand™.

Music is one tool. Memory is the mission. This phase manufactures reusable text IP:
Memory Sentence/Hook/Chant, Call-and-Response, Character Scripts, Educational Lyrics,
Character Dialogue, adaptive Legacy Learners™ versions, and production-ready music prompts.
NO AI-generated songs/instrumentals yet (those become prompts for future rendering).
"""
import asyncio
import logging

from database import db
from models import now_iso
from ai_service import llm_generate, parse_json
from org_activity import log_org

logger = logging.getLogger("qru.memory")

# QRU Character Voices™ — consistent personalities learners come to trust.
CHARACTERS = [
    {"name": "Kingdom Lion™", "traits": ["Confident", "Protective", "Truth-focused", "Encouraging"],
     "role": "Guardian of verified truth", "voice": "Bold, reassuring, authoritative yet warm"},
    {"name": "Legacy Bear™", "traits": ["Patient", "Warm", "Gentle", "Teacher"],
     "role": "The patient teacher", "voice": "Slow, kind, nurturing"},
    {"name": "Legacy Eagle™", "traits": ["Strategic", "Thoughtful", "Big-picture"],
     "role": "The strategic thinker", "voice": "Measured, insightful, visionary"},
    {"name": "Queen Unity™", "traits": ["Compassionate", "Balanced", "Inclusive"],
     "role": "The compassionate connector", "voice": "Gentle, inclusive, harmonizing"},
    {"name": "Crowned Bull™", "traits": ["Practical", "Motivating", "Action-oriented"],
     "role": "The motivator", "voice": "Energetic, direct, driving"},
    {"name": "Royal Phoenix™", "traits": ["Creative", "Hopeful", "Future-focused"],
     "role": "The hopeful creative", "voice": "Uplifting, imaginative, inspiring"},
]

MEMORY_SYSTEM = """You are QRU Memory Engineering™. Transform ONE verified educational truth into memorable, reusable learning assets.
Do NOT invent facts — only reshape the given verified understanding for recall. Keep everything faithful to the source.
Return ONLY JSON with these keys:
{
 "memory_sentence": "one clear sentence capturing the core idea",
 "memory_hook": "a 5-15 second catchy line that reinforces ONE core idea (rhythmic, easy to remember)",
 "memory_chant": "a short call-out chant (2-4 lines)",
 "call_and_response": [{"call": "...", "response": "..."}, {"call": "...", "response": "..."}],
 "one_line_repeat": "a single line meant to be repeated for spaced repetition",
 "educational_lyrics": {"chorus": "4 lines", "verse": "4 lines"},
 "memory_rhythm": "describe the clap/rhythm pattern (e.g. clap-clap-rest) that fits the hook",
 "character_scripts": [{"character": "Kingdom Lion™", "script": "1-2 lines the character performs, in their voice"}, {"character": "Legacy Bear™", "script": "..."}],
 "character_dialogue": [{"character": "Legacy Bear™", "line": "..."}, {"character": "Crowned Bull™", "line": "..."}],
 "legacy_learners": {"child": "simple rhyme for young learners", "teen": "modern rhythmic hook", "adult": "short spoken affirmation", "professional": "concise memory phrase"},
 "music_prompt": "a production-ready prompt describing a song a music-gen service could create (style, tempo, mood, structure)",
 "instrumental_prompt": "a prompt for an instrumental study/theme track"
}"""


async def manufacture_memory_job(kr_id, actor):
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        return
    await db.knowledge_records.update_one({"id": kr_id}, {"$set": {"memory_status": "manufacturing"}})
    await log_org("Memory Engineering™", "Memory Engineering", "is engineering memory assets for", kr.get("kr_code", ""))
    source = "\n".join(filter(None, [
        f"Title: {kr.get('title')}",
        f"Simple Answer: {kr.get('simple_answer')}",
        f"QRU Translation: {kr.get('qru_translation')}",
        f"Why It Matters: {kr.get('why_it_matters')}",
        f"Everyday Analogy: {kr.get('everyday_analogy')}",
        f"Existing Memory Sentence: {kr.get('memory_sentence')}",
    ]))
    try:
        raw = await llm_generate(MEMORY_SYSTEM, source, f"memory-{kr_id}")
        assets = parse_json(raw)
        if not assets:
            raise ValueError("empty memory assets")
        assets["manufactured_at"] = now_iso()
        assets["characters_featured"] = [s.get("character") for s in assets.get("character_scripts", [])]
        await db.knowledge_records.update_one({"id": kr_id}, {"$set": {
            "memory_assets": assets, "memory_status": "manufactured", "updated_at": now_iso()}})
        # keep the canonical memory_sentence in sync if the record lacked one
        if not (kr.get("memory_sentence") or "").strip() and assets.get("memory_sentence"):
            await db.knowledge_records.update_one({"id": kr_id}, {"$set": {"memory_sentence": assets["memory_sentence"]}})
        await log_org("Memory Engineering™", "Memory Engineering", "manufactured memory assets for", kr.get("kr_code", ""), "success")
    except Exception as e:
        logger.error(f"memory manufacture failed for {kr_id}: {e}")
        await db.knowledge_records.update_one({"id": kr_id}, {"$set": {"memory_status": "failed"}})
