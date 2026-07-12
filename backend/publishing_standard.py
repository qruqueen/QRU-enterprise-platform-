"""QRU Enterprise Publishing & Presentation Standard™ (QRU-CON-0002, Version 1.0).

The single, governed source of truth for how EVERY customer-facing QRU product looks and reads —
books, workbooks, Knowledge Records, presentations, PDFs, web pages, courses, marketing and future
categories. Codifies typography, color, layout, the QRU Callout System™, the professional Table of
Contents standard, the Cover & Visual Identity Standard™, and the deterministic Treasure Standard™
Pre-Ship Validation Gate. Bound to the Governance Binding Layer so current and future generators
inherit it automatically (no manual redesign). Amendments create a new version — v1.0 is preserved.

Design tokens carry full governance metadata (purpose, allowed/prohibited use, product types,
accessibility, version, effective/superseded date, governing standard, approval status). A token may
render differently across CSS/PDF/DOCX/slides but MUST preserve the same semantic role.
"""
import re
from datetime import datetime, timezone

from database import db
from models import gen_id, now_iso

DOC_ID = "QRU-CON-0002"
VERSION = "1.0"
STATUS = "Founder Approved"
EFFECTIVE = "2026-07-12"

# ---------------------------------------------------------------- COLOR TOKENS
COLOR_TOKENS = [
    {"token": "color.ink.navy", "purpose": "Foundational brand ground & primary heading ink", "value": "#0B1B3F",
     "allowed_use": "Backgrounds, primary titles, spine", "prohibited_use": "Body text on dark grounds",
     "product_types": ["all"], "accessibility": "≥7:1 on white", "approval_status": "Approved"},
    {"token": "color.gold.treasure", "purpose": "Verified-excellence accent (QRU Gold)", "value": "#F5B21A",
     "allowed_use": "Accents, seals, dividers, key emphasis", "prohibited_use": "Long-form body text",
     "product_types": ["all"], "accessibility": "Use on navy only; not for small text on white", "approval_status": "Approved"},
    {"token": "color.royal.signature", "purpose": "Signature Royal Purple — used sparingly", "value": "#35106A",
     "allowed_use": "Signature panels, callout accents", "prohibited_use": "Dominant backgrounds",
     "product_types": ["all"], "accessibility": "≥7:1 with white text", "approval_status": "Approved"},
    {"token": "color.body.ink", "purpose": "Primary body text ink", "value": "#1A2233",
     "allowed_use": "Body copy, captions", "prohibited_use": "Titles on dark grounds",
     "product_types": ["all"], "accessibility": "≥12:1 on white", "approval_status": "Approved"},
    {"token": "color.canvas", "purpose": "Clarity canvas / page ground", "value": "#FFFFFF",
     "allowed_use": "Page background (print/digital)", "prohibited_use": "As text color on white",
     "product_types": ["all"], "accessibility": "n/a", "approval_status": "Approved"},
    {"token": "color.muted", "purpose": "Secondary / caption ink", "value": "#5B6472",
     "allowed_use": "Captions, footnotes, metadata", "prohibited_use": "Body at <11pt on tinted grounds",
     "product_types": ["all"], "accessibility": "≥4.5:1 on white", "approval_status": "Approved"},
]

