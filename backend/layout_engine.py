"""QRU Universal Page Layout Engine™ (STD-UPLE-0001).

Turns ANY imported artwork (PNG / JPG / SVG) into a governed page rendered with a chosen layout mode.
The headline mode is "poster" (Full-Page Printable): the artwork fills the maximum printable area inside
the printer-safe margin, aspect preserved, centered — never shrunk to a tiny centered thumbnail.

Fit modes (how the image sits in its box): fit (contain) · fill (cover+crop) · original · custom_scale.
Layout modes (page structure): poster · coloring · bordered · book_illustration (image-forward)
and worksheet · workbook · activity · cut_paste (image + teaching furniture).
"""
import io

import design_language as dl

DEFAULT_DPI = 300
DEFAULT_MARGIN_IN = 0.25
_WHITE = (255, 255, 255)

LAYOUTS = [
    {"id": "poster", "label": "Poster (Full Page)", "group": "image", "desc": "Fills the page inside the safe margin."},
    {"id": "fill", "label": "Fill Page (crop)", "group": "image", "desc": "Covers the page; crops overflow."},
    {"id": "original", "label": "Original Size", "group": "image", "desc": "Native size, centered (no upscaling)."},
    {"id": "custom_scale", "label": "Custom Scale (%)", "group": "image", "desc": "Scale a % of the full-page fit."},
    {"id": "coloring", "label": "Coloring Page", "group": "image", "desc": "Full-page line art with a thin frame."},
    {"id": "bordered", "label": "Bordered Print", "group": "image", "desc": "Artwork inside a decorative border."},
    {"id": "book_illustration", "label": "Book Illustration", "group": "image", "desc": "Centered with a caption line."},
    {"id": "worksheet", "label": "Worksheet", "group": "structured", "desc": "Image on top + writing lines."},
    {"id": "workbook", "label": "Workbook Page", "group": "structured", "desc": "Title + image + lined section."},
    {"id": "activity", "label": "Activity Page", "group": "structured", "desc": "Title strip + framed art + lines."},
    {"id": "cut_paste", "label": "Cut-and-Paste", "group": "structured", "desc": "Dashed cut borders + prompt."},
]
LAYOUT_IDS = {l["id"] for l in LAYOUTS}


def decode_artwork(data, mime=""):
    """Decode PNG/JPG/WebP via PIL, or rasterize SVG (cairosvg) at high DPI. Returns an RGB(A) PIL image."""
    from PIL import Image
    head = data[:256].lstrip()[:64].lower()
    is_svg = b"<svg" in head or "svg" in (mime or "").lower()
    if is_svg:
        import cairosvg
        png = cairosvg.svg2png(bytestring=data, output_width=2550, output_height=3300)
        return Image.open(io.BytesIO(png)).convert("RGBA")
    im = Image.open(io.BytesIO(data)); im.load()
    return im


def _flatten(im):
    from PIL import Image
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, _WHITE); bg.paste(im, mask=im.split()[-1]); return bg
    return im.convert("RGB")


def _effective_dpi(orig_w, orig_h, placed_w_px, placed_h_px):
    printed_w_in = max(placed_w_px / DEFAULT_DPI, 0.01)
    printed_h_in = max(placed_h_px / DEFAULT_DPI, 0.01)
    return round(min(orig_w / printed_w_in, orig_h / printed_h_in))


def _place(im, box_w, box_h, fit_mode, custom_scale=100):
    """Return a resized image + its (w,h) for the given fit mode. Never distorts."""
    from PIL import Image
    ow, oh = im.width, im.height
    if fit_mode == "fill":  # cover: scale up so it covers the box, then center-crop
        ratio = max(box_w / ow, box_h / oh)
        nw, nh = max(int(round(ow * ratio)), 1), max(int(round(oh * ratio)), 1)
        scaled = im.resize((nw, nh), Image.LANCZOS)
        left, top = (nw - box_w) // 2, (nh - box_h) // 2
        return scaled.crop((left, top, left + box_w, top + box_h)), (ow, oh)
    if fit_mode == "original":  # native px at 300 DPI, capped to box (never upscale)
        ratio = min(box_w / ow, box_h / oh, 1.0)
        nw, nh = max(int(round(ow * ratio)), 1), max(int(round(oh * ratio)), 1)
        return im.resize((nw, nh), Image.LANCZOS), (ow, oh)
    # fit (contain) — optionally scaled by custom %
    ratio = min(box_w / ow, box_h / oh)
    if fit_mode == "custom":
        ratio *= max(min(custom_scale, 400), 5) / 100.0
    nw, nh = max(int(round(ow * ratio)), 1), max(int(round(oh * ratio)), 1)
    return im.resize((nw, nh), Image.LANCZOS), (ow, oh)


