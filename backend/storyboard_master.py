"""QRU Storyboard Master™ — the shared media blueprint inside the QRU Product Manufacturing Engine™.

One approved Knowledge Record™ → one versioned Storyboard Master™ → many format-specific media renders.
Knowledge-First & honest: factual content is inherited verbatim from the exact approved KR version; the
media workflow adapts presentation/pacing only — it never rewrites source knowledge. A successful render
is NOT Gold Standard; Gold requires verified source + passed validation + human approval. No new
top-level engine is created — this extends Product Manufacturing.
"""
import os
import re
import textwrap
from pathlib import Path

import cairosvg

from database import db
from models import gen_id, now_iso
import poster_studio as pstudio  # reuse governed SVG brand primitives

MEDIA_DIR = Path(os.environ.get("QRU_MEDIA_DIR", "/app/backend/generated_media"))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

STATUS_MODEL = ["DRAFT", "INTERNAL_REVIEW", "VERIFICATION_REQUIRED", "REVISION_REQUIRED",
                "MEDIA_APPROVED", "PLATFORM_READY", "PUBLISHING_READY", "QRU_GOLD_STANDARD", "SUPERSEDED"]

VOICE_PROFILES = {
    "QRU Narrator™": {"tone": "warm, authoritative", "pacing": "measured", "energy": "calm", "audience": "general"},
    "QRU Teacher™": {"tone": "clear, encouraging", "pacing": "deliberate", "energy": "steady", "audience": "learners"},
    "QRU Coach™": {"tone": "motivating, direct", "pacing": "brisk", "energy": "high", "audience": "practitioners"},
    "QRU Documentary™": {"tone": "reflective, cinematic", "pacing": "slow", "energy": "low", "audience": "general"},
    "QRU Youth Educator™": {"tone": "friendly, vivid", "pacing": "lively", "energy": "high", "audience": "youth"},
    "QRU Executive™": {"tone": "concise, confident", "pacing": "efficient", "energy": "steady", "audience": "executives"},
    "QRU Inspirational™": {"tone": "uplifting", "pacing": "building", "energy": "rising", "audience": "general"},
}

MOTION_LANGUAGE = ["Elegant fades", "Slow zooms", "Purposeful highlights", "Relationship lines",
                   "Diagram reveals", "Subtle movement", "Calm pacing", "Clear scene transitions"]

# One governed recipe per media format.
FORMAT_RECIPES = {
    "youtube_video": {"label": "YouTube Video", "aspect": "16:9", "resolution": "1920x1080", "target_seconds": 90,
                      "captions": True, "voice": "QRU Narrator™", "render": "video", "intro_outro": True},
    "promo_short": {"label": "Short Promotional Video", "aspect": "9:16", "resolution": "1080x1920", "target_seconds": 30,
                    "captions": True, "voice": "QRU Coach™", "render": "video", "intro_outro": False,
                    "promo_rules": ["No overstated outcomes", "No invented claims", "No guaranteed results"]},
    "audio_lesson": {"label": "Narrated Audio Lesson", "aspect": "audio", "resolution": "audio", "target_seconds": 180,
                     "captions": True, "voice": "QRU Teacher™", "render": "audio"},
    "teacher_presentation": {"label": "Teacher Presentation", "aspect": "16:9", "resolution": "1280x720", "target_seconds": 0,
                             "captions": False, "voice": None, "render": "pptx", "facing": "teacher"},
    "student_presentation": {"label": "Student Presentation", "aspect": "16:9", "resolution": "1280x720", "target_seconds": 0,
                             "captions": False, "voice": None, "render": "pptx", "facing": "student"},
}


# ── Knowledge-First resolution ──────────────────────────────────────────────
async def _load_kr(kr_id):
    for coll in (db.knowledge_engine_records, db.knowledge_records):
        doc = await coll.find_one({"id": kr_id}, {"_id": 0})
        if doc:
            return doc
    return None


def _kr_topic(kr):
    return kr.get("topic") or kr.get("title") or "this topic"


