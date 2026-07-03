"""MT-033 — QRU Preview & Marketing Manufacturing System™.

One Manufacturing Run → Many Finished Deliverables.

For every manufactured product this builds the complete product ecosystem, deterministically
(no LLM budget required):
  1. Founder Master Edition™   — internal editable version + full manufacturing metadata
  2. Customer Edition™         — the clean purchased product (from customer_deliverable)
  3. Preview Edition™          — a professional free sample that encourages purchase
  4. Store Preview Images™     — high-res store graphics
  5. Social Media Kit™         — FB / IG / Pinterest / LinkedIn / X / TikTok / YouTube
  6. Product Flyer™
  7. Product Thumbnail™
  8. Marketing Graphics™

All editions remain linked under one Product ID (stored on product.marketing_kit).
Customers never receive the full product before purchase — the Preview Edition is gated.
"""
import io
import os
import logging

from database import db
from models import now_iso
import rendering_engine as re_engine
import design_language as dl
import product_recipes as pr

logger = logging.getLogger("qru.marketing")

BACKEND_PUBLIC = os.environ.get("REACT_APP_BACKEND_URL", "")

# Founder-configurable Preview Edition defaults.
DEFAULT_PREVIEW_CONFIG = {
    "include_percentage": 30,          # % of sections shown in full
    "show_cover": True,
    "show_table_of_contents": True,
    "watermark_text": "PREVIEW — NOT FOR RESALE",
    "preview_message": "You're reading a free preview. Unlock the complete, Treasure Standard™ edition to continue.",
    "cta_text": "Continue Learning in the Full Edition",
}

# Social platforms → the branded image size used for each.
PLATFORM_SPECS = {
    "Facebook":  (1200, 630),
    "Instagram": (1080, 1080),
    "Pinterest": (1000, 1500),
    "LinkedIn":  (1200, 627),
    "X":         (1200, 675),
    "TikTok":    (1080, 1920),
    "YouTube":   (1280, 720),
}


def _load_cover(p):
    cu = p.get("cover_url")
    if cu:
        path = os.path.join(re_engine.ASSET_DIR, cu.split("/")[-1])
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
    kr = None
    return dl.premium_cover(p, kr or {})


# --------------------------------------------------------------------------- #
# Preview Edition™ — intentionally designed to encourage purchase.
# --------------------------------------------------------------------------- #
def _preview_markdown(content, cfg):
    """Build the preview content: TOC + first N% of sections in full + a purchase CTA gate."""
    import math
    from deliverable_renderer import filter_customer_content
    clean, _ = filter_customer_content(content or "")
    clean, _ = pr.strip_placeholders(clean)
    doc_title, sections = pr._parse_sections(clean)
    total = len(sections)
    pct = max(5, min(90, int(cfg.get("include_percentage", 30))))
    keep = max(1, math.ceil(total * pct / 100))
    parts = []
    if doc_title:
        parts.append(f"# {doc_title}\n")
    if cfg.get("show_table_of_contents", True) and total > 1:
        parts.append("## Table of Contents\n")
        for i, (h, _b) in enumerate(sections, 1):
            locked = "" if i <= keep else "  — 🔒 Full Edition"
            parts.append(f"- {h}{locked}")
        parts.append("")
    for h, b in sections[:keep]:
        parts.append(f"## {h}\n\n{b}\n")
    omitted = total - keep
    if omitted > 0:
        parts.append("---\n")
        parts.append(f"## {cfg.get('cta_text', DEFAULT_PREVIEW_CONFIG['cta_text'])}\n")
        parts.append(cfg.get("preview_message", DEFAULT_PREVIEW_CONFIG["preview_message"]))
        parts.append("")
        parts.append(f"**{omitted} more section(s)** are included in the complete Treasure Standard™ edition.")
    return "\n".join(parts), keep, omitted


