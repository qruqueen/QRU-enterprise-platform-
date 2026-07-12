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
    {"id": "data-comparison-v1", "family": "Data Comparison Poster", "version": "1.0",
     "dimensions": {"w": 1600, "h": 2000, "aspect": "4:5"}, "steps": 0, "factual": True,
     "purpose": "A governed comparison table of indicators across entities, with cited sources."},
    {"id": "scorecard-grid-v1", "family": "Scorecard Grid Poster", "version": "1.0",
     "dimensions": {"w": 1600, "h": 2000, "aspect": "4:5"}, "steps": 0, "factual": True,
     "purpose": "A grid of scorecards with grades and key metrics per entity."},
    {"id": "illustrated-learning-v1", "family": "Illustrated Learning Poster", "version": "1.0",
     "dimensions": {"w": 1600, "h": 2000, "aspect": "4:5"}, "steps": 0,
     "purpose": "A learning poster of concept cards; decorative art composited, all text machine-rendered."},
    {"id": "decoder-v1", "family": "Multi-Section Decoder Poster", "version": "1.0",
     "dimensions": {"w": 1600, "h": 2000, "aspect": "4:5"}, "steps": 0, "factual": True,
     "purpose": "Up to 10 numbered decoder sections with headline stats and citations."},
    {"id": "knowledge-card-v1", "family": "QRU Knowledge Card™", "version": "1.0",
     "dimensions": {"w": 1500, "h": 2143, "aspect": "7:10"}, "steps": 0, "factual": True,
     "purpose": "A governed single-term educational card: plain + professional definition, analogy, chart clue, real-life clues, challenge, memory sentence, category flow and tags."},
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


def _svg_open():
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="2000" viewBox="0 0 1600 2000">',
            f'<rect width="1600" height="2000" fill="{INK}"/>',
            f'<rect x="10" y="10" width="1580" height="1980" fill="none" stroke="{GOLD}" stroke-width="2" opacity="0.5"/>']


def _header(parts, c, W=1600):
    parts.append(_shield(70, 60, 110))
    parts.append(_seal(W - 150, 128, 86))
    tm = '<tspan font-size="30" dy="-24">\u2122</tspan>' if c.get("trademark") else ""
    parts.append(f'<text x="{W/2}" y="130" font-family="{SERIF}" font-size="72" font-weight="bold" fill="{WHITE}" text-anchor="middle" letter-spacing="1">{_esc(c["title"])}{tm}</text>')
    parts.append(f'<text x="{W/2}" y="185" font-family="{SANS}" font-size="26" font-weight="bold" fill="{GOLD}" text-anchor="middle" letter-spacing="2">{_esc(c.get("subtitle",""))}</text>')


def _footer(parts, text, W=1600, H=2000):
    parts.append(f'<rect x="10" y="{H-84}" width="{W-20}" height="74" fill="{NAVY}"/>')
    parts.append(f'<text x="{W/2}" y="{H-38}" font-family="{SANS}" font-size="24" font-weight="bold" fill="{GOLD}" text-anchor="middle" letter-spacing="1">{_esc(text)}</text>')


# ── Data Comparison Poster ──────────────────────────────────────────────────
def _default_data_comparison(topic="Global Financial Health"):
    return {"title": "FINANCIAL HEALTH CARD", "trademark": True, "subtitle": "SELECTED ECONOMIES · IMF, APRIL 2025",
            "columns": ["USA", "China", "Germany", "India", "Japan"],
            "rows": [
                {"label": "GDP (USD trn)", "values": ["30.3", "19.5", "4.9", "4.3", "4.4"]},
                {"label": "GDP Growth %", "values": ["2.7", "4.6", "0.8", "6.5", "1.1"]},
                {"label": "Inflation %", "values": ["3.0", "0.9", "2.4", "4.1", "2.4"]},
                {"label": "Unemployment %", "values": ["4.1", "5.1", "3.4", "7.8", "2.5"]},
                {"label": "Debt / GDP %", "values": ["122", "88", "63", "83", "251"]},
            ],
            "source_note": "Source: IMF World Economic Outlook, April 2025. Figures rounded; illustrative.",
            "footer": "READ THE NUMBERS. UNDERSTAND THE STORY."}


