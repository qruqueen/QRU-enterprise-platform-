"""QRU Factory™ — Capability Registry™ (Consolidation Initiative · Phase 1/6/7).

The governed, living record of every Factory capability. No capability remains
dormant without an intentional status. This is the canonical manufacturing
architecture: One Knowledge Record™ → Many Products™.

Treasure Standard™: statuses are honest recommendations surfaced for Founder
review. Nothing is deleted. Founder status edits are preserved across re-seeds
($setOnInsert for status; descriptive fields refreshed on every boot).
"""
from datetime import datetime, timezone
from database import db

COLLECTION = "capability_registry"

# --- Status vocabulary (intentional lifecycle states) ---
STATUSES = ["active", "inherited", "deprecated", "merged", "future"]
STATUS_LABEL = {
    "active": "Active",
    "inherited": "Inherited",
    "deprecated": "Deprecated",
    "merged": "Merged",
    "future": "Future Backlog",
}

# --- Manufacturing Map™ layers (Phase 7 canonical flow) ---
LAYERS = [
    ("knowledge", "Knowledge Record™", "The single verified source of truth."),
    ("engine", "Understanding Engine™", "Turns verified knowledge into manufacturable plans."),
    ("publishing", "Publishing", "Books, PDFs, covers, print-ready editions."),
    ("learning", "Learning", "Courses, colleges, classroom material."),
    ("entertainment", "Entertainment", "Story & Cinema Studio™ — motion, characters, episodes."),
    ("marketing", "Marketing", "Posters, promo assets, campaigns."),
    ("audio", "Audio", "Narration, audiobooks, podcasts."),
    ("video", "Video", "Motion storybooks, educational video, shorts."),
    ("assessment", "Assessment", "Quality gates, quizzes, verification."),
    ("distribution", "Distribution", "Store, YouTube, Podcast, Classroom, Enterprise, Future."),
    ("governance", "Governance & Trust", "Constitution, standards, protection, authenticity."),
    ("enterprise", "Enterprise & Mission Control", "Command, health, autonomy, economics."),
    ("admin", "Administration", "Integrations, users, configuration."),
    ("future", "Future Backlog", "Architecture-ready, not yet built."),
]
LAYER_NAME = {k: n for k, n, _ in LAYERS}

# The Manufacturing Promise™ (Phase 6) — every product inherits these five pillars.
MANUFACTURING_PROMISE = {
    "title": "The QRU Manufacturing Promise™",
    "statement": "Every product manufactured by the QRU Factory™ inherits from a verified source — never invented, never faked.",
    "pillars": [
        {"id": "verified_knowledge", "name": "Verified Knowledge™",
         "description": "Manufactured only from a Verified Knowledge Record™ — no AI-hallucinated facts reach a customer."},
        {"id": "constitutional_governance", "name": "Constitutional Governance™",
         "description": "Bound to the Factory Constitution™ and the standards that govern its product type."},
        {"id": "enterprise_memory", "name": "Enterprise Memory™",
         "description": "Reuses approved assets, characters, and institutional knowledge instead of regenerating from scratch."},
        {"id": "treasure_standard", "name": "Treasure Standard™",
         "description": "Absolute honesty: no fake metrics, no fake publishing states, no silent failures."},
        {"id": "continuous_craftsmanship", "name": "Continuous Craftsmanship™",
         "description": "Improved by every run through inspection, refinement, and the improvement loop."},
    ],
}


def _c(cid, name, layer, status, owner, route, original, current,
       inherited_from=None, duplicate_of=None, note="", moat=False):
    return {
        "id": cid, "name": name, "layer": layer, "status": status,
        "owner": owner, "route": route,
        "original_purpose": original, "current_purpose": current,
        "inherited_from": inherited_from, "duplicate_of": duplicate_of,
        "note": note, "moat": moat,
    }


