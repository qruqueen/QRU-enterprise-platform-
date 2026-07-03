"""QRU Product Manufacturing Recipe™ Architecture.

A Recipe™ defines HOW a specific product type is laid out and rendered so that every
manufactured product looks intentional and customer-ready — a Poster does not look like
a Book, a Workbook does not look like a Presentation, a Quick Card does not look like a
Course.

This module is the single source of truth for:
  • the Recipe registry (product type → layout category, primary format, label)
  • recipe-aware, deterministic HTML rendering (distinct layout per category)
  • placeholder/internal-note guards so nothing draft-y reaches the customer

Fully deterministic — requires no LLM budget.
"""
import html as _html
import re as _re

import design_language as dl

# --------------------------------------------------------------------------- #
# 1. RECIPE REGISTRY — every product type maps to a layout category + primary format.
# --------------------------------------------------------------------------- #
# category: the visual/layout family used by the renderer
# primary : the downloadable primary customer format
# label   : the human name of the manufacturing recipe
RECIPES = {
    "Book":              {"category": "book",        "primary": "epub", "label": "QRU Book Recipe™"},
    "Course":            {"category": "book",        "primary": "epub", "label": "QRU Course Recipe™"},
    "Poster":            {"category": "poster",      "primary": "png",  "label": "QRU Poster Recipe™"},
    "Infographic":       {"category": "poster",      "primary": "png",  "label": "QRU Infographic Recipe™"},
    "Presentation":      {"category": "deck",        "primary": "pptx", "label": "QRU Presentation Recipe™"},
    "Teacher Guide":     {"category": "guide",       "primary": "pdf",  "label": "QRU Teacher Guide Recipe™"},
    "Caregiver Guide":   {"category": "guide",       "primary": "pdf",  "label": "QRU Caregiver Guide Recipe™"},
    "Student Guide":     {"category": "guide",       "primary": "pdf",  "label": "QRU Student Guide Recipe™"},
    "Family Guide":      {"category": "guide",       "primary": "pdf",  "label": "QRU Family Guide Recipe™"},
    "Lesson Plan":       {"category": "guide",       "primary": "pdf",  "label": "QRU Lesson Plan Recipe™"},
    "Printable PDF":     {"category": "guide",       "primary": "pdf",  "label": "QRU Printable Recipe™"},
    "Workbook":          {"category": "workbook",    "primary": "pdf",  "label": "QRU Workbook Recipe™"},
    "Flash Cards":       {"category": "card",        "primary": "pdf",  "label": "QRU Flash Cards Recipe™"},
    "Quick Card":        {"category": "card",        "primary": "pdf",  "label": "QRU Quick Card Recipe™"},
    "Quick Guide":       {"category": "card",        "primary": "pdf",  "label": "QRU Quick Guide Recipe™"},
    "Cheat Sheet":       {"category": "card",        "primary": "pdf",  "label": "QRU Cheat Sheet Recipe™"},
    "Quiz":              {"category": "quiz",        "primary": "html", "label": "QRU Quiz Recipe™"},
    "Interactive Lesson":{"category": "lesson",      "primary": "html", "label": "QRU Interactive Lesson Recipe™"},
    "AI Tutor":          {"category": "lesson",      "primary": "html", "label": "QRU AI Tutor Recipe™"},
    "Video Script":      {"category": "script",      "primary": "html", "label": "QRU Video Script Recipe™"},
    "Podcast Script":    {"category": "script",      "primary": "html", "label": "QRU Podcast Script Recipe™"},
    "Short-form Content":{"category": "script",      "primary": "html", "label": "QRU Short-form Recipe™"},
    "Certificate":       {"category": "certificate", "primary": "pdf",  "label": "QRU Certificate Recipe™"},
}

DEFAULT_RECIPE = {"category": "book", "primary": "pdf", "label": "QRU Document Recipe™"}

# Layout categories that are visually short/single-view (fewer sections expected).
COMPACT_CATEGORIES = {"poster", "card", "certificate"}


