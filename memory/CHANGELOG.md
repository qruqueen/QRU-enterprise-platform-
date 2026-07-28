# QRU Factory™ — CHANGELOG

## 2026-07-28 — Store Readiness: Test Product Cleanup + Batch Upgrade Assets™ + Store Health™ (testing_agent iteration_96 — 100% backend + frontend, 0 issues)
Delivered 3 of the Founder's 4 store-readiness tasks as governed, reversible operations. All run against the DB the backend is connected to (PRODUCTION when triggered on the live site) — preview & prod remain SEPARATE DBs, so the Founder runs these in production from the deployed Production Operations™ panel.
- **Test Product Cleanup (P0)** — `prod_migrations.py`: `test_products_preflight` / `test_products_cleanup(apply)` / `test_products_cleanup_rollback(apply)`. Deterministically detects internal test/placeholder products by KNOWN signatures only (`UI_TEST_PROD`, `QRU Factory Acceptance Test`, `test infographic asset`, `TEST_*`, dummy, sample product — never a bare word), classifies TEST_VISIBLE_IN_CATALOG / TEST_NOT_PUBLISHED / TEST_ALREADY_ARCHIVED / TEST_HAS_PAID_ORDER, and archives removable ones (status→Archived + `test_cleanup{prior_status}`), so they leave the /learn learner catalog. Paid-order products ALWAYS skipped. Dry-run default; fully reversible. Endpoints `/api/admin/migrations/test-products/{preflight,cleanup,cleanup/rollback}`. Verified reversible (Published 90→66→90), idempotent. Preview scan: 59 matched, 24 visible, 0 paid.
- **Batch Upgrade Assets™ (P1)** — `prod_migrations.py`: `asset_upgrade_preflight` + background `_asset_upgrade_worker(actor, force)` + `asset_upgrade_status` (job coll `asset_upgrade_jobs`, id=current). Re-renders every non-test Published catalog product cover through the HARDENED deterministic renderer (`re_engine.ensure_branded_assets(pid, allow_ai_hero_art=False)`) — guaranteed $0 AI. Founder-selected Asset Vault covers preserved (counted 'skipped'). Resumable (`force=false` skips already-upgraded via `assets_upgrade.upgraded_at`; `force=true` re-renders all). Background + status polling (mirrors products/rerender-documents pattern). Endpoints `/api/admin/migrations/assets-upgrade[/preflight|/status]`. Verified full run: 66 eligible → 65 upgraded, 1 preserved, 0 failed, complete.
- **Store Health™ (P2)** — new `store_health.py` + `routers/store_health.py` (`GET /api/store/health`, super-admin) + page `StoreHealth.js` (route `/store-health`, nav item, capability registered). Read-only, evidence-only (Treasure Standard): overall rollup (healthy/warnings/attention + 7 integrity checks), public storefront (authorized vs live vs hidden-by-missing-cover, featured), catalog hygiene (test products matched/visible — links to Cleanup), commerce config (Stripe mode LIVE/TEST, webhook secret, email provider), orders & delivery (total/paid/pending, confirmation email sent/failed, newsletter subs). Preview shows LIVE Stripe mode from the real running env.
- UI: two new cards in `ProductionOperations.js` (`test-cleanup`, `assets-upgrade`) with Preflight/DryRun/Apply/Rollback + live progress bar. Fixed a missing `RefreshCw` import that briefly tripped the page error boundary.
- REMAINING of the 4 tasks: **Audiobook Storefront (P1)** — free Ch-1 sample + purchasable full-audiobook SKU + e-book bundle. NOT started: it spends TTS credits and touches the LIVE Stripe path, so it needs Founder approval on scope (sample length, pricing/bundle, voice) before building.


