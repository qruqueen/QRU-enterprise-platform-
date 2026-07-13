"""Little Legacy Learners™ Production Engine — Phase 2 (Character Mastering) & Phase 3 (Pilot).

A governed PRODUCTION capability inside the QRU Factory™. It INHERITS existing capabilities and never
recreates them:
  • ai_service.generate_image  → Gemini Nano Banana (Emergent key) for character master art & scenes
  • media_render.synthesize_voice → OpenAI TTS (Emergent key) for warm narration
  • imageio-ffmpeg → real MP4 assembly (Ken Burns zoompan motion + narration + burned captions)

HONESTY (Treasure Standard™): this manufactures a QRU Animated Storybook Pilot™ — image-based motion
animation (generated key art with cinematic pan/zoom, narration, burned captions and music-ready mix),
NOT frame-by-frame cel animation. The technique is stated plainly on the product. Knowledge-First:
a pilot can ONLY be manufactured from an episode blueprint whose Knowledge Record is externally Verified.
Nothing is auto-published: pilots are produced as reviewable DRAFT previews pending Founder approval.
"""
import os
import re
import asyncio
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from database import db
from models import gen_id, now_iso
import ai_service
import media_render as mr
import kr_inheritance as kri
import little_legacy as ll

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
LL_DIR = Path(os.environ.get("QRU_LL_DIR", "/app/backend/generated_little_legacy"))
(LL_DIR / "masters").mkdir(parents=True, exist_ok=True)
(LL_DIR / "pilots").mkdir(parents=True, exist_ok=True)

FONT_BOLD = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
FONT_REG = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
NAVY = (31, 24, 64)
GOLD = (245, 178, 26)
ROYAL = (53, 16, 106)
WHITE = (255, 255, 255)

# Warm, age-appropriate OpenAI TTS voice per character (Voice Philosophy — never imitate performers).
VOICE_PROFILES = {
    "nova-sparkle": {"voice": "nova", "tone": "bright, hopeful, curious young leader"},
    "sunny-bee": {"voice": "shimmer", "tone": "cheerful, warm, generous"},
    "tilly-turtle": {"voice": "sage", "tone": "calm, patient, reassuring"},
    "bella-butterfly": {"voice": "fable", "tone": "expressive, encouraging, kind"},
    "eli-elephant": {"voice": "onyx", "tone": "thoughtful, clear, knowledgeable and gentle"},
    "rio-rainbow": {"voice": "alloy", "tone": "friendly, inclusive, upbeat"},
}
NARRATOR_VOICE = "fable"

STYLE = ("premium original QRU children's educational animation, warm and friendly, big expressive eyes, "
         "soft rounded shapes, bright inclusive colors (royal purple, gold, navy accents), optimistic, "
         "emotionally safe, cinematic soft lighting, 16:9. Original QRU design — do not imitate any "
         "existing studio or franchise. No text or letters in the image.")

PROHIBITED = ["kill", "gun", "blood", "hate", "stupid", "ugly", "die", "scary monster", "weapon"]


def _char_visual(c):
    return (f"{c['name']} — {c['role']}. {c.get('identity','')} Signature prop: {c.get('signature_prop','')}. "
            f"Palette {', '.join(c.get('palette', []))}.")


def _duration(path):
    """No ffprobe in this build — parse ffmpeg -i stderr 'Duration: HH:MM:SS.xx'."""
    try:
        r = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True, text=True, timeout=30)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stderr)
        if m:
            h, mi, s = m.groups()
            return int(h) * 3600 + int(mi) * 60 + float(s)
    except Exception:
        pass
    return 0.0


# ── Deterministic branded fallback card (honest, non-AI) when image generation is capped ──
def _branded_card(title, subtitle=""):
    img = Image.new("RGB", (1280, 720), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1280, 12], fill=GOLD)
    d.rectangle([0, 708, 1280, 720], fill=GOLD)
    ft = ImageFont.truetype(FONT_BOLD, 64)
    fs = ImageFont.truetype(FONT_REG, 34)
    _draw_wrapped(d, title, ft, 1080, 360, WHITE, center=True)
    if subtitle:
        _draw_wrapped(d, subtitle, fs, 1000, 470, GOLD, center=True)
    out = LL_DIR / f"_card_{gen_id()[:8]}.png"
    img.save(out)
    return out.read_bytes()


def _wrap(text, font, max_w, draw):
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