def get_recipe(product_type: str) -> dict:
    r = dict(RECIPES.get(product_type or "", DEFAULT_RECIPE))
    r["product_type"] = product_type
    r["category"] = r.get("category", "book")
    return r


def catalog() -> list:
    """Full recipe catalog for the UI."""
    out = []
    for ptype, r in RECIPES.items():
        out.append({"product_type": ptype, "category": r["category"],
                    "primary_format": r["primary"], "label": r["label"]})
    return sorted(out, key=lambda x: x["product_type"])


# --------------------------------------------------------------------------- #
# 2. PLACEHOLDER GUARD — strip draft/placeholder markers from customer content.
# --------------------------------------------------------------------------- #
_PLACEHOLDER_PATTERNS = [
    _re.compile(r"\{\{[^}]*\}\}"),                                              # {{ variable }}
    _re.compile(r"\[\s*(?:insert|todo|tbd|placeholder|add|your|xxx|example text|fill in)[^\]]*\]", _re.I),
    _re.compile(r"<\s*(?:insert|placeholder|todo|tbd)[^>]*>", _re.I),
    _re.compile(r"(?i)\blorem ipsum[^\n]*"),
]
_PLACEHOLDER_LINE = _re.compile(r"^\s*(?:TODO|TBD|PLACEHOLDER|XXX)\s*:?.*$", _re.I)


def strip_placeholders(content: str):
    """Return (clean, removed_count). Removes obvious placeholder tokens/lines so no
    draft artifacts reach the customer deliverable."""
    if not content:
        return content, 0
    removed = 0
    lines = []
    for line in content.split("\n"):
        if _PLACEHOLDER_LINE.match(line):
            removed += 1
            continue
        new = line
        for pat in _PLACEHOLDER_PATTERNS:
            new, n = pat.subn("", new)
            removed += n
        lines.append(new)
    text = "\n".join(lines)
    text = _re.sub(r"[ \t]{2,}", " ", text)
    text = _re.sub(r"\n{3,}", "\n\n", text).strip()
    return text, removed


# --------------------------------------------------------------------------- #
# 3. Minimal Markdown helpers (no external deps, no LLM).
# --------------------------------------------------------------------------- #
def _inline(esc: str) -> str:
    while "**" in esc:
        esc = esc.replace("**", "<strong>", 1)
        esc = esc.replace("**", "</strong>", 1) if "**" in esc else esc + "</strong>"
    esc = _re.sub(r"\*(.+?)\*", r"<em>\1</em>", esc)
    return esc


