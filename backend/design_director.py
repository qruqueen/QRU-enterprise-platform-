"""QRU Design Director™ (MT-032) — active, autonomous design-review stage.

Turns the passive MT-025 scorecard into an improvement system: it scores every rendered
product across 11 categories, and the auto-correction loop deterministically re-renders /
re-brands / re-scores until the Founder's passing score is met (or max iterations hit),
so the Founder reviews polished products — not rough drafts.

Deterministic-first: works even while AI capacity is capped. Learns by recording every
Founder-approved / high-scoring product as a reference example.
"""
import os
import logging

from database import db
from models import now_iso

logger = logging.getLogger("qru.design_director")

SETTINGS_KEY = "design_director"
DEFAULT_SETTINGS = {"passing_score": 90, "auto_improve": True, "max_iterations": 3,
                    "allow_founder_override": True}

CATEGORIES = ["QRU Branding", "Treasure Standard™ Compliance", "Educational Clarity",
              "Visual Hierarchy", "Typography", "Graphics & Illustration", "Layout & Spacing",
              "Color Harmony", "Readability", "Print Quality", "Customer Readiness"]


async def get_settings():
    doc = await db.factory_settings.find_one({"key": SETTINGS_KEY})
    s = dict(DEFAULT_SETTINGS)
    if doc:
        s.update({k: doc[k] for k in DEFAULT_SETTINGS if k in doc})
    return s


async def update_settings(updates):
    s = await get_settings()
    for k in DEFAULT_SETTINGS:
        if k in updates and updates[k] is not None:
            s[k] = updates[k]
    await db.factory_settings.update_one({"key": SETTINGS_KEY}, {"$set": {"key": SETTINGS_KEY, **s}}, upsert=True)
    return s


def _priority(score):
    return "Critical" if score <= 3 else "Major" if score <= 6 else ("Minor" if score < 9 else "Pass")


def _line(category, score, reason, recommendation):
    return {"category": category, "score": score, "reason": reason,
            "recommendation": recommendation, "priority": _priority(score)}


async def score_product(product, files=None):
    """11-category Design Scorecard with reason + recommended fix + priority per deduction."""
    files = files or (product.get("customer_deliverable") or {}).get("files", [])
    content = product.get("content") or ""
    sections = content.count("\n## ") + (1 if content.startswith("## ") else 0)
    chars = len(content)
    branded = bool(product.get("design_language_applied"))
    hero = bool(product.get("cover_has_hero_art"))
    has_html = any(f.get("format") == "html" and f.get("bytes", 0) >= 4000 for f in files)
    has_pdf = any(f.get("format") == "pdf" and f.get("bytes", 0) >= 20000 for f in files)
    deliver_ready = bool(product.get("deliverable_ready"))
    content_clean = not product.get("customer_content_review_required")

    cover_w = 0
    try:
        import rendering_engine as re_engine
        from PIL import Image
        cu = product.get("cover_url")
        if cu:
            path = os.path.join(re_engine.ASSET_DIR, cu.split("/")[-1])
            if os.path.exists(path):
                with Image.open(path) as im:
                    cover_w = im.size[0]
    except Exception:
        pass

    lines = []
    lines.append(_line("QRU Branding", 10 if (branded and cover_w) else 4,
                       "QRU Design Language™ applied with branded cover." if branded else "No QRU branding detected on the product.",
                       "Apply the QRU cover frame, shield, and brand palette." ))
    lines.append(_line("Treasure Standard™ Compliance", 10 if (branded and deliver_ready) else 5,
                       "Meets Treasure Standard™ manufacturing markers." if (branded and deliver_ready) else "Deliverable not yet certified to Treasure Standard™.",
                       "Render the deliverable and apply the Treasure Standard™ seal."))
    lines.append(_line("Educational Clarity", 10 if (sections >= 3 and chars >= 600) else (7 if sections >= 2 else 4),
                       f"{sections} teaching sections, {chars} chars." ,
                       "Structure the content into clear teaching sections with a question → answer → why-it-matters flow."))
    lines.append(_line("Visual Hierarchy", 9 if (sections >= 2 and "# " in content) else 4,
                       "Clear heading hierarchy present." if sections >= 2 else "Weak heading structure.",
                       "Add a title, section headings, and sub-points to guide the reader's eye."))
    lines.append(_line("Typography", 9 if branded else 6,
                       "Premium serif/sans typographic system applied." if branded else "Default typography.",
                       "Use the QRU premium typography (Times body, Helvetica headings)."))
    lines.append(_line("Graphics & Illustration", 9 if hero else 3,
                       "Educational hero artwork present." if hero else "Relies primarily on text and lacks educational visuals.",
                       "Generate QRU-style educational graphics, diagrams, icons, and callouts appropriate for the audience."))
    lines.append(_line("Layout & Spacing", 9 if branded else 6,
                       "Premium template spacing/margins." if branded else "Generic layout spacing.",
                       "Apply the QRU template margins, spacing, and grid."))
    lines.append(_line("Color Harmony", 9 if branded else 6,
                       "Brand palette applied consistently." if branded else "No consistent color system.",
                       "Apply the QRU royal/gold/navy palette with an audience-appropriate accent."))
    lines.append(_line("Readability", 9 if (has_html and chars >= 400) else 5,
                       "Responsive, readable customer edition." if has_html else "Readable edition not rendered.",
                       "Render the responsive HTML reading edition."))
    lines.append(_line("Print Quality", 9 if has_pdf else 5,
                       "Print-ready PDF rendered." if has_pdf else "No print-ready PDF.",
                       "Render a paginated, print-ready PDF with cover + footers."))
    lines.append(_line("Customer Readiness", 9 if (deliver_ready and content_clean) else 4,
                       "Customer-ready — no internal notes, deliverable validated." if (deliver_ready and content_clean) else "Not customer-ready (missing deliverable or internal notes present).",
                       "Render & validate the deliverable and remove any internal production notes."))

    overall = round(sum(l["score"] for l in lines) / (len(lines) * 10) * 100)
    settings = await get_settings()
    return {"overall": overall, "passing_score": settings["passing_score"],
            "passed": overall >= settings["passing_score"], "categories": lines,
            "deductions": [l for l in lines if l["priority"] != "Pass"],
            "scored_at": now_iso()}