def _build_data_comparison_svg(c):
    parts = _svg_open(); _header(parts, c)
    cols = c["columns"]; rows = c["rows"]
    x0, y0 = 60, 300
    label_w = 420
    table_w = 1480 - label_w
    col_w = table_w / max(1, len(cols))
    rh = min(150, (1560 - y0) / max(1, (len(rows) + 1)))
    # header row
    parts.append(f'<rect x="{x0}" y="{y0}" width="1480" height="{rh}" fill="{NAVY}"/>')
    parts.append(f'<text x="{x0+20}" y="{y0+rh*0.62}" font-family="{SANS}" font-size="26" font-weight="bold" fill="{GOLD}">Indicator</text>')
    for j, col in enumerate(cols):
        cx = x0 + label_w + j * col_w + col_w / 2
        parts.append(f'<text x="{cx}" y="{y0+rh*0.62}" font-family="{SANS}" font-size="26" font-weight="bold" fill="{WHITE}" text-anchor="middle">{_esc(col)}</text>')
    # data rows
    for i, row in enumerate(rows):
        ry = y0 + rh * (i + 1)
        if i % 2 == 0:
            parts.append(f'<rect x="{x0}" y="{ry}" width="1480" height="{rh}" fill="#0E0C20"/>')
        parts.append(f'<text x="{x0+20}" y="{ry+rh*0.62}" font-family="{SANS}" font-size="24" font-weight="bold" fill="{CREAM}">{_esc(row["label"])}</text>')
        for j, val in enumerate(row["values"][:len(cols)]):
            cx = x0 + label_w + j * col_w + col_w / 2
            parts.append(f'<text x="{cx}" y="{ry+rh*0.62}" font-family="{SERIF}" font-size="30" font-weight="bold" fill="{GOLD}" text-anchor="middle">{_esc(val)}</text>')
    # grid lines
    parts.append(f'<rect x="{x0}" y="{y0}" width="1480" height="{rh*(len(rows)+1)}" fill="none" stroke="{GOLD}" stroke-width="1.5" opacity="0.5"/>')
    parts.append(f'<line x1="{x0+label_w}" y1="{y0}" x2="{x0+label_w}" y2="{y0+rh*(len(rows)+1)}" stroke="{GOLD}" stroke-width="1" opacity="0.4"/>')
    # source note
    for i, ln in enumerate(_wrap(c.get("source_note", ""), 90)):
        parts.append(f'<text x="{x0}" y="{1640 + i*30}" font-family="{SANS}" font-size="20" fill="{CREAM}" opacity="0.85">{_esc(ln)}</text>')
    _footer(parts, c.get("footer", "")); parts.append('</svg>'); return "\n".join(parts)


# ── Scorecard Grid Poster ───────────────────────────────────────────────────
def _default_scorecard(topic="Economic Scorecard"):
    return {"title": "GDP SCORECARD", "trademark": True, "subtitle": "TOP ECONOMIES · 2025 SNAPSHOT",
            "cards": [
                {"name": "United States", "grade": "A", "score": "30.3T", "metrics": [{"label": "Growth", "value": "2.7%"}, {"label": "Rank", "value": "#1"}]},
                {"name": "China", "grade": "A-", "score": "19.5T", "metrics": [{"label": "Growth", "value": "4.6%"}, {"label": "Rank", "value": "#2"}]},
                {"name": "Germany", "grade": "B+", "score": "4.9T", "metrics": [{"label": "Growth", "value": "0.8%"}, {"label": "Rank", "value": "#3"}]},
                {"name": "Japan", "grade": "B+", "score": "4.4T", "metrics": [{"label": "Growth", "value": "1.1%"}, {"label": "Rank", "value": "#4"}]},
                {"name": "India", "grade": "A", "score": "4.3T", "metrics": [{"label": "Growth", "value": "6.5%"}, {"label": "Rank", "value": "#5"}]},
                {"name": "UK", "grade": "B", "score": "3.7T", "metrics": [{"label": "Growth", "value": "1.2%"}, {"label": "Rank", "value": "#6"}]},
            ],
            "source_note": "Source: IMF WEO, April 2025. Nominal GDP (USD).",
            "footer": "SCORES TELL YOU WHERE. UNDERSTANDING TELLS YOU WHY."}