def _preview_html(product, cover_bytes, cfg, purchase_url):
    prev_md, keep, omitted = _preview_markdown(product.get("content") or "", cfg)
    pprod = {**product, "content": prev_md, "title": product.get("title", "")}
    html = pr.render_html(pprod, cover_bytes if cfg.get("show_cover", True) else None).decode("utf-8")
    wm = cfg.get("watermark_text", DEFAULT_PREVIEW_CONFIG["watermark_text"])
    overlay = f"""
<style>
.preview-ribbon{{position:fixed;top:22px;right:-52px;transform:rotate(45deg);background:#F5B21A;color:#221A42;
font-family:Arial,sans-serif;font-weight:800;letter-spacing:.08em;padding:8px 60px;font-size:12px;z-index:50;box-shadow:0 4px 14px rgba(0,0,0,.2)}}
.preview-wm{{position:fixed;inset:0;pointer-events:none;z-index:40;background-image:repeating-linear-gradient(-30deg,transparent,transparent 180px,rgba(53,16,106,.05) 180px,rgba(53,16,106,.05) 360px)}}
.buy-bar{{position:sticky;bottom:0;background:linear-gradient(135deg,#35106A,#221A42);color:#fff;text-align:center;
padding:16px;font-family:Arial,sans-serif;z-index:60;box-shadow:0 -6px 24px rgba(0,0,0,.25)}}
.buy-bar a{{display:inline-block;background:#F5B21A;color:#221A42;font-weight:800;text-decoration:none;padding:10px 24px;border-radius:999px;margin-left:10px}}
</style>
<div class="preview-ribbon">PREVIEW</div><div class="preview-wm"></div>
<div class="buy-bar">{cfg.get('preview_message', DEFAULT_PREVIEW_CONFIG['preview_message'])}
<a href="{purchase_url}">Buy the Full Edition →</a></div>
<!-- {wm} -->
"""
    html = html.replace("</body>", overlay + "</body>")
    return html.encode("utf-8"), keep, omitted


def _preview_pdf(product, cover_bytes, cfg, purchase_url):
    prev_md, keep, omitted = _preview_markdown(product.get("content") or "", cfg)
    pprod = {**product, "content": prev_md,
             "title": f"{product.get('title','')} — Free Preview"}
    qr = re_engine._make_qr(purchase_url)
    return re_engine._make_pdf(pprod, {}, cover_bytes, qr)


