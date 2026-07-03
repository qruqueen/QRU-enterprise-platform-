"""QRU AI Services Manager™ — coordinates every external AI production service.

The manager maps each production CAPABILITY (image, video, voice, etc.) to a
connected AI service (configured once in the QRU Integration Hub™), executes the
task, verifies completion, retries on failure, and records production history.

HONESTY NOTE:
- Text capabilities (scripts, quizzes, copy, translation, captions, etc.) run REAL
  via the Emergent LLM key.
- Image runs REAL via Gemini Nano Banana (Emergent key).
- PDF runs REAL via the rendering engine.
- Media render capabilities (video, animation, voice audio, music) require an external
  AI service; until that service's real credentials are activated in the Integration Hub,
  the manager produces the full spec/script and records a SIMULATED asset so the entire
  production line operates end-to-end. Activating a connector upgrades these to REAL.
"""
import logging

from database import db
from models import gen_id, now_iso
from ai_service import llm_generate, generate_image
from rendering_engine import _save, _asset_url
from org_activity import log_org

logger = logging.getLogger("qru.ai_services")

# Capability → preferred connected providers (first connected wins).
CAPABILITY_PROVIDERS = {
    "image": ["Gemini Nano Banana (Image)", "OpenAI Image"],
    "video": ["Runway (Video)", "Pika (Video)"],
    "animation": ["D-ID (Animation)"],
    "voice": ["ElevenLabs (Voice)", "OpenAI TTS (Voice)"],
    "music": ["Suno (Music)"],
    "presentation": ["Gamma (Presentation)"],
    "translation": ["DeepL (Translation)"],
    "caption": ["Whisper (Captions)"],
}

# Capabilities that run natively/REAL without an external connector.
NATIVE_TEXT = {"text", "translation", "caption", "subtitle", "quiz", "social",
               "website", "presentation", "document", "seo"}
NATIVE_IMAGE = {"image"}
MEDIA_CAPS = {"video", "animation", "voice", "music", "audio"}

ALL_CAPABILITIES = sorted(NATIVE_TEXT | NATIVE_IMAGE | MEDIA_CAPS)

# Capabilities now produced REAL natively (no external connector required):
#   voice/audio → OpenAI TTS (Emergent key) ; video/animation → ffmpeg slideshow (images + narration).
NATIVE_MEDIA = {"voice", "audio", "video", "animation"}

# Estimated Production Cost™ (USD) per capability — labelled "estimated" in the UI.
# Replaced automatically with actual provider billing when those APIs are wired.
CAP_UNIT_COST = {
    "text": 0.0, "quiz": 0.0, "social": 0.0, "seo": 0.0, "website": 0.0, "document": 0.0,
    "presentation": 0.0, "translation": 0.0, "caption": 0.0, "subtitle": 0.0,
    "image": 0.04, "voice": 0.015, "audio": 0.015, "video": 0.13, "animation": 0.13, "music": 0.0,
}


def estimate_cost(capability: str, content: str = "") -> float:
    base = CAP_UNIT_COST.get(capability, 0.0)
    if capability in NATIVE_TEXT:
        # ~ $0.60 / 1M output tokens, tokens ≈ chars/4
        return round(len(content or "") / 4 / 1_000_000 * 0.60, 6)
    if capability in ("voice", "audio"):
        return round(len(content or "") / 1000 * 0.015, 6)  # $0.015 / 1K chars (tts-1)
    return round(base, 6)


async def select_service(capability: str):
    """Return the connected provider for a capability, else None."""
    candidates = CAPABILITY_PROVIDERS.get(capability, [])
    for provider in candidates:
        conn = await db.integrations.find_one({"platform": provider, "status": "Connected"})
        if conn and conn.get("connection_health") not in ("error", "expired"):
            return provider
    return None


def capability_mode(capability: str, provider) -> str:
    if capability in NATIVE_TEXT or capability in NATIVE_IMAGE or capability in NATIVE_MEDIA:
        return "real"
    return "real" if provider else "simulated"


async def _record_job(capability, provider, mode, status, retries, detail="", cost=0.0):
    await db.ai_service_jobs.insert_one({
        "id": gen_id(), "capability": capability, "provider": provider or "native",
        "mode": mode, "status": status, "retries": retries, "detail": detail[:300],
        "est_cost_usd": round(float(cost or 0.0), 6), "at": now_iso(),
    })


async def _scene_images(title: str, script: str, session_id: str, count: int = 3):
    """Generate a few branded scene stills for a slideshow video; always returns >=1 image."""
    from rendering_engine import _placeholder_cover
    images = []
    beats = [b.strip() for b in (script or "").replace("\n", " ").split(".") if b.strip()][:count] or [title]
    for i, beat in enumerate(beats):
        prompt = (f"Premium educational slide illustration for a QRU video about '{title}'. "
                  f"Scene: {beat[:180]}. QRU brand: royal purple #35106A, gold #F5B21A, deep navy, "
                  f"clean white space, subtle shield motif. 16:9, flat vector, minimal text, high quality.")
        try:
            img = await generate_image(prompt, f"{session_id}-scene{i}")
        except Exception:
            img = None
        images.append(img or _placeholder_cover(title, "QRU", {}))
    return images


