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
import product_recipes as pr

logger = logging.getLogger("qru.design_director")

SETTINGS_KEY = "design_director"
DEFAULT_SETTINGS = {"passing_score": 91, "auto_improve": True, "max_iterations": 3,
                    "allow_founder_override": True, "allow_ai_hero_art": False}

# QRU Design Standard™ — the 11 evaluated categories (MT-032 Auto-Gate).
CATEGORIES = ["Understanding & Clarity", "Educational Effectiveness", "Visual Hierarchy",
              "Typography", "Layout & Spacing", "Accessibility", "QRU Branding",
              "Treasure Standard™ Compliance", "Print Readiness", "Marketplace Readiness",
              "Product-Type Compliance"]

# Deduction category → recurring-issue tag for Factory Continuous Improvement™.
_ISSUE_TAGS = {
    "Understanding & Clarity": "unclear_content",
    "Educational Effectiveness": "weak_teaching_flow",
    "Visual Hierarchy": "weak_visual_hierarchy",
    "Typography": "inconsistent_typography",
    "Layout & Spacing": "poor_spacing",
    "Accessibility": "readability_problems",
    "QRU Branding": "branding_imbalance",
    "Treasure Standard™ Compliance": "treasure_standard_gap",
    "Print Readiness": "print_readiness_issues",
    "Marketplace Readiness": "marketplace_export_issues",
    "Product-Type Compliance": "recipe_violations",
}


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


def validate_product_type(product, files=None):
    """Product-Type Compliance — verify a product follows its Manufacturing Recipe™."""
    ptype = product.get("product_type", "")
    recipe = pr.get_recipe(ptype)
    cat = recipe["category"]
    content = product.get("content") or ""
    sections = content.count("\n## ") + (1 if content.startswith("## ") else 0)
    chars = len(content)
    low = content.lower()
    has_toc = "table of contents" in low
    has_chapter = "chapter" in low
    has_exercise = any(k in low for k in ("exercise", "practice", "activity", "answer", "fill in", "worksheet"))
    branded = bool(product.get("design_language_applied"))
    v = []
    if cat == "poster":
        if sections <= 1 and not branded:
            v.append("Cover-only poster — needs a strong single-page educational graphic.")
        if sections > 6:
            v.append("Poster should be a single educational page, not multi-section.")
        if has_toc or has_chapter:
            v.append("Poster must not contain a table of contents or chapters.")
    elif cat == "book":
        if sections < 3:
            v.append("Book needs multiple chapters/sections.")
        if not product.get("cover_url"):
            v.append("Book needs a cover.")
    elif cat == "workbook":
        if not has_exercise:
            v.append("Workbook needs exercises / practice / answer spaces.")
    elif cat == "deck":
        if sections < 3:
            v.append("Presentation needs a proper multi-slide hierarchy.")
    elif cat == "card":
        if sections > 4 or chars > 2500:
            v.append("Quick Card / Cheat Sheet must be a concise single-page reference.")
    compliant = len(v) == 0
    score = 10 if compliant else (6 if len(v) == 1 else 3)
    return {"compliant": compliant, "score": score, "violations": v,
            "recipe": recipe["label"], "category": cat}