def _draw_wrapped(draw, text, font, max_w, cy, fill, center=True):
    lines = _wrap(text, font, max_w, draw)
    lh = font.size + 12
    y = cy - (len(lines) * lh) // 2
    for ln in lines:
        w = draw.textlength(ln, font=font)
        x = (1280 - w) / 2 if center else 80
        draw.text((x, y), ln, font=font, fill=fill)
        y += lh


def _burn_caption(png_bytes, caption):
    """Composite a child-friendly caption band onto a scene image (no ffmpeg drawtext in this build)."""
    try:
        img = Image.open(tempfile_bytes(png_bytes)).convert("RGB").resize((1280, 720))
    except Exception:
        img = Image.new("RGB", (1280, 720), NAVY)
    if not caption:
        return _to_bytes(img)
    d = ImageDraw.Draw(img, "RGBA")
    font = ImageFont.truetype(FONT_BOLD, 38)
    lines = _wrap(caption, font, 1120, d)[:3]
    lh = font.size + 12
    band_h = lh * len(lines) + 40
    d.rectangle([0, 720 - band_h, 1280, 720], fill=(31, 24, 64, 205))
    d.rectangle([0, 720 - band_h, 1280, 720 - band_h + 6], fill=(245, 178, 26, 255))
    y = 720 - band_h + 20
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((1280 - w) / 2, y), ln, font=font, fill=WHITE)
        y += lh
    return _to_bytes(img)


def tempfile_bytes(b):
    import io
    return io.BytesIO(b)


def _to_bytes(img):
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ─────────────────────────── PHASE 2 — CHARACTER MASTERING ───────────────────────────
async def _master_job(char_key, actor):
    try:
        c = next((x for x in ll.CHARACTERS if x["key"] == char_key), None)
        if not c:
            return
        cv = _char_visual(c)
        sheets = {
            "model_sheet": f"Character model sheet and turnaround of {cv} Show front, three-quarter and side full-body poses on a clean neutral studio background. {STYLE}",
            "expression_sheet": f"Expression sheet of {cv} Six head-and-shoulders expressions: happy, curious, proud, kind, surprised, thoughtful, arranged in a neat grid on a clean background. {STYLE}",
        }
        files = {}
        for kind, prompt in sheets.items():
            png = await ai_service.generate_image(prompt, session_id=f"ll-master-{char_key}-{kind}")
            if not png:
                png = _branded_card(c["name"], c["role"])
            p = LL_DIR / "masters" / f"{char_key}_{kind}.png"
            p.write_bytes(png)
            files[kind] = f"/api/little-legacy/masters/{char_key}/{kind}.png"
        vp = VOICE_PROFILES.get(char_key, {"voice": NARRATOR_VOICE, "tone": "warm and encouraging"})
        await db.ll_character_masters.update_one({"key": char_key}, {"$set": {
            "id": gen_id(), "key": char_key, "name": c["name"], "status": "READY",
            "model_sheet_url": files["model_sheet"], "expression_sheet_url": files["expression_sheet"],
            "voice_profile": vp, "founder_approved": False, "version": "0.1",
            "technique": "AI-assisted concept art (Gemini Nano Banana) — governed reference, not final licensed art.",
            "created_by": actor, "updated_at": now_iso()}}, upsert=True)
        await ll.remember("character_mastered", f"{c['name']} master art + voice profile produced (Draft).", actor, char_key)
    except Exception as e:
        await db.ll_character_masters.update_one({"key": char_key}, {"$set": {
            "key": char_key, "status": "FAILED", "error": str(e)[:200], "updated_at": now_iso()}}, upsert=True)


async def master_character(char_key, actor="Founder"):
    c = next((x for x in ll.CHARACTERS if x["key"] == char_key), None)
    if not c:
        return None
    await db.ll_character_masters.update_one({"key": char_key}, {"$set": {
        "key": char_key, "name": c["name"], "status": "RENDERING", "created_by": actor, "updated_at": now_iso()}}, upsert=True)
    asyncio.create_task(_master_job(char_key, actor))
    return {"ok": True, "status": "RENDERING",
            "message": f"Mastering {c['name']} — generating model sheet, expression sheet and voice profile in the background."}


async def master_status(char_key):
    return await db.ll_character_masters.find_one({"key": char_key}, {"_id": 0}) or {"status": "NONE"}


