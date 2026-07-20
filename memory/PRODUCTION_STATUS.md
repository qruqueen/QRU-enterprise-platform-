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

## REMAINING PRODUCTION BLOCKERS
1. **Phase B durable storage NOT yet in production** (built + verified in preview; prod endpoints
   return 405 = absent). Requires ONE redeploy, then the authenticated certification runbook
   (UKR status → storage-audit → deterministic recovery → re-audit → real-file JWT → 1 paid download).
   Until then, a redeploy still risks wiping current on-disk covers/EPUBs/audio (rebuilt at $0 after).

## Deferred (NOT started, per Founder "verification only" directives)
- Retire legacy `?download=1` (P0, backend) — blocked on Founder all-clear.
- Founder Operations Toolkit (governed buttons for audit/recovery/health) — recommended, not yet built.
- Publishing Intelligence Dashboard™ (P1); Master Design Standard™ Phase 3 (P1).
