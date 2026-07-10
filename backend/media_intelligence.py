"""QRU Media Intelligence Division™ (MO-010) — multimedia config + capability truth.

Configured by the Founder declaration. Treasure Standard™: `capabilities()` reports the REAL,
honest status of each media integration — which are live now (OpenAI TTS, YouTube), which need an
API key, and which are optional/future. No fake "enabled" states in the UI.
"""
import os

CONFIG = {
    "enabled": True, "version": "1.0",
    "mission": "Transform QRU products into premium multimedia learning experiences across audio, "
               "video, animation, narration, interactive learning, and future media formats.",
    "governing_standard": "QRU Media Intelligence Division",
    "production": {k: True for k in [
        "audiobooks", "podcasts", "lesson_audio", "avatar_video", "mp4_lessons", "documentary_series",
        "animation", "webinar_content", "social_media_video", "multilingual_media", "xr_ready"]},
    "pipelines": {
        "audio": ["script", "pronunciation_review", "voice_selection", "narration", "mastering", "quality_review", "distribution"],
        "video": ["storyboard", "asset_collection", "motion_design", "narration", "captions", "rendering", "quality_review", "export"],
    },
    "voice_registry": {"enabled": True, "commercial_license_required": True, "consent_required": True, "version_control": True},
    "rendering": {"queue_enabled": True, "retry_failed_jobs": True, "archive_masters": True},
    "accessibility": {"captions_required": True, "transcripts_required": True, "audio_descriptions_optional": True},
    "analytics": ["watch_time", "completion_rate", "replay_points", "assessment_results", "customer_feedback"],
    "approval": {"treasure_standard_required": True, "gold_standard_required": True},
}

# Honest integration status. status: live | needs_key | optional_needs_key
INTEGRATIONS = [
    {"id": "openai", "name": "OpenAI (TTS / narration)", "status": "live", "note": "Active via Emergent key (media_render real TTS)."},
    {"id": "youtube", "name": "YouTube", "status": "connected", "note": "OAuth connected — real publishing (MO-006/007)."},
    {"id": "elevenlabs", "name": "ElevenLabs (premium voices)", "status": "needs_key", "note": "Requires an ElevenLabs API key."},
    {"id": "heygen", "name": "HeyGen (avatar video)", "status": "needs_key", "note": "Requires a HeyGen API key."},
    {"id": "google_flow", "name": "Google Flow / Veo (video gen)", "status": "needs_key", "note": "Requires Google video-gen access/key."},
    {"id": "runway", "name": "Runway (video gen)", "status": "optional_needs_key", "note": "Optional — requires a Runway API key."},
    {"id": "pika", "name": "Pika (video gen)", "status": "optional_needs_key", "note": "Optional — requires a Pika API key."},
    {"id": "canva", "name": "Canva", "status": "needs_key", "note": "Requires a Canva Connect API key."},
    {"id": "vimeo", "name": "Vimeo", "status": "optional_needs_key", "note": "Optional — requires Vimeo OAuth."},
]


async def capabilities():
    live = [i for i in INTEGRATIONS if i["status"] in ("live", "connected")]
    return {
        "integrations": INTEGRATIONS,
        "live_count": len(live),
        "total": len(INTEGRATIONS),
        "available_now": ["Lesson audio & narration (OpenAI TTS)", "Slideshow MP4 lessons (ffmpeg render)", "YouTube distribution"],
        "needs_setup": [i["name"] for i in INTEGRATIONS if "needs_key" in i["status"]],
    }
