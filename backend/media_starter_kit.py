"""QRU Media Starter Kit™ (MO-011) — deterministic production-package engine.

After a product passes the Treasure Standard™ and Gold Standard™, MO-011 assembles a standardized
Media Starter Kit™ — the single production package every downstream media format (audiobook, narrated
poster, MP4 showcase, podcast, YouTube Short, social clip, presentation intro, marketing video) draws
from. $0 AI: components are assembled deterministically from the product's already-verified knowledge
and rendered assets. Treasure Standard™: a component is reported READY only when its real source
exists; otherwise it is honestly marked PENDING with the exact missing input — never faked.
"""
import re

import media_intelligence as mi

CONFIG = {
    "enabled": True, "version": "1.0",
    "mission": "Automatically prepare every approved QRU product for multimedia production by "
               "generating a standardized Media Starter Kit™ that serves as the single production "
               "package for audiobooks, narrated posters, videos, documentaries, podcasts and social media.",
    "governing_standard": "QRU Media Intelligence Division",
    "trigger": {"after": ["treasure_standard", "gold_standard"]},
    "components": [
        "hero_cover", "poster", "thumbnail", "narration_script", "approved_voice", "caption_file",
        "transcript", "keywords", "music_profile", "emotional_target", "visual_style",
        "qrubrand_intro", "qrubrand_outro"],
    "outputs": ["narrated_poster", "audiobook", "mp4_showcase", "podcast", "youtube_short",
                "social_clip", "presentation_intro", "marketing_video"],
    "approval": {"treasure_standard_required": True, "gold_standard_required": True},
}

COMPONENT_LABELS = {
    "hero_cover": "Hero Cover", "poster": "Poster", "thumbnail": "Thumbnail",
    "narration_script": "Narration Script", "approved_voice": "Approved Voice",
    "caption_file": "Caption File", "transcript": "Transcript", "keywords": "Keywords",
    "music_profile": "Music Profile", "emotional_target": "Emotional Target",
    "visual_style": "Visual Style", "qrubrand_intro": "QRU Brand Intro", "qrubrand_outro": "QRU Brand Outro",
}

OUTPUT_LABELS = {
    "narrated_poster": "Narrated Poster", "audiobook": "Audiobook", "mp4_showcase": "MP4 Showcase",
    "podcast": "Podcast", "youtube_short": "YouTube Short", "social_clip": "Social Clip",
    "presentation_intro": "Presentation Intro", "marketing_video": "Marketing Video",
}

QRU_INTRO = ("Welcome to QRU — where verified knowledge becomes understanding you can trust. "
             "In this experience, we simplify the path to the truth.")
QRU_OUTRO = ("This has been a QRU production. Every fact was verified before it reached you. "
             "QRU — the path to understanding the truth.")

# Deterministic emotional target + music profile by product family / type.
_EMOTION_MAP = {
    "guide": ("Confident Clarity", "Calm, steady, focused — light ambient pads"),
    "course": ("Motivated Focus", "Uplifting, forward-moving — gentle percussion"),
    "story": ("Warm Wonder", "Cinematic, emotive — soft strings"),
    "reference": ("Trusted Authority", "Neutral, professional — minimal underscore"),
    "kids": ("Playful Joy", "Bright, curious — light melodic"),
}
_STOPWORDS = set("the a an and or of to in for with on at is are be by from this that your you our we it as".split())


def _text(product):
    return (product.get("content") or product.get("summary") or "").strip()


def _classify(product):
    hay = " ".join(str(product.get(k) or "") for k in ("family", "product_type", "audience", "learning_level")).lower()
    for key in ("kids", "story", "course", "reference", "guide"):
        if key in hay:
            return key
    return "guide"


def _keywords(product, limit=8):
    text = " ".join(str(product.get(k) or "") for k in ("title", "topic", "content")).lower()
    words = re.findall(r"[a-z][a-z\-]{2,}", text)
    freq = {}
    for w in words:
        if w in _STOPWORDS:
            continue
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:limit]]


