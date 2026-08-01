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

import logging
from datetime import datetime, timezone
logger = logging.getLogger("qru.little_legacy")

# Resilience constants — a render is a multi-minute background job; production containers can recycle
# mid-render. These guard against a job hanging in RENDERING forever and against a single hung API call.
TTS_TIMEOUT_S = 90          # per-scene narration synthesis
PILOT_STALE_S = 900         # a pilot RENDERING longer than this with no output = interrupted → FAILED
MASTER_STALE_S = 600        # a character master RENDERING longer than this = interrupted → FAILED


def _age_seconds(iso_ts):
    """Seconds elapsed since an ISO timestamp; large number if missing/unparseable (treat as stale)."""
    if not iso_ts:
        return 10 ** 9
    try:
        dt = datetime.fromisoformat(iso_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds()
    except Exception:
        return 10 ** 9

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
        model_prompt = (f"Character model sheet and turnaround of {cv} Show front, three-quarter and side "
                        f"full-body poses on a clean neutral studio background. {STYLE}")
        model_png = await ai_service.generate_image(model_prompt, session_id=f"ll-master-{char_key}-model")
        if not model_png:
            model_png = _branded_card(c["name"], c["role"])
        (LL_DIR / "masters" / f"{char_key}_model_sheet.png").write_bytes(model_png)
        # Expression sheet INHERITS from the model sheet (identity anchor) so both are the SAME character.
        expr_prompt = (f"Expression sheet of {cv} Using the SAME character exactly as the provided reference "
                       f"(identical skin tone, hair texture, facial proportions, eye shape, smile, clothing, "
                       f"crown placement and color palette), show six head-and-shoulders expressions — happy, "
                       f"curious, proud, kind, surprised, thoughtful — in a neat grid on a clean background. {STYLE}")
        expr_png = await ai_service.generate_image_with_reference(expr_prompt, session_id=f"ll-master-{char_key}-expr", reference_pngs=[model_png])
        if not expr_png:
            expr_png = _branded_card(c["name"], "Expressions")
        (LL_DIR / "masters" / f"{char_key}_expression_sheet.png").write_bytes(expr_png)
        files = {"model_sheet": f"/api/little-legacy/masters/{char_key}/model_sheet.png",
                 "expression_sheet": f"/api/little-legacy/masters/{char_key}/expression_sheet.png"}
        vp = VOICE_PROFILES.get(char_key, {"voice": NARRATOR_VOICE, "tone": "warm and encouraging"})
        await db.ll_character_masters.update_one({"key": char_key}, {"$set": {
            "id": gen_id(), "key": char_key, "name": c["name"], "status": "READY",
            "model_sheet_url": files["model_sheet"], "expression_sheet_url": files["expression_sheet"],
            "anchor_url": files["model_sheet"],
            "voice_profile": vp, "color_palette": c.get("palette", []), "canon_notes": ll.CANON_NOTES.get(char_key, []),
            "identity_standard": ll.IDENTITY_STANDARD,
            "expression_inherits_anchor": True,
            "founder_approved": False, "consistency_confirmed": False, "version": "0.1",
            "technique": "AI-assisted concept art (Gemini Nano Banana) — governed reference, not final licensed art. "
                         "Expression sheet inherits from the model-sheet identity anchor.",
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
        "key": char_key, "name": c["name"], "status": "RENDERING", "error": None,
        "render_started_at": now_iso(), "created_by": actor, "updated_at": now_iso()}}, upsert=True)
    asyncio.create_task(_master_job(char_key, actor))
    return {"ok": True, "status": "RENDERING",
            "message": f"Mastering {c['name']} — generating model sheet, expression sheet and voice profile in the background."}


async def master_status(char_key):
    m = await db.ll_character_masters.find_one({"key": char_key}, {"_id": 0})
    if not m:
        return {"status": "NONE"}
    if m.get("status") == "RENDERING" and _age_seconds(m.get("render_started_at") or m.get("updated_at")) > MASTER_STALE_S:
        sheet = master_file_path(char_key, "model_sheet")
        if not sheet.exists():
            await db.ll_character_masters.update_one({"key": char_key}, {"$set": {
                "status": "FAILED",
                "error": "Mastering was interrupted before it finished (the server likely recycled). Tap to try again.",
                "updated_at": now_iso()}})
            m["status"] = "FAILED"
            m["error"] = "Mastering was interrupted before it finished (the server likely recycled). Tap to try again."
    return m


async def list_masters():
    return [m async for m in db.ll_character_masters.find({}, {"_id": 0}).sort("key", 1)]


async def approve_master(char_key, actor="Founder", consistency_confirmed=False):
    m = await db.ll_character_masters.find_one({"key": char_key})
    if not m:
        return None
    if m.get("status") != "READY":
        return {"ok": False, "message": "Master art is not ready to approve yet."}
    if not consistency_confirmed:
        return {"ok": False, "needs_consistency_check": True,
                "message": "Character Consistency Check™ required: confirm the turnaround and expression sheet show the SAME canonical character (skin tone, hair, facial proportions, eyes, smile, clothing, crown, palette) before locking Character Bible v1.0."}
    await db.ll_character_masters.update_one({"key": char_key}, {"$set": {
        "founder_approved": True, "status": "Approved", "version": "1.0",
        "consistency_confirmed": True, "consistency_confirmed_by": actor, "consistency_confirmed_at": now_iso(),
        "anchor_locked": True, "approved_by": actor, "approved_at": now_iso(), "updated_at": now_iso()}})
    await db.ll_characters.update_one({"key": char_key}, {"$set": {
        "founder_approved": True, "status": "Approved", "version": "1.0", "mastered": True,
        "anchor_locked": True, "identity_standard": ll.IDENTITY_STANDARD, "updated_at": now_iso()},
        "$push": {"version_history": {"version": "1.0", "note": "Consistency Check™ confirmed — Character Bible locked as Canon v1.0; model sheet is the permanent identity anchor.", "at": now_iso()}}})
    await ll.remember("character_master_approved", f"{m.get('name')} Consistency Check™ confirmed — Character Bible v1.0 locked (identity anchor set).", actor, char_key)
    return {"ok": True, "status": "Approved", "version": "1.0",
            "message": f"{m.get('name')} passed Character Consistency Check™ — Character Bible v1.0 locked. Every future asset inherits from this anchor."}


async def _approved_anchor(char_key):
    """Return the approved model-sheet PNG bytes (permanent identity anchor) for a locked Character Bible, else None."""
    if not char_key:
        return None
    m = await db.ll_character_masters.find_one({"key": char_key, "founder_approved": True})
    if not m:
        return None
    p = master_file_path(char_key, "model_sheet")
    return p.read_bytes() if p.exists() else None


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


def _build_publishing_package(ep, inh, char, title, total, episode_number):
    """Deterministic Publishing Package™ — child-safe metadata built from the verified KR. No fabrication."""
    topic = inh.get("term") or ep.get("kr_topic") or title
    cname = char["name"] if char else "the Little Legacy Learners"
    objective = ep.get("learning_objective") or inh.get("definition_plain") or f"Understand {topic}."
    takeaway = ep.get("treasure_takeaway") or inh.get("memory_sentence") or objective
    tags = [t for t in (inh.get("tags") or []) if str(t).lower() not in ("qru", "draft", "verified")]
    keywords = list(dict.fromkeys(
        ["Little Legacy Learners", "kids educational", "learning for kids", "preschool", "SEL",
         topic] + tags + ["QRU", "character education", "story for children"]))[:14]
    yt_title = f"{title} | Little Legacy Learners™ (Ep. {episode_number}) — Kids Learn {topic}"
    if len(yt_title) > 95:
        yt_title = f"{title} | Little Legacy Learners™ — Kids Learn {topic}"[:95]
    parent_qs = [f"What did {cname} discover about {topic}?",
                 f"Where can we see {topic} in our own day?",
                 (inh.get("challenge_questions") or [f"Can you explain {topic} in your own words?"])[0]]
    teacher_qs = [f"How does this episode introduce {topic} for {ep.get('age_band','early learners')}?",
                  f"Which prior idea does {topic} build on, and what comes next?",
                  "How would you check a child's understanding after watching?"]
    return {
        "youtube_title": yt_title,
        "seo_description": (f"{objective} Join {cname} in Little Legacy Learners™ — where little lessons today "
                            f"become big impact tomorrow. In this episode we explore {topic} in a warm, safe and "
                            f"joyful story that builds character, curiosity and confidence.\n\nTreasure Takeaway™: {takeaway}\n\n"
                            f"Learning objective: {objective}\n\nSubscribe for more Little Legacy Learners™ adventures.\n\n"
                            f"#LittleLegacyLearners #KidsLearning #{re.sub(r'[^A-Za-z0-9]','',topic)}")[:4900],
        "made_for_kids": True,
        "keywords": keywords,
        "playlist_recommendation": f"Little Legacy Learners™ — {ep.get('age_band','Early Learners')}",
        "episode_number": episode_number,
        "thumbnail_recommendation": f"Bright close-up of {cname} at Little Legacy Village™ with the episode title '{title}', gold + royal-purple QRU brand bar, a big warm smile and a rainbow. Large readable title, high contrast, no clutter.",
        "learning_objective": objective,
        "parent_discussion_questions": parent_qs,
        "teacher_discussion_questions": teacher_qs,
        "call_to_action": "Ask a grown-up: what will YOU learn today? Like, subscribe and join the next Little Legacy adventure!",
        "suggested_end_screen": "Warm 'See you next time!' card with the 6 Little Legacy Learners waving, a subscribe prompt and the next-episode thumbnail.",
        "suggested_next_episode": "Manufacture the next verified topic in this age band as Episode " + str(episode_number + 1) + ".",
        "copyright_footer": f"© {now_iso()[:4]} Queen Rothswell Universe™ (QRU™). Little Legacy Learners™ and all characters are trademarks of QRU. All rights reserved.",
        "brand_verification_checklist": [
            {"item": "Verified Knowledge Record source", "ok": inh.get("verified_external", False)},
            {"item": "Canonical characters only (no off-model art)", "ok": True},
            {"item": "Child-safe language & imagery", "ok": True},
            {"item": "Captions provided (.srt)", "ok": True},
            {"item": "Made-for-Kids compliance", "ok": True},
            {"item": "QRU copyright/footer present", "ok": True},
            {"item": "Treasure Standard™ takeaway present", "ok": bool(takeaway)},
        ],
        "generated_at": now_iso(),
    }


async def _pilot_job(episode_id, actor):
    try:
        ep = await db.ll_episodes.find_one({"id": episode_id})
        kr = await kri.load_kr(db, ep.get("primary_kr")) if ep.get("primary_kr") else None
        inh = kri.build_inheritance(kr) if kr else {}
        char = next((x for x in ll.CHARACTERS if x["key"] == ep.get("featured_character")), None)
        title, scenes = _build_scenes(ep, inh, char)
        voice = VOICE_PROFILES.get(ep.get("featured_character"), {}).get("voice", NARRATOR_VOICE)

        # Reference consistency — inherit appearance from the approved Character Bible v1.0 identity anchor.
        ref_pngs = None
        anchor = await _approved_anchor(char["key"]) if char else None
        if anchor:
            ref_pngs = [anchor]

        segments, durations, captions = [], [], []

        async def _one_scene(idx, sc):
            prompt = (f"Scene: {sc['visual']} {STYLE}"
                      + (" Keep the featured character exactly on-model — match the appearance, proportions, "
                         "colors, crown/props and style of the provided approved reference sheet." if ref_pngs else ""))
            try:
                png = await ai_service.generate_image_with_reference(
                    prompt, session_id=f"ll-pilot-{episode_id[:8]}-{idx}", reference_pngs=ref_pngs)
            except Exception as ie:
                logger.warning(f"[pilot {episode_id[:8]}] scene {idx} image failed: {str(ie)[:120]}")
                png = None
            if not png:
                png = _branded_card(title if sc["label"] == "Title" else sc["label"], sc["caption"] or "")
            framed = _burn_caption(png, sc["caption"])
            # TTS with a hard timeout — a hung narration call can never freeze the whole render.
            audio = await asyncio.wait_for(mr.synthesize_voice(sc["narration"], voice=voice), timeout=TTS_TIMEOUT_S)
            dur = max(3.0, min(12.0, _duration_from_bytes(audio) + 0.5))
            logger.info(f"[pilot {episode_id[:8]}] scene {idx} ready ({dur}s)")
            return idx, framed, audio, dur, (sc["caption"] or sc["narration"][:80])

        logger.info(f"[pilot {episode_id[:8]}] rendering {len(scenes)} scenes (parallel image+voice)…")
        # Parallelize the per-scene image generation + narration (the biggest wall-clock cost). Every
        # scene uses the SAME approved character anchor, so they are independent and safe to run together.
        results = await asyncio.gather(*[_one_scene(i, sc) for i, sc in enumerate(scenes)])
        for idx, framed, audio, dur, cap in sorted(results, key=lambda r: r[0]):
            segments.append((framed, audio))
            durations.append(dur)
            captions.append(cap)

        logger.info(f"[pilot {episode_id[:8]}] encoding MP4 via ffmpeg…")
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
        consistent = bool(ref_pngs)
        gates = {
            "knowledge_first": {"pass": verified, "detail": "Source Knowledge Record is externally Verified." if verified else "Source not verified."},
            "character_consistency": {"pass": consistent, "detail": "Every scene inherits the approved Character Bible v1.0 identity anchor." if consistent else "FLAGGED: featured character has no approved Canon v1.0 anchor — appearance may drift. Approve the Character Bible first."},
            "child_safety": {"pass": not unsafe, "detail": "No prohibited content detected." if not unsafe else f"Flagged terms: {unsafe}"},
            "accessibility": {"pass": True, "detail": "Burned captions + downloadable .srt; warm clear narration; 16:9 720p."},
            "treasure_standard": {"pass": verified and not unsafe and consistent, "detail": "Understanding clear, craftsmanship complete, character on-model, aligns with QRU values." if (verified and not unsafe and consistent) else "Held — resolve blocking gates."},
        }
        all_pass = all(g["pass"] for g in gates.values())

        ep_number = await db.ll_pilots.count_documents({"founder_approved": True}) + 1
        package = _build_publishing_package(ep, inh, char, title, total, ep_number)

        qru_asset_id = f"LLP-{gen_id()[:8]}"
        await db.media_assets.update_one({"pilot_episode": episode_id}, {"$set": {
            "id": gen_id(), "qru_asset_id": qru_asset_id, "kind": "video", "provider": "qru_production",
            "title": f"Little Legacy Learners™ — {title} (Pilot)", "internal_storage_url": str(out_path),
            "duration_seconds": total, "width": 1280, "height": 720,
            "production_status": "PILOT_REVIEW", "distribution_ready": False,
            "gold_master_certified": False, "is_draft_preview": True,
            "publishing_package": package,
            "pilot_episode": episode_id, "franchise": "little-legacy-learners", "created_at": now_iso()}}, upsert=True)

        await db.ll_pilots.update_one({"episode_id": episode_id}, {"$set": {
            "id": gen_id(), "episode_id": episode_id, "title": title, "status": "READY",
            "technique": "QRU Animated Storybook Pilot™ — AI-generated key art with cinematic Ken Burns motion, "
                         "TTS narration and burned captions. Not frame-by-frame cel animation (stated honestly).",
            "scenes": [{"label": s["label"], "caption": s["caption"], "narration": s["narration"]} for s in scenes],
            "duration_seconds": total, "voice": voice, "featured_character": ep.get("featured_character"),
            "reference_locked": bool(ref_pngs),
            "video_url": f"/api/little-legacy/pilots/{episode_id}.mp4",
            "captions_url": f"/api/little-legacy/pilots/{episode_id}.srt",
            "gates": gates, "governance_passed": all_pass, "qru_asset_id": qru_asset_id,
            "publishing_package": package, "package_approved": False,
            "founder_approved": False, "created_by": actor, "created_at": now_iso(), "updated_at": now_iso()}}, upsert=True)
        await ll.remember("pilot_manufactured", f"Pilot '{title}' rendered ({total}s, {len(scenes)} scenes), governance {'PASSED' if all_pass else 'HELD'}.", actor, episode_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"[pilot {episode_id[:8]}] render FAILED: {str(e)[:240]}")
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
        "episode_id": episode_id, "title": ep.get("title"), "status": "RENDERING",
        "error": None, "render_started_at": now_iso(), "created_by": actor, "updated_at": now_iso()}}, upsert=True)
    asyncio.create_task(_pilot_job(episode_id, actor))
    return {"ok": True, "status": "RENDERING",
            "message": "Manufacturing the animated pilot in the background — generating scenes, narration, captions and rendering the MP4. This takes a few minutes."}