async def fix_design_issues(pid, actor="QRU Design Director™"):
    """Auto-correction loop: apply improvements → re-render → re-score, repeat until the
    passing score is met or max iterations reached. Deterministic (no manual prompting)."""
    s = await get_settings()
    import rendering_engine as re_engine
    import deliverable_renderer as dr
    history, last = [], None
    for i in range(max(1, s["max_iterations"])):
        try:
            await re_engine.ensure_branded_assets(pid, "Creative Studio™")   # attempts hero art, deterministic fallback
            await dr.ensure_deliverable(pid, actor)
        except Exception as e:
            logger.error(f"fix iteration {i+1} render failed: {e}")
        p = await db.products.find_one({"id": pid})
        sc = await score_product(p, (p.get("customer_deliverable") or {}).get("files", []))
        history.append({"iteration": i + 1, "overall": sc["overall"], "passed": sc["passed"]})
        # store latest scorecard on the product
        await db.products.update_one({"id": pid}, {"$set": {"design_scorecard": sc, "updated_at": now_iso()}})
        if sc["passed"]:
            break
        if last is not None and sc["overall"] <= last:
            break  # plateaued — no further deterministic improvement possible (e.g., AI graphics capped)
        last = sc["overall"]
    try:
        from org_activity import log_org
        p = await db.products.find_one({"id": pid})
        await log_org("QRU Design Director™", "Creative Studio",
                      f"ran {len(history)} design-improvement pass(es) ({history[-1]['overall']}/100) for",
                      p.get("product_code", ""), "success" if history[-1]["passed"] else "warning")
    except Exception:
        pass
    return {"history": history, "final": sc, "passed": sc["passed"],
            "iterations": len(history), "max_iterations": s["max_iterations"]}


async def record_reference(product):
    """Learning system — every Founder-approved / high-scoring product becomes a reference."""
    sc = product.get("design_scorecard") or {}
    await db.design_references.update_one({"product_id": product.get("id")}, {"$set": {
        "product_id": product.get("id"), "product_code": product.get("product_code"),
        "product_type": product.get("product_type"), "family": product.get("family"),
        "overall": sc.get("overall"), "cover_url": product.get("cover_url"),
        "recorded_at": now_iso()}}, upsert=True)


async def references(limit=50):
    docs = await db.design_references.find({}).sort("overall", -1).to_list(limit)
    for d in docs:
        d.pop("_id", None)
    return docs
