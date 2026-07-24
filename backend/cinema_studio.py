"""QRU Story & Cinema Studio™ + Podcast Studio™ (Stone 3 · Inheritance-First™).

Governed manufacturing departments for AUDIO and VIDEO — lighting up the Audio/Video
lanes of the Factory Map. Every production inherits from a verified Knowledge Record™
and is governed by the Approved Knowledge Record Manufacturing Standard™.

Truthful messaging (Treasure Standard™): video uses IMAGE-BASED MOTION (Ken Burns
zoompan over AI illustrations) with narration — NOT frame-by-frame cel animation.
Audio uses real OpenAI TTS narration.
"""
import os
import tempfile
import logging
from database import db
from models import gen_id, now_iso, clean
from ai_service import llm_generate, parse_json, generate_image
from media_production import _tts
from little_legacy_production import _render_pilot_mp4, _duration_from_bytes
import rendering_engine as re_engine
from media_division import _resolve_kr, _is_verified, _promise_manifest
from org_activity import log_org

logger = logging.getLogger("qru.cinema_studio")

PRODUCTIONS = "studio_productions"

FORMATS = [
    {"id": "audiobook", "name": "Audiobook", "dept": "Podcast Studio™", "kind": "audio",
     "technique": "OpenAI narration (TTS)", "words": 260},
    {"id": "podcast", "name": "Podcast Episode", "dept": "Podcast Studio™", "kind": "audio",
     "technique": "Narrated host episode (TTS)", "words": 300},
    {"id": "motion_storybook", "name": "Motion Storybook™", "dept": "Story & Cinema Studio™", "kind": "video",
     "technique": "Image-based motion (Ken Burns) + narration", "scenes": 3},
    {"id": "animated_episode", "name": "Educational Episode", "dept": "Story & Cinema Studio™", "kind": "video",
     "technique": "Image-based motion (Ken Burns) + narration", "scenes": 3},
    {"id": "youtube_short", "name": "YouTube Short", "dept": "Story & Cinema Studio™", "kind": "video",
     "technique": "Image-based motion (Ken Burns) + narration", "scenes": 2},
    {"id": "promo_video", "name": "Promotional Video", "dept": "Story & Cinema Studio™", "kind": "video",
     "technique": "Image-based motion (Ken Burns) + narration", "scenes": 3},
]
FMT = {f["id"]: f for f in FORMATS}

STD = ("Govern the voice by the Approved Knowledge Record Manufacturing Standard™: begin with hope and "
       "possibility, preserve dignity, teach capability first, warm/positive yet fully truthful. Use ONLY "
       "the verified knowledge provided — never invent facts.")

IMG_STYLE = ("QRU brand cinematic illustration: deep navy-to-royal-purple with warm gold light, elegant, "
             "aspirational, gallery quality. NO text, NO letters, NO logos.")


def _kr_context(kr):
    return (f"Topic: {kr.get('title')}\n"
            f"Verified Truth: {kr.get('verified_truth','')}\n"
            f"Why It Matters: {kr.get('why_it_matters','')}\n"
            f"Everyday Analogy: {kr.get('everyday_analogy','')}\n"
            f"Real-World Example: {kr.get('real_world_example','')}\n"
            f"Memorable Line: {kr.get('memory_sentence','')}")


def _chunk_for_tts(text, limit=3800):
    """Split narration into <=limit-char chunks on sentence/paragraph boundaries (OpenAI TTS caps at 4096)."""
    import re as _re
    text = (text or "").strip()
    if len(text) <= limit:
        return [text] if text else []
    # Prefer paragraph, then sentence boundaries.
    pieces = _re.split(r"(?<=[.!?])\s+|\n+", text)
    chunks, cur = [], ""
    for p in pieces:
        p = p.strip()
        if not p:
            continue
        while len(p) > limit:  # a single monster sentence — hard split
            if cur:
                chunks.append(cur); cur = ""
            chunks.append(p[:limit]); p = p[limit:]
        if len(cur) + len(p) + 1 <= limit:
            cur = (cur + " " + p).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = p
    if cur:
        chunks.append(cur)
    return chunks


async def _tts_bytes(text, voice="sage", speed=1.0):
    chunks = _chunk_for_tts(text)
    if not chunks:
        raise RuntimeError("No narration text to synthesize.")
    audio_parts = []
    for chunk in chunks:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
            path = tf.name
        try:
            res = await _tts(chunk, path, voice=voice, speed=speed)
            if res is True and os.path.exists(path):
                audio_parts.append(open(path, "rb").read())
            else:
                raise RuntimeError(res if isinstance(res, str) else "TTS produced no audio.")
        finally:
            if os.path.exists(path):
                os.remove(path)
    return b"".join(audio_parts)