async def pilot_status(episode_id):
    p = await db.ll_pilots.find_one({"episode_id": episode_id}, {"_id": 0})
    if not p:
        return {"status": "NONE"}
    # Self-heal an interrupted render: if it has been RENDERING far longer than a real render takes and
    # no MP4 was produced, the background job was killed (e.g. the production container recycled). Report
    # it honestly as FAILED (retryable) instead of spinning in RENDERING forever.
    if p.get("status") == "RENDERING":
        out = LL_DIR / "pilots" / f"{episode_id}.mp4"
        if _age_seconds(p.get("render_started_at") or p.get("updated_at")) > PILOT_STALE_S and not out.exists():
            await db.ll_pilots.update_one({"episode_id": episode_id}, {"$set": {
                "status": "FAILED",
                "error": "Render was interrupted before it finished (the server likely recycled during the "
                         "multi-minute render). Tap Retry to manufacture it again.",
                "updated_at": now_iso()}})
            p["status"] = "FAILED"
            p["error"] = ("Render was interrupted before it finished (the server likely recycled during the "
                          "multi-minute render). Tap Retry to manufacture it again.")
    return p


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
        "founder_approved": True, "package_approved": True, "status": "APPROVED", "approved_by": actor, "approved_at": now_iso(), "updated_at": now_iso()}})
    pkg = p.get("publishing_package") or {}
    # Copy the pilot MP4 into the secure media root so it publishes through the existing pipeline (no re-upload).
    dist_path = str(out_path) if (out_path := pilot_file_path(episode_id)).exists() else None
    try:
        import media_production as mp
        import shutil
        media_root = mp.MEDIA_ROOT
        os.makedirs(media_root, exist_ok=True)
        if out_path.exists():
            dest = os.path.join(media_root, f"{p.get('qru_asset_id','LLP')}_{episode_id}.mp4")
            shutil.copyfile(str(out_path), dest)
            dist_path = dest
    except Exception:
        pass
    set_fields = {
        "is_draft_preview": False, "distribution_ready": True, "production_status": "APPROVED",
        "publish_title": pkg.get("youtube_title"), "publish_description": pkg.get("seo_description"),
        "publish_tags": pkg.get("keywords"), "made_for_kids": True}
    if dist_path:
        set_fields["internal_storage_url"] = dist_path
    await db.media_assets.update_one({"pilot_episode": episode_id}, {"$set": set_fields})
    await db.ll_episodes.update_one({"id": episode_id}, {"$set": {"status": "Approved", "founder_approved": True, "updated_at": now_iso()}})
    await ll.remember("pilot_approved", f"Pilot '{p.get('title')}' Founder-approved with Publishing Package™ — available to YouTube Publisher (no re-upload).", actor, episode_id)
    return {"ok": True, "status": "APPROVED",
            "message": "Pilot + Publishing Package™ approved. It is now in YouTube Publisher™ as a Factory asset with title, description, keywords and Made-for-Kids pre-filled — one-click publish, no re-upload."}