# ============================================================
# CAPABILITY DEFINITIONS — the audited menu of the Factory.
# ============================================================
DEFINITIONS = [
    # ---------- KNOWLEDGE (source) ----------
    _c("kr-manufacturing", "Knowledge Record Manufacturing™", "knowledge", "active", "kr_manufacturing.py", "/kr-manufacturing",
       "Manufacture governed Knowledge Records from a source.", "The Factory's first responsibility — Idea→Research→Verify→Founder Review→Enterprise Memory™. One KR, many products.", moat=True),
    _c("knowledge-records", "Knowledge Records", "knowledge", "active", "routers/knowledge.py", "/knowledge",
       "Store verified knowledge.", "Single source of verified truth — every product inherits from here.", moat=True),
    _c("kr2", "Knowledge Architecture™ (KR 2.0)", "knowledge", "active", "routers/knowledge_v2.py", "/kr2",
       "36-section versioned knowledge model.", "Canonical KR schema: one record, many products.", moat=True),
    _c("topic-registry", "Topic Registry™", "knowledge", "active", "routers/registry.py", "/topic-registry",
       "Decide what to teach and in what order.", "Curriculum backbone feeding the promotion pipeline."),
    _c("promotion-pipeline", "Promotion Pipeline™", "knowledge", "active", "routers/promotion.py", "/promotion-pipeline",
       "Turn a topic seed into verified knowledge.", "Governed path Topic Seed → Verified KR."),
    _c("library-import", "Bulk Library Import™", "knowledge", "active", "routers/library_import.py", "/library-import",
       "Import folders of documents.", "Batch source ingestion into draft KRs."),
    _c("translation-engine", "Translation Engine™", "knowledge", "active", "translation_pipeline.py", "/translation-engine",
       "Make knowledge truly understandable.", "Audience-tuned rewriting stage."),
    _c("research", "Research Center", "knowledge", "active", "knowledge_extraction.py", "/research",
       "Gather evidence.", "Source gathering + citation capture."),
    _c("verification", "Verification Center", "knowledge", "active", "routers/verification.py", "/verification",
       "Confirm we can trust it.", "Founder-facing verification surface.", moat=True),
    _c("verification-team", "Verification Team™", "knowledge", "active", "verification_engine.py", "/verification-team",
       "Verify automatically at scale.", "Autonomous AI verification + revision loop.", moat=True),
    _c("memory-engineering", "Memory Engineering™", "knowledge", "active", "memory_engineering.py", "/memory-engineering",
       "Make it memorable.", "Retention engineering for every KR."),
    _c("qiks", "Institutional Knowledge™", "knowledge", "active", "routers/qiks.py", "/qiks",
       "Remember what QRU has learned.", "Standards library — Governed-by traceability source.", moat=True),

    # ---------- UNDERSTANDING ENGINE ----------
    _c("refinement", "Refinement Engines™", "engine", "active", "refinement_engine.py", "/refinement",
       "Prove the factory manufactures knowledge & products.", "Knowledge/product manufacturing proof engine."),
    _c("flow", "Manufacturing Flow™", "engine", "active", "manufacturing_flow.py", "/flow",
       "See where every project is and what's next.", "Canonical project flow view."),
    _c("architecture", "Architecture Explorer™", "engine", "active", "enterprise_architecture.py", "/architecture",
       "See how the whole factory is organized.", "Enterprise architecture explorer."),
    _c("workflows", "Workflow Engine™", "engine", "active", "workflow_engine.py", "/workflows",
       "Decide what happens next.", "Governed pipeline + job queue + auto recovery.", moat=True),
    _c("orchestrator", "Bulk Orchestrator™", "engine", "active", "orchestrator.py", "/orchestrator",
       "Scale production without breaking.", "Parallel batch manufacturing."),
    _c("director", "Manufacturing Director™", "engine", "active", "manufacturing_director.py", "/director",
       "Approve/hold/reject orders with gap analysis.", "Supervisory manufacturing intelligence.", moat=True),
    _c("manufacturing", "Manufacturing Orders", "engine", "active", "routers/manufacturing.py", "/manufacturing",
       "Track what's being built.", "Production order tracking."),
    _c("manufacture", "Product Manufacturing", "engine", "active", "product_automation.py", "/manufacture",
       "Make the actual product.", "Primary product manufacturing surface."),
    _c("knowledge-manufacturing", "Manufacturing Dashboard™", "engine", "active", "routers/manufacturing_dashboard.py", "/knowledge-manufacturing",
       "See what each KR has manufactured.", "Canonical KR → products manufacturing map."),
    _c("manufacturing-studio", "Manufacturing Studio", "engine", "merged", "manufacturing2.py", "/manufacturing-studio",
       "Assemble & finalize products.", "Overlaps Product Manufacturing — consolidate.",
       duplicate_of="manufacture", note="Recommend merging into Product Manufacturing."),
    _c("mfg-command", "Manufacturing Command™", "engine", "merged", "routers/manufacturing_dashboard.py", "/mfg-command",
       "Live factory command view.", "Overlaps Manufacturing Dashboard™ — consolidate.",
       duplicate_of="knowledge-manufacturing", note="Recommend merging into Manufacturing Dashboard™."),

    # ---------- PUBLISHING ----------
    _c("publishing", "Publishing Standard™", "publishing", "active", "publishing_standard.py", "/publishing",
       "Define how every product looks & reads.", "Governing standard for all published output.", moat=True),
    _c("cover-studio", "Cover Studio™", "publishing", "active", "poster_studio.py", "/cover-studio",
       "Produce premium on-brand covers.", "Branded cover manufacturing."),
    _c("products", "My Products", "publishing", "active", "routers/products.py", "/products",
       "Find every manufactured product.", "Canonical product shelf."),
    _c("product-library", "Product Library", "publishing", "merged", "routers/products.py", "/product-library",
       "Browse manufactured products.", "Overlaps My Products — consolidate.",
       duplicate_of="products", note="Recommend merging into My Products."),
    _c("companion", "Companion System™", "publishing", "active", "product_recipes.py", "/companion",
       "Let products live beyond the page.", "QR/companion experiences for products."),

    # ---------- LEARNING ----------
    _c("colleges", "Understanding Colleges", "learning", "active", "college_activation.py", "/colleges",
       "Teach subjects at depth.", "Modular subject colleges."),
    _c("teach", "What to Teach Today", "learning", "active", "routers/pipeline.py", "/teach",
       "Choose today's lesson.", "Production line entry for teaching."),

    # ---------- ENTERTAINMENT (Story & Cinema Studio™) ----------
    _c("storyboard-studio", "Storyboard Studio™", "entertainment", "active", "storyboard_master.py", "/storyboard-studio",
       "Turn one KR into many media formats.", "Multi-format storyboarding engine.", moat=True),
    _c("little-legacy", "Little Legacy Learners™", "entertainment", "active", "little_legacy_production.py", "/little-legacy",
       "Teach children through a governed animated universe.", "Flagship franchise — Character Identity Consistency™.", moat=True),
    _c("flagship-showcase", "Flagship Showcase™", "entertainment", "active", "flagship_showcase.py", "/flagship-showcase",
       "Manufacture governed multi-scene video.", "Scene-by-scene governed video manufacturing."),
    _c("media-studio", "Media Studio™", "entertainment", "active", "media_production.py", "/media-studio",
       "Bring products to life in sound & motion.", "Canonical media manufacturing studio."),
    _c("wis", "Character Library™", "entertainment", "active", "character_registry.py", "/wis",
       "Keep official reusable characters.", "Workforce Identity System™ — brand-consistent characters.", moat=True),
    _c("media-library", "Stock Media Library™", "entertainment", "active", "media_library.py", "/media-library",
       "Track licensed video & audio.", "Provenance-verified stock media."),
    _c("creative-studio", "Creative Studio™", "entertainment", "merged", "creative_director.py", "/creative-studio",
       "Make it beautiful and engaging.", "Overlaps Media Studio™ — consolidate.",
       duplicate_of="media-studio", note="Recommend merging into Media Studio™."),
    _c("visual-studio", "Visual & Media Studio™", "entertainment", "merged", "visual_studio.py", "/visual-studio",
       "Make it visible & shareable.", "Overlaps Media Studio™ — consolidate.",
       duplicate_of="media-studio", note="Recommend merging into Media Studio™."),
    _c("media-starter-kit", "Media Starter Kit™", "entertainment", "merged", "media_starter_kit.py", "/media-starter-kit",
       "Package products for every media format.", "Overlaps Media Studio™ — consolidate.",
       duplicate_of="media-studio", note="Recommend merging into Media Studio™."),

    # ---------- MARKETING ----------
    _c("poster-studio", "Poster Studio™", "marketing", "active", "poster_studio.py", "/poster-studio",
       "Manufacture governed infographic posters.", "Poster & marketing asset manufacturing.", moat=True),

    # ---------- ASSESSMENT ----------
    _c("inspection", "Quality Gates™", "assessment", "active", "inspection_system.py", "/inspection",
       "Decide if a product is good enough.", "9 objective blocking quality gates.", moat=True),

    # ---------- DISTRIBUTION ----------
    _c("store", "QRU Store™", "distribution", "active", "commerce.py", "/store",
       "Let people buy what we make.", "Owned native marketplace + Stripe checkout.", moat=True),
    _c("youtube", "YouTube Publisher™", "distribution", "active", "youtube_publisher.py", "/youtube",
       "Publish real videos to YouTube.", "Real resumable upload with verified Video ID."),
    _c("connectors", "Publishing Connectors™", "distribution", "active", "connectors.py", "/connectors",
       "Connect publishing destinations.", "Universal connector framework (OAuth)."),
    _c("distribution", "Distribution Center™", "distribution", "active", "distribution/", "/distribution",
       "Publish everywhere, verified, from one place.", "Universal Distribution Framework™.", moat=True),

    # ---------- GOVERNANCE & TRUST ----------
    _c("constitution", "Factory Constitution™", "governance", "active", "constitution_v1.py", "/constitution",
       "Govern everything the factory makes.", "Supreme governing document.", moat=True),
    _c("governance", "Governance Center™", "governance", "active", "qru_governance.py", "/governance",
       "See the rules that govern products.", "Governance surface + binding layer."),
    _c("trust", "Trust & Authenticity™", "governance", "active", "trust_authenticity.py", "/trust",
       "Prove products are authentic & registered.", "Authenticity registry."),
    _c("agents", "Factory Agents™", "governance", "active", "routers/qics.py", "/agents",
       "Know who governs manufacturing.", "Governing agents & standards."),
    _c("product-protection", "Product Protection™", "governance", "active", "product_protection.py", "/product-protection",
       "Protect & license products.", "Licensing & protection registry."),
    _c("design-director", "Design Director™", "governance", "active", "design_director.py", "/design-director",
       "Polish every product before the Founder sees it.", "Design QC gate."),
    _c("design-intelligence", "Design Intelligence™", "governance", "active", "design_intelligence.py", "/design-intelligence",
       "Repeat great QRU design.", "Design language & pattern library."),

    # ---------- ENTERPRISE & MISSION CONTROL ----------
    _c("factory-map", "Factory Map™", "enterprise", "active", "capability_registry.py", "/factory-map",
       "See the canonical manufacturing architecture.", "Capability Registry™ + Manufacturing Map™ — one KR, many products.", moat=True),
    _c("dashboard", "Founder Console", "enterprise", "active", "routers/command.py", "/",
       "Focus the Founder each day.", "Founder mission-control home."),
    _c("create", "Create", "enterprise", "active", "factory_os.py", "/create",
       "Start something new.", "Outcome-first creation entry."),
    _c("concierge", "Factory Concierge™", "enterprise", "active", "factory_concierge.py", "/concierge",
       "Set up the right workflow conversationally.", "Conversational guide over Factory OS."),
    _c("projects", "My Projects", "enterprise", "active", "continuity.py", "/projects",
       "See each project and the next step.", "Product Continuity Principle™ tracker."),
    _c("founder-inbox", "Founder Review Inbox™", "enterprise", "active", "routers/founder_inbox.py", "/founder-inbox",
       "Approve & publish what's ready.", "Founder approval queue.", moat=True),
    _c("command-center", "Enterprise Command Center™", "enterprise", "active", "routers/command_center.py", "/command-center",
       "See how the whole enterprise is doing.", "Canonical enterprise command view."),
    _c("evidence", "Evidence Dashboard™", "enterprise", "active", "routers/metrics.py", "/evidence",
       "Show where every number came from.", "Evidence-backed metrics.", moat=True),
    _c("factory-health", "Factory Health™", "enterprise", "active", "factory_audit.py", "/factory-health",
       "See how healthy the factory is.", "Canonical health & learning view."),
    _c("factory-monitor", "Factory Monitor™", "enterprise", "active", "orchestrator.py", "/factory-monitor",
       "See what's happening right now.", "Real-time production monitor."),
    _c("failure-intelligence", "Failure Intelligence™", "enterprise", "active", "failure_intelligence.py", "/failure-intelligence",
       "Understand why a run failed.", "Classify → recover → learn."),
    _c("autonomy", "Autonomy Center™", "enterprise", "active", "autonomous_engine.py", "/autonomy",
       "Run and improve ourselves.", "Level-5 autonomy scaffolding.", moat=True),
    _c("enterprise-autonomy", "Continuous Improvement™", "enterprise", "active", "continuous_improvement.py", "/enterprise-autonomy",
       "Make the factory better every run.", "Closed improvement loop."),
    _c("analytics", "Analytics", "enterprise", "active", "routers/analytics.py", "/analytics",
       "Understand the numbers.", "Performance analytics."),
    _c("manufacturing-economics", "Manufacturing Economics™", "enterprise", "active", "economics.py", "/manufacturing-economics",
       "See product cost & profit.", "Unit economics."),
    _c("first-dollar", "First Dollar Mode™", "enterprise", "active", "first_dollar.py", "/first-dollar",
       "Confirm a real customer will pay.", "Revenue-first validation."),
    _c("factory-readiness", "Factory Readiness™", "enterprise", "active", "readiness.py", "/factory-readiness",
       "Choose what to manufacture first.", "Readiness scoring."),
    _c("customers", "Customers", "enterprise", "active", "routers/misc.py", "/customers",
       "Know who we serve.", "Customer records."),
    _c("workforce", "Digital Workforce", "enterprise", "active", "routers/workforce.py", "/workforce",
       "Know which AI does each job.", "Digital workforce roster."),
    _c("organization", "Organization", "enterprise", "active", "routers/organization.py", "/organization",
       "Know who does the work.", "Org & department registry."),
    _c("asset-vault", "Asset Vault™", "enterprise", "active", "vault.py", "/asset-vault",
       "Reuse approved assets instead of regenerating.", "Digital Asset Vault™ (DAM).", moat=True),
    _c("command", "Command Console", "enterprise", "merged", "routers/command.py", "/command",
       "Do things in your own words.", "Overlaps Factory Concierge™ — consolidate.",
       duplicate_of="concierge", note="Recommend merging into Factory Concierge™."),
    _c("enterprise-health", "Enterprise Health", "enterprise", "merged", "routers/enterprise.py", "/enterprise-health",
       "See if the enterprise is healthy.", "Overlaps Factory Health™ — consolidate.",
       duplicate_of="factory-health", note="Recommend merging into Factory Health™."),
    _c("blueprint", "Enterprise Blueprint™", "enterprise", "merged", "department_registry.py", "/blueprint",
       "See what every department does.", "Overlaps Architecture Explorer™ — consolidate.",
       duplicate_of="architecture", note="Recommend merging into Architecture Explorer™."),
    _c("experience-lab", "Experience Lab™", "enterprise", "deprecated", "routers/enterprise.py", "/experience-lab",
       "Feel how it is to learn.", "Early prototype — no active manufacturing role.",
       note="Recommend deprecating; superseded by consumer preview."),

    # ---------- ADMINISTRATION ----------
    _c("integration-hub", "Integration Hub™", "admin", "active", "integration_hub.py", "/integration-hub",
       "See what we're connected to.", "External integration status."),
    _c("ai-services", "AI Services™", "admin", "active", "ai_services_manager.py", "/ai-services",
       "See which AI powers are available.", "AI provider registry."),
    _c("users", "User Management", "admin", "active", "routers/misc.py", "/users",
       "Manage access.", "Users & roles."),
    _c("portability", "Portability Center™", "admin", "active", "routers/portability.py", "/portability",
       "Back up & redeploy QRU.", "Export/redeploy."),
    _c("engineering-console", "Engineering Console", "admin", "active", "routers/autonomy_engine.py", "/engineering-console",
       "See technical diagnostics.", "Developer diagnostics."),
    _c("settings", "Settings", "admin", "active", "routers/misc.py", "/settings",
       "Configure the factory.", "Configuration."),

    # ---------- FUTURE BACKLOG (Phase 8 — architecture-ready, not built) ----------
    _c("media-division", "Media Manufacturing Division™", "publishing", "active", "media_division.py", "/media-division",
       "One verified KR → the full media catalog.", "Manufacture books, guides, slides, posters & scripts from one governed KR. Every product inherits the Manufacturing Promise™.", moat=True),
    _c("cinema-studio", "Story & Cinema Studio™", "video", "active", "cinema_studio.py", "/cinema-studio",
       "Manufacture narrated motion video from a verified KR.", "Motion Storybooks™, episodes, shorts & promos — image-based motion (Ken Burns) + narration. Truthful: not frame-by-frame animation.", moat=True),
    _c("podcast-studio", "Podcast Studio™", "audio", "active", "cinema_studio.py", "/cinema-studio",
       "Manufacture narrated audio from a verified KR.", "Audiobooks & podcast episodes via real OpenAI TTS narration — inherits verified knowledge & Voice.", moat=True),
    _c("cinema-studio-future", "Feature Film Prep", "future", "future", None, None,
       "Feature-length production prep.", "Phase 8 backlog — architecture-ready only."),
    _c("feature-film", "Feature Film Manufacturing", "future", "future", None, None,
       "Feature-length animated films.", "Phase 8 backlog — architecture-ready only."),
    _c("streaming", "Streaming Distribution", "future", "future", None, None,
       "Distribute to streaming platforms.", "Phase 8 backlog."),
    _c("interactive-learning", "Interactive Learning", "future", "future", None, None,
       "Interactive lessons & assessments.", "Phase 8 backlog."),
    _c("trending-topics", "Trending Topic Manufacturing", "future", "future", None, None,
       "Manufacture from trending topics.", "Phase 8 backlog."),
    _c("multi-language", "Multi-language Production", "future", "future", None, None,
       "Produce in many languages.", "Phase 8 backlog — inherits Translation Engine™."),
    _c("ai-tutor", "AI Tutor Expansion", "future", "future", None, None,
       "Personal AI tutor from verified KRs.", "Phase 8 backlog."),
    _c("documentary", "Documentary Manufacturing", "future", "future", None, None,
       "Documentary & companion production.", "Phase 8 backlog."),
]


