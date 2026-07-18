# QRU Online — Refund & Customer-Support Process (DRAFT — Founder review)

> Status: DRAFT process doc. No code depends on this yet. Defines how QRU handles money-back,
> failed payments, and support so the Founder isn't answering ad-hoc questions at launch.

## 1. Product nature
Digital ebooks (EPUB), delivered instantly via a time-limited download link (72h, 5 downloads).

## 2. Refund policy (proposed)
Because delivery is instant and digital, propose one of:
- **A. Satisfaction guarantee (recommended):** Full refund within 14 days on request, no questions,
  even if downloaded. Simple, builds trust for a new premium brand. Low risk at low volume.
- **B. Conditional:** Refund only if the file is defective/undeliverable or not as described.
- **C. No refunds** (state clearly before purchase). Higher friction; not recommended at launch.

**Founder decision required:** choose A / B / C and state it on the site before taking Live payments.

## 3. How a refund is issued
1. Customer emails [support@qru-online.com] with their order reference (from receipt / success page).
2. Locate the order in **Stripe Dashboard → Payments** (search by email or session id).
3. Click **Refund** (full or partial). Stripe returns funds to the original method.
4. Optionally revoke the download link (set order status to refunded). [Future small code hook.]
5. Reply to the customer confirming.

## 4. Failed / incomplete payments
- Stripe declines are handled on Stripe's hosted checkout; the buyer stays on Stripe until success
  or cancels. On cancel/abandon they return to the book page — no order is fulfilled.
- Our `/purchase/success` page polls for up to ~24s; if payment isn't confirmed it shows a
  "couldn't confirm" state directing the customer to support. No download is granted unless paid.
- If a customer was charged but has no link: locate the paid session in Stripe, confirm, and
  (current) re-share status URL / (future) resend link.

## 5. Support intake
- **Channel:** [support@qru-online.com] (single inbox at launch).
- **Target response:** [1 business day].
- **Common cases + answers:** link expired (72h) → verify paid in Stripe, extend/reissue;
  download limit hit (5) → verify and reissue; wrong book → refund + repurchase; can't open EPUB
  → recommend a reader (Apple Books, Google Play Books, Calibre).

## 6. Records
Keep support/refund correspondence with the Stripe order reference for accounting.

---
### Founder decisions required
- [ ] Refund policy A/B/C and public wording
- [ ] Support email + who monitors it
- [ ] Response-time commitment
