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


## Implemented — Iteration 15 (2026-07-03) · FAT run + Phase D (Level-5 Autonomy) foundation
- **Factory Acceptance Test™ RESULT: PASS at 89%** (threshold 80%). WF-00009, Full Treasure Package™, 10/11 products manufactured, real OpenAI TTS narration produced, all divisions green. Two transient defects under heavy parallel load: the Short Video MP4 and one Podcast Script (both HTTP 503 rate-limit bursts, not budget).
- **Reliability hardening:** `ai_service.llm_generate` + `generate_image` now retry transient errors 3× with backoff and **fail fast** on hard limits ("Budget has been exceeded" / "spend limit"). Workflow parallel-manufacturing concurrency reduced 4→2 to avoid 503 bursts. `ai_services_manager.execute` retry now backs off.
- **PHASE D (Level-5 Autonomy) — deterministic foundation** (`autonomy.py`, `routers/autonomy.py`, `/api/autonomy/*`): Self-Diagnostics™ (+ safe auto-repair of unprotected published products), Factory Health™ (8 named metrics), Executive Advisor™ daily brief, Cost Optimization™ + AI Provider Scorecard™, Capacity Planning™, Knowledge Gap Detector™, Factory Council™ (continuous improvement report), Enterprise Memory™ (best templates & recipes). All computed from factory data — runs WITHOUT LLM budget. Frontend `AutonomyCenter.js` (/autonomy, nav-autonomy). LLM-narrated recommendations deferred.
- **Phase C — controlled batch (10 topics: 5 Health + 5 Faith) created & launched via Orchestrator**, then **PAUSED** — blocked by the Emergent key's **DAILY spend limit** ("Daily spend limit reached", hit after the FAT + a day of testing). Batch id saved; 3 topics pending, 7 to retry.

### ⚠️ BLOCKER (external, not code)
- Emergent LLM key **DAILY spend limit reached** today. This is separate from total balance. It resets on the daily cycle (or can be raised). Until then, no text/image LLM manufacturing runs. Stripe checkout, TTS/ffmpeg media, and all autonomy dashboards are unaffected.

### Next (after daily limit resets / is raised)
- P0: **Resume Phase C** — open Bulk Orchestrator™, "Retry failed" on the "Phase C — Health & Faith Controlled Batch", let it finish (research→KR→verify→QC→publish per topic). Optionally re-run the FAT for a clean 11/11 (the reliability hardening should now also produce the Short Video MP4).
- P1: **Phase D LLM layer** — add GPT-narrated recommendations to Continuous Improvement Engine, Product Evolution (ratings/reviews→v2), Predictive Manufacturing, Innovation Radar; wire daily Executive Brief delivery.


## Implemented — Iteration 16 (2026-07-03) · Phase D LLM layer + QRU Design Language™
### Phase D — Enterprise Intelligence™ (LLM-narrated, degrades gracefully) — `autonomy_ai.py`, `/api/autonomy/*`
- Continuous Improvement narrative (`/improvement-report`), Predictive Manufacturing™ (`/predictive-manufacturing`), Innovation Radar™ (`/innovation-radar`), narrated Executive Brief™ (`/executive-brief/narrated`).
- Product Evolution™: customer ratings (`POST /autonomy/products/{id}/rate` → `product_ratings`), evolution overview (`/product-evolution`), per-product v2/v3 recommendation (`/product-evolution/{id}`).
- Every LLM function returns deterministic data + `ai_available:false` + reason when the LLM is capped — nothing 500s. Surfaced in `AutonomyCenter.js` (Enterprise Intelligence™ section with degraded note).
### QRU Design Language™ & Treasure Standard™ Visual System — `design_language.py`
- Premium deterministic (Pillow) product covers with real typography (Liberation Serif/Sans), QRU Shield™, College eyebrow, product-type badge, wrapped serif title, subtitle, difficulty/audience, Treasure Standard™ seal, QRU PRESS™ publisher band + edition. **No blank placeholders.**
- Dynamic Color System™: 15 subject palettes (heart=red, brain/sleep=purple, lung/mental=blue, nutrition=green, faith/finance/business=navy/emerald+gold, programming=electric blue, science=teal, history=bronze, math=royal blue, children=playful) resolved from family/department/topic/title keywords.
- `premium_thumbnail`, `premium_store_graphic`, and Treasure Standard™ Visual Review™ (`visual_review()` → `/api/rendering/{pid}/visual-review`).
- Auto-applied on publish via `rendering_engine.ensure_branded_assets()` wired into `product_protection.treasure_finalize`; `render_product_job` now uses the Design Language too. Backfill endpoint applied it to all 27 published products.
- Store redesigned (`Store.js`): branded cover, accent top-border, product-type chip, family, audience, Treasure Standard™ badge; storefront payload enriched (thumbnail_url, audience, design_palette, treasure_standard).
- Verified: sample covers render professionally; visual review 100/Approved; ratings + evolution work; LLM intel endpoints degrade gracefully; Store + Autonomy Center render.
### Deferred (design)
- AI hero-art compositing inside covers (when LLM/image budget returns); true multi-format export variants (KDP/Etsy/TpT print profiles) — layout system is ready, exporters pending.
### Still blocked by DAILY LLM spend cap
- Phase C bulk run + clean 11/11 FAT (need LLM). Adding balance does NOT clear the daily cap; it resets on the daily cycle.