def _md_to_html(md: str) -> str:
    out, in_list = [], False
    for raw in (md or "").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            if in_list:
                out.append("</ul>"); in_list = False
            continue
        esc = _inline(_html.escape(line))
        if line.strip() in ("---", "***", "___"):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append("<hr/>"); continue
        if line.startswith("### "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<h3>{esc[4:]}</h3>")
        elif line.startswith("## "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<h2>{esc[3:]}</h2>")
        elif line.startswith("# "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<h1>{esc[2:]}</h1>")
        elif line.lstrip().startswith(("- ", "* ")):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{esc.lstrip()[2:]}</li>")
        else:
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<p>{esc}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _parse_sections(md: str):
    """Return (doc_title, [(heading, body_md), ...]) split on ## headings."""
    doc_title = None
    sections, cur_h, cur_b = [], None, []
    for line in (md or "").split("\n"):
        if line.startswith("# ") and doc_title is None and cur_h is None:
            doc_title = line[2:].strip(); continue
        if line.startswith("## "):
            if cur_h is not None:
                sections.append((cur_h, "\n".join(cur_b).strip()))
            cur_h, cur_b = line[3:].strip(), []
        elif line.startswith("# "):
            continue
        else:
            cur_b.append(line)
    if cur_h is not None:
        sections.append((cur_h, "\n".join(cur_b).strip()))
    if not sections:
        sections = [("Overview", (md or "").strip())]
    return doc_title, sections


def _bullets(body_md: str):
    """Extract list items / short lines as bullet points."""
    pts = []
    for line in (body_md or "").split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith(("- ", "* ")):
            pts.append(s[2:].strip())
        elif len(s) < 220 and not s.startswith("#"):
            pts.append(s)
    return pts


# --------------------------------------------------------------------------- #
# 4. Shared branded shell + per-category CSS.
# --------------------------------------------------------------------------- #
_BASE_CSS = """
*{box-sizing:border-box}
body{margin:0;font-family:Georgia,'Times New Roman',serif;color:#221A42;background:#f4f2f7;line-height:1.7}
.masthead{background:linear-gradient(135deg,var(--royal),var(--navy));color:#fff;padding:38px 32px}
.eyebrow{font-family:Arial,Helvetica,sans-serif;letter-spacing:.22em;text-transform:uppercase;font-size:11px;color:var(--gold);font-weight:700}
.masthead h1{margin:.35em 0 .1em;font-size:34px;line-height:1.15}
.meta{font-family:Arial,sans-serif;font-size:13px;opacity:.85}
.seal{display:inline-block;margin-top:14px;font-family:Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:.1em;color:var(--navy);background:var(--gold);padding:6px 12px;border-radius:999px}
.wrap{max-width:820px;margin:0 auto;padding:34px 26px 80px}
.cover{width:100%;max-width:400px;display:block;margin:0 auto 26px;border-radius:10px;box-shadow:0 18px 50px rgba(53,16,106,.28)}
h1,h2,h3{font-family:Arial,Helvetica,sans-serif;color:var(--royal)}
ul{padding-left:22px} li{margin:.35em 0}
hr{border:none;border-top:1px solid #e5e1ee;max-width:120px;margin:24px 0}
.footer{text-align:center;font-family:Arial,sans-serif;font-size:12px;color:#8a83a3;margin-top:40px}
.footer strong{color:var(--royal)}
.recipe-chip{font-family:Arial,sans-serif;font-size:10px;letter-spacing:.08em;color:var(--royal);background:#fff;border:1px solid var(--gold);padding:4px 10px;border-radius:999px;display:inline-block}
"""

# Per-category layout CSS — this is what makes each product type look distinct.
_CAT_CSS = {
    "book": """
.paper{background:#fff;border-radius:14px;padding:46px 52px;box-shadow:0 10px 40px rgba(34,26,66,.08)}
.paper h2{border-left:5px solid var(--accent);padding-left:14px;margin-top:2em;font-size:23px}
.paper h3{font-size:17px;color:var(--navy)} .paper p{font-size:16px}
""",
    "guide": """
.guide-step{background:#fff;border-radius:12px;padding:26px 30px;margin:18px 0;box-shadow:0 6px 22px rgba(34,26,66,.07);border-left:6px solid var(--accent)}
.guide-step .n{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;background:var(--royal);color:var(--gold);font-family:Arial;font-weight:700;font-size:16px;margin-right:12px}
.guide-step h2{display:inline;font-size:21px;vertical-align:middle}
.guide-note{background:#fff8e8;border:1px dashed var(--gold);border-radius:10px;padding:14px 18px;margin-top:14px;font-family:Arial,sans-serif;font-size:14px;color:var(--navy)}
""",
    "workbook": """
.ws{background:#fff;border-radius:12px;padding:24px 28px;margin:18px 0;box-shadow:0 6px 22px rgba(34,26,66,.07)}
.ws h2{font-size:20px;color:var(--royal);margin:0 0 4px}
.ws .tag{font-family:Arial;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:700}
.answerlines{margin-top:14px}
.answerlines .ln{border-bottom:1.5px solid #d8d2e6;height:26px;margin:12px 0}
.ws ul li{font-family:Georgia,serif}
""",
    "poster": """
body{background:linear-gradient(160deg,var(--royal),var(--navy))}
.wrap{max-width:900px}
.poster{background:#fff;border-radius:18px;padding:48px 44px;box-shadow:0 24px 70px rgba(0,0,0,.35);text-align:center}
.poster .big{font-family:Arial;font-size:40px;font-weight:800;color:var(--royal);line-height:1.05;margin:6px 0 4px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:26px;text-align:left}
.tile{border-radius:12px;padding:20px 22px;color:#fff;background:linear-gradient(135deg,var(--royal),var(--accent));box-shadow:0 8px 24px rgba(34,26,66,.18)}
.tile .k{font-family:Arial;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);font-weight:700}
.tile p{margin:6px 0 0;font-family:Arial,sans-serif;font-size:15px;line-height:1.45}
""",
    "card": """
.wrap{max-width:640px}
.qcard{background:#fff;border-radius:14px;padding:26px 30px;margin:14px 0;box-shadow:0 8px 26px rgba(34,26,66,.10);border-top:5px solid var(--accent)}
.qcard .front{font-family:Arial;font-size:18px;font-weight:800;color:var(--royal);margin-bottom:8px}
.qcard .back{font-size:15px;color:var(--navy)}
.qcard ul{margin:6px 0 0}
""",
    "deck": """
.slide{background:#fff;border-radius:12px;margin:16px 0;box-shadow:0 8px 26px rgba(34,26,66,.10);overflow:hidden}
.slide .bar{background:var(--royal);color:#fff;padding:14px 22px;display:flex;justify-content:space-between;align-items:center}
.slide .bar h2{margin:0;color:#fff;font-size:20px}
.slide .num{font-family:Arial;font-size:12px;color:var(--gold);font-weight:700}
.slide .body{padding:22px 26px;border-left:6px solid var(--accent)}
.slide .body li{font-size:16px}
""",
    "quiz": """
.q{background:#fff;border-radius:12px;padding:22px 26px;margin:14px 0;box-shadow:0 6px 22px rgba(34,26,66,.07)}
.q .qn{font-family:Arial;font-weight:800;color:var(--royal);font-size:17px}
.q .opt{border:1px solid #e2ddee;border-radius:8px;padding:10px 14px;margin:8px 0;font-family:Arial,sans-serif;font-size:15px}
""",
    "lesson": """
.step{background:#fff;border-radius:12px;padding:24px 28px;margin:16px 0;box-shadow:0 6px 22px rgba(34,26,66,.07);position:relative}
.step .badge{font-family:Arial;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#fff;background:var(--accent);padding:5px 12px;border-radius:999px;font-weight:700}
.step h2{margin:12px 0 6px;font-size:21px}
""",
    "script": """
.script{background:#fff;border-radius:12px;padding:30px 34px;box-shadow:0 10px 40px rgba(34,26,66,.08);font-family:'Courier New',monospace;color:#221A42}
.script .cue{color:var(--royal);font-weight:800;text-transform:uppercase;letter-spacing:.04em}
.script .dir{color:#8a6d1f;font-style:italic}
.script h2{font-family:Arial;color:var(--royal);border-bottom:2px solid var(--accent);padding-bottom:6px;margin-top:26px}
.script p{margin:.4em 0}
""",
    "certificate": """
body{background:linear-gradient(160deg,#efe9fb,#fff)}
.cert{background:#fff;border:3px solid var(--gold);border-radius:8px;padding:60px 50px;text-align:center;box-shadow:0 18px 60px rgba(53,16,106,.18);margin-top:20px}
.cert .rule{width:120px;height:3px;background:var(--gold);margin:18px auto}
.cert .name{font-family:Arial;font-size:34px;font-weight:800;color:var(--royal);margin:10px 0}
.cert p{font-size:16px;color:var(--navy)}
""",
}


def _shell(product, pal, recipe, body_html, extra_css):
    accent = "#%02X%02X%02X" % pal["accent"]
    title = _html.escape(product.get("title", "QRU Product"))
    ptype = _html.escape(product.get("product_type", ""))
    family = _html.escape(product.get("family", ""))
    code = _html.escape(product.get("product_code", ""))
    return (
        f"""<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title} — QRU PRESS™</title>
<style>:root{{--royal:#35106A;--gold:#F5B21A;--navy:#221A42;--accent:{accent};}}{_BASE_CSS}{extra_css}</style>
</head><body>
<header class="masthead">
  <div class="eyebrow">QRU PRESS™ · {family}</div>
  <h1>{title}</h1>
  <div class="meta">{ptype} · {code} · Customer Edition</div>
  <div class="seal">TREASURE STANDARD™ CERTIFIED</div>
  <div style="margin-top:12px"><span class="recipe-chip">{_html.escape(recipe['label'])}</span></div>
</header>
<div class="wrap">
{body_html}
  <div class="footer">Manufactured by <strong>QRU Factory™</strong> — Quest for Real Understanding.<br/>
  QRU simplifies the path to understanding the truth.</div>
</div>
</body></html>"""
    ).encode("utf-8")


# --------------------------------------------------------------------------- #
# 5. Per-category body builders — distinct layouts.
# --------------------------------------------------------------------------- #
def _b64_cover(cover_bytes):
    if not cover_bytes:
        return ""
    import base64
    b = base64.b64encode(cover_bytes).decode("ascii")
    return f'<img class="cover" src="data:image/png;base64,{b}" alt="cover"/>'


def _body_book(product, sections, cover_bytes):
    inner = _md_to_html(product.get("content") or "")
    return f'{_b64_cover(cover_bytes)}<article class="paper">{inner}</article>'


def _body_guide(product, sections, cover_bytes):
    blocks = []
    for i, (h, b) in enumerate(sections, 1):
        note = ""
        body = _md_to_html(b)
        blocks.append(
            f'<div class="guide-step"><span class="n">{i}</span><h2>{_html.escape(h)}</h2>'
            f'<div style="margin-top:12px">{body}</div>{note}</div>')
    return _b64_cover(cover_bytes) + "\n".join(blocks)


def _body_workbook(product, sections, cover_bytes):
    blocks = []
    for i, (h, b) in enumerate(sections, 1):
        pts = _bullets(b)
        items = "".join(f"<li>{_html.escape(p)}</li>" for p in pts[:8]) or _md_to_html(b)
        lines = '<div class="answerlines">' + "".join('<div class="ln"></div>' for _ in range(4)) + "</div>"
        blocks.append(
            f'<div class="ws"><div class="tag">Activity {i}</div><h2>{_html.escape(h)}</h2>'
            f'<ul>{items}</ul>{lines}</div>')
    return "\n".join(blocks)


def _body_poster(product, sections, cover_bytes):
    title = _html.escape(product.get("title", ""))
    tiles = []
    for h, b in sections[:6]:
        pts = _bullets(b)
        summary = _html.escape(pts[0]) if pts else ""
        tiles.append(f'<div class="tile"><div class="k">{_html.escape(h)}</div><p>{summary}</p></div>')
    return (f'<div class="poster"><div class="eyebrow" style="color:var(--accent)">{_html.escape(product.get("family",""))}</div>'
            f'<div class="big">{title}</div>'
            f'<div class="tiles">{"".join(tiles)}</div></div>')


def _body_card(product, sections, cover_bytes):
    cards = []
    for h, b in sections:
        pts = _bullets(b)
        items = "".join(f"<li>{_html.escape(p)}</li>" for p in pts[:5])
        back = f"<ul>{items}</ul>" if items else f'<div class="back">{_md_to_html(b)}</div>'
        cards.append(f'<div class="qcard"><div class="front">{_html.escape(h)}</div>{back}</div>')
    return "\n".join(cards)


def _body_deck(product, sections, cover_bytes):
    total = len(sections)
    slides = []
    for i, (h, b) in enumerate(sections, 1):
        pts = _bullets(b)
        items = "".join(f"<li>{_html.escape(p)}</li>" for p in pts[:8]) or _md_to_html(b)
        slides.append(
            f'<div class="slide"><div class="bar"><h2>{_html.escape(h)}</h2>'
            f'<span class="num">SLIDE {i}/{total}</span></div>'
            f'<div class="body"><ul>{items}</ul></div></div>')
    return "\n".join(slides)


def _body_quiz(product, sections, cover_bytes):
    blocks = []
    n = 0
    for h, b in sections:
        for line in b.split("\n"):
            s = line.strip()
            if not s:
                continue
            if s.startswith(("- ", "* ")):
                blocks.append(f'<div class="opt">{_html.escape(s[2:].strip())}</div>')
            elif s.endswith("?") or _re.match(r"^\d+[.)]", s):
                n += 1
                blocks.append(f'<div class="q"><div class="qn">{_html.escape(s)}</div>')
                blocks.append("__OPEN__")
    # close question wrappers cleanly
    htmlout, open_q = [], False
    for blk in blocks:
        if blk == "__OPEN__":
            open_q = True; continue
        if blk.startswith('<div class="q">'):
            if open_q:
                htmlout.append("</div>")
            htmlout.append(blk); open_q = True
        else:
            htmlout.append(blk)
    if open_q:
        htmlout.append("</div>")
    body = "".join(htmlout) if htmlout else _md_to_html(product.get("content") or "")
    return body


def _body_lesson(product, sections, cover_bytes):
    blocks = []
    for i, (h, b) in enumerate(sections, 1):
        blocks.append(
            f'<div class="step"><span class="badge">Step {i}</span><h2>{_html.escape(h)}</h2>'
            f'{_md_to_html(b)}</div>')
    return "\n".join(blocks)


def _body_script(product, sections, cover_bytes):
    lines_out = []
    for h, b in sections:
        lines_out.append(f"<h2>{_html.escape(h)}</h2>")
        for line in b.split("\n"):
            s = line.strip()
            if not s:
                continue
            m = _re.match(r"^([A-Z][A-Za-z0-9 .'\-]{0,28}):\s*(.*)$", s)
            if s.startswith("(") and s.endswith(")"):
                lines_out.append(f'<p class="dir">{_html.escape(s)}</p>')
            elif s.startswith(("[", "*(")) or _re.match(r"^\*[A-Z ]+\*$", s):
                lines_out.append(f'<p class="dir">{_html.escape(s.strip("*[]"))}</p>')
            elif m:
                lines_out.append(f'<p><span class="cue">{_html.escape(m.group(1))}:</span> {_html.escape(m.group(2))}</p>')
            else:
                lines_out.append(f"<p>{_html.escape(s)}</p>")
    return f'<div class="script">{"".join(lines_out)}</div>'


def _body_certificate(product, sections, cover_bytes):
    title = _html.escape(product.get("title", ""))
    body = _md_to_html(product.get("content") or "")
    return (f'<div class="cert"><div class="eyebrow" style="color:var(--accent)">Certificate of Understanding</div>'
            f'<div class="name">{title}</div><div class="rule"></div>{body}'
            f'<div class="rule"></div><p><strong>QRU PRESS™</strong> · Treasure Standard™ Certified</p></div>')


_BUILDERS = {
    "book": _body_book, "guide": _body_guide, "workbook": _body_workbook,
    "poster": _body_poster, "card": _body_card, "deck": _body_deck,
    "quiz": _body_quiz, "lesson": _body_lesson, "script": _body_script,
    "certificate": _body_certificate,
}


def render_html(product, cover_bytes=None) -> bytes:
    """Render the customer-ready HTML edition using the recipe for this product type."""
    recipe = get_recipe(product.get("product_type", ""))
    cat = recipe["category"]
    pal = dl.resolve_palette(product.get("family", ""),
                             product.get("department", product.get("college", "")),
                             product.get("topic", ""), product.get("title", ""))
    _, sections = _parse_sections(product.get("content") or "")
    builder = _BUILDERS.get(cat, _body_book)
    # Compact layouts do not embed the tall cover; text-flow layouts do.
    cb = None if cat in ("poster", "card", "deck", "quiz", "script", "certificate", "workbook") else cover_bytes
    body_html = builder(product, sections, cb)
    extra_css = _CAT_CSS.get(cat, _CAT_CSS["book"])
    return _shell(product, pal, recipe, body_html, extra_css)