# ---------------------------------------------------------------- TYPOGRAPHY HIERARCHY (13 levels)
FONT_HEADING = "Playfair Display"
FONT_BODY = "Manrope"
TYPO_TOKENS = [
    {"token": "type.title.primary", "role": "Primary Title", "font": FONT_HEADING, "size_pt": 42, "line": 1.05, "weight": 800, "tracking": "-0.5", "space_after_pt": 18},
    {"token": "type.subtitle", "role": "Subtitle", "font": FONT_BODY, "size_pt": 18, "line": 1.3, "weight": 500, "tracking": "0", "space_after_pt": 14},
    {"token": "type.chapter.title", "role": "Chapter Title", "font": FONT_HEADING, "size_pt": 30, "line": 1.1, "weight": 700, "tracking": "-0.25", "space_after_pt": 16},
    {"token": "type.section.heading", "role": "Section Heading", "font": FONT_HEADING, "size_pt": 22, "line": 1.15, "weight": 700, "tracking": "0", "space_after_pt": 10},
    {"token": "type.subheading", "role": "Subheading", "font": FONT_BODY, "size_pt": 16, "line": 1.2, "weight": 700, "tracking": "0", "space_after_pt": 8},
    {"token": "type.body", "role": "Body Text", "font": FONT_BODY, "size_pt": 11.5, "line": 1.55, "weight": 400, "tracking": "0", "space_after_pt": 10},
    {"token": "type.caption", "role": "Caption", "font": FONT_BODY, "size_pt": 9.5, "line": 1.35, "weight": 500, "tracking": "0.2", "space_after_pt": 6},
    {"token": "type.quote", "role": "Quote / Pull Quote", "font": FONT_HEADING, "size_pt": 18, "line": 1.4, "weight": 500, "tracking": "0", "space_after_pt": 12},
    {"token": "type.callout", "role": "Callout", "font": FONT_BODY, "size_pt": 11, "line": 1.45, "weight": 500, "tracking": "0", "space_after_pt": 8},
    {"token": "type.footnote", "role": "Footnote", "font": FONT_BODY, "size_pt": 8.5, "line": 1.3, "weight": 400, "tracking": "0", "space_after_pt": 4},
    {"token": "type.header", "role": "Running Header", "font": FONT_BODY, "size_pt": 8.5, "line": 1.2, "weight": 600, "tracking": "1.5", "space_after_pt": 0},
    {"token": "type.footer", "role": "Running Footer", "font": FONT_BODY, "size_pt": 8.5, "line": 1.2, "weight": 500, "tracking": "1.5", "space_after_pt": 0},
    {"token": "type.pagenumber", "role": "Page Number", "font": FONT_BODY, "size_pt": 9, "line": 1, "weight": 600, "tracking": "0", "space_after_pt": 0},
]

# ---------------------------------------------------------------- SPACING & LAYOUT
LAYOUT_TOKENS = {
    "page.trim": "6in x 9in (US Trade) — default book trim",
    "margin.top_in": 0.75, "margin.bottom_in": 0.75, "margin.outer_in": 0.6, "margin.gutter_in": 0.85,
    "line_length_chars": "55–75 (optimal ~66)", "baseline_grid_pt": 12,
    "paragraph.space_after_pt": 10, "paragraph.first_indent_in": 0.2,
    "widow_orphan_control": "Minimum 2 lines; never leave a single line stranded",
    "whitespace_rule": "Whitespace is comprehension — no wall-of-text, no oversized empty areas",
    "min_body_size_pt": 10.5, "min_caption_size_pt": 8.5,
}
DIVIDER_TOKENS = {
    "rule.section": "0.75pt gold hairline with 0.35in clearance",
    "ornament.chapter": "Centered gold diamond ornament between title and body",
    "spine.rule": "Gold vertical hairline framing the spine title",
}

# ---------------------------------------------------------------- QRU CALLOUT SYSTEM™ (10 types)
CALLOUTS = [
    {"id": "key_insight", "name": "Key Insight", "icon": "Lightbulb", "accent": "#F5B21A", "ground": "#FFF8E8", "border": "#E4A700"},
    {"id": "scientific_evidence", "name": "Scientific Evidence", "icon": "FlaskConical", "accent": "#2563EB", "ground": "#EEF3FF", "border": "#2563EB"},
    {"id": "historical_context", "name": "Historical Context", "icon": "Landmark", "accent": "#8B5E34", "ground": "#F7F0E8", "border": "#B07D4A"},
    {"id": "practical_application", "name": "Practical Application", "icon": "Wrench", "accent": "#059669", "ground": "#ECFDF5", "border": "#059669"},
    {"id": "common_misunderstanding", "name": "Common Misunderstanding", "icon": "AlertTriangle", "accent": "#DC2626", "ground": "#FEF2F2", "border": "#DC2626"},
    {"id": "qru_treasure", "name": "QRU Treasure", "icon": "Gem", "accent": "#35106A", "ground": "#F3EEFA", "border": "#35106A"},
    {"id": "reflection", "name": "Reflection", "icon": "MessageCircleQuestion", "accent": "#0891B2", "ground": "#ECFEFF", "border": "#0891B2"},
    {"id": "vocabulary", "name": "Vocabulary", "icon": "BookA", "accent": "#7C3AED", "ground": "#F5F3FF", "border": "#7C3AED"},
    {"id": "example", "name": "Example", "icon": "ListChecks", "accent": "#0B1B3F", "ground": "#F1F4F9", "border": "#0B1B3F"},
    {"id": "warning", "name": "Warning", "icon": "ShieldAlert", "accent": "#B45309", "ground": "#FFFBEB", "border": "#B45309"},
]