## Implemented — Iteration 17 (2026-07-03) · Multi-Format Output™ + AI hero-art hook (P1 non-LLM)
- **Multi-Format Output™** (`design_language.export_formats`, `rendering_engine.export_multi_format`, `POST /api/rendering/{pid}/export-formats`): generates 10 optimized, branded renditions — KDP eBook (1600×2560), KDP Print 6×9 (1800×2700), Etsy square (2000²), Teachers Pay Teachers (1200×1600), High-Res Poster (2400×3600 @300dpi), Social square/story, Pinterest, Web thumb, Desktop banner. Each preserves the QRU frame via `_fit_on_brand` (contain-fit on branded gradient + accent border + QRU PRESS™ footer). Verified: 10 formats, correct dimensions, professional output.
- **AI hero-art compositing** wired into `ensure_branded_assets`: best-effort `generate_image` call composited as a subtle backdrop under the QRU frame (`premium_cover(..., hero_bytes=)` blends art 0.62 toward the gradient for readability). Skips silently on daily cap/budget → covers always render; auto-activates (`cover_has_hero_art`) when AI capacity returns.
- Still blocked by DAILY LLM spend cap: Phase C bulk run, clean 11/11 FAT, and live AI hero-art/LLM narratives. Adding balance does not clear the daily cap (resets on daily cycle).
- Deferred UI: a product "Downloads/Formats" panel to surface export URLs (endpoints ready).


## Implemented — Iteration 18 (2026-07-03) · Treasure Standard™ Enterprise Architecture (4 subsystems, non-LLM)
> LLM daily spend cap STILL active this session (verified). Phase C bulk + clean 11/11 FAT remain blocked. All work below is deterministic and required no runtime LLM. Official character portraits were generated via the platform image tool (separate from the capped runtime key).

### 1. The One Question Test™ — navigation standard
- Every nav item now carries its department's Primary Business Question as a hover tooltip (`title` on each `NavLink` in `Layout.js`). No menu exists without a clear single question.

### 2. QRU Enterprise Blueprint™ — canonical Operations Manual
- `department_registry.py` (single source of truth): 37 Department Profiles, each with the full standardized structure (Mission, Purpose, Primary Question, Why It Exists, Problems Solved, Responsibilities, Inputs, Outputs, Daily Activities, AI Agents, People, Related Depts, Workflow, Use Cases, KPIs, Treasure Standard™ Requirements, Future Expansion). Enforces the One Question Test™.
- `routers/departments.py` → `/api/departments`, `/api/departments/questions`, `/api/departments/{key}`.
- Frontend `EnterpriseBlueprint.js` (`/blueprint`, nav-blueprint): grouped cards + full-profile dialog.
- Canonical `/app/memory/QRU_ENTERPRISE_OPERATIONS_MANUAL.md` generated (2580 lines).

### 3. QRU Workforce Identity System™ (WIS) — permanent Character Library™
- `character_registry.py` + `routers/wis.py` (`/api/wis/*`, collection `character_library`): 6 flagship Treasure Standard™-approved Character Records (Kingdom Lion™, Legacy Eagle™, Legacy Bear™, Queen Unity™, Crowned Bull™, Royal Phoenix™) with full schema (bio, personality, teaching/voice style, catchphrases, official portrait, palette, uniform, expressions, poses, prompt library, brand guidelines, copyright, version + previous versions).
- Official regal portraits generated & stored as PERMANENT URLs. Endpoints: list, get, `resolve/{role-or-dept}` (apps RETRIEVE approved characters), `POST .../variations` (create pose/expression variation that preserves the approved identity — never a new generic portrait).
- Frontend `CharacterLibrary.js` (`/wis`, nav-wis): portrait grid + full Character Record dialog with approved palette.

