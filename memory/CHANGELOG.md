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

**Deferred / notes:**
- Hero image is a decorative Unsplash asset (not a QRU-owned/authorized asset) — pending a
  QRU Press™-owned hero.
- Book covers are large PNGs (1.5–2.2MB) — a thumbnail/optimized-cover path is a future perf win.
- Not yet built (future iterations): Courses/University, Products catalog, storefront/checkout,
  custom domain (qru-online.com) at deploy time.