def _build_scorecard_svg(c):
    parts = _svg_open(); _header(parts, c)
    cards = c["cards"][:6]
    cols, x0, y0, gap = 2, 60, 300, 30
    cw = (1480 - gap) / cols
    ch = 380
    for i, card in enumerate(cards):
        r, cc = divmod(i, cols)
        x = x0 + cc * (cw + gap); y = y0 + r * (ch + gap)
        col = STEP_COLORS[i % len(STEP_COLORS)]
        parts.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="16" fill="#0E0C20" stroke="{col}" stroke-width="2.5"/>')
        parts.append(f'<text x="{x+30}" y="{y+60}" font-family="{SANS}" font-size="30" font-weight="bold" fill="{WHITE}">{_esc(card["name"])}</text>')
        parts.append(f'<circle cx="{x+cw-70}" cy="{y+60}" r="42" fill="none" stroke="{col}" stroke-width="3"/>')
        parts.append(f'<text x="{x+cw-70}" y="{y+74}" font-family="{SERIF}" font-size="40" font-weight="bold" fill="{col}" text-anchor="middle">{_esc(card["grade"])}</text>')
        parts.append(f'<text x="{x+30}" y="{y+180}" font-family="{SERIF}" font-size="72" font-weight="bold" fill="{GOLD}">{_esc(card["score"])}</text>')
        for j, m in enumerate(card.get("metrics", [])[:2]):
            my = y + 250 + j * 50
            parts.append(f'<text x="{x+30}" y="{my}" font-family="{SANS}" font-size="24" fill="{CREAM}">{_esc(m["label"])}</text>')
            parts.append(f'<text x="{x+cw-30}" y="{my}" font-family="{SANS}" font-size="24" font-weight="bold" fill="{col}" text-anchor="end">{_esc(m["value"])}</text>')
    parts.append(f'<text x="{x0}" y="1650" font-family="{SANS}" font-size="20" fill="{CREAM}" opacity="0.85">{_esc(c.get("source_note",""))}</text>')
    _footer(parts, c.get("footer", "")); parts.append('</svg>'); return "\n".join(parts)


# ── Illustrated Learning Poster ─────────────────────────────────────────────
def _default_illustrated(topic="Welcome to QRU"):
    return {"title": "WELCOME TO QRU", "trademark": True, "subtitle": "WHERE CURIOSITY BECOMES UNDERSTANDING",
            "lesson_points": [
                {"heading": "Ask Better Questions", "body": "Every discovery starts with genuine curiosity about how things really work."},
                {"heading": "Connect the Dots", "body": "Understanding grows when you link new ideas to what you already know."},
                {"heading": "See the System", "body": "Nothing exists in isolation — learn to see the bigger picture."},
                {"heading": "Think, Don't Memorize", "body": "We teach you how to think, not what to think."},
                {"heading": "Grow With Others", "body": "Shared understanding builds stronger families and communities."},
                {"heading": "Leave Transformed", "body": "You'll see the world — and yourself — differently."},
            ],
            "footer": "CURIOSITY STARTS THE JOURNEY. UNDERSTANDING CHANGES EVERYTHING."}