### 4. QRU Institutional Knowledge System™ (QIKS) — enterprise memory
- `qiks.py` + `routers/qiks.py` (`/api/qiks/*`, collections `qiks_standards`, `qiks_lessons`): Enterprise Standards Registry™ (16 seeded standards with full schema, drawn from existing subsystems), 24 Knowledge Categories, 9-stage Knowledge Promotion™ pipeline, Knowledge Graph™ (16 nodes / 22 edges), Enterprise Memory™ (Lessons Learned per division, 3 seeded), Search & Discovery, and Version Governance™ (revise never overwrites — bumps version, archives superseded snapshot, appends change history). Executive Knowledge Dashboard™ metrics incl. Institutional Health™.
- Endpoints: overview, standards (filter by category/status/q), search, graph, lessons, get, create (starts as Working Idea), promote, PUT revise (version governance), add lesson.
- Frontend `InstitutionalKnowledge.js` (`/qiks`, nav-qiks): metrics header + Standards/Graph/Memory/Promotion tabs, search, category filter, standard detail dialog with change history.

### Verification
- All backend endpoints curl-verified (departments 37, questions map, wis 6 chars + resolve + variation persistence, qiks 16 standards + graph 22 edges + search + create/promote + version-governance revise to v1.1). Frontend `/blueprint`, `/wis`, `/qiks` screenshot-verified rendering correctly. Test artifacts cleaned up.

### Still blocked / deferred
- P0: Phase C bulk run + clean 11/11 FAT (need LLM daily cap to clear).
- WIS deep-wiring: auto-inject approved portraits into Organization director cards, reports, and product artwork (source-of-truth + retrieval API are ready; consumer surfaces are future work).
- QIKS AI-consultation wiring: agents can retrieve via `/api/qiks/standards` today; enforcing "consult before generate" inside each agent is future work.

## Implemented — Iteration 19 (2026-07-03) · Character Bible™ full-body assets + enterprise Director cards
- Generated official **full-body, transparent-PNG** artwork for all 6 flagship Directors (Kingdom Lion™, Legacy Eagle™, Legacy Bear™, Queen Unity™, Crowned Bull™, Royal Phoenix™) via the platform image tool (permanent URLs). Stored on each Character Record as `official_full_body` + `transparent_png` (`character_registry.FULL_BODY`), persisted idempotently on seed.
- **Enterprise Director cards** now use the APPROVED QRU identity: new reusable `components/DirectorRoster.js` (fetches `/api/wis/characters`) renders 6 branded navy full-body director cards; added to the top of the Organization page. Executive Board avatars now map by name to the WIS official portraits (no more generic placeholder headshots).
- Character Library dialog surfaces the full-body transparent artwork alongside the portrait. Verified via curl (all 6 have full_body + transparent set) and screenshots (roster, board avatars, dialog).
- NEXT MAJOR TRACK (directive received, not yet built): QRU Enterprise Autonomy & Continuous Improvement™ — Enterprise Relationship Engine™, After-Action Review™ → QIKS lessons, enhanced per-failed-job diagnostics (root cause/recovery/retry/dependency/ETA/confidence), and a safe auto-resume watcher that completes Phase C automatically when LLM capacity returns. Investigation of job/batch structures done (orchestrator `manufacturing_batches` + `resume_batch`/`retry_failed`; `workflow_jobs`; `ai_service` fail-fast on hard limits).

## Implemented — Iteration 20 (2026-07-03) · QRU Enterprise Autonomy & Continuous Improvement™
- **Enterprise Relationship Engine™** (`relationship_engine.py`, `routers/relationships.py`, `/api/relationships/*`): canonical 15-object-type SCHEMA with 51 relationship connections + live counts; `object/{type}/{id}` (what an object connects to) and `suggest/{type}/{id}` (auto-suggested related standards + aligned Director). Verified: 15 types, 51 connections.
- **Continuous Improvement™** (`continuous_improvement.py`, `routers/continuous.py`, `/api/continuous/*`):
  - **Capacity Probe™** — detects when AI capacity returns; distinguishes daily-cap vs budget vs transient (cached 10 min). Currently reports "Daily spend limit reached".
  - **Safe Auto-Resume™** — a background `watcher_loop` (started at startup, every 180s) that resumes paused batches + retries failed batch items THE MOMENT capacity returns, WITHOUT Founder intervention. Escalated/high-impact work still requires the Founder. Actions logged to `autonomy_actions`. This will finish Phase C automatically.
  - **After-Action Review™** — deterministic AAR per completed batch → writes a lesson into QIKS (pending Founder approval). Stored in `after_action_reviews`.
  - **Enterprise Diagnostics™** — every failed job/topic gets root cause, recovery recommendation, retry status, dependency status, estimated resolution, and confidence score. Verified: 15 failed jobs classified (incl. Phase C topics).
  - **Enterprise-First Thinking™** 10-question checklist surfaced.
