"""MO-036 — Factory Intelligence™ Library Audit & Continuous Learning System.

QRU Factory Health Audit™: a ONE-CLICK, fully DETERMINISTIC inspection of the entire
Product Library. It scores every product against the QRU Design Standard™ (read-only),
aggregates a Factory Health Dashboard, records a snapshot, and produces a Factory Learning
Report™ that compares snapshots over time to show what the factory got better at.

STRICT: audit-only. No AI, no regeneration, no rewriting, no modification of Founder
assets or verified Knowledge Records. It never calls the improvement/re-render loop.
"""
import logging

from database import db
from models import now_iso
import design_director as dd

logger = logging.getLogger("qru.factory_audit")

IMAGE_RATE = 0.04  # $ per AI image avoided (matches cost_meter)
TEXT_RATE = 0.01
MINUTES_SAVED_PER_PRODUCT = 18  # deterministic design QC the Founder didn't have to do

MFG_ISSUE_LABELS = {
    "deliverable_not_rendered": "Deliverable not rendered",
    "no_preview_kit": "No preview / marketing kit",
    "not_treasure_certified": "Not Treasure Standard™ certified",
    "missing_cover": "Missing cover",
}


def _cat(sc, name):
    for l in sc["categories"]:
        if l["category"] == name:
            return l["score"]
    return 0


async def run_audit(actor="QRU Factory Health Audit™", persist=True):
    products = await db.products.find({}).to_list(2000)
    rows = []
    design_scores, treasure, marketplace = [], [], []
    reuse_count = preview_count = passing = needs_review = 0
    ai_avoided = 0.0
    design_issues, recipe_violations, mfg_issues = {}, {}, {}
    by_type = {}
    cat_sums, cat_n = {}, 0

    for p in products:
        files = (p.get("customer_deliverable") or {}).get("files", [])
        sc = await dd.score_product(p, files)  # READ-ONLY — no writes, no AI
        comp = sc["product_type_compliance"]
        design_scores.append(sc["overall"])
        treasure.append(_cat(sc, "Treasure Standard™ Compliance") * 10)
        marketplace.append(_cat(sc, "Marketplace Readiness") * 10)
        cat_n += 1
        for l in sc["categories"]:
            cat_sums[l["category"]] = cat_sums.get(l["category"], 0) + l["score"]

        reused = bool(p.get("cover_vault_asset") or p.get("cover_source") in ("asset_vault", "asset_vault_selected"))
        if reused:
            reuse_count += 1
            ai_avoided += IMAGE_RATE
        if not p.get("cover_has_hero_art"):
            ai_avoided += IMAGE_RATE          # deterministic branded cover avoided an AI image
        if p.get("assembled"):
            ai_avoided += 2 * TEXT_RATE       # assembled from a verified Knowledge Record
        has_preview = bool(p.get("preview_url") or p.get("marketing_kit_ready"))
        if has_preview:
            preview_count += 1

        if sc["passed"]:
            passing += 1
        else:
            needs_review += 1
        for t in dd._issue_tags(sc):
            design_issues[t] = design_issues.get(t, 0) + 1
        for v in comp.get("violations", []):
            recipe_violations[v] = recipe_violations.get(v, 0) + 1
        if not p.get("deliverable_ready"):
            mfg_issues["deliverable_not_rendered"] = mfg_issues.get("deliverable_not_rendered", 0) + 1
        if not has_preview:
            mfg_issues["no_preview_kit"] = mfg_issues.get("no_preview_kit", 0) + 1
        if not p.get("treasure_standard"):
            mfg_issues["not_treasure_certified"] = mfg_issues.get("not_treasure_certified", 0) + 1
        if not p.get("cover_url"):
            mfg_issues["missing_cover"] = mfg_issues.get("missing_cover", 0) + 1

        bt = by_type.setdefault(p.get("product_type") or "Unknown", {"count": 0, "score_sum": 0, "passed": 0})
        bt["count"] += 1
        bt["score_sum"] += sc["overall"]
        bt["passed"] += 1 if sc["passed"] else 0

        rows.append({
            "id": p["id"], "product_code": p.get("product_code"), "title": p.get("title"),
            "product_type": p.get("product_type"), "status": p.get("status"),
            "design_score": sc["overall"], "passed": sc["passed"],
            "treasure_score": _cat(sc, "Treasure Standard™ Compliance") * 10,
            "recipe_compliant": comp["compliant"],
            "print_readiness": _cat(sc, "Print Readiness") * 10,
            "marketplace_readiness": _cat(sc, "Marketplace Readiness") * 10,
            "educational_clarity": _cat(sc, "Understanding & Clarity") * 10,
            "layout": _cat(sc, "Layout & Spacing") * 10,
            "typography": _cat(sc, "Typography") * 10,
            "visual_hierarchy": _cat(sc, "Visual Hierarchy") * 10,
            "asset_vault_used": reused, "preview_generated": has_preview,
            "publication_status": "Published" if p.get("status") == "Published" else p.get("status"),
        })

    n = len(products) or 1
    avg = lambda a: round(sum(a) / len(a), 1) if a else 0
    reuse_pct = round(100 * reuse_count / n)
    time_saved_min = passing * MINUTES_SAVED_PER_PRODUCT
    category_avgs = {k: round(v / cat_n, 2) for k, v in cat_sums.items()} if cat_n else {}
    rank = sorted([{"product_type": k, "count": v["count"], "avg_score": round(v["score_sum"] / v["count"], 1),
                    "pass_rate": round(100 * v["passed"] / v["count"])} for k, v in by_type.items()],
                  key=lambda x: -x["avg_score"])

    dashboard = {
        "total_products": len(products),
        "products_passing": passing,
        "products_requiring_review": needs_review,
        "avg_design_score": avg(design_scores),
        "avg_treasure_score": avg(treasure),
        "avg_product_readiness": avg(design_scores),
        "avg_marketplace_readiness": avg(marketplace),
        "avg_asset_reuse_pct": reuse_pct,
        "preview_coverage_pct": round(100 * preview_count / n),
        "founder_time_saved_minutes": time_saved_min,
        "founder_time_saved_hours": round(time_saved_min / 60, 1),
        "estimated_ai_cost_avoided_usd": round(ai_avoided, 2),
        "most_common_design_issues": sorted([{"issue": k, "count": v} for k, v in design_issues.items()], key=lambda x: -x["count"])[:8],
        "most_common_manufacturing_issues": sorted([{"issue": MFG_ISSUE_LABELS.get(k, k), "count": v} for k, v in mfg_issues.items()], key=lambda x: -x["count"])[:8],
        "most_common_recipe_violations": sorted([{"violation": k, "count": v} for k, v in recipe_violations.items()], key=lambda x: -x["count"])[:8],
        "best_performing_types": rank[:5],
        "lowest_performing_types": list(reversed(rank))[:5] if len(rank) > 1 else [],
    }

    snapshot = {
        "created_at": now_iso(), "by": actor,
        "total": len(products), "passing": passing, "needs_review": needs_review,
        "avg_design_score": dashboard["avg_design_score"],
        "avg_treasure_score": dashboard["avg_treasure_score"],
        "avg_marketplace_readiness": dashboard["avg_marketplace_readiness"],
        "asset_reuse_pct": reuse_pct,
        "category_avgs": category_avgs,
        "ai_cost_avoided_usd": dashboard["estimated_ai_cost_avoided_usd"],
        "time_saved_minutes": time_saved_min,
        "needs_review_rate": round(100 * needs_review / n, 1),
    }
    if persist:
        await db.factory_audits.insert_one(dict(snapshot))
        try:
            from org_activity import log_org
            await log_org("Factory Intelligence™", "Manufacturing",
                          f"completed a Factory Health Audit™ — {passing}/{len(products)} passing, avg {dashboard['avg_design_score']}/100",
                          "", "success")
        except Exception:
            pass

    return {"dashboard": dashboard, "products": rows, "snapshot_at": snapshot["created_at"]}


