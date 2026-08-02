"""Audiobook → YouTube Video builder.

Turns a book's finished full audiobook (already rendered: artifacts.audio.full_audiobook.url) into a
YouTube-ready MP4 by pairing the audio with a branded cover title-card, then (via a separate action)
publishes it to the connected channel as Private for review. Runs on the durable job spine, so a
long full-length encode survives server restarts.

Honest: this is an audiobook video (a still cover card over narration), NOT animation. Nothing is
faked — if the audiobook or cover is missing, it fails clearly.
"""
import os
import subprocess
import tempfile
import logging

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from database import db
import rendering_engine as re_engine
from models import now_iso

logger = logging.getLogger("qru.audiobook_video")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
COLL = "book_records"

NAVY = (11, 27, 43)
GOLD = (198, 160, 74)
CREAM = (244, 240, 232)


def _font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _read_asset(url):
    if not url:
        return None
    path = os.path.join(re_engine.ASSET_DIR, url.split("/")[-1])
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def _title_card(book):
    """Build a 1920x1080 branded audiobook title-card with the book cover centered."""
    W, H = 1920, 1080
    card = Image.new("RGB", (W, H), NAVY)
    # subtle vertical gradient
    top = Image.new("RGB", (W, H), (20, 42, 66))
    mask = Image.new("L", (W, H))
    md = ImageDraw.Draw(mask)
    for y in range(H):
        md.line([(0, y), (W, y)], fill=int(120 * (1 - y / H)))
    card = Image.composite(top, card, mask)
    draw = ImageDraw.Draw(card)

    cover_bytes = _read_asset(((book.get("artifacts", {}).get("design", {}) or {}).get("selected_cover") or {}).get("url"))
    cover_w = 0
    if cover_bytes:
        try:
            cov = Image.open(__import__("io").BytesIO(cover_bytes)).convert("RGB")
            target_h = 860
            ratio = target_h / cov.height
            cover_w = int(cov.width * ratio)
            cov = cov.resize((cover_w, target_h), Image.LANCZOS)
            cx = 150
            cy = (H - target_h) // 2
            shadow = Image.new("RGBA", (cover_w + 40, target_h + 40), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow)
            sd.rectangle([20, 20, cover_w + 20, target_h + 20], fill=(0, 0, 0, 120))
            card.paste(shadow, (cx - 20, cy - 20), shadow)
            card.paste(cov, (cx, cy))
        except Exception:
            cover_w = 0

    text_x = 150 + cover_w + (110 if cover_w else 0)
    text_w = W - text_x - 120
    # brand kicker
    draw.text((text_x, 210), "QRU PRESS™ · AUDIOBOOK", font=_font(30, bold=True), fill=GOLD)
    # title
    title = book.get("title", "Audiobook")
    tf = _font(74, bold=True)
    ty = 270
    for ln in _wrap(draw, title, tf, text_w)[:4]:
        draw.text((text_x, ty), ln, font=tf, fill=CREAM)
        ty += 88
    # author
    author = book.get("author") or "QRU Press"
    ty += 20
    draw.text((text_x, ty), f"Narrated · {author}", font=_font(38), fill=(200, 205, 214))
    # footer standard
    draw.text((text_x, H - 150), "Verified to the QRU Treasure Standard™", font=_font(28), fill=GOLD)
    return card


def _duration(book):
    fa = ((book.get("artifacts", {}).get("audio", {}) or {}).get("full_audiobook")) or {}
    return float(fa.get("duration_sec") or 0), fa.get("url")


