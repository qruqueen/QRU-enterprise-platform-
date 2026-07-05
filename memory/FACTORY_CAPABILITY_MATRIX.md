# QRU Factory™ — Factory Capability Matrix™
### Chief Manufacturing Architect™ analysis · June 2026
> Grounded in the actual codebase (not aspirational). Status legend:
> ✅ **Exists** (real & wired) · 🟡 **Partial** (exists but incomplete/stubbed/deterministic-only) · 🔴 **Missing** · ⭐ = strategic moat if built natively.

The factory is architected around one promise: **Approved Knowledge Record™ → Manufacture → QC → Render → Publish → Verify → Store IDs → Archive → Analytics**, with minimal manual work. This matrix maps every capability required to fulfill that promise across a 20‑year horizon.

---

## PART 1 — Capability Profiles (by lifecycle phase)

### PHASE A · KNOWLEDGE FOUNDATION

**A1. Knowledge Management™** — ✅ Exists (`knowledge_record_v2.py`, `routers/knowledge_v2.py`, `KnowledgeRecords.js`)
- Purpose: Single source of verified truth. Inputs: research, imports, founder entry. Outputs: KR 2.0 (36 independent versioned sections + dependency map).
- Native. Deps: none. Security: role-gated writes, section version history. QC: completeness %, dependency readiness. Treasure Standard™: verification_status per KR; manufacturing blocked without required sections. Priority: **Core**.

**A2. Research & Knowledge Extraction™** — 🟡 Partial (`knowledge_extraction.py`, `ResearchCenter.js`, `library_import.py`)
- Purpose: Gather source material → structured knowledge. Inputs: URLs, documents, libraries. Outputs: draft KR sections + citations.
- Native orchestrating external. External connectors: web scraper, academic/search APIs (future). APIs: search/scrape. Deps: A1. Security: source provenance capture. QC: source credibility scoring (partial). Treasure Standard™: **must cite verifiable sources — no AI-invented facts**. Priority: **Important**. ⭐ (evidence-graded research = trust moat).

**A3. Verification Engine™ (Verification Lion™)** — ✅ Exists (`verification_engine.py`, `verification.py`, `VerificationCenter.js`)
- Purpose: Autonomous AI verification + revision loop, founder escalation only on true exceptions. Inputs: manufactured KR/products. Outputs: verdict, confidence, revisions.
- Native. Deps: A1, AI orchestration. Security: immutable verdict log. QC: confidence thresholds. Treasure Standard™: **core enforcer**. Priority: **Core**.

### PHASE B · CONTENT MANUFACTURING (text)

**B1. AI Orchestration™** — ✅ Exists (`orchestrator.py`, `ai_services_manager.py`, `ai_service.py`)
- Purpose: Route prompts to the right model with deterministic fallback. Inputs: task + context. Outputs: text/image. Uses OpenAI gpt‑5.5 (Emergent key), Gemini 3.1 image. Native orchestrating external LLMs. Security: key server-side only. Treasure Standard™: **deterministic fallback = $0 AI, never fake output**. Priority: **Core**.

**B2. Writing & Translation Pipeline™** — ✅ Exists (`translation_pipeline.py`, `TranslationEngine.js`)
- Purpose: Turn verified knowledge into audience-tuned copy. Deterministic intent/audience/retrieval/memory/verification stages; LLM only for unknown-topic drafts. Priority: **Core**.

**B3. Editing & Continuous Improvement™** — 🟡 Partial (`continuous_improvement.py`, verification revision loop)
- Purpose: Post-manufacture refinement from QC + performance signals. Missing: closed-loop edits driven by live analytics. Priority: **Important**.

### PHASE C · CREATIVE MANUFACTURING (visual / audio / video)

**C1. Graphic & Cover Generation™** — ✅ Exists (`ai_service.generate_image` Gemini nano banana, `rendering_engine.py`, `design_intelligence.py`, `design_director.py`, `design_language.py`)
- Purpose: Branded covers, thumbnails, store graphics, QR. Native orchestrating Gemini image. Treasure Standard™: QRU visual language enforced, no generic AI layouts. Priority: **Core**.