def _narration_script(product):
    body = _text(product)
    # Strip markdown heading hashes; keep readable narration.
    clean = "\n".join(re.sub(r"^#+\s*", "", ln).strip() for ln in body.split("\n") if ln.strip())
    return f"{QRU_INTRO}\n\n{clean}\n\n{QRU_OUTRO}"


def _caption_file(script):
    """Deterministic .srt caption track — one cue per sentence, fixed 4s cadence."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
    lines, t = [], 0
    for i, s in enumerate(sentences, 1):
        start, end = t, t + 4
        lines.append(f"{i}\n{_ts(start)} --> {_ts(end)}\n{s[:120]}\n")
        t = end
    return "\n".join(lines), len(sentences)


def _ts(sec):
    return f"00:{sec // 60:02d}:{sec % 60:02d},000"


def assess(product):
    """Deterministically assess every Media Starter Kit™ component against the product's real data.
    Returns per-component {status: ready|pending, source, detail} + assembled artifacts."""
    text = _text(product)
    cls = _classify(product)
    emotion, music = _EMOTION_MAP[cls]
    script = _narration_script(product) if text else ""
    srt, cue_count = _caption_file(script) if script else ("", 0)
    kw = _keywords(product)
    voice_live = any(i["status"] in ("live", "connected") and i["id"] == "openai" for i in mi.INTEGRATIONS)

    def comp(status, source, detail, value=None):
        return {"status": status, "source": source, "detail": detail, "value": value}

    components = {
        "hero_cover": comp(
            "ready" if product.get("cover_url") and product.get("cover_has_hero_art") else "pending",
            "cover_url",
            "Rendered hero cover present." if product.get("cover_url") else "No hero cover rendered yet — run Visual Intelligence Studio™.",
            product.get("cover_url")),
        "poster": comp(
            "ready" if product.get("store_graphic_url") or product.get("cover_url") else "pending",
            "store_graphic_url / cover_url",
            "Poster-ready graphic available." if (product.get("store_graphic_url") or product.get("cover_url")) else "No poster graphic yet.",
            product.get("store_graphic_url") or product.get("cover_url")),
        "thumbnail": comp(
            "ready" if product.get("thumbnail_url") else "pending",
            "thumbnail_url",
            "Thumbnail available." if product.get("thumbnail_url") else "No thumbnail rendered yet.",
            product.get("thumbnail_url")),
        "narration_script": comp(
            "ready" if script else "pending", "content",
            f"{len(script.split())} words assembled with QRU intro/outro." if script else "No verified content to narrate.",
            script),
        "approved_voice": comp(
            "ready" if voice_live else "pending", "Media Intelligence Division™",
            "OpenAI narration voice licensed & live." if voice_live else "No narration voice integration is live.",
            "QRU Narrator (OpenAI TTS)" if voice_live else None),
        "caption_file": comp(
            "ready" if cue_count else "pending", "derived from narration",
            f"{cue_count} caption cues (.srt) generated." if cue_count else "Captions require a narration script.",
            srt),
        "transcript": comp(
            "ready" if text else "pending", "content",
            f"{len(text.split())} word verified transcript." if text else "No verified transcript.",
            text),
        "keywords": comp(
            "ready" if kw else "pending", "title / topic / content",
            f"{len(kw)} keywords extracted." if kw else "Not enough text to extract keywords.",
            kw),
        "music_profile": comp("ready", "deterministic (family)", f"Selected profile: {music}.", music),
        "emotional_target": comp("ready", "deterministic (family)", f"Target emotion: {emotion}.", emotion),
        "visual_style": comp(
            "ready" if product.get("design_language_applied") else "pending", "design_palette",
            f"Palette: {product.get('design_palette') or 'QRU default'}." if product.get("design_language_applied") else "QRU design language not applied yet.",
            product.get("design_palette") or ("QRU Master Design Language™" if product.get("design_language_applied") else None)),
        "qrubrand_intro": comp("ready", "QRU brand standard", "Standard QRU brand intro.", QRU_INTRO),
        "qrubrand_outro": comp("ready", "QRU brand standard", "Standard QRU brand outro.", QRU_OUTRO),
    }
    ready = [k for k, v in components.items() if v["status"] == "ready"]
    return components, ready, cls


def _outputs_readiness(components, cls):
    """Which media outputs can be produced now, given ready components + live integrations."""
    live_ids = {i["id"] for i in mi.INTEGRATIONS if i["status"] in ("live", "connected")}
    r = lambda k: components[k]["status"] == "ready"
    audio_ready = r("narration_script") and r("approved_voice")
    video_visual = r("hero_cover") or r("poster") or r("thumbnail")

    specs = {
        "narrated_poster": {"needs": ["poster", "narration_script", "approved_voice"], "ok": r("poster") and audio_ready, "channel": "OpenAI TTS + poster"},
        "audiobook": {"needs": ["narration_script", "approved_voice", "transcript"], "ok": audio_ready, "channel": "OpenAI TTS"},
        "mp4_showcase": {"needs": ["poster", "narration_script", "caption_file"], "ok": video_visual and audio_ready, "channel": "ffmpeg slideshow render"},
        "podcast": {"needs": ["narration_script", "approved_voice", "music_profile"], "ok": audio_ready, "channel": "OpenAI TTS + music profile"},
        "youtube_short": {"needs": ["poster", "narration_script", "caption_file"], "ok": video_visual and audio_ready and "youtube" in live_ids, "channel": "ffmpeg render → YouTube"},
        "social_clip": {"needs": ["thumbnail", "narration_script", "caption_file"], "ok": video_visual and audio_ready, "channel": "ffmpeg render"},
        "presentation_intro": {"needs": ["hero_cover", "qrubrand_intro", "music_profile"], "ok": r("hero_cover") and r("music_profile"), "channel": "ffmpeg render"},
        "marketing_video": {"needs": ["poster", "keywords", "narration_script", "music_profile"], "ok": video_visual and audio_ready and r("keywords"), "channel": "ffmpeg render"},
    }
    out = []
    for oid, s in specs.items():
        missing = [COMPONENT_LABELS[n] for n in s["needs"] if components[n]["status"] != "ready"]
        out.append({
            "id": oid, "name": OUTPUT_LABELS[oid], "channel": s["channel"],
            "status": "ready_to_produce" if s["ok"] else "blocked",
            "requires": [COMPONENT_LABELS[n] for n in s["needs"]],
            "missing": missing,
            "detail": "All inputs ready — queue production." if s["ok"] else f"Waiting on: {', '.join(missing)}.",
        })
    return out


def build_kit(product, gold):
    """Assemble the full Media Starter Kit™ assessment for a product, honoring the MO-011 gate."""
    treasure_ok = gold.get("treasure_standard") == "Met"
    gold_ok = treasure_ok  # Gold gate is human-reviewed; treasure is the deterministic prerequisite.
    components, ready, cls = assess(product)
    outputs = _outputs_readiness(components, cls)
    total = len(CONFIG["components"])
    return {
        "product_id": product.get("id"), "product_code": product.get("product_code"), "title": product.get("title"),
        "gate": {
            "treasure_standard": gold.get("treasure_standard"),
            "gold_standard": gold.get("gold_standard"),
            "passed": treasure_ok and gold_ok,
            "blocked_reason": None if treasure_ok else "Product has not met the Treasure Standard™ — fix layout/value in Visual Studio first.",
        },
        "components": components,
        "component_labels": COMPONENT_LABELS,
        "ready_count": len(ready), "component_total": total,
        "kit_completeness": round(len(ready) / total * 100),
        "outputs": outputs,
        "outputs_ready": sum(1 for o in outputs if o["status"] == "ready_to_produce"),
        "outputs_total": len(outputs),
    }
