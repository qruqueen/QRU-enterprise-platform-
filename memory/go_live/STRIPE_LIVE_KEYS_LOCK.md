# 🔒 STRIPE LIVE KEYS — DO NOT REVERT

**Status:** LIVE cutover in progress (2026-06).

`backend/.env` now holds **LIVE** Stripe credentials:
- `STRIPE_API_KEY` = `sk_live_...` (validated against Stripe /v1/balance → livemode:true, USD)
- `STRIPE_PUBLISHABLE_KEY` = `pk_live_...`
- `STRIPE_WEBHOOK_SECRET` = `whsec_...` (Live webhook → https://qru-online.com/api/public/webhook, event checkout.session.completed)

## CRITICAL RULES (platform-confirmed via support)
1. `backend/.env` is **shared by BOTH preview and production**. No per-env scoping.
2. Each **redeploy is a snapshot** of `.env` at deploy time.
3. **NEVER revert these to `sk_test_`/`pk_test_`** — the next redeploy would silently
   downgrade PRODUCTION to test mode and stop real payments.
4. Preview storefront is therefore ALSO in LIVE mode — do NOT make test purchases with a
   real card on the preview URL (they are real charges). Use Stripe test cards only if you
   temporarily switch back to test keys locally (and remember rule 3 before any redeploy).

## Verified
- Preview checkout endpoint returns `cs_live_...` sessions ✅ (after this change).
- Production (qru-online.com) will go Live only AFTER the user redeploys with this .env snapshot.