**C2. Illustration System™** — 🟡 Partial (shares C1 image gen; no dedicated multi-panel/consistent-illustration pipeline)
- Missing: consistent illustrated sequences, style locking across a product. Priority: **Future**. ⭐.

**C3. Character Management™ (Workforce Identity System™)** — ✅ Exists (`character_registry.py`, `CharacterLibrary.js`)
- Purpose: Permanent, reusable character identities (voices, portraits, poses). Approved assets never regenerated — variations only. Priority: **Important**. ⭐ (brand consistency moat).

**C4. Voice Generation™** — ✅ Exists (`media_render.py` — REAL OpenAI TTS via Emergent key)
- Purpose: Spoken narration. Native orchestrating OpenAI TTS. Priority: **Core**.

**C5. Music / Sound Generation™** — 🔴 Missing
- Purpose: Background music, stingers, meditation beds. External: Suno/ElevenLabs Music/Mubert (licensing-safe). Treasure Standard™: **license provenance required**. Priority: **Future**. ⭐ if native library of owned music.

**C6. Video Generation & Rendering™** — 🟡 Partial (`media_render.py` = REAL ffmpeg slideshow: branded images + TTS → MP4; `media_engine.py` = scripts/metadata)
- Exists: deterministic slideshow video (images + narration). Missing: true motion/AI video (talking character, b-roll, captions burn-in, transitions), scalable render farm. External (Phase 2): Runway/Veo/Kling/Pika + a render service. Priority: **Important → Core** (per Founder MO‑007 vision). ⭐ (native education video render = biggest moat).

### PHASE D · DOCUMENT & PRODUCT ASSEMBLY

**D1. Deliverable Renderer™** — ✅ Exists (`deliverable_renderer.py`) — PDF, EPUB, PPTX, PNG, readable HTML edition. Fully deterministic ($0 AI). Idempotent. Treasure Standard™: validates the rendered file itself. Priority: **Core**.

**D2. Product Recipes™** — ✅ Exists (`product_recipes.py`, `product_automation.py`) — layout-per-type registry (Poster ≠ Book ≠ Course ≠ Quiz). The recipe is the natural home for MO‑007 publishing rules. Priority: **Core**.

**D3. Course / Quiz / Presentation Generation™** — ✅ Exists (recipes for Interactive Lesson, Workbook, Quiz, Presentation, Course). 🟡 SCORM/xAPI export for LMS = Missing. Priority: **Important**.

**D4. Accessibility™** — 🟡 Partial (readable HTML edition) → 🔴 formal a11y (alt-text, captions/subtitles, WCAG audit, screen-reader structure). Treasure Standard™: **inclusive by default**. Priority: **Important**. ⭐ (institutional/gov sales moat).

### PHASE E · ASSET & INVENTORY MANAGEMENT

**E1. Digital Asset Vault™ / DAM** — ✅ Exists (`vault.py`, `asset_manufacturing.py`, `AssetVault.js`) — disk-backed, classified, versioned, reused-by-default, never overwritten. Priority: **Core**.

**E2. Version Control™** — ✅ Exists (KR 2.0 section versions + vault version history). 🟡 Missing: cross-product diff/rollback UI. Priority: **Important**.

### PHASE F · ORCHESTRATION & SCALE

**F1. Workflow Engine™** — ✅ Exists (`workflow_engine.py`, `orchestrator.py`, `Workflows.js`) — governed pipeline, parallel manufacturing, job queue, auto error-recovery + alternate provider, production logs, cost estimate, factory monitor. Priority: **Core**.

**F2. Batch Manufacturing™** — ✅ Exists (parallel workflow + Director "Manufacture Cleared" batch). Priority: **Core**.

**F3. Manufacturing Director™ AI** — ✅ Exists (`manufacturing_director.py`, MO‑005) — deterministic supervisory approve/hold/reject + gap analysis, optional AI brief. Priority: **Core**.

**F4. Scheduling™** — 🔴 Missing — timed/queued publishing, editorial calendar, drip release. Needed by MO‑007 (Scheduled mode). Priority: **Important**. ⭐.