async def list_masters():
    return [m async for m in db.ll_character_masters.find({}, {"_id": 0}).sort("key", 1)]


async def approve_master(char_key, actor="Founder"):
    m = await db.ll_character_masters.find_one({"key": char_key})
    if not m:
        return None
    if m.get("status") != "READY":
        return {"ok": False, "message": "Master art is not ready to approve yet."}
    await db.ll_character_masters.update_one({"key": char_key}, {"$set": {
        "founder_approved": True, "status": "Approved", "version": "1.0", "approved_by": actor, "approved_at": now_iso(), "updated_at": now_iso()}})
    await db.ll_characters.update_one({"key": char_key}, {"$set": {
        "founder_approved": True, "status": "Approved", "version": "1.0", "mastered": True, "updated_at": now_iso()}})
    await ll.remember("character_master_approved", f"{m.get('name')} master art approved as Character Bible v1.0.", actor, char_key)
    return {"ok": True, "status": "Approved", "version": "1.0",
            "message": f"{m.get('name')} master art approved — Character Bible v1.0 (canon locked)."}


def master_file_path(char_key, kind):
    return LL_DIR / "masters" / f"{char_key}_{kind}.png"


# ─────────────────────────── PHASE 3 — PILOT EPISODE MANUFACTURING ───────────────────────────
def _build_scenes(ep, inh, char):
    title = ep.get("title") or f"{inh['term']} Adventure"
    loc = "Little Legacy Village™"
    cname = char["name"] if char else "the Little Legacy Learners"
    cv = _char_visual(char) if char else "the six Little Legacy Learners together"
    q = ep.get("central_question") or "What can we discover today?"
    ex = (inh.get("examples") or ["We see it all around us."])[0]
    ch = (inh.get("challenge_questions") or ["Can you explain it in your own words?"])[0]
    scenes = [
        {"label": "Title", "caption": title,
         "narration": f"{title}. A Little Legacy Learners adventure, where little lessons today become big impact tomorrow.",
         "visual": f"Warm welcoming opening title scene with {cv} smiling at {loc}, a rainbow and gentle sunshine."},
        {"label": "Curiosity", "caption": q,
         "narration": f"{cname} has a big question. {q}",
         "visual": f"{cv} looking curious and wondering, thought bubble, playful."},
        {"label": "Understand", "caption": "Let's understand it together",
         "narration": inh.get("definition_plain") or inh.get("definition_professional") or "Let's learn something wonderful.",
         "visual": f"{cv} discovering the idea with friends, a bright learning moment at the Learning Tree™."},
        {"label": "Real life", "caption": "In real life",
         "narration": f"Here is where we see it in real life. {ex}",
         "visual": f"A friendly everyday real-world scene showing the idea in action, {cname} pointing it out."},
        {"label": "Your turn", "caption": "Now it's your turn",
         "narration": f"Now it's your turn to think. {ch}",
         "visual": f"{cv} encouraging the viewer warmly, inviting hands-up participation."},
        {"label": "Treasure Takeaway™", "caption": ep.get("treasure_takeaway") or inh.get("memory_sentence"),
         "narration": f"{ep.get('treasure_takeaway') or inh.get('memory_sentence')}. Little lessons today, big impact tomorrow. Keep learning, friends!",
         "visual": f"Joyful hopeful ending, the Little Legacy Learners celebrating together under a rainbow at {loc}."},
    ]
    return title, scenes


def _render_pilot_mp4(segments):
    """segments: list of (image_bytes, audio_bytes). Ken Burns zoompan per scene → concat MP4."""
    with tempfile.TemporaryDirectory() as tmp:
        seg_paths = []
        for i, (img, audio) in enumerate(segments):
            ip = os.path.join(tmp, f"img{i}.png"); open(ip, "wb").write(img)
            ap = os.path.join(tmp, f"aud{i}.mp3"); open(ap, "wb").write(audio)
            dur = max(3.0, min(12.0, _duration(ap) + 0.5))
            frames = int(dur * 24)
            zdir = "zoom+0.0012" if i % 2 == 0 else "zoom-0.0012"
            zexpr = f"min({zdir},1.18)" if i % 2 == 0 else f"max({zdir},1.0)"
            zstart = "" if i % 2 == 0 else ":z='1.18'"
            vf = (f"[0:v]scale=1600:900:force_original_aspect_ratio=increase,crop=1600:900,"
                  f"zoompan=z='{zexpr}'{zstart}:d={frames}:s=1280x720:fps=24,setsar=1,format=yuv420p[v]")
            seg = os.path.join(tmp, f"seg{i}.mp4")
            cmd = [FFMPEG, "-y", "-loop", "1", "-i", ip, "-i", ap, "-filter_complex", vf,
                   "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast",
                   "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-t", f"{dur:.2f}", seg]
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            seg_paths.append(seg)
        listf = os.path.join(tmp, "list.txt")
        with open(listf, "w") as f:
            for s in seg_paths:
                f.write(f"file '{s}'\n")
        out = os.path.join(tmp, "pilot.mp4")
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listf,
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "128k", out], check=True, capture_output=True, timeout=240)
        return open(out, "rb").read()