# ---------------------------------------------------------------- TABLE OF CONTENTS STANDARD
TOC_STANDARD = {
    "appearance": "Professionally typeset textbook contents page",
    "rules": [
        "Automatic page numbering with right-aligned numerals",
        "Dot leaders between title and page number",
        "No markdown syntax (#, *, -, backticks)",
        "No displayed hyperlinks, raw URLs or bracket notation",
        "No internal anchor references or slugs",
        "Consistent left alignment for titles; consistent right alignment for numbers",
        "Front-matter in roman numerals; body in arabic",
        "Two-level depth by default (Chapter → Section)",
    ],
}

# ---------------------------------------------------------------- COVER & VISUAL IDENTITY STANDARD™
COVER_STANDARD = {
    "philosophy": "The cover is the reader's first lesson — curiosity, discovery, credibility, luxury simplicity.",
    "requirements": [
        "Clear visual hierarchy", "Compelling title treatment", "Professional subtitle treatment",
        "Consistent QRU Press™ branding (Shield + Treasure Standard™ seal)", "Balanced whitespace",
        "Premium typography (Playfair Display + Manrope)", "Strong focal point / conceptual artwork",
        "Excellent thumbnail readability", "Excellent print readability", "Professional spine (when applicable)",
        "Professional back cover layout", "Barcode safe area + ISBN compatibility",
    ],
    "checklist": [
        "Would this compete visually with major publishers?", "Is the title readable at thumbnail size?",
        "Does the design reflect the quality of the content?", "Does the cover create curiosity?",
        "Does it feel timeless rather than trendy?", "Does it strengthen the QRU brand?",
        "Would someone proudly display it?",
    ],
    "series_consistency": ["Consistent logo placement", "Consistent title positioning", "Consistent typography",
                           "Consistent color philosophy", "Publisher marks", "Series identifiers", "Enough variation for individual identity"],
    "cover_states": ["DRAFT_CONCEPT", "UNDER_REVIEW", "REVISION_REQUIRED", "APPROVED_DESIGN", "GOLD_MASTER", "RETIRED_SUPERSEDED"],
    "trim_presets": {"us_trade_6x9": "6 x 9 in", "kdp_ebook": "1600 x 2560 px", "square_1x1": "2048 x 2048 px", "video_16x9": "1920 x 1080 px", "reel_9x16": "1080 x 1920 px"},
}

# Reference covers — classified as evidence of visual DIRECTION, NOT auto-approved Gold Standard.
REFERENCE_COVERS = [
    {"id": "ref-ai-survival-wrap", "name": "AI Survival Mini-Kit™ — Full Wrap", "classification": "Approved Reference",
     "url": "https://customer-assets.emergentagent.com/job_understanding-os/artifacts/80a91irs_0B337C3B-57AE-4989-9F39-1F4CF012490A.png",
     "retain": ["Navy+gold hierarchy", "Icon halo composition", "Back-cover 'What you'll learn' checklist", "Treasure Standard seal", "Barcode placement"],
     "avoid": ["Text crowding near spine", "Over-busy back cover"], "thumbnail_performance": "Strong", "series_value": "High"},
    {"id": "ref-ai-survival-front", "name": "AI Survival Mini-Kit™ — Front", "classification": "Inspiration",
     "url": "https://customer-assets.emergentagent.com/job_understanding-os/artifacts/uf4fu94p_D5106850-2739-4276-8CA7-50BDB3B20264.png",
     "retain": ["Bold stacked title", "Gold/white split", "Neural-brain focal artwork"],
     "avoid": ["Slight kerning drift on large title", "Contrast dip on purple body text"], "thumbnail_performance": "Strong", "series_value": "Medium"},
    {"id": "ref-forex-v1-wrap", "name": "QRU Forex Fundamentals™ V1 — Wrap", "classification": "Approved Reference",
     "url": "https://customer-assets.emergentagent.com/job_understanding-os/artifacts/v3cisz23_F3ED4E4F-E624-4656-97C9-5587E24D13AD.png",
     "retain": ["Lion crest QRU Shield", "Global currency artwork", "Spine 'VOLUME 1' band", "QR access panel"],
     "avoid": ["Deep navy back text contrast", "Seal duplication density"], "thumbnail_performance": "Strong", "series_value": "High"},
    {"id": "ref-forex-money-wrap", "name": "QRU Forex — Money Foundations™ Wrap", "classification": "Template Candidate",
     "url": "https://customer-assets.emergentagent.com/job_understanding-os/artifacts/bvjoffva_4D8F3C3B-CD70-4A19-A86B-417FD2433B3C.webp",
     "retain": ["White title panel for max contrast", "Feature icon row on back", "Student Edition band", "Manufactured-from-Verified-Knowledge footer"],
     "avoid": ["3D currency render can feel stocky", "Gold footer heaviness"], "thumbnail_performance": "Excellent", "series_value": "High"},
]

