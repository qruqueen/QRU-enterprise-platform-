"""QRU Enterprise Manufacturing Dashboard™ (MO-002 / P6) — the command center.

Deterministic ($0 AI) aggregation of the whole factory: Knowledge Records, products
manufactured & in queue, connector status/health, publishing, real revenue, licensing,
throughput, quality scores, Treasure Standard™ status, and live manufacturing alerts.
Composes existing engines (Inspection System™, Connectors, real payment records).
"""
import os
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends

from database import db
from auth import get_current_user
import connectors as cx
import inspection_system as insp

router = APIRouter(prefix="/api/manufacturing-dashboard", tags=["manufacturing-dashboard"])

STRIPE_TEST = os.environ.get("STRIPE_API_KEY", "").startswith("sk_test_")


@router.get("")
async def dashboard(user=Depends(get_current_user)):
    # --- Knowledge Records ---
    kr_total = await db.knowledge_records.count_documents({})
    kr_verified = await db.knowledge_records.count_documents({"verification_status": "Verified"})

    # --- Products ---
    prod_total = await db.products.count_documents({})
    prod_published = await db.products.count_documents({"status": "Published"})
    prod_treasure = await db.products.count_documents({"treasure_standard": True})

    # --- Manufacturing queue / throughput ---
    orders = await db.production_orders.find().sort("created_at", -1).to_list(1000)
    in_queue = sum(1 for o in orders if o.get("status") in ("manufacturing", "queued", "in_progress", "running"))
    completed = sum(1 for o in orders if o.get("status") == "completed")
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    throughput_7d = sum(1 for o in orders if (o.get("created_at") or "") >= week_ago)

    # --- Quality (Inspection System™) ---
    ops = 0
    connectors = await cx.list_connectors()
    ops = sum(1 for c in connectors if c["operational"])
    products = await db.products.find().to_list(500)
    cleared = paused = 0
    score_sum = 0
    for p in products:
        r = insp.inspect_product(p, ops)
        score_sum += r["overall_score"]
        if r["manufacturing_allowed"]:
            cleared += 1
        else:
            paused += 1
    avg_quality = round(score_sum / len(products)) if products else 0

    # --- Revenue (REAL Stripe records only) ---
    paid = await db.payment_transactions.find({"payment_status": "paid"}).to_list(2000)
    revenue = round(sum(t.get("amount", 0) or 0 for t in paid), 2)

    # --- Licensing ---
    licenses = await db.product_licenses.count_documents({})

    # --- Connector health ---
    connector_health = [
        {"name": c["name"], "status": c["status"], "operational": c["operational"],
         "category": c["category"], "account": c.get("account")}
        for c in connectors
    ]

    # --- Manufacturing alerts (honest, actionable) ---
    alerts = []
    if paused:
        alerts.append({"level": "warn", "message": f"{paused} products are paused by the Inspection System™ — open Quality Gates™ to see what's missing.", "link": "/inspection"})
    needs_auth = [c["name"] for c in connectors if c["status"] in ("Needs Authorization", "Reconnect Required", "Connection Expired")]
    if needs_auth:
        alerts.append({"level": "warn", "message": f"Connectors need attention: {', '.join(needs_auth)}.", "link": "/connectors"})
    if STRIPE_TEST:
        alerts.append({"level": "info", "message": "Stripe is in TEST mode — revenue shown is from test orders, not live payments.", "link": "/evidence"})
    if kr_total and kr_verified < kr_total:
        alerts.append({"level": "info", "message": f"{kr_total - kr_verified} Knowledge Records are not yet Verified — they cannot manufacture until verified.", "link": None})
    if not alerts:
        alerts.append({"level": "ok", "message": "No manufacturing alerts — the factory is healthy.", "link": None})

    return {
        "knowledge_records": {"total": kr_total, "verified": kr_verified, "provenance": "LIVE"},
        "products_manufactured": {"total": prod_total, "published": prod_published, "provenance": "LIVE"},
        "products_in_queue": {"value": in_queue, "completed": completed, "provenance": "LIVE"},
        "connector_status": {"operational": ops, "total": len(connectors), "provenance": "LIVE"},
        "publishing_status": {"published": prod_published, "provenance": "LIVE"},
        "revenue": {"value": revenue, "provenance": "TEST" if STRIPE_TEST else ("LIVE" if paid else "NOT_TRACKED"),
                    "orders": len(paid)},
        "licensing": {"value": licenses, "provenance": "LIVE" if licenses else "NOT_TRACKED"},
        "manufacturing_throughput": {"last_7_days": throughput_7d, "total_orders": len(orders), "provenance": "LIVE"},
        "quality_scores": {"average": avg_quality, "cleared": cleared, "paused": paused, "provenance": "LIVE"},
        "treasure_standard": {"certified": prod_treasure, "total": prod_total, "provenance": "LIVE"},
        "connector_health": connector_health,
        "alerts": alerts,
    }