def render_page(artwork, *, layout="poster", page_size_px, margin_px, custom_scale=100,
                palette=None, page_no=1, title="", flatten_bg=_WHITE):
    """Render a single content page. `artwork` is a decoded PIL image. Returns (canvas, meta)."""
    from PIL import Image, ImageDraw
    pw, ph = page_size_px
    im = _flatten(artwork)
    orig_w, orig_h = im.width, im.height
    canvas = Image.new("RGB", (pw, ph), _WHITE)
    d = ImageDraw.Draw(canvas)
    accent = (palette or {}).get("accent", (200, 160, 40))
    top_c = (palette or {}).get("top", (36, 30, 90))
    m = margin_px

    def footer():
        d.text((pw // 2, ph - int(0.20 * DEFAULT_DPI)), f"QRU PRESS™  ·  {page_no}",
                font=dl._f(dl.SANS, 24), fill=(120, 120, 130), anchor="mm")

    def paste_centered(placed, box_l, box_t, box_w, box_h):
        x = box_l + (box_w - placed.width) // 2
        y = box_t + (box_h - placed.height) // 2
        canvas.paste(placed, (x, y))
        return placed.width, placed.height

    # ---- Image-forward layouts ----
    if layout in ("poster", "fill", "original", "custom_scale"):
        fit = {"poster": "fit", "fill": "fill", "original": "original", "custom_scale": "custom"}[layout]
        box_l, box_t, box_w, box_h = m, m, pw - 2 * m, ph - 2 * m
        placed, _ = _place(im, box_w, box_h, fit, custom_scale)
        pw_px, ph_px = paste_centered(placed, box_l, box_t, box_w, box_h)
        eff = _effective_dpi(orig_w, orig_h, pw_px, ph_px)

    elif layout == "coloring":
        box_l, box_t, box_w, box_h = m, m, pw - 2 * m, ph - 2 * m
        placed, _ = _place(im, box_w, box_h, "fit")
        pw_px, ph_px = paste_centered(placed, box_l, box_t, box_w, box_h)
        x = box_l + (box_w - pw_px) // 2; y = box_t + (box_h - ph_px) // 2
        d.rectangle([x - 8, y - 8, x + pw_px + 8, y + ph_px + 8], outline=(180, 180, 190), width=3)
        eff = _effective_dpi(orig_w, orig_h, pw_px, ph_px)

    elif layout == "bordered":
        d.rectangle([m, m, pw - m, ph - m], outline=accent, width=14)
        d.rectangle([m + 30, m + 30, pw - m - 30, ph - m - 30], outline=top_c, width=4)
        inset = m + 70
        box_l, box_t, box_w, box_h = inset, inset, pw - 2 * inset, ph - 2 * inset
        placed, _ = _place(im, box_w, box_h, "fit")
        pw_px, ph_px = paste_centered(placed, box_l, box_t, box_w, box_h)
        eff = _effective_dpi(orig_w, orig_h, pw_px, ph_px)

    elif layout == "book_illustration":
        big = int(0.9 * DEFAULT_DPI)  # generous picture-book margins
        box_l, box_t, box_w, box_h = big, big, pw - 2 * big, ph - int(1.6 * DEFAULT_DPI)
        placed, _ = _place(im, box_w, box_h, "fit")
        pw_px, ph_px = paste_centered(placed, box_l, box_t, box_w, box_h)
        d.line([(big, ph - int(0.7 * DEFAULT_DPI)), (pw - big, ph - int(0.7 * DEFAULT_DPI))], fill=(210, 210, 220), width=3)
        footer(); eff = _effective_dpi(orig_w, orig_h, pw_px, ph_px)

    # ---- Structured (teaching furniture) layouts ----
    elif layout in ("worksheet", "workbook"):
        strip_h = 0
        if layout == "workbook":
            strip_h = int(1.0 * DEFAULT_DPI)
            d.rectangle([0, 0, pw, strip_h], fill=top_c)
            d.rectangle([0, strip_h - 10, pw, strip_h], fill=accent)
            d.text((pw // 2, strip_h // 2), (title or "Workbook")[:48], font=dl._f(dl.SERIF_BOLD, 56), fill=_WHITE, anchor="mm")
        art_top = (strip_h + int(0.2 * DEFAULT_DPI)) if strip_h else m
        art_bottom = int(ph * 0.55)
        box_l, box_w = m, pw - 2 * m
        placed, _ = _place(im, box_w, art_bottom - art_top, "fit")
        pw_px, ph_px = paste_centered(placed, box_l, art_top, box_w, art_bottom - art_top)
        py = art_bottom + int(0.35 * DEFAULT_DPI)
        d.text((m, py), "Your turn:", font=dl._f(dl.SANS_BOLD, 42), fill=top_c)
        _lines(d, m, py + int(0.55 * DEFAULT_DPI), pw - m, ph - int(0.45 * DEFAULT_DPI))
        footer(); eff = _effective_dpi(orig_w, orig_h, pw_px, ph_px)

    elif layout == "activity":
        strip_h = int(1.0 * DEFAULT_DPI)
        d.rectangle([0, 0, pw, strip_h], fill=top_c)
        d.rectangle([0, strip_h - 10, pw, strip_h], fill=accent)
        d.text((pw // 2, strip_h // 2), (title or "Activity")[:48], font=dl._f(dl.SERIF_BOLD, 56), fill=_WHITE, anchor="mm")
        art_top = strip_h + int(0.2 * DEFAULT_DPI); art_bottom = int(ph * 0.60)
        box_l, box_w = m, pw - 2 * m
        placed, _ = _place(im, box_w, art_bottom - art_top, "fit")
        pw_px, ph_px = paste_centered(placed, box_l, art_top, box_w, art_bottom - art_top)
        x = box_l + (box_w - pw_px) // 2
        d.rectangle([x - 6, art_top + (art_bottom - art_top - ph_px) // 2 - 6,
                     x + pw_px + 6, art_top + (art_bottom - art_top - ph_px) // 2 + ph_px + 6], outline=accent, width=5)
        py = art_bottom + int(0.3 * DEFAULT_DPI)
        d.text((m, py), "Your turn:", font=dl._f(dl.SANS_BOLD, 42), fill=top_c)
        _lines(d, m, py + int(0.55 * DEFAULT_DPI), pw - m, ph - int(0.45 * DEFAULT_DPI))
        footer(); eff = _effective_dpi(orig_w, orig_h, pw_px, ph_px)

    elif layout == "cut_paste":
        d.text((m, m), "Cut along the dashed lines:", font=dl._f(dl.SANS_BOLD, 40), fill=top_c)
        box_l, box_t = m, m + int(0.6 * DEFAULT_DPI)
        box_w, box_h = pw - 2 * m, ph - box_t - m
        placed, _ = _place(im, box_w - 40, box_h - 40, "fit")
        pw_px, ph_px = paste_centered(placed, box_l, box_t, box_w, box_h)
        x = box_l + (box_w - pw_px) // 2; y = box_t + (box_h - ph_px) // 2
        _dashed_rect(d, x - 24, y - 24, x + pw_px + 24, y + ph_px + 24, accent)
        eff = _effective_dpi(orig_w, orig_h, pw_px, ph_px)

    else:
        raise ValueError(f"Unknown layout '{layout}'.")

    status = "CLEAN" if eff >= 300 else ("ACCEPTABLE" if eff >= 150 else "LOW_RES")
    return canvas, {"page": page_no, "type": f"layout_{layout}", "layout": layout,
                    "effective_dpi": eff, "status": status, "source_px": [orig_w, orig_h]}


def _lines(d, l, top, r, bottom, gap_in=0.5):
    y = top; gap = int(gap_in * DEFAULT_DPI)
    while y < bottom:
        d.line([(l, y), (r, y)], fill=(205, 205, 215), width=3); y += gap


def _dashed_rect(d, x0, y0, x1, y1, color, dash=26, w=4):
    def hline(y):
        x = x0
        while x < x1:
            d.line([(x, y), (min(x + dash, x1), y)], fill=color, width=w); x += dash * 2

    def vline(x):
        y = y0
        while y < y1:
            d.line([(x, y), (x, min(y + dash, y1))], fill=color, width=w); y += dash * 2
    hline(y0); hline(y1); vline(x0); vline(x1)
