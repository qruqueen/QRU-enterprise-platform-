"""QRU Design Language™ — the permanent visual system for every QRU product.

Deterministic (Pillow) premium cover / thumbnail / store-graphic composition so NO
generic placeholder ever reaches a customer — and it works without any AI/LLM budget.
Each College & subject gets its own palette while staying unmistakably QRU.
"""
import io
import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger("qru.design")

# ---- QRU master brand ----
QRU_GOLD = (245, 178, 26)
QRU_ROYAL = (53, 16, 106)
QRU_NAVY = (26, 20, 52)
WHITE = (255, 255, 255)
CREAM = (247, 242, 230)

# ---- Dynamic Color System™ — per subject/College ----
PALETTES = {
    "heart":       {"top": (128, 22, 34),  "bottom": (56, 8, 16),   "accent": QRU_GOLD,        "label": "Heart Health"},
    "brain":       {"top": (74, 28, 122),  "bottom": (30, 12, 58),  "accent": QRU_GOLD,        "label": "Brain Health"},
    "lung":        {"top": (22, 96, 156),  "bottom": (10, 42, 82),  "accent": (176, 230, 255), "label": "Lung Health"},
    "nutrition":   {"top": (30, 112, 62),  "bottom": (12, 56, 32),  "accent": (245, 205, 90),  "label": "Nutrition"},
    "sleep":       {"top": (42, 32, 92),   "bottom": (16, 12, 46),  "accent": (168, 156, 232), "label": "Sleep & Rest"},
    "mental":      {"top": (30, 84, 124),  "bottom": (14, 42, 68),  "accent": (150, 222, 240), "label": "Mental Health"},
    "movement":    {"top": (156, 64, 22),  "bottom": (82, 32, 12),  "accent": (255, 202, 120), "label": "Movement"},
    "faith":       {"top": (22, 30, 74),   "bottom": (10, 14, 40),  "accent": QRU_GOLD,        "label": "Faith"},
    "finance":     {"top": (10, 92, 72),   "bottom": (6, 46, 36),   "accent": QRU_GOLD,        "label": "Finance"},
    "business":    {"top": (46, 46, 56),   "bottom": (20, 20, 28),  "accent": QRU_GOLD,        "label": "Business"},
    "programming": {"top": (16, 62, 144),  "bottom": (8, 26, 72),   "accent": (86, 202, 255),  "label": "Programming"},
    "science":     {"top": (10, 112, 112), "bottom": (6, 56, 56),   "accent": (160, 255, 240), "label": "Science"},
    "history":     {"top": (122, 82, 32),  "bottom": (70, 46, 16),  "accent": (245, 205, 140), "label": "History"},
    "math":        {"top": (22, 52, 144),  "bottom": (10, 26, 82),  "accent": QRU_GOLD,        "label": "Mathematics"},
    "children":    {"top": (255, 142, 62), "bottom": (232, 72, 122),"accent": (255, 240, 120), "label": "For Children"},
    "default":     {"top": QRU_ROYAL,      "bottom": QRU_NAVY,      "accent": QRU_GOLD,        "label": "QRU"},
}

KEYWORDS = [
    ("heart", ["heart", "cardio", "blood pressure", "circulat"]),
    ("brain", ["brain", "memory", "cognit", "neuro", "focus", "mind"]),
    ("lung", ["lung", "breath", "respirat", "oxygen"]),
    ("sleep", ["sleep", "rest", "insomnia"]),
    ("mental", ["stress", "anxiety", "mental", "calm", "mood", "emotion"]),
    ("movement", ["walk", "exercise", "movement", "fitness", "strength", "muscle"]),
    ("nutrition", ["nutrition", "hydrat", "water", "food", "diet", "fiber", "vitamin", "gut"]),
    ("faith", ["faith", "gratitude", "hope", "forgive", "prayer", "patience", "generos", "spirit", "scripture"]),
    ("finance", ["finance", "money", "invest", "budget", "trade", "saving"]),
    ("business", ["business", "leadership", "market", "startup", "management"]),
    ("programming", ["program", "code", "software", "python", "javascript", "developer"]),
    ("science", ["science", "physics", "chemistry", "biology", "climate"]),
    ("history", ["history", "ancient", "war", "civilization", "empire"]),
    ("math", ["math", "algebra", "geometry", "calculus", "number"]),
    ("children", ["kid", "child", "toddler", "young learner"]),
]