**F5. Enterprise Scalability™** — 🟡 Partial — modular routers + job queue exist; missing: distributed worker pool, backpressure, horizontal render scaling. Priority: **Future**.

### PHASE G · QUALITY, GOVERNANCE & TRUST

**G1. Quality Control / Inspection System™** — ✅ Exists (`inspection_system.py`, MO‑001) — 9 objective blocking gates. Priority: **Core**.
**G2. Governance / Constitution™** — ✅ Exists (`constitution.py`, `qru_governance.py`, `GovernanceCenter.js`). Priority: **Core**.
**G3. Audit Logging™** — ✅ Exists (`org_activity.py`, `factory_audit.py`). Priority: **Core**.
**G4. Monitoring & Confidence™** — ✅ Exists (`factory_confidence.py`, `FactoryMonitor.js`, `EnterpriseHealth.js`, `readiness.py`). Priority: **Core**.
**G5. Self-Healing / Failure Intelligence™** — ✅ Exists (`self_healing.py`, `failure_intelligence.py`) — classify → recover → learn. Priority: **Important**.
**G6. Disaster Recovery / Backup™** — 🔴 Missing — DB snapshots, asset backup, restore runbook, RPO/RTO. Priority: **Important** (pre-scale must-have). ⭐ (enterprise trust).

### PHASE H · LICENSING, PROTECTION & COMMERCE

**H1. Licensing & Copyright™** — 🟡 Partial (`product_protection.py`, `ProductProtection.js`, commerce tiers) — missing: per-platform license terms, rights registry for imported assets, DMCA workflow. Treasure Standard™: **provenance & rights on every asset**. Priority: **Important**. ⭐.
**H2. Commerce / Checkout™** — ✅ Exists (`commerce.py` — real Stripe, server-side pricing, one-time fulfillment). Priority: **Core**.
**H3. Marketing Manufacturing™** — ✅ Exists (`marketing_engine.py`) — master/customer/preview editions + store images, deterministic. Priority: **Important**.

### PHASE I · PUBLISHING & DISTRIBUTION (MO‑007 Universal Publishing Engine™)

**I1. Universal Connector Framework™** — ✅ Exists (`connectors.py`, `oauth_framework.py`, `Connectors.js`) — OAuth (Developer vs Founder mode), token refresh, connection verification. Priority: **Core**.
**I2. YouTube Publishing™** — ✅ Exists (`youtube_publisher.py`, MO‑006) — REAL resumable upload, metadata, thumbnail, playlist, privacy, real Video ID stored. Priority: **Core**.
**I3. Universal Publishing Engine™ (publishing-as-a-stage)** — 🔴 Missing (MO‑007) — a connector interface `publish(product, recipe_rules) → external_id` with: metadata mapping per platform, asset selection, mode (draft/private/unlisted/scheduled/public), status tracking, **retry logic**, external-ID storage, publication audit. Priority: **Core (next big build)**. ⭐⭐ (the defining moat — "manufacture once, publish everywhere").
**I4. Platform Connectors** — 🔴 Missing (except YouTube + native Store): TikTok, Instagram, Facebook, Pinterest, X, LinkedIn, Etsy, Teachers Pay Teachers, Amazon KDP, Shopify, WordPress, Google Drive, Dropbox, OneDrive, Podcast (RSS/Spotify), Email (Resend/SendGrid). Mostly **orchestrate external**; each: auth + metadata map + upload + ID capture + status. Priority: **Important** (sequenced after I3).
**I5. QRU Store™ (native marketplace)** — ✅ Exists (`Store.js`, commerce). Priority: **Core**. ⭐ (owned distribution).
**I6. Publication Verification™** — 🟡 Partial (YouTube returns real ID) → 🔴 generalized "confirm live + store canonical URL/ID + re-check" across platforms. Treasure Standard™: **never mark Published without a confirmed external ID**. Priority: **Core** (part of MO‑007).

### PHASE J · POST-PUBLISH: DELIVERY, ANALYTICS, LIFECYCLE