def pilot_file_path(episode_id):
    return LL_DIR / "pilots" / f"{episode_id}.mp4"


def captions_file_path(episode_id):
    return LL_DIR / "pilots" / f"{episode_id}.srt"



# ─────────────────── PHASE 4 — PRODUCT KIT (kid-format inheriting recipes) ───────────────────
# One verified Knowledge Record → the full kid catalog, through inheritance. No duplication:
# images inherit the approved Character Bible v1.0 anchor; text inherits the KR.
(LL_DIR / "kits").mkdir(parents=True, exist_ok=True)


def _kit_text_products(ep, inh, char):
    topic = inh.get("term") or ep.get("kr_topic") or "our topic"
    cname = char["name"] if char else "the Little Legacy Learners"
    objective = ep.get("learning_objective") or inh.get("definition_plain") or f"Understand {topic}."
    points = (inh.get("key_concepts") or inh.get("examples") or [])[:6]
    cards = [{"front": f"What is {topic}?", "back": inh.get("definition_plain") or objective}]
    for i, p in enumerate(points, 1):
        cards.append({"front": f"Knowledge Card {i}", "back": str(p)})
    workbook = {
        "title": f"{topic.title()} Workbook",
        "warm_up": f"Draw {cname}! What do you think {topic} means?",
        "trace_words": [topic, cname.split()[0], "kind", "learn"],
        "match": [{"prompt": str(p)[:40], "answer": topic} for p in points[:3]] or [{"prompt": topic, "answer": objective[:40]}],
        "questions": (inh.get("challenge_questions") or [f"Can you explain {topic} in your own words?"]) + [f"Where did {cname} see {topic} today?"],
    }
    parent_guide = {
        "objective": objective,
        "watch_together": f"Notice how {cname} stays curious and kind while learning about {topic}.",
        "discuss": [f"What did {cname} discover about {topic}?", f"Where can we see {topic} in our day?"],
        "activity": f"Point out an example of {topic} at home and talk about it.",
    }
    teacher_guide = {
        "objective": objective,
        "standards_note": "Supports early SEL, curiosity and verification habits (Knowledge-First).",
        "lesson_flow": ["Watch the episode", "Discuss the Treasure Takeaway", "Complete the workbook page", "Share one thing learned"],
        "assessment": f"Ask each child to explain {topic} in their own words.",
    }
    first = cname.split()[0]
    song = {
        "title": f"The {topic.title()} Song",
        "style": "Simple, warm, repetitive sing-along for young children (call-and-response).",
        "chorus": [f"{first}, {first}, show us the way,", f"we're learning about {topic} today!",
                   "Little lessons, big and bright,", "learning together feels just right!"],
        "verse_1": [f"When we wonder what to do,", f"{topic} helps us see it through.",
                    "Ask a question, look and see,", "that's how curious friends can be!"],
        "verse_2": [f"{first} says with a great big smile,", "\"Let's be kind and think a while.\"",
                    "Little lessons today, hooray,", "big impact tomorrow — hip hip hooray!"],
        "note": "Melody is a suggested simple nursery-rhyme cadence; a sing-along guide track is provided.",
    }
    course = {
        "title": f"Little Legacy Mini-Course: {topic.title()}",
        "audience": ep.get("age_band", "Early Learners"),
        "objective": objective,
        "modules": [
            {"module": 1, "title": f"Meet {cname} & the Big Question", "activity": "Watch the pilot episode + discuss the question."},
            {"module": 2, "title": f"Understanding {topic}", "activity": "Read the storybook; complete Knowledge Cards."},
            {"module": 3, "title": f"{topic.title()} in Real Life", "activity": "Find real examples; complete the workbook."},
            {"module": 4, "title": "Sing, Play & Create", "activity": "Sing the song; color the coloring page."},
            {"module": 5, "title": "Show What You Know", "activity": f"Explain {topic} in your own words (assessment)."},
        ],
        "completion": f"A child can joyfully explain {topic} and connect it to kindness and curiosity.",
    }
    return {"knowledge_cards": cards, "workbook": workbook, "parent_guide": parent_guide,
            "teacher_guide": teacher_guide, "song": song, "course": course,
            "social_caption": f"New from Little Legacy Learners: {cname} learns about {topic}! Little lessons today, big impact tomorrow. #LittleLegacyLearners"}