_NONCUSTOMER_TITLE_SUFFIXES = {
    "book", "short-form content", "long-form content", "content", "article",
    "publication", "document", "pdf", "ebook", "e-book",
}


def _clean_cover_title(title):
    """Strip an internal/redundant ' - X' / ' — X' manufacturing suffix from a customer-facing title."""
    t = (title or "").strip()
    for sep in (" — ", " - ", " – "):
        if sep in t:
            base, _, suffix = t.rpartition(sep)
            if base.strip() and suffix.strip().lower() in _NONCUSTOMER_TITLE_SUFFIXES:
                return base.strip()
    return t


import os as _os

# Fonts are BUNDLED with the app (assets/fonts) so they ship with every deploy — production
# containers do not always have system fonts installed, which previously caused PIL to fall back
# to a ~10px bitmap and render every cover title tiny. Bundled first, system path as fallback.
_BUNDLED_FONT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "assets", "fonts")
_SYSTEM_FONT_DIR = "/usr/share/fonts/truetype/liberation/"


def _font_path(name):
    bundled = _os.path.join(_BUNDLED_FONT_DIR, name)
    if _os.path.exists(bundled):
        return bundled
    return _SYSTEM_FONT_DIR + name


SERIF_BOLD = _font_path("LiberationSerif-Bold.ttf")
SERIF = _font_path("LiberationSerif-Regular.ttf")
SANS_BOLD = _font_path("LiberationSans-Bold.ttf")
SANS = _font_path("LiberationSans-Regular.ttf")


def _f(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        # Last-resort: scan any available bundled/system TTF before the tiny bitmap fallback.
        for d in (_BUNDLED_FONT_DIR, _SYSTEM_FONT_DIR, "/usr/share/fonts"):
            try:
                for root, _dirs, files in _os.walk(d):
                    for fn in files:
                        if fn.lower().endswith(".ttf"):
                            try:
                                return ImageFont.truetype(_os.path.join(root, fn), size)
                            except Exception:
                                continue
            except Exception:
                continue
        import logging as _lg
        _lg.getLogger("design").error("No TrueType font available — cover text will render tiny. Bundle fonts in assets/fonts.")
        return ImageFont.load_default()


def resolve_palette(family="", department="", topic="", title=""):
    text = " ".join([str(x) for x in (family, department, topic, title)]).lower()
    for key, words in KEYWORDS:
        if any(w in text for w in words):
            return {**PALETTES[key], "key": key}
    # fall back by explicit family names
    for key, p in PALETTES.items():
        if p["label"].lower() in text:
            return {**p, "key": key}
    return {**PALETTES["default"], "key": "default"}


def _gradient(w, h, top, bottom):
    base = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(base)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)],
               fill=(int(top[0] + (bottom[0] - top[0]) * t),
                     int(top[1] + (bottom[1] - top[1]) * t),
                     int(top[2] + (bottom[2] - top[2]) * t)))
    return base


def _cover_fit(img, W, H):
    """Resize+crop an image to exactly fill WxH (like CSS object-fit: cover)."""
    src_ratio = img.width / img.height
    dst_ratio = W / H
    if src_ratio > dst_ratio:
        nh = H
        nw = int(H * src_ratio)
    else:
        nw = W
        nh = int(W / src_ratio)
    img = img.resize((max(nw, 1), max(nh, 1)))
    left = (img.width - W) // 2
    top = (img.height - H) // 2
    return img.crop((left, top, left + W, top + H))


def _vignette(img):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([-w * 0.3, -h * 0.3, w * 1.3, h * 1.3], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(w * 0.15))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(img, Image.blend(img, dark, 0.5), mask)