def _now():
    return datetime.now(timezone.utc).isoformat()


async def seed():
    """Idempotent. Founder status edits (founder_locked=True) are preserved; everything
    else follows the authoritative definitions and descriptive fields refresh on boot."""
    for d in DEFINITIONS:
        setter = {k: v for k, v in d.items() if k != "status"}
        setter["updated_at"] = _now()
        await db[COLLECTION].update_one(
            {"id": d["id"]},
            {"$set": setter,
             "$setOnInsert": {"status": d["status"], "founder_locked": False, "created_at": _now()}},
            upsert=True,
        )
        # Non-locked capabilities follow the definition's status (keeps the registry authoritative).
        await db[COLLECTION].update_one(
            {"id": d["id"], "founder_locked": {"$ne": True}},
            {"$set": {"status": d["status"]}},
        )


async def list_capabilities(layer=None, status=None):
    q = {}
    if layer:
        q["layer"] = layer
    if status:
        q["status"] = status
    docs = await db[COLLECTION].find(q, {"_id": 0}).to_list(1000)
    order = {k: i for i, (k, _, _) in enumerate(LAYERS)}
    docs.sort(key=lambda d: (order.get(d.get("layer"), 99), d.get("name", "")))
    return docs


async def summary():
    docs = await db[COLLECTION].find({}, {"_id": 0}).to_list(1000)
    by_status = {s: 0 for s in STATUSES}
    by_layer = {}
    moats = 0
    for d in docs:
        by_status[d.get("status", "active")] = by_status.get(d.get("status", "active"), 0) + 1
        by_layer[d.get("layer")] = by_layer.get(d.get("layer"), 0) + 1
        if d.get("moat"):
            moats += 1
    return {
        "total": len(docs),
        "by_status": [{"status": s, "label": STATUS_LABEL[s], "count": by_status.get(s, 0)} for s in STATUSES],
        "by_layer": [{"layer": k, "name": n, "count": by_layer.get(k, 0)} for k, n, _ in LAYERS],
        "moats": moats,
        "needs_review": by_status.get("deprecated", 0) + by_status.get("merged", 0),
    }


