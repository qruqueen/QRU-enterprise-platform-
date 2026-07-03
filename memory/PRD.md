# QRU FACTORY™ — Product Requirements Document

## Original Problem Statement
Build QRU Factory™, an enterprise Knowledge Manufacturing Operating System for QRU (Quest for Real Understanding). Mission: "QRU manufactures understanding from verified knowledge. QRU does not simplify the truth — it simplifies the path to understanding the truth." The system runs the full workflow: Idea → Research → Verification → Knowledge Record™ → Understanding Translation → Manufacturing Order™ → AI Collaboration → Product Manufacturing → Quality Review → Approval → Publication → Delivery → Continuous Improvement.

## User Choices
- AI: **GPT-5.5** (via Emergent LLM key)
- Auth: **JWT email/password with roles**
- Product content: **Full AI-generated content**
- Design: **Light, clean, minimal enterprise** (Outfit + IBM Plex Sans, primary #0047FF)

## Architecture
- **Backend**: FastAPI (modular routers) + MongoDB (motor). Bearer-token JWT auth, role dependency (`require_roles`). AI via `emergentintegrations` LlmChat (openai/gpt-5.5). All routes under `/api`.
  - Files: `server.py`, `auth.py`, `database.py`, `models.py`, `ai_service.py`, `seed.py`, `routers/{knowledge,manufacturing,workforce,products,analytics,command,misc}.py`
- **Frontend**: React (CRA + craco), react-router v7, Tailwind + shadcn/ui, recharts, sonner. Sidebar Layout + ProtectedRoute. Bearer token in `localStorage['qru_token']`.

## User Personas / Roles
Administrator, Executive, Researcher, Reviewer, Designer, Publisher, Teacher, Customer, ReadOnly.

## Implemented (2026-07-02)
- JWT auth (login/register/me/logout), admin + executive seeded, RBAC on user management.
- Executive Command Center dashboard (KPIs, pipeline, workflow visualization, activity feed).
- Conversational Command Console — AI interprets commands and auto-creates Knowledge Records / Manufacturing Orders / runs research.
- Knowledge Records: data grid, create, detail, AI Understanding Translation, Verify/Approve.
- Research Center (AI research → draft record) and Verification Center.
- Manufacturing Orders: 6-stage Kanban with stage advancement.
- Product Manufacturing: AI generates full Markdown products (18 product types); Product Library + detail with publish/review/archive.
- Digital Workforce: 13 seeded AI Digital Employees with mission/permissions/tools/metrics + detail dialog.
- QRU Health University (7 colleges), Analytics (recharts), Customers/Licensing, Notifications, Global Search, Settings, User Management.
- Verified by testing agent: backend 30/30, frontend 100% of flows.

## Implemented — Iteration 2 (2026-07-02)
- **QRU Teaching Methodology**: Knowledge Records now carry the full 11-part structure (The Question, Simple Answer, Why It Matters, Real-World Example, QRU Translation™, Everyday Analogy, Memory Sentence™, Practice/Application, Key Vocabulary, Deep Roots™, Verification Status) with per-section status (Empty/Draft/Verified). Existing records auto-migrated (content preserved; missing sections AI-fillable, marked Draft).
- **QRU Translation Engine™** (flagship): dedicated page (paste technical text → full methodology) + per-record "Manufacture Understanding" that fills only empty sections, never overwriting verified content.
- **Verification Center redesign**: reviewer evaluates Evidence, Sources, Confidence, Observed Facts, Calculated Data, Analytical Judgment, Conflicting Evidence, Open Questions, Comments → Approve / Reject / Request Revision. Approval promotes Draft sections to Verified and can grant Knowledge Master File™ + Treasure Standard™.
- **AI Director Departments**: workforce cards open department view (metrics, current orders, assigned records, product output, team activity).
- **Executive Command Center expanded**: Enterprise Health, Revenue, Treasure Standard, Verification Queue, Marketplace Ops, workforce status.
- **Understanding Colleges** (modular): Health division active with per-college workspace tabs; future divisions (Trading, Finance, AI, Programming, Parenting, Business, Government) seeded as Coming Soon — all plug into the same OS.
- **Full QRU rebrand**: Royal Purple / Gold / Navy / White, QRU Shield logo, mission statement throughout.
- **QRU Focus Audio**: Web-Audio player (Off/Focus/Calm/Nature/Orchestra/Lo-Fi/Solfeggio/Instrumental), muted by default, header + Settings controls (swappable for licensed audio later).
- **Search** now indexes Colleges. Verified by testing agent: frontend 40/40, backend iteration-2 15/15.

## Implemented — Iteration 4 (2026-07-02) · QRU Enterprise Organization™
- **Executive Board** — 13 AI directors (Kingdom Lion™, Legacy Eagle™, Legacy Bear™, Queen Unity™, Crowned Bull™, Royal Phoenix™, Consumer Advocate™, Marketing/Sales/Brand/Manufacturing/Health, Creative Studio Director™) in an **Expertise Registry** (`registry_agents`) with expertise, workload, availability, projects.
- **Emergent collaboration** — 13 Emergent platform specialists (Software Architect, Security, Testing, Deployment, UX, etc.) registered as origin=Emergent; QRU extends, not replaces them.
- **Collaborative review teams** — `POST /registry/assemble` assembles the most qualified specialists per task type.
- **Live Organization Activity feed** — department-voiced entries emitted during manufacturing (per batch) and verification; polled on the Organization page.
- **QRU Creative Studio™** — brand standards (color system, typography, principles, QRU Shield master asset), AI product-page **creative briefs** (who-for, problem, skills, what's included, reading level, time, next path, related products), a Creative Quality Review queue, and a **publication gate** (products can't publish until Creative-reviewed).
- Verified by testing agent: backend 10/10, frontend 100%. Fixed related-product link projection, publish-gate tightening, and background-job None-guard.


## Implemented — Iteration 3 (2026-07-02) · "Research Once. Verify Once. Manufacture Forever."
- **Expanded Knowledge Record** — ~46 AI-manufacturable fields across 7 batches (Core Understanding, Comprehension Aids, Vocabulary & FAQ, Assessment, Audience Versions, Guidance Notes, Media & Product Assets): incl. Kingdom Lion Verification Questions™, Vocabulary Decoder™, Cheat Sheet™, Conversation Starter™, quiz, FAQ, story/children/teen/adult/professional versions, poster/video/podcast/presentation scripts, lesson plans. Each field has status (Empty/Draft/Verified/Approved) + version history.
- **AI Manufacturing Pipeline** — background job (`manufacturing_engine.py`) runs 7 sequential GPT-5.5 batches with live progress; `POST /knowledge-records/{id}/manufacture-all` → poll `GET /manufacturing-jobs/{id}`; auto-triggers on verification approval. Frontend shows live progress + accordion of manufactured fields with per-field regenerate/approve.
- **Manufacturing Recipes** — `POST /products/assemble` composes products from EXISTING KR fields (no regeneration); assembled products stamped with `kr_version`.
- **Traceability** — editing a KR bumps version and flips dependent products to "Needs Regeneration" (+ notification); `GET /knowledge-records/{id}/dependents`.
- **Dashboard** — Live Manufacturing Jobs panel, Recently Updated Records, needs-regeneration count.
- Verified by testing agent: backend 10/10 (incl. real full-pipeline run), frontend 100%.


## Implemented — Iteration 5 & 6 (2026-07-02) · V2.0 Evolution + Manufacturing Engine 2.0

### Enterprise Mode vs Consumer Mode (role-driven)
- `ModeContext` (frontend): Customer/ReadOnly roles are LOCKED to Consumer Mode; staff default to Enterprise with a header toggle to preview Consumer Mode ("Preview Consumer Mode" / "Enterprise" buttons). `App.js` ModeRouter renders `EnterpriseRoutes` or `ConsumerRoutes`.
- Consumer test user: learner@qru.com / qru-learn-2026 (Customer).

### Consumer Learning Platform (customer-facing, at /learn)
- `ConsumerLayout` + pages: Discover/Catalog, Learn (product), My Learning, Favorites, Certificates, Learning Paths.
- Backend `routers/consumer.py`: catalog, product understanding (assembled from the verified Knowledge Record — no regeneration), enroll, progress, favorite, certificates, pathways, recommendations. Collections: `consumer_enrollments`, `consumer_certificates`.
- Learn page renders: Kingdom Lion™ Verification card (expandable refs), 4-layer Layered Understanding selector (Quick Understanding/Understand It/Scientific Explanation/Professional Resources), 6 Learning Modes (Child/Consumer/Student/Professional/Scientific/Story), the full ordered QRU branded educational structure, Mark Complete → certificate.
- Demo data: 3 fully-populated verified records + published Treasure Standard products seeded via `consumer_seed.py` (is_demo=True, marked with "Demo Data" badges).

### Executive Command Center — Mission-First (Enterprise Mode only)
- New `MissionControl.js` (index dashboard) + `routers/command_center.py`: Daily Executive Briefing, Understanding Impact™ KPIs (people reached, lives helped, master records, understanding assets, lessons completed, certificates, treasure products, etc.) beside business metrics, transparent Enterprise Health breakdown (10 systems, expandable: why/owner/recommendation/urgency/next action), Department Status cards, intelligent Alerts & Recommendations panel, live org activity. ENTERPRISE MODE badge; mission copy "Verified knowledge enters. Understanding grows. Lives improve."
- `EnterpriseHealth.js` full dashboard page; `ExperienceLab.js` (AI experience evaluation).

### Manufacturing Engine 2.0 + Automatic Treasure Standard™ Quality Control
- `manufacturing2.py` + `routers/pipeline.py` (/api/manufacturing2/*): 13 Manufacturing Recipes™ (required KR fields + stages + deliverables), Missing-Content Detection, assembly-first `assemble` (composes from verified fields), `manufacture-missing` (fills only missing fields), Product Assembly stage + deliverables, 8 Release Gates.
- Automatic QC loop: scores product (GPT), routes each failing criterion to its owning department (routing rules), auto-improves (real GPT content rewrite + Creative Studio deterministic branding for Visual/Accessibility/Brand), re-scores monotonically until Treasure Standard™ thresholds met → certifies → unlocks gated Release. Release is LOCKED until all gates pass. `ManufacturingStudio.js` frontend with live stages/gates/QC panel.
- Verified: backend 11/11 (real GPT QC certified in 2 rounds), frontend 100%.

## Implemented — Iteration 7 (2026-07-02) · Design Intelligence + Evolution Governance

### QRU Design Intelligence™ (Phase 1 of approved order) — TESTED 100%
- `design_intelligence.py` + `routers/design.py` (/api/design/*): Brand Library™ (5 colors, 2 typefaces, spacing, shield, treasure badge, components, 6 templates), Design Library™ (grows from Treasure Standard™ products), Master Asset Library™ (searchable, full metadata), evolving Design Language™ (baseline + learned principles), Design Checklist™ (10 questions), Creative Studio autonomy (`recommend-templates` auto-selects template/layout/illustration/palette/typography/tone by product type + audience).
- Learning hook wired into `manufacturing2._certify()`: every Treasure Standard™ product is learned into the Design Library + Master Assets and extracts a design principle.
- Frontend `DesignIntelligence.js` (/design-intelligence, nav-design-intel): 5 tabs + stats. Seeded from demo Treasure Standard products (6 refs, 9 assets, 6 principles).

### Extend Before Expand™ — Enterprise Evolution Governance (EXTENDED Organizational Health Director, no new dept)
- `routers/evolution.py` (/api/evolution/*): Enterprise Evolution Review™ (GPT decides EXTEND vs CREATE across existing capabilities, biased to elegant simplicity, saved to `evolution_log` = Enterprise Memory), Continuous Refactoring insights (traceability gaps, workforce-model overlap, unmanufactured knowledge, stuck pipeline), capabilities registry.
- EXTENDED `EnterpriseHealth.js` with an Enterprise Evolution Review™ section (objective → recommendation + 10-question review) and Continuous Refactoring panel. Curl-verified: fulfillment objective → "EXTEND EXISTING SYSTEM → Consumer Learning Platform".

## Approved Build Order (remaining) — updated 2026-07-02
1. ✅ Design Intelligence™ (DONE, tested 100%)
2. ✅ Memory Engineering™ (text-first) — DONE, tested 100%. `memory_engineering.py` + `routers/memory.py` (/api/memory/*): 6 Character Voices™, manufactures memory assets (Memory Sentence/Hook/Chant, Call-and-Response, One-Line Repeat, Educational Lyrics, Character Scripts + Dialogue, Legacy Learners™ child/teen/adult/professional, music+instrumental prompts) stored ON the Knowledge Record. Frontend `MemoryEngineering.js` (/memory-engineering). Memory Hook surfaced to learners in Consumer Mode. TTS spoken narration deferred (optional next).
3. ✅ Product Rendering Engine™ — DONE, tested 100%. `rendering_engine.py` + `routers/rendering.py` (/api/rendering/*): renders branded cover (Gemini Nano Banana via Emergent key, with deterministic placeholder fallback), thumbnail + store graphic (Pillow), QR code (qrcode → consumer URL), print-ready PDF (fpdf2). Assets served via /api/rendering/asset/{fname}. Gated to Treasure Standard™ products. `ai_service.generate_image()` added. Surfaced in Manufacturing Studio (render panel + gallery) and Consumer catalog covers.

## Queued specs — apply Extend Before Expand™ (next session)
- **Understanding Fulfillment Center™ (PRJ-QOS-017)**: EXTEND Consumer Platform — auto-package on Treasure Standard cert, Customer Library (search/collections/bookmarks/downloads/certificates/history/streaks), delivery + notifications, Learning Success metrics, Understanding Support (recommend modes), Customer Delight, Lifetime Updates/version mgmt, Licensing/Enterprise + White-Label, Fulfillment Verification, Executive Fulfillment Dashboard.
- **Treasure Standard™ Gold Master Reference System (PRJ-QOS-018)**: EXTEND Design Intelligence + QC — official Gold Master™ per product category, compare-against-master before certification, Gold Master Library with versioning + executive promotion, dashboards.
- **Manufacturing Orchestrator™**: EXTEND Command Center + Manufacturing Engine — Manufacturing Orders™, CEO natural-language commands, multi-department routing, retrospectives, White-Label.
- **Enterprise Intelligence™**: EXTEND Organizational Health/Command Center — Competitive/Technology/Customer/Manufacturing/Learning/Brand/Fulfillment/Innovation intelligence divisions + weekly executive briefing (self-improvement, no auto new departments).
- **Optional**: OpenAI TTS spoken narration for Memory Hooks/Character Voices.





## Backlog / Next (iteration 1 — superseded items kept for history)
- P1: Stream AI responses (SSE) in Command Console & product generation for token-by-token UX.
- P1: Real knowledge-growth time-series in Analytics (currently synthetic).
- P2: Product export (PDF/print), asset management + AI image generation for posters/infographics.
- P2: Licensing records & revenue analytics, pagination on large lists, version history UI for records.
- P2: Marketplace Intelligence + Reports modules, notification generation on workflow events.

## Implemented — Iteration 11 (2026-07-03) · Ownership, Registry, Orchestrator, Verification & Protection
- **Phase 1 · Ownership Transfer & Security**: Removed all personal demo users (Jordan Ellis, Erica Chen) and old admin@qru.com. Founder & CEO super-admin = Erica Talbert (22j2rsdzb8@privaterelay.appleid.com), sole permanent owner (protected from deletion). All existing data remapped via `owner_id`. Generic env-gated demo accounts only (Demo Administrator/Instructor/Student). Founder password NOT hard-coded: seeded TEMPORARY password (`FOUNDER_TEMP_PASSWORD`) so Preview never locks out, plus `/api/auth/change-password` (authenticated) to set a permanent one; `/api/auth/setup-status`, `/api/auth/setup-founder`. FounderSecurityBanner prompts to set permanent password.
- **Phase 2 · QRU Topic Registry™** (`routers/registry.py`, collection `topic_registry`): permanent TOP-##### IDs, priority/public-need/educational-value scores, manufacturing/verification/treasure status, assigned MO, version history. AI topic generation (Health/Faith) for review + bulk-import that creates College + Topic Registry entries + Manufacturing Orders (no KR manufacture). Frontend `TopicRegistry.js`.
- **Phase 3 · Intelligent Bulk Manufacturing Orchestrator™** (`orchestrator.py`, `routers/orchestrator.py`): batches (25–50), queue, pause/resume/retry, dependency tracking, progress, logs, token-cost estimate. Per-topic: Research → KR → QRU methodology → AI Verification → (auto-approve/escalate). Frontend `Orchestrator.js`.
- **AI Verification Team™ autonomy** (`verification_engine.py`, `routers/verification.py`): reviews accuracy/clarity/completeness/readability, auto-revises weak sections + re-verifies, records verification_log; escalates to Founder ONLY on true exceptions (reject, conflicting evidence, human judgment, policy, or confidence < threshold 80). High-confidence request_revision auto-approves. `founder_escalations` queue. Frontend `VerificationTeam.js`.
- **Hands-Free Manufacturing Mode™** (default ON, `factory_settings`): Orchestrator auto-advances Manufacture → Verify → QC → Treasure Standard → auto-Publish into Product Library + Customer Library. `/api/orchestrator/settings`, `/api/orchestrator/autopilot` (AI Publishing Team advances eligible products). Founder governs, AI manufactures.
- **Product Protection & Verification Agent™** (`product_protection.py`, `routers/protection.py`): AI product verification gate before publish; license system (Personal/Classroom/School-Org/Commercial); copyright notice + watermark flag + version history/proof of creation; account-gated access + expiring secure download links w/ access tracking; Protection Dashboard. Publish gate now requires verification. Frontend `ProductProtection.js`.
- Backend validated end-to-end via curl: founder temp login, ownership, registry, single-topic hands-free batch (manufacture→verify→QC→protect→publish with copyright+license). Comprehensive testing pending.

### Backlog / Next
- P1: Understanding Fulfillment Center™ (Customer Library, lifetime updates/versioning).
- P1: Treasure Standard™ Gold Master Reference System.
- P2: Enterprise Intelligence™ modules. Founder dashboard widgets (revenue, quality metrics, approval stats).

## Implemented — Iteration 12 (2026-07-03) · Integration Hub, AI Services, Product Automation, Production Line, Enterprise Divisions
- **QRU Integration Hub™** (`integration_hub.py`, `routers/integrations.py`): single source of truth for external platforms (Publishing/Educational/Commerce/Video/Marketing/Storage/Communication/Payment/Analytics/AI Services). Encrypted credentials (Fernet, never returned), OAuth-vs-APIkey detection, smart routing (product type → platforms), auto-distribution with AI-generated SEO metadata, monitoring + retry/escalation. Live external publishing is a connector layer — SIMULATED until real credentials wired. Frontend `IntegrationHub.js`.
- **AI Services Manager™** (`ai_services_manager.py`, `routers/ai_services.py`): capability→connected-service selection. Text + image + pdf REAL via Emergent key; media (video/animation/voice/music) SIMULATED until connector. Job history, retry, verification. Frontend `AIServices.js`.
- **Product Automation Engine™** (`product_automation.py`, `routers/automation.py`): reusable Product Recipes™ (44 types) + AI Production Agents™ (20). One-command package manufacture from a verified KR → products → hands-free verify/protect/publish/distribute. 21 package presets incl complete "Package™" bundles (Video/Book/Course/Teacher/Marketing/Podcast/Poster/Presentation).
- **Meditation & Inspiration Studio™**: 16 meditation/inspiration recipes, 10 reusable Inspiration Profiles™ (teaching-style based, never imitating real people), configurable Frequency Library (12 soundscapes), themed packages (Morning Motivation™, Sleep Meditation™, etc.).
- **QRU Digital Production Line™**: "What do you want to teach today?" — one command from a TOPIC. Finds or manufactures a verified KR, then runs the full package line autonomously across divisions. Frontend `ProductionLine.js` (marquee page at /teach).
- **Enterprise Operating Divisions™ + Command Center™** (`routers/enterprise.py`): 6-division Founder dashboard (Knowledge, Manufacturing, AI Services, Integration, Commerce & Distribution, Analytics) with cross-division metrics, factory health, exceptions, portfolio. Frontend `EnterpriseCommandCenter.js` at /command-center. Sidebar reorganized with "The QRU Experience" section.
- **The QRU Mind™**: production + product-verification prompts now enforce the 8-point QRU Thinking Model (True/Understandable/Useful/Complete/Beautiful/Memorable/On-brand/Treasure Standard) and QRU Content Standard.
- Tested: iteration_12.json — 100% (backend 17/17, frontend production-line/command-center/ai-services/integration-hub all verified). Credentials encrypted & never leaked.

### Backlog / Next
- Activate real AI connectors (video/voice/music) and real publishing connectors (Stripe payment is available with test keys) one at a time via integration_expert.
- Understanding Fulfillment Center™ (Customer Library lifetime updates/versioning); Treasure Standard™ Gold Master Reference; Analytics & Continuous Improvement feedback loop (real revenue/engagement).
- Minor UI: always render default routing table on Integration Hub even with no connections.

## Implemented — Iteration 13 (2026-07-03) · Treasure Standard™ Constitution + Factory Acceptance Test™
- **Treasure Standard™ Quality Constitution**: Product verification now enforces THE QRU QUESTION™ ("Would Erica Talbert be proud to put her name on this?") + the 16-point Treasure Standard™ Test (verification returns treasure_standard_met + founder_would_be_proud).
- **Improvement Loop™** (`product_protection.treasure_finalize` + `_improve_product`): every product is auto-verified → auto-revised (content rewritten to fix issues) → re-verified, up to 2 rounds, before publish. Publishes only when the Treasure Standard™ is met; escalates a 'quality' exception to the Founder only when it can't reach standard or true judgment is needed. Centralized and wired into hands-free (_produce_one), orchestrator (_auto_publish), and autopilot.
- **Enterprise Readiness Review™** (`GET /api/enterprise/readiness`) + **Factory Acceptance Test™** (`GET /api/enterprise/factory-acceptance-test`): per-module Enterprise Quality Score™ (12 modules), production_ready flag, lifecycle map. Surfaced on the Enterprise Command Center (readiness-panel, run-fat-btn → fat-panel). Current EQS 99% (Analytics 90 until a payment provider is connected — honest).
- UX polish: renamed sidebar "/" item to "Founder Console" (vs Enterprise Command Center™); FAT badge shows a "Production-ready once a payment provider is connected" hint.
- Tested: iteration_13.json — 100% (backend 9/9, frontend all pages/buttons/nav; no dead buttons). Treasure Standard loop verified end-to-end (auto-revise + re-verify + publish, no Founder clicks).

### Note on performance
- The Improvement Loop adds multiple LLM calls per product (verify→improve→re-verify), so a single product can take ~2-4 minutes. This is the intended quality-over-speed tradeoff; runs fully in the background/hands-free.


## Implemented — Iteration 14 (2026-07-03) · Real Connectors + QRU Enterprise Workflow Engine™
### PHASE A — Real Production Connectors (no more SIMULATED where feasible)
- **Stripe Commerce™** (`commerce.py`, `routers/commerce.py`): real Stripe Checkout via emergentintegrations. Server-side PRICE_TIERS catalog (frontend never sends amount), `payment_transactions` collection, status polling, single-fulfillment (`purchases` + product sales/revenue increment), `/api/webhook/stripe`. Stripe registered as a Connected Payment integration on startup (env key STRIPE_API_KEY=sk_test_emergent). Endpoints: `/api/commerce/{storefront,revenue,checkout,checkout/status/{id},purchases,transactions}`.
- **Real Voice (OpenAI TTS)** + **Real Slideshow Video** (`media_render.py`): `synthesize_voice()` (OpenAI TTS `tts-1`, voice `fable`, chunked) → MP3; `make_slideshow_video()` assembles branded scene images + narration into a 720p MP4 via ffmpeg. Wired into `ai_services_manager.execute()` — voice/audio/video/animation now REAL; only music remains spec-only. Manually verified: 129KB mp3 + 426KB mp4 produced.
- **Estimated Production Cost™**: `ai_services_manager.estimate_cost()` + `est_cost_usd` on ai_service_jobs; surfaced everywhere, labeled "Estimated".
- **Analytics → 100%**: FAT Analytics Division™ score is 100 when a Payment provider is Connected; Command Center revenue now shows live Stripe revenue/AOV/paid orders.
### PHASE B — QRU Enterprise Workflow Engine™ (`workflow_engine.py`, `routers/workflow.py`)
- **Workflow Engine™** governed 10-stage pipeline: KR Retrieval → Verification → Treasure Standard™ → Product Recipes™ → Parallel Manufacturing → QC → Packaging → Distribution → Analytics → Continuous Improvement.
- **Parallel Manufacturing™**: `asyncio.gather` over recipes with a concurrency semaphore(4); each product runs the hands-free Treasure Standard finalize (QC→protect→publish→distribute).
- **Job Queue™**: `workflow_jobs` with job_number (WF-#####), status, stage, progress, current_task, completed_tasks[], warnings[], errors[], retry_count, products[], est_cost_usd, eta, full logs[].
- **Automatic Error Recovery™**: per-product retry; escalate only true exceptions.
- **Production Logs™** + **Workflow Templates™** (8: Book/Video/Health/Faith/Course/Marketing/Translation/Full Treasure Package™).
- **Executive Factory Monitor™** (`/api/workflow/monitor`): jobs running/waiting/completed/escalated, division activity, AI usage, Estimated Production Cost™, quality/Treasure compliance, distribution, revenue, factory health (automation success, founder intervention, knowledge health).
- **Factory Acceptance Test™** (Phase B.5): `POST /api/workflow/factory-acceptance-test` runs one full Full Treasure Package™ end-to-end; `GET .../{id}` evaluates every division (checks[], score, PASS/REVIEW, defects[]).
- Frontend: `Workflows.js` (/workflows), `FactoryMonitor.js` (/factory-monitor), `Store.js` (/store), `CheckoutSuccess.js` (/checkout/success); nav + routes added. Learning Factory seed: `factory_learnings`.
- Added "Student Guide" recipe to product_automation.
- Tested (iteration_14.json): backend 13/14 (1 skip), Workflows/Store/Factory Monitor UI verified. Testing agent fixed an async-generator bug in `evaluate_fat`.

### ⚠️ BLOCKER (not a code issue)
- Emergent LLM key **budget exceeded** (current cost ~$18.42 > max ~$18.19). Text/image LLM calls fail with "Budget has been exceeded" → this caused FAT to reach 10/11 and a re-run to fail at KR Retrieval. **Action:** Founder must add balance (Profile → Universal Key → Add Balance) to run a fully clean FAT and Phase C bulk manufacturing. Stripe/TTS/ffmpeg are unaffected.

### Next (after budget top-up)
- P0: Re-run FAT to green (target PASS ≥80%); then PHASE C — controlled batch manufacturing of seeded Health/Faith libraries via the Workflow Engine.
- P1 (PHASE D — Level-5 Autonomy directive received): Continuous Improvement Engine, Learning Factory, Product Evolution, Knowledge Gap Detector, Predictive Manufacturing, Cost Optimization, Capacity Planning, Self-Diagnostics, Executive Advisor daily brief, Factory Council, Innovation Radar, Enterprise Memory.