## 2026-07-27b — Storefront covers tightened + fixed + full catalog sweep (all $0 except 3 storefront art regens)
- **Tighten Trading Cover:** regenerated style-matched art (1 credit via image tool) + re-composited with hardened safe-band → long title now 4 tidy lines, full subtitle, no overlap. In place; id/slug/pricing/purchases preserved.
- **Fix Factory Tag:** "Ordinary Tuesdays (Factory Ready)" → title cleaned to "Ordinary Tuesdays" + cover re-rendered with regenerated art (1 credit). Slug now `ordinary-tuesdays` (derived; old slug 404s — purchases key off UUID so unaffected). Verified via public API.
- **Product cover renderer bug fixed ($0):** `design_language._wrap` now hard-breaks over-long tokens and `_fit_title` requires every line to fit the column width (was checking line-count only → long titles overflowed the frame horizontally, e.g. the poster test). 
- **Catalog Cover Sweep ($0):** re-rendered all 90 published commerce products via `re_engine.ensure_branded_assets(allow_ai_hero_art=False)` → 89 deterministic branded covers (hardened, legible, no overflow) + 1 correctly preserved its Founder-selected Asset Vault cover. 90/90, 0 errors. (Gemini image is blocked on the current universal key, so $0 deterministic is also the only viable path for hero art right now.)
- **Delivery:** re-rendered assets are git-tracked (`rendered_assets/`) AND durable-mirrored (shared `qru-online/assets` bucket), so they travel with the Founder's re-deploy; the hardened rules deploy as code. NOTE: DB pointer changes (cover_url/title) live in the preview DB — confirm production picks these up on re-deploy or via a production migration if the live store still shows old covers.
- **Minor findings (content, not rendering — deferred):** many product titles carry a redundant "— <ProductType>" suffix + inconsistent casing (e.g. "how sleep consolidates memory — Poster"); the catalog also contains test products (UI_TEST_PROD/TEST_*).

## 2026-07-27 — Cover legibility: hardened rules + public-storefront fix (option C) + full store inventory
- **RULES ($0, done):** `design_studio.compose()` — added a vertical SAFE BAND (30%–86%), ≤4-line title auto-fit, min-readable floor (46px), 2-line subtitle cap, guaranteed byline gap, block centered in band. Long titles no longer overflow/overlap. Applies to all future/re-rendered covers.
- **Storefront scaling:** verified consistent — all storefront covers 1024×1536 (2:3), shown in 2:3 containers, thumbs 460×690 (2:3). No crop/stretch.
- **Reconciliation of prior batch:** the 2026-07-25 `pilot_coordinator.batch_rerender` (RI-MFG-0002) re-rendered EPUBs only and REUSED the composited cover PNGs untouched ("Never touches cover art"); ran in PREVIEW only, never deployed. => zero covers were ever re-composited, in either env. No clean/textless art layer is stored for any book (pipeline saves only the flattened cover), so re-compositing needs AI art regen.
- **Public storefront fix (Founder option C, this session):**
  - *Patterns of Intelligence* — AI-regenerated the "Emergent Lattice" artwork (1 image credit via OpenAI gpt-image; Gemini image models are NOT allowed on the current universal key — key error: "key can only access models=[gpt-*...]"), re-composited with corrected title (no more "FINAL") + hardened rules, replaced the selected cover IN PLACE. Preserved id/slug/pricing/purchases/epub/authorization. Verified full-size + 460px thumb + public API (slug `patterns-of-intelligence`, cover-thumb 200).
  - *The Understanding Tree* — re-inspected at thumbnail: title/subtitle/byline legible over the painted artwork; NOT a real defect (earlier "legacy" flag was a proxy). Left untouched to avoid degrading artwork (AI not approved for it).
  - Verified all 8 storefront books: readable thumbnail type, no overlap/crop, correct titles/bylines/selected assets.
- **⚠️ Finding (out of today's scope):** "Ordinary Tuesdays (Factory Ready)" has an internal tag "(Factory Ready)" leaked into the customer-facing TITLE (same defect class as Patterns' "FINAL"). Flagged for a separate decision (title correction changes slug).
- **QRU STORE INVENTORY (98 customer-facing covers): PASS 15 / FAIL 83** (no-cover 9, legacy/outdated 73, other-defect 1). $0-repairable 74, AI-required 9.
  - DEFERRED post-launch maintenance (Founder directive — do NOT run today): the 90-product authenticated commerce catalog batch → 74 zero-cost deterministic re-renders + 9 AI-regeneration covers (need image-credit approval + note: universal key currently blocks Gemini image; OpenAI gpt-image works).
