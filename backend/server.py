import os
import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from database import client
from auth import auth_router
from seed import seed
from routers.knowledge import router as knowledge_router
from routers.manufacturing import router as manufacturing_router
from routers.workforce import router as workforce_router
from routers.products import router as products_router
from routers.analytics import router as analytics_router
from routers.command import router as command_router
from routers.translation import router as translation_router
from routers.colleges import router as colleges_router
from routers.jobs import router as jobs_router
from routers.organization import router as organization_router, seed_registry
from routers.consumer import router as consumer_router
from routers.command_center import router as command_center_router
from routers.pipeline import router as pipeline_router
from routers.design import router as design_router
from routers.evolution import router as evolution_router
from routers.memory import router as memory_router
from routers.rendering import router as rendering_router
from routers.media import router as media_router
from routers.registry import router as topic_registry_router
from routers.verification import router as verification_router
from routers.orchestrator import router as orchestrator_router
from routers.protection import router as protection_router
from routers.integrations import router as integrations_router
from routers.ai_services import router as ai_services_router
from routers.automation import router as automation_router
from routers.enterprise import router as enterprise_router
from routers.commerce import router as commerce_router, webhook_router as stripe_webhook_router
from routers.workflow import router as workflow_router
from routers.autonomy import router as autonomy_router
from routers.qbos import router as qbos_router
from routers.qeds import router as qeds_router
from routers.governance import router as governance_router
from routers.departments import router as departments_router
from routers.wis import router as wis_router
from routers.qiks import router as qiks_router
from routers.relationships import router as relationships_router
from routers.continuous import router as continuous_router
from routers.first_dollar import router as first_dollar_router
from routers.portability import router as portability_router
from routers.cost_meter import router as cost_meter_router
from routers.readiness import router as readiness_router
from routers.vault import router as vault_router
from routers.economics import router as economics_router
from routers.promotion import router as promotion_router
from routers.failure_intelligence import router as failure_intelligence_router
from routers.marketing import router as marketing_router
from routers.design_director import router as design_director_router
from consumer_seed import seed_consumer_demo
from design_intelligence import seed_design_intelligence
from routers.misc import (
    customers_router, notif_router, health_router, search_router, users_router,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("qru")

app = FastAPI(title="QRU Factory Enterprise OS")


@app.get("/api/")
async def root():
    return {"message": "QRU Factory Enterprise OS", "status": "operational"}


for r in [
    auth_router, knowledge_router, manufacturing_router, workforce_router,
    products_router, analytics_router, command_router, translation_router,
    colleges_router, jobs_router, organization_router, customers_router, notif_router, health_router,
    search_router, users_router, consumer_router, command_center_router, pipeline_router, design_router, evolution_router, memory_router, rendering_router, media_router,
    topic_registry_router, verification_router, orchestrator_router, protection_router, integrations_router,
    ai_services_router, automation_router, enterprise_router,
    commerce_router, stripe_webhook_router, workflow_router, autonomy_router, qbos_router, qeds_router,
    governance_router, departments_router, wis_router, qiks_router,
    relationships_router, continuous_router, first_dollar_router,
    portability_router, cost_meter_router, readiness_router, vault_router, economics_router,
    promotion_router,
    failure_intelligence_router,
    marketing_router,
    design_director_router,
]:
    app.include_router(r)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await seed()
    await seed_registry()
    await seed_consumer_demo()
    await seed_design_intelligence()
    import commerce
    await commerce.ensure_stripe_connection()
    import qbos
    await qbos.seed_qbos()
    import qeds
    await qeds.seed_qeds()
    import constitution
    await constitution.seed_constitution()
    import character_registry
    await character_registry.seed_characters()
    import qiks
    await qiks.seed_qiks()
    import seed_forex_seeds
    await seed_forex_seeds.seed()
    import asyncio
    import continuous_improvement
    asyncio.create_task(continuous_improvement.watcher_loop())
    logger.info("QRU Factory seeded and operational")


@app.on_event("shutdown")
async def shutdown():
    client.close()
