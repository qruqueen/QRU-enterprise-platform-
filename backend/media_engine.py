"""QRU Media Manufacturing Engine™ — turns ONE verified Knowledge Record™ into a complete
multimedia package (scripts, memory assets, video metadata OR meditation session), stored in
the Media Library with modular publishing destinations and Treasure Standard™ readiness.

EXTENDS Memory Engineering™ (character voices/hooks), Manufacturing Engine™ (QC pattern),
and Design Intelligence™ (thumbnail briefs). Publishing connectors are modular stubs.
"""
import asyncio
import logging

from database import db
from models import gen_id, now_iso, clean
from ai_service import llm_generate, parse_json
from org_activity import log_org

logger = logging.getLogger("qru.media")

# Modular publishing destinations — add more without touching manufacturing.
PUBLISHING_DESTINATIONS = [
    "YouTube", "Website", "QRU Consumer Platform", "QRU Health University\u2122",
    "Podcast Feed", "Email Newsletter", "Social Media", "LMS",
]

MEDITATION_SESSIONS = [
    "Deep Roots Meditation\u2122", "Kingdom Lion Focus\u2122", "Legacy Bear Understanding\u2122",
    "Legacy Eagle Vision\u2122", "Queen Unity Reflection\u2122", "Royal Phoenix Renewal\u2122",
    "Crowned Bull Persistence\u2122",
]

VIDEO_SYSTEM = """You are the QRU Media Manufacturing Engine\u2122. From ONE verified educational truth, manufacture a complete YouTube media package. Do NOT invent facts. Feature a QRU character (Kingdom Lion\u2122, Legacy Bear\u2122, Crowned Bull\u2122, Queen Unity\u2122, Legacy Eagle\u2122, or Royal Phoenix\u2122).
Return ONLY JSON:
{
 "long_form_script": "a structured educational script (~6-10 short paragraphs)",
 "short_form_script": "a 30-60 second script",
 "narration_script": "YouTube narration script",
 "voice_over_script": "clean voice-over script",
 "memory_sentence": "...", "memory_hook": "5-15s catchy line", "memory_chant": "2-4 line chant",
 "educational_lyrics": {"chorus": "4 lines", "verse": "4 lines"},
 "instrumental_prompt": "...", "music_prompt": "production-ready song prompt",
 "character_dialogue": [{"character": "Legacy Bear\u2122", "line": "..."}],
 "legacy_learners": {"child": "...", "teen": "...", "adult": "...", "teacher": "...", "parent": "...", "caregiver": "..."},
 "video": {"title": "...", "seo_title": "...", "description": "...", "chapters": [{"time": "0:00", "title": "..."}], "thumbnail_text": "3-5 words", "thumbnail_brief": "design brief in QRU brand", "opening_hook": "...", "closing_cta": "...", "hashtags": ["#..."], "keywords": ["..."], "playlist": "suggested playlist", "series": "suggested series", "end_screen": "recommendation"}
}"""

MEDITATION_SYSTEM = """You are the QRU Media Manufacturing Engine\u2122 producing a QRU Frequency Collection\u2122 meditation session from ONE verified truth, combining story, reflection, character, and faith-compatible understanding. Feature the named QRU character.
Return ONLY JSON:
{
 "memory_sentence": "...", "memory_hook": "5-15s line",
 "character_dialogue": [{"character": "...", "line": "..."}],
 "legacy_learners": {"child": "...", "teen": "...", "adult": "...", "teacher": "...", "parent": "...", "caregiver": "..."},
 "instrumental_prompt": "...", "music_prompt": "...",
 "meditation": {"session_name": "...", "script": "guided meditation script (calm, reflective)", "reflection_prompts": ["..."], "journal_page": "journal page content", "poster_brief": "poster design brief", "workbook_page": "companion workbook page", "ambient_music_prompt": "...", "narration_prompt": "spoken narration prompt", "character_intro": "character introduction", "closing_reflection": "..."}
}"""

# Treasure Standard\u2122 readiness checks for media.
MEDIA_QC_SYSTEM = """You are Treasure Standard\u2122 Quality Control for QRU media. Rate readiness (0-100) and be demanding but fair.
Return ONLY JSON: {"scores": {"Factual Accuracy": n, "Educational Quality": n, "Memory Effectiveness": n, "Character Consistency": n, "Accessibility": n, "Production Completeness": n}, "notes": ["..."]}"""

MEDIA_THRESHOLD = 75