# ---------------------------------------------------------------- PILOT: THE SCIENCE OF UNDERSTANDING™
# Raw TOC deliberately carries the current defects (markdown, anchors, URLs, brackets) to demonstrate the fix.
PILOT = {
    "title": "The Science of Understanding",
    "subtitle": "What We Keep Mistaking for Understanding — and What It Actually Is",
    "series": "QRU Foundations™",
    "edition": "Consumer Edition",
    "author": "QRU Press™",
    "isbn": "979-8-9921234-2-5",
    "toc_raw": """## Table of Contents
- [Introduction: The Illusion of Knowing](#introduction-illusion) .......... 1
- **Chapter 1 — What Understanding Is Not** [see also](https://qru.world/ch1) .... 7
  - *1.1 Recognition Is Not Comprehension* ...... 9
  - 1.2 Fluency Is Not Understanding `#fluency` .... 14
- ## Chapter 2 — The Anatomy of a Real Idea .......... 21
  - 2.1 Structure Before Memory [ref] .... 23
- Chapter 3 — Manufacturing Understanding (#ch3-manufacturing) ... 34
- Conclusion: The Quiet Power of Knowing Why ....... 48""",
    "chapters": [
        {"number": 1, "title": "What Understanding Is Not",
         "quote": "To know the name of a thing is not to know the thing.",
         "objectives": ["Separate recognition from comprehension", "Detect the fluency illusion", "Name what real understanding requires"],
         "summary": "We routinely mistake familiarity for understanding. This chapter draws the line."},
    ],
}


# ---------------------------------------------------------------- TOC ENGINE
_MD_STRIP = [
    (r"`([^`]*)`", r"\1"), (r"\*\*([^*]+)\*\*", r"\1"), (r"\*([^*]+)\*", r"\1"),
    (r"_([^_]+)_", r"\1"), (r"\[([^\]]*)\]\([^)]*\)", r"\1"),  # [text](url) -> text
    (r"\[[^\]]*\]", ""),  # bare [ref]
    (r"\(#[^)]*\)", ""), (r"#\S+", ""),  # anchors/slugs
    (r"https?://\S+", ""),  # raw urls
]


def clean_toc_markdown(raw):
    """Turn a raw markdown/anchored TOC into clean, structured entries (title, level, page)."""
    entries = []
    for line in (raw or "").splitlines():
        s = line.rstrip()
        if not s.strip() or re.match(r"^\s*#{1,3}\s*table of contents", s, re.I):
            continue
        indent = len(s) - len(s.lstrip())
        level = 2 if indent >= 2 else 1
        # page number = trailing integer after dots/spaces
        page = None
        pm = re.search(r"[.\s]{2,}(\d{1,4})\s*$", s)
        if not pm:
            pm = re.search(r"\s(\d{1,4})\s*$", s)
        if pm:
            page = int(pm.group(1))
            s = s[:pm.start()]
        for pat, rep in _MD_STRIP:
            s = re.sub(pat, rep, s)
        s = re.sub(r"^\s*[#>\-*+]+\s*", "", s)  # leading markdown bullets/heading marks
        s = re.sub(r"\.{2,}", " ", s)  # stray dot leaders
        s = re.sub(r"\s+", " ", s).strip(" .-—")
        if len(s) >= 2:
            entries.append({"level": level, "title": s, "page": page})
    return entries


def render_toc_lines(entries, width=64):
    """Typeset lines with aligned dot leaders (used by text/PDF renderers)."""
    lines = []
    for e in entries:
        indent = "    " if e["level"] == 2 else ""
        title = f"{indent}{e['title']}"
        page = str(e["page"]) if e.get("page") is not None else ""
        dots = max(3, width - len(title) - len(page))
        lines.append(f"{title} {'.' * dots} {page}".rstrip())
    return lines