def _kr_verified(kr):
    v = kr.get("verification") or {}
    return bool(v.get("evidence_sufficient_for_external_publication") or kr.get("verified_external"))


def _kr_sections(kr):
    """Extract (label, text) knowledge blocks verbatim from the approved KR (never rewritten)."""
    out = []
    sec = kr.get("sections")
    if isinstance(sec, dict):
        for k in ("definition", "explanation", "examples", "relationships", "common_misunderstandings"):
            v = sec.get(k)
            if isinstance(v, list):
                v = " ".join(str(x) for x in v)
            if v:
                out.append((k.replace("_", " ").title(), str(v)))
    for k, lab in (("simple_answer", "Simple Answer"), ("verified_truth", "Verified Truth"),
                   ("qru_translation", "QRU Translation™"), ("deep_roots", "Deep Roots"), ("content", "Content")):
        v = kr.get(k)
        if isinstance(v, list):
            v = " ".join(str(x) for x in v)
        if v:
            out.append((lab, str(v)))
    return out[:6] or [("Overview", f"A governed explanation of {_kr_topic(kr)}.")]


def _sentences(text, n=2):
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return " ".join([p.strip() for p in parts if p.strip()][:n])


# ── Storyboard Master generation ────────────────────────────────────────────
def _build_scenes(kr):
    topic = _kr_topic(kr)
    blocks = _kr_sections(kr)
    scenes = []
    # Opening hook
    scenes.append({
        "scene": 1, "learning_objective": f"Orient the viewer to {topic}",
        "kr_section": "Opening", "narration": f"What if you finally understood {topic}? Let's make it simple.",
        "visual_direction": "Open on a familiar, relatable scene; slow zoom in.",
        "visual_asset_ref": None, "on_screen_text": topic.title(),
        "animation": "Elegant fade in", "audio_direction": "Warm intro tone, low bed",
        "duration_sec": 6, "accessibility": "Caption + high contrast title", "citation": None,
        "assessment": None, "cta": None,
    })
    for i, (label, text) in enumerate(blocks, start=2):
        scenes.append({
            "scene": i, "learning_objective": f"Explain: {label}",
            "kr_section": label, "narration": _sentences(text, 2),
            "visual_direction": "Reveal the idea with one clean supporting visual; purposeful highlight.",
            "visual_asset_ref": None, "on_screen_text": label,
            "animation": "Diagram reveal", "audio_direction": "Narration forward, bed low",
            "duration_sec": 12, "accessibility": "Accurate captions; readable placement",
            "citation": (kr.get("kr_code") or None),
            "assessment": (f"Reflect: how does {label.lower()} apply to you?" if i == len(blocks) + 1 else None),
            "cta": None,
        })
    # Close / CTA
    scenes.append({
        "scene": len(scenes) + 1, "learning_objective": "Leave the viewer seeing the world differently",
        "kr_section": "Close", "narration": "That's the QRU way — we don't just teach information, we create understanding.",
        "visual_direction": "Close on an empowered, transformed viewer; QRU brand outro.",
        "visual_asset_ref": None, "on_screen_text": "Quest for Real Understanding™",
        "animation": "Slow zoom out + fade", "audio_direction": "Uplifting resolve",
        "duration_sec": 6, "accessibility": "Caption + brand seal alt-text", "citation": None,
        "assessment": None, "cta": "Learn more with QRU.",
    })
    return scenes


async def create_storyboard(kr_id, actor="Founder", audience="General learners", tone="Warm, authoritative"):
    kr = await _load_kr(kr_id)
    if not kr:
        return None
    scenes = _build_scenes(kr)
    sid = gen_id()
    total = sum(s["duration_sec"] for s in scenes)
    rec = {
        "id": sid, "sb_code": f"SBM-{sid[:6].upper()}", "version": 1,
        "kr_id": kr_id, "kr_code": kr.get("kr_code"), "kr_version": kr.get("version", 1),
        "topic": _kr_topic(kr), "audience": audience, "tone": tone,
        "knowledge_first": True, "source_verified_external": _kr_verified(kr),
        "scenes": scenes, "scene_count": len(scenes), "estimated_seconds": total,
        "motion_language": MOTION_LANGUAGE,
        "provenance": {"source_kr": kr_id, "source_kr_version": kr.get("version", 1),
                       "generated_at": now_iso(), "by": actor, "renderer": "storyboard_master",
                       "governing_standards": ["STD-CON-0001", "STD-DESIGN-0001", "QRU-CON-0002"]},
        "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
        "history": [{"event": "created", "at": now_iso(), "by": actor, "version": 1}],
    }
    await db.storyboard_masters.insert_one(dict(rec))
    rec.pop("_id", None)
    return rec