async def manufacturing_map():
    """Phase 7 canonical visual: layer → live capabilities feeding it."""
    docs = await db[COLLECTION].find({}, {"_id": 0}).to_list(1000)
    grouped = {k: [] for k, _, _ in LAYERS}
    for d in docs:
        grouped.setdefault(d.get("layer"), []).append(d)
    nodes = []
    for k, name, desc in LAYERS:
        caps = sorted(grouped.get(k, []), key=lambda x: x.get("name", ""))
        nodes.append({
            "layer": k, "name": name, "description": desc,
            "capabilities": [
                {"id": c["id"], "name": c["name"], "status": c["status"],
                 "route": c.get("route"), "moat": c.get("moat", False)}
                for c in caps
            ],
        })
    # The distribution destinations (Universal Distribution Framework™ targets)
    destinations = ["QRU Store™", "YouTube", "Podcast", "Classroom", "Enterprise", "Future"]
    return {
        "promise": MANUFACTURING_PROMISE,
        "flow": ["Knowledge Record™", "Understanding Engine™", "Creative Divisions", "Distribution"],
        "nodes": nodes,
        "destinations": destinations,
    }


async def set_status(cap_id, status, founder_name):
    if status not in STATUSES:
        return None
    res = await db[COLLECTION].update_one(
        {"id": cap_id},
        {"$set": {"status": status, "founder_locked": True,
                  "status_changed_by": founder_name, "updated_at": _now()}},
    )
    if not res.matched_count:
        return None
    return await db[COLLECTION].find_one({"id": cap_id}, {"_id": 0})


