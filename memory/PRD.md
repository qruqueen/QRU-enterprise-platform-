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

## Completed (recent → older)
### MO-045 — Founder Beta Stabilization & Evidence Completion (2026-07-05) · VERIFIED (testing_agent iteration_25, 18/18 backend, 100% frontend)
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

## Known Limitations (as of MO-045)
- Stripe TEST mode only — no live payments; email delivery not wired (downloads shown in-app).
- External connectors (YouTube/KDP/Etsy/etc.) are honest "Needs Authorization / Setup Required" — not operational.
- `analytics.py` still emits a synthetic `knowledge_growth` trend chart (Analytics page only, not a headline metric). Flag/replace for full Treasure Standard™ if desired.
- LLM text/image generation CAPPED — deterministic $0 fallbacks in use.

## Backlog / Next Milestones (P-ordered, awaiting Founder direction)
- P1: Reach Founder Beta Complete™ (25 consecutive clean manufacturing runs).
- P2: Customer Purchase History / Library (re-download past purchases).
- P2: Replace synthetic `knowledge_growth` trend with real time-series or SIMULATED label.
- Pre-Production: add live Stripe keys + email delivery for public launch.

## Credentials
- Founder: `22j2rsdzb8@privaterelay.appleid.com` / `QruFounder2026!`
