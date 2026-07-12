# QRU Factory™ — Enterprise Knowledge Manufacturing OS

## Original Problem Statement
Production-ready enterprise OS for "QRU", a knowledge-manufacturing company using an autonomous
"Digital Workforce" to manufacture educational products. Core: Stripe commerce, Enterprise Workflow
Engine, Level-5 Autonomy, QRU Constitution governance, "First Dollar Mode".

## Standing Directives (Founder)
- **Founder Beta Stabilization Mode** — NO NEW FEATURES unless explicitly requested. Finish & stabilize.
- **Knowledge-First Rule** — never AI-generate customer-facing Knowledge Records.
- **$0 AI by default** — deterministic code; LLM caps handled gracefully.
- **Treasure Standard™** — no dead ends, no silent failures, evidence before any number/approval.
- Language: English only (code, comments, UI).

## Architecture
- Backend: FastAPI + MongoDB (`/app/backend`, routers in `/app/backend/routers`).
- Frontend: React + Tailwind + Shadcn (`/app/frontend/src`, pages + components).
- Auth: JWT founder login. Stripe: TEST mode (sk_test).

## Phase Next — Manufacturing Orders (approved sequence)
MO-001 Quality Gates ✅ · MO-002 Enterprise Manufacturing Dashboard ✅ · MO-003 Knowledge Record 2.0 ✅ · MO-004 QRU Design Language ✅ · MO-005 Manufacturing Director™ ✅ · MO-006 YouTube Publisher™ (Founder Upload Mode) ✅ · MO-007 Universal Distribution Framework™ ✅ · MO-008 Governance Binding Layer™ ✅. Build one at a time; deterministic infra before AI content.

## Completed (recent → older)
### Session 2026-07-10 (fork) — MO-007 expansion, MO-011, MO-015/016/017, MO-018, MO-021/023 foundation
- **MO-009/010 Visual & Media Studio™ wired** into `/visual-studio` (route + nav). VERIFIED iteration_35.
- **MO-007 Connector Expansion** — added real, code-complete **Dev.to** (blog) + **Shopify** (marketplace) connectors to `distribution/connectors.py` following the WordPress pattern; added the missing **Developer Setup config UI** (`ConnectorConfigDialog`) to `/distribution` with honest states + validation. VERIFIED iteration_36 (17/17).
- **MO-011 QRU Media Starter Kit™** (`media_starter_kit.py`, `routers/media_starter_kit.py`, `/media-starter-kit`) — deterministic $0 assembly of 13 components + 8 media outputs, Treasure/Gold gated, honest ready/pending. VERIFIED iteration_36.
- **MO-015/016/017 Trust & Authenticity™** (`trust_authenticity.py`, `routers/trust.py`, `/trust`) — protection layers (honest enforced/platform_provided), security levels, platform capability awareness, authenticity certificate + QRU-SEAL™ + SVG QR, permanent registry, PUBLIC verify lookup, audit log. FR-095 Protect Without Punishing™. VERIFIED iteration_37 (20/20).
- **MO-018 QICS™ Intelligent Companion System** (`qics.py`, `routers/qics.py`, `/companion`) — immutable type-aware identity (QRU-BK/KR/WB/CR/AU/VD/PT/AS), dynamic QR gateway (permanent, destination-updatable, never expires), companion portal (15 sections), PUBLIC portal scan + analytics events. FR-096 Lives Beyond the Page™. VERIFIED iteration_37.
- **MO-021 Stock Video + MO-023 Audio foundation** (`media_library.py`, `routers/media_library.py`, `/media-library`) — one governed acquisition layer: 10 providers (Pexels/Pixabay/Freesound live-capable, tier-2 prepared), video+audio collections, StockMediaAsset schema, Master Asset Vault registration, live search gated on real keys (honest NEEDS_SETUP otherwise). FR-097 No Unverified Stock Media™ + FR-AUDIO. Backend curl-tested + frontend smoke-tested; live search pending Pexels/Pixabay keys.

