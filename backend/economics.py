"""QRU Manufacturing Economics™ & AI Cost Intelligence (MT-028) — informational only.

Estimates per-product manufacturing cost (text/image/narration/translation/rendering),
manufacturing economics (price, fees, gross profit/margin), and reuse savings from the
Asset Vault™ + assembly-first pipeline. Changes NO factory behavior — pure read/report.
"""
import csv
import io
import logging

from database import db
from models import now_iso
import cost_meter
import commerce

logger = logging.getLogger("qru.economics")

# Typical AI operations per product type (deterministic estimate when no live usage exists).
# calls are approximate; costs use cost_meter.UNIT_COST.
TYPE_PROFILE = {
    # type: (text_calls, image_calls, tts_calls, translation_calls)
    "Book": (9, 1, 0, 1), "Workbook": (6, 1, 0, 1), "Teacher Guide": (5, 1, 0, 1),
    "Caregiver Guide": (5, 1, 0, 1), "Student Guide": (5, 1, 0, 1), "Course": (8, 1, 0, 1),
    "Quiz": (3, 0, 0, 0), "Flash Cards": (3, 1, 0, 0), "Interactive Lesson": (6, 1, 0, 1),
    "Poster": (2, 1, 0, 0), "Presentation": (5, 1, 0, 1), "Blog Article": (3, 1, 0, 0),
    "Short-form Content": (2, 1, 0, 0), "Podcast Script": (3, 0, 1, 0),
    "Video Script": (3, 0, 1, 0), "Audio Narration": (2, 0, 3, 0), "Quick Guide": (2, 1, 0, 0),
    "Video": (4, 2, 3, 1), "Animation": (4, 3, 2, 1), "Movie": (6, 4, 4, 1),
}
DEFAULT_PROFILE = (5, 1, 0, 1)

STRIPE_PCT = 0.029
STRIPE_FIXED = 0.30
MARKETPLACE_FEE_PCT = 0.0  # own QRU Store™ → no marketplace fee


def _rate(k):
    return cost_meter.UNIT_COST.get(k, 0.01)


async def _live_cost_for(product_id):
    total = 0.0
    n = 0
    async for e in cost_meter.USAGE_COL.find({"product_id": product_id}):
        total += e.get("est_cost", 0.0)
        n += 1
    return (round(total, 4), n) if n else (None, 0)


async def estimate_product_cost(product):
    ptype = product.get("product_type", "")
    t, im, tts, tr = TYPE_PROFILE.get(ptype, DEFAULT_PROFILE)

    # Reuse: if the cover is deterministic (no AI hero art) or a vault asset is reused,
    # the image generation cost is avoided.
    used_ai_image = bool(product.get("cover_has_hero_art"))
    image_calls = im if used_ai_image else 0

    text_cost = round(t * _rate("text"), 4)
    image_cost = round(image_calls * _rate("image"), 4)
    narration_cost = round(tts * _rate("tts"), 4)
    translation_cost = round(tr * _rate("text"), 4)  # translation runs as text calls
    rendering_cost = 0.0  # deterministic (Pillow / fpdf / pptx / ebooklib) — no AI

    est_total = round(text_cost + image_cost + narration_cost + translation_cost + rendering_cost, 4)

    live_total, live_calls = await _live_cost_for(product.get("id"))
    breakdown = {
        "text": text_cost, "image": image_cost, "narration": narration_cost,
        "translation": translation_cost, "rendering": rendering_cost,
    }
    return {
        "estimated": breakdown,
        "estimated_total": est_total,
        "live_total": live_total,          # actual recorded AI cost for this product, if any
        "live_calls": live_calls,
        "basis": "measured" if live_total is not None else "modeled",
        "total": live_total if live_total is not None else est_total,
    }


async def _reuse_savings(product):
    """Estimated cost avoided by reusing deterministic covers, templates, and existing assets."""
    saved = 0.0
    reasons = []
    if not product.get("cover_has_hero_art"):
        saved += _rate("image"); reasons.append("Deterministic branded cover (no AI image)")
    # linked vault assets that were reused
    reused = await db.asset_vault.count_documents({"related_products.id": product.get("id")})
    if reused:
        saved += reused * _rate("image"); reasons.append(f"{reused} reused Asset Vault™ asset(s)")
    if product.get("assembled"):
        saved += 2 * _rate("text"); reasons.append("Assembly-first (composed from verified Knowledge Record)")
    return {"estimated_savings": round(saved, 4), "reasons": reasons}


async def economics_row(product):
    cost = await estimate_product_cost(product)
    price = commerce.product_price(product)
    marketplace_fee = round(price * MARKETPLACE_FEE_PCT, 2)
    processing_fee = round(price * STRIPE_PCT + STRIPE_FIXED, 2) if price else 0.0
    total_cost = cost["total"] + marketplace_fee + processing_fee
    gross_profit = round(price - total_cost, 2)
    margin = round(100 * gross_profit / price, 1) if price else 0.0
    savings = await _reuse_savings(product)
    return {
        "id": product.get("id"), "product_code": product.get("product_code"),
        "title": product.get("title"), "product_type": product.get("product_type"),
        "status": product.get("status"),
        "manufacturing_cost": cost["total"], "cost_basis": cost["basis"],
        "cost_breakdown": cost["estimated"],
        "suggested_price": price, "marketplace_fee": marketplace_fee,
        "processing_fee": processing_fee, "gross_profit": gross_profit, "gross_margin_pct": margin,
        "reuse_savings": savings["estimated_savings"], "reuse_reasons": savings["reasons"],
    }


