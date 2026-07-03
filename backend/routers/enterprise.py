"""QRU Enterprise Command Center™ — cross-division visibility for the Founder.
Aggregates the six Enterprise Operating Divisions™ into one dashboard."""
from fastapi import APIRouter, Depends

from database import db
from auth import get_current_user
import ai_services_manager as ai
import integration_hub as hub

router = APIRouter(prefix="/api/enterprise", tags=["enterprise"])


@router.get("/command-center")
async def command_center(user=Depends(get_current_user)):
    # Knowledge Division
    kr_total = await db.knowledge_records.count_documents({})
    kr_verified = await db.knowledge_records.count_documents({"verification_status": "Verified"})
    kr_treasure = await db.knowledge_records.count_documents({"treasure_standard": True})
    # Manufacturing Division
    orders = await db.manufacturing_orders.count_documents({})
    products = await db.products.count_documents({})
    published = await db.products.count_documents({"status": "Published"})
    prod_orders = await db.production_orders.count_documents({})
    batches_running = await db.manufacturing_batches.count_documents({"status": "running"})
    # AI Services Division
    ai_status = await ai.status_summary()
    ai_connected = sum(1 for c in ai_status["capabilities"] if c["connected_provider"])
    # Integration Division
    monitor = await hub.monitor_summary()
    # Commerce & Distribution Division
    distributions = await db.distributions.count_documents({})
    licenses = await db.product_licenses.count_documents({})
    protected = await db.products.count_documents({"protected": True})
    # Exceptions
    open_esc = await db.founder_escalations.count_documents({"status": "Open"})

    divisions = [
        {"key": "knowledge", "name": "Knowledge Division™",
         "metrics": {"Records": kr_total, "Verified": kr_verified, "Treasure Certified": kr_treasure},
         "health": "healthy" if kr_total else "idle"},
        {"key": "manufacturing", "name": "Manufacturing Division™",
         "metrics": {"Orders": orders, "Products": products, "Production Runs": prod_orders, "Batches Running": batches_running},
         "health": "active" if batches_running else "healthy"},
        {"key": "ai_services", "name": "AI Services Division™",
         "metrics": {"Capabilities": len(ai_status["capabilities"]), "Connected": ai_connected,
                     "Jobs": ai_status["jobs_total"], "Failed": ai_status["jobs_failed"]},
         "health": "warning" if ai_status["jobs_failed"] else "healthy"},
        {"key": "integration", "name": "Integration Division™",
         "metrics": {"Configured": monitor["platforms_configured"], "Connected": monitor["platforms_connected"],
                     "Unhealthy": len(monitor["unhealthy"])},
         "health": "warning" if monitor["unhealthy"] else "healthy"},
        {"key": "commerce", "name": "Commerce & Distribution Division™",
         "metrics": {"Published": published, "Protected": protected, "Distributions": distributions, "Licenses": licenses},
         "health": "healthy"},
        {"key": "analytics", "name": "Analytics & Intelligence Division™",
         "metrics": {"Products": products, "Published": published,
                     "Publish Rate %": round((published / products * 100) if products else 0),
                     "Open Exceptions": open_esc},
         "health": "warning" if open_esc else "healthy"},
    ]
    return {
        "divisions": divisions,
        "factory_health": "attention" if open_esc or monitor["unhealthy"] or ai_status["jobs_failed"] else "healthy",
        "exceptions": open_esc,
        "portfolio": {"products": products, "published": published, "protected": protected},
        "revenue": {"note": "Connect a payment provider in the Integration Hub to activate revenue tracking.",
                    "licenses_granted": licenses},
    }
