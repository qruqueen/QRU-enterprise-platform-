"""QRU Factory Readiness Score™ (MT-026) — decision-support ONLY.

Computes, per product type, how ready the factory is to manufacture, review, publish,
and SELL it — blending current factory capability (deterministic maturity of the
manufacturing + rendering pipeline) with live product data. Scores improve automatically
as new capabilities land and as real products get certified & delivered.

This module is strictly informational. It NEVER changes manufacturing, publishing,
approvals, rendering, or any existing workflow — it only reads data.
"""
from database import db

# Per-type baseline maturity of the current factory (0-100) + capability class.
# Baseline reflects how complete/deterministic the manufacture+render pipeline is TODAY.
TYPES = [
    ("Quick Guide",         "document",    100),
    ("Teacher Guide",       "document",    100),
    ("Book",                "document",     98),
    ("Blog Article",        "document",     96),
    ("Poster",              "visual",       96),
    ("Presentation",        "visual",       95),
    ("Student Guide",       "document",     95),
    ("Caregiver Guide",     "document",     94),
    ("Short-form Content",  "document",     92),
    ("Flash Cards",         "document",     90),
    ("Quiz",                "document",     88),
    ("Workbook",            "document",     88),
    ("Course",              "document",     86),
    ("Podcast Script",      "script",       84),
    ("Interactive Lesson",  "interactive",  82),
    ("Video Script",        "script",       80),
    ("Audio Narration",     "audio",        68),
    ("Video",               "video",        60),
    ("Animation",           "animation",    45),
    ("Movie",               "movie",        10),
]

# Component weights (sum = 100). Every score is a transparent blend of these six.
WEIGHTS = {
    "manufacturing_reliability": 20,
    "treasure_standard_readiness": 20,
    "rendering_quality": 20,
    "testing_completion": 10,
    "founder_approval_readiness": 15,
    "customer_delivery_readiness": 15,
}

SALE_THRESHOLD = 90  # "Recommended for First Dollar Mode™" cut-off
COMPONENT_LABELS = {
    "manufacturing_reliability": "Manufacturing reliability",
    "treasure_standard_readiness": "Treasure Standard™ readiness",
    "rendering_quality": "Rendering quality",
    "testing_completion": "Testing completion",
    "founder_approval_readiness": "Founder approval readiness",
    "customer_delivery_readiness": "Customer delivery readiness",
}


def _boost(baseline, live_fraction):
    """Upward-only live adjustment: proven success can RAISE a type's score toward 100,
    but legacy/undelivered products never drag capability below its baseline."""
    if live_fraction <= baseline:
        return baseline
    return min(100, round(baseline + (live_fraction - baseline) * 0.5))


async def compute_readiness():
    products = await db.products.find({}).to_list(5000)
    by_type = {}
    for p in products:
        by_type.setdefault(p.get("product_type"), []).append(p)

    rows = []
    for name, klass, baseline in TYPES:
        prods = by_type.get(name, [])
        n = len(prods)
        published = sum(1 for p in prods if p.get("status") == "Published")
        certified = sum(1 for p in prods if p.get("treasure_standard"))
        delivered = sum(1 for p in prods if p.get("deliverable_ready"))
        design_ok = sum(1 for p in prods if not p.get("design_review_required", False) and p.get("deliverable_ready"))

        comp = {
            "manufacturing_reliability": _boost(baseline, round(100 * certified / n) if n else 0),
            "treasure_standard_readiness": _boost(baseline, round(100 * certified / n) if n else 0),
            "rendering_quality": _boost(baseline, round(100 * delivered / n) if n else 0),
            "testing_completion": min(100, baseline + (5 if n else 0)),
            "founder_approval_readiness": _boost(baseline, round(100 * published / n) if n else 0),
            "customer_delivery_readiness": _boost(baseline, round(100 * design_ok / n) if n else 0),
        }
        score = round(sum(comp[k] * w for k, w in WEIGHTS.items()) / 100)
        ready_for_sale = score >= SALE_THRESHOLD and comp["customer_delivery_readiness"] >= SALE_THRESHOLD
        rows.append({
            "product_type": name, "capability_class": klass, "score": score,
            "components": comp, "recommended_for_first_dollar": ready_for_sale,
            "live": {"total": n, "certified": certified, "published": published, "delivered": delivered},
        })

    rows.sort(key=lambda r: r["score"], reverse=True)

    # Live pipeline buckets (informational counts across ALL products).
    review_states = {"Quality Control", "Improving", "Needs Review", "In Review"}
    kr_verified = await db.knowledge_records.count_documents({"verification_status": "Verified"})
    dashboard = {
        "ready_to_manufacture": kr_verified,
        "ready_for_review": sum(1 for p in products if p.get("status") in review_states),
        "ready_for_publication": sum(1 for p in products if p.get("status") == "Ready for Release" and p.get("deliverable_ready")),
        "ready_for_sale": sum(1 for p in products if p.get("status") == "Published" and p.get("deliverable_ready")),
        "highest_readiness": [{"product_type": r["product_type"], "score": r["score"]} for r in rows[:5]],
        "recommended_types": [r["product_type"] for r in rows if r["recommended_for_first_dollar"]],
    }
    return {
        "types": rows,
        "dashboard": dashboard,
        "weights": WEIGHTS,
        "component_labels": COMPONENT_LABELS,
        "sale_threshold": SALE_THRESHOLD,
        "note": "Decision-support only. Scores improve as capabilities complete and products succeed.",
    }