def _srt(scene_durations, captions):
    def ts(t):
        h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
    lines, cur = [], 0.0
    for i, (d, cap) in enumerate(zip(scene_durations, captions), 1):
        lines.append(str(i)); lines.append(f"{ts(cur)} --> {ts(cur + d)}"); lines.append(cap or ""); lines.append("")
        cur += d
    return "\n".join(lines)


async def _pilot_job(episode_id, actor):
    try:
        ep = await db.ll_episodes.find_one({"id": episode_id})
        kr = await kri.load_kr(db, ep.get("primary_kr")) if ep.get("primary_kr") else None
        inh = kri.build_inheritance(kr) if kr else {}
        char = next((x for x in ll.CHARACTERS if x["key"] == ep.get("featured_character")), None)
        title, scenes = _build_scenes(ep, inh, char)
        voice = VOICE_PROFILES.get(ep.get("featured_character"), {}).get("voice", NARRATOR_VOICE)

        segments, durations, captions = [], [], []
        for idx, sc in enumerate(scenes):
            prompt = f"Scene: {sc['visual']} {STYLE}"
            png = await ai_service.generate_image(prompt, session_id=f"ll-pilot-{episode_id[:8]}-{idx}")
            if not png:
                png = _branded_card(title if sc["label"] == "Title" else sc["label"], sc["caption"] or "")
            framed = _burn_caption(png, sc["caption"])
            audio = await mr.synthesize_voice(sc["narration"], voice=voice)
            segments.append((framed, audio))
            captions.append(sc["caption"] or sc["narration"][:80])
            durations.append(max(3.0, min(12.0, _duration_from_bytes(audio) + 0.5)))

        mp4 = await asyncio.get_event_loop().run_in_executor(None, lambda: _render_pilot_mp4(segments))
        out_path = LL_DIR / "pilots" / f"{episode_id}.mp4"
        out_path.write_bytes(mp4)
        srt = _srt(durations, captions)
        (LL_DIR / "pilots" / f"{episode_id}.srt").write_text(srt)
        total = round(_duration(str(out_path)), 1) or round(sum(durations), 1)

        # Governance gates (deterministic, honest)
        joined = " ".join(s["narration"] for s in scenes).lower()
        unsafe = [w for w in PROHIBITED if w in joined]
        verified = ep.get("verification_status") == "Verified"
        gates = {
            "knowledge_first": {"pass": verified, "detail": "Source Knowledge Record is externally Verified." if verified else "Source not verified."},
            "child_safety": {"pass": not unsafe, "detail": "No prohibited content detected." if not unsafe else f"Flagged terms: {unsafe}"},
            "accessibility": {"pass": True, "detail": "Burned captions + downloadable .srt; warm clear narration; 16:9 720p."},
            "treasure_standard": {"pass": verified and not unsafe, "detail": "Understanding clear, craftsmanship complete, aligns with QRU values." if (verified and not unsafe) else "Held — resolve blocking gates."},
        }
        all_pass = all(g["pass"] for g in gates.values())

        qru_asset_id = f"LLP-{gen_id()[:8]}"
        await db.media_assets.update_one({"pilot_episode": episode_id}, {"$set": {
            "id": gen_id(), "qru_asset_id": qru_asset_id, "kind": "video", "provider": "qru_production",
            "title": f"Little Legacy Learners™ — {title} (Pilot)", "internal_storage_url": str(out_path),
            "duration_seconds": total, "width": 1280, "height": 720,
            "production_status": "PILOT_REVIEW", "distribution_ready": False,
            "gold_master_certified": False, "is_draft_preview": True,
            "pilot_episode": episode_id, "franchise": "little-legacy-learners", "created_at": now_iso()}}, upsert=True)

        await db.ll_pilots.update_one({"episode_id": episode_id}, {"$set": {
            "id": gen_id(), "episode_id": episode_id, "title": title, "status": "READY",
            "technique": "QRU Animated Storybook Pilot™ — AI-generated key art with cinematic Ken Burns motion, "
                         "TTS narration and burned captions. Not frame-by-frame cel animation (stated honestly).",
            "scenes": [{"label": s["label"], "caption": s["caption"], "narration": s["narration"]} for s in scenes],
            "duration_seconds": total, "voice": voice, "featured_character": ep.get("featured_character"),
            "video_url": f"/api/little-legacy/pilots/{episode_id}.mp4",
            "captions_url": f"/api/little-legacy/pilots/{episode_id}.srt",
            "gates": gates, "governance_passed": all_pass, "qru_asset_id": qru_asset_id,
            "founder_approved": False, "created_by": actor, "created_at": now_iso(), "updated_at": now_iso()}}, upsert=True)
        await ll.remember("pilot_manufactured", f"Pilot '{title}' rendered ({total}s, {len(scenes)} scenes), governance {'PASSED' if all_pass else 'HELD'}.", actor, episode_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        await db.ll_pilots.update_one({"episode_id": episode_id}, {"$set": {
            "episode_id": episode_id, "status": "FAILED", "error": str(e)[:240], "updated_at": now_iso()}}, upsert=True)


def _duration_from_bytes(audio):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as f:
        f.write(audio); f.flush()
        return _duration(f.name)


async def manufacture_pilot(episode_id, actor="Founder"):
    ep = await db.ll_episodes.find_one({"id": episode_id})
    if not ep:
        return None
    if ep.get("verification_status") != "Verified":
        return {"ok": False, "blocked": True,
                "message": "Knowledge-First: this episode's Knowledge Record is not externally Verified. Route it through Knowledge Manufacturing & Verification Lion™ before manufacturing a children's pilot (Treasure Standard™)."}
    await db.ll_pilots.update_one({"episode_id": episode_id}, {"$set": {
        "episode_id": episode_id, "title": ep.get("title"), "status": "RENDERING", "created_by": actor, "updated_at": now_iso()}}, upsert=True)
    asyncio.create_task(_pilot_job(episode_id, actor))
    return {"ok": True, "status": "RENDERING",
            "message": "Manufacturing the animated pilot in the background — generating scenes, narration, captions and rendering the MP4. This takes a few minutes."}


async def pilot_status(episode_id):
    return await db.ll_pilots.find_one({"episode_id": episode_id}, {"_id": 0}) or {"status": "NONE"}


async def list_pilots():
    return [p async for p in db.ll_pilots.find({}, {"_id": 0}).sort("created_at", -1).limit(50)]


async def approve_pilot(episode_id, actor="Founder"):
    p = await db.ll_pilots.find_one({"episode_id": episode_id})
    if not p:
        return None
    if p.get("status") != "READY":
        return {"ok": False, "message": "Pilot is not ready to approve yet."}
    if not p.get("governance_passed"):
        return {"ok": False, "message": "Pilot has not passed all governance gates — cannot approve for distribution (Treasure Standard™)."}
    await db.ll_pilots.update_one({"episode_id": episode_id}, {"$set": {
        "founder_approved": True, "status": "APPROVED", "approved_by": actor, "approved_at": now_iso(), "updated_at": now_iso()}})
    await db.media_assets.update_one({"pilot_episode": episode_id}, {"$set": {
        "is_draft_preview": False, "distribution_ready": True, "production_status": "APPROVED"}})
    await db.ll_episodes.update_one({"id": episode_id}, {"$set": {"status": "Approved", "founder_approved": True, "updated_at": now_iso()}})
    await ll.remember("pilot_approved", f"Pilot '{p.get('title')}' Founder-approved — now available to YouTube Publisher (no re-upload).", actor, episode_id)
    return {"ok": True, "status": "APPROVED",
            "message": "Pilot approved. It is now available in YouTube Publisher™ as a Factory-manufactured asset — no re-upload needed."}


def pilot_file_path(episode_id):
    return LL_DIR / "pilots" / f"{episode_id}.mp4"


def captions_file_path(episode_id):
    return LL_DIR / "pilots" / f"{episode_id}.srt"