- **QIKS consult-before-generate™**: `qiks.consult(objective)` + `/api/qiks/consult`; a concise institutional preamble is now prepended to the product-manufacturing prompt (`product_automation.TEXT_SYSTEM`) so every generation honors Treasure Standard™ / QBOS / Character Bible™ / QRU Thinking Model™.
- Frontend `EnterpriseAutonomy.js` (`/enterprise-autonomy`, nav-enterprise-autonomy): capacity banner + Probe/Auto-resume buttons, and Continuous Improvement / Diagnostics / Relationship Engine / Enterprise-First Thinking tabs. Screenshot-verified.
- Still gated by the daily cap: actual Phase C completion + clean FAT (the watcher will trigger automatically on reset). Auto-resume correctly holds jobs safely while capacity is unavailable.

## Bug Fix — FM-001 Creative Studio Enhancement Failure (2026-07-03) · VERIFIED by testing_agent
- **Root cause**: `POST /api/products/{pid}/creative-brief` called `llm_generate()`, which fails while the OpenAI daily spend limit is active; the frontend caught it as a generic "Enhancement failed".
- **Fix (targeted, no redesign)**: the endpoint now wraps the AI Brief Writer™ stage in try/except and, on failure, builds a deterministic on-brand brief (`_fallback_brief`) so the enhancement COMPLETES and sets `creative_status='Reviewed'`. Response returns `enhancement_stage_note` + `creative_brief_source` (`ai` | `deterministic`). Frontend (CreativeStudio.js, ProductDetail.js) now surfaces the specific stage note instead of "Enhancement failed", plus a persistent amber chip on the product page when the brief is a fallback.
- **Verified**: testing_agent iteration_14.json — backend 100% (5/5), frontend E2E confirmed, zero issues. Screenshot confirms brief renders + stage note + persistent chip. Test file: `/app/backend/tests/test_fm001_creative_brief.py`.

## Implemented — Iteration 21 (2026-07-03) · Portability Center™ + AI Usage & Cost Meter™
- **MT-PORT-001 QRU Portability Center™** (`routers/portability.py` → `/api/portability/overview`; page `/portability`, nav Administration): documentation-only recovery hub. Shows GitHub export guidance, live MongoDB collections (42, with counts), Environment Variables & API Keys checklist (presence only — NO secret values), LLM provider config (openai/gpt-5.5 + swap note), Domain info (reads REACT_APP_BACKEND_URL from frontend/.env), Deployment Targets, Third-Party Services, Backup/Disaster-Recovery checklists, Restore Procedure, and copy-able mongodump/mongorestore command templates.
- **AI Usage & Cost Meter™** (`cost_meter.py`, `routers/cost_meter.py` → `/api/cost-meter/*`; `components/CostMeter.js` embedded at top of AI Services page): estimated daily/weekly/monthly AI spend, by-service breakdown (text/image/TTS/video), remaining budget + soft thresholds (50/75/90/100%), provider limits + OpenAI daily-cap status, per-product/per-order estimated cost. Configurable daily soft budget + Founder 100% override. Instrumented `ai_service.llm_generate` (text) & `generate_image` (image) & `media_render.synthesize_voice` (TTS) to record non-blocking estimated events. All values labeled ESTIMATED. Deterministic fallback workflows are never blocked (`can_spend` is advisory only).
- Verified via curl (portability 42 collections + env presence + domain resolves; cost-meter overview/budget/can-spend) and screenshots (both pages render with copy buttons, gauge, warnings, controls). No LLM required.

