# PILOT-MFG-0001 · Shadow-Mode Proposal — Publish-Time KR Snapshot Control for QRU Learn
Responsibility: RI-MFG-0003 (proposal only). No code/DB/product/content changes. Stop after proposal.

## 1. Current-state risk statement
QRU Learn renders the **live mutable KR** (`consumer.py:219` find_one by id → build_understanding). KR edits mutate the
single doc in place (`knowledge.py:119`). Products stamp `kr_version` at generation but it is **never enforced** at read
time, and **no approved content snapshot exists**. Consequences today (evidence from 90 published products):
- **5 published products are backed by UNVERIFIED KRs** (Topic Seed / "Needs Founder Review") — learners are being served
  unverified content right now. Direct Treasure Standard™ breach.
- Any future KR edit (even to Draft) silently changes published lessons with no review/republish gate.
- No tamper-evidence, no drift signal enforced, no rollback of learner-facing content.

## 2. Proposed schema changes (smallest extension — NO new Learning Record architecture)
- **New collection `product_publication_snapshots`** (append-only, immutable):
  `{ id, product_id, kr_id, kr_version, verification_status, verification_reference, content, content_hash (sha256),
     published_at, published_by, active: bool }`
  - `content` = the exact KR field subset `build_understanding` consumes (sections/layers/modes/memory/verification).
  - Immutable: never updated after insert. `active=True` marks the currently served snapshot; superseded ones kept `active=False`.
- **Two fields on `products`:** `active_snapshot_id` (pointer) + reuse existing `knowledge_record_id`, `kr_version`.
- Index: `product_publication_snapshots` on `{product_id, active}` and `{product_id, published_at}`.

## 3. Publish workflow changes
File `routers/products.py`, the publish branch (`status == "Published"`, ~lines 631–645):
1. **Require `kr.verification_status == "Verified"`** (in addition to existing AI-Verification + Knowledge-First trace guard).
2. Load KR → extract the `build_understanding` field subset → compute `content_hash = sha256(canonical(fields))`.
3. Insert an immutable snapshot (`active=True`); set the prior active snapshot (if any) to `active=False` (retained).
4. Set `product.active_snapshot_id`. Republish repeats this → new active snapshot, old one preserved.

## 4. Consumer read-path changes
File `routers/consumer.py`, `consumer_product()` (~lines 211–231):
- Load `product.active_snapshot_id` → `build_understanding(snapshot.content)` (build_understanding unchanged — reused on snapshot).
- **Never** read the live KR for learner content.
- If **no active snapshot** → return a governed **`AWAITING_APPROVED_SNAPSHOT`** state (understanding=null + reason), so the UI
  shows a "temporarily unavailable — awaiting verified approval" message rather than unverified content.
- Catalog/pathways/my-learning (content-excluded projections) unchanged; optionally surface snapshot presence.

## 5. Drift detection logic (read-only, off the hot path)
- For each published product compare `active_snapshot.kr_version` vs current `kr.version`.
  - `kr.version > snapshot.kr_version` → **`KNOWLEDGE_UPDATE_AVAILABLE`** (drift). Surface to Founder.
  - Learner content **does not change** on drift. Advancing requires: KR Verified → impact review → **explicit republish** (§3).
- Computed on demand in a governance/Coordinator endpoint; no live mutation, no auto-republish.

## 6. Migration classification results (READ-ONLY, executed now — 90 published products)
| Class | Count | Meaning / action |
|---|---|---|
| SAFE_FOR_SNAPSHOT_BACKFILL | **70** | product.kr_version == current kr.version AND KR Verified → safe to backfill an approved snapshot from current KR |
| DRIFT_REVIEW_REQUIRED | **0** | none currently drifted |
| UNVERIFIED_KR | **5** | KR not Verified (Topic Seed / Needs Review) — cannot snapshot; Founder decision |
| MISSING_KR_LINK | **9** | no knowledge_record_id (mostly asset types: infographic/short-form/posters/store bundles) |
| MISSING_PROVENANCE | **6** | KR linked but no kr_version stamp (early/UI-test + store bundles) |