# ---------------------------------------------------------------- GOVERNED CSS (tokens → CSS)
def render_css():
    lines = [":root{"]
    for c in COLOR_TOKENS:
        lines.append(f"  --{c['token'].replace('.', '-')}: {c['value']};")
    lines.append(f"  --font-heading: '{FONT_HEADING}', Georgia, serif;")
    lines.append(f"  --font-body: '{FONT_BODY}', system-ui, sans-serif;")
    lines.append("}")
    lines.append(f".qru-doc{{font-family:var(--font-body);color:var(--color-body-ink);line-height:{LAYOUT_TOKENS['baseline_grid_pt']/11.5:.2f};max-width:40rem;}}")
    for t in TYPO_TOKENS:
        cls = "." + t["token"].replace(".", "-")
        fam = "var(--font-heading)" if t["font"] == FONT_HEADING else "var(--font-body)"
        lines.append(f"{cls}{{font-family:{fam};font-size:{t['size_pt']}pt;line-height:{t['line']};font-weight:{t['weight']};letter-spacing:{t['tracking']}px;margin:0 0 {t['space_after_pt']}pt;}}")
    for c in CALLOUTS:
        lines.append(f".qru-callout-{c['id']}{{background:{c['ground']};border-left:4px solid {c['border']};padding:12px 16px;border-radius:4px;margin:14px 0;color:var(--color-body-ink);}}")
    lines.append("@page{size:6in 9in;margin:0.75in 0.6in 0.75in 0.85in;}")
    return "\n".join(lines)


# ---------------------------------------------------------------- TREASURE STANDARD™ PRE-SHIP GATE
_PLACEHOLDER = re.compile(r"(lorem ipsum|TODO|TBD|\{\{[^}]+\}\}|\[insert[^\]]*\]|xxxx)", re.I)
_MD_REMNANT = re.compile(r"(^|\s)(#{1,6}\s|\*\*|```|- \[ \]|\]\()", re.M)
_RAW_URL = re.compile(r"https?://\S+")


def _rule(rid, name, category, module, status, where="", why="", correction=""):
    return {"rule_id": rid, "name": name, "category": category, "responsible_module": module,
            "status": status, "where": where, "why": why, "correction": correction,
            "reinspection_required": status == "BLOCKING_FAILURE"}