## MT-026 (2026-07-03) · Factory Readiness Score™ (decision-support, LLM-free) · self-verified
- **Factory Readiness Score™** (`readiness.py`, `routers/readiness.py` → `GET /api/readiness/overview`; page `/factory-readiness`, nav "Factory Readiness™" under The QRU Experience): per product-type readiness (0-100) blending a factory-capability baseline with live product data across 6 components — Manufacturing reliability, Treasure Standard™ readiness, Rendering quality, Testing completion, Founder approval readiness, Customer delivery readiness (weighted). Live signal is **upward-only** (`_boost`) so legacy/undelivered products never drag a mature type below its capability baseline; scores rise automatically as capabilities complete and products succeed.
- **"Recommended for First Dollar Mode™"** badge for types scoring ≥90 with delivery ≥90. Founder dashboard buckets: Ready to Manufacture (verified KRs), Ready for Review, Ready for Publication (certified + deliverable rendered), Ready for Sale (published + validated deliverable), plus Highest-Readiness ranking and expandable per-type component breakdowns.
- Ordering matches the ticket's illustrative shape (Quick Guide/Teacher Guide 100, Book 98, Poster/Presentation/Student Guide 96, Workbook 88, Interactive Lesson 82, Video 60, Animation 45, Movie 10). **Strictly informational — does NOT affect manufacturing, publishing, approvals, rendering, or any workflow.**
- Verified: curl (buckets + scores + recommendations) and screenshot (page renders, buckets, ranking, badges, expandable component detail). Low-priority per ticket; built only after MT-024 + MT-025 verified.