## OPEN / PENDING (this fork)
- **MO-021 END-TO-END LIVE PROOF — DONE (2026-07-10) · QRU Factory Milestone 001:** Real pipeline verified (iteration_38, 17/17): live Pixabay search → recommend → approve → license verify → download+sha256 checksum → register → **OpenAI TTS narration (emergentintegrations, tts-1, voice sage)** → .srt captions → **ffmpeg 720p MP4 render (burned captions + QRU brand bar)** → ffprobe quality review → Master Asset Vault™ → distribution-ready. Endpoints: /api/media-library/produce-proof, /milestones, /asset/{id}/file (streams video/mp4). Provider credential hardening: masked keys, validate-before-save (rejects bad keys), Test Connection codes, audit logs, revoke; transient-flake fix (only definitive codes change stored status).
- **Scene Asset Matcher™ — DONE (2026-07-10):** POST /api/media-library/scene-match — narration→scenes→learning purpose→literal/metaphorical/emotional/environmental terms + topic exclusions (forex: gambling/casino/guaranteed profit/crypto/etc)→live provider search→top-5 deterministic-scored candidates/scene (relevance/technical/composition/brand-fit/licensing/representation) with tier (Gold Gallery≥90/Approved≥80/Shortlist≥70) + crop/start/end/duration/speed/transition/text-safe recommendations + Approve→Vault. UI panel on /media-library. Self-tested (curl + screenshot).
- **Pexels** = env-provided (rate-limited proxy, honest errors); **Pixabay** = real user key ACTIVE; pixabay_music/freesound still need keys.
- **MO-020 Gold Master Design System™ / FOREX FOUNDATIONS™** — AUTHORIZED, NOT STARTED. Fresh from DB Forex KR; legacy PDF supplied (preserve as "Legacy Baseline"). Phased: Visual Blueprint / Page Composition / Preflight Service / Template Registry engines → outline/page-type map → 28–40pp PDF + 14 visuals.
- **MO-023 audio-specific UI tabs**, **MO-024 Mind & Renewal University™** — QUEUED.
- **First full Flagship Showcase™ (30–60s, MO-012)** using Scene Matcher output — QUEUED.