async def latest_audit():
    snap = await db.factory_audits.find_one(sort=[("created_at", -1)])
    if not snap:
        return {"available": False}
    snap.pop("_id", None)
    return {"available": True, "snapshot": snap}


async def learning_report():
    """Factory Learning Report™ — what did the factory get better at, period over period."""
    snaps = await db.factory_audits.find().sort("created_at", -1).to_list(2)
    if not snaps:
        return {"available": False, "message": "Run a Factory Health Audit™ first to establish a baseline."}
    for s in snaps:
        s.pop("_id", None)
    cur = snaps[0]
    if len(snaps) < 2:
        return {"available": True, "baseline": True,
                "message": "Baseline established. Run another audit later to measure improvement.",
                "current": cur}
    prev = snaps[1]

    def pct_change(new, old):
        if not old:
            return 0.0
        return round(100 * (new - old) / old, 1)

    improved_at = []
    labels = {
        "Understanding & Clarity": "Educational clarity", "Educational Effectiveness": "Teaching effectiveness",
        "Visual Hierarchy": "Visual hierarchy", "Typography": "Typography", "Layout & Spacing": "Spacing & layout",
        "Accessibility": "Accessibility", "QRU Branding": "Cover & branding",
        "Treasure Standard™ Compliance": "Treasure Standard™ compliance", "Print Readiness": "Print readiness",
        "Marketplace Readiness": "Marketplace exports", "Product-Type Compliance": "Recipe compliance",
    }
    for cat, cur_v in (cur.get("category_avgs") or {}).items():
        prev_v = (prev.get("category_avgs") or {}).get(cat)
        if prev_v is not None and cur_v > prev_v + 0.05:
            improved_at.append({"area": labels.get(cat, cat), "from": prev_v, "to": cur_v})
    improved_at.sort(key=lambda x: -(x["to"] - x["from"]))

    corrections_reduced = round(prev.get("needs_review_rate", 0) - cur.get("needs_review_rate", 0), 1)
    return {
        "available": True, "baseline": False,
        "period": {"from": prev["created_at"], "to": cur["created_at"]},
        "improved_at": improved_at,
        "metrics": {
            "avg_design_score_change_pct": pct_change(cur["avg_design_score"], prev["avg_design_score"]),
            "avg_design_score_now": cur["avg_design_score"], "avg_design_score_before": prev["avg_design_score"],
            "asset_reuse_change_points": round(cur["asset_reuse_pct"] - prev["asset_reuse_pct"], 1),
            "asset_reuse_now": cur["asset_reuse_pct"], "asset_reuse_before": prev["asset_reuse_pct"],
            "founder_corrections_reduced_pct": corrections_reduced,
            "estimated_ai_savings_usd": cur["ai_cost_avoided_usd"],
            "founder_hours_saved": round(cur["time_saved_minutes"] / 60, 1),
        },
        "current": cur, "previous": prev,
    }