def _build_illustrated_svg(c):
    parts = _svg_open(); _header(parts, c)
    pts = c["lesson_points"][:6]
    cols, x0, y0, gap = 2, 60, 300, 30
    cw = (1480 - gap) / cols; ch = 370
    for i, pt in enumerate(pts):
        r, cc = divmod(i, cols)
        x = x0 + cc * (cw + gap); y = y0 + r * (ch + gap)
        col = STEP_COLORS[i % len(STEP_COLORS)]
        parts.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="18" fill="#0E0C20" stroke="{col}" stroke-width="2"/>')
        cx = x + 90
        parts.append(f'<circle cx="{cx}" cy="{y+90}" r="52" fill="{col}" opacity="0.15"/>')
        parts.append(f'<circle cx="{cx}" cy="{y+90}" r="52" fill="none" stroke="{col}" stroke-width="2"/>')
        parts.append(f'<text x="{cx}" y="{y+106}" font-family="{SERIF}" font-size="44" font-weight="bold" fill="{col}" text-anchor="middle">{i+1}</text>')
        for k, ln in enumerate(_wrap(pt["heading"], 22)):
            parts.append(f'<text x="{x+170}" y="{y+70 + k*32}" font-family="{SANS}" font-size="27" font-weight="bold" fill="{WHITE}">{_esc(ln)}</text>')
        for k, ln in enumerate(_wrap(pt["body"], 34)):
            parts.append(f'<text x="{x+30}" y="{y+200 + k*30}" font-family="{SANS}" font-size="20" fill="{CREAM}">{_esc(ln)}</text>')
    _footer(parts, c.get("footer", "")); parts.append('</svg>'); return "\n".join(parts)


# ── Multi-Section Decoder Poster ────────────────────────────────────────────
def _default_decoder(topic="Alzheimer's Decoder"):
    return {"title": "THE ALZHEIMER'S DECODER", "trademark": True, "subtitle": "10 THINGS EVERYONE SHOULD UNDERSTAND",
            "sections": [
                {"heading": "It's a disease, not aging", "body": "Alzheimer's is a specific brain disease, not a normal part of getting older.", "stat": "#1 cause of dementia"},
                {"heading": "Plaques and tangles", "body": "Abnormal proteins build up and disrupt how brain cells communicate.", "stat": ""},
                {"heading": "Memory first", "body": "Recent memory is usually affected earliest as the hippocampus is hit.", "stat": ""},
                {"heading": "It progresses", "body": "Symptoms worsen over years, from mild forgetfulness to full dependence.", "stat": ""},
                {"heading": "Risk rises with age", "body": "Age is the biggest risk factor, but it is not inevitable.", "stat": "~1 in 9 over 65"},
                {"heading": "Genes matter, partly", "body": "Some genes raise risk, but lifestyle and health also play a role.", "stat": ""},
                {"heading": "Brain-healthy habits help", "body": "Exercise, sleep, learning and social ties support brain resilience.", "stat": ""},
                {"heading": "Early detection counts", "body": "Earlier diagnosis opens more options for care and planning.", "stat": ""},
                {"heading": "Caregivers need support", "body": "Care is demanding — support and respite protect caregiver health.", "stat": ""},
                {"heading": "Research is advancing", "body": "New treatments and tests are emerging; understanding drives progress.", "stat": ""},
            ],
            "source_note": "Source: Alzheimer's Association, 2024. Educational summary; not medical advice.",
            "footer": "KNOW THE SIGNS. UNDERSTAND THE SCIENCE."}