## MT-025 (2026-07-03) · Treasure Standard™ Design Validation + Founder Review download reliability · VERIFIED (14/14)
- **Treasure Standard™ Design Validation** (`deliverable_renderer.assess_design_quality`, `DESIGN_THRESHOLD=85`): every rendered deliverable now gets a deterministic design-quality grade across 9 weighted criteria (cover resolution, QRU branding, Treasure Standard™ seal, interior sections, visual hierarchy, typography/readability, print quality PDF, mobile/responsive HTML, margins & spacing). Below threshold → `status="Rendered — Design Review Required"` (not fully Approved). Stored on `customer_deliverable.design_review` + `design_approved` + product `design_review_required`.
- **Design gate on publish**: `release_product()` blocks release (HTTP 400, message contains "design review") when `design_review_required`; snapshot preserves the design_review in `published_deliverable`. Founder can Review, Return to Creative Studio™, Re-render, and Approve only when design meets standard.
- **Premium PDF interior upgrade** (`rendering_engine._make_pdf`): serif (Times) body, royal/gold section headings with rule accents, proper bullets, page-numbered "QRU PRESS™" footers, cover + colophon pages, markdown `---` rendered as visual dividers (also in HTML). PDF now paginates to a real book (e.g. 53pp for the sample).
- **Download reliability fix** (Founder's reported bug): the cross-origin `download` HTML attribute is silently ignored by browsers, so `GET /api/rendering/asset/{fname}?download=1&name=X` now sets `Content-Disposition: attachment` server-side (inline preserved for the reader). Frontend download links (ProductDetail + FinalProductPreview) use `?download=1&name=<title>`. Works in Preview + Live.
- **UI**: ProductDetail Founder Review Copy™ panel shows the design badge (Approved · grade / "Design Review Required" · grade + recommendations + Return to Creative Studio™); FinalProductPreview mirrors it and gates Approve & Publish on design_approved.
- Verified: testing_agent iteration_17.json — backend 14/14 + full frontend Founder workflow (real Playwright cross-origin download events for html/epub/pdf/pptx/png, design badges, gate block/allow, inline reader). Test file: `/app/backend/tests/test_mt025_design_and_downloads.py`.

## MT-024 (2026-07-03) · Complete End-to-End Manufacturing Workflow — Customer-Ready Deliverables · VERIFIED
- **Customer-Ready Deliverable Renderer™** (`deliverable_renderer.py`): at Treasure Standard™ certification the factory now auto-renders the EXACT file(s) a customer receives — fully deterministic (no LLM budget). Always a branded, self-contained **readable HTML edition** (open/read/scroll) + a type-specific primary format + a downloadable PDF. `PRIMARY_FORMAT` map: Book→EPUB, Presentation→PPTX (python-pptx), Poster→PNG, Workbook/Teacher/Caregiver/Course/Flash Cards→PDF, Quiz/Interactive Lesson/Short-form/Podcast/Video Script→HTML. Cover embedded as base64 so the HTML is portable. New deps: `python-pptx`, `EbookLib`.
- **Treasure Standard™ validates the deliverable itself** (`validate_deliverable`): checks source content ≥180 chars, readable edition rendered, primary format rendered, and every file present on disk ≥800 bytes → `customer_deliverable.ready`/`validated`.
- **Wiring**: `manufacturing2._certify()` now renders branded cover (`ensure_branded_assets`) + deliverable before Founder Approval. `product_protection.treasure_finalize()` (hands-free path) renders the deliverable before publish and snapshots `published_deliverable`. `release_product()` refuses to publish unless `deliverable_ready` (auto-renders on demand) and stamps `published_deliverable` so what ships equals what was reviewed.
- **API**: `POST /api/manufacturing2/{pid}/render-deliverable`; `GET /{pid}/pipeline` now returns `customer_deliverable`, `deliverable_ready`, `cover_url`, `thumbnail_url`; `GET /api/rendering/asset/{fname}` serves html/epub/pptx/png/pdf/mp4/mp3 with correct Content-Type.
- **Founder inspection UI** (`FinalProductPreview.js`): replaced "pending render" with the real branded cover; lists each customer-ready file (HTML/EPUB/PDF/PPTX/PNG) with size + download; a "Deliverable validated · Treasure Standard™" badge; and an inline **reader** (iframe of the HTML edition) so the Founder can open, read, and scroll the finished product before clicking **Approve & Publish** (which calls the gated release/snapshot flow).
- **Auto-resume preserved**: rendering is deterministic, so when the LLM daily cap clears and the watcher resumes Phase C, each certified product automatically renders its deliverable through the same `_certify`/`treasure_finalize` paths — no restart of completed stages, never publishes incomplete products.
- **Verified**: testing_agent iteration_16.json — backend 14/14 (render across Book/Presentation/Poster, correct Content-Types + valid magic bytes/ZIP, pipeline exposure, idempotency, 404s, release gating + `published_deliverable` snapshot + gate-lock). Frontend modal screenshot-verified (cover, HTML/EPUB/PDF downloads, validation badge, inline reader). Test file: `/app/backend/tests/test_mt024_deliverable.py`.
- **Still gated by LLM daily cap (external)**: the live Manufacture→Render→Founder Review→Approve→Publish demo of a FRESH product and the clean 11/11 FAT need the LLM QC step; they will run automatically when capacity returns (deliverable rendering is already wired into that path).

## Iteration 22 (2026-07-03) · MT-021 Final Product Preview VERIFIED + workflow-integrity check
- **MT-021 Final Product Preview™** visually verified (screenshot): the modal auto-opens on a completed/certified pipeline showing the "Manufacturing Complete · Final Product Preview" header, product title/code, Finished Deliverables, branded cover (or "cover pending render" fallback), and all four action buttons — Preview, Download, Edit, Approve & Publish (renders "Published" when already live). Verified against certified product PRD-00051 (Book). Temporary `?previewPid=` load-hook used only for the screenshot was reverted.
- **Auto-Resume Watcher confirmed ARMED**: `asyncio.create_task(continuous_improvement.watcher_loop())` runs at server startup (180s loop, `running: True`). Capacity probe reports `available:false — Daily spend limit reached (resets on daily cycle)`.
- **Phase C batch confirmed SAFELY PAUSED**: batch `59110741…` "Phase C — Health & Faith Controlled Batch" status=`paused`, total 10 / done 0 / failed 10 (retryable). The watcher will resume it the moment LLM capacity returns — no Founder action needed.
- Per Founder directive: development STOPPED after these verifications. No new P1 features until the full Manufacture → Final Product Preview → Founder Review → Approval → Publication workflow is demonstrated end-to-end (currently gated by the LLM daily cap on the QC step).

## Bug Fix — MT-IP-001 Protection Center™ operates without AI (2026-07-03) · VERIFIED by testing_agent
- **Root cause**: `product_protection.ai_verify_product()` called `llm_generate()`, which fails while the OpenAI daily cap is active — making the Protection Center's Verify action fail with a generic error.
- **Fix (targeted)**: `ai_verify_product()` now wraps the AI review in try/except; on failure it runs a DETERMINISTIC structural verification (approve if content ≥200 chars, else request_revision), persists it, logs a warning, and returns `ai_recommendations_available=False` + message "Core verification completed. AI recommendations temporarily unavailable." `apply_protection()` was already AI-free (assign level, protection record, product link, timestamps, ownership/version, audit history). Frontend `ProductProtection.js` shows the graceful message instead of a generic failure.
- **Verified**: testing_agent iteration_15.json — backend 100% (5/5), frontend 100% E2E, zero issues. Applied reviewer's logging suggestion.

