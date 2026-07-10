"""QRU Media Production Pipeline™ — first live end-to-end proof (Milestone 001).

Runs the governed workflow on a real licensed stock asset:
  live search → recommend → approve → license verify → download+checksum → register →
  narration (OpenAI TTS) → captions (.srt) → MP4 render (ffmpeg) → quality review →
  Master Asset Vault™ → distribution ready.

$0-safe & honest: if narration (TTS) is unavailable, the video still renders from the licensed
background with an honest note — no step is faked. Every asset preserves full provenance + checksum.
"""
import os
import re
import hashlib
import asyncio
import subprocess

import httpx
from dotenv import load_dotenv

from database import db
from models import gen_id, now_iso

load_dotenv()

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), "rendered_assets", "media_masters")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

NARRATION = (
    "Take a slow breath. As the sun rises over the quiet forest, let your mind settle and your "
    "thoughts grow clear. Understanding begins in stillness. This is a QRU reflection — a moment "
    "to renew your focus before the day ahead."
)


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _srt(text, seconds_per_cue=4):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    lines, t = [], 0
    for i, s in enumerate(sentences, 1):
        a, b = t, t + seconds_per_cue
        lines.append(f"{i}\n{_ts(a)} --> {_ts(b)}\n{s}\n")
        t = b
    return "\n".join(lines)


def _ts(sec):
    return f"00:{sec // 60:02d}:{sec % 60:02d},000"


async def _download(url):
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as c:
        r = await c.get(url)
    r.raise_for_status()
    return r.content


async def _tts(text, path):
    """Generate narration via OpenAI TTS (Emergent key). Returns True on success, else honest False."""
    try:
        from emergentintegrations.llm.openai import OpenAITextToSpeech
        tts = OpenAITextToSpeech(api_key=os.getenv("EMERGENT_LLM_KEY"))
        audio = await tts.generate_speech(text=text, model="tts-1", voice="sage")
        with open(path, "wb") as f:
            f.write(audio)
        return os.path.getsize(path) > 1000
    except Exception as e:
        return str(e)


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    return p.returncode, p.stderr[-600:]