def _build_decoder_svg(c):
    parts = _svg_open(); _header(parts, c)
    secs = c["sections"][:10]
    cols, x0, y0, gap = 2, 60, 290, 20
    cw = (1480 - gap) / cols
    rows = (len(secs) + 1) // 2
    ch = min(250, (1600 - y0 - gap * rows) / max(1, rows))
    for i, s in enumerate(secs):
        r, cc = divmod(i, cols)
        x = x0 + cc * (cw + gap); y = y0 + r * (ch + gap)
        col = STEP_COLORS[i % len(STEP_COLORS)]
        parts.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="12" fill="#0E0C20" stroke="{col}" stroke-width="2"/>')
        parts.append(f'<circle cx="{x+40}" cy="{y+40}" r="26" fill="{col}"/>')
        parts.append(f'<text x="{x+40}" y="{y+50}" font-family="{SERIF}" font-size="28" font-weight="bold" fill="{INK}" text-anchor="middle">{i+1}</text>')
        for k, ln in enumerate(_wrap(s["heading"], 30)):
            parts.append(f'<text x="{x+80}" y="{y+38 + k*28}" font-family="{SANS}" font-size="23" font-weight="bold" fill="{WHITE}">{_esc(ln)}</text>')
        for k, ln in enumerate(_wrap(s["body"], 42)[:3]):
            parts.append(f'<text x="{x+24}" y="{y+108 + k*28}" font-family="{SANS}" font-size="18" fill="{CREAM}">{_esc(ln)}</text>')
        if s.get("stat"):
            parts.append(f'<text x="{x+cw-24}" y="{y+ch-20}" font-family="{SANS}" font-size="20" font-weight="bold" fill="{GOLD}" text-anchor="end">{_esc(s["stat"])}</text>')
    parts.append(f'<text x="{x0}" y="1655" font-family="{SANS}" font-size="19" fill="{CREAM}" opacity="0.85">{_esc(c.get("source_note",""))}</text>')
    _footer(parts, c.get("footer", "")); parts.append('</svg>'); return "\n".join(parts)


BUILDERS.update({
    "data-comparison-v1": _build_data_comparison_svg,
    "scorecard-grid-v1": _build_scorecard_svg,
    "illustrated-learning-v1": _build_illustrated_svg,
    "decoder-v1": _build_decoder_svg,
})


# ── QRU Knowledge Card™ (light theme, single-term educational card) ──────────
CARD_PAGE = "#FBFAF5"
CARD_NAVY = "#241A54"
CARD_GREEN = "#2E7D32"
CARD_PURPLE = "#4A2E8F"


def _default_knowledge_card(topic="Support"):
    return {"card_number": "004", "card_kind": "QRU KNOWLEDGE CARD", "trademark": True,
            "series": "UNIVERSAL LANGUAGE OF UNDERSTANDING\u2122",
            "term": "SUPPORT", "term_tagline": "A price level where buying interest is strong enough to prevent price from falling further.",
            "plain_definition": "Support is a level where the price usually stops falling and bounces up because buyers step in.",
            "professional_definition": "Support is a price area on a chart where demand overcomes supply, causing downward movement to pause or reverse. It is identified by repeated reactions at or near the same level.",
            "analogy_title": "The Floor",
            "analogy_body": "When price falls to the floor, buyers step in and push it back up \u2014 just like the floor holds the weight.",
            "analogy_caption": "Buyers create the floor. That floor is support.",
            "chart_clue": ["Price drops to a level and bounces up", "Multiple touches of the same area",
                           "Wicks (shadows) below the level", "Volume may increase on the bounce", "The level holds \u2014 at least for now"],
            "real_life_clues": ["A price many investors think is a good deal", "A price customers refuse to pay less than",
                                "The bottom of a range in real estate", "A law or rule that protects people", "A promise that builds trust"],
            "challenge_intro": "Open a chart and find one strong support level.",
            "challenge_questions": ["Where did price bounce?", "How many times did it bounce there?",
                                    "What happened when price broke below it?", "Would you call it strong or weak support? Why?"],
            "memory_sentence": "Support is where buyers say, \u2018Not any lower.\u2019 They create the floor.",
            "category_flow": ["MARKET STRUCTURE", "SUPPLY & DEMAND", "PRICE ACTION"],
            "tags": ["Support", "PriceLevel", "Demand", "Buyers", "Bounce", "TechnicalAnalysis", "Beginner", "Investing"],
            "footer_left": "Understanding builds clarity. Clarity creates confidence.",
            "footer_right": "THINK. UNDERSTAND. TRANSFORM."}


def _card_box(parts, x, y, w, h, fill="#FFFFFF", stroke="#E0D9C4", rx=14):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')


