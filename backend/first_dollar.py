"""
QRU FIRST DOLLAR MODE™ — prove the factory manufactures verified products that real
customers voluntarily purchase. The first dollar validates the manufacturing system.

Records FOUNDATION MILESTONE #001 — "The Factory Works." — the moment a real customer
first exchanges money for a QRU-manufactured product. Nothing learned is temporary.
"""
from database import db
from models import now_iso
import qiks

MILESTONE_COL = db["foundation_milestones"]
SETTINGS_COL = db["factory_settings"]

PRIORITIES = [
    "Priority 1 — Manufacture and publish high-value products.",
    "Priority 2 — Collect customer feedback.",
    "Priority 3 — Measure manufacturing performance.",
    "Priority 4 — Repair only issues that block manufacturing or customer experience.",
    "Priority 5 — Document every improvement in the Enterprise Standards Registry™ so the factory becomes permanently smarter.",
]

FREEZE_POLICY = [
    "Do not redesign the architecture.",
    "Do not reorganize departments.",
    "Do not introduce major workflows.",
    "Do not rename systems.",
    "Do not change branding standards.",
]

PHILOSOPHY = "Do not chase perfection. Prove usefulness. The first dollar validates the manufacturing system; future dollars validate scalability."


async def get_mode():
    s = await SETTINGS_COL.find_one({"key": "factory_mode"})
    return (s or {}).get("mode", "first_dollar")


async def set_mode(mode: str):
    await SETTINGS_COL.update_one({"key": "factory_mode"}, {"$set": {"key": "factory_mode", "mode": mode, "updated_at": now_iso()}}, upsert=True)
    return await get_mode()


async def check_and_record_milestone():
    """If a real paid purchase exists and the milestone is not yet recorded, record it permanently."""
    existing = await MILESTONE_COL.find_one({"id": "FOUNDATION-001"})
    first_paid = await db.payment_transactions.find_one({"payment_status": "paid"}, sort=[("created_at", 1)])
    if not first_paid:
        return {"achieved": False, "milestone": existing}
    if existing:
        return {"achieved": True, "milestone": {k: v for k, v in existing.items() if k != "_id"}, "newly_recorded": False}
    milestone = {
        "id": "FOUNDATION-001",
        "name": "FOUNDATION MILESTONE #001",
        "title": "The Factory Works.",
        "description": "A verified customer voluntarily exchanged money for a QRU-manufactured product.",
        "product_id": first_paid.get("product_id"),
        "amount_usd": first_paid.get("amount"),
        "session_id": first_paid.get("session_id"),
        "achieved_at": first_paid.get("updated_at") or now_iso(),
        "recorded_at": now_iso(),
    }
    await MILESTONE_COL.insert_one({**milestone})
    # Make the learning permanent in Institutional Knowledge.
    await qiks.add_lesson(
        title="FOUNDATION MILESTONE #001 — The Factory Works",
        division="Finance",
        lesson=f"First verified customer purchase (${first_paid.get('amount')}) proved the QRU manufacturing system produces products people voluntarily buy. Transition from perfection-chasing to measured iteration.",
        source="First Dollar Mode™",
        reviewer="Crowned Bull™",
    )
    return {"achieved": True, "milestone": milestone, "newly_recorded": True}


async def status():
    mode = await get_mode()
    published = await db.products.count_documents({"status": "Published"})
    storefront = published
    paid = await db.payment_transactions.find({"payment_status": "paid"}).to_list(2000)
    revenue = round(sum(t.get("amount", 0) for t in paid), 2)
    purchases = await db.purchases.count_documents({})
    ms = await check_and_record_milestone()
    return {
        "mode": mode,
        "mode_label": "FIRST DOLLAR MODE™" if mode == "first_dollar" else "FACTORY CONSTRUCTION MODE",
        "philosophy": PHILOSOPHY,
        "priorities": PRIORITIES,
        "freeze_policy": FREEZE_POLICY,
        "primary_objective": "Demonstrate that the factory can consistently manufacture verified educational products that real customers voluntarily purchase.",
        "success_metric": "One verified customer voluntarily exchanging money for a QRU-manufactured product.",
        "progress": {
            "published_products": published,
            "storefront_products": storefront,
            "paid_orders": len(paid),
            "revenue_usd": revenue,
            "fulfilled_purchases": purchases,
        },
        "first_dollar_achieved": ms["achieved"],
        "milestone": ms.get("milestone"),
        "treasure_standard_required": True,
    }
