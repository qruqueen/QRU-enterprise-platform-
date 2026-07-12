"""QRU Poster Studio™ — governed template-driven poster manufacturing (QRU-CON-0002 family).

Text, numbers, citations, spacing, dimensions and layout are 100% controlled by machine-rendered
SVG templates (never AI). AI art may only be composited as an approved decorative asset. Factual
posters must originate from an externally-verified Knowledge Record™ (Knowledge-First); if the source
KR is not externally verified, the poster is held at INTERNAL_DRAFT and never labelled QRU Gold
Standard™. Renders to a crisp vector PDF (print) + high-resolution PNG (screen/thumbnail).
"""
import os
import html
import textwrap
from pathlib import Path

import cairosvg

from database import db
from models import gen_id, now_iso
import publishing_standard as ps

POSTER_DIR = Path(os.environ.get("QRU_POSTER_DIR", "/app/backend/generated_posters"))
POSTER_DIR.mkdir(parents=True, exist_ok=True)

SERIF = "'DejaVu Serif', Georgia, serif"
SANS = "'DejaVu Sans', Helvetica, Arial, sans-serif"

# QRU palette
NAVY = "#0B1030"
INK = "#05040E"
GOLD = "#E7B53C"
CREAM = "#F3ECD8"
WHITE = "#FFFFFF"
STEP_COLORS = ["#8B6FD6", "#4A8FD6", "#4FAE5A", "#D6A93A"]  # familiar / discovery / connection / transformation

STATUS_MODEL = ["DRAFT", "INTERNAL_REVIEW", "VERIFICATION_REQUIRED", "REVISION_REQUIRED",
                "DESIGN_APPROVED", "PRINT_READY", "PUBLISHING_READY", "QRU_GOLD_STANDARD", "SUPERSEDED"]

TEMPLATES = [
    {"id": "process-formula-v1", "family": "Process / Formula Poster", "version": "1.0",
     "dimensions": {"w": 1600, "h": 2000, "aspect": "4:5"}, "steps": 4,
     "purpose": "A 4-step transformation formula with per-step outcome and a summary journey band."},
]


def _esc(s):
    return html.escape(str(s or ""), quote=True)


def _wrap(text, width):
    """Word-wrap into lines for SVG tspans (approx chars-per-line by panel width)."""
    return textwrap.wrap(str(text or ""), width=width) or [""]


def _tspans(lines, x, y, dy, cls_attrs):
    out = []
    for i, ln in enumerate(lines):
        out.append(f'<text x="{x}" y="{y + i * dy}" {cls_attrs}>{_esc(ln)}</text>')
    return "\n".join(out)


def _default_process_content(topic="The QRU Learning Formula"):
    return {
        "eyebrow": "THE QRU",
        "title": "LEARNING FORMULA",
        "trademark": True,
        "tagline": "SIMPLE.  POWERFUL.  TRANSFORMATIVE.",
        "subtitle": "WE DON'T JUST TEACH INFORMATION. WE CREATE UNDERSTANDING.",
        "steps": [
            {"heading": "START WITH WHAT PEOPLE ALREADY KNOW.",
             "body": "Begin with a familiar experience or idea. Meet people where they are.",
             "outcome": "YOU FEEL CONNECTED."},
            {"heading": "REVEAL WHAT THEY NEVER NOTICED.",
             "body": "Uncover the hidden patterns, connections, or truths that were always there.",
             "outcome": "YOU HAVE AN \u201cAHA!\u201d MOMENT."},
            {"heading": "CONNECT IT TO THE BIGGER SYSTEM.",
             "body": "Show how it fits into the larger picture. Everything is connected.",
             "outcome": "YOU SEE THE BIGGER PICTURE."},
            {"heading": "LEAVE THEM SEEING THE WORLD DIFFERENTLY.",
             "body": "End with a new lens, not just new information. Empower them to think differently, act wisely, and live empowered.",
             "outcome": "YOU ARE TRANSFORMED."},
        ],
        "mid_wordmark": "QRU",
        "mid_line": "WE TEACH PEOPLE HOW TO THINK, NOT WHAT TO THINK.",
        "mid_left": "Knowledge Changes Everything.",
        "mid_right": "Legacy Changes Generations.",
        "summary": [
            {"label": "FAMILIAR", "text": "They understand this part."},
            {"label": "DISCOVERY", "text": "They discover what they missed."},
            {"label": "CONNECTION", "text": "They connect it to the system."},
            {"label": "TRANSFORMATION", "text": "They see the world in a new way."},
        ],
        "footer": "CURIOSITY STARTS THE JOURNEY.  UNDERSTANDING CHANGES EVERYTHING.",
    }