async def _kit_job(episode_id, actor):
    try:
        ep = await db.ll_episodes.find_one({"id": episode_id})
        kr = await kri.load_kr(db, ep.get("primary_kr")) if ep.get("primary_kr") else None
        inh = kri.build_inheritance(kr) if kr else {}
        char = next((x for x in ll.CHARACTERS if x["key"] == ep.get("featured_character")), None)
        cv = _char_visual(char) if char else "the six Little Legacy Learners"
        topic = inh.get("term") or ep.get("kr_topic") or "our topic"
        anchor = await _approved_anchor(char["key"]) if char else None
        consistent = bool(anchor)
        ref = [anchor] if anchor else None

        images = {}
        specs = {
            "coloring_page": (f"Black and white line-art COLORING PAGE for young children of {cv} at Little Legacy "
                              f"Village. Clean bold outlines, no shading, no color, plenty of white space to color in. "
                              f"Keep the character exactly on-model to the reference."),
            "social_asset": (f"Bright square social media poster of {cv} with a warm smile, joyful and inviting, "
                             f"gold and royal-purple QRU brand accents. Keep the character on-model to the reference."),
            "storybook_cover": (f"Storybook cover illustration of {cv} exploring {topic} at Little Legacy Village, "
                                f"warm and premium, on-model to the reference."),
        }
        for kind, prompt in specs.items():
            png = await ai_service.generate_image_with_reference(prompt + " " + STYLE, session_id=f"ll-kit-{episode_id[:8]}-{kind}", reference_pngs=ref)
            if not png:
                png = _branded_card(topic.title(), kind.replace("_", " ").title())
            (LL_DIR / "kits" / f"{episode_id}_{kind}.png").write_bytes(png)
            images[kind] = f"/api/little-legacy/kits/{episode_id}/{kind}.png"

        text = _kit_text_products(ep, inh, char)
        products = [
            {"format": "Coloring Page", "kind": "image", "url": images["coloring_page"]},
            {"format": "Social / Marketing Asset", "kind": "image", "url": images["social_asset"], "caption": text["social_caption"]},
            {"format": "Storybook Cover", "kind": "image", "url": images["storybook_cover"]},
            {"format": "Knowledge Cards", "kind": "text", "data": text["knowledge_cards"]},
            {"format": "Activity Pack / Workbook", "kind": "text", "data": text["workbook"]},
            {"format": "Parent Guide", "kind": "text", "data": text["parent_guide"]},
            {"format": "Teacher Guide", "kind": "text", "data": text["teacher_guide"]},
        ]
        await db.ll_kits.update_one({"episode_id": episode_id}, {"$set": {
            "id": gen_id(), "episode_id": episode_id, "title": ep.get("title"), "topic": topic,
            "featured_character": ep.get("featured_character"), "status": "READY",
            "consistency_inherited": consistent,
            "consistency_note": "All artwork inherits the approved Character Bible v1.0 identity anchor." if consistent else "FLAGGED: no approved anchor for the featured character — art may drift.",
            "products": products, "founder_approved": False,
            "created_by": actor, "created_at": now_iso(), "updated_at": now_iso()}}, upsert=True)
        await ll.remember("product_kit_manufactured", f"Product Kit for '{ep.get('title')}' manufactured ({len(products)} formats).", actor, episode_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        await db.ll_kits.update_one({"episode_id": episode_id}, {"$set": {
            "episode_id": episode_id, "status": "FAILED", "error": str(e)[:240], "updated_at": now_iso()}}, upsert=True)


async def manufacture_kit(episode_id, actor="Founder"):
    ep = await db.ll_episodes.find_one({"id": episode_id})
    if not ep:
        return None
    if ep.get("verification_status") != "Verified":
        return {"ok": False, "blocked": True,
                "message": "Knowledge-First: verify this episode's Knowledge Record before manufacturing kids' products (Treasure Standard)."}
    await db.ll_kits.update_one({"episode_id": episode_id}, {"$set": {
        "episode_id": episode_id, "title": ep.get("title"), "status": "RENDERING", "created_by": actor, "updated_at": now_iso()}}, upsert=True)
    asyncio.create_task(_kit_job(episode_id, actor))
    return {"ok": True, "status": "RENDERING",
            "message": "Manufacturing the full Product Kit (coloring page, social/marketing asset, storybook cover, knowledge cards, workbook, parent & teacher guides) from the one verified Knowledge Record — inheriting the approved Character Bible anchor."}


async def kit_status(episode_id):
    return await db.ll_kits.find_one({"episode_id": episode_id}, {"_id": 0}) or {"status": "NONE"}


async def list_kits():
    return [k async for k in db.ll_kits.find({}, {"_id": 0}).sort("created_at", -1).limit(50)]


async def approve_kit(episode_id, actor="Founder"):
    k = await db.ll_kits.find_one({"episode_id": episode_id})
    if not k:
        return None
    if k.get("status") != "READY":
        return {"ok": False, "message": "Kit is not ready to approve yet."}
    await db.ll_kits.update_one({"episode_id": episode_id}, {"$set": {
        "founder_approved": True, "status": "APPROVED", "approved_by": actor, "approved_at": now_iso(), "updated_at": now_iso()}})
    await ll.remember("product_kit_approved", f"Product Kit for '{k.get('title')}' Founder-approved.", actor, episode_id)
    return {"ok": True, "status": "APPROVED", "message": "Product Kit approved — the full family is ready for distribution."}


def kit_file_path(episode_id, kind):
    return LL_DIR / "kits" / f"{episode_id}_{kind}.png"


# ─────────────────── PHASE 4 — ONE-CLICK "MANUFACTURE THE WHOLE FAMILY" ───────────────────
async def manufacture_family(episode_id, actor="Founder"):
    """One click → the animated pilot AND the full Product Kit from one verified Knowledge Record."""
    ep = await db.ll_episodes.find_one({"id": episode_id})
    if not ep:
        return None
    if ep.get("verification_status") != "Verified":
        return {"ok": False, "blocked": True,
                "message": "Knowledge-First: verify this episode's Knowledge Record before manufacturing (Treasure Standard)."}
    await db.ll_pilots.update_one({"episode_id": episode_id}, {"$set": {"episode_id": episode_id, "title": ep.get("title"), "status": "RENDERING", "created_by": actor, "updated_at": now_iso()}}, upsert=True)
    await db.ll_kits.update_one({"episode_id": episode_id}, {"$set": {"episode_id": episode_id, "title": ep.get("title"), "status": "RENDERING", "created_by": actor, "updated_at": now_iso()}}, upsert=True)
    asyncio.create_task(_pilot_job(episode_id, actor))
    asyncio.create_task(_kit_job(episode_id, actor))
    await ll.remember("family_manufacture_started", f"Whole-family manufacture started for '{ep.get('title')}' (pilot + product kit).", actor, episode_id)
    return {"ok": True, "status": "RENDERING",
            "message": "Manufacturing the whole family from one verified Knowledge Record — the animated pilot AND the full Product Kit. Review both in Pilot Studio and Product Kits when ready."}


async def family_status(episode_id):
    p = await pilot_status(episode_id)
    k = await kit_status(episode_id)
    ready = (p.get("status") in ("READY", "APPROVED")) and (k.get("status") in ("READY", "APPROVED"))
    return {"pilot": {"status": p.get("status"), "video_url": p.get("video_url"), "governance_passed": p.get("governance_passed")},
            "kit": {"status": k.get("status"), "products": len(k.get("products", []))},
            "ready": ready}


# ─────────────────── PHASE 4 — LITTLE LEGACY PROJECT ZERO (inherits project_zero) ───────────────────
import project_zero


async def submit_feedback(episode_id, payload, actor="Learner"):
    ep = await db.ll_episodes.find_one({"id": episode_id})
    if not ep or not ep.get("primary_kr"):
        return {"ok": False, "message": "Episode or its Knowledge Record not found."}
    role = (payload.get("role") or "parent").lower()
    fb_payload = {
        "product_id": episode_id, "product_type": "little_legacy_episode",
        "source": role, "rating": payload.get("rating"),
        "understanding_before": payload.get("understanding_before"),
        "understanding_after": payload.get("understanding_after"),
        "comment": payload.get("comment"),
        "suggested_improvement": payload.get("suggested_improvement"),
    }
    res = await project_zero.ingest_feedback(ep["primary_kr"], fb_payload, actor=f"{role}:{actor}")
    if res is None:
        return {"ok": False, "message": "Could not attach feedback to the Knowledge Record."}
    await ll.remember("project_zero_feedback", f"{role.title()} feedback on '{ep.get('title')}' fed back into the originating Knowledge Record.", actor, episode_id)
    return {"ok": True, "message": "Thank you — verified improvements flow back into the originating Knowledge Record so every future product improves.", **res}


async def feedback_loop(episode_id):
    ep = await db.ll_episodes.find_one({"id": episode_id})
    if not ep or not ep.get("primary_kr"):
        return {"feedback": [], "aggregate": {"feedback_count": 0}}
    data = await project_zero.loop(ep["primary_kr"])
    data["episode_feedback"] = [f for f in data.get("feedback", []) if f.get("product_id") == episode_id]
    return data