def preflight_validate(artifact):
    """Deterministic, auditable, BLOCKING pre-ship gate. Returns per-rule results + overall verdict."""
    a = artifact or {}
    body = " ".join(str(v) for v in [a.get("body_text", ""), a.get("body_html", "")] + [s.get("content", "") for s in a.get("sections", [])])
    results = []

    def add(*args, **kw):
        results.append(_rule(*args, **kw))

    # Markdown remnants
    add("PS-01", "Markdown remnants", "Content", "Deliverable Renderer",
        "BLOCKING_FAILURE" if _MD_REMNANT.search(body) else "PASSED",
        where="Body text", why="Raw markdown breaks professional typesetting.",
        correction="Render through the governed HTML/PDF pipeline (no raw markdown).")
    # Raw URLs / anchors / slugs
    urls = _RAW_URL.findall(body) + _RAW_URL.findall(" ".join(e.get("title", "") for e in a.get("toc_entries", [])))
    add("PS-02", "Raw URLs / anchors / slugs", "Content", "TOC Engine",
        "BLOCKING_FAILURE" if urls else "PASSED", where="TOC / body",
        why="Displayed URLs and slugs look self-published.", correction="Strip via clean_toc_markdown / link styling.")
    # TOC malformed / page refs
    toc = a.get("toc_entries", [])
    if not toc:
        add("PS-03", "Table of Contents present", "Structure", "TOC Engine", "WARNING",
            where="Front matter", why="A professional book needs a typeset contents page.",
            correction="Generate a governed TOC.")
    else:
        bad = [e for e in toc if not e.get("title") or re.search(r"[#`*\[\]]|https?://", e.get("title", ""))]
        missing_pages = [e for e in toc if e.get("page") in (None, "", 0)]
        add("PS-03", "TOC well-formed", "Structure", "TOC Engine",
            "BLOCKING_FAILURE" if bad else "PASSED", where="Contents page",
            why="TOC entries must be clean text with valid page numbers.", correction="Re-run TOC cleaner.")
        add("PS-04", "TOC page references", "Structure", "TOC Engine",
            "WARNING" if missing_pages else "PASSED", where="Contents page",
            why="Every entry should resolve to a page.", correction="Assign page numbers during pagination.")
    # Heading order (no jump >1 level)
    heads = a.get("heading_levels", [])
    jump = any(heads[i] - heads[i - 1] > 1 for i in range(1, len(heads)))
    add("PS-05", "Heading order", "Structure", "Design Intelligence",
        "WARNING" if jump else ("PASSED" if heads else "NOT_APPLICABLE"),
        where="Document outline", why="Skipped heading levels harm accessibility & hierarchy.",
        correction="Use sequential heading levels.")
    # Fonts
    unsupported = [f for f in a.get("fonts_used", []) if f not in (FONT_HEADING, FONT_BODY)]
    add("PS-06", "Approved fonts only", "Typography", "Publishing Standard",
        "BLOCKING_FAILURE" if unsupported else ("PASSED" if a.get("fonts_used") else "NOT_APPLICABLE"),
        where=f"Fonts: {unsupported}", why="Only QRU-approved fonts may ship.", correction="Substitute Playfair Display / Manrope.")
    # Min font size
    mn = a.get("min_font_pt")
    add("PS-07", "Minimum font size", "Accessibility", "Publishing Standard",
        "BLOCKING_FAILURE" if (mn is not None and mn < LAYOUT_TOKENS["min_caption_size_pt"]) else ("PASSED" if mn else "NOT_APPLICABLE"),
        where=f"min {mn}pt", why="Text below 8.5pt is not readable in print.", correction="Raise to ≥ standard.")
    # Contrast (declared pairs {fg,bg,ratio})
    lowc = [c for c in a.get("contrast_pairs", []) if c.get("ratio", 21) < 4.5]
    add("PS-08", "Text contrast", "Accessibility", "Design Intelligence",
        "BLOCKING_FAILURE" if lowc else ("PASSED" if a.get("contrast_pairs") else "NOT_APPLICABLE"),
        where=str(lowc), why="Contrast < 4.5:1 fails accessibility.", correction="Adjust to approved token pairs.")
    # Print margins
    m = a.get("margins_in", {})
    unsafe = any((m.get(k, 1) or 0) < 0.5 for k in m) if m else False
    add("PS-09", "Safe print margins", "Layout", "Publishing Standard",
        "BLOCKING_FAILURE" if unsafe else ("PASSED" if m else "NOT_APPLICABLE"),
        where=str(m), why="Margins < 0.5in risk trimming.", correction="Apply governed margin tokens.")
    # Images: alt + resolution
    imgs = a.get("images", [])
    no_alt = [i for i in imgs if not i.get("alt")]
    lowres = [i for i in imgs if (i.get("dpi") or 300) < 200 or (i.get("width", 9999) < 600)]
    add("PS-10", "Image alt text", "Accessibility", "Media",
        "WARNING" if no_alt else ("PASSED" if imgs else "NOT_APPLICABLE"),
        where=f"{len(no_alt)} image(s)", why="Alt text supports screen readers.", correction="Add descriptive alt text.")
    add("PS-11", "Image resolution", "Quality", "Media",
        "BLOCKING_FAILURE" if lowres else ("PASSED" if imgs else "NOT_APPLICABLE"),
        where=f"{len(lowres)} image(s)", why="Low-res images look unprofessional in print.", correction="Replace with ≥300dpi assets.")
    # Placeholders
    add("PS-12", "Unresolved placeholders", "Content", "Deliverable Renderer",
        "BLOCKING_FAILURE" if _PLACEHOLDER.search(body) else "PASSED", where="Body",
        why="Placeholder text must never ship.", correction="Resolve all placeholders.")
    # Metadata
    meta = a.get("metadata", {})
    need_meta = a.get("product_type") in (None, "book", "ebook", "workbook")
    missing_meta = [k for k in ("title", "author", "isbn") if not meta.get(k)] if need_meta else []
    add("PS-13", "Required metadata", "Metadata", "Publishing Standard",
        "WARNING" if missing_meta else "PASSED", where=str(missing_meta),
        why="Title/author/ISBN required for publishing.", correction="Complete product metadata.")
    # Approvals
    add("PS-14", "Human approval present", "Governance", "Governance Binding",
        "BLOCKING_FAILURE" if not a.get("approvals") else "PASSED", where="Approval log",
        why="Nothing ships without human approval (§9).", correction="Obtain founder/authorized approval.")
    # Unapproved AI assets
    bad_ai = [x for x in a.get("ai_assets", []) if x.get("approval_status") not in ("APPROVED_DESIGN", "GOLD_MASTER")]
    add("PS-15", "AI assets approved", "Governance", "Cover Studio",
        "BLOCKING_FAILURE" if bad_ai else ("PASSED" if a.get("ai_assets") else "NOT_APPLICABLE"),
        where=f"{len(bad_ai)} unapproved", why="AI-generated visuals need human approval before shipping.",
        correction="Route AI assets through the approval workflow.")
    # Design tokens current
    add("PS-16", "Design tokens current", "Governance", "Publishing Standard",
        "WARNING" if a.get("tokens_version") not in (None, VERSION) else "PASSED",
        where=f"tokens {a.get('tokens_version')}", why="Superseded tokens cause visual drift.",
        correction=f"Rebuild against Publishing Standard v{VERSION}.")
    # Cover thumbnail readability
    cov = a.get("cover", {})
    add("PS-17", "Cover thumbnail readability", "Cover", "Cover Studio",
        "BLOCKING_FAILURE" if (cov and cov.get("thumbnail_readable") is False) else ("PASSED" if cov else "NOT_APPLICABLE"),
        where="Cover", why="Title must be legible at thumbnail size.", correction="Increase title scale/contrast.")

    blocking = [r for r in results if r["status"] == "BLOCKING_FAILURE"]
    warnings = [r for r in results if r["status"] == "WARNING"]
    verdict = "RETURN_TO_PRODUCTION" if blocking else ("SHIP_WITH_ADVISORIES" if warnings else "TREASURE_STANDARD_PASSED")
    counts = {s: len([r for r in results if r["status"] == s]) for s in ("BLOCKING_FAILURE", "WARNING", "ADVISORY", "PASSED", "NOT_APPLICABLE")}
    return {"verdict": verdict, "blocked": bool(blocking), "counts": counts, "results": results,
            "governed_by": [f"{DOC_ID} §Pre-Ship Gate", "QRU-CON-0001 §9/§10"], "evaluated_at": now_iso()}


