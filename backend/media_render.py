"""QRU Media Render™ — REAL spoken narration (OpenAI TTS via Emergent key) and
slideshow video assembly (branded images + narration → MP4 via ffmpeg).

Replaces SIMULATED voice/video where real production is technically feasible.
"""
import os
import re
import logging
import tempfile
import subprocess
import imageio_ffmpeg

from emergentintegrations.llm.openai import OpenAITextToSpeech

logger = logging.getLogger("qru.media_render")

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
TTS_MODEL = "tts-1"
DEFAULT_VOICE = "fable"          # expressive, storytelling
MAX_TTS_CHARS = 8000             # bound cost/time per asset


def _clean_for_tts(text: str) -> str:
    t = re.sub(r"https?://\S+", "", text or "")
    t = re.sub(r"[#*_`>|]", " ", t)
    t = re.sub(r"\[[^\]]*\]", " ", t)   # drop [stage directions]
    t = re.sub(r"\s+", " ", t).strip()
    return t[:MAX_TTS_CHARS]


def _chunk(text: str, size: int = 3500):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > size:
            if cur:
                out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out or [""]


async def synthesize_voice(text: str, voice: str = DEFAULT_VOICE, model: str = TTS_MODEL) -> bytes:
    """Return MP3 bytes of narrated text (chunks joined)."""
    clean = _clean_for_tts(text)
    if not clean:
        clean = "Welcome to QRU. Understanding, manufactured from verified knowledge."
    tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
    audio = bytearray()
    n = 0
    for chunk in _chunk(clean):
        part = await tts.generate_speech(text=chunk, model=model, voice=voice, response_format="mp3")
        audio.extend(part)
        n += 1
    try:
        import cost_meter
        await cost_meter.record("tts", units=n, est_cost=round(cost_meter.UNIT_COST["tts"] * max(n, 1), 4))
    except Exception:
        pass
    return bytes(audio)


def _audio_duration(path: str) -> float:
    try:
        out = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True, text=True, timeout=30)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", out.stderr)
        if m:
            h, mi, s = m.groups()
            return int(h) * 3600 + int(mi) * 60 + float(s)
    except Exception:
        pass
    return 0.0


def make_slideshow_video(images: list, audio_bytes: bytes) -> bytes:
    """Assemble branded images + narration audio into a 720p MP4 slideshow."""
    if not images:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        has_audio = bool(audio_bytes)
        audio_path = os.path.join(tmp, "audio.mp3")
        if has_audio:
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
            dur = _audio_duration(audio_path) or (len(images) * 5.0)
        else:
            dur = len(images) * 5.0
        per = max(2.5, dur / len(images))

        paths = []
        for i, img in enumerate(images):
            p = os.path.join(tmp, f"img{i}.png")
            with open(p, "wb") as f:
                f.write(img)
            paths.append(p)

        listfile = os.path.join(tmp, "list.txt")
        lines = []
        for p in paths:
            lines.append(f"file '{p}'")
            lines.append(f"duration {per:.2f}")
        lines.append(f"file '{paths[-1]}'")   # concat demuxer needs the last file repeated
        with open(listfile, "w") as f:
            f.write("\n".join(lines))

        out = os.path.join(tmp, "out.mp4")
        cmd = [
            FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-i", audio_path,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
                   "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x221A42,setsar=1,format=yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest", out,
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        with open(out, "rb") as f:
            return f.read()