def _card_pill(parts, x, y, w, label, dot_color):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="46" rx="23" fill="{CARD_NAVY}"/>')
    parts.append(f'<circle cx="{x+30}" cy="{y+23}" r="15" fill="{dot_color}"/>')
    parts.append(f'<text x="{x+58}" y="{y+31}" font-family="{SANS}" font-size="21" font-weight="bold" fill="#FFFFFF" letter-spacing="1">{_esc(label)}</text>')


def _build_knowledge_card_svg(c):
    W, H = 1500, 2143
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    p.append(f'<rect width="{W}" height="{H}" fill="{CARD_PAGE}"/>')
    p.append(f'<rect x="12" y="12" width="{W-24}" height="{H-24}" rx="20" fill="none" stroke="{GOLD}" stroke-width="3"/>')

    # Header
    p.append(_shield(50, 40, 130, GOLD))
    p.append(f'<text x="230" y="105" font-family="{SERIF}" font-size="58" font-weight="bold" fill="{CARD_NAVY}">{_esc(c["card_kind"])}<tspan font-size="26" dy="-24">\u2122</tspan></text>')
    p.append(f'<text x="232" y="150" font-family="{SANS}" font-size="24" font-weight="bold" fill="{GOLD}" letter-spacing="1">{_esc(c["series"])}</text>')
    p.append(f'<rect x="{W-250}" y="45" width="205" height="120" rx="14" fill="{CARD_NAVY}"/>')
    p.append(f'<text x="{W-147}" y="95" font-family="{SANS}" font-size="26" font-weight="bold" fill="#FFFFFF" text-anchor="middle">CARD</text>')
    p.append(f'<text x="{W-147}" y="145" font-family="{SERIF}" font-size="46" font-weight="bold" fill="{GOLD}" text-anchor="middle">#{_esc(c["card_number"])}</text>')

    # Title band
    ty = 195
    p.append(f'<rect x="40" y="{ty}" width="{W-80}" height="200" rx="16" fill="{CARD_NAVY}"/>')
    p.append(f'<text x="{W/2}" y="{ty+90}" font-family="{SERIF}" font-size="90" font-weight="bold" fill="#FFFFFF" text-anchor="middle" letter-spacing="2">{_esc(c["term"])}</text>')
    for i, ln in enumerate(_wrap(c["term_tagline"], 66)):
        p.append(f'<text x="{W/2}" y="{ty+135 + i*32}" font-family="{SANS}" font-size="23" font-style="italic" fill="{CREAM}" text-anchor="middle">{_esc(ln)}</text>')

    # Two definitions
    dy = 425
    bw = (W - 100) / 2
    for i, (label, key, dot) in enumerate([("PLAIN-LANGUAGE DEFINITION", "plain_definition", CARD_PURPLE),
                                           ("PROFESSIONAL DEFINITION", "professional_definition", CARD_NAVY)]):
        x = 40 + i * (bw + 20)
        _card_box(p, x, dy, bw, 300)
        _card_pill(p, x + 20, dy + 18, bw - 40, label, dot)
        for k, ln in enumerate(_wrap(c[key], 44)):
            p.append(f'<text x="{x+30}" y="{dy+100 + k*30}" font-family="{SANS}" font-size="22" fill="#2A2540">{_esc(ln)}</text>')

    # Three middle boxes: analogy | chart clue | real-life clues
    my = 750
    cw = (W - 120) / 3
    # Analogy
    _card_box(p, 40, my, cw, 560)
    _card_pill(p, 60, my + 18, cw - 40, "TODAY'S ANALOGY", GOLD)
    p.append(f'<text x="{40+cw/2}" y="{my+100}" font-family="{SERIF}" font-size="26" font-weight="bold" fill="{CARD_GREEN}" text-anchor="middle">{_esc(c["analogy_title"])}</text>')
    for k, ln in enumerate(_wrap(c["analogy_body"], 30)):
        p.append(f'<text x="{60}" y="{my+150 + k*28}" font-family="{SANS}" font-size="20" fill="#2A2540">{_esc(ln)}</text>')
    p.append(f'<rect x="60" y="{my+430}" width="{cw-40}" height="100" rx="10" fill="#FBF3D9"/>')
    for k, ln in enumerate(_wrap(c["analogy_caption"], 30)):
        p.append(f'<text x="{40+cw/2}" y="{my+470 + k*26}" font-family="{SANS}" font-size="19" font-weight="bold" fill="{CARD_NAVY}" text-anchor="middle">{_esc(ln)}</text>')
    # Chart clue
    x2 = 60 + cw
    _card_box(p, x2, my, cw, 560)
    _card_pill(p, x2 + 20, my + 18, cw - 40, "TODAY'S CHART CLUE", CARD_GREEN)
    for k, item in enumerate(c["chart_clue"][:6]):
        iy = my + 100 + k * 66
        p.append(f'<circle cx="{x2+38}" cy="{iy-6}" r="11" fill="{CARD_GREEN}"/>')
        p.append(f'<text x="{x2+38}" y="{iy}" font-family="{SANS}" font-size="16" fill="#FFF" text-anchor="middle">\u2713</text>')
        for j, ln in enumerate(_wrap(item, 26)):
            p.append(f'<text x="{x2+58}" y="{iy + j*24}" font-family="{SANS}" font-size="19" fill="#2A2540">{_esc(ln)}</text>')
    # Real-life clues
    x3 = 80 + 2 * cw
    _card_box(p, x3, my, cw, 560)
    _card_pill(p, x3 + 20, my + 18, cw - 40, "REAL-LIFE CLUES", GOLD)
    for k, item in enumerate(c["real_life_clues"][:5]):
        iy = my + 100 + k * 88
        p.append(f'<circle cx="{x3+38}" cy="{iy-6}" r="16" fill="{CARD_GREEN}"/>')
        for j, ln in enumerate(_wrap(item, 24)):
            p.append(f'<text x="{x3+66}" y="{iy + j*24}" font-family="{SANS}" font-size="18" fill="#2A2540">{_esc(ln)}</text>')

    # Challenge + Memory
    ch = 1340
    _card_box(p, 40, ch, cw * 1.5 + 10, 380)
    _card_pill(p, 60, ch + 18, cw * 1.5 - 30, "TODAY'S CHALLENGE", CARD_PURPLE)
    p.append(f'<text x="60" y="{ch+95}" font-family="{SANS}" font-size="20" fill="#2A2540">{_esc(c["challenge_intro"])}</text>')
    for k, q in enumerate(c["challenge_questions"][:4]):
        qy = ch + 140 + k * 52
        p.append(f'<circle cx="{78}" cy="{qy-6}" r="15" fill="{CARD_NAVY}"/>')
        p.append(f'<text x="78" y="{qy}" font-family="{SERIF}" font-size="18" font-weight="bold" fill="#FFF" text-anchor="middle">{k+1}</text>')
        p.append(f'<text x="104" y="{qy}" font-family="{SANS}" font-size="19" fill="#2A2540">{_esc(_wrap(q, 40)[0])}</text>')
    xm = 60 + cw * 1.5 + 10
    mw = W - 40 - xm
    _card_box(p, xm, ch, mw, 380)
    _card_pill(p, xm + 20, ch + 18, mw - 40, "MEMORY SENTENCE", GOLD)
    for k, ln in enumerate(_wrap(c["memory_sentence"], 26)):
        p.append(f'<text x="{xm+mw/2}" y="{ch+140 + k*38}" font-family="{SERIF}" font-size="26" font-weight="bold" fill="{CARD_NAVY}" text-anchor="middle">{_esc(ln)}</text>')

    # Category flow + tags
    fy = 1750
    _card_box(p, 40, fy, W - 80, 210, fill="#FFFFFF")
    p.append(f'<text x="70" y="{fy+45}" font-family="{SANS}" font-size="20" font-weight="bold" fill="{CARD_NAVY}">RELATED QRU CATEGORY</text>')
    flow_colors = [CARD_GREEN, CARD_NAVY, GOLD]
    fx = 70
    for i, cat in enumerate(c["category_flow"][:3]):
        w = 200
        p.append(f'<rect x="{fx}" y="{fy+65}" width="{w}" height="56" rx="8" fill="{flow_colors[i%3]}"/>')
        p.append(f'<text x="{fx+w/2}" y="{fy+100}" font-family="{SANS}" font-size="17" font-weight="bold" fill="#FFF" text-anchor="middle">{_esc(cat)}</text>')
        fx += w
        if i < len(c["category_flow"][:3]) - 1:
            p.append(f'<text x="{fx+16}" y="{fy+102}" font-family="{SANS}" font-size="26" fill="{CARD_NAVY}">\u2192</text>')
            fx += 44
    # tags
    tx, tline = 70, fy + 155
    for tag in c["tags"][:10]:
        tw = 24 + len(tag) * 11
        if tx + tw > W - 80:
            tx = 70; tline += 40
        p.append(f'<rect x="{tx}" y="{tline-24}" width="{tw}" height="32" rx="16" fill="none" stroke="{CARD_PURPLE}" stroke-width="1.5"/>')
        p.append(f'<text x="{tx+tw/2}" y="{tline-2}" font-family="{SANS}" font-size="16" fill="{CARD_PURPLE}" text-anchor="middle">{_esc(tag)}</text>')
        tx += tw + 12

    # Footer
    p.append(f'<rect x="12" y="{H-96}" width="{W-24}" height="84" rx="0" fill="{CARD_NAVY}"/>')
    p.append(_shield(40, H - 90, 62, GOLD))
    for k, ln in enumerate(_wrap(c["footer_left"], 48)[:2]):
        p.append(f'<text x="150" y="{H-58 + k*26}" font-family="{SANS}" font-size="19" fill="{CREAM}">{_esc(ln)}</text>')
    p.append(f'<text x="{W-50}" y="{H-45}" font-family="{SANS}" font-size="22" font-weight="bold" fill="{GOLD}" text-anchor="end">{_esc(c["footer_right"])}</text>')

    p.append('</svg>')
    return "\n".join(p)