# --------------------------------------------------------------------------- #
# Marketing image family — reuses the tested Design Language™ Pillow pipeline.
# --------------------------------------------------------------------------- #
def _flyer(product, cover_bytes):
    from PIL import Image, ImageDraw
    pal = dl.resolve_palette(product.get("family", ""), product.get("department", ""),
                             product.get("topic", ""), product.get("title", ""))
    W, H = 1080, 1528
    canvas = dl._vignette(dl._gradient(W, H, pal["top"], pal["bottom"]))
    d = ImageDraw.Draw(canvas)
    accent = pal["accent"]
    d.rectangle([36, 36, W - 36, H - 36], outline=accent, width=4)
    cover = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    cover.thumbnail((640, 860))
    x = (W - cover.width) // 2
    canvas.paste(cover, (x, 150))
    d.rectangle([x - 5, 145, x + cover.width + 5, 155 + cover.height], outline=accent, width=3)
    d.text((W // 2, 90), f"QRU • {(product.get('family') or pal['label']).upper()}",
           font=dl._f(dl.SANS_BOLD, 32), fill=accent, anchor="mm")
    ty = 150 + cover.height + 60
    font, lines, size = dl._fit_title(d, product.get("title", "Understanding"), W - 160, 3, start=64, min_size=38)
    for ln in lines:
        d.text((W // 2, ty), ln, font=font, fill=dl.WHITE, anchor="mm"); ty += int(size * 1.15)
    d.text((W // 2, ty + 40), "Available now at the QRU Store™",
           font=dl._f(dl.SANS, 34), fill=dl.CREAM, anchor="mm")
    d.text((W // 2, H - 90), "★ Treasure Standard™ Certified",
           font=dl._f(dl.SANS_BOLD, 30), fill=accent, anchor="mm")
    buf = io.BytesIO(); canvas.save(buf, "PNG")
    return buf.getvalue()


def _save_png(prefix, data):
    return re_engine._asset_url(re_engine._save(prefix, "png", data))


async def build_family(pid, actor="Manufacturing Director™", base_url=None):
    """Manufacture the complete Preview & Marketing deliverable family for a product."""
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    base_url = base_url or BACKEND_PUBLIC
    purchase_url = f"{base_url}/store"
    cfg = {**DEFAULT_PREVIEW_CONFIG, **(p.get("preview_config") or {})}
    cover_bytes = _load_cover(p)

    # 3) Preview Edition™ (HTML + PDF), gated + watermarked + purchase CTA.
    preview_files = []
    try:
        html, keep, omitted = _preview_html(p, cover_bytes, cfg, purchase_url)
        fid = re_engine._save("preview-html", "html", html)
        preview_files.append({"format": "html", "label": "Read Sample (HTML)",
                              "url": re_engine._asset_url(fid), "filename": fid, "bytes": len(html)})
    except Exception as e:
        logger.error(f"preview html failed for {pid}: {e}")
        keep = omitted = 0
    try:
        pdf = _preview_pdf(p, cover_bytes, cfg, purchase_url)
        fid = re_engine._save("preview-pdf", "pdf", pdf)
        preview_files.append({"format": "pdf", "label": "Download Preview PDF",
                              "url": re_engine._asset_url(fid), "filename": fid, "bytes": len(pdf)})
    except Exception as e:
        logger.error(f"preview pdf failed for {pid}: {e}")

    # 4-8) Image family — one Pillow pass over branded formats.
    fmts = dl.export_formats(p, {}, cover_bytes)
    thumb_url = p.get("thumbnail_url") or _save_png("thumb", dl.premium_thumbnail(cover_bytes))
    store_graphic_url = p.get("store_graphic_url") or _save_png("store", dl.premium_store_graphic(p, cover_bytes))

    store_images = [
        {"label": "Store Cover", "url": p.get("cover_url") or _save_png("cover", cover_bytes)},
        {"label": "Store Graphic", "url": store_graphic_url},
        {"label": dl.EXPORT_SPECS["etsy_listing"]["label"], "url": _save_png("store-etsy", fmts["etsy_listing"])},
        {"label": dl.EXPORT_SPECS["tpt_thumbnail"]["label"], "url": _save_png("store-tpt", fmts["tpt_thumbnail"])},
        {"label": dl.EXPORT_SPECS["kdp_ebook"]["label"], "url": _save_png("store-kdp", fmts["kdp_ebook"])},
    ]

    # Social Media Kit™ — platform-specific branded graphics.
    master = None
    social_kit = []
    from PIL import Image
    master = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    pal = dl.resolve_palette(p.get("family", ""), p.get("department", ""), p.get("topic", ""), p.get("title", ""))
    for platform, (W, H) in PLATFORM_SPECS.items():
        data = dl._fit_on_brand(master, W, H, pal)
        social_kit.append({"platform": platform, "label": f"{platform} ({W}×{H})",
                           "url": _save_png(f"social-{platform.lower()}", data), "size": [W, H]})

    marketing_graphics = [
        {"label": dl.EXPORT_SPECS["desktop_banner"]["label"], "url": _save_png("mkt-banner", fmts["desktop_banner"])},
        {"label": dl.EXPORT_SPECS["social_story"]["label"], "url": _save_png("mkt-story", fmts["social_story"])},
        {"label": dl.EXPORT_SPECS["poster_print"]["label"], "url": _save_png("mkt-poster", fmts["poster_print"])},
    ]

    flyer_url = _save_png("flyer", _flyer(p, cover_bytes))

    customer_deliverable = p.get("customer_deliverable") or {}
    kit = {
        "founder_master_edition": {
            "label": "Founder Master Edition™",
            "editable": True,
            "content_chars": len(p.get("content") or ""),
            "metadata_fields": ["product_code", "knowledge_record_id", "kr_version", "creative_brief",
                                "design_review", "treasure_standard", "version_history"],
            "version": p.get("kr_version", 1),
            "note": "Internal editable master with full manufacturing metadata and version history.",
        },
        "customer_edition": {
            "label": "Customer Edition™",
            "files": customer_deliverable.get("files", []),
            "primary_format": customer_deliverable.get("primary_format"),
            "note": "The clean, purchased product — no internal manufacturing notes.",
        },
        "preview_edition": {
            "label": "Preview Edition™",
            "files": preview_files,
            "sections_included": keep,
            "sections_locked": omitted,
            "config": cfg,
            "purchase_url": purchase_url,
            "note": "Free, watermarked sample designed to increase purchase confidence without giving away the full product.",
        },
        "store_images": store_images,
        "social_kit": social_kit,
        "marketing_graphics": marketing_graphics,
        "product_flyer": {"label": "Product Flyer™", "url": flyer_url},
        "product_thumbnail": {"label": "Product Thumbnail™", "url": thumb_url},
        "generated_at": now_iso(),
        "generated_by": actor,
    }
    await db.products.update_one({"id": pid}, {"$set": {
        "marketing_kit": kit,
        "preview_url": next((f["url"] for f in preview_files if f["format"] == "html"), None),
        "preview_pdf_url": next((f["url"] for f in preview_files if f["format"] == "pdf"), None),
        "thumbnail_url": thumb_url, "store_graphic_url": store_graphic_url,
        "marketing_kit_ready": True, "updated_at": now_iso()}})
    try:
        from org_activity import log_org
        await log_org("Marketing Director™", "Marketing",
                      f"manufactured the Preview & Marketing Kit™ ({len(social_kit)} social assets) for",
                      p.get("product_code", ""), "success")
    except Exception:
        pass
    return kit


async def update_preview_config(pid, config):
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    cfg = {**DEFAULT_PREVIEW_CONFIG, **(p.get("preview_config") or {}), **(config or {})}
    await db.products.update_one({"id": pid}, {"$set": {"preview_config": cfg, "updated_at": now_iso()}})
    return cfg