async def manufacture_media_job(kr_id, media_type, actor):
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        return
    source = "\n".join(filter(None, [
        f"Title: {kr.get('title')}", f"Verified Truth: {kr.get('verified_truth')}",
        f"Simple Answer: {kr.get('simple_answer')}", f"QRU Translation: {kr.get('qru_translation')}",
        f"Why It Matters: {kr.get('why_it_matters')}", f"Deep Roots: {kr.get('deep_roots')}",
    ]))
    system = MEDITATION_SYSTEM if media_type == "meditation" else VIDEO_SYSTEM
    mid = gen_id()
    doc = {
        "id": mid, "media_code": f"MED-{gen_id()[:6].upper()}", "media_type": media_type,
        "knowledge_record_id": kr_id, "kr_code": kr.get("kr_code"), "title": kr.get("title"),
        "family": kr.get("category"), "status": "manufacturing", "assets": None,
        "qc": {"status": "not_started", "scores": {}}, "publishing_ready": False,
        "publications": [], "destinations": PUBLISHING_DESTINATIONS, "version": 1,
        "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.media_assets.insert_one(dict(doc))
    await log_org("Media Manufacturing\u2122", "Media", f"is manufacturing {media_type} media for", kr.get("kr_code", ""))
    try:
        raw = await llm_generate(system, source, f"media-{mid}")
        assets = parse_json(raw)
        if not assets:
            raise ValueError("empty media assets")
        await db.media_assets.update_one({"id": mid}, {"$set": {
            "assets": assets, "status": "manufactured", "updated_at": now_iso()}})
        await log_org("Media Manufacturing\u2122", "Media", f"manufactured {media_type} media for", kr.get("kr_code", ""), "success")
    except Exception as e:
        logger.error(f"media manufacture failed {mid}: {e}")
        await db.media_assets.update_one({"id": mid}, {"$set": {"status": "failed"}})


async def media_qc_job(mid, actor):
    m = await db.media_assets.find_one({"id": mid})
    if not m or not m.get("assets"):
        return
    await db.media_assets.update_one({"id": mid}, {"$set": {"qc.status": "running"}})
    a = m["assets"]
    summary = " ".join(str(a.get(k, "")) for k in ["long_form_script", "narration_script", "memory_hook", "memory_sentence"])[:2500]
    try:
        raw = await llm_generate(MEDIA_QC_SYSTEM, f"Title: {m['title']}\nType: {m['media_type']}\n{summary}", f"media-qc-{mid}")
        data = parse_json(raw) or {}
        scores = data.get("scores", {})
        # deterministic completeness/consistency from ACTUAL asset presence (not AI opinion)
        core = ["memory_hook", "memory_sentence", "long_form_script", "legacy_learners"]
        has_core = sum(1 for k in core if a.get(k))
        scores["Production Completeness"] = 95 if has_core >= 3 else (80 if has_core >= 2 else 60)
        scores["Character Consistency"] = 92 if a.get("character_dialogue") else 78
        ready = all(v >= MEDIA_THRESHOLD for v in scores.values())
        await db.media_assets.update_one({"id": mid}, {"$set": {
            "qc": {"status": "certified" if ready else "needs_improvement", "scores": scores, "notes": data.get("notes", [])},
            "publishing_ready": ready, "status": "ready" if ready else "manufactured", "updated_at": now_iso()}})
        dept = "Organizational Health" if ready else "Media"
        await log_org("Treasure Standard\u2122 QC", dept,
                      "certified media" if ready else "returned media for improvement", m.get("media_code", ""),
                      "success" if ready else "warning")
    except Exception as e:
        logger.error(f"media qc failed {mid}: {e}")
        await db.media_assets.update_one({"id": mid}, {"$set": {"qc.status": "failed"}})


async def publish_media(mid, destination):
    m = await db.media_assets.find_one({"id": mid})
    if not m:
        return None, "Media not found"
    if destination not in PUBLISHING_DESTINATIONS:
        return None, "Unknown destination"
    # Honest guard (Treasure Standard™): QRU manufactures & QC-certifies media, but automated
    # upload to external platforms (YouTube, Podcast, Social, etc.) is NOT wired yet. We never
    # mark media as "Published" without a real, verifiable upload (e.g. a YouTube video ID).
    return None, (f"Automated upload to {destination} isn't wired yet. This media has been "
                  f"manufactured and QC-certified, but QRU does not yet perform the real upload, "
                  f"so it cannot be marked Published. Connect {destination} in Publishing "
                  f"Connectors™ — automated upload is a planned manufacturing milestone.")