# --- Self-cleaning sidebar (driven by the Registry) ---
# Layers pinned to the top "Start Here" section (by capability id).
NAV_PINNED = ["factory-map", "dashboard", "create", "concierge", "projects"]
# Friendly sidebar section titles per layer.
NAV_SECTION = {
    "knowledge": "Knowledge",
    "engine": "Manufacturing Engine",
    "publishing": "Publishing",
    "learning": "Learning",
    "entertainment": "Story & Cinema",
    "marketing": "Marketing",
    "audio": "Audio",
    "video": "Video",
    "assessment": "Quality",
    "distribution": "Distribution",
    "governance": "Governance & Trust",
    "enterprise": "Mission Control",
    "admin": "Administration",
}


async def navigation():
    """The sidebar, generated from the Registry. Active/Inherited routed capabilities
    are grouped by division; Merged/Deprecated collapse into 'Legacy — Under Review'."""
    docs = await db[COLLECTION].find({}, {"_id": 0}).to_list(1000)
    by_id = {d["id"]: d for d in docs}

    pinned = []
    for cid in NAV_PINNED:
        d = by_id.get(cid)
        if d and d.get("route"):
            pinned.append({"id": d["id"], "label": d["name"], "route": d["route"],
                           "hint": d.get("current_purpose", ""), "moat": d.get("moat", False)})

    order = {k: i for i, (k, _, _) in enumerate(LAYERS)}
    sections, legacy = [], []
    grouped = {}
    for d in docs:
        if d["id"] in NAV_PINNED:
            continue
        route = d.get("route")
        if not route:
            continue
        status = d.get("status")
        item = {"id": d["id"], "label": d["name"], "route": route,
                "hint": d.get("current_purpose", ""), "moat": d.get("moat", False), "status": status}
        if status in ("merged", "deprecated"):
            item["duplicate_of"] = d.get("duplicate_of")
            legacy.append(item)
        elif status in ("active", "inherited"):
            grouped.setdefault(d["layer"], []).append(item)

    for layer_key in sorted(grouped.keys(), key=lambda k: order.get(k, 99)):
        items = sorted(grouped[layer_key], key=lambda x: x["label"])
        sections.append({"layer": layer_key, "label": NAV_SECTION.get(layer_key, layer_key), "items": items})

    legacy.sort(key=lambda x: x["label"])
    return {"pinned": pinned, "sections": sections, "legacy": legacy}

