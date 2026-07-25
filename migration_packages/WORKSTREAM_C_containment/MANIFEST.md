WORKSTREAM C — QRU LEARN GOVERNANCE CONTAINMENT (SEPARATE from A/B)
# Read-Only Production Verification + Conditional Governed Hold — REVIEW PACKAGE
Status: PREPARED FOR REVIEW. NOT EXECUTED. Preview has NO production write authority.
Execution path: authorized production-data path (Emergent Support). Verification is READ-ONLY.

## Package files
- `verify_and_hold_c.py` — read-only classifier (default) + conditional governed hold (`--apply-hold`) + rollback.
- `MANIFEST.md` — this document.

## Target record IDs (product_code)
PRD-00130, PRD-00196, PRD-00201, PRD-00202, PRD-00205

## Why production verification is required first
These 5 products were classified in PREVIEW as PRODUCTION_HOLD_REQUIRED (Published + linked Knowledge Record
NOT Verified). Production is a SEPARATE database and its consumer endpoints are auth-gated, so the building
agent could NOT confirm their production state. Support must run the read-only classifier IN PRODUCTION first.

## Collections
- `products` (read; write only on `--apply-hold` for qualifying records)
- `knowledge_records` (read only — verification_status)

## Classification (per product)
- PRODUCTION_HOLD_REQUIRED  — product exists, status Published (learner-accessible), linked KR NOT Verified
- NOT_PRESENT_IN_PRODUCTION — product_code absent in production
- NOT_LEARNER_ACCESSIBLE    — exists but not Published
- FOUNDER_REVIEW_REQUIRED   — published + verified, or published with missing/unlinked KR (not a containment target)

Only PRODUCTION_HOLD_REQUIRED records may be held.

## Governed hold behavior (containment only — NOT the snapshot architecture)
On `--apply-hold --apply`, for PRODUCTION_HOLD_REQUIRED only:
- set `products.status = "On Hold (Governance)"` (removes it from the learner catalog, which serves status=="Published")
- save `products.status_before_hold` (prior status, for rollback)
- write `products.governance_hold = {reason, by, at, unavailable_message}`
- PRESERVE product record, all assets, purchase history, and provenance. Nothing deleted or overwritten.

## Dry-run / rollback instructions (run in production by Support)
1. Verify (read-only, default):   `python verify_and_hold_c.py`
   → prints the classification table; take the list of PRODUCTION_HOLD_REQUIRED ids.
2. Dry-run hold:                  `python verify_and_hold_c.py --apply-hold`      (no --apply = no writes)
3. Apply hold:                    `python verify_and_hold_c.py --apply-hold --apply`
4. Rollback hold:                 `python verify_and_hold_c.py --rollback-hold --apply`

## Validation after hold
- Held products no longer appear in `/api/consumer/catalog`.
- Product, assets, and any `book_purchases`/entitlements remain intact.
- `governance_hold` present with reason; `status_before_hold` recorded.

## Prohibitions honored
No deletion/overwrite of content · no snapshot-system implementation · no republish · hold acts only on
confirmed PRODUCTION_HOLD_REQUIRED records · read-only by default.

## Preview reference classification (NOT production truth)
All 5 classified PRODUCTION_HOLD_REQUIRED in preview (KR states: Topic Seed / "Extracted — Needs Founder Review").
Production classification is expected to differ (likely NOT_PRESENT_IN_PRODUCTION) and must be established by
running this verifier in production.