def _ffprobe(path):
    code, _ = _run(["ffprobe", "-v", "error", "-show_entries",
                    "format=duration,size:stream=codec_type,width,height", "-of", "json", path])
    import json
    p = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json",
                        "-show_format", "-show_streams", path], capture_output=True, text=True)
    try:
        data = json.loads(p.stdout)
    except Exception:
        return {}
    streams = data.get("streams", [])
    vid = next((s for s in streams if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    return {"duration": float(data.get("format", {}).get("duration", 0) or 0),
            "size": int(data.get("format", {}).get("size", 0) or 0),
            "width": vid.get("width"), "height": vid.get("height"), "has_audio": has_audio}


async def produce_showcase(item, product_title, actor, milestone=None):
    steps = []

    def step(name, status, detail, **extra):
        steps.append({"step": name, "status": status, "detail": detail, **extra})

    job_id = gen_id()
    work = os.path.join(MEDIA_ROOT, job_id)
    os.makedirs(work, exist_ok=True)

    # 1. Live search result (already recommended) + human approval (endpoint = approval action).
    step("live_provider_search", "ok", f"Selected {item.get('provider')} asset {item.get('provider_asset_id')} for '{product_title}'.")
    step("asset_recommendation", "ok", f"Recommended: {str(item.get('title'))[:60]}")
    step("human_approval", "ok", f"Approved by {actor}.")

    # 2. License verification (FR-097).
    commercial = item.get("commercial_use_allowed")
    if commercial is False:
        step("license_verification", "blocked", "Commercial use not permitted — asset blocked.")
        return {"ok": False, "steps": steps, "job_id": job_id}
    step("license_verification", "ok", f"{item.get('license_type')} · commercial use {'confirmed' if commercial else 'assumed per provider terms'}.")

    # 3. Download + checksum.
    file_url = item.get("file_url")
    if not file_url:
        step("download", "failed", "No downloadable file URL on this asset.")
        return {"ok": False, "steps": steps, "job_id": job_id}
    try:
        data = await _download(file_url)
    except Exception as e:
        step("download", "failed", f"Download error: {str(e)[:100]}")
        return {"ok": False, "steps": steps, "job_id": job_id}
    master_path = os.path.join(work, "master.mp4")
    with open(master_path, "wb") as f:
        f.write(data)
    checksum = _sha256(data)
    step("download", "ok", f"Downloaded {len(data):,} bytes.", checksum=checksum[:24], bytes=len(data))

    # 4. Register source asset in Master Asset Vault™ with full provenance.
    source_doc = {
        "id": gen_id(), "qru_asset_id": f"QRU-MEDIA-{gen_id()[:8].upper()}", "kind": "video",
        "provider": item.get("provider"), "provider_asset_id": item.get("provider_asset_id"),
        "source_url": item.get("source_url"), "creator_name": item.get("creator_name"),
        "title": item.get("title"), "license_type": item.get("license_type"),
        "commercial_use_allowed": commercial, "checksum": checksum,
        "internal_storage_url": master_path, "file_size_bytes": len(data),
        "download_date": now_iso(), "imported_by": actor, "approval_status": "Approved",
        "active_status": "Active", "collection": "Nature and Earth", "version": 1,
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.media_assets.insert_one(dict(source_doc))
    step("asset_registration", "ok", f"Registered {source_doc['qru_asset_id']} with checksum + provenance.", qru_asset_id=source_doc["qru_asset_id"])

    # 5. Narration (OpenAI TTS).
    narration_path = os.path.join(work, "narration.mp3")
    tts_res = await _tts(NARRATION, narration_path)
    has_narration = tts_res is True
    if has_narration:
        step("narration", "ok", "Narration generated via OpenAI TTS (voice: sage).")
    else:
        step("narration", "degraded", f"TTS unavailable ({tts_res if isinstance(tts_res, str) else 'no audio'}) — rendering with the licensed clip's own audio. Honest fallback, not faked.")

    # 6. Captions.
    srt_path = os.path.join(work, "captions.srt")
    with open(srt_path, "w") as f:
        f.write(_srt(NARRATION))
    step("caption_generation", "ok", f"{NARRATION.count('.') } caption cues written (.srt).")

    # 7. MP4 render (ffmpeg): trim 22s, 720p, burn captions + QRU brand bar, narration audio if present.
    out_path = os.path.join(work, "showcase.mp4")
    vf = ("trim=0:22,setpts=PTS-STARTPTS,scale=1280:720:force_original_aspect_ratio=increase,"
          "crop=1280:720,subtitles=captions.srt:force_style='FontName=DejaVu Sans,FontSize=20,"
          "PrimaryColour=&H00FFFFFF&,BackColour=&H80000000&,BorderStyle=3,Outline=1',"
          f"drawtext=fontfile={FONT}:text='QRU Trading University':fontcolor=white:fontsize=22:"
          "x=40:y=H-70:box=1:boxcolor=0x35106A@0.85:boxborderw=12")
    cmd = ["ffmpeg", "-y", "-i", "master.mp4"]
    if has_narration:
        cmd += ["-i", "narration.mp3", "-filter_complex", f"[0:v]{vf}[v]",
                "-map", "[v]", "-map", "1:a", "-shortest"]
    else:
        cmd += ["-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", "-map", "0:a?", "-t", "22"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "showcase.mp4"]
    loop = asyncio.get_event_loop()
    proc = await loop.run_in_executor(None, lambda: subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=180))
    if proc.returncode != 0 or not os.path.exists(out_path):
        step("mp4_rendering", "failed", f"ffmpeg error: {proc.stderr[-300:]}")
        return {"ok": False, "steps": steps, "job_id": job_id}
    step("mp4_rendering", "ok", "Rendered 720p MP4 with burned captions + QRU brand bar.")

    # 8. Quality review.
    probe = _ffprobe(out_path)
    checks = {
        "opens": bool(probe),
        "has_video": bool(probe.get("width")),
        "resolution_ok": (probe.get("width") or 0) >= 1280,
        "duration_ok": 5 <= (probe.get("duration") or 0) <= 90,
        "has_audio": probe.get("has_audio"),
    }
    passed = all([checks["opens"], checks["has_video"], checks["resolution_ok"], checks["duration_ok"]])
    step("quality_review", "ok" if passed else "failed",
         f"{probe.get('width')}x{probe.get('height')} · {round(probe.get('duration',0),1)}s · audio={checks['has_audio']}", checks=checks)
    if not passed:
        return {"ok": False, "steps": steps, "job_id": job_id, "probe": probe}

    # 9. Register final showcase MP4 as a derivative in the vault.
    with open(out_path, "rb") as f:
        final_bytes = f.read()
    final_doc = {
        "id": gen_id(), "qru_asset_id": f"QRU-SHOWCASE-{gen_id()[:8].upper()}", "kind": "video",
        "title": f"{product_title} — QRU Flagship Showcase", "provider": "qru_production",
        "parent_asset_id": source_doc["qru_asset_id"], "checksum": _sha256(final_bytes),
        "internal_storage_url": out_path, "file_size_bytes": len(final_bytes),
        "duration_seconds": round(probe.get("duration", 0), 1), "width": probe.get("width"),
        "height": probe.get("height"), "has_narration": has_narration,
        "license_type": "QRU Production (derivative of licensed source)", "approval_status": "Approved",
        "active_status": "Active", "distribution_ready": True, "collection": "Cinematic Openings",
        "imported_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.media_assets.insert_one(dict(final_doc))
    step("master_asset_vault", "ok", f"Master {final_doc['qru_asset_id']} archived with checksum.", qru_asset_id=final_doc["qru_asset_id"])
    step("distribution_ready", "ok", "Marked distribution-ready — eligible for the publication queue.")

    if milestone:
        await db.factory_milestones.update_one({"code": milestone["code"]}, {"$set": {**milestone, "achieved_at": now_iso(),
            "source_asset": source_doc["qru_asset_id"], "showcase_asset": final_doc["qru_asset_id"]}}, upsert=True)

    return {"ok": True, "steps": steps, "job_id": job_id,
            "source_asset": {k: source_doc[k] for k in ("qru_asset_id", "provider", "creator_name", "license_type", "checksum")},
            "showcase_asset": {k: final_doc[k] for k in ("qru_asset_id", "duration_seconds", "width", "height", "has_narration", "distribution_ready", "checksum")},
            "narration": has_narration}