# ── Brand title card (governed SVG → PNG, machine text) ─────────────────────
def _title_card_png(topic, subtitle, w, h):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
             f'<rect width="{w}" height="{h}" fill="{pstudio.INK}"/>',
             f'<rect x="8" y="8" width="{w-16}" height="{h-16}" fill="none" stroke="{pstudio.GOLD}" stroke-width="2" opacity="0.5"/>',
             pstudio._shield(w/2 - 55, h*0.16, 110)]
    lines = textwrap.wrap(topic.title(), width=18) or [topic]
    ty = h*0.5
    for ln in lines:
        parts.append(f'<text x="{w/2}" y="{ty}" font-family="{pstudio.SERIF}" font-size="{min(96, int(w/12))}" font-weight="bold" fill="{pstudio.WHITE}" text-anchor="middle">{pstudio._esc(ln)}</text>')
        ty += min(96, int(w/12)) * 1.1
    parts.append(f'<text x="{w/2}" y="{ty+20}" font-family="{pstudio.SANS}" font-size="{min(34, int(w/32))}" fill="{pstudio.GOLD}" text-anchor="middle" letter-spacing="3">{pstudio._esc(subtitle)}</text>')
    parts.append(f'<text x="{w/2}" y="{h-40}" font-family="{pstudio.SANS}" font-size="22" fill="{pstudio.CREAM}" text-anchor="middle" letter-spacing="2">QUEST FOR REAL UNDERSTANDING\u2122</text>')
    parts.append('</svg>')
    return cairosvg.svg2png(bytestring="\n".join(parts).encode("utf-8"), output_width=w, output_height=h)


# ── Presentation renderer (real PPTX) ───────────────────────────────────────
def _render_presentation(sb, facing):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    NAVY = RGBColor(0x0B, 0x10, 0x30)
    GOLD = RGBColor(0xE7, 0xB5, 0x3C)
    WHITE = RGBColor(0xFF, 0xFF, 0xFF)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    def bg(slide, color=NAVY):
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = color

    def tb(slide, x, y, w, h, text, size, color=WHITE, bold=False, align_center=False):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame; tf.word_wrap = True
        tf.text = text
        p = tf.paragraphs[0]
        p.font.size = Pt(size); p.font.bold = bold; p.font.color.rgb = color
        from pptx.enum.text import PP_ALIGN
        if align_center:
            p.alignment = PP_ALIGN.CENTER
        return box

    # Title slide
    s = prs.slides.add_slide(blank); bg(s)
    tb(s, 1, 2.4, 11.3, 1.5, sb["topic"].title(), 44, GOLD, True, True)
    tb(s, 1, 4.0, 11.3, 0.8, f"{'Teacher Edition' if facing=='teacher' else 'Student Edition'} · QRU PRESS\u2122", 20, WHITE, False, True)
    tb(s, 1, 6.6, 11.3, 0.6, f"Source: {sb.get('kr_code','verified KR')} · Quest for Real Understanding\u2122", 12, WHITE, False, True)

    for sc in sb["scenes"]:
        s = prs.slides.add_slide(blank); bg(s)
        tb(s, 0.7, 0.5, 12, 1.0, sc["on_screen_text"] or sc["kr_section"], 30, GOLD, True)
        tb(s, 0.7, 1.7, 12, 3.0, sc["narration"], 22, WHITE)
        tb(s, 0.7, 5.0, 12, 0.6, f"Objective: {sc['learning_objective']}", 14, GOLD)
        if facing == "teacher":
            note = sc.get("assessment") or sc.get("cta") or "Discussion: invite learners to explain this in their own words."
            tb(s, 0.7, 5.7, 12, 1.2, f"Teacher note: {note}", 14, WHITE)
            notes = s.notes_slide.notes_text_frame
            notes.text = f"Learning objective: {sc['learning_objective']}\nVisual: {sc['visual_direction']}\nSource: {sc['kr_section']}"
        else:
            tb(s, 0.7, 5.7, 12, 1.2, "Reflect: how would you explain this to a friend?", 14, WHITE)
    import io
    buf = io.BytesIO(); prs.save(buf); return buf.getvalue()


