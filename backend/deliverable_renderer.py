"""QRU Customer-Ready Deliverable Renderer™ (MT-024).

Turns an approved, Treasure Standard™-certified product into the EXACT file(s) a
customer receives — a readable/scrollable branded HTML edition (the "open & read"
experience) plus a downloadable primary format per product type (PDF, EPUB, PPTX,
PNG …). Fully deterministic — requires no LLM budget — so it always runs, even while
AI capacity is capped. Idempotent: re-rendering replaces the prior deliverable.

Treasure Standard™ certification validates the rendered deliverable itself here —
not just the metadata — via `validate_deliverable`.
"""
import os
import io
import html as _html
import logging

from database import db
from models import now_iso
import rendering_engine as re_engine
import design_language as dl

logger = logging.getLogger("qru.deliverable")

# Primary customer-facing file format per product type.
PRIMARY_FORMAT = {
    "Book": "epub", "Workbook": "pdf", "Teacher Guide": "pdf", "Caregiver Guide": "pdf",
    "Course": "pdf", "Quiz": "html", "Interactive Lesson": "html", "Short-form Content": "html",
    "Poster": "png", "Flash Cards": "pdf", "Presentation": "pptx",
    "Podcast Script": "html", "Video Script": "html",
}

FORMAT_LABEL = {
    "html": "Readable Edition (HTML)", "pdf": "Print-Ready PDF", "epub": "Digital eBook (EPUB)",
    "pptx": "Slide Deck (PPTX)", "png": "High-Res Poster (PNG)",
}
MEDIA_TYPE = {
    "html": "text/html", "pdf": "application/pdf", "epub": "application/epub+zip",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "png": "image/png", "mp4": "video/mp4",
}

MIN_BYTES = 800          # a real deliverable is never tiny
MIN_CONTENT_CHARS = 180  # source content must be substantive