UNVERIFIED_KR examples: PRD-00130 (Forex Interactive), PRD-00196, PRD-00201, PRD-00202, PRD-00205.
MISSING_KR_LINK examples: PRD-00089, PRD-00108, PRD-00178/180/181/182, PRD-00199, STORE-5A8B7519.
MISSING_PROVENANCE examples: PRD-00001, PRD-00002, STORE Assessment/Workbook/Instructor bundles.

## 7. Rollback approach
Snapshots are append-only + immutable. Rollback = **flip `active`** to a prior snapshot (+ update `product.active_snapshot_id`);
nothing deleted/overwritten. Mirrors the proven RI-MFG-0002 rollback pattern (pointer + retained history).

## 8. Test plan
- Determinism: `content_hash` stable for identical content; build_understanding(live) == build_understanding(snapshot) for an
  unchanged Verified KR.
- Publish: Verified KR → snapshot created (hash, version, verification ref); Unverified KR → publish blocked.
- Read: learner served snapshot; editing live KR afterward does NOT change learner content; no-snapshot → governed unavailable.
- Drift: bump kr.version → product flagged KNOWLEDGE_UPDATE_AVAILABLE; content unchanged until republish.
- Rollback: flip to prior snapshot restores exact prior content+hash; prior snapshots preserved.
- Regression: catalog/pathways/my-learning/enrollment/certificates + purchase/download unaffected.
- Backfill: 70 SAFE get snapshots; counts + hashes reconcile.

## 9. Security & performance
- Security: sha256 tamper-evidence; write-once snapshots; unverified/edited content can no longer reach learners; publish gated
  on Verified + existing guards.
- Performance: read swaps one KR find_one for one snapshot find_one (net neutral). Storage = text subset per publication (small).
  Drift detection is periodic/on-demand, not on the request path.

## 10. Estimated implementation scope — SMALL→MEDIUM
1 new collection + 2 product fields; ~1 function changed in products.py (publish) and ~1 in consumer.py (read); 1 new helper
`publication_snapshots.py`; 1 read-only drift/backfill endpoint (shadow) then a governed backfill/republish endpoint post-approval;
2 frontend touch points (consumer unavailable state + Founder drift/republish/rollback panel — can reuse the Coordinator console).

## 11. Exact files & functions that would change
- `backend/routers/products.py` → publish/`update_status` handler (~631–645): add Verified gate + snapshot creation.
- `backend/routers/consumer.py` → `consumer_product()` (211–231): serve active snapshot; `AWAITING_APPROVED_SNAPSHOT` fallback.
- NEW `backend/publication_snapshots.py`: `content_hash(kr)`, `create_snapshot(product, kr, actor)`, `serve(product)`,
  `rollback(product, snapshot_id)`, `detect_drift(product)`, `classify_backfill()`.
- `backend/routers/pilot.py` (or new governance router): read-only drift + backfill classification (shadow), later governed actions.
- `frontend/src/pages/consumer/ConsumerLearn.js` (product view): handle `AWAITING_APPROVED_SNAPSHOT`.
- `frontend/src/pages/PilotCoordinator.js` (or new page): drift / republish / rollback controls.
- DB: new `product_publication_snapshots` collection; `products.active_snapshot_id`.

## 12. Founder decisions still required
1. **5 UNVERIFIED_KR published products** — unpublish, hold in governed-unavailable, or verify-then-republish?
2. **9 MISSING_KR_LINK** — most are asset types with no "understanding". Recommend: **exempt non-lesson asset product types**
   from the snapshot rule (posters/infographics/short-form/bundles) rather than forcing a KR link. Confirm exemption list.
3. **6 MISSING_PROVENANCE** — backfill after confirming current KR Verified, or route to drift-review?
4. **Governed-unavailable UX wording** for learners when no approved snapshot exists.
5. **Backfill baseline** — accept the CURRENT KR content as the approved snapshot for the 70 SAFE (recommended, since version
   matches and KR is Verified)?
6. **Snapshot granularity** — store raw approved KR field subset + hash (recommended) vs full assembled understanding.

## Prohibitions honored
No new Learning Record architecture · no auto-republish · no live-record mutation · no product removal · no broad redesign ·
no implementation until Founder approval. STOP after proposal.
