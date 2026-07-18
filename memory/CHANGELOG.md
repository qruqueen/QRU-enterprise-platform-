# QRU Factory™ — CHANGELOG

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

**Backlog (non-blocking, from review):** manual "I paid — check again" button on success page;
`Intl.NumberFormat` for non-USD currency; publicApi retry/backoff. Domain `qru-online.com` pointing
is a deploy-time action. Next scope (Founder-gated): complete the bookstore, then Courses/University.
