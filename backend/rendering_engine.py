"""QRU Product Rendering Engine™ — transforms approved Understanding Assets™ into fully
branded, finished QRU products using Design Intelligence™: a branded cover (AI image),
thumbnail, QR code, print-ready PDF, and a store graphic.

No generic AI layouts are released — every rendered asset carries the QRU visual language.
"""
import os
import io
import re
import logging

from database import db
from models import now_iso, gen_id
from ai_service import generate_image
from org_activity import log_org
import design_intelligence as di
import design_language as dl

logger = logging.getLogger("qru.render")

ASSET_DIR = "/app/backend/rendered_assets"
os.makedirs(ASSET_DIR, exist_ok=True)

# QRU brand colors (RGB)
ROYAL = (53, 16, 106)
GOLD = (245, 178, 26)
NAVY = (34, 26, 66)
WHITE = (255, 255, 255)


def _save(name_prefix, ext, data: bytes):
    fid = f"{name_prefix}-{gen_id()[:8]}.{ext}"
    with open(os.path.join(ASSET_DIR, fid), "wb") as f:
        f.write(data)
    return fid


def _asset_url(fid):
    return f"/api/rendering/asset/{fid}" if fid else None


def _placeholder_cover(title, family, palette):
    """Deterministic branded cover if AI image generation is unavailable."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (1024, 1024), ROYAL)
    d = ImageDraw.Draw(img)
    for y in range(1024):
        t = y / 1024
        d.line([(0, y), (1024, y)], fill=(int(ROYAL[0] + (NAVY[0] - ROYAL[0]) * t),
                                          int(ROYAL[1] + (NAVY[1] - ROYAL[1]) * t),
                                          int(ROYAL[2] + (NAVY[2] - ROYAL[2]) * t)))
    d.ellipse([362, 200, 662, 500], outline=GOLD, width=10)
    d.text((512, 350), "QRU", fill=GOLD, anchor="mm")
    d.rectangle([100, 620, 924, 624], fill=GOLD)
    words = title.split()
    lines, cur = [], ""
    for w in words:
        if len(cur + " " + w) > 22:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    y = 680
    for ln in lines[:4]:
        d.text((512, y), ln, fill=WHITE, anchor="mm")
        y += 60
    d.text((512, 940), family.upper(), fill=GOLD, anchor="mm")
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


def _make_thumbnail(cover_bytes, size=(512, 512)):
    from PIL import Image
    img = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    img.thumbnail(size)
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


def _make_store_graphic(cover_bytes, title):
    """Compose a 1536x1024 store graphic: cover + gold-framed title panel."""
    from PIL import Image, ImageDraw
    canvas = Image.new("RGB", (1536, 1024), NAVY)
    cover = Image.open(io.BytesIO(cover_bytes)).convert("RGB").resize((820, 820))
    canvas.paste(cover, (80, 102))
    d = ImageDraw.Draw(canvas)
    d.rectangle([70, 92, 910, 932], outline=GOLD, width=8)
    d.text((980, 300), "QRU", fill=GOLD)
    words = title.split(); lines, cur = [], ""
    for w in words:
        if len(cur + " " + w) > 18:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    y = 380
    for ln in lines[:5]:
        d.text((980, y), ln, fill=WHITE); y += 46
    d.text((980, y + 30), "Treasure Standard\u2122 Certified", fill=GOLD)
    buf = io.BytesIO(); canvas.save(buf, "PNG")
    return buf.getvalue()


def _make_qr(url):
    import qrcode
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url); qr.make(fit=True)
    img = qr.make_image(fill_color="#35106A", back_color="white").convert("RGB")
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


def _strip_md(text):
    text = re.sub(r"[#*_`>]", "", text or "")
    text = text.replace("\u2122", "(TM)").replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u2013", "-").replace("\u2014", "-")
    return text.encode("latin-1", "replace").decode("latin-1")


def _make_pdf(product, kr, cover_bytes, qr_bytes):
    from fpdf import FPDF
    pdf = FPDF(format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(True, margin=18)
    # Cover page
    pdf.add_page()
    pdf.set_fill_color(*ROYAL); pdf.rect(0, 0, 210, 297, "F")
    cover_path = os.path.join(ASSET_DIR, _save("tmp-cover", "png", cover_bytes))
    pdf.image(cover_path, x=30, y=30, w=150)
    os.remove(cover_path)
    pdf.set_text_color(*GOLD); pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(15, 200); pdf.multi_cell(180, 10, _strip_md(product["title"]), align="C")
    pdf.set_text_color(255, 255, 255); pdf.set_font("Helvetica", "", 12)
    pdf.set_xy(15, 235); pdf.multi_cell(180, 8, _strip_md("Treasure Standard(TM) Certified  |  Kingdom Lion(TM) Verified"), align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(15, 248); pdf.multi_cell(180, 6, _strip_md(f"QRU {product.get('product_type','')}  -  {product.get('family','')}"), align="C")
    # Content page
    pdf.add_page(); pdf.set_text_color(*NAVY)
    body = product.get("content") or ""
    for block in body.split("\n"):
        b = _strip_md(block).strip()
        pdf.set_x(pdf.l_margin)
        if not b:
            pdf.ln(3); continue
        if block.startswith("## "):
            pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(*ROYAL)
            pdf.multi_cell(0, 8, b); pdf.set_text_color(*NAVY)
        elif block.startswith("# "):
            pdf.set_font("Helvetica", "B", 18); pdf.multi_cell(0, 10, b)
        else:
            pdf.set_font("Helvetica", "", 11); pdf.multi_cell(0, 6, b)
    # QR
    qr_path = os.path.join(ASSET_DIR, _save("tmp-qr", "png", qr_bytes))
    pdf.ln(6); pdf.set_x(pdf.l_margin); pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(*ROYAL)
    pdf.multi_cell(0, 6, "Continue learning at QRU:")
    pdf.image(qr_path, x=15, w=30); os.remove(qr_path)
    out = pdf.output()
    return bytes(out)


async def ensure_branded_assets(pid, actor="Creative Studio™"):
    """Guarantee every product carries the QRU Design Language™ — professional cover,
    thumbnail and store graphic. Fully deterministic (no AI budget required)."""
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    kr = await db.knowledge_records.find_one({"id": p.get("knowledge_record_id")}) if p.get("knowledge_record_id") else {}
    pal = dl.resolve_palette(p.get("family", ""), p.get("department", p.get("college", "")),
                             p.get("topic", ""), p.get("title", ""))
    # Best-effort AI hero artwork — composited under the QRU frame. Skips silently when
    # AI capacity is unavailable (daily cap / budget), so covers always render.
    hero = None
    try:
        prompt = (f"Elegant editorial illustration for an educational product about "
                  f"'{p.get('title','')}' ({p.get('family','')}). {pal['label']} theme, "
                  f"palette accent {'#%02X%02X%02X' % pal['accent']}, deep {pal['label']} tones, "
                  f"premium flat-vector style, atmospheric, NO text, portrait composition.")
        hero = await generate_image(prompt, f"hero-{pid}")
    except Exception:
        hero = None
    cover = dl.premium_cover(p, kr or {}, hero_bytes=hero)
    cover_url = _asset_url(_save("cover", "png", cover))
    thumb_url = _asset_url(_save("thumb", "png", dl.premium_thumbnail(cover)))
    store_url = _asset_url(_save("store", "png", dl.premium_store_graphic(p, cover)))
    await db.products.update_one({"id": pid}, {"$set": {
        "cover_url": cover_url, "thumbnail_url": thumb_url, "store_graphic_url": store_url,
        "design_palette": {"key": pal["key"], "label": pal["label"],
                           "accent": "#%02X%02X%02X" % pal["accent"]},
        "cover_has_hero_art": bool(hero),
        "design_language_applied": True, "updated_at": now_iso()}})
    await log_org("Creative Studio Director™", "Creative Studio",
                  f"applied QRU Design Language™ ({pal['label']}) to", p.get("product_code", ""), "success")
    return {"cover_url": cover_url, "thumbnail_url": thumb_url, "store_graphic_url": store_url, "palette": pal["label"]}


async def export_multi_format(pid, actor="Creative Studio™"):
    """Multi-Format Output™ — generate optimized KDP/Etsy/TpT/social/print renditions."""
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    kr = await db.knowledge_records.find_one({"id": p.get("knowledge_record_id")}) if p.get("knowledge_record_id") else {}
    # reuse the existing branded cover if present, else compose one
    cover_bytes = None
    cu = p.get("cover_url")
    if cu:
        path = os.path.join(ASSET_DIR, cu.split("/")[-1])
        if os.path.exists(path):
            with open(path, "rb") as f:
                cover_bytes = f.read()
    formats = dl.export_formats(p, kr or {}, cover_bytes)
    urls = {}
    for name, data in formats.items():
        urls[name] = {"url": _asset_url(_save(f"fmt-{name}", "png", data)),
                      "label": dl.EXPORT_SPECS[name]["label"],
                      "size": list(dl.EXPORT_SPECS[name]["size"])}
    await db.products.update_one({"id": pid}, {"$set": {"export_formats": urls, "updated_at": now_iso()}})
    await log_org("Creative Studio Director™", "Creative Studio",
                  f"exported {len(urls)} optimized formats for", p.get("product_code", ""), "success")
    return urls


async def render_product_job(pid, actor, base_url):
    p = await db.products.find_one({"id": pid})
    if not p:
        return
    await db.products.update_one({"id": pid}, {"$set": {"render_status": "rendering"}})
    await log_org("Creative Studio Director\u2122", "Creative Studio", "is rendering branded assets for", p.get("product_code", ""))
    kr = await db.knowledge_records.find_one({"id": p.get("knowledge_record_id")}) if p.get("knowledge_record_id") else None
    rec = di.recommend_templates(p.get("product_type", "Interactive Lesson"), p.get("audience", "General public"))

    # QRU Design Language™ cover — deterministic, consistent, premium (no AI dependency).
    cover = dl.premium_cover(p, kr or {})
    pal = dl.resolve_palette(p.get("family", ""), p.get("department", p.get("college", "")),
                             p.get("topic", ""), p.get("title", ""))

    assets = {}
    try:
        assets["cover"] = _asset_url(_save("cover", "png", cover))
        assets["thumbnail"] = _asset_url(_save("thumb", "png", dl.premium_thumbnail(cover)))
        assets["store_graphic"] = _asset_url(_save("store", "png", dl.premium_store_graphic(p, cover)))
        qr = _make_qr(f"{base_url}/learn/{pid}")
        assets["qr_code"] = _asset_url(_save("qr", "png", qr))
        assets["print_pdf"] = _asset_url(_save("product", "pdf", _make_pdf(p, kr, cover, qr)))
    except Exception as e:
        logger.error(f"asset composition failed: {e}")

    deliverables = p.get("deliverables", [])
    for dlv in deliverables:
        dlv["status"] = "rendered"
    await db.products.update_one({"id": pid}, {"$set": {
        "rendered_assets": assets, "render_status": "rendered", "cover_url": assets.get("cover"),
        "thumbnail_url": assets.get("thumbnail"), "store_graphic_url": assets.get("store_graphic"),
        "design_palette": {"key": pal["key"], "label": pal["label"], "accent": "#%02X%02X%02X" % pal["accent"]},
        "design_language_applied": True, "deliverables": deliverables,
        "design_recommendation": rec, "updated_at": now_iso()}})
    await log_org("Creative Studio Director\u2122", "Creative Studio", "rendered branded QRU product", p.get("product_code", ""), "success")
