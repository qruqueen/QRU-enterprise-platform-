# QRU UKR-Inheritance Governance Gap — Post-Launch Initiative (PLAN ONLY)

> Status: IDENTIFIED, DEFERRED to after launch (Founder instruction). No code changes during
> launch freeze. Classification: this is (2) a CURRENT governance gap, which has also produced
> (1) a migration backlog. Constitution: "Every published product traceable to exactly one
> verified Universal Knowledge Record. Verified UKR → Decoder → Manufacturing → Publishing."

## Evidence (live audit, 2026-06 — 225 products)
- Backed by a verified/approved UKR: **142**
- No `knowledge_record_id` at all: **62**
- KR id set but KR document missing (dangling): **1**
- KR exists but NOT verified/approved: **20**
- Published products: **76**, of which only **61** trace to a verified UKR
  → **15 published products are NOT traceable to a verified UKR** (constitution breach).
- Knowledge Records: 80 total, 40 verified/approved.
- Verified field: `verification_status == "Verified"` (also `approval_status == "Approved"`).

## Current pathways that BYPASS verified-UKR inheritance (code)
1. `POST /api/products/generate` with only a `topic` (no KR) → `knowledge_record_id = None`.
   (`routers/products.py` ~L288–334)
2. `POST /api/products/generate` / `POST /api/products/assemble` with a KR id → check the KR
   EXISTS but never check `verification_status` → unverified/draft KR accepted.
   (`routers/products.py` ~L225–264, L288–334)
3. `asset_manufacturing.manufacture_from_asset` → builds products from an uploaded asset with
   NO `knowledge_record_id`. (`asset_manufacturing.py` ~L234–252)

## Pathways that ALREADY enforce it (discipline exists, just uneven)
- `media_division.verified_krs` (filters `verification_status=Verified`/`approval_status=Approved`)
- `product_automation` (topic auto-resolve requires `verification_status=Verified`, L431)
- `manufacturing2` (marks assemble "failed / Source record not verified" if not Verified, L178)
- Decoder → `book_manufacturing.create_book_from_decoder` (decodes verified KRs only)

## Launch impact: NONE
The public QRU Online bookstore reads `book_records` and surfaces only Founder-authorized books
(Decoder → Book Manufacturing = verified path). The gap is in the `products` collection (Founders
Console / consumer campus), not the public storefront. Book launch is clean.

## Remediation plan (post-launch)
1. **Single enforcement choke point** — a shared guard used by every product-creation path that
   requires a verified UKR. `/generate` with no KR either (a) blocks, or (b) auto-creates a DRAFT
   UKR that must reach `verification_status=Verified` before the product can advance/publish.
   Asset-manufactured products must bind to a UKR (create/attach one on import).
2. **Publish guard** — block `status → Published` unless the product traces to exactly one verified
   UKR (enforce in the unified publishing path / Manufacturing Foundation).
3. **Migration/remediation** — remediate the 83 non-conforming products (62 no-KR + 20 unverified +
   1 dangling): bind each to a verified UKR or quarantine. Prioritize the 15 published-but-unverified
   (bind or unpublish first).
4. **Audit report** — a Founders Console view listing every product's UKR-traceability status
   (green = verified UKR, amber = unverified, red = no UKR), so compliance is visible at a glance.

## Sequencing
After launch. Relationship to other post-launch work: this Governance Gap closure and the Master
Design Standard™ program are complementary (both are "improve the standard" / Manufacturing
Foundation). Founder to set order. Do NOT start during launch freeze.