async def overview(limit=500):
    ai = await cost_meter.overview()
    products = await db.products.find({}).sort("created_at", -1).to_list(limit)
    rows = [await economics_row(p) for p in products]

    total_savings = round(sum(r["reuse_savings"] for r in rows), 2)
    avg_cost = round(sum(r["manufacturing_cost"] for r in rows) / len(rows), 4) if rows else 0
    avg_margin = round(sum(r["gross_margin_pct"] for r in rows) / len(rows), 1) if rows else 0

    # Credit consumption ranking (what consumes the most).
    consumption = [
        {"operation": "AI text generation", "unit_cost": _rate("text"), "note": "Largest recurring cost — content + QC rounds", "tier": "high"},
        {"operation": "AI image generation", "unit_cost": _rate("image"), "note": "Cover / hero art — avoid by reusing Asset Vault™", "tier": "high"},
        {"operation": "AI narration (TTS)", "unit_cost": _rate("tts"), "note": "Audio/video products only", "tier": "medium"},
        {"operation": "Rendering (PDF/EPUB/PPTX/PNG/cover)", "unit_cost": 0.0, "note": "Deterministic — essentially free", "tier": "free"},
        {"operation": "Deliverable assembly & validation", "unit_cost": 0.0, "note": "Deterministic — free", "tier": "free"},
        {"operation": "Asset Vault™ reuse", "unit_cost": 0.0, "note": "Free — avoids regeneration", "tier": "free"},
    ]

    # First Dollar Mode™ recommendations: published/ready, lowest cost, highest margin.
    sellable = [r for r in rows if r["status"] in ("Published", "Ready for Release") and r["suggested_price"]]
    sellable.sort(key=lambda r: (-r["gross_margin_pct"], r["manufacturing_cost"]))
    recommendations = sellable[:8]

    return {
        "ai_dashboard": ai,
        "summary": {
            "products": len(rows), "avg_manufacturing_cost": avg_cost,
            "avg_gross_margin_pct": avg_margin, "total_reuse_savings": total_savings,
        },
        "products": rows,
        "credit_consumption": consumption,
        "recommendations": recommendations,
        "assumptions": {
            "unit_costs_usd": cost_meter.UNIT_COST,
            "stripe": {"pct": STRIPE_PCT, "fixed": STRIPE_FIXED},
            "marketplace_fee_pct": MARKETPLACE_FEE_PCT,
            "note": "All figures ESTIMATED. Rendering is deterministic (no AI). Selling an already-manufactured product incurs no new AI cost — only payment processing.",
        },
        "generated_at": now_iso(),
    }


def to_csv(data) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Product Code", "Title", "Type", "Status", "Manufacturing Cost (USD)", "Cost Basis",
                "Suggested Price", "Processing Fee", "Marketplace Fee", "Gross Profit", "Gross Margin %", "Reuse Savings"])
    for r in data["products"]:
        w.writerow([r["product_code"], r["title"], r["product_type"], r["status"],
                    r["manufacturing_cost"], r["cost_basis"], r["suggested_price"], r["processing_fee"],
                    r["marketplace_fee"], r["gross_profit"], r["gross_margin_pct"], r["reuse_savings"]])
    s = data["summary"]
    w.writerow([])
    w.writerow(["SUMMARY", f"Products: {s['products']}", f"Avg cost: ${s['avg_manufacturing_cost']}",
                f"Avg margin: {s['avg_gross_margin_pct']}%", f"Total reuse savings: ${s['total_reuse_savings']}"])
    return buf.getvalue().encode("utf-8")


def to_pdf(data) -> bytes:
    from fpdf import FPDF
    ROYAL, GOLD, NAVY = (53, 16, 106), (245, 178, 26), (34, 26, 66)

    def sanitize(t):
        return str(t).replace("™", "(TM)").encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF(format="A4"); pdf.set_auto_page_break(True, 15); pdf.add_page()
    pdf.set_fill_color(*ROYAL); pdf.rect(0, 0, 210, 30, "F")
    pdf.set_text_color(*GOLD); pdf.set_font("Helvetica", "B", 16); pdf.set_xy(12, 10)
    pdf.cell(0, 10, sanitize("QRU Manufacturing Economics(TM) Report"))
    pdf.set_text_color(*NAVY); pdf.set_xy(12, 36); pdf.set_font("Helvetica", "", 10)
    s = data["summary"]
    pdf.multi_cell(0, 6, sanitize(f"Products: {s['products']}   |   Avg manufacturing cost: ${s['avg_manufacturing_cost']}   |   "
                                  f"Avg gross margin: {s['avg_gross_margin_pct']}%   |   Total reuse savings: ${s['total_reuse_savings']}"))
    pdf.ln(2)
    headers = ["Code", "Type", "Cost$", "Price$", "Fees$", "Profit$", "Margin%"]
    widths = [26, 34, 20, 20, 20, 22, 22]
    pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*ROYAL)
    for h, wd in zip(headers, widths):
        pdf.cell(wd, 7, h, border="B")
    pdf.ln(7); pdf.set_text_color(*NAVY); pdf.set_font("Helvetica", "", 8)
    for r in data["products"][:60]:
        fees = round(r["processing_fee"] + r["marketplace_fee"], 2)
        cells = [r["product_code"], r["product_type"], f"{r['manufacturing_cost']}", f"{r['suggested_price']}",
                 f"{fees}", f"{r['gross_profit']}", f"{r['gross_margin_pct']}"]
        for c, wd in zip(cells, widths):
            pdf.cell(wd, 6, sanitize(c))
        pdf.ln(6)
    return bytes(pdf.output())
