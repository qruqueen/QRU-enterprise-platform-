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

_FONT_DIR = "/usr/share/fonts/truetype/liberation/"
SERIF_BOLD = _FONT_DIR + "LiberationSerif-Bold.ttf"
SERIF = _FONT_DIR + "LiberationSerif-Regular.ttf"
SANS_BOLD = _FONT_DIR + "LiberationSans-Bold.ttf"
SANS = _FONT_DIR + "LiberationSans-Regular.ttf"


def _f(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
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


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fit_title(draw, text, max_w, max_lines, start=88, min_size=44):
    size = start
    while size >= min_size:
        font = _f(SERIF_BOLD, size)
        lines = _wrap(draw, text, font, max_w)
        if len(lines) <= max_lines:
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

    # Title
    title = p.get("title") or "Understanding"
    font, lines, size = _fit_title(d, title, W - 200, 5)
    y = 620
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