# ---------------------------------------------------------------- PILOT REGENERATION (before/after)
def regenerate_pilot():
    before_entries_note = "Raw source: markdown headings, [text](url) links, (#anchors), [ref] brackets, uneven dot leaders."
    cleaned = clean_toc_markdown(PILOT["toc_raw"])
    toc_lines = render_toc_lines(cleaned)
    ch = PILOT["chapters"][0]
    return {
        "title": PILOT["title"], "subtitle": PILOT["subtitle"], "series": PILOT["series"],
        "edition": PILOT["edition"], "author": PILOT["author"], "isbn": PILOT["isbn"],
        "toc_before_raw": PILOT["toc_raw"], "toc_before_note": before_entries_note,
        "toc_after_entries": cleaned, "toc_after_lines": toc_lines,
        "chapter_opening": {"number": ch["number"], "title": ch["title"], "quote": ch["quote"],
                            "objectives": ch["objectives"], "summary": ch["summary"]},
    }


def get_pilot_artifact(clean=True):
    """Build a preflight artifact for the pilot. clean=False seeds defects (for gate testing)."""
    reg = regenerate_pilot()
    if clean:
        return {
            "title": PILOT["title"], "product_type": "book",
            "body_text": "Understanding is not recognition. This chapter separates the two with clear examples.",
            "toc_entries": reg["toc_after_entries"], "heading_levels": [1, 2, 2, 1],
            "fonts_used": [FONT_HEADING, FONT_BODY], "min_font_pt": 10.5,
            "contrast_pairs": [{"fg": "#1A2233", "bg": "#FFFFFF", "ratio": 15.0}],
            "margins_in": {"top": 0.75, "bottom": 0.75, "outer": 0.6, "gutter": 0.85},
            "images": [{"alt": "Diagram of recognition vs comprehension", "dpi": 300, "width": 1600}],
            "metadata": {"title": PILOT["title"], "author": PILOT["author"], "isbn": PILOT["isbn"]},
            "approvals": [{"by": "Founder", "at": now_iso()}], "ai_assets": [],
            "tokens_version": VERSION, "cover": {"thumbnail_readable": True},
        }
    # Defective (as the current book shipped): markdown, raw url, low-res image no alt, placeholder, no approval, unapproved AI cover.
    return {
        "title": PILOT["title"], "product_type": "book",
        "body_text": "## Chapter 1\nUnderstanding is **not** recognition. See https://qru.world/ch1 . TODO: add example.",
        "toc_entries": [{"level": 1, "title": "Introduction [see](https://qru.world) #intro", "page": None}],
        "heading_levels": [1, 3], "fonts_used": ["Arial", FONT_BODY], "min_font_pt": 7.5,
        "contrast_pairs": [{"fg": "#8A8FA0", "bg": "#FFFFFF", "ratio": 2.1}],
        "margins_in": {"top": 0.3, "outer": 0.35, "gutter": 0.4},
        "images": [{"alt": "", "dpi": 96, "width": 320}],
        "metadata": {"title": PILOT["title"]}, "approvals": [],
        "ai_assets": [{"id": "c1", "approval_status": "DRAFT_CONCEPT"}],
        "tokens_version": "0.9", "cover": {"thumbnail_readable": False},
    }


