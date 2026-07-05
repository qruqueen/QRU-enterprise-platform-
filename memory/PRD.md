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
MO-001 P4 Quality Gates ✅ · MO-002 P6 Enterprise Manufacturing Dashboard ✅ · MO-003 Knowledge Record 2.0 ✅ · MO-004 QRU Design Language ✅ · MO-005 Manufacturing Director™ ✅ · MO-006 True YouTube publishing (Founder Upload Mode) — NEXT. Build one at a time; deterministic infra before AI content.

## Completed (recent → older)
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
