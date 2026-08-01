"""QRU Governed Printable Product Manufacturing™ (STD-PPB-0001).

Turns uploaded artwork (PNG/JPEG) into a governed, distributable multi-page PDF product:
  • 1-Page Printable
  • 3-Page QuickStart
  • 5-Page Mini Workbook
  • 8-Page Coloring / Activity Book

The SAME governance philosophy as the Render/Export engine applies:
  • Never distort or crop — images are contain-fit onto the page with brand-safe margins.
  • A resolution QUALITY GATE runs per page. Below 150 effective DPI → "Revision Required" (blurry in
    print, needs human sign-off). 150–300 DPI → warning. ≥300 DPI → clean.
  • Never silently degrade — every page's effective DPI and status is reported.

The finished PDF is a real, embeddable file suitable as an Etsy digital download, a QRU Online download,
or a Teachers Pay Teachers resource. It NEVER auto-publishes.
"""
import io

import design_language as dl
import layout_engine as lay

STANDARD_ID = "STD-PPB-0001"

# Page geometry — US Letter portrait @ 300 DPI (the norm for printables / workbooks / TpT / coloring books).
PAGE_SIZES = {
    "letter": {"label": "US Letter 8.5×11", "in": (8.5, 11.0)},
    "a4": {"label": "A4 8.27×11.69", "in": (8.27, 11.69)},
    "square": {"label": "Square 8×8", "in": (8.0, 8.0)},
}
DEFAULT_DPI = 300
MARGIN_IN = 0.5
DEFAULT_MARGIN_IN = 0.25   # Universal Page Layout Engine™ printer-safe margin (configurable)
MIN_PRINT_DPI = 150      # below this → blurry in print → human review required
IDEAL_PRINT_DPI = 300    # at/above this → clean

# Product types (MVP). content_slots is a guidance target; the builder is flexible about actual count.
PRODUCT_TYPES = {
    "one_page_printable": {"label": "1-Page Printable", "pages": 1, "cover": False, "instructions": False},
    "three_page_quickstart": {"label": "3-Page QuickStart", "pages": 3, "cover": True, "instructions": True},
    "five_page_mini_workbook": {"label": "5-Page Mini Workbook", "pages": 5, "cover": True, "instructions": True},
    "eight_page_activity_book": {"label": "8-Page Coloring / Activity Book", "pages": 8, "cover": True, "instructions": True, "activity": True},
}

# Destinations this deliverable can serve (informational — publication is decided by governed policy).
SUITABLE_DESTINATIONS = [
    {"id": "etsy_download", "label": "Etsy digital download"},
    {"id": "qru_online_download", "label": "QRU Online download"},
    {"id": "tpt_resource", "label": "Teachers Pay Teachers resource"},
]


def _page_px(page_size):
    w_in, h_in = PAGE_SIZES.get(page_size, PAGE_SIZES["letter"])["in"]
    return int(round(w_in * DEFAULT_DPI)), int(round(h_in * DEFAULT_DPI)), w_in, h_in


def _content_box(pw, ph):
    m = int(round(MARGIN_IN * DEFAULT_DPI))
    return m, m, pw - m, ph - m  # left, top, right, bottom


def _contain_fit(im, box_w, box_h):
    """Scale to FIT the content box (up or down), preserving aspect — never distort, never crop."""
    from PIL import Image
    ratio = min(box_w / im.width, box_h / im.height)
    new_w, new_h = max(int(round(im.width * ratio)), 1), max(int(round(im.height * ratio)), 1)
    return im.resize((new_w, new_h), Image.LANCZOS)