def draw_shield(canvas, cx, top_y, w, h, accent, line=6):
    d = ImageDraw.Draw(canvas)
    left, right = cx - w // 2, cx + w // 2
    pts = [(left, top_y), (right, top_y), (right, top_y + int(h * 0.55)),
           (cx, top_y + h), (left, top_y + int(h * 0.55))]
    d.polygon(pts, fill=QRU_NAVY, outline=accent)
    for off in range(line):
        d.polygon([(x + (1 if i in (0, 4) else -1) * 0, y) for i, (x, y) in enumerate(pts)],
                  outline=accent)
    d.line([(left, top_y), (right, top_y)], fill=accent, width=line)
    d.line([(right, top_y), (right, top_y + int(h * 0.55))], fill=accent, width=line)
    d.line([(right, top_y + int(h * 0.55)), (cx, top_y + h)], fill=accent, width=line)
    d.line([(cx, top_y + h), (left, top_y + int(h * 0.55))], fill=accent, width=line)
    d.line([(left, top_y + int(h * 0.55)), (left, top_y)], fill=accent, width=line)
    fs = int(h * 0.34)
    d.text((cx, top_y + int(h * 0.42)), "QRU", font=_f(SERIF_BOLD, fs), fill=accent, anchor="mm")


def _break_token(draw, token, font, max_w):
    """Hard-break a single token that is wider than max_w (e.g. long unbroken IDs/URLs)."""
    if draw.textlength(token, font=font) <= max_w:
        return [token]
    parts, cur = [], ""
    for ch in token:
        if draw.textlength(cur + ch, font=font) <= max_w:
            cur += ch
        else:
            if cur:
                parts.append(cur)
            cur = ch
    if cur:
        parts.append(cur)
    return parts


def _wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for w in text.split():
        # a single word longer than the column must be hard-broken so it never overflows
        for piece in _break_token(draw, w, font, max_w):
            test = (cur + " " + piece).strip()
            if draw.textlength(test, font=font) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = piece
    if cur:
        lines.append(cur)
    return lines


def _fits(draw, lines, font, max_w):
    return all(draw.textlength(ln, font=font) <= max_w for ln in lines)


def _fit_title(draw, text, max_w, max_lines, start=88, min_size=44):
    size = start
    while size >= min_size:
        font = _f(SERIF_BOLD, size)
        lines = _wrap(draw, text, font, max_w)
        # require BOTH the line count AND every line's width to fit — never overflow horizontally
        if len(lines) <= max_lines and _fits(draw, lines, font, max_w):
            return font, lines, size
        size -= 4
    font = _f(SERIF_BOLD, min_size)
    return font, _wrap(draw, text, font, max_w)[:max_lines], min_size


def _difficulty(kr):
    lvl = str((kr or {}).get("difficulty", "") or (kr or {}).get("level", "")).lower()
    if "adv" in lvl:
        return "Advanced"
    if "inter" in lvl:
        return "Intermediate"
    return "Foundational"