async def score_product(product, files=None):
    """QRU Design Standard™ — 11-category Design Readiness Score™ (0–100), deterministic.
    Each category carries a reason + recommended fix + priority."""
    files = files or (product.get("customer_deliverable") or {}).get("files", [])
    content = product.get("content") or ""
    low = content.lower()
    sections = content.count("\n## ") + (1 if content.startswith("## ") else 0)
    chars = len(content)
    branded = bool(product.get("design_language_applied"))
    hero = bool(product.get("cover_has_hero_art"))
    has_html = any(f.get("format") == "html" and f.get("bytes", 0) >= 4000 for f in files)
    has_print_quality = any(f.get("format") in ("pdf", "epub", "pptx", "png") and f.get("bytes", 0) >= 15000 for f in files)
    deliver_ready = bool(product.get("deliverable_ready"))
    content_clean = not product.get("customer_content_review_required")
    has_thumb = bool(product.get("thumbnail_url"))
    has_store = bool(product.get("store_graphic_url"))
    has_market = bool(product.get("marketing_kit_ready"))
    teaching_flow = sum(1 for k in ("?", "example", "why", "imagine", "step", "practice") if k in low)
    compliance = validate_product_type(product, files)

    lines = []
    lines.append(_line("Understanding & Clarity", 10 if (sections >= 3 and chars >= 600) else (7 if sections >= 2 else 4),
                       f"{sections} teaching sections, {chars} chars.",
                       "Structure content as question → simple answer → why it matters."))
    lines.append(_line("Educational Effectiveness", 10 if teaching_flow >= 3 else (7 if teaching_flow >= 1 else 4),
                       f"{teaching_flow} teaching-flow signals (questions, examples, why, steps).",
                       "Teach before defining: add a question, a real example, and why it matters."))
    lines.append(_line("Visual Hierarchy", 9 if (sections >= 2 and "# " in content) else 4,
                       "Clear heading hierarchy present." if sections >= 2 else "Weak heading structure.",
                       "Add a title, section headings, and sub-points to guide the reader's eye."))
    lines.append(_line("Typography", 9 if branded else 6,
                       "Premium serif/sans typographic system applied." if branded else "Default typography.",
                       "Apply the QRU premium typography (serif body, sans headings)."))
    lines.append(_line("Layout & Spacing", 9 if branded else 6,
                       "Premium template margins, spacing & grid." if branded else "Generic layout spacing.",
                       "Apply the QRU template margins, spacing and grid."))
    lines.append(_line("Accessibility", 9 if (has_html and sections >= 2) else (7 if has_html else 4),
                       "Responsive, readable edition with clear structure." if has_html else "No responsive readable edition.",
                       "Render the responsive HTML edition with clear headings and high-contrast brand palette."))
    lines.append(_line("QRU Branding", 10 if (branded and product.get("cover_url")) else 4,
                       "QRU Design Language™ applied with branded cover." if branded else "No QRU branding detected.",
                       "Apply the QRU cover frame, shield and brand palette."))
    lines.append(_line("Treasure Standard™ Compliance", 10 if (branded and deliver_ready) else 5,
                       "Meets Treasure Standard™ manufacturing markers." if (branded and deliver_ready) else "Not yet certified to Treasure Standard™.",
                       "Render the deliverable and apply the Treasure Standard™ seal."))
    lines.append(_line("Print Readiness", 9 if has_print_quality else 5,
                       "Print-ready deliverable rendered in the product's native format." if has_print_quality else "No substantial print/output-ready file.",
                       "Render a paginated, print-ready file (PDF/EPUB/PPTX/PNG) with cover + footers."))
    lines.append(_line("Marketplace Readiness", 10 if (has_thumb and has_store and has_market) else (7 if (has_thumb and has_store) else 4),
                       "Thumbnail, store graphic & marketing kit ready." if has_market else ("Store thumbnail & graphic ready." if (has_thumb and has_store) else "Missing marketplace assets."),
                       "Manufacture the Preview & Marketing Kit™ (thumbnail, store images, social kit)."))
    lines.append(_line("Product-Type Compliance", compliance["score"],
                       "Follows its Manufacturing Recipe™." if compliance["compliant"] else "; ".join(compliance["violations"]),
                       f"Conform to the {compliance['recipe']} layout." if not compliance["compliant"] else "Recipe honored."))

    overall = round(sum(l["score"] for l in lines) / (len(lines) * 10) * 100)
    settings = await get_settings()
    return {"overall": overall, "passing_score": settings["passing_score"],
            "passed": overall >= settings["passing_score"], "categories": lines,
            "deductions": [l for l in lines if l["priority"] != "Pass"],
            "product_type_compliance": compliance,
            "scored_at": now_iso()}


async def fix_design_issues(pid, actor="QRU Design Director™"):
    """Auto-correction loop: apply improvements → re-render → re-score, repeat until the
    passing score is met or max iterations reached. Deterministic (no manual prompting)."""
    s = await get_settings()
    import rendering_engine as re_engine
    import deliverable_renderer as dr
    allow_ai = bool(s.get("allow_ai_hero_art"))
    history, last = [], None
    for i in range(max(1, s["max_iterations"])):
        try:
            # Deterministic-first: re-renders spend ZERO AI unless allow_ai_hero_art is on.
            await re_engine.ensure_branded_assets(pid, "QRU Design Director™", allow_ai_hero_art=allow_ai)
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
    est_cost = round((len(history) * _rate_image()) if allow_ai else 0.0, 4)
    return {"history": history, "final": sc, "passed": sc["passed"],
            "iterations": len(history), "max_iterations": s["max_iterations"],
            "allow_ai_hero_art": allow_ai, "estimated_ai_cost_usd": est_cost}


def _rate_image():
    try:
        import cost_meter
        return cost_meter.UNIT_COST.get("image", 0.04)
    except Exception:
        return 0.04


async def queue(limit=200):
    """Products the Design Director can review, with their latest score (if any)."""
    prods = await db.products.find(
        {"$or": [{"customer_deliverable": {"$ne": None}}, {"design_scorecard": {"$ne": None}}]}
    ).sort("updated_at", -1).to_list(limit)
    s = await get_settings()
    out = []
    for p in prods:
        sc = p.get("design_scorecard") or {}
        overall = sc.get("overall")
        out.append({
            "id": p["id"], "product_code": p.get("product_code"), "title": p.get("title"),
            "product_type": p.get("product_type"), "family": p.get("family"),
            "status": p.get("status"), "cover_url": p.get("cover_url"),
            "overall": overall,
            "passed": (overall is not None and overall >= s["passing_score"]),
            "scored": overall is not None,
        })
    return {"passing_score": s["passing_score"], "products": out}