- **MO-021 credential hardening + live proof — DONE (2026-07-10):** Protected provider flow with masked keys (e.g. `pex_••••••••WXYZ`), validate-BEFORE-save (Pixabay correctly rejects bad keys → 400; nothing saved), Test Connection returning CONNECTED/INVALID_KEY/RATE_LIMITED/PROVIDER_UNAVAILABLE/PERMISSION_DENIED, status ACTIVE/DEVELOPER_SETUP_REQUIRED/PREPARED_NOT_ACTIVATED, credential audit logs (`credential_logs`), revoke, last_validated/last_successful_request. Live Pexels proof: searched → registered a REAL asset (kaboompics finance clip) to Master Asset Vault with creator/source/Pexels License/commercial=true/Approved. NOTE: Pexels egress in the PREVIEW env is a limited/rate-limited proxy cache (intermittent 401 on uncached query,per_page combos) — handled with retry + HONEST error UI; a real Pexels key needed for reliable production use. Pixabay/Freesound still need real keys.
- **MO-020 Gold Master Design System™** — AUTHORIZED to proceed fresh from the verified Forex KR in DB (legacy PDF now supplied: https://customer-assets.emergentagent.com/job_understanding-os/artifacts/nkurrvf8_Forex%20KR%20%20Workbook%20%20Workbook.pdf — preserve as "Legacy Baseline — Forex KR Workbook — Pre-Gold-Master Redesign"). NOT STARTED. Phased: engines (Visual Blueprint, Page Composition, Preflight Service, Gold Master Template Registry) → outline/page-type map → 28–40pp PDF + 14 visuals.
- **Scene Asset Matcher™ (MO-021 intelligence layer)** — QUEUED after live provider proof (narration→scenes→literal/metaphorical/emotional/environmental search terms + Forex exclusion terms: gambling/casino/guaranteed profit/crypto/etc → top-5 candidates/scene with scores + crop/timing/text-safe zone).
- **MO-023 audio-specific UI tabs** + **MO-024 Mind & Renewal University™** — QUEUED.
- **First Live Media Proof (MO-021 §6)** — 30–60s Flagship Showcase using a Gold Standard visual + approved stock asset — QUEUED (needs reliable stock access + Scene Matcher).


### QIKS™ Founder Governance Library + MO-008 Governance Binding Layer™ (2026-07-10) · VERIFIED (iteration_34)
- **15 Founder governance PDFs ingested** into QIKS™ as founding Institutional Standards™ (STD-00017…00031), verbatim content (`qiks.adopt_founder_document`, dedupe by name, no-overwrite versioning). Full-document viewer added to `/qiks` (Classification, Source, verbatim body).
- **Governance Binding Layer™** (`governance_binding.py`, `routers/governance_binding.py`): 8 governed agents + 7 governed manufacturing stages + design decisions, each bound to a real standard. Priority enforcement 5/5 (KR Master Spec is #1). Endpoints: /overview, /agents, /design, /strip/{entity}, /manufacturing/{id}/compliance.
- **Factory Agents™ page** (`/agents`): governance loop, agent registry, Manufacturing Governance Chain (compliance record per order), Experience Design Governance. Visible **"Governed by"** strips on Command Center + Knowledge Architecture (reusable `GovernedBy` component).

### MO-007 Universal Distribution Framework™ (2026-07-10) · VERIFIED (iteration_34)
- **Connector SDK™** (`distribution/sdk.py`): one interface every destination implements (ConnectorKind publish/deliver, DistMode draft/private/unlisted/scheduled/public, DistStatus, DistributionResult with real external_id).
- **Connectors** (`distribution/connectors.py`): QRU Store™ (native, real — lists product Published + purchasable), YouTube (real, via Data API, requires file), + honest NEEDS_SETUP stubs (WordPress, Google Drive, Email, Etsy, Amazon KDP). REGISTRY-based — new platforms just implement the interface.
- **Engines** (`distribution/engines.py`): Publishing/Delivery/Verification/Analytics over one job ledger (`distribution_jobs`) with retry (max 3), verification (stores canonical external ID), real analytics (Store purchases/revenue; YouTube views). Router `routers/distribution.py` (+ chunked upload). Frontend **Distribution Center™** (`/distribution`).

### MO-006 YouTube Publisher™ — Founder Upload Mode (2026-07-10) · Built & endpoint-verified (real upload pending a Founder MP4)
- `youtube_publisher.py` (resumable Data API upload, metadata/thumbnail/playlist/privacy, real Video ID, verify_video, video_stats), `routers/youtube.py` (chunked MP4 upload + publish). Frontend **YouTube Publisher™** (`/youtube`): compose from a product, Private default, publish → real Video ID. YouTube channel connected via OAuth.


### MO-005 · QRU Manufacturing Director™ (2026-07-05) · VERIFIED (iteration_33: 12/12 backend, frontend 100%)
- **`manufacturing_director.py`**: supervisory review of manufacturing orders. Verdicts: APPROVE /
  APPROVE_WITH_CONDITIONS / HOLD / REJECT. **The verdict is ALWAYS deterministic/evidence-based**
  (`_decide()` is the sole authority) — reuses `inspection_system.inspect_kr_for_manufacture` +
  `knowledge_record_v2.manufacturing_readiness`/DEPENDENCY_MAP. Identifies exactly which KR 2.0
  sections are missing per requested product type. `_find_kr()` resolves the backing KR by
  `knowledge_record_id` else keyword-overlap (≥0.5) on topic vs KR title.
- **Optional AI executive brief** (`_ai_brief`): reuses existing `ai_service.llm_generate` (Emergent
  key). Treasure Standard™: AI writes narrative ONLY, NEVER changes the verdict; on LLM cap it falls
  back to a `_deterministic_brief` ($0 AI). Verified verdict is identical with/without AI.
- **`routers/director.py`**: GET /api/director/queue (fast, no AI), GET /api/director/review/{id}
  (?use_ai=true), POST /api/director/review/{id}/decision (applies recommended_status →
  APPROVE→Research, HOLD/REJECT→Queued; appends approval_history attributed to the Director;
  idempotency-guarded).
- **Frontend** `ManufacturingDirector.js` (route `/director`, nav "Manufacturing Director™"):
  summary MetricCards, verdict-filtered queue table, ReviewPanel (verdict, confidence, executive
  brief with "Request AI brief", missing knowledge → /kr2, readiness-by-product, recommended actions,
  Apply Director Decision).
- **One-click "Manufacture Cleared" batch** (POST /api/director/manufacture-cleared, super-admin):
  launches `product_automation.manufacture_package` for every CLEARED order (re-passes Quality Gates);
  returns launched[] + skipped[] with explicit reasons (no silent failures). Verified end-to-end:
  MO-00021 (Poster ← verified KR-00008) → APPROVE → launched → production order completed 100% →
  PRD-00129 Published. Orders with empty product_types now correctly return HOLD (nothing to make).

### MO-004 · QRU Master Design Language™ + QRU Component Library™ (2026-07-05) · VERIFIED (iteration_32: frontend 100%)
- **Global tokens** (`index.css`): Deep Navy `--primary` (foundation), QRU Gold `--secondary`
  (verified excellence), Royal Purple `--accent` (signature — used sparingly), white clarity canvas.
  Fonts: **Playfair Display** (headings) + **Manrope** (body). Named tokens `--navy/--gold/--royal`
  remapped so all existing utilities cascade the new hierarchy. `tailwind.config.js` fonts + shadows.
- **QRU Component Library** (`src/components/qru.js`): QRUShield, TreasureSeal, ProvenanceBadge,
  StatusChip (universal status→tone map), MetricCard (accent left-rule + hover lift), Panel, ScoreBar,
  StageTimeline, VerifiedBadge — every future page inherits the QRU look.
- **Shell**: Layout sidebar = inline QRUShield + navy ground + gold active state; PageHeader = gold
  left-rule + Playfair display title. Login redesigned (navy brand panel, QRUShield, royal/gold glow).
- **Flagship pages elevated** to the library: Manufacturing Command Center, Quality Gates, Evidence
  Dashboard, Knowledge Architecture (KR2), Publishing Connectors. Remaining ~55 pages inherit tokens/
  fonts automatically per Founder directive (no manual per-page polish).


### MO-003 · Knowledge Record 2.0™ (2026-07-05) · VERIFIED (iteration_31: 13/13 backend, frontend 100%)
- **`knowledge_record_v2.py`**: 36 sections across 10 groups, each an independent managed object
  {section_id,title,content,status,source,verification_status,confidence_score,author,reviewer,
  created_at,updated_at,version,evidence_links,dependencies,manufacturing_ready}. Extensible — new
  sections need no DB redesign. **Manufacturing Dependency Map** (product-family → required sections)
  + reverse lookup. Non-destructive `migrate_kr` mapped legacy fields (verified_truth→Deep Explanation,
  qru_translation→QRU Translation™, references→Scientific References evidence_links, etc.), preserved
  unmapped legacy. All 47 KRs migrated (idempotent).
- **`routers/knowledge_v2.py`**: /registry, /migrate (super-admin), /{id}, PUT /{id}/section/{sid},
  /{id}/manufacturing-readiness, /dependency-map.
- **Gate integration**: `manufacture_package` now pauses when required KR 2.0 sections are incomplete
  (e.g. video needs YouTube Script + Image Concepts) and names the missing sections.
- **Frontend** `KnowledgeRecord2.js` (route `/kr2`, nav "Knowledge Architecture™"): KR selector,
  completeness bar, collapsible per-section editor (content/status/source, versioned).
### MO-002 · P6 — Enterprise Manufacturing Dashboard™ (2026-07-05) · VERIFIED (iteration_30: 18/18 backend, frontend 100%)
- **`routers/manufacturing_dashboard.py`** `GET /api/manufacturing-dashboard`: deterministic command
  center aggregating KRs (total/verified), products (total/published), queue, connector status + health
  (23 rows), publishing, REAL Stripe revenue (TEST provenance), licensing, throughput (7d), quality
  scores (avg + cleared/paused from Inspection System™), Treasure Standard™ certified, and live
  actionable alerts (paused products → /inspection, connectors needing auth → /connectors, etc.).
- **Frontend** `ManufacturingDashboard.js` (route `/mfg-command`, nav "Manufacturing Command™"):
  alerts, 10 provenance-badged metric cards (drill to /evidence, /inspection, /connectors), connector health table.

### MO-001 · P4 — Manufacturing Quality Gates / Inspection System™ (2026-07-05) · VERIFIED (iteration_29)
- **`inspection_system.py`** (deterministic, $0 AI): 9 gates — Knowledge/Verification Completeness,
  Educational Value, Consumer Clarity, Visual Readiness, Product Eligibility, Connector Readiness,
  Publication Readiness, Treasure Standard™. Blocking gates PAUSE manufacturing + Director report.
  `_kr_text` reads real KR fields (verified_truth, qru_translation, deep_roots, simple_answer…).
- **`routers/inspection.py`**: /summary, /product/{id}, /knowledge-record/{id}, /gates.
- Gate enforced in `product_automation.manufacture_package` (400 pause when blocking gates fail).
- **Frontend** `ManufacturingInspection.js` (route `/inspection`, nav "Quality Gates™").

### Connector UX honesty + Media Studio + YouTube live (2026-07-05)
- Media Studio no longer fakes "Published" (destinations "· Coming Soon"; `publish_media` refuses fake publish).
- YouTube connected via real Google OAuth (fixed iframe 403 by launching OAuth in a top-level tab).
- Connectors: Developer/Founder mode, every disabled Publish has a reason, "Next:" step per card.

### MO-046 — Founder Beta Completion™ · Universal OAuth Framework™ (2026-07-05) · VERIFIED (iteration_26: backend 16/16, frontend 100%)
- **`oauth_framework.py`** — one config-driven OAuth 2.0 engine for 15 providers (YouTube, Google
  Drive/Docs/Slides, Microsoft, OneDrive, Dropbox, Etsy, LinkedIn, Facebook, Instagram, Pinterest,
  TikTok, X, Canva). Standard authorize/token/userinfo endpoints + scopes; PKCE for Etsy/X/TikTok/Canva.
  Amazon KDP & TPT honestly marked unsupported (no public OAuth publishing API).
- **Developer-side config** (`db.connector_configs`): admin sets Client ID / Secret / Redirect URI;
  secret encrypted at rest (Fernet, reuses `INTEGRATION_ENC_KEY`) and NEVER returned to the client.
- **Founder flow**: Connect → `GET /authorize-url` (real provider URL) → official provider login →
  `GET /api/oauth/callback` (public) exchanges code→tokens (encrypted), fetches account name →
  Connected. Automatic token refresh. Founder never sees tokens/credentials.
- **Honest statuses**: Developer Configuration Required → Needs Authorization → Connected → Test Passed
  / Disconnected. **Test Connection** returns an evidence checklist (auth, account ownership, token
  validity via live userinfo call, publish/read permission from granted scopes, refresh capability,
  Ready to Publish). Disconnect + delete-config revert cleanly.
- **Frontend** `Connectors.js`: Developer Setup dialog, OAuth Connect (redirect to provider),
  Test Connection checklist dialog, Disconnect; callback return (`?oauth=success|error`) toasts +
  reloads. No dead/silent buttons — disabled Publish always shows a reason.
- Founder Beta Status™ answers updated to reflect the OAuth framework honestly.

### MO-045 — Founder Beta Stabilization & Evidence Completion (2026-07-05) · VERIFIED (iteration_25)
- **Evidence Metrics Engine™** (`routers/metrics.py`): `GET /api/metrics/summary` returns 15 metrics
  across Commerce/Manufacturing/Publishing, each with a provenance label (LIVE / TEST / SIMULATED /
  NOT_TRACKED). `GET /api/metrics/{id}/evidence` drills into the exact underlying records with full
  fields (Order ID, Product, Customer, Date/Time, Provider, Payment, Live/Test, Revenue, Taxes,
  Discounts, Fulfillment, Delivered, Transaction ID, Platform…). `GET /api/metrics/beta-status?host=`
  returns the Founder Beta Status™ transparency Q&A + deployment state + shareability.
- **Synthetic revenue REMOVED** everywhere: `analytics.py` (was `published*1250 + customers*3400`) and
  `command_center.py` mission-impact (was `11450 + certificates*49`) now compute revenue ONLY from
  `db.payment_transactions` where `payment_status='paid'`. Single source of truth.
- **Frontend** `pages/EvidenceDashboard.js` (route `/evidence`, nav `nav-evidence`): clickable metric
  cards with provenance badges + drilldown modal (real record tables / honest empty states) +
  permanent Founder Beta Status™ panel (Shareable=LIMITED, Payments=SANDBOX TEST, blocks-promotion
  list, 19 plain-language Q&A, deployment = "Founder Preview (Private Beta)").
- **Universal Connector Framework™ now reachable**: added `/connectors` route + nav `nav-connectors`
  (UI/backend already existed from prior session — only wiring added, no redesign).
- Workflow transparency: existing Gate Ladder retained (Founder Inbox evidence dossier).

### Customer Delivery Pipeline (2026-07-04) · VERIFIED iteration_24
- Store → Stripe checkout → post-checkout secure file download. `commerce.purchase_download`.

### MO-038…MO-043 — Autonomy, Design Director, Evidence Decision Center, Self-Guiding Gates,
Founder Beta Dashboard, Automatic Knowledge Extraction, PreviewViewer. (all VERIFIED)

## Known Limitations (as of MO-046)
- **OAuth end-to-end requires registered provider apps**: the framework is complete and honest, but a
  developer/admin must register an OAuth app at each provider and enter Client ID/Secret/Redirect URI
  before Connect works. Live authorization can only be verified once real credentials exist.
- **Automated file publishing** to OAuth connectors (uploading the actual video/doc/listing) is NOT
  yet wired — connect + test connection are operational; the publish-the-file step is a next milestone.
- Stripe TEST mode only — no live payments; email delivery not wired (downloads shown in-app).
- Amazon KDP & Teachers Pay Teachers have no public OAuth publishing API (honestly shown).
- `analytics.py` still emits a synthetic `knowledge_growth` trend chart (Analytics page only).
- LLM text/image generation CAPPED — deterministic $0 fallbacks in use.

## Production Blockers
- Live Stripe keys (currently sk_test) · Email delivery for customer downloads · Registered OAuth apps
  + automated publish-the-file step for external connectors.

## Backlog / Next Milestones (P-ordered, awaiting Founder direction)
- P1: Reach Founder Beta Complete™ (25 consecutive clean manufacturing runs).
- P2: Customer Purchase History / Library (re-download past purchases).
- P2: Replace synthetic `knowledge_growth` trend with real time-series or SIMULATED label.
- Pre-Production: add live Stripe keys + email delivery for public launch.

## Credentials
- Founder: `22j2rsdzb8@privaterelay.appleid.com` / `QruFounder2026!`

## Session 2026-07-11 (fork) — MO-012, QRU Constitution adoption, Factory OS, Product Continuity
### Scene Asset Matcher™ cross-scene dedup — DONE (iteration_40, 18/18)
- `scene_matcher.py`: cross-scene ledgers (provider asset ID, canonical source URL, creator, title Jaccard). Hard duplicates never occupy the selected slot; near-duplicates penalized. Response adds `variety_score`, `dedup_status`, `dedup_flags` per candidate + `project_variety_score`/`unique_assets`/`unique_creators`/`variety_ok`/`scenes_needing_review`. Configurable variety rules (max_per_creator etc).
### MO-012 Controlled Flagship Showcase™ Pilot + Gold Master Certified™ — DONE (iteration_40) · MILESTONE 001 preserved unchanged
- `flagship_showcase.py` + `/api/media-library/showcase/*`: 3 approval modes (Human Approval Required default, Auto-Select Draft Preview only, Governed Auto-Select disabled until ≥5 approved runs + authorization). Multi-scene ffmpeg concat assembly (per-scene license verify→download→checksum→register), TTS narration, captions, Technical QA + Brand/Content QA, Master Asset Vault™, Distribution Ready. `certify_gold_master` enforces 11 gates (authorized only; drafts can never certify). Production Acceptance Record (`production_acceptance_records`) preserves scene list, license evidence, checksums, QA, version history. Frontend `FlagshipShowcase.js` (`/flagship-showcase`): full Scene Approval Interface (approve/reject/replace/search-again/lock, dedup+variety badges), transparent step ledger, video player, Gold Master certify.
### QRU Factory™ Constitution (QRU-CON-0001 v1.0, Founder Approved) — ADOPTED & BOUND (iteration_41)
- `constitution_v1.py`: verbatim full text + 14 structured sections + 12 product statuses + 4 quality gates + 3 automation modes; registered in `db.factory_constitution` AND the QIKS Standards Registry (`qiks_standards` id QRU-CON-0001). `governance_binding.py`: 9 system→section bindings (Knowledge Foundry, Product Mfg, Design Intelligence, Factory OS, Approval Modes, Quality Gates, Gold Master, Vault, Distribution). Endpoints `/api/governance/factory-constitution[/bindings]`. Frontend `Constitution.js` (`/constitution`): searchable sections, binding map, gates, statuses. Version-controlled — amendments create new versions (never overwrite v1.0).
### Factory OS™ Phase A — Create experience — DONE (iteration_41)
- `factory_os.py` + `/api/factory-os/*`: 11 outcome catalog with honest maturity labels; deterministic `knowledge_gap_check` (Knowledge-First — never fabricates a KR; obscure topics return exact message "This topic has not yet been manufactured as a governed QRU Knowledge Record™." + offer to begin Promotion Pipeline); `build_plan` returns governed plan + guidance (the 7 §7 questions). Frontend `CreateExperience.js` (`/create`, nav "Start Here"): outcome grid → describe → Knowledge-First check → guidance → governed plan → launch. Governed by QRU-CON-0001 §7/§8.
### Product Continuity Principle™ (Constitution §4/§14G) — DONE (iteration_42, 14/14 + 2 honesty fixes)
- `continuity.py` + `/api/factory-os/projects*`: per-outcome stage chains (video 11-stage, book/podcast/audiobook/presentation/workbook). `_advance_auto` completes `auto` stages and pauses at workflow/gate/connector. Human-approval gates (§9), connector stages honestly `blocked` (never faked publish), blocked-KR routes to Promotion Pipeline™. Pause/resume/stop. Frontend `ProjectsContinuity.js` (`/projects`, nav "My Projects"): stage pipeline board, progress, recommended next action, approve/open/complete/setup + pause/resume/stop. Create→launch now creates a tracked project.

### Automatic Asset Continuity — YouTube Publisher (Founder directive) — DONE (iteration_43, 8/8 backend, frontend 100%)
- Foundational Principle: a Factory-manufactured product NEVER requires manual re-upload into another module. `routers/youtube.py`: `GET /factory-assets` lists vault videos (provider qru_production, file on disk); `POST /publish` now accepts `factory_asset_id` → resolves the vault MP4 (path validated inside media root), auto-fills title/description/tags from the asset + Production Acceptance Record, extracts a real first-frame thumbnail via ffmpeg, publishes via the YouTube Data API, and NEVER deletes the vault master. Draft previews are blocked from publishing. On success, `media_assets` is stamped with `youtube_video_id`/`youtube_url`. Verified with a REAL publish to the connected channel "Quest Understand" (real Video ID). Frontend `YouTubePublisher.js`: source toggle (Factory-manufactured default / External manual upload); Factory mode = dropdown picker, no file browse, auto-filled metadata; manual mode retained for external videos only.

## Roadmap (Founder-approved, remaining)
### STD-MFG-0001 — QRU Universal Manufacturing Flow Engine™ — DONE (2026-07-12, iteration_51, backend 14/14 + frontend 100%)
- `manufacturing_flow.py` + `routers/manufacturing_flow.py` (`/api/flow/*`): constitutional orchestration layer (KMES) atop the Product Continuity Engine. Canonical **Universal Production Lifecycle** (18 stages idea→…→Enterprise Memory→Observatory loop) + 13 governed production states; **Module Responsibility Registry**; **Next-Stage Intelligence** (current/previous/next/remaining/approvals/blockers/health); **Production Blueprint**; **Production Cards™**; **Smart Handoffs** into Enterprise Memory (`db.flow_transitions`); **Enterprise Dashboard**; **Constitutional Registry** (QRU-CON-0001/0002/STD-MFG-0001, never overwritten). Registered in constitution + QIKS + registry. Honesty invariant verified: Gold Master never auto-certified by simple approval.
- Frontend `ManufacturingFlow.js` (`/flow`, nav-flow): 4 tabs (Enterprise Dashboard + Factory Health + Production Cards™, 18-stage Lifecycle, Module Registry, Constitutional Registry).

### Enterprise Architecture Foundation (QRU Enterprise Intelligence Platform™) — PARTIALLY DELIVERED via STD-MFG-0001
- Delivered: Constitutional Registry, Enterprise Lifecycle engine, Module Responsibility declarations, next-stage/dependency awareness, Enterprise Memory of transitions, Enterprise Dashboard.
- FUTURE (inherit this foundation): 4 Pillars as governed entities + relationship map; Capability Maturity Model (11 states); Enterprise Health Dashboard (11 drillable healths); Knowledge Graph navigator; Enterprise Memory decision store; per-capability AI-Governance declarations; Measurement Framework trends; Enterprise Showcase; Experience Layer (navigate-by-outcome).


### QRU Enterprise Publishing & Presentation Standard™ (QRU-CON-0002) — SPRINT 1 DONE (2026-07-12, iteration_50, backend 13/13 + frontend 100%)
- `publishing_standard.py` (single source of truth) + `routers/publishing.py` (`/api/publishing/*`): versioned constitutional standard QRU-CON-0002 v1.0, registered in `factory_constitution` + QIKS registry + governance bindings (`publishing_bindings`: Deliverable Renderer, Cover Studio, Design Intelligence, Pre-Ship Gate, Factory OS/Concierge, Distribution, Media — every generator inherits it). Machine-readable design tokens (13-level typography, 6 color tokens w/ full governance metadata, layout/margins, dividers), governed **tokens.css**, **QRU Callout System™** (10 types), professional **TOC engine** (`clean_toc_markdown` strips markdown/urls/anchors/brackets → aligned dot-leader typeset), **Cover & Visual Identity Standard™** + 4 classified reference covers (Approved Reference / Inspiration / Template Candidate — NOT auto Gold Standard).
- **Treasure Standard™ Pre-Ship Gate** (`preflight_validate`): 17 deterministic, auditable, BLOCKING rules (markdown remnants, raw urls/anchors, TOC malformed/page refs, heading order, approved fonts, min font size, contrast, safe margins, image alt/resolution, placeholders, metadata, human approval, unapproved AI assets, token version, cover thumbnail). Severities BLOCKING_FAILURE/WARNING/ADVISORY/PASSED/NOT_APPLICABLE; verdict RETURN_TO_PRODUCTION vs TREASURE_STANDARD_PASSED; audit trail in `preflight_runs`.
- **Pilot — THE SCIENCE OF UNDERSTANDING™** regenerated: defective source (12 BLOCKING → RETURN_TO_PRODUCTION) vs governed rebuild (0 blocking → TREASURE_STANDARD_PASSED); clean typeset TOC; chapter opening. Same tokens render in **in-app preview + tokens.css (HTML/CSS) + governed PDF** (`/pilot.pdf` via fpdf2; fonts substitute per platform, semantic role preserved).
- **Cover Studio™** (`/cover-studio`): governed AI cover production (Gemini Nano Banana via Emergent key) — produced a real premium navy/gold pilot cover (QRU shield, Treasure Standard seal, brain-gears focal art) in the reference family without copying. Provenance stored (provider/model/date/prompt/version/standard); states DRAFT_CONCEPT→UNDER_REVIEW→REVISION_REQUIRED→APPROVED_DESIGN→GOLD_MASTER→RETIRED (GOLD_MASTER requires APPROVED_DESIGN — no auto-cert); spec-only/manual fallback so provider outage never blocks publishing. Human approval always required.
- Frontend `PublishingStandard.js` (`/publishing`, nav-publishing): searchable standard, live typography/color/callout previews, TOC before/after, Pre-Ship Gate before/after, reference gallery + governed PDF button.

### Publishing Standard — REMAINING SPRINTS (P1, inherited-but-not-yet-activated)
- Platform renderers: DOCX, Google Docs, WordPress, Canva, PowerPoint/slides, KDP print-wrap, mobile/dark-mode adapters (structurally inherit the standard; activate per controlled sprint).
- Wire the Pre-Ship Gate as a mandatory blocking step inside every existing product generator (deliverable_renderer, media_production, flagship_showcase) + authorized-exception audit log.
- Cover Studio derivatives: full print wrap w/ spine calc + bleed/safe-zone overlays, back-cover grid, barcode area, grayscale/print preview, per-platform export presets; eBook/workbook/KR/course-thumbnail/podcast/social derivatives that inherit identity (not stretch/crop).
- Chapter-opening / educational-diagram / header-footer components rendered into real multi-page book/workbook output.

### QCIOL™-STD-0001 — QRU Collaborative Intelligence Operating Experience™ (FUTURE, Founder-approved directive; NOT in Sprint 1)
- Evolve Factory Concierge™ into the governed operating experience: 3 modes (Quick Request™ / Guided Collaboration™ / Enterprise Planning™), Guided Production Mode™ (post-Gold-Master recommendations w/ approval), Production Blueprint™ visual pipeline, Factory Awareness™ (all departments), Proactive Recommendations™ (approval-gated), Decision Support™ (explain WHY + estimates), unified Production Dashboard + Founder Command Center™, Learning Concierge™, Enterprise Memory™, command-center visual language. Human Judgment Always™; no autonomous execution.
- **Phase C: QRU Factory Operating Manual™** — interactive, searchable, module-linked, context-aware, embedded; downloadable PDF/Markdown/Word/HTML (part of QCIOL priority).
- Universal "Publish Everywhere" (TikTok/Reels/LinkedIn 9:16 + per-target failure isolation); MO-023 Audio Library™; MO-024 Mind & Renewal University™; MO-020 FOREX Workbook; auto-link MO-012 Gold Master into continuity stages.
### Phase B — Factory Concierge™ — DONE (2026-07-12, iteration_49, backend 11/11 + frontend 100%)
- `factory_concierge.py` + `POST /api/factory-os/concierge/message` (+ `GET /concierge/session/{sid}`): conversational guide over Factory OS. Deterministic parsing ($0) of a plain-language request → outcome + topic + audience + goal; optional user-enabled light-AI ONLY parses the request (never authors knowledge). Knowledge-First check is ALWAYS deterministic (fos.knowledge_gap_check on Verified KRs) — zero KR hallucination. Sessions persisted in `db.concierge_sessions`; slots accumulate across turns. Stages: need_outcome (with outcome suggestion chips) → need_topic → ready (verified KR found → launch workflow) OR knowledge_gap (honest "not yet a governed Knowledge Record" + offer Knowledge Manufacturing Pipeline). Reset short-circuits parsing (no "start over" false topic).
- Frontend `FactoryConcierge.js` (`/concierge`, nav "Factory Concierge™"): chat UI with greeting (once, StrictMode-safe), light-AI toggle (default off), suggestion chips, live "Your request" rail + Knowledge-First panel with Launch / Begin Knowledge Pipeline buttons. Governed by QRU-CON-0001 §7/§8/§3.1.

### MO-028 Civilization Status improvement — DONE (2026-07-12, iteration_49)
- `improvement_loop.py`: civilization_status ALWAYS renders all 6 departments (idle → standby=true, progress=100, "Standing by"). Added auditable `cycle_log[]` (which department raised which score each pass). Frontend `fs-loop-cyclelog` Improvement Log + standby dept styling.

### MO-028 QRU Autonomous Improvement Loop™ — DONE (2026-07-11, iteration_48, backend 12/12 + frontend 100%)
- `improvement_loop.py` + `POST /api/media-library/improvement-loop`: evaluate (Creative Direction Report) → auto-assign every recommendation to a specialized department (Creative Director™, Design Intelligence™, Director Intelligence™, Learning Experience™, Knowledge Verification™, QA™) via deterministic ROUTING → improvement cycles nudge each dimension toward an honest ceiling → re-evaluate → present ONE Gold Master Candidate. HONEST: sensitive topic (medical/health/financial/forex/legal…) with NO verified KR → knowledge_verification becomes a BLOCKING work order, gold_master_candidate_ready=false (never fabricated/false-certified). Threshold clamped 70–98.
- Frontend `FlagshipShowcase.js` "Civilization Status" dashboard (`fs-loop*`): auto-runs after Creative Direction; animated per-department progress bars, threshold slider + re-run, Treasure Standard climb, Gold Master Candidate Ready card (score/100 · Departments Complete N/N · Approve/Request Changes/Publish), honest blocking panel, always-visible honest_note. Approve unlocks Manufacture. Governed by QRU-CON-0001 §5/§6/§9/§10.

- **Phase C: QRU Factory Operating Manual™** — in-app interactive (searchable, module-linked) + downloadable PDF/Markdown. (NEXT)
- Universal "Publish Everywhere" — adapt Gold Master for TikTok/Reels/LinkedIn (9:16, platform metadata) with per-target failure isolation.
- MO-023 QRU Audio Intelligence & Licensed Sound Library™ · MO-024 Mind & Renewal University™ · MO-020 FOREX FOUNDATIONS™ Gold Standard Workbook · YouTube E2E real upload.
- Wire MO-012 produce completion + Gold Master into continuity project stage completion (auto-link).