def _shield(x, y, s, color=GOLD):
    """A compact QRU crest at (x,y) with size s."""
    return (
        f'<g transform="translate({x},{y})">'
        f'<path d="M0,0 L{s},0 L{s},{s*0.72} Q{s},{s*1.02} {s*0.5},{s*1.15} '
        f'Q0,{s*1.02} 0,{s*0.72} Z" fill="{NAVY}" stroke="{color}" stroke-width="3"/>'
        f'<text x="{s*0.5}" y="{s*0.62}" font-family="{SERIF}" font-size="{s*0.34}" font-weight="bold" '
        f'fill="{color}" text-anchor="middle">QRU</text>'
        f'</g>'
    )


def _seal(cx, cy, r):
    return (
        f'<g><circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GOLD}" stroke-width="3"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r-8}" fill="none" stroke="{GOLD}" stroke-width="1"/>'
        f'<text x="{cx}" y="{cy-6}" font-family="{SANS}" font-size="16" font-weight="bold" fill="{GOLD}" text-anchor="middle">QUEST FOR</text>'
        f'<text x="{cx}" y="{cy+14}" font-family="{SERIF}" font-size="20" font-weight="bold" fill="{GOLD}" text-anchor="middle">REAL</text>'
        f'<text x="{cx}" y="{cy+34}" font-family="{SANS}" font-size="13" font-weight="bold" fill="{GOLD}" text-anchor="middle">UNDERSTANDING</text></g>'
    )


