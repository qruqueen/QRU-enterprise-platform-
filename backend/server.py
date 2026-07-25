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
from routers.factory_audit import router as factory_audit_router
from routers.founder_inbox import router as founder_inbox_router
from routers.autonomy_engine import router as autonomy_engine_router
from routers.asset_manufacturing import router as asset_manufacturing_router
from routers.library_import import router as library_import_router
from routers.connectors import router as connectors_router, oauth_router as oauth_callback_router
from routers.metrics import router as metrics_router
from routers.inspection import router as inspection_router
from routers.manufacturing_dashboard import router as mfg_dashboard_router
from routers.knowledge_v2 import router as kr2_router
from routers.director import router as director_router
from routers.youtube import router as youtube_router
from routers.video_fulfillment import router as video_fulfillment_router
from routers.distribution import router as distribution_router
from routers.governance_binding import router as governance_binding_router
from routers.visual_studio import router as visual_studio_router
from routers.media_starter_kit import router as media_starter_kit_router
from routers.trust import router as trust_router
from routers.qics import router as qics_router
from routers.media_library import router as media_library_router
from routers.factory_os import router as factory_os_router
from routers.publishing import router as publishing_router
from routers.manufacturing_flow import router as manufacturing_flow_router
from routers.enterprise_architecture import router as enterprise_architecture_router
from routers.refinement import router as refinement_router
from routers.media_studio import router as media_studio_router
from routers.little_legacy import router as little_legacy_router
from routers.capability_registry import router as capability_registry_router
from routers.kr_manufacturing import router as kr_manufacturing_router
from routers.media_division import router as media_division_router
from routers.cinema_studio import router as cinema_studio_router
from routers.decoder_engine import router as decoder_engine_router
from routers.book_manufacturing import router as book_manufacturing_router
from routers.family import router as family_router
from routers.audit_exports import router as audit_exports_router
from routers.public_site import router as public_site_router
from routers.public_commerce import router as public_commerce_router
from routers.pilot import router as pilot_router
from routers.manufacturing_standards import router as manufacturing_standards_router
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
    factory_audit_router,
    founder_inbox_router,
    autonomy_engine_router,
    asset_manufacturing_router,
    library_import_router,
    connectors_router,
    oauth_callback_router,
    metrics_router,
    inspection_router,
    mfg_dashboard_router,
    kr2_router,
    director_router,
    youtube_router,
    video_fulfillment_router,
    distribution_router,
    governance_binding_router,
    visual_studio_router,
    media_starter_kit_router,
    trust_router,
    qics_router,
    media_library_router,
    factory_os_router,
    publishing_router,
    manufacturing_flow_router,
    enterprise_architecture_router,
    refinement_router,
    media_studio_router,
    little_legacy_router,
    capability_registry_router,
    kr_manufacturing_router,
    media_division_router,
    cinema_studio_router,
    decoder_engine_router,
    book_manufacturing_router,
    family_router,
    audit_exports_router,
    manufacturing_standards_router,
    public_site_router,
    public_commerce_router,
    pilot_router,
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
    import constitution_v1
    await constitution_v1.seed_constitution_v1()
    import publishing_standard
    await publishing_standard.seed_publishing_standard()
    import manufacturing_flow
    await manufacturing_flow.seed_flow()
    import enterprise_architecture
    await enterprise_architecture.seed_eip()
    import refinement_engine
    await refinement_engine.seed_refinement()
    import little_legacy
    await little_legacy.seed()
    import capability_registry
    await capability_registry.seed()
    import ukr_standard
    try:
        _ukr_rep = await ukr_standard.migrate_to_canonical(actor="System (startup)")
        logger.info(f"UKR canonical migration: {_ukr_rep['migrated']}/{_ukr_rep['total']} records on v1.1 canonical spec ({_ukr_rep['sections_completed_count']} sections populated)")
    except Exception as e:
        logger.error(f"UKR canonical migration skipped: {e}")
    import seed_forex_seeds
    await seed_forex_seeds.seed()
    import book_manufacturing
    await book_manufacturing.seed_pilot()
    import asyncio
    import continuous_improvement
    asyncio.create_task(continuous_improvement.watcher_loop())
    logger.info("QRU Factory seeded and operational")


@app.on_event("shutdown")
async def shutdown():
    client.close()