async def _make_audio(kr, spec):
    if spec["id"] == "podcast":
        sys = (f"You are the host of the QRU Podcast. {STD} Write a spoken-word episode (~{spec['words']} words): "
               f"a warm welcome, the core idea explained through a relatable story/analogy, one thing the listener "
               f"can do today, and a hopeful sign-off. Natural spoken English, no stage directions, no markdown.")
    else:
        sys = (f"You are the QRU narrator. {STD} Write flowing audiobook narration (~{spec['words']} words) that "
               f"teaches this clearly and warmly. Natural spoken prose, no headings, no markdown, no stage directions.")
    script = await llm_generate(sys, _kr_context(kr), f"studio-audio-{kr.get('id')}-{spec['id']}")
    audio = await _tts_bytes(script)
    fid = re_engine._save(f"studio-{spec['id']}", "mp3", audio)
    return {"url": re_engine._asset_url(fid), "media_type": "audio/mpeg", "bytes": len(audio),
            "duration": round(_duration_from_bytes(audio), 1), "script": script}


async def _make_video(kr, spec):
    n = spec.get("scenes", 3)
    sys = (f"You are the QRU Story & Cinema Studio director. {STD} Plan a short narrated {spec['name']} in EXACTLY "
           f"{n} scenes. Return STRICT JSON: {{\"title\": str, \"scenes\": [{{\"narration\": \"~30 spoken words\", "
           f"\"visual\": \"a vivid concrete image description for an illustrator\"}}]}}. No markdown fences.")
    plan = parse_json(await llm_generate(sys, _kr_context(kr), f"studio-video-{kr.get('id')}-{spec['id']}")) or {}
    scenes = (plan.get("scenes") or [])[:n]
    if not scenes:
        raise RuntimeError("Scene plan was empty.")
    segments, durations, captions = [], [], []
    for i, sc in enumerate(scenes):
        narration = str(sc.get("narration") or "").strip() or kr.get("memory_sentence") or kr.get("title")
        visual = str(sc.get("visual") or "").strip() or kr.get("title")
        try:
            img = await generate_image(f"{visual}. {IMG_STYLE}", f"studio-scene-{kr.get('id')}-{spec['id']}-{i}")
        except Exception as e:
            raise RuntimeError(f"Scene image generation failed: {str(e)[:100]}")
        audio = await _tts_bytes(narration)
        segments.append((img, audio))
        durations.append(round(_duration_from_bytes(audio), 1))
        captions.append(narration)
    mp4 = _render_pilot_mp4(segments)
    fid = re_engine._save(f"studio-{spec['id']}", "mp4", mp4)
    return {"url": re_engine._asset_url(fid), "media_type": "video/mp4", "bytes": len(mp4),
            "duration": round(sum(durations), 1), "scenes": len(scenes),
            "title": plan.get("title") or kr.get("title"), "captions": captions}


async def manufacture(kr_id, format_id, actor="Founder"):
    spec = FMT.get(format_id)
    if not spec:
        return {"ok": False, "error": "Unknown format."}
    kr = await _resolve_kr(kr_id)
    if not kr:
        return {"ok": False, "error": "Knowledge Record not found."}
    if not _is_verified(kr):
        return {"ok": False, "error": "This Knowledge Record is not yet Verified. Approve it first — "
                "every production must inherit from verified knowledge (Knowledge-First)."}
    try:
        media = await _make_audio(kr, spec) if spec["kind"] == "audio" else await _make_video(kr, spec)
    except Exception as e:
        logger.warning(f"studio production failed [{format_id}]: {e}")
        return {"ok": False, "error": f"Production failed: {str(e)[:160]}"}

    prod = {
        "id": gen_id(), "kr_id": kr.get("id"), "kr_code": kr.get("kr_code"), "kr_title": kr.get("title"),
        "format": format_id, "name": spec["name"], "department": spec["dept"], "kind": spec["kind"],
        "technique": spec["technique"], "status": "Manufactured",
        "manufacturing_promise": _promise_manifest(kr), "created_by": actor, "created_at": now_iso(),
        **media,
    }
    await db[PRODUCTIONS].insert_one(dict(prod))
    await log_org(spec["dept"], "Video" if spec["kind"] == "video" else "Audio",
                  f"manufactured {spec['name']} from {kr.get('kr_code') or kr.get('title')}", kr.get("kr_code") or "", "success")
    prod.pop("_id", None)
    return {"ok": True, "production": clean(prod)}


async def list_productions(kr_id=None, limit=100):
    q = {"kr_id": kr_id} if kr_id else {}
    return await db[PRODUCTIONS].find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def stats():
    audio = await db[PRODUCTIONS].count_documents({"kind": "audio"})
    video = await db[PRODUCTIONS].count_documents({"kind": "video"})
    return {"audio_productions": audio, "video_productions": video, "formats": len(FORMATS)}
