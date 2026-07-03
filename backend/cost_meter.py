"""
QRU AI USAGE & COST METER™ — lightweight, estimated AI spend tracking to protect cash
flow during First Dollar Mode™. Records one event per AI call and aggregates daily/weekly/
monthly, by service, and per product/order. All figures are ESTIMATED unless exact billing
data is available. Never blocks deterministic fallback workflows.
"""
import logging
from datetime import datetime, timezone, timedelta

from database import db

logger = logging.getLogger("qru.cost")

USAGE_COL = db["ai_usage"]
SETTINGS_COL = db["factory_settings"]

# Estimated unit costs (USD). Rough — clearly labeled Estimated in the UI.
UNIT_COST = {
    "text": 0.010,     # per text generation call (approx, model gpt-5.5)
    "image": 0.040,    # per generated image
    "tts": 0.015,      # per voice synthesis
    "video": 0.050,    # per video-related AI call
}
SERVICE_LABELS = {"text": "Text generation", "image": "Image generation", "tts": "TTS / Voice", "video": "Video AI"}

DEFAULT_DAILY_BUDGET = 10.0  # USD soft budget per day
THRESHOLDS = [50, 75, 90, 100]


def _now():
    return datetime.now(timezone.utc)


async def record(service: str, product_id=None, order_id=None, units: float = 1.0, est_cost: float = None):
    """Record an estimated AI usage event. Safe: never raises to the caller."""
    try:
        if service not in UNIT_COST:
            service = "text"
        cost = est_cost if est_cost is not None else round(UNIT_COST[service] * units, 4)
        await USAGE_COL.insert_one({
            "service": service, "product_id": product_id, "order_id": order_id,
            "units": units, "est_cost": cost, "at": _now().isoformat(),
        })
        return cost
    except Exception as e:
        logger.warning(f"cost_meter.record failed (non-blocking): {e}")
        return 0.0


async def _sum_since(since: datetime):
    total = 0.0
    by_service = {k: {"calls": 0, "est_cost": 0.0} for k in UNIT_COST}
    async for e in USAGE_COL.find({"at": {"$gte": since.isoformat()}}):
        s = e.get("service", "text")
        c = e.get("est_cost", 0.0)
        total += c
        if s in by_service:
            by_service[s]["calls"] += 1
            by_service[s]["est_cost"] = round(by_service[s]["est_cost"] + c, 4)
    return round(total, 4), by_service


async def get_budget():
    s = await SETTINGS_COL.find_one({"key": "ai_budget"})
    return {
        "daily_budget_usd": (s or {}).get("daily_budget_usd", DEFAULT_DAILY_BUDGET),
        "override_100": (s or {}).get("override_100", False),
    }


async def set_budget(daily_budget_usd=None, override_100=None):
    update = {"key": "ai_budget"}
    cur = await get_budget()
    update["daily_budget_usd"] = daily_budget_usd if daily_budget_usd is not None else cur["daily_budget_usd"]
    update["override_100"] = override_100 if override_100 is not None else cur["override_100"]
    await SETTINGS_COL.update_one({"key": "ai_budget"}, {"$set": update}, upsert=True)
    return await get_budget()


async def can_spend():
    """Soft control: is optional AI manufacturing allowed right now? (Never blocks fallbacks.)"""
    b = await get_budget()
    today = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    spent, _ = await _sum_since(today)
    pct = round(100 * spent / b["daily_budget_usd"], 1) if b["daily_budget_usd"] else 0
    allowed = pct < 100 or b["override_100"]
    return {"allowed": allowed, "pct": pct, "spent": spent, "budget": b["daily_budget_usd"], "override": b["override_100"]}


async def overview():
    now = _now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week = now - timedelta(days=7)
    month = now - timedelta(days=30)

    daily_total, daily_by = await _sum_since(today)
    weekly_total, _ = await _sum_since(week)
    monthly_total, _ = await _sum_since(month)

    b = await get_budget()
    budget = b["daily_budget_usd"]
    pct = round(100 * daily_total / budget, 1) if budget else 0
    remaining = round(max(0.0, budget - daily_total), 4)

    # active warnings
    warnings = [t for t in THRESHOLDS if pct >= t]
    active_level = max(warnings) if warnings else 0

    # capacity / cap status (reuse continuous improvement probe cache; no forced call)
    try:
        import continuous_improvement as ci
        cap = dict(ci._capacity)
    except Exception:
        cap = {"available": None, "reason": "unknown"}

    # per-product / per-order (last 30 days)
    by_product, by_order = {}, {}
    async for e in USAGE_COL.find({"at": {"$gte": month.isoformat()}}):
        if e.get("product_id"):
            by_product[e["product_id"]] = round(by_product.get(e["product_id"], 0.0) + e.get("est_cost", 0.0), 4)
        if e.get("order_id"):
            by_order[e["order_id"]] = round(by_order.get(e["order_id"], 0.0) + e.get("est_cost", 0.0), 4)

    top_products = sorted(by_product.items(), key=lambda x: -x[1])[:10]

    return {
        "estimated": True,
        "note": "All costs are ESTIMATED from per-call unit rates unless exact provider billing is connected.",
        "daily": {"total": daily_total, "by_service": {SERVICE_LABELS[k]: v for k, v in daily_by.items()}},
        "weekly_total": weekly_total,
        "monthly_total": monthly_total,
        "budget": {"daily_budget_usd": budget, "spent_today": daily_total, "remaining_today": remaining,
                   "percent_used": pct, "override_100": b["override_100"]},
        "warnings": {"thresholds": THRESHOLDS, "active_level": active_level,
                     "message": _warn_message(active_level, b["override_100"])},
        "provider_limits": {
            "provider": "OpenAI (via Emergent Universal Key)",
            "openai_daily_cap": cap.get("reason", "unknown"),
            "capacity_available": cap.get("available"),
            "universal_key_balance": "Not exposed via API — check Profile → Universal Key.",
        },
        "unit_costs": {SERVICE_LABELS[k]: v for k, v in UNIT_COST.items()},
        "per_product": [{"product_id": p, "est_cost": c} for p, c in top_products],
        "per_order": [{"order_id": o, "est_cost": c} for o, c in sorted(by_order.items(), key=lambda x: -x[1])[:10]],
    }


def _warn_message(level, override):
    if level >= 100:
        return "100% of daily AI budget used — optional AI manufacturing is PAUSED. Founder override " + ("is ACTIVE." if override else "required to continue.")
    if level >= 90:
        return "90% of daily AI budget used — consider pausing non-essential AI runs."
    if level >= 75:
        return "75% of daily AI budget used."
    if level >= 50:
        return "50% of daily AI budget used."
    return "Within budget."
