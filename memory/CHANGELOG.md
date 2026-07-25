# QRU Factory™ — CHANGELOG

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