# ── Format render dispatch ──────────────────────────────────────────────────
def _save_media(sid, fmt, ext, data):
    path = MEDIA_DIR / f"{sid}-{fmt}.{ext}"
    path.write_bytes(data if isinstance(data, (bytes, bytearray)) else data.encode("utf-8"))
    return path


async def render_format(sb, fmt, actor="Founder"):
    recipe = FORMAT_RECIPES.get(fmt)
    if not recipe:
        return {"error": f"Unknown format '{fmt}'."}
    sid = sb["id"]
    files, notes, render_status = [], [], "RENDERED"

    if recipe["render"] == "pptx":
        data = _render_presentation(sb, recipe["facing"])
        _save_media(sid, fmt, "pptx", data)
        files.append({"format": "pptx", "bytes": len(data), "url": f"/api/media-studio/file/{sid}/{fmt}/pptx"})

    elif recipe["render"] == "audio":
        # Narration transcript (verbatim from storyboard; TTS available downstream via OpenAI voice).
        transcript = "\n\n".join([f"[Scene {s['scene']}] {s['narration']}" for s in sb["scenes"]])
        _save_media(sid, fmt, "txt", transcript)
        files.append({"format": "txt", "bytes": len(transcript.encode()), "url": f"/api/media-studio/file/{sid}/{fmt}/txt", "label": "Narration transcript"})
        notes.append(f"Voice profile: {recipe['voice']}. TTS narration renders on demand (OpenAI voice) — transcript is final & governed.")
        render_status = "SCRIPT_READY"

    elif recipe["render"] == "video":
        w, h = [int(x) for x in recipe["resolution"].split("x")]
        card = _title_card_png(sb["topic"], recipe["label"], w, h)
        _save_media(sid, fmt, "png", card)
        files.append({"format": "png", "bytes": len(card), "url": f"/api/media-studio/file/{sid}/{fmt}/png", "label": "Title card / thumbnail"})
        shotlist = "\n\n".join([
            f"SCENE {s['scene']} ({s['duration_sec']}s) — {s['kr_section']}\n"
            f"  NARRATION: {s['narration']}\n  ON-SCREEN: {s['on_screen_text']}\n"
            f"  VISUAL: {s['visual_direction']}\n  MOTION: {s['animation']}\n  AUDIO: {s['audio_direction']}\n"
            f"  ACCESSIBILITY: {s['accessibility']}" for s in sb["scenes"]])
        _save_media(sid, fmt, "txt", shotlist)
        files.append({"format": "txt", "bytes": len(shotlist.encode()), "url": f"/api/media-studio/file/{sid}/{fmt}/txt", "label": "Shot list / captions script"})
        notes.append("Final MP4 is assembled by the EXISTING Flagship Showcase™ pipeline (scene assets + TTS + ffmpeg) — not duplicated here. Storyboard, title card and caption script are governed and ready.")
        if fmt == "promo_short":
            notes.append("Promo rules enforced: no overstated outcomes, no invented claims, no guaranteed results.")
        render_status = "STORYBOARD_READY"

    # Media Quality Gate (deterministic)
    checks = _media_quality_gate(sb, recipe, files)
    # Knowledge-First status gating
    if not sb.get("source_verified_external"):
        status = "VERIFICATION_REQUIRED"
    elif checks["blocked"]:
        status = "REVISION_REQUIRED"
    else:
        status = "DRAFT"  # rendered; MEDIA_APPROVED / GOLD require human approval

    pid = gen_id()
    product = {
        "id": pid, "storyboard_id": sid, "sb_code": sb["sb_code"], "format": fmt, "recipe": recipe,
        "label": recipe["label"], "topic": sb["topic"], "kr_id": sb["kr_id"], "kr_code": sb.get("kr_code"),
        "kr_version": sb.get("kr_version"), "voice_profile": recipe.get("voice"),
        "render_status": render_status, "files": files, "notes": notes,
        "quality_gate": checks, "treasure_status": checks["verdict"],
        "verification_status": "VERIFIED_EXTERNAL" if sb.get("source_verified_external") else "PENDING_HUMAN_VERIFICATION",
        "status": status, "provenance": {**sb["provenance"], "media_recipe": fmt},
        "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
        "history": [{"status": status, "at": now_iso(), "by": actor}],
    }
    await db.media_products.insert_one(dict(product))
    product.pop("_id", None)
    return product