async def record_reference(product):
    """Learning system — every Founder-approved / high-scoring product becomes a reference."""
    sc = product.get("design_scorecard") or {}
    await db.design_references.update_one({"product_id": product.get("id")}, {"$set": {
        "product_id": product.get("id"), "product_code": product.get("product_code"),
        "product_type": product.get("product_type"), "family": product.get("family"),
        "overall": sc.get("overall"), "cover_url": product.get("cover_url"),
        "recorded_at": now_iso()}}, upsert=True)


# --------------------------------------------------------------------------- #
# MO-039 — Autonomous Improvement Mode™: escalation intelligence.
# Categories the Factory can safely repair deterministically vs those needing a human.
# --------------------------------------------------------------------------- #
_DETERMINISTIC_FIXABLE = {
    "Visual Hierarchy", "Typography", "Layout & Spacing", "Accessibility",
    "QRU Branding", "Print Readiness", "Marketplace Readiness", "Product-Type Compliance",
    "Treasure Standard™ Compliance",
}
_NEEDS_FOUNDER = {"Understanding & Clarity", "Educational Effectiveness"}


def improvement_escalation(scorecard, product):
    """After Autonomous Improvement Mode™ runs, decide whether the Founder is genuinely
    needed and, if so, explain exactly what remains and what decision is required."""
    if scorecard.get("passed"):
        return None
    remaining = [l["category"] for l in scorecard.get("deductions", [])]
    content_gaps = [c for c in remaining if c in _NEEDS_FOUNDER]
    if content_gaps:
        return {
            "needs_founder": True,
            "stopped_reason": "Knowledge content is too thin for the Factory to reach the Gold Standard on its own.",
            "whats_remaining": remaining,
            "decision_needed": "Add or promote a fuller Knowledge Record (content), then the Factory finishes automatically.",
            "category": "knowledge_content",
        }
    return {
        "needs_founder": True,
        "stopped_reason": "The Factory applied every safe deterministic repair, but the design is still below the Gold Standard.",
        "whats_remaining": remaining,
        "decision_needed": "Provide creative direction, or approve the current design as an acceptable choice.",
        "category": "creative_direction",
    }


def _issue_tags(scorecard):
    tags = []
    for l in scorecard.get("deductions", []):
        tag = _ISSUE_TAGS.get(l["category"])
        if tag:
            tags.append(tag)
    comp = scorecard.get("product_type_compliance", {})
    for v in comp.get("violations", []):
        if "cover-only" in v.lower():
            tags.append("cover_only_posters")
    return sorted(set(tags))


async def record_telemetry(product, scorecard, improvements, time_saved_min):
    """Design Telemetry™ — one immutable record per gate run."""
    await db.design_telemetry.insert_one({
        "product_id": product.get("id"), "product_code": product.get("product_code"),
        "product_type": product.get("product_type"),
        "design_score": scorecard.get("overall"), "passed": scorecard.get("passed"),
        "improvement_count": improvements.get("iterations", 0),
        "improvement_categories": improvements.get("improved_categories", []),
        "issue_tags": _issue_tags(scorecard),
        "knowledge_record_id": product.get("knowledge_record_id"),
        "manufacturing_recipe": (scorecard.get("product_type_compliance") or {}).get("recipe"),
        "asset_vault_item": (product.get("cover_vault_asset") or {}).get("asset_code"),
        "marketplace_destination": product.get("marketplace") or "QRU Store™",
        "approval_status": product.get("status"),
        "publication_status": "Published" if product.get("status") == "Published" else "Pending Founder Review",
        "time_saved_minutes": time_saved_min,
        "recorded_at": now_iso(),
    })