BUILDERS["knowledge-card-v1"] = _build_knowledge_card_svg
DEFAULTS.update({
    "data-comparison-v1": _default_data_comparison,
    "scorecard-grid-v1": _default_scorecard,
    "illustrated-learning-v1": _default_illustrated,
    "decoder-v1": _default_decoder,
    "knowledge-card-v1": _default_knowledge_card,
})


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
    # Template-aware content items (steps / rows / cards / lesson_points / sections).
    item_key = next((k for k in ("steps", "rows", "cards", "lesson_points", "sections") if content.get(k)), None)
    items = content.get(item_key, []) if item_key else []
    item_text = " ".join(str(v) for it in items for v in (it.values() if isinstance(it, dict) else [it]))
    all_text = " ".join([str(content.get("title", "")), str(content.get("subtitle", "")), item_text]).lower()

    chk("Title present & clean", bool(content.get("title", "").strip()) and "\n" not in content.get("title", ""),
        content.get("title", ""))
    chk("Subtitle present", bool(content.get("subtitle", "").strip()))
    if tmpl["steps"] > 0:
        chk("All steps complete", len(steps) == tmpl["steps"] and all(s.get("heading") and s.get("body") and s.get("outcome") for s in steps),
            f"{len(steps)}/{tmpl['steps']} steps")
    else:
        chk("Content items present & complete", len(items) > 0 and all(isinstance(it, dict) and any(it.values()) for it in items),
            f"{len(items)} {item_key or 'items'}")
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
    is_factual = bool(is_factual or tmpl.get("factual"))
    builder = BUILDERS[template_id]
    c = {**DEFAULTS[template_id](), **(content or {})}
    for k in ("steps", "rows", "cards", "lesson_points", "sections"):
        if content and content.get(k):
            c[k] = content[k]

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