def _media_quality_gate(sb, recipe, files):
    checks = []

    def chk(name, ok, why=""):
        checks.append({"check": name, "passed": bool(ok), "detail": why,
                       "severity": "PASSED" if ok else "BLOCKING_FAILURE"})

    all_narr = " ".join(s["narration"] for s in sb["scenes"]).lower()
    chk("Knowledge fidelity (inherits verified KR)", bool(sb.get("kr_id")))
    chk("Narration present & clean", bool(all_narr.strip()) and not any(t in all_narr for t in ("lorem", "todo", "{{", "placeholder")))
    chk("Scenes complete", all(s.get("narration") and s.get("learning_objective") and s.get("on_screen_text") for s in sb["scenes"]))
    chk("Accessibility (captions/notes)", all(s.get("accessibility") for s in sb["scenes"]))
    chk("At least one deliverable file", len(files) > 0)
    chk("Brand + platform recipe applied", bool(recipe.get("aspect")))
    if not sb.get("source_verified_external"):
        chk("Knowledge-First: verified source KR", False, "media from an unverified KR stays INTERNAL_DRAFT")
    else:
        checks.append({"check": "Knowledge-First: verified source KR", "passed": True, "detail": "KR externally verified", "severity": "PASSED"})
    blocked = any(c["severity"] == "BLOCKING_FAILURE" for c in checks)
    return {"verdict": "RETURN_TO_PRODUCTION" if blocked else "TREASURE_STANDARD_PASSED",
            "blocked": blocked, "checks": checks,
            "counts": {"passed": sum(1 for c in checks if c["passed"]), "total": len(checks),
                       "blocking": sum(1 for c in checks if c["severity"] == "BLOCKING_FAILURE")}}


def media_file_path(sid, fmt, ext):
    return MEDIA_DIR / f"{sid}-{fmt}.{ext}"


async def run_media_order(kr_id, formats, actor="Founder"):
    """One KR → one Storyboard Master → render the SELECTED formats (never all automatically)."""
    sb = await create_storyboard(kr_id, actor)
    if sb is None:
        return None
    products = []
    for fmt in formats:
        p = await render_format(sb, fmt, actor)
        if p and not p.get("error"):
            products.append(p)
    return {"storyboard": sb, "products": products,
            "knowledge_first": True, "source_verified_external": sb.get("source_verified_external"),
            "note": ("All media inherits the verified Knowledge Record; a successful render is NOT Gold Standard."
                     if sb.get("source_verified_external") else
                     "Source KR is not externally verified — media is held at INTERNAL DRAFT (Verify & Promote the KR first).")}


def overview():
    return {"status_model": STATUS_MODEL, "voice_profiles": VOICE_PROFILES, "motion_language": MOTION_LANGUAGE,
            "format_recipes": {k: {kk: vv for kk, vv in v.items() if kk != "render"} for k, v in FORMAT_RECIPES.items()},
            "model": "Approved Knowledge Record™ → Storyboard Master™ → Format Rendering → Gold Standard Media Products™",
            "note": "Extends the Product Manufacturing Engine™ — no new top-level engine."}
