# QRU Production Operational Status (qru-online.com)

_Live bookstore on real Stripe. Verified processing real purchases (2 payments / $9.98 gross)._

## Post-sale investigation — CLOSED items (2026-07-20)
- ✅ **RESOLVED — EPUB validity.** The storefront EPUB is spec-conformant OCF (mimetype-first +
  STORED, META-INF/container.xml, content.opf, toc.ncx + nav.xhtml, zip integrity OK, ebooklib
  round-trip reads title + embedded cover). NOT corrupted. The "opened in MS Word on Windows"
  symptom = Windows file-association issue (no native EPUB reader), not a QRU defect. No code change.
- ✅ **RESOLVED — "Customers: 0" in Stripe.** Expected. Checkout runs `mode='payment'` guest checkout
  via the emergentintegrations wrapper (no `customer`/`customer_creation`), so Payments + Gross Sales
  record correctly without Customer objects. Not a failure. No code change.

## OPEN OPERATIONAL ITEM (not a proven code issue)
- ⏳ **Automatic Stripe receipt not sent for today's purchase (Jul 18 one was).**
  MOST LIKELY CAUSE (pending Stripe **web dashboard** verification): the Live-mode "Successful
  payments" email-receipt toggle is OFF/changed (Dashboard → Settings → Customer emails). QRU code
  never sends `receipt_email` (wrapper has no such field) and did NOT change between Jul 18 and today,
  so the variable is Stripe-side. **DO NOT make code/deploy/Stripe-API changes until dashboard evidence
  shows a code issue.** Action = Founder verifies the Live-mode receipt setting in the Stripe web UI.

## ✅ PHASE B CERTIFIED IN PRODUCTION (2026-07-21)
Re-published successfully (2nd attempt; 1st failed on a transient K8s readiness timeout — retry fixed).
Authenticated certification with Founder token, all green:
- Deploy: storage endpoints 405→401 (live/gated); storefront home+books 200.
- UKR migration: 80/80 migrated, 0 pending, backward-compatible.
- Storage audit (before): 225 products/11 books, 639 referenced · 635 local · 0 object · 4 missing
  (1 deterministic + 2 poster/media "other"; 0 AI-art, 0 audio, 0 book). NOTE: redeploy did NOT wipe
  disk — prior rendered assets are git-committed + baked into the image, so they persist. Phase B now
  protects RUNTIME-generated files (not git-committed) going forward.
- Deterministic recovery: 94 docs, 0 recovered / 94 skipped / 0 failed, $0 AI, 0 approval items.
- Re-audit (after): identical (4 missing) — idempotent, no dupes, no regression.
- JWT deliverable: tokened preview 200, no-token 403, bogus-token 403.
- Paid download (Step 9): FOUNDER-VERIFIED via today's real $4.99 purchase (EPUB delivered); all paid
  EPUBs present (book_epub 7/7, deliverable_epub 32/32). Programmatic re-check pending a cs_ session id.
- OPTIONAL FINISH: run `POST /api/rendering/storage-backfill` in prod to push the 635 current on-disk
  files into object storage (so durability no longer relies on git-committed assets). Not yet run.

## REMAINING PRODUCTION BLOCKERS
None. Phase B durable storage is live and certified.

## Deferred (NOT started, per Founder "verification only" directives)
- Retire legacy `?download=1` (P0, backend) — blocked on Founder all-clear.
- Founder Operations Toolkit (governed buttons for audit/recovery/health) — recommended, not yet built.
- Publishing Intelligence Dashboard™ (P1); Master Design Standard™ Phase 3 (P1).