- **NOTE for future AI image work:** universal key blocks `gemini-*-image-preview` ("key not allowed to access model"); use OpenAI `gpt-image-1` path (or the image tool) instead, or Founder tops up / enables Gemini access.


## 2026-07-25e — RI-MFG-0002b production migration package (REVIEW ONLY, not executed)
- Confirmed via support_agent: preview & production are SEPARATE MongoDB DBs; Deploy ships CODE only, not DATA;
  preview cannot write to production. Root cause of "4 of 8 books live": the 4 newer books exist only in preview
  (prod direct-id fetch = 404). Domain/DNS healthy (Cloudflare, valid cert, www→root); not a cache/CDN/DNS issue.
- Built /app/migration_packages/RI-MFG-0002b/ : migrate_production.py (idempotent, dry-run default, Stage1 create 4
  books + Stage2 EPUB pointer cutover for 8, asset-existence prereq checks, rollback), data_stage1_books.json,
  data_stage2_pointers.json, MANIFEST.md. Dry-run evidence: preview re-run = all SKIP (idempotent); empty DB =
  WOULD CREATE x4 assets-verified. NOT executed against production (no prod write authority).
- Built /app/migration_packages/WORKSTREAM_C_containment/verify_and_hold_c.py : read-only classifier for the 5
  unverified products + conditional governed hold (PRODUCTION_HOLD_REQUIRED only) + rollback. C cannot be scoped
  from preview (prod consumer endpoints auth-gated, no prod DB access) → Support must run the verifier in production.
- Workstream B: pilot unchanged; future RI reports to add execution/database environment, production applicability,
  production data dependency, required deployment/migration path.


## 2026-07-25d — RI-MFG-0002 governed batch re-render (executed in preview, NOT deployed)
- pilot_coordinator.py: `batch_rerender()` acts ONLY on the 8 authorized book codes. Reuses existing cover art
  (zero AI, zero spend); re-renders EPUB via deterministic `deliverable_renderer._render_epub`; rollback-copies
  old EPUB/cover/interior to /rendered_assets/rollback/RI-MFG-0002 + snapshots old record to `pilot_rollbacks`;
  validates each EPUB (opens, mimetype, container, opf, nav, content); guards pricing/source/KR/cover unchanged;
  updates only artifacts.design.ebook.epub pointer + stamps rerender_provenance.
- routers/pilot.py: POST /api/pilot/mfg-coordinator/batch-rerender, GET /post-render-report (super-admin).
- Frontend PilotCoordinator.js: RI-MFG-0002 panel (run button + summary, per-book table, 5 metrics, deploy rec).
- Result: 8/8 rendered, validated, rollback-protected, guards passed; metrics 100% classification accuracy,
  0 founder touches, 0 missing-context; deploy recommendation = RECOMMEND DEPLOY (awaiting Founder approval).
- STOP condition honored — nothing published/deployed. Fixed a false-negative guard (purchase count folded into bool).
- Also answered QRU Learn evidence questions (Consumer Learning Platform): powered by products + knowledge_records
  (+ consumer_enrollments/certificates); learning content composed live from linked KR; refresh = product status→Published.