**J1. Customer Delivery™** — ✅ Exists (`deliverable_renderer.py` + commerce fulfillment + consumer library). 🟡 Missing: email delivery of downloads. Priority: **Core**.
**J2. Notifications™** — ✅ Exists (`Notifications.js`, `routers/*`). 🟡 Missing: external email/SMS/push channels. Priority: **Important**.
**J3. Analytics & Performance Tracking™** — 🟡 Partial (`analytics.py`, `EvidenceDashboard.js`, `metrics.py` — internal evidence-based). 🔴 Missing: **pull real platform metrics** (YouTube views, Etsy sales, etc.) into a unified performance store. Priority: **Important**. ⭐ (closed feedback loop → smarter manufacturing).
**J4. Archive & Lifecycle™** — 🟡 Partial (statuses exist) → 🔴 formal archive stage, retirement, re-issue. Priority: **Future**.
**J5. Reporting™** — 🟡 Partial (dashboards) → executive/financial/production reports export. Priority: **Important**.
**J6. Cost Optimization™** — ✅ Exists (`cost_meter.py` tracking) → 🟡 active optimization (model routing by cost, budget guards). Priority: **Important**.
**J7. Automation / Autonomy™** — ✅ Exists (`autonomous_engine.py`, `autonomy*.py`, `AutonomyCenter.js`) — Level‑5 autonomy scaffolding. Priority: **Core**.

---

## PART 2 — Factory Capability Matrix™ (master table)

| # | Capability | Status | Native vs External | Priority | Build next? | Moat |
|---|-----------|:------:|--------------------|:--------:|:-----------:|:----:|
| A1 | Knowledge Management | ✅ | Native | Core | — | |
| A2 | Research & Extraction | 🟡 | Native + ext (scrape/search) | Important | ▲ | ⭐ |
| A3 | Verification Engine | ✅ | Native | Core | — | ⭐ |
| B1 | AI Orchestration | ✅ | Native + ext LLM | Core | — | |
| B2 | Writing / Translation | ✅ | Native + ext LLM | Core | — | |
| B3 | Editing / Continuous Improvement | 🟡 | Native | Important | | |
| C1 | Graphic & Cover Generation | ✅ | Native + ext image | Core | — | |
| C2 | Illustration System | 🟡 | Native + ext image | Future | | ⭐ |
| C3 | Character Management (WIS) | ✅ | Native | Important | — | ⭐ |
| C4 | Voice Generation | ✅ | Native + ext TTS | Core | — | |
| C5 | Music / Sound | 🔴 | External | Future | | ⭐ |
| C6 | Video Generation & Rendering | 🟡 | Native (slideshow) + ext (AI video) | **Core** | ▲▲ | ⭐⭐ |
| D1 | Deliverable Renderer (PDF/EPUB/PPTX) | ✅ | Native | Core | — | ⭐ |
| D2 | Product Recipes | ✅ | Native | Core | — | ⭐ |
| D3 | Course/Quiz/Presentation | ✅ | Native | Important | | |
| D3b | SCORM / xAPI (LMS export) | 🔴 | Native | Important | ▲ | ⭐ |
| D4 | Accessibility | 🟡 | Native | Important | ▲ | ⭐ |
| E1 | Digital Asset Vault (DAM) | ✅ | Native | Core | — | ⭐ |
| E2 | Version Control | ✅ | Native | Important | | |
| F1 | Workflow Engine | ✅ | Native | Core | — | ⭐ |
| F2 | Batch Manufacturing | ✅ | Native | Core | — | |
| F3 | Manufacturing Director AI | ✅ | Native | Core | — | ⭐ |
| F4 | Scheduling | 🔴 | Native | Important | ▲ | ⭐ |
| F5 | Enterprise Scalability | 🟡 | Native/infra | Future | | |
| G1 | Quality Control / Inspection | ✅ | Native | Core | — | ⭐ |
| G2 | Governance / Constitution | ✅ | Native | Core | — | |
| G3 | Audit Logging | ✅ | Native | Core | — | |
| G4 | Monitoring & Confidence | ✅ | Native | Core | — | |
| G5 | Self-Healing / Failure Intel | ✅ | Native | Important | — | ⭐ |
| G6 | Disaster Recovery / Backup | 🔴 | Native/infra | Important | ▲ | ⭐ |
| H1 | Licensing & Copyright | 🟡 | Native | Important | ▲ | ⭐ |
| H2 | Commerce / Checkout | ✅ | Native + Stripe | Core | — | |
| H3 | Marketing Manufacturing | ✅ | Native | Important | — | |
| I1 | Universal Connector Framework | ✅ | Native | Core | — | ⭐ |
| I2 | YouTube Publishing | ✅ | Native + YT API | Core | — | |
| I3 | **Universal Publishing Engine (MO‑007)** | 🔴 | Native | **Core** | ▲▲▲ | ⭐⭐ |
| I4 | Platform Connectors (TikTok, IG, Etsy, KDP…) | 🔴 | External | Important | ▲▲ | |
| I5 | QRU Store (native marketplace) | ✅ | Native | Core | — | ⭐ |
| I6 | Publication Verification | 🟡 | Native | Core | ▲▲ | ⭐ |
| J1 | Customer Delivery | ✅ | Native | Core | — | |
| J1b | Email delivery of downloads | 🔴 | External (Resend/SendGrid) | Important | ▲ | |
| J2 | Notifications (external channels) | 🟡 | Native + ext | Important | | |
| J3 | Analytics / Performance Tracking | 🟡 | Native + ext platform APIs | Important | ▲ | ⭐ |
| J4 | Archive & Lifecycle | 🟡 | Native | Future | | |
| J5 | Reporting | 🟡 | Native | Important | | |
| J6 | Cost Optimization | ✅/🟡 | Native | Important | | ⭐ |
| J7 | Automation / Autonomy | ✅ | Native | Core | — | ⭐ |