async def render_audiobook_video(book_id, actor="Founder", progress=None):
    async def _p(msg, done=None, total=None):
        if progress:
            await progress(done=done, total=total, message=msg)
    book = await db[COLL].find_one({"id": book_id})
    if not book:
        raise ValueError("Book not found.")
    dur, audio_url = _duration(book)
    if not audio_url or dur <= 0:
        raise ValueError("No full audiobook found. Render the full audiobook first, then create the video.")
    audio_bytes = _read_asset(audio_url)
    if not audio_bytes:
        raise ValueError("The full audiobook audio file is missing on the server — re-render the audiobook, then try again.")

    await _p("Building branded cover title-card…", 1, 3)
    card = _title_card(book)
    tmp = tempfile.mkdtemp(prefix="abvideo-")
    card_path = os.path.join(tmp, "card.png")
    audio_path = os.path.join(tmp, "audio.mp3")
    out_path = os.path.join(tmp, "audiobook_video.mp4")
    card.save(card_path)
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)

    await _p(f"Encoding {round(dur/60,1)}-minute audiobook video…", 2, 3)
    # Static cover card over the narration. Reliable at any length; x264 collapses duplicate frames
    # so the file stays small even for long audiobooks.
    cmd = [FFMPEG, "-y", "-loop", "1", "-framerate", "2", "-i", card_path, "-i", audio_path,
           "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-pix_fmt", "yuv420p",
           "-r", "24", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=max(300, int(dur) + 120))
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Video encode failed: {e.stderr.decode('utf-8', 'ignore')[:200]}")
    with open(out_path, "rb") as f:
        video_bytes = f.read()
    fid = re_engine._save(f"audiobook-video-{book_id}", "mp4", video_bytes)
    url = re_engine._asset_url(fid)

    await _p("Storing the audiobook video…", 3, 3)
    artifacts = book.get("artifacts", {})
    audio_art = artifacts.get("audio", {}) or {}
    fa = audio_art.get("full_audiobook", {}) or {}
    fa["video"] = {
        "label": "Audiobook Video (cover title-card + full narration) — YouTube-ready. AI narration; disclose before commercial distribution.",
        "url": url, "file_id": fid, "duration_sec": round(dur, 1), "duration_min": round(dur / 60, 1),
        "bytes": len(video_bytes), "generated_at": now_iso(), "generated_by": actor,
    }
    audio_art["full_audiobook"] = fa
    artifacts["audio"] = audio_art
    await db[COLL].update_one({"id": book_id}, {"$set": {"artifacts": artifacts, "updated_at": now_iso()}})
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    return {"book_id": book_id, "url": url, "file_id": fid, "duration_sec": round(dur, 1)}


async def publish_audiobook_video(book_id, actor="Founder", privacy="private"):
    """Publish the rendered audiobook video to the connected YouTube channel (Private by default)."""
    import youtube_publisher as yt
    book = await db[COLL].find_one({"id": book_id})
    if not book:
        return None
    fa = ((book.get("artifacts", {}).get("audio", {}) or {}).get("full_audiobook")) or {}
    vid = fa.get("video") or {}
    fid = vid.get("file_id")
    if not fid:
        return {"ok": False, "message": "No audiobook video yet — create the video first, then publish."}
    path = os.path.join(re_engine.ASSET_DIR, fid)
    if not os.path.exists(path):
        return {"ok": False, "message": "The audiobook video file is missing — re-create the video, then publish."}
    privacy = privacy if privacy in ("private", "unlisted", "public") else "private"
    title = f"{book.get('title', 'Audiobook')} — Full Audiobook"
    desc = (book.get("description") or "").strip()
    desc = f"{desc}\n\nNarrated audiobook from QRU Press™. Verified to the QRU Treasure Standard™.\n(AI narration.)".strip()
    tags = (book.get("keywords") or [])[:15] or ["audiobook", "QRU Press"]
    try:
        pub = await yt.publish_video(file_path=path, title=title[:100], description=desc[:4900],
                                     tags=tags, privacy=privacy, actor=actor, made_for_kids=False)
    except yt.YouTubeError as e:
        low = str(e).lower()
        if "401" in str(e) or "invalid authentication" in low or "unauthorized" in low or "invalid_grant" in low:
            return {"ok": False, "not_connected": True,
                    "message": "YouTube rejected the upload — the channel connection has expired. Reconnect your channel in Publishing Connectors™, then publish again."}
        return {"ok": False, "not_connected": "connect" in low, "message": str(e)}
    vid["youtube_video_id"] = pub.get("video_id")
    vid["youtube_url"] = pub.get("url")
    vid["youtube_privacy"] = pub.get("privacy")
    vid["youtube_published_at"] = pub.get("published_at")
    fa["video"] = vid
    await db[COLL].update_one({"id": book_id}, {"$set": {
        "artifacts.audio.full_audiobook.video": vid, "updated_at": now_iso()}})
    return {"ok": True, "message": f"Published to YouTube as {pub.get('privacy')}. Review it in YouTube Studio, then set Public when ready.",
            "video_id": pub.get("video_id"), "url": pub.get("url"), "studio_url": pub.get("studio_url"), "privacy": pub.get("privacy")}


# ---- Job handler -----------------------------------------------------------
async def _job_render(job, progress):
    p = job.get("payload", {})
    return await render_audiobook_video(p["book_id"], actor=p.get("actor", "Founder"), progress=progress)