## 2026-07-25c — PILOT-MFG-0001 Manufacturing Operations Coordinator™ (Shadow Mode, read-only)
- New governed digital role (observe/evaluate only; cannot modify/publish/delete/spend/override). Deterministic ($0 AI).
- Backend: `pilot_coordinator.py` (charter + RI-MFG-0001 store re-render readiness evaluator) + `routers/pilot.py`
  (`GET /api/pilot/mfg-coordinator` charter, `GET .../readiness-report` read-only, `POST .../readiness-report/run`
  files to the pilot's own `pilot_reports` evidence journal — no Factory records touched). Registered in server.py + nav.
- Frontend: `pages/PilotCoordinator.js` + route `/pilot-coordinator` — charter (may / may-not), summary counts,
  per-book classification with evidence chips, recommended route, governance note.
- First report: 8 store books reviewed → 8 READY_FOR_BATCH_RERENDER, 0 CORRECTION, 0 FOUNDER_DECISION.
  Advisories: none link a Knowledge Record (Founder-manuscript exception), no print-wrap despite paperback list
  prices, several missing explicit ebook price (list-price fallback). Verified via curl (auth-gated 401); compiles clean.
- STOP after report per directive; await Founder approval before any batch re-render.


## 2026-07-25b — QRU Online Orders console + one-tap Resend (preview, ready to deploy)
- Backend: `GET /api/public/orders` (super-admin) lists storefront orders with fulfillment + email status;
  reuses existing `POST /api/public/orders/{sid}/resend-confirmation` (mints fresh token, no charge).
- Registered capability `qru-online-orders` (distribution layer) → appears in Founder nav.
- Frontend: `pages/QRUOnlineOrders.js` + route `/qru-online-orders` — orders table with payment/email-status
  badges, provider-connected indicator, and a per-paid-order **Resend** button.
- Resend now sends REAL emails (domain qru-online.com verified; sender receipts@qru-online.com). Verified:
  endpoint 401 unauth / 200 super-admin; list returns 26 orders/4 paid; resend on an order with a customer
  email → `sent-to-provider` (msg id captured). Frontend compiles clean. Demo test order cleaned up.
- Stripe "Successful payments" receipt = Dashboard-only toggle (cannot be set via API) → Founder action.
- Added client-side **search** (email / title / order ref) + **status filter** (all/paid/pending) to the Orders console. deployment_agent scan = PASS (no hardcoded secrets, env handling correct, ready to deploy).


## 2026-07-25 — QRU Purchase Confirmation + Secure Tokenized Delivery (Stage A+B, awaiting Founder review before deploy)

**Investigation (read-only) that led here:** queried the LIVE Stripe account directly. 3 completed live
purchases (all "The Heart as a Daily Circulation Pump", $4.99, same buyer minders.powers11@icloud.com).
`receipt_email` is null on every PI/charge (app never set it; emergentintegrations `CheckoutSessionRequest`
has no such field). Only the July 20 charge has a `receipt_number` (1100-1236) → the single Stripe receipt
came from the account-level "Successful payments" toggle, most likely active only around that date (timeline
evidence, not proof). Also found: preview process exports `STRIPE_API_KEY=sk_test_emergent` which OVERRIDES
the `sk_live_…` in `.env` (load_dotenv doesn't override) → preview runs TEST mode; production uses live.

**Stage A/B implementation (test-mode only, NOT deployed):**
- New `order_access.py` — signed, expiring JWT (typ=ord) bound to a random `access_id` + `book_id`, action=download,
  72h TTL. Customer URL never exposes the Stripe session id or file path.
- New `qru_email.py` — Resend provider abstraction (async, key from env only, NEVER logged) + QRU-branded HTML
  template (payment-success, product, amount, date, purchase ref, secure link, expiry, download cap, recovery,
  support, "separate Stripe receipt may also be sent"). Missing key → status `skipped` (order still fulfilled).
  Provider "accepted" recorded as `sent-to-provider` (NOT claimed as delivered).
- `routers/public_commerce.py` — on the FIRST atomic transition to paid (`_fulfill` modified_count==1) sends ONE
  confirmation via `_fulfill_and_notify` (shared by webhook + status poll); assigns `access_id` + `order_ref`
  (QRU-XXXXXXXX); captures `customer_email` from Stripe. New order fields: `customer_email`, `order_ref`,
  `access_id`, `confirmation_email{status, provider, provider_message_id, attempted_at, attempts, error}`.
  New endpoints: `GET /api/public/order/{token}` (metadata), `GET /api/public/order/{token}/download` (secure EPUB),
  `POST /api/public/orders/{session_id}/resend-confirmation` (super-admin; mints fresh token, no Stripe/charge).
  Legacy `/download/{session_id}` kept working (success page).
- Frontend `pages/public/QRUAccess.js` + route `/access/:token` — verifies token, shows title/ref/downloads-left/
  expiry + Download; expired→410 / invalid→403 states show recovery + support contact.
- `.env`: added non-secret `SENDER_EMAIL`, `SUPPORT_EMAIL`. `RESEND_API_KEY` intentionally NOT added (Founder).
- `requirements.txt`: `resend==2.34.0`.
- **VERIFIED (no live charge):** 24/24 in-process checks (send-once, replay idempotency, correct product, email
  failure preserves order, resend increments attempts, token valid/tampered/expired, token has no session id,
  unpaid blocked) + HTTP: metadata 200, token download 200 (epub 2.28MB), invalid 403, expired 410, cap 410,
  legacy download 200, resend 401 unauth / 200 super-admin (skipped, no key) / 404 missing order. All test
  artifacts + test order removed.
- **PENDING Founder actions (Stage C):** approve Resend + provide `RESEND_API_KEY`; verify qru-online.com sending
  domain (SPF/DKIM); confirm Stripe "Successful payments" toggle; then Deploy. NOT deployed; no live purchase run.


## 2026-06 — QRU Online™ public presentation layer (Iteration 1)

**Architecture decision:** Option A — one deployment, one domain, one source of truth.
The Factory stays private behind auth; QRU Online is the public presentation layer at the
domain root for unauthenticated visitors. After Founder login, the same root transitions to
the Factory. No duplication, no parallel data stores.

**Backend** (`/app/backend/routers/public_site.py`, mounted in `server.py`):
- New read-only, no-auth public API: `GET /api/public/home`, `/api/public/books`, `/api/public/books/{id}`.
- Single published gate: `book_records.founder_authorization.authorized == True`.
- `_public_book()` projects an explicit allow-list of public-safe fields only (title, subtitle,
  author, genre, imprint, audience, cover_url, price, description, edition, language, publisher).
  No Factory internals (provenance, manifests, working_copy, states) can leak.
- Book detail returns 404 with plain `{detail}` for unpublished/missing ids (no existence leak).

**Frontend** (`/app/frontend/src/pages/public/`):
- `PublicLayout.js` (glass sticky header + dark Treasure Standard footer), `QRUHome.js`,
  `QRUCatalog.js`, `QRUBookPage.js`, `publicApi.js` (token-free axios instance).
- `App.js` `ModeRouter`: unauthenticated → `PublicRoutes` (was: forced `/login`). PublicRoutes
  catch-all redirects any Factory URL to public Home while logged out — enforces the private
  boundary at the router layer.
- Distinct public brand per design_guidelines.json: Cormorant Garamond headings + Manrope body,
  Bone White / Ink Black / Treasure Gold palette, paper-grain background.

**Scope (iteration 1):** Home + Books Catalog + individual Book pages. Display/preview only —
no checkout. 4 authorized books live.

**Testing:** iteration_80.json — 13/13 backend pytest pass; all frontend acceptance criteria
pass including the security guarantee (Factory routes/APIs unreachable while logged out) and
public-API field isolation. Regression test: `/app/backend/tests/test_qru_online_public.py`.

## 2026-06 — QRU Online bookstore: covers + one end-to-end purchase (Iteration 2)

**Master Asset Principle™ (new standard):** one canonical cover → auto-derived web thumbnail.
- `/api/public/books/{id}/cover-thumb` derives a cached ~50 KB JPEG (460px) from the canonical
  print cover (Pillow), generated once. Catalog, home, and book-detail grids use `thumb_url`;
  no second asset is hand-maintained. Fixed the blank/slow-cover bottleneck (1.5–2.2 MB → ~50 KB).

**Homepage finished:** split-layout hero (crisp text on solid bone + QRU-owned `/qru-hero.png`),
copy sharpened to pass the Founder's 10-second test (what is QRU / what can I buy / where to click).
Copy: "Every title is carefully researched, thoughtfully written, and verified to the QRU Treasure Standard™."

**Purchase flow (mission — one complete customer purchase):** `/app/backend/routers/public_commerce.py`
- POST `/api/public/checkout` — Stripe Checkout (emergentintegrations, Founder's own TEST keys in
  `STRIPE_API_KEY`). Price resolved SERVER-SIDE (`ebook_price` → `list_price`); client cannot set amount.
- GET `/api/public/checkout/status/{sid}` — polls Stripe, idempotently flips DB to paid.
- GET `/api/public/download/{sid}` — releases the authorized EPUB ONLY when paid (else 403).
- Frontend: `QRUBookPage` "Buy the ebook" → Stripe hosted checkout; `QRUPurchaseSuccess` polls then
  shows Download EPUB. Guest checkout, no login.

**Verified (iteration_81.json):** 16/16 backend pytest; full E2E with real Stripe test card
(4242…) → paid → EPUB delivered (2.28 MB, application/epub+zip); unpaid = 403; price tamper-proof;
Mobile (390) + Tablet (820) pass. Regression: `/app/backend/tests/test_qru_public_commerce.py`.

**Learnings:** hot-reload does NOT reliably regenerate Tailwind CSS / bundle for new files —
`sudo supervisorctl restart frontend` is required after adding new pages or big class sets.
Framer-motion entrance opacity animations rendered unreliably here; public pages use static render.

## 2026-06 — QRU Go Live Security Review™ (code-side hardening, Stripe stays TEST)

**All four code-side items closed + verified (iteration_82.json — 33/33 backend pytest, full E2E, no regressions):**

1. **Secrets / git history** — `.env` patterns added to `.gitignore` (`.env`, `**/.env`, `**/.env.*`).
   Confirmed `backend/.env` was NEVER committed and the secret key never appears in any commit,
   the JS bundle, public API responses, or logs.
2. **Stripe webhook** — `POST /api/public/webhook` (namespaced to avoid collision with commerce.py's
   legacy `/api/webhook/stripe`). Signature verification via `StripeCheckout.handle_webhook` when
   `STRIPE_WEBHOOK_SECRET` is set; idempotent fulfillment via `processed_webhook_events` (dedup on
   `event_id`) + `_grant_fulfillment` guarded by `{payment_status:{$ne:'paid'}}`. Fail-closed: refuses
   unsigned webhooks under `sk_live` keys (503). Malformed → 400.
3. **Secure downloads** — `/api/public/download/{sid}` uses atomic `find_one_and_update` reserving a
   slot: requires paid + within 72h (`download_expires_at`) + `download_count < 5`. 200 within policy,
   410 on expiry/limit, 403 on unpaid/unknown. Raw EPUB path/URL never exposed (streamed via
   FileResponse; public book JSON omits `epub`/`artifacts`/`working_copy`).
4. **Privacy page** — `/privacy` (public route + footer link): what QRU collects, Stripe processing,
   why, 72h/5-download retention, support/deletion contact (`privacy@qru-online.com` placeholder).

**Draft docs (NOT published, Founder review) in `/app/memory/go_live/`:**
`PRIVACY_POLICY_DRAFT.md`, `REFUND_AND_SUPPORT_PROCESS_DRAFT.md`, `BACKUP_AND_RECOVERY_RUNBOOK_DRAFT.md`.

**Stripe remains in TEST mode. No domain, no Live keys, no email collection, no public deploy.**

**Deploy gate reminders (before Live):** set `STRIPE_WEBHOOK_SECRET`, register the Stripe Dashboard
webhook endpoint to `/api/public/webhook`, swap to Live keys, confirm `privacy@qru-online.com`.
Founder/ops items still open: 2FA on all accounts, DB backups, refund policy choice, one Founder
Live test purchase before promotion.

**Backlog (advisory, non-blocking):** Pydantic `PublicBookOut` model to hard-whitelist public book
fields (currently an explicit dict allow-list); "I paid — check again" button on success page.

## 2026-06 — Refund policy wording (Founder decision: Option A)

Added the **14-day satisfaction guarantee** wording at point-of-purchase (book page, under the Buy
button — data-testid `refund-guarantee`) and on the purchase success page (data-testid
`refund-guarantee-success`). No refund automation built (handled via Stripe Dashboard per the
draft process doc). Support/privacy email still placeholder `privacy@qru-online.com` pending the
Founder's final production address. Live cutover NOT started — operational checklist in progress.