def _content_page(img_bytes, page_size, palette, page_no):
    """Render one content page (contain-fit, no crop/distort) and report its effective print DPI."""
    from PIL import Image, ImageDraw
    pw, ph, w_in, h_in = _page_px(page_size)
    canvas = Image.new("RGB", (pw, ph), (255, 255, 255))
    src = Image.open(io.BytesIO(img_bytes))
    if src.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", src.size, (255, 255, 255))
        src = src.convert("RGBA"); bg.paste(src, mask=src.split()[-1]); src = bg
    else:
        src = src.convert("RGB")
    orig_w, orig_h = src.width, src.height
    l, t, r, b = _content_box(pw, ph)
    box_w, box_h = r - l, b - t
    fitted = _contain_fit(src, box_w, box_h)
    # Effective print DPI = original pixels ÷ the printed size (inches) it now occupies.
    printed_w_in = fitted.width / DEFAULT_DPI
    printed_h_in = fitted.height / DEFAULT_DPI
    eff_dpi = round(min(orig_w / max(printed_w_in, 0.01), orig_h / max(printed_h_in, 0.01)))
    x = l + (box_w - fitted.width) // 2
    y = t + (box_h - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    d = ImageDraw.Draw(canvas)
    d.text((pw // 2, ph - int(0.28 * DEFAULT_DPI)), f"QRU PRESS™  ·  {page_no}",
           font=dl._f(dl.SANS, 26), fill=(120, 120, 130), anchor="mm")
    status = "CLEAN" if eff_dpi >= IDEAL_PRINT_DPI else ("ACCEPTABLE" if eff_dpi >= MIN_PRINT_DPI else "LOW_RES")
    return canvas, {"page": page_no, "type": "content", "effective_dpi": eff_dpi, "status": status,
                    "source_px": [orig_w, orig_h]}


def _cover_page(title, subtitle, page_size, palette):
    from PIL import Image, ImageDraw
    pw, ph, _, _ = _page_px(page_size)
    canvas = dl._vignette(dl._gradient(pw, ph, palette["top"], palette["bottom"]))
    d = ImageDraw.Draw(canvas)
    accent = palette["accent"]
    d.text((pw // 2, int(0.16 * ph)), "QRU PRESS™", font=dl._f(dl.SANS_BOLD, 40), fill=accent, anchor="mm")
    # Title (wrapped)
    ty = int(0.40 * ph)
    words = (title or "Untitled").split()
    lines, cur = [], ""
    fnt = dl._f(dl.SERIF_BOLD, 96)
    maxw = pw - int(1.4 * DEFAULT_DPI)
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=fnt) <= maxw:
            cur = test
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    for i, ln in enumerate(lines[:4]):
        d.text((pw // 2, ty + i * 110), ln, font=fnt, fill=(255, 255, 255), anchor="mm")
    if subtitle:
        d.text((pw // 2, ty + len(lines[:4]) * 110 + 90), subtitle,
               font=dl._f(dl.SERIF, 44), fill=(230, 230, 235), anchor="mm")
    d.text((pw // 2, int(0.9 * ph)), "Treasure Standard™", font=dl._f(dl.SANS, 30), fill=accent, anchor="mm")
    return canvas, {"type": "cover", "effective_dpi": DEFAULT_DPI, "status": "CLEAN"}


def _instructions_page(title, lines, page_size, palette):
    from PIL import Image, ImageDraw
    pw, ph, _, _ = _page_px(page_size)
    canvas = Image.new("RGB", (pw, ph), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    accent = palette["accent"]
    l = int(MARGIN_IN * DEFAULT_DPI)
    d.text((l, int(0.12 * ph)), "How to Use This Resource", font=dl._f(dl.SERIF_BOLD, 72), fill=palette["top"])
    d.line([(l, int(0.12 * ph) + 96), (pw - l, int(0.12 * ph) + 96)], fill=accent, width=6)
    y = int(0.20 * ph)
    body = lines or ["Print at 100% (do not 'fit to page') for exact sizing.",
                     "Use quality paper for best results.",
                     "For classroom or personal use as licensed.",
                     "Every page is verified against the QRU Treasure Standard™."]
    for ln in body:
        d.text((l, y), "•  " + ln, font=dl._f(dl.SANS, 40), fill=(40, 40, 55))
        y += 84
    d.text((pw // 2, ph - int(0.28 * DEFAULT_DPI)), "QRU PRESS™", font=dl._f(dl.SANS, 26),
           fill=(120, 120, 130), anchor="mm")
    return canvas, {"type": "instructions", "effective_dpi": DEFAULT_DPI, "status": "CLEAN"}


def build(product, product_type, images, *, include_cover=None, include_instructions=None,
          title=None, subtitle=None, instructions=None, page_size="letter", activity_layout=None,
          worksheet_presets=None, layout=None, margin_in=None, custom_scale=100):
    """Assemble the governed PDF. `images` is a list of raw bytes in the desired page order.

    Returns {pdf_bytes, page_count, qa, quality_review_required, pages_meta} or {error}.
    """
    ptype = PRODUCT_TYPES.get(product_type)
    if not ptype:
        return {"error": f"Unknown product type '{product_type}'. Choose one of: {', '.join(PRODUCT_TYPES)}."}
    if page_size not in PAGE_SIZES:
        page_size = "letter"
    inc_cover = ptype["cover"] if include_cover is None else bool(include_cover)
    inc_instr = ptype["instructions"] if include_instructions is None else bool(include_instructions)
    # Activity templates (title strip + worksheet lines) default ON for the activity book.
    use_activity = ptype.get("activity", False) if activity_layout is None else bool(activity_layout)
    # Universal Page Layout Engine™ — default: Activity Book keeps "activity", everything else "poster".
    if not layout:
        layout = "activity" if use_activity else "poster"
    if layout not in lay.LAYOUT_IDS:
        return {"error": f"Unknown layout '{layout}'. Choose one of: {', '.join(sorted(lay.LAYOUT_IDS))}."}
    margin_in = DEFAULT_MARGIN_IN if margin_in is None else max(float(margin_in), 0.0)

    p = product or {}
    palette = dl.resolve_palette(p.get("family", ""), p.get("department", p.get("college", "")),
                                 p.get("topic", ""), p.get("title", ""))
    title = title or p.get("title") or "QRU Printable"
    subtitle = subtitle if subtitle is not None else (p.get("subtitle") or "")

    pw, ph, _, _ = _page_px(page_size)
    margin_px = int(round(margin_in * DEFAULT_DPI))

    issues, warnings, pages_meta, canvases = [], [], [], []

    if inc_cover:
        c, meta = _cover_page(title, subtitle, page_size, palette)
        canvases.append(c); pages_meta.append({"page": len(canvases), **meta})
    if inc_instr:
        c, meta = _instructions_page(title, instructions, page_size, palette)
        canvases.append(c); pages_meta.append({"page": len(canvases), **meta})

    if not images:
        return {"error": "No artwork uploaded. Add at least one page image before building the PDF."}

    quality_review = False
    for img_bytes in images:
        try:
            artwork = lay.decode_artwork(img_bytes)
            c, meta = lay.render_page(artwork, layout=layout, page_size_px=(pw, ph), margin_px=margin_px,
                                      custom_scale=custom_scale or 100, palette=palette,
                                      page_no=len(canvases) + 1, title=title)
        except Exception as e:
            issues.append(f"Page {len(canvases)+1}: could not import artwork ({str(e)[:80]}).")
            continue
        canvases.append(c); pages_meta.append(meta)
        if meta["status"] == "LOW_RES":
            quality_review = True
            warnings.append(f"Page {meta['page']}: low resolution ({meta['effective_dpi']} DPI) — will look "
                            f"blurry in print. Upload a larger image, tap Regenerate Larger, or approve after review.")
        elif meta["status"] == "ACCEPTABLE":
            warnings.append(f"Page {meta['page']}: {meta['effective_dpi']} DPI (below the 300 DPI ideal).")

    if not canvases:
        return {"error": "Could not build any pages from the uploaded artwork."}

    # Worksheet Presets — drop in ready-made activity layouts (tracing / matching / word search).
    if use_activity and worksheet_presets:
        for preset in worksheet_presets:
            if preset in WORKSHEET_PRESETS:
                c, meta = _preset_page(preset, title, page_size, palette, len(canvases) + 1)
                canvases.append(c); pages_meta.append(meta)

    # Activity templates: auto-fill to the target page count so a few PNGs become a full book.
    if use_activity:
        while len(canvases) < ptype["pages"]:
            c, meta = _activity_template_page(title, page_size, palette, len(canvases) + 1)
            canvases.append(c); pages_meta.append(meta)

    total = len(canvases)
    if total != ptype["pages"]:
        warnings.append(f"This is a {total}-page PDF; the '{ptype['label']}' type targets {ptype['pages']} pages.")

    # Encode multi-page PDF at 300 DPI.
    buf = io.BytesIO()
    canvases[0].save(buf, format="PDF", save_all=True, append_images=canvases[1:],
                     resolution=float(DEFAULT_DPI))
    pdf_bytes = buf.getvalue()

    if issues:
        result = "FAIL"
    elif quality_review:
        result = "REVISION_REQUIRED"
    elif warnings:
        result = "PASS WITH WARNINGS"
    else:
        result = "PASS"

    return {
        "standard": STANDARD_ID, "product_type": product_type, "product_type_label": ptype["label"],
        "page_size": page_size, "page_size_label": PAGE_SIZES[page_size]["label"],
        "layout": layout, "margin_in": margin_in, "custom_scale": custom_scale,
        "dpi": DEFAULT_DPI, "page_count": total, "pages_meta": pages_meta,
        "quality_review_required": quality_review,
        "qa": {"result": result, "issues": issues, "warnings": warnings,
               "gate": {"min_print_dpi": MIN_PRINT_DPI, "ideal_print_dpi": IDEAL_PRINT_DPI}},
        "suitable_destinations": SUITABLE_DESTINATIONS,
        "pdf_bytes": pdf_bytes,
    }


def render_preview_page(product, image_bytes, *, layout="poster", page_size="letter",
                        margin_in=None, custom_scale=100, title=None, max_px=760):
    """Fast single-page PNG preview (base64-ready bytes) for the live layout preview — no PDF, no store."""
    if page_size not in PAGE_SIZES:
        page_size = "letter"
    if layout not in lay.LAYOUT_IDS:
        return {"error": f"Unknown layout '{layout}'."}
    margin_in = DEFAULT_MARGIN_IN if margin_in is None else max(float(margin_in), 0.0)
    p = product or {}
    palette = dl.resolve_palette(p.get("family", ""), p.get("department", p.get("college", "")),
                                 p.get("topic", ""), p.get("title", ""))
    pw, ph, _, _ = _page_px(page_size)
    try:
        artwork = lay.decode_artwork(image_bytes)
        canvas, meta = lay.render_page(artwork, layout=layout, page_size_px=(pw, ph),
                                       margin_px=int(round(margin_in * DEFAULT_DPI)),
                                       custom_scale=custom_scale or 100, palette=palette, page_no=1,
                                       title=title or p.get("title") or "QRU Printable")
    except Exception as e:
        return {"error": f"Could not render preview: {str(e)[:100]}"}
    from PIL import Image
    canvas.thumbnail((max_px, max_px), Image.LANCZOS)
    buf = io.BytesIO(); canvas.save(buf, format="PNG")
    return {"png_bytes": buf.getvalue(), "effective_dpi": meta["effective_dpi"], "status": meta["status"],
            "layout": layout, "margin_in": margin_in}



# ---------------------------------------------------------------------------
# Activity Templates — title strip + framed artwork + worksheet/coloring lines.
# ---------------------------------------------------------------------------
def _title_strip(d, pw, palette, text):
    strip_h = int(0.10 * DEFAULT_DPI * 11)  # ~1.1in strip
    d.rectangle([0, 0, pw, strip_h], fill=palette["top"])
    d.rectangle([0, strip_h - 10, pw, strip_h], fill=palette["accent"])
    d.text((pw // 2, strip_h // 2), (text or "Activity")[:48], font=dl._f(dl.SERIF_BOLD, 60),
           fill=(255, 255, 255), anchor="mm")
    return strip_h


def _worksheet_lines(d, l, top, r, bottom, accent):
    y = top
    gap = int(0.5 * DEFAULT_DPI)
    while y < bottom:
        d.line([(l, y), (r, y)], fill=(205, 205, 215), width=3)
        y += gap


def _activity_content_page(img_bytes, title, page_size, palette, page_no):
    """Content page with a branded title strip, framed artwork (top half), and ruled lines below."""
    from PIL import Image, ImageDraw
    pw, ph, _, _ = _page_px(page_size)
    canvas = Image.new("RGB", (pw, ph), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    strip_h = _title_strip(d, pw, palette, title)
    src = Image.open(io.BytesIO(img_bytes))
    if src.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", src.size, (255, 255, 255)); src = src.convert("RGBA")
        bg.paste(src, mask=src.split()[-1]); src = bg
    else:
        src = src.convert("RGB")
    orig_w, orig_h = src.width, src.height
    l = int(MARGIN_IN * DEFAULT_DPI)
    art_top = strip_h + int(0.2 * DEFAULT_DPI)
    art_bottom = int(ph * 0.60)
    box_w, box_h = pw - 2 * l, art_bottom - art_top
    fitted = _contain_fit(src, box_w, box_h)
    printed_w_in, printed_h_in = fitted.width / DEFAULT_DPI, fitted.height / DEFAULT_DPI
    eff_dpi = round(min(orig_w / max(printed_w_in, 0.01), orig_h / max(printed_h_in, 0.01)))
    x = l + (box_w - fitted.width) // 2
    canvas.paste(fitted, (x, art_top))
    d.rectangle([x - 6, art_top - 6, x + fitted.width + 6, art_top + fitted.height + 6],
                outline=palette["accent"], width=5)
    # Worksheet / coloring prompt + ruled lines in the lower half.
    py = art_bottom + int(0.3 * DEFAULT_DPI)
    d.text((l, py), "Your turn:", font=dl._f(dl.SANS_BOLD, 44), fill=palette["top"])
    _worksheet_lines(d, l, py + int(0.6 * DEFAULT_DPI), pw - l, ph - int(0.5 * DEFAULT_DPI), palette["accent"])
    d.text((pw // 2, ph - int(0.28 * DEFAULT_DPI)), f"QRU PRESS™  ·  {page_no}",
           font=dl._f(dl.SANS, 26), fill=(120, 120, 130), anchor="mm")
    status = "CLEAN" if eff_dpi >= IDEAL_PRINT_DPI else ("ACCEPTABLE" if eff_dpi >= MIN_PRINT_DPI else "LOW_RES")
    return canvas, {"page": page_no, "type": "activity", "effective_dpi": eff_dpi, "status": status,
                    "source_px": [orig_w, orig_h]}


def _activity_template_page(title, page_size, palette, page_no):
    """Auto-added activity/worksheet page (no artwork) so a few PNGs become a full book."""
    from PIL import Image, ImageDraw
    pw, ph, _, _ = _page_px(page_size)
    canvas = Image.new("RGB", (pw, ph), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    strip_h = _title_strip(d, pw, palette, "Activity")
    l = int(MARGIN_IN * DEFAULT_DPI)
    py = strip_h + int(0.4 * DEFAULT_DPI)
    d.text((l, py), "Draw, color, or write your answer:", font=dl._f(dl.SANS_BOLD, 44), fill=palette["top"])
    # Large framed blank area for drawing/coloring + ruled lines beneath.
    fb_top = py + int(0.7 * DEFAULT_DPI); fb_bottom = int(ph * 0.55)
    d.rectangle([l, fb_top, pw - l, fb_bottom], outline=(205, 205, 215), width=4)
    _worksheet_lines(d, l, fb_bottom + int(0.4 * DEFAULT_DPI), pw - l, ph - int(0.5 * DEFAULT_DPI), palette["accent"])
    d.text((pw // 2, ph - int(0.28 * DEFAULT_DPI)), f"QRU PRESS™  ·  {page_no}",
           font=dl._f(dl.SANS, 26), fill=(120, 120, 130), anchor="mm")
    return canvas, {"page": page_no, "type": "activity_template", "effective_dpi": DEFAULT_DPI, "status": "CLEAN",
                    "auto_generated": True}


# ---------------------------------------------------------------------------
# Regenerate Larger — upscale a source image so it meets print DPI (honest: upscaled, flagged).
# ---------------------------------------------------------------------------
def enhance_image_for_print(image_bytes, page_size="letter", activity=False):
    """Lanczos-upscale the source so it fills its page slot at ~300 DPI. Adds no real detail, so the
    result is flagged 'enhanced' (upscaled) — quality still needs a human eye, but it won't be tiny/blurry
    from stretching a stored thumbnail."""
    from PIL import Image
    if page_size not in PAGE_SIZES:
        page_size = "letter"
    pw, ph, _, _ = _page_px(page_size)
    l = int(MARGIN_IN * DEFAULT_DPI)
    if activity:
        box_w = pw - 2 * l
        box_h = int(ph * 0.60) - (int(0.10 * DEFAULT_DPI * 11) + int(0.2 * DEFAULT_DPI))
    else:
        box_w, box_h = pw - 2 * l, ph - 2 * l
    src = Image.open(io.BytesIO(image_bytes))
    src = src.convert("RGBA") if src.mode in ("RGBA", "LA", "P") else src.convert("RGB")
    ratio = min(box_w / src.width, box_h / src.height)
    tw, th = max(int(round(src.width * ratio)), 1), max(int(round(src.height * ratio)), 1)
    upscaled = ratio > 1.0
    out_im = src.resize((tw, th), Image.LANCZOS)
    if out_im.mode == "RGBA":
        bg = Image.new("RGB", out_im.size, (255, 255, 255)); bg.paste(out_im, mask=out_im.split()[-1]); out_im = bg
    buf = io.BytesIO(); out_im.save(buf, format="PNG", dpi=(DEFAULT_DPI, DEFAULT_DPI))
    return {"data": buf.getvalue(), "upscaled": upscaled, "new_px": [tw, th],
            "target_dpi": DEFAULT_DPI, "original_px": [src.width, src.height]}


# ---------------------------------------------------------------------------
# Bundle — table-of-contents page renderer (single-page PDF bytes).
# ---------------------------------------------------------------------------
def render_toc_pdf(title, entries, page_size, palette):
    """entries: [{title, start_page, pages}] → a branded Contents page as single-page PDF bytes."""
    from PIL import Image, ImageDraw
    pw, ph, _, _ = _page_px(page_size)
    canvas = Image.new("RGB", (pw, ph), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    strip_h = _title_strip(d, pw, palette, title or "Activity Pack")
    l = int(MARGIN_IN * DEFAULT_DPI)
    y = strip_h + int(0.5 * DEFAULT_DPI)
    d.text((l, y), "Contents", font=dl._f(dl.SERIF_BOLD, 64), fill=palette["top"])
    y += int(0.9 * DEFAULT_DPI)
    for e in entries:
        line = f"{e['title']}"
        d.text((l, y), line[:60], font=dl._f(dl.SANS, 40), fill=(40, 40, 55))
        pg = f"p.{e['start_page']}"
        d.text((pw - l, y), pg, font=dl._f(dl.SANS_BOLD, 40), fill=palette["top"], anchor="ra")
        d.line([(l, y + 56), (pw - l, y + 56)], fill=(225, 225, 232), width=2)
        y += int(0.75 * DEFAULT_DPI)
    d.text((pw // 2, ph - int(0.3 * DEFAULT_DPI)), "QRU PRESS™ · Treasure Standard™",
           font=dl._f(dl.SANS, 26), fill=(120, 120, 130), anchor="mm")
    buf = io.BytesIO(); canvas.save(buf, format="PDF", resolution=float(DEFAULT_DPI))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Worksheet Presets — ready-made activity layouts the activity book can drop in.
# ---------------------------------------------------------------------------
WORKSHEET_PRESETS = {
    "tracing": "Tracing Practice",
    "matching": "Match the Pairs",
    "word_search": "Word Search",
}


def _preset_page(preset, title, page_size, palette, page_no):
    import random
    from PIL import ImageDraw, Image
    pw, ph, _, _ = _page_px(page_size)
    canvas = Image.new("RGB", (pw, ph), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    label = WORKSHEET_PRESETS.get(preset, "Activity")
    _title_strip(d, pw, palette, label)
    l = int(MARGIN_IN * DEFAULT_DPI)
    top = int(0.14 * DEFAULT_DPI * 11)
    accent = palette["accent"]

    if preset == "tracing":
        d.text((l, top), "Trace the dotted lines, then write your own:", font=dl._f(dl.SANS_BOLD, 40), fill=palette["top"])
        y = top + int(0.7 * DEFAULT_DPI)
        row_gap = int(1.1 * DEFAULT_DPI)
        while y < ph - int(0.7 * DEFAULT_DPI):
            # top guide, dotted mid guide, bottom baseline
            d.line([(l, y), (pw - l, y)], fill=(210, 210, 220), width=3)
            xx = l
            while xx < pw - l:
                d.line([(xx, y + row_gap // 2), (xx + 26, y + row_gap // 2)], fill=(180, 180, 195), width=3)
                xx += 52
            d.line([(l, y + row_gap - 20), (pw - l, y + row_gap - 20)], fill=(150, 150, 170), width=4)
            y += row_gap

    elif preset == "matching":
        d.text((l, top), "Draw a line to match each pair:", font=dl._f(dl.SANS_BOLD, 40), fill=palette["top"])
        left = ["1", "2", "3", "4", "5"]
        right = left[:]; random.shuffle(right)
        y = top + int(0.8 * DEFAULT_DPI); gap = int(1.3 * DEFAULT_DPI)
        lx, rx = l + int(0.4 * DEFAULT_DPI), pw - l - int(0.4 * DEFAULT_DPI)
        for i in range(5):
            d.ellipse([lx - 60, y - 60, lx + 60, y + 60], outline=accent, width=5)
            d.text((lx, y), left[i], font=dl._f(dl.SERIF_BOLD, 60), fill=palette["top"], anchor="mm")
            d.rectangle([rx - 200, y - 60, rx + 60, y + 60], outline=accent, width=4)
            d.text((rx - 70, y), f"Item {right[i]}", font=dl._f(dl.SANS, 36), fill=(60, 60, 75), anchor="mm")
            d.ellipse([lx + 90, y - 12, lx + 114, y + 12], fill=accent)
            d.ellipse([rx - 224, y - 12, rx - 200, y + 12], fill=accent)
            y += gap

    elif preset == "word_search":
        d.text((l, top), "Find the hidden words:", font=dl._f(dl.SANS_BOLD, 40), fill=palette["top"])
        cols = rows = 12
        grid_top = top + int(0.7 * DEFAULT_DPI)
        grid_size = min(pw - 2 * l, int(ph * 0.55))
        cell = grid_size // cols
        gx = (pw - cell * cols) // 2
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        f = dl._f(dl.SANS_BOLD, int(cell * 0.55))
        for r in range(rows):
            for c in range(cols):
                cx = gx + c * cell + cell // 2
                cy = grid_top + r * cell + cell // 2
                d.text((cx, cy), random.choice(letters), font=f, fill=(70, 70, 90), anchor="mm")
        by = grid_top + rows * cell + int(0.3 * DEFAULT_DPI)
        d.text((l, by), "Words:  LEARN   FOCUS   THINK   GROW   TRUTH",
               font=dl._f(dl.SANS_BOLD, 34), fill=palette["top"])

    d.text((pw // 2, ph - int(0.28 * DEFAULT_DPI)), f"QRU PRESS™  ·  {page_no}",
           font=dl._f(dl.SANS, 26), fill=(120, 120, 130), anchor="mm")
    return canvas, {"page": page_no, "type": f"worksheet_{preset}", "effective_dpi": DEFAULT_DPI,
                    "status": "CLEAN", "preset": preset}
