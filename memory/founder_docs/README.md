# QRU Factory™ Founder Operator's Manual v1.0 — location & scope

Delivered as a permanent, print-friendly in-app page so the Founder can open and print it from inside the Factory.

- **Page:** `/founder-manual` (nav item "Operator's Manual™", Founder/Admin only). Print/Save-PDF button included.
- **Content source of truth:** `/app/frontend/src/data/founderManual.js` — grounded in the live Capability Registry™ (`/app/backend/capability_registry.py`). Business language, documents the Factory as it exists today.

## Three deliverables (tabs on the page)
1. **Operator's Manual** — full 18-field detail for the ~17 core launch capabilities (purpose, why, inputs/outputs, records created/modified/consumed, predecessor/successor, Founder-required, auto/manual, use cases, example, common misunderstanding, status) + a by-department catalog of every other implemented capability.
2. **Quick Start** — 11 "I have X, what next?" workflows (manuscript, import, KR, book, product family, cover, publish, update, remove/relist, deliver to customer, clean/upgrade live store) with start → decision → next → output → done.
3. **Relationship Map** — 6 lanes (Knowledge → Understanding/Manufacturing → Assessment → Publishing/Catalog → Customer-facing Delivery → always-on Governance/Memory/Health), each node showing In / Out / Next.

## QRU Store™ vs qru-online.com (confirmed)
QRU Factory™ → QRU Store™ (internal publishing/catalog capability) → qru-online.com (customer website) → Customer.
Honest nuance documented: today the customer site's "is it live?" gate reads a book's Founder-authorization flag directly, so authorizing/publishing lists it in QRU Store™ AND shows it on qru-online.com together (not two separate manual steps).

## Observations (documented gaps, NOT a redesign)
Merged/duplicate capabilities, Future-Backlog items, preview-vs-production DB separation, and the not-yet-built Audiobook Storefront are noted on the page under "Observations".