# ---------------------------------------------------------------- STANDARD VIEW + SEED/BINDING
def standard_view():
    return {
        "doc_id": DOC_ID, "name": "QRU Enterprise Publishing & Presentation Standard™",
        "version": VERSION, "status": STATUS, "effective_date": EFFECTIVE, "authority": "Foundational",
        "scope": ["books", "ebooks", "workbooks", "knowledge_records", "knowledge_cards", "presentations",
                  "pdf_downloads", "web_pages", "wordpress", "courses", "video_slides", "infographics",
                  "study_guides", "assessments", "landing_pages", "marketing", "investor_docs", "reports",
                  "operating_manuals", "future_categories"],
        "philosophy": ["Professionalism", "Consistency", "Intentionality", "Trust", "Educational Excellence",
                       "Luxury Simplicity", "Understanding Before Decoration", "Visual Calm", "Readable Intelligence",
                       "Manufactured Understanding", "Every design decision must improve comprehension"],
        "typography": TYPO_TOKENS, "colors": COLOR_TOKENS, "layout": LAYOUT_TOKENS, "dividers": DIVIDER_TOKENS,
        "callouts": CALLOUTS, "toc_standard": TOC_STANDARD, "cover_standard": COVER_STANDARD,
        "reference_covers": REFERENCE_COVERS,
        "pre_ship_gate": {"severities": ["BLOCKING_FAILURE", "WARNING", "ADVISORY", "PASSED", "NOT_APPLICABLE"],
                          "rule_count": 17, "override_rule": "No workflow may override a BLOCKING_FAILURE without an authorized, audit-logged exception."},
        "governed_by": [DOC_ID, "QRU-CON-0001"],
    }


def design_tokens():
    return {"version": VERSION, "governing_standard": DOC_ID, "effective_date": EFFECTIVE,
            "typography": TYPO_TOKENS, "colors": COLOR_TOKENS, "layout": LAYOUT_TOKENS,
            "dividers": DIVIDER_TOKENS, "callouts": CALLOUTS,
            "token_metadata_fields": ["token", "purpose", "value", "allowed_use", "prohibited_use",
                                      "product_types", "accessibility", "version", "effective_date",
                                      "superseded_version", "governing_standard", "approval_status"]}


async def seed_publishing_standard():
    """Register QRU-CON-0002 (idempotent) in the constitution collection + QIKS Standards Registry, and bind."""
    existing = await db.factory_constitution.find_one({"doc_id": DOC_ID, "version": VERSION})
    if not existing:
        sv = standard_view()
        await db.factory_constitution.insert_one({
            "id": gen_id(), "doc_id": DOC_ID, "name": sv["name"], "version": VERSION, "status": STATUS,
            "authority_level": "Foundational", "effective_date": EFFECTIVE, "owner": "QRU Press™",
            "read_only": True, "standard": sv, "created_at": now_iso(), "updated_at": now_iso()})
    # QIKS registry entry (dedupe by standard_id)
    if not await db.qiks_standards.find_one({"standard_id": DOC_ID}):
        await db.qiks_standards.insert_one({
            "id": gen_id(), "standard_id": DOC_ID, "name": "QRU Enterprise Publishing & Presentation Standard™",
            "category": "Publishing / Design Governance", "status": "Active", "version": VERSION,
            "date_adopted": EFFECTIVE, "founder_approval": True,
            "description": "Universal presentation, typography, layout, callout, TOC, cover and pre-ship standard for all QRU products.",
            "purpose": "Every QRU product looks professionally published and communicates manufactured understanding.",
            "related_standards": ["QRU-CON-0001"], "related_products": ["all"], "created_at": now_iso()})
    # Governance bindings (idempotent) — systems that MUST inherit the standard.
    binds = [
        ("Deliverable Renderer", "Typography, layout, callouts, TOC"),
        ("Cover Studio", "Cover & Visual Identity Standard™"),
        ("Design Intelligence", "Hierarchy, contrast, heading order"),
        ("Treasure Standard Pre-Ship Gate", "Blocking validation before ship"),
        ("Factory OS / Concierge", "Every generated product inherits the standard"),
        ("Distribution Center", "Platform standardization matrix"),
        ("Media Production", "Image quality, alt text, thumbnails"),
    ]
    for system, section in binds:
        await db.publishing_bindings.update_one(
            {"system": system}, {"$set": {"system": system, "standard": DOC_ID, "section": section,
                                          "version": VERSION, "updated_at": now_iso()}}, upsert=True)


async def bindings_view():
    docs = [d async for d in db.publishing_bindings.find({}, {"_id": 0})]
    return {"standard": DOC_ID, "version": VERSION, "bindings": docs}