**Tally:** ✅ ~26 · 🟡 ~12 · 🔴 ~9 capabilities.

---

## PART 3 — What to build next (sequenced)

1. **MO‑007 Universal Publishing Engine™ (I3 + I6)** — generalize the YouTube publisher into a connector interface `publish(product, recipe_rules)→external_id` with modes (draft/private/unlisted/scheduled/public), retry logic, external-ID storage, and **publication verification**. Add publishing as a real workflow stage. *This is the highest-leverage next build — it turns the factory into a distribution OS.* ⭐⭐
2. **Scheduling™ (F4)** — required for MO‑007 "Scheduled" mode; editorial calendar + timed release.
3. **Platform Connectors (I4)** — sequence: WordPress/Blog → Pinterest/X/LinkedIn (metadata-light) → Etsy/Shopify/KDP (commerce) → TikTok/Instagram (video). Each rides the MO‑007 interface.
4. **Analytics Performance Ingestion (J3)** — pull real platform metrics → close the loop into Continuous Improvement (B3).
5. **Email delivery (J1b)** + external Notifications (J2) — Resend/SendGrid for downloads & alerts.
6. **Video Generation Phase 2 (C6)** — AI-rendered educational video as a native manufacturing stage. ⭐⭐
7. **Backup/Disaster Recovery (G6)** and **Licensing registry (H1)** — pre-scale enterprise trust.

## PART 4 — Strategic moat (build native, don't rent)
- ⭐⭐ **Universal Publishing Engine + native video render** — "manufacture once, publish everywhere, verified" is the category-defining advantage.
- ⭐ **Verification + Treasure Standard™ + evidence-graded research** — trust is the durable moat in an AI-slop world.
- ⭐ **Recipes + Deliverable Renderer + DAM + Character WIS** — a proprietary, brand-consistent production system competitors can't copy quickly.
- ⭐ **QRU Store™** — owned distribution + customer relationship.
- **Rent (orchestrate externally):** raw LLMs, TTS, AI image/video/music models, payment rails, individual social platform APIs — these are commodities; own the *orchestration, quality, and trust* layer on top.

## Guiding principle
Own the **manufacturing intelligence, quality, trust, and distribution orchestration** natively; rent the **raw generation commodities**. Every capability must satisfy the Treasure Standard™: no fake states, verified provenance, confirmed external IDs before "Published."