def _build_process_svg(c):
    W, H = 1600, 2000
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    # background
    parts.append(f'<rect width="{W}" height="{H}" fill="{INK}"/>')
    parts.append(f'<rect x="10" y="10" width="{W-20}" height="{H-20}" fill="none" stroke="{GOLD}" stroke-width="2" opacity="0.5"/>')

    # ── Header ──
    parts.append(_shield(70, 60, 120))
    parts.append(_seal(W - 150, 130, 92))
    parts.append(f'<text x="{W/2}" y="95" font-family="{SERIF}" font-size="46" font-weight="bold" fill="{GOLD}" text-anchor="middle" letter-spacing="4">{_esc(c["eyebrow"])}</text>')
    tm = '<tspan font-size="34" dy="-28">\u2122</tspan>' if c.get("trademark") else ""
    parts.append(f'<text x="{W/2}" y="165" font-family="{SERIF}" font-size="84" font-weight="bold" fill="{WHITE}" text-anchor="middle" letter-spacing="2">{_esc(c["title"])}{tm}</text>')
    parts.append(f'<text x="{W/2}" y="215" font-family="{SANS}" font-size="30" font-weight="bold" fill="{CREAM}" text-anchor="middle" letter-spacing="8">{_esc(c["tagline"])}</text>')
    parts.append(f'<text x="{W/2}" y="252" font-family="{SANS}" font-size="22" font-weight="bold" fill="{GOLD}" text-anchor="middle" letter-spacing="2">{_esc(c["subtitle"])}</text>')

    # ── 4 step panels ──
    top, bot = 300, 1300
    pad = 40
    pw = (W - pad * 5) / 4
    for i, st in enumerate(c["steps"][:4]):
        col = STEP_COLORS[i]
        x = pad + i * (pw + pad)
        parts.append(f'<rect x="{x}" y="{top}" width="{pw}" height="{bot-top}" rx="18" fill="#0E0C20" stroke="{col}" stroke-width="2.5"/>')
        # number badge
        cx = x + pw / 2
        parts.append(f'<circle cx="{cx}" cy="{top+55}" r="34" fill="none" stroke="{col}" stroke-width="3"/>')
        parts.append(f'<text x="{cx}" y="{top+68}" font-family="{SERIF}" font-size="40" font-weight="bold" fill="{col}" text-anchor="middle">{i+1}</text>')
        # heading
        hl = _wrap(st["heading"], 18)
        parts.append(_tspans(hl, cx, top + 130, 30, f'font-family="{SANS}" font-size="24" font-weight="bold" fill="{WHITE}" text-anchor="middle"'))
        # divider
        hy = top + 130 + len(hl) * 30 + 6
        parts.append(f'<line x1="{cx-40}" y1="{hy}" x2="{cx+40}" y2="{hy}" stroke="{col}" stroke-width="2"/>')
        # art placeholder circle (decorative — composited AI art may replace later)
        ay = top + 340
        parts.append(f'<circle cx="{cx}" cy="{ay}" r="90" fill="{col}" opacity="0.14"/>')
        parts.append(f'<circle cx="{cx}" cy="{ay}" r="90" fill="none" stroke="{col}" stroke-width="1.5" opacity="0.5"/>')
        parts.append(f'<text x="{cx}" y="{ay+14}" font-family="{SERIF}" font-size="46" font-weight="bold" fill="{col}" text-anchor="middle">{i+1}</text>')
        # body
        bl = _wrap(st["body"], 26)
        parts.append(_tspans(bl, cx, ay + 150, 26, f'font-family="{SANS}" font-size="19" fill="{CREAM}" text-anchor="middle"'))
        # outcome chip
        oy = bot - 90
        parts.append(f'<rect x="{x+16}" y="{oy}" width="{pw-32}" height="62" rx="10" fill="none" stroke="{col}" stroke-width="2"/>')
        ol = _wrap(st["outcome"], 18)
        oty = oy + (34 if len(ol) == 1 else 24)
        parts.append(_tspans(ol, cx, oty, 24, f'font-family="{SANS}" font-size="20" font-weight="bold" fill="{col}" text-anchor="middle"'))
        # connector arrow
        if i < 3:
            axx = x + pw + pad / 2
            parts.append(f'<path d="M{axx-12},{top+330} L{axx+12},{top+345} L{axx-12},{top+360} Z" fill="{GOLD}"/>')

    # ── Mid band ──
    my = 1420
    parts.append(f'<text x="{W/2}" y="{my}" font-family="{SERIF}" font-size="120" font-weight="bold" fill="{GOLD}" text-anchor="middle" opacity="0.95">{_esc(c["mid_wordmark"])}</text>')
    parts.append(f'<text x="{W/2}" y="{my+55}" font-family="{SANS}" font-size="30" font-weight="bold" fill="{GOLD}" text-anchor="middle" letter-spacing="3">{_esc(c["mid_line"])}</text>')
    parts.append(f'<text x="120" y="{my-30}" font-family="{SERIF}" font-size="24" fill="{CREAM}">{_esc(c["mid_left"])}</text>')
    parts.append(f'<text x="{W-120}" y="{my-30}" font-family="{SERIF}" font-size="24" fill="{CREAM}" text-anchor="end">{_esc(c["mid_right"])}</text>')

    # ── Summary strip ──
    sy = 1560
    parts.append(f'<rect x="40" y="{sy}" width="{W-80}" height="230" rx="14" fill="#0E0C20" stroke="{GOLD}" stroke-width="1.5" opacity="0.9"/>')
    sw = (W - 80) / 4
    for i, s in enumerate(c["summary"][:4]):
        col = STEP_COLORS[i]
        sx = 40 + i * sw + 30
        parts.append(f'<circle cx="{sx+18}" cy="{sy+50}" r="20" fill="none" stroke="{col}" stroke-width="2.5"/>')
        parts.append(f'<text x="{sx+18}" y="{sy+58}" font-family="{SERIF}" font-size="22" font-weight="bold" fill="{col}" text-anchor="middle">{i+1}</text>')
        parts.append(f'<text x="{sx+52}" y="{sy+45}" font-family="{SANS}" font-size="24" font-weight="bold" fill="{col}">{_esc(s["label"])}</text>')
        tl = _wrap(s["text"], 22)
        parts.append(_tspans(tl, sx + 52, sy + 78, 24, f'font-family="{SANS}" font-size="18" fill="{CREAM}"'))
        if i < 3:
            parts.append(f'<path d="M{40 + (i+1)*sw - 18},{sy+42} L{40 + (i+1)*sw - 2},{sy+52} L{40 + (i+1)*sw - 18},{sy+62} Z" fill="{col}"/>')

    # ── Footer ──
    parts.append(f'<rect x="10" y="{H-90}" width="{W-20}" height="80" fill="{NAVY}"/>')
    parts.append(f'<text x="{W/2}" y="{H-42}" font-family="{SANS}" font-size="26" font-weight="bold" fill="{GOLD}" text-anchor="middle" letter-spacing="2">{_esc(c["footer"])}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


BUILDERS = {"process-formula-v1": _build_process_svg}
DEFAULTS = {"process-formula-v1": _default_process_content}


def _template(tid):
    return next((t for t in TEMPLATES if t["id"] == tid), None)


async def _resolve_kr(kr_id):
    """Look up a KR across the Refinement engine + legacy stores; return (found, externally_verified, version)."""
    if not kr_id:
        return None
    doc = await db.knowledge_engine_records.find_one({"id": kr_id}, {"_id": 0})
    if doc:
        return {"id": kr_id, "topic": doc.get("topic"), "version": doc.get("version", 1),
                "externally_verified": doc.get("verification", {}).get("evidence_sufficient_for_external_publication", False)}
    doc = await db.knowledge_records.find_one({"id": kr_id}, {"_id": 0})
    if doc:
        return {"id": kr_id, "topic": doc.get("title") or doc.get("topic"), "version": doc.get("version", 1),
                "externally_verified": bool(doc.get("verified_external"))}
    return None


def validate_poster(content, tmpl, png_w, png_h, kr_info, is_factual):
    """Deterministic Gold-Standard / Pre-Ship checks. Returns verdict + per-check detail."""
    checks = []

    def chk(name, ok, why=""):
        checks.append({"check": name, "passed": bool(ok), "detail": why,
                       "severity": "PASSED" if ok else "BLOCKING_FAILURE"})

    steps = content.get("steps", [])
    placeholder_tokens = ("lorem", "todo", "tbd", "xxx", "{{", "}}", "placeholder")
    all_text = " ".join([str(content.get("title", "")), str(content.get("subtitle", ""))] +
                         [f"{s.get('heading','')} {s.get('body','')} {s.get('outcome','')}" for s in steps]).lower()

    chk("Title present & clean", bool(content.get("title", "").strip()) and "\n" not in content.get("title", ""),
        content.get("title", ""))
    chk("Subtitle present", bool(content.get("subtitle", "").strip()))
    chk("All steps complete", len(steps) == tmpl["steps"] and all(s.get("heading") and s.get("body") and s.get("outcome") for s in steps),
        f"{len(steps)}/{tmpl['steps']} steps")
    chk("No placeholders / garbled text", not any(tok in all_text for tok in placeholder_tokens))
    chk("No markdown remnants", not any(m in all_text for m in ("**", "##", "](", "`")))
    chk("Correct dimensions", png_w == tmpl["dimensions"]["w"] and png_h == tmpl["dimensions"]["h"], f"{png_w}x{png_h}")
    chk("Print resolution", png_w >= 1500 and png_h >= 1500, f"{png_w}x{png_h}px")
    chk("Thumbnail readability (title scale)", len(content.get("title", "")) <= 40, f"{len(content.get('title',''))} chars")
    # Knowledge-First: factual posters require an externally-verified KR
    if is_factual:
        chk("Knowledge-First: verified source KR", bool(kr_info and kr_info.get("externally_verified")),
            "factual poster requires an externally-verified Knowledge Record")
    else:
        checks.append({"check": "Knowledge-First (conceptual poster)", "passed": True,
                       "detail": "No factual data — conceptual/brand content", "severity": "NOT_APPLICABLE"})

    blocked = any(c["severity"] == "BLOCKING_FAILURE" for c in checks)
    return {"verdict": "RETURN_TO_PRODUCTION" if blocked else "TREASURE_STANDARD_PASSED",
            "blocked": blocked, "checks": checks,
            "counts": {"passed": sum(1 for c in checks if c["passed"]),
                       "blocking": sum(1 for c in checks if c["severity"] == "BLOCKING_FAILURE"),
                       "total": len(checks)}}


async def generate_poster(template_id, content=None, kr_id=None, is_factual=False, actor="Founder"):
    tmpl = _template(template_id)
    if not tmpl:
        return {"error": f"Unknown template '{template_id}'."}
    builder = BUILDERS[template_id]
    c = {**DEFAULTS[template_id](), **(content or {})}
    if content and content.get("steps"):
        c["steps"] = content["steps"]

    kr_info = await _resolve_kr(kr_id)
    if kr_id and kr_info is None:
        return {"error": "Knowledge Record not found."}

    svg = builder(c)
    W, H = tmpl["dimensions"]["w"], tmpl["dimensions"]["h"]
    pid = gen_id()
    png_bytes = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=W, output_height=H)
    pdf_bytes = cairosvg.svg2pdf(bytestring=svg.encode("utf-8"))
    png_path = POSTER_DIR / f"{pid}.png"
    pdf_path = POSTER_DIR / f"{pid}.pdf"
    thumb_path = POSTER_DIR / f"{pid}_thumb.png"
    png_path.write_bytes(png_bytes)
    pdf_path.write_bytes(pdf_bytes)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=W // 4, output_height=H // 4, write_to=str(thumb_path))

    validation = validate_poster(c, tmpl, W, H, kr_info, is_factual)

    # Knowledge-First status gating — factual w/o verified KR is held at INTERNAL_DRAFT.
    if is_factual and not (kr_info and kr_info.get("externally_verified")):
        status = "VERIFICATION_REQUIRED"
    elif validation["blocked"]:
        status = "REVISION_REQUIRED"
    else:
        status = "DRAFT"  # rendered OK; Gold Standard requires explicit human approval (never auto)

    rec = {
        "id": pid, "template_id": template_id, "template_version": tmpl["version"],
        "family": tmpl["family"], "title": c.get("title"), "content": c,
        "is_factual": bool(is_factual),
        "kr_id": kr_id, "kr_version": (kr_info or {}).get("version"), "kr_topic": (kr_info or {}).get("topic"),
        "verification_status": ("VERIFIED_EXTERNAL" if (kr_info and kr_info.get("externally_verified"))
                                else ("PENDING_HUMAN_VERIFICATION" if is_factual else "NOT_APPLICABLE")),
        "treasure_status": validation["verdict"],
        "status": status,
        "dimensions": {"w": W, "h": H}, "resolution_px": f"{W}x{H}", "color_profile": "sRGB",
        "print_status": "PRINT_READY" if not validation["blocked"] else "BLOCKED",
        "publishing_status": "PUBLISHING_READY" if not validation["blocked"] else "BLOCKED",
        "files": [
            {"format": "png", "bytes": len(png_bytes), "w": W, "h": H},
            {"format": "pdf", "bytes": len(pdf_bytes), "vector": True},
            {"format": "thumb", "bytes": os.path.getsize(thumb_path), "w": W // 4, "h": H // 4},
        ],
        "provenance": {"template": template_id, "template_version": tmpl["version"],
                       "governing_standard": ps.DOC_ID, "tokens_version": ps.VERSION,
                       "renderer": "cairosvg", "generated_at": now_iso(), "by": actor},
        "validation": validation,
        "history": [{"status": status, "at": now_iso(), "by": actor}],
        "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.poster_assets.insert_one(dict(rec))
    rec.pop("_id", None)
    return _with_urls(rec)


def _with_urls(rec):
    pid = rec["id"]
    rec["png_url"] = f"/api/publishing/poster/{pid}/file?format=png"
    rec["pdf_url"] = f"/api/publishing/poster/{pid}/file?format=pdf"
    rec["thumb_url"] = f"/api/publishing/poster/{pid}/file?format=thumb"
    return rec


async def list_posters(limit=60):
    rows = [d async for d in db.poster_assets.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)]
    return [_with_urls(d) for d in rows]


async def get_poster(pid):
    d = await db.poster_assets.find_one({"id": pid}, {"_id": 0})
    return _with_urls(d) if d else None


def poster_file_path(rec, fmt):
    if fmt == "pdf":
        return POSTER_DIR / f"{rec['id']}.pdf"
    if fmt == "thumb":
        return POSTER_DIR / f"{rec['id']}_thumb.png"
    return POSTER_DIR / f"{rec['id']}.png"


async def set_poster_status(pid, new_status, actor="Founder", note=""):
    rec = await db.poster_assets.find_one({"id": pid}, {"_id": 0})
    if not rec:
        return None
    if new_status not in STATUS_MODEL:
        return {"error": f"Invalid status. Allowed: {STATUS_MODEL}"}
    # Gold Standard is never automatic — it requires verified source + passed validation + design approval.
    if new_status == "QRU_GOLD_STANDARD":
        if rec["validation"]["blocked"]:
            return {"error": "Cannot certify Gold Standard: Pre-Ship validation has blocking failures."}
        if rec.get("is_factual") and rec.get("verification_status") != "VERIFIED_EXTERNAL":
            return {"error": "Cannot certify Gold Standard: factual poster requires an externally-verified Knowledge Record."}
        if rec.get("status") != "DESIGN_APPROVED":
            return {"error": "A poster must be DESIGN_APPROVED before it can become QRU_GOLD_STANDARD."}
    entry = {"status": new_status, "at": now_iso(), "by": actor, "note": note}
    await db.poster_assets.update_one({"id": pid}, {"$set": {"status": new_status, "updated_at": now_iso()},
                                                    "$push": {"history": entry}})
    return await get_poster(pid)


def overview():
    return {"templates": TEMPLATES, "status_model": STATUS_MODEL,
            "note": "Templates control all text/data; AI art is composited only. Factual posters require a verified Knowledge Record™."}