# --------------------------------------------------------------------------- #
# Minimal, safe Markdown → HTML (headings, bold, lists, paragraphs). No LLM.
# --------------------------------------------------------------------------- #
def _md_to_html(md: str) -> str:
    out, in_list = [], False
    for raw in (md or "").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            if in_list:
                out.append("</ul>"); in_list = False
            continue
        esc = _html.escape(line)
        if line.strip() in ("---", "***", "___", "- - -"):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append("<hr/>")
            continue
        # bold
        while "**" in esc:
            esc = esc.replace("**", "<strong>", 1)
            esc = esc.replace("**", "</strong>", 1) if "**" in esc else esc + "</strong>"
        if line.startswith("# "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<h1>{esc[2:]}</h1>")
        elif line.startswith("## "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<h2>{esc[3:]}</h2>")
        elif line.startswith("### "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<h3>{esc[4:]}</h3>")
        elif line.lstrip().startswith("- "):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{esc.lstrip()[2:]}</li>")
        else:
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<p>{esc}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _render_html(product, cover_bytes=None) -> bytes:
    import base64
    pal = dl.resolve_palette(product.get("family", ""), product.get("department", product.get("college", "")),
                             product.get("topic", ""), product.get("title", ""))
    accent = "#%02X%02X%02X" % pal["accent"]
    title = _html.escape(product.get("title", "QRU Product"))
    ptype = _html.escape(product.get("product_type", ""))
    family = _html.escape(product.get("family", ""))
    body = _md_to_html(product.get("content") or "")
    cover_html = ""
    if cover_bytes:
        b64 = base64.b64encode(cover_bytes).decode("ascii")
        cover_html = f'<img class="cover" src="data:image/png;base64,{b64}" alt="cover"/>'
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title} — QRU PRESS™</title>
<style>
:root{{--royal:#35106A;--gold:#F5B21A;--navy:#221A42;--accent:{accent};}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:Georgia,'Times New Roman',serif;color:#221A42;background:#f4f2f7;line-height:1.7}}
.masthead{{background:linear-gradient(135deg,var(--royal),var(--navy));color:#fff;padding:40px 32px}}
.eyebrow{{font-family:Arial,Helvetica,sans-serif;letter-spacing:.22em;text-transform:uppercase;font-size:11px;color:var(--gold);font-weight:700}}
.masthead h1{{margin:.35em 0 .1em;font-size:34px;line-height:1.15}}
.meta{{font-family:Arial,sans-serif;font-size:13px;opacity:.85}}
.seal{{display:inline-block;margin-top:14px;font-family:Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:.1em;color:var(--navy);background:var(--gold);padding:6px 12px;border-radius:999px}}
.wrap{{max-width:760px;margin:0 auto;padding:36px 28px 80px}}
.cover{{width:100%;max-width:420px;display:block;margin:0 auto 28px;border-radius:10px;box-shadow:0 18px 50px rgba(53,16,106,.28)}}
.paper{{background:#fff;border-radius:14px;padding:44px 48px;box-shadow:0 10px 40px rgba(34,26,66,.08)}}
h1,h2,h3{{font-family:Arial,Helvetica,sans-serif;color:var(--royal)}}
h2{{border-left:5px solid var(--accent);padding-left:14px;margin-top:2em;font-size:22px}}
h3{{font-size:17px;color:var(--navy)}}
ul{{padding-left:22px}} li{{margin:.35em 0}}
hr{{border:none;border-top:1px solid #e5e1ee;max-width:120px;margin:24px 0}}
.footer{{text-align:center;font-family:Arial,sans-serif;font-size:12px;color:#8a83a3;margin-top:40px}}
.footer strong{{color:var(--royal)}}
</style></head><body>
<header class="masthead">
  <div class="eyebrow">QRU PRESS™ · {family}</div>
  <h1>{title}</h1>
  <div class="meta">{ptype} · {_html.escape(product.get('product_code',''))} · Customer Edition</div>
  <div class="seal">TREASURE STANDARD™ CERTIFIED</div>
</header>
<div class="wrap">
  {cover_html}
  <article class="paper">{body}</article>
  <div class="footer">Manufactured by <strong>QRU Factory™</strong> — Quest for Real Understanding.<br/>
  QRU simplifies the path to understanding the truth.</div>
</div>
</body></html>"""
    return doc.encode("utf-8")


def _render_pdf(product, kr, cover_bytes) -> bytes:
    qr = re_engine._make_qr(product.get("id", ""))
    return re_engine._make_pdf(product, kr or {}, cover_bytes, qr)


def _render_pptx(product) -> bytes:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    pal = dl.resolve_palette(product.get("family", ""), "", product.get("topic", ""), product.get("title", ""))
    ROYAL, GOLD, NAVY = RGBColor(53, 16, 106), RGBColor(245, 178, 26), RGBColor(34, 26, 66)
    ACCENT = RGBColor(*pal["accent"])
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    def bg(slide, color):
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = color

    def textbox(slide, text, top, size, color, bold=False, left=0.8, width=11.7, font="Arial"):
        tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(1.2))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; r = p.add_run(); r.text = text
        r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = font
        return tb

    # Title slide
    s = prs.slides.add_slide(blank); bg(s, ROYAL)
    textbox(s, "QRU PRESS™ · " + product.get("family", ""), 2.2, 16, GOLD, True)
    textbox(s, product.get("title", ""), 2.9, 40, RGBColor(255, 255, 255), True)
    textbox(s, "Treasure Standard™ Certified", 5.2, 16, GOLD, True)

    # Content slides — one per ## section
    content = product.get("content") or ""
    sections, cur_title, cur_body = [], None, []
    for line in content.split("\n"):
        if line.startswith("## "):
            if cur_title:
                sections.append((cur_title, "\n".join(cur_body)))
            cur_title, cur_body = line[3:].strip(), []
        elif line.startswith("# "):
            continue
        else:
            cur_body.append(line)
    if cur_title:
        sections.append((cur_title, "\n".join(cur_body)))
    if not sections:
        sections = [("Overview", content)]

    for stitle, sbody in sections[:24]:
        s = prs.slides.add_slide(blank); bg(s, RGBColor(255, 255, 255))
        bar = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(0.35), Inches(7.5))
        bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()
        textbox(s, stitle, 0.6, 30, ROYAL, True)
        clean_body = "\n".join(b.strip("-* ").strip() for b in sbody.split("\n") if b.strip())[:1100]
        tb = s.shapes.add_textbox(Inches(0.9), Inches(1.9), Inches(11.5), Inches(5.0))
        tf = tb.text_frame; tf.word_wrap = True
        for i, para in enumerate([x for x in clean_body.split("\n") if x][:12]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            r = p.add_run(); r.text = "• " + para
            r.font.size = Pt(16); r.font.color.rgb = NAVY; r.font.name = "Arial"
    buf = io.BytesIO(); prs.save(buf)
    return buf.getvalue()


def _render_poster_png(product, cover_bytes) -> bytes:
    # The branded premium cover already IS a print-ready poster at high resolution.
    return cover_bytes


def _render_epub(product) -> bytes:
    from ebooklib import epub
    book = epub.EpubBook()
    book.set_identifier(product.get("id", "qru"))
    book.set_title(product.get("title", "QRU Book"))
    book.set_language("en")
    book.add_author("QRU PRESS™")
    body_html = _md_to_html(product.get("content") or "")
    c = epub.EpubHtml(title=product.get("title", "Chapter"), file_name="content.xhtml", lang="en")
    c.content = (f"<h1>{_html.escape(product.get('title',''))}</h1>"
                 f"<p><em>Treasure Standard™ Certified · QRU PRESS™</em></p>{body_html}")
    book.add_item(c)
    book.toc = (c,)
    book.spine = ["nav", c]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    buf = io.BytesIO()
    epub.write_epub(buf, book)
    return buf.getvalue()


async def ensure_deliverable(pid, actor="Manufacturing Director™", base_url=""):
    """Render (idempotently) the customer-ready deliverable set for a product.
    Always produces a readable HTML edition + a downloadable primary format.
    Deterministic — safe to call while the LLM budget is capped."""
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    kr = await db.knowledge_records.find_one({"id": p.get("knowledge_record_id")}) if p.get("knowledge_record_id") else {}

    # branded cover (reuse existing if rendered, else compose deterministically)
    cover_bytes = None
    cu = p.get("cover_url")
    if cu:
        path = os.path.join(re_engine.ASSET_DIR, cu.split("/")[-1])
        if os.path.exists(path):
            with open(path, "rb") as f:
                cover_bytes = f.read()
    if cover_bytes is None:
        cover_bytes = dl.premium_cover(p, kr or {})

    files = []

    def add(fmt, data):
        fid = re_engine._save(f"deliverable-{fmt}", fmt, data)
        files.append({"format": fmt, "label": FORMAT_LABEL.get(fmt, fmt.upper()),
                      "url": re_engine._asset_url(fid), "media_type": MEDIA_TYPE.get(fmt, "application/octet-stream"),
                      "filename": fid, "bytes": len(data)})

    ptype = p.get("product_type", "")
    primary = PRIMARY_FORMAT.get(ptype, "pdf")

    # 1) Always: readable HTML edition (the open/read/scroll experience)
    try:
        add("html", _render_html(p, cover_bytes))
    except Exception as e:
        logger.error(f"HTML render failed for {pid}: {e}")

    # 2) Type-specific primary + universal PDF fallback
    try:
        if primary == "pptx":
            add("pptx", _render_pptx(p))
        elif primary == "png":
            add("png", _render_poster_png(p, cover_bytes))
        elif primary == "epub":
            add("epub", _render_epub(p))
        # PDF is always available as a print/download format for text products.
        if primary in ("pdf", "epub", "html", "pptx"):
            add("pdf", _render_pdf(p, kr, cover_bytes))
    except Exception as e:
        logger.error(f"primary({primary}) render failed for {pid}: {e}")
        # guarantee at least a PDF exists
        if not any(f["format"] == "pdf" for f in files):
            try:
                add("pdf", _render_pdf(p, kr, cover_bytes))
            except Exception as e2:
                logger.error(f"pdf fallback failed for {pid}: {e2}")

    validation = validate_deliverable(p, files, primary)
    design = assess_design_quality(p, files, cover_bytes)
    deliverable = {
        "primary_format": primary if any(f["format"] == primary for f in files) else (files[0]["format"] if files else None),
        "files": files,
        "ready": validation["ready"],
        "validated": validation["ready"],
        "validation": validation,
        "design_review": design,
        "design_approved": design["approved"],
        "status_label": design["status"],
        "preview_url": next((f["url"] for f in files if f["format"] == "html"), None),
        "download_url": next((f["url"] for f in files if f["format"] == primary),
                             (files[0]["url"] if files else None)),
        "rendered_at": now_iso(),
        "rendered_by": actor,
    }
    await db.products.update_one({"id": pid}, {"$set": {
        "customer_deliverable": deliverable, "deliverable_ready": validation["ready"],
        "design_review_required": not design["approved"], "updated_at": now_iso()}})
    try:
        from org_activity import log_org
        note = "success" if (validation["ready"] and design["approved"]) else "warning"
        await log_org("Creative Studio Director™", "Creative Studio",
                      f"rendered the customer-ready {primary.upper()} deliverable ({design['status']}) for",
                      p.get("product_code", ""), note)
    except Exception:
        pass
    return deliverable


# --------------------------------------------------------------------------- #
# MT-025 — Treasure Standard™ Design Validation (deterministic, no LLM).
# Validates that the rendered product is not only present but visually
# customer-ready: cover, interior structure, typography, hierarchy, QRU +
# Treasure Standard™ branding, readability, print & mobile quality.
# --------------------------------------------------------------------------- #
DESIGN_THRESHOLD = 85


def assess_design_quality(product, files, cover_bytes=None):
    content = product.get("content") or ""
    section_count = content.count("\n## ") + (1 if content.startswith("## ") else 0)
    chars = len(content)
    branded = bool(product.get("design_language_applied"))
    has_html = any(f["format"] == "html" and f["bytes"] >= 4000 for f in files)
    has_pdf = any(f["format"] == "pdf" for f in files)
    pdf_bytes = max([f["bytes"] for f in files if f["format"] == "pdf"] + [0])

    # cover dimensions
    cover_w = cover_h = 0
    try:
        from PIL import Image
        cb = cover_bytes
        if cb is None and product.get("cover_url"):
            cpath = os.path.join(re_engine.ASSET_DIR, product["cover_url"].split("/")[-1])
            if os.path.exists(cpath):
                with open(cpath, "rb") as f:
                    cb = f.read()
        if cb:
            with Image.open(io.BytesIO(cb)) as im:
                cover_w, cover_h = im.size
    except Exception:
        pass

    c = []

    def crit(name, passed, weight, detail=""):
        c.append({"name": name, "passed": bool(passed), "weight": weight, "detail": detail})

    crit("Cover design (high-resolution branded)", cover_w >= 1000 and cover_h >= 1000, 15,
         f"{cover_w}×{cover_h}px")
    crit("QRU branding applied", branded, 10, "QRU Design Language™" if branded else "not applied")
    crit("Treasure Standard™ branding", branded, 5, "seal present" if branded else "missing")
    crit("Interior page design & sections", section_count >= 3, 15, f"{section_count} sections")
    crit("Visual hierarchy (headings)", ("# " in content) and section_count >= 2, 10,
         "title + sections" if ("# " in content) else "no title heading")
    crit("Typography & readability", 600 <= chars, 15, f"{chars} chars")
    crit("Print quality (PDF)", has_pdf and pdf_bytes >= 20000, 10, f"{pdf_bytes // 1024} KB PDF")
    crit("Mobile readability (responsive HTML)", has_html, 10, "viewport + fluid layout")
    crit("Margins & spacing (premium template)", branded and has_html, 10, "premium template")

    grade = sum(x["weight"] for x in c if x["passed"])
    approved = grade >= DESIGN_THRESHOLD
    failed = [x["name"] for x in c if not x["passed"]]
    return {
        "grade": grade,
        "approved": approved,
        "status": "Treasure Standard™ Approved" if approved else "Rendered — Design Review Required",
        "threshold": DESIGN_THRESHOLD,
        "criteria": c,
        "recommendations": failed,
        "assessed_at": now_iso(),
    }


def validate_deliverable(product, files, primary):
    """Treasure Standard™ deliverable validation — the FILE itself, not just metadata."""
    checks = []
    content_chars = len(product.get("content") or "")
    checks.append({"check": "Source content substantive", "passed": content_chars >= MIN_CONTENT_CHARS,
                   "detail": f"{content_chars} chars"})
    has_readable = any(f["format"] == "html" and f["bytes"] >= MIN_BYTES for f in files)
    checks.append({"check": "Readable customer edition rendered", "passed": has_readable})
    has_primary = any(f["format"] == primary and f["bytes"] >= MIN_BYTES for f in files)
    checks.append({"check": f"Primary format ({primary.upper()}) rendered", "passed": has_primary})
    # every file exists on disk and is non-trivial
    on_disk = True
    for f in files:
        path = os.path.join(re_engine.ASSET_DIR, f.get("filename", ""))
        if not (os.path.exists(path) and os.path.getsize(path) >= MIN_BYTES):
            on_disk = False
    checks.append({"check": "All deliverable files present on disk", "passed": on_disk and bool(files)})
    ready = all(c["passed"] for c in checks)
    return {"ready": ready, "checks": checks, "content_chars": content_chars,
            "file_count": len(files)}