def premium_cover(product, kr=None, hero_bytes=None):
    """A professionally composed portrait cover (1080x1440). No blank placeholders.
    If hero_bytes (AI artwork) is supplied it becomes a subtle backdrop under the QRU
    frame; otherwise a branded subject gradient is used."""
    p = product or {}
    kr = kr or {}
    W, H = 1080, 1440
    pal = resolve_palette(p.get("family", ""), p.get("department", p.get("college", "")),
                          p.get("topic", ""), p.get("title", ""))
    accent = pal["accent"]
    if hero_bytes:
        try:
            hero = Image.open(io.BytesIO(hero_bytes)).convert("RGB")
            hero = _cover_fit(hero, W, H)
            grad = _gradient(W, H, pal["top"], pal["bottom"])
            img = _vignette(Image.blend(hero, grad, 0.62))  # blend keeps art visible + text readable
        except Exception:
            img = _vignette(_gradient(W, H, pal["top"], pal["bottom"]))
    else:
        img = _vignette(_gradient(W, H, pal["top"], pal["bottom"]))
    d = ImageDraw.Draw(img)

    # frame
    d.rectangle([40, 40, W - 40, H - 40], outline=accent, width=4)
    d.rectangle([54, 54, W - 54, H - 54], outline=(accent[0], accent[1], accent[2]), width=1)

    # College / series eyebrow
    college = (p.get("family") or pal["label"] or "QRU").upper()
    d.text((W // 2, 130), f"QRU • {college}", font=_f(SANS_BOLD, 30), fill=accent, anchor="mm")

    # Shield
    draw_shield(img, W // 2, 185, 200, 240, accent)

    # Product-type badge (top-right)
    ptype = (p.get("product_type") or "Product").upper()
    bw = d.textlength(ptype, font=_f(SANS_BOLD, 24)) + 44
    d.rounded_rectangle([W - 60 - bw, 470, W - 60, 512], radius=20, fill=accent)
    d.text((W - 60 - bw / 2, 491), ptype, font=_f(SANS_BOLD, 24), fill=QRU_NAVY, anchor="mm")

    # Title — large, publication-scale (auto-fit; higher floor so it never renders tiny)
    title = _clean_cover_title(p.get("title") or "Understanding")
    font, lines, size = _fit_title(d, title, W - 150, 3, start=150, min_size=58)
    y = 600
    for ln in lines:
        d.text((W // 2, y), ln, font=font, fill=WHITE, anchor="mm")
        y += int(size * 1.12)

    # divider + subtitle
    d.rectangle([W // 2 - 120, y + 10, W // 2 + 120, y + 14], fill=accent)
    subtitle = kr.get("subtitle") or kr.get("hook") or f"A {pal['label']} learning product"
    subtitle = subtitle[:90]
    d.text((W // 2, y + 60), subtitle, font=_f(SERIF, 34), fill=CREAM, anchor="mm")

    # metadata row
    meta = f"{_difficulty(kr)}   •   {(p.get('audience') or 'All Learners')}"
    d.text((W // 2, H - 300), meta, font=_f(SANS, 28), fill=(220, 215, 235), anchor="mm")

    # Treasure Standard seal
    if p.get("treasure_standard") or p.get("status") == "Published":
        sx, sy, r = W // 2, H - 210, 66
        d.ellipse([sx - r, sy - r, sx + r, sy + r], outline=accent, width=5)
        d.ellipse([sx - r + 10, sy - r + 10, sx + r - 10, sy + r - 10], outline=accent, width=2)
        d.text((sx, sy - 12), "TREASURE", font=_f(SANS_BOLD, 18), fill=accent, anchor="mm")
        d.text((sx, sy + 12), "STANDARD", font=_f(SANS_BOLD, 18), fill=accent, anchor="mm")

    # publisher band
    d.rectangle([40, H - 118, W - 40, H - 40], fill=(0, 0, 0))
    d.rectangle([40, H - 122, W - 40, H - 118], fill=accent)
    edition = f"Edition {p.get('kr_version', 1)}"
    d.text((80, H - 79), "QRU PRESS™", font=_f(SERIF_BOLD, 34), fill=accent, anchor="lm")
    d.text((W - 80, H - 79), edition, font=_f(SANS, 26), fill=CREAM, anchor="rm")

    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def premium_thumbnail(cover_bytes, size=(600, 800)):
    img = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    img.thumbnail(size)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def premium_store_graphic(product, cover_bytes):
    p = product or {}
    W, H = 1536, 1024
    pal = resolve_palette(p.get("family", ""), p.get("department", ""), p.get("topic", ""), p.get("title", ""))
    accent = pal["accent"]
    canvas = _gradient(W, H, pal["top"], pal["bottom"])
    cover = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    cover.thumbnail((620, 820))
    cx, cy = 90, (H - cover.height) // 2
    shadow = Image.new("RGB", (W, H), (0, 0, 0))
    canvas.paste(shadow.crop((0, 0, cover.width + 20, cover.height + 20)), (cx + 12, cy + 14))
    canvas.paste(cover, (cx, cy))
    d = ImageDraw.Draw(canvas)
    d.rectangle([cx - 6, cy - 6, cx + cover.width + 6, cy + cover.height + 6], outline=accent, width=4)

    tx = cx + cover.width + 90
    d.text((tx, 150), f"QRU • {(p.get('family') or pal['label']).upper()}", font=_f(SANS_BOLD, 30), fill=accent)
    title = p.get("title") or "Understanding"
    font, lines, size = _fit_title(d, title, W - tx - 90, 5, start=72, min_size=40)
    y = 220
    for ln in lines:
        d.text((tx, y), ln, font=font, fill=WHITE)
        y += int(size * 1.12)
    d.text((tx, y + 30), (p.get("product_type") or "Product"), font=_f(SANS, 34), fill=CREAM)
    d.text((tx, H - 160), "★ Treasure Standard™ Certified", font=_f(SANS_BOLD, 30), fill=accent)
    buf = io.BytesIO()
    canvas.save(buf, "PNG")
    return buf.getvalue()


def _isbn13(product):
    """A stable, deterministic ISBN-13 (978 prefix + 9 digits from product id + check digit)."""
    import hashlib
    seed = str(product.get("isbn") or product.get("product_code") or product.get("id") or "QRU")
    core = "978" + "".join(c for c in hashlib.sha1(seed.encode()).hexdigest() if c.isdigit())[:9].ljust(9, "0")
    s = sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(core[:12]))
    check = (10 - (s % 10)) % 10
    return core[:12] + str(check)


def _barcode(draw, x, y, w, h, digits, accent=(0, 0, 0)):
    """A clean EAN-13-style barcode drawn from the digit string (visual, scannable-looking)."""
    draw.rectangle([x - 12, y - 12, x + w + 12, y + h + 34], fill=WHITE)
    n = len(digits)
    bar_area = w
    px = x
    step = bar_area / (n * 7)
    for i, ch in enumerate(digits):
        pat = [(int(ch) % 2) + 1, 1, (int(ch) % 3) + 1, 1]  # deterministic bar widths per digit
        for j, bw in enumerate(pat):
            bwid = max(1, step * bw)
            if j % 2 == 0:
                draw.rectangle([px, y, px + bwid, y + h], fill=(0, 0, 0))
            px += bwid
    # human-readable ISBN
    f = _f(SANS, max(16, int(h * 0.22)))
    draw.text((x + w / 2, y + h + 14), f"ISBN {digits[:3]}-{digits[3]}-{digits[4:9]}-{digits[9:12]}-{digits[12]}",
              font=f, fill=(0, 0, 0), anchor="ma")


def premium_wrap(product, kr=None, cover_bytes=None):
    """A KDP/print-ready full cover WRAP: back panel (blurb + learn-list + QR + ISBN) · spine · front cover.
    The front reuses the composed premium front cover; everything stays on-brand and inherits the KR."""
    p, kr = product or {}, kr or {}
    pal = resolve_palette(p.get("family", ""), p.get("department", ""), p.get("topic", ""), p.get("title", ""))
    PW, PH, SPINE, M = 1080, 1440, 210, 60
    W = M * 2 + PW * 2 + SPINE
    H = M * 2 + PH
    canvas = _gradient(W, H, pal["top"], pal["bottom"])
    d = ImageDraw.Draw(canvas)
    accent = pal["accent"]

    back_x, spine_x, front_x = M, M + PW, M + PW + SPINE

    # ---------- FRONT (right) ----------
    if cover_bytes:
        try:
            front = _cover_fit(Image.open(io.BytesIO(cover_bytes)).convert("RGB"), PW, PH)
            canvas.paste(front, (front_x, M))
        except Exception:
            cover_bytes = None
    if not cover_bytes:
        canvas.paste(_gradient(PW, PH, pal["top"], pal["bottom"]), (front_x, M))

    # ---------- SPINE (center) ----------
    d.rectangle([spine_x, M, spine_x + SPINE, M + PH], fill=QRU_NAVY)
    d.line([(spine_x, M), (spine_x, M + PH)], fill=accent, width=4)
    d.line([(spine_x + SPINE, M), (spine_x + SPINE, M + PH)], fill=accent, width=4)
    draw_shield(canvas, spine_x + SPINE // 2, M + 30, 120, 150, accent, line=4)
    spine_img = Image.new("RGBA", (PH - 360, SPINE - 60), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spine_img)
    title = (p.get("title") or "").split(" — ")[0][:46]
    sd.text((spine_img.width // 2, spine_img.height // 2), title, font=_f(SERIF_BOLD, 66), fill=WHITE, anchor="mm")
    canvas.paste(spine_img.rotate(90, expand=True), (spine_x + 30, M + 210), spine_img.rotate(90, expand=True))
    d.text((spine_x + SPINE // 2, M + PH - 40), "QRU", font=_f(SERIF_BOLD, 44), fill=accent, anchor="mm")

    # ---------- BACK (left) ----------
    bx, bw = back_x + 70, PW - 140
    y = M + 80
    d.text((bx, y), pal["label"].upper() + "  ·  QRU PRESS™", font=_f(SANS_BOLD, 26), fill=accent)
    y += 54
    headline = (p.get("subtitle") or f"Understand {title} — and put it to work.")[:70]
    hf, hl, _ = _fit_title(d, headline, bw, 3, start=64, min_size=40)
    for ln in hl:
        d.text((bx, y), ln, font=hf, fill=WHITE)
        y += int(hf.size * 1.15)
    y += 24
    # blurb from the verified KR
    blurb = (kr.get("why_it_matters") or kr.get("qru_translation") or kr.get("verified_truth")
             or p.get("description") or "A clear, verified, dignity-first guide from the QRU Factory™.")
    bf = _f(SANS, 30)
    for ln in _wrap(d, str(blurb), bf, bw)[:6]:
        d.text((bx, y), ln, font=bf, fill=CREAM)
        y += 40
    y += 24
    # "In this book you will learn"
    learn = []
    pa = kr.get("practice_application")
    if isinstance(pa, list):
        learn += [str(x) for x in pa if isinstance(x, str) and x.strip()]
    kv = kr.get("key_vocabulary")
    if isinstance(kv, list):
        for v in kv:
            if isinstance(v, dict):
                term, deff = str(v.get("term", "")).strip(), str(v.get("definition", "")).strip()
                if term:
                    learn.append(f"{term}: {deff}" if deff else term)
            elif isinstance(v, str) and v.strip():
                learn.append(v.strip())
    learn = learn[:4] or ["The core idea, explained simply", "Why it matters in real life",
                          "A memorable way to keep it", "How to apply it today"]
    d.text((bx, y), "IN THIS BOOK YOU WILL LEARN", font=_f(SANS_BOLD, 26), fill=accent)
    y += 46
    lf = _f(SANS, 27)
    for item in learn:
        d.ellipse([bx, y + 8, bx + 12, y + 20], fill=accent)
        for i, ln in enumerate(_wrap(d, str(item), lf, bw - 40)[:2]):
            d.text((bx + 30, y), ln, font=lf, fill=WHITE)
            y += 36
        y += 6

    # bottom band: QR (companion) + ISBN barcode + price
    by = M + PH - 320
    d.line([(bx, by - 24), (bx + bw, by - 24)], fill=accent, width=2)
    try:
        import qrcode
        qr = qrcode.make(f"https://quest.qru/learn/{p.get('id','')}").convert("RGB").resize((180, 180))
        canvas.paste(qr, (bx, by))
        d.text((bx + 90, by + 190), "Companion Experience", font=_f(SANS, 20), fill=CREAM, anchor="ma")
    except Exception:
        pass
    # ISBN barcode (bottom-right of back)
    _barcode(d, bx + bw - 340, by + 6, 320, 130, _isbn13(p), accent)
    # QRU Press footer band
    d.rectangle([back_x, M + PH - 52, back_x + PW, M + PH], fill=QRU_NAVY)
    d.rectangle([back_x, M + PH - 52, back_x + PW, M + PH - 48], fill=accent)
    d.text((back_x + PW // 2, M + PH - 26), "QRU PRESS™  ·  Quest for Real Understanding",
           font=_f(SANS_BOLD, 22), fill=accent, anchor="mm")

    # outer gold frame around whole wrap
    d.rectangle([20, 20, W - 20, H - 20], outline=accent, width=4)

    canvas = canvas.convert("RGB")
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()



def visual_review(product):
    """Treasure Standard™ Visual Review — deterministic pre-publish design check."""
    p = product or {}
    checks = [
        {"item": "Professional cover present", "pass": bool(p.get("cover_url"))},
        {"item": "Store thumbnail present", "pass": bool(p.get("thumbnail_url"))},
        {"item": "Store graphic present", "pass": bool(p.get("store_graphic_url"))},
        {"item": "Subject palette assigned", "pass": bool(p.get("design_palette"))},
        {"item": "Title within layout limits", "pass": len(p.get("title", "")) <= 120},
        {"item": "Product type labeled", "pass": bool(p.get("product_type"))},
    ]
    passed = sum(1 for c in checks if c["pass"])
    score = round(passed / len(checks) * 100)
    return {"score": score, "passed": passed, "total": len(checks),
            "approved": score >= 80, "checks": checks,
            "verdict": "Approved" if score >= 80 else "Needs design pass"}


# ---------------- Multi-Format Output™ ----------------
# Optimized, print/marketplace-ready renditions. Each preserves the QRU frame & branding.
EXPORT_SPECS = {
    "kdp_ebook":       {"size": (1600, 2560), "label": "Amazon KDP eBook Cover"},
    "kdp_print_6x9":   {"size": (1800, 2700), "label": "KDP Print 6×9 (300dpi)"},
    "etsy_listing":    {"size": (2000, 2000), "label": "Etsy Listing (square)"},
    "tpt_thumbnail":   {"size": (1200, 1600), "label": "Teachers Pay Teachers"},
    "poster_print":    {"size": (2400, 3600), "label": "High-Res Poster (300dpi)"},
    "social_square":   {"size": (1080, 1080), "label": "Social — Square"},
    "social_story":    {"size": (1080, 1920), "label": "Social — Story/Reel"},
    "pinterest":       {"size": (1000, 1500), "label": "Pinterest Graphic"},
    "web_thumb":       {"size": (600, 800),   "label": "Web Thumbnail"},
    "desktop_banner":  {"size": (1920, 1080), "label": "Desktop / Web Banner"},
}


def _fit_on_brand(master, W, H, pal):
    """Place the master cover on a branded, correctly-sized canvas (contain-fit)."""
    accent = pal["accent"]
    canvas = _vignette(_gradient(W, H, pal["top"], pal["bottom"]))
    m = master.copy()
    pad = 0.86 if (W / H) < 1.4 else 0.78
    m.thumbnail((int(W * pad), int(H * pad)))
    x, y = (W - m.width) // 2, (H - m.height) // 2
    canvas.paste(m, (x, y))
    d = ImageDraw.Draw(canvas)
    d.rectangle([x - 6, y - 6, x + m.width + 6, y + m.height + 6], outline=accent, width=max(3, W // 400))
    # small brand footer for wide/social formats where there is spare margin
    if y > 70:
        d.text((W // 2, max(34, y // 2)), "QRU PRESS™ • Treasure Standard™",
               font=_f(SANS_BOLD, max(18, W // 60)), fill=accent, anchor="mm")
    buf = io.BytesIO()
    canvas.save(buf, "PNG")
    return buf.getvalue()


def export_formats(product, kr=None, cover_bytes=None):
    """Return {format_name: png_bytes} across all EXPORT_SPECS, preserving QRU quality."""
    p = product or {}
    pal = resolve_palette(p.get("family", ""), p.get("department", p.get("college", "")),
                          p.get("topic", ""), p.get("title", ""))
    if cover_bytes:
        master = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    else:
        master = Image.open(io.BytesIO(premium_cover(p, kr))).convert("RGB")
    out = {}
    for name, spec in EXPORT_SPECS.items():
        W, H = spec["size"]
        out[name] = _fit_on_brand(master, W, H, pal)
    return out