async def execute(capability: str, spec: dict, session_id: str, actor="AI Services Manager™") -> dict:
    """Execute one production task. spec may contain: system, prompt (text),
    image_prompt (image), title (media). Returns {status, mode, provider, content, asset_url}."""
    provider = await select_service(capability)
    mode = capability_mode(capability, provider)
    retries = 0
    last_err = ""

    for attempt in range(2):
        try:
            # --- REAL text-producing capabilities ---
            if capability in NATIVE_TEXT:
                content = await llm_generate(spec.get("system", ""), spec.get("prompt", ""), session_id)
                cost = estimate_cost(capability, content)
                await _record_job(capability, provider or "Emergent LLM", "real", "success", retries, cost=cost)
                return {"status": "success", "mode": "real", "provider": provider or "Emergent LLM",
                        "content": content, "asset_url": None, "est_cost_usd": cost}

            # --- REAL image ---
            if capability in NATIVE_IMAGE:
                img = await generate_image(spec.get("image_prompt", spec.get("prompt", "")), session_id)
                if img:
                    fid = _save("qru_asset", "png", img)
                    url = _asset_url(fid)
                    cost = estimate_cost("image")
                    await _record_job(capability, provider or "Gemini Nano Banana (Image)", "real", "success", retries, cost=cost)
                    return {"status": "success", "mode": "real",
                            "provider": provider or "Gemini Nano Banana (Image)",
                            "content": spec.get("caption", ""), "asset_url": url, "est_cost_usd": cost}
                raise RuntimeError("image generation returned no data")

            # --- REAL voice / audio narration (OpenAI TTS) — degrades gracefully ---
            if capability in ("voice", "audio"):
                import media_render as mr
                script = spec.get("script") or spec.get("prompt") or spec.get("title", "")
                try:
                    audio = await mr.synthesize_voice(script)
                    fid = _save("qru_voice", "mp3", audio)
                    url = _asset_url(fid)
                    cost = estimate_cost("voice", script)
                    await _record_job(capability, "OpenAI TTS (Voice)", "real", "success", retries, cost=cost)
                    return {"status": "success", "mode": "real", "provider": "OpenAI TTS (Voice)",
                            "content": script, "asset_url": url, "est_cost_usd": cost}
                except Exception as ve:
                    await _record_job(capability, "OpenAI TTS (Voice)", "degraded", "warning", retries, str(ve)[:120])
                    return {"status": "success", "mode": "degraded", "provider": "OpenAI TTS (Voice)",
                            "content": script, "asset_url": None, "est_cost_usd": 0,
                            "message": "AI voice narration temporarily unavailable — script prepared and saved; audio can be generated when capacity returns."}

            # --- REAL slideshow video (branded images + TTS narration → MP4) — degrades to SILENT ---
            if capability in ("video", "animation"):
                import media_render as mr
                script = spec.get("script") or spec.get("prompt") or spec.get("title", "")
                narrated, audio = True, b""
                try:
                    audio = await mr.synthesize_voice(script)
                except Exception:
                    narrated, audio = False, b""
                images = await _scene_images(spec.get("title", "QRU"), script, session_id)  # already degrades to branded placeholders
                mp4 = mr.make_slideshow_video(images, audio)
                if not mp4:
                    raise RuntimeError("slideshow assembly returned no data")
                fid = _save("qru_video", "mp4", mp4)
                url = _asset_url(fid)
                cost = (estimate_cost("voice", script) if narrated else 0) + len(images) * estimate_cost("image")
                await _record_job(capability, "QRU Slideshow Video™ (OpenAI TTS + Render)", "real" if narrated else "degraded",
                                  "success" if narrated else "warning", retries, cost=round(cost, 6))
                return {"status": "success", "mode": "real" if narrated else "degraded",
                        "provider": "QRU Slideshow Video™", "content": script,
                        "asset_url": url, "est_cost_usd": round(cost, 6),
                        "message": None if narrated else "Video produced as a silent branded slideshow — AI narration temporarily unavailable and can be added when capacity returns."}

            # --- MEDIA render still needing an external connector (e.g. music) ---
            if capability in MEDIA_CAPS:
                await _record_job(capability, provider, "simulated", "success", retries,
                                  "spec produced; dedicated generative provider not yet connected")
                return {"status": "success", "mode": "simulated", "provider": provider,
                        "content": spec.get("script", ""), "asset_url": None, "est_cost_usd": 0.0,
                        "note": f"{capability} render pending a dedicated AI Services connector"}

            raise ValueError(f"unknown capability: {capability}")
        except Exception as e:
            last_err = str(e)
            retries += 1
            logger.error(f"AI service {capability} attempt {attempt+1} failed: {e}")
            import asyncio
            await asyncio.sleep(1.5)

    await _record_job(capability, provider, mode, "failed", retries, last_err)
    await log_org("AI Services Manager™", "Manufacturing", f"{capability} task failed after retry", "", "error")
    return {"status": "failed", "mode": mode, "provider": provider, "content": "", "asset_url": None, "error": last_err}


async def status_summary():
    caps = []
    for c in ALL_CAPABILITIES:
        provider = await select_service(c)
        native_real = c in NATIVE_TEXT or c in NATIVE_IMAGE or c in NATIVE_MEDIA
        caps.append({"capability": c, "mode": capability_mode(c, provider),
                     "connected_provider": provider or ("Native (QRU)" if native_real else None),
                     "requires_connector": (c in MEDIA_CAPS) and (c not in NATIVE_MEDIA) and not provider})
    total = await db.ai_service_jobs.count_documents({})
    failed = await db.ai_service_jobs.count_documents({"status": "failed"})
    real = await db.ai_service_jobs.count_documents({"mode": "real"})
    cost_agg = await db.ai_service_jobs.aggregate(
        [{"$group": {"_id": None, "c": {"$sum": "$est_cost_usd"}}}]).to_list(1)
    est_cost = round(cost_agg[0]["c"], 4) if cost_agg else 0.0
    return {"capabilities": caps, "jobs_total": total, "jobs_failed": failed, "jobs_real": real,
            "estimated_cost_usd": est_cost, "capability_providers": CAPABILITY_PROVIDERS}