async def auto_gate(pid, actor="QRU Design Director™"):
    """MT-032 Auto-Gate — runs immediately after manufacturing, before Founder Review.
    Deterministic ($0 by default). Founder retains final approval authority — this only
    scores, deterministically improves, and annotates the product; it never publishes."""
    s = await get_settings()
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    files = (p.get("customer_deliverable") or {}).get("files", [])
    before = await score_product(p, files)
    improvements = {"iterations": 0, "improved_categories": []}
    final = before

    if s["auto_improve"] and not before["passed"]:
        weak_before = {l["category"] for l in before["deductions"]}
        result = await fix_design_issues(pid, actor)
        p = await db.products.find_one({"id": pid})
        final = p.get("design_scorecard") or await score_product(p, (p.get("customer_deliverable") or {}).get("files", []))
        weak_after = {l["category"] for l in final.get("deductions", [])}
        improvements = {"iterations": result.get("iterations", 0),
                        "improved_categories": sorted(weak_before - weak_after),
                        "estimated_ai_cost_usd": result.get("estimated_ai_cost_usd", 0.0)}
    else:
        await db.products.update_one({"id": pid}, {"$set": {"design_scorecard": final}})

    # ~18 min of manual design QC saved per product + 4 min per improvement pass.
    time_saved = 18 + 4 * improvements.get("iterations", 0)
    p_after = await db.products.find_one({"id": pid})
    escalation = improvement_escalation(final, p_after)
    result_summary = {
        "manufactured": True,
        "autonomous_improvements": improvements.get("iterations", 0),
        "improved_categories": improvements.get("improved_categories", []),
        "final_design_score": final["overall"],
        "gold_standard": s["passing_score"],
        "passed": final["passed"],
        "treasure_status": p_after.get("treasure_standard_status") or ("Certified" if p_after.get("treasure_standard") else "Pending"),
        "needs_founder": bool(escalation),
    }
    gate = {
        "score": final["overall"], "passed": final["passed"],
        "passing_score": s["passing_score"],
        "improvement_count": improvements.get("iterations", 0),
        "improved_categories": improvements.get("improved_categories", []),
        "issue_tags": _issue_tags(final),
        "gated_at": now_iso(), "gated_by": actor,
        "estimated_ai_cost_usd": improvements.get("estimated_ai_cost_usd", 0.0),
        "escalation": escalation,
        "result_summary": result_summary,
    }
    await db.products.update_one({"id": pid}, {"$set": {
        "design_gate": gate, "design_escalation": escalation, "updated_at": now_iso()}})
    p = await db.products.find_one({"id": pid})
    await record_telemetry(p, final, improvements, time_saved)
    if final["passed"]:
        await record_reference(p)
    try:
        from org_activity import log_org
        if final["passed"]:
            note = f"reached the Gold Standard ({final['overall']}/100) after {improvements.get('iterations',0)} autonomous improvement pass(es) for"
        else:
            note = f"auto-improved to {final['overall']}/100 and escalated to the Founder ({(escalation or {}).get('category','')}) for"
        await log_org("QRU Design Director™", "Creative Studio", note,
                      p.get("product_code", ""), "success" if final["passed"] else "warning")
    except Exception:
        pass
    return {"gate": gate, "scorecard": final, "improvements": improvements,
            "escalation": escalation, "result_summary": result_summary,
            "time_saved_minutes": time_saved}


async def telemetry(limit=300):
    docs = await db.design_telemetry.find({}).sort("recorded_at", -1).to_list(limit)
    for d in docs:
        d.pop("_id", None)
    return docs


async def factory_intelligence():
    """Factory Continuous Improvement™ — aggregate telemetry into Factory Intelligence™."""
    docs = await db.design_telemetry.find({}).to_list(2000)
    total = len(docs)
    passed = sum(1 for d in docs if d.get("passed"))
    scores = [d.get("design_score") for d in docs if isinstance(d.get("design_score"), (int, float))]
    avg = round(sum(scores) / len(scores), 1) if scores else 0
    total_saved = sum(d.get("time_saved_minutes", 0) for d in docs)
    total_improvements = sum(d.get("improvement_count", 0) for d in docs)
    issue_counts = {}
    for d in docs:
        for t in d.get("issue_tags", []):
            issue_counts[t] = issue_counts.get(t, 0) + 1
    by_type = {}
    for d in docs:
        t = d.get("product_type") or "Unknown"
        b = by_type.setdefault(t, {"count": 0, "passed": 0, "score_sum": 0})
        b["count"] += 1
        b["passed"] += 1 if d.get("passed") else 0
        b["score_sum"] += d.get("design_score") or 0
    by_type_out = [{"product_type": k, "count": v["count"], "pass_rate": round(100 * v["passed"] / v["count"]) if v["count"] else 0,
                    "avg_score": round(v["score_sum"] / v["count"], 1) if v["count"] else 0}
                   for k, v in sorted(by_type.items(), key=lambda x: -x[1]["count"])]
    recurring = sorted([{"issue": k, "count": v} for k, v in issue_counts.items()], key=lambda x: -x["count"])
    return {
        "summary": {
            "products_gated": total, "passing": passed,
            "pass_rate": round(100 * passed / total) if total else 0,
            "avg_design_score": avg, "total_improvements": total_improvements,
            "time_saved_minutes": total_saved, "time_saved_hours": round(total_saved / 60, 1),
        },
        "recurring_issues": recurring,
        "by_product_type": by_type_out,
        "generated_at": now_iso(),
    }


async def references(limit=50):
    docs = await db.design_references.find({}).sort("overall", -1).to_list(limit)
    for d in docs:
        d.pop("_id", None)
    return docs
