# QRU Factory™ — DQ-7B Canonical Standards Reconciliation Pass (READ-ONLY PROPOSAL)
**Type:** Founder-reviewable canonicalization proposal. **NO database, application, registry, or production changes made.**
**Date:** 2026-07-26 · **Governing inventory:** 39 unique standard identities. · **Scope of 7B:** the 5 IDs duplicated across `qiks_standards` and `constitutional_registry`.
**Unchanged:** the 11 evidence-backed enforcement classifications and 28 unresolved unique standards from DQ-7 remain in their existing proposal status. DQ-7B does not touch enforcement.

---

## A. Side-by-side field comparison (the 5 duplicated IDs)

**Canonical join key = `standard_id`** (qiks) ↔ `id` (constitutional). ⚠️ Identity-key inconsistency: in `qiks_standards`, `QRU-CON-0001` stores `id="QRU-CON-0001"` (code as id), while the other four store a **UUID** `id` with the code in `standard_id`. `constitutional_registry` uses the code as `id` for all five.

| ID | `qiks_standards` (CANONICAL — rich) | `constitutional_registry` (INDEX — lean) | Divergences |
|---|---|---|---|
| QRU-CON-0001 | id=QRU-CON-0001; name; status=Active; version 1.0; founder_approval=True; **authority_level=Foundational**; is_founder_document=True; classification="Foundational Governance Standard"; related_standards=[00001,00005,00003,00016]; implementation_status=**Implemented**; promotion_stage=Institutional Knowledge™; word_count; description/purpose/document_content | id=QRU-CON-0001; name; version 1.0; **owner=QRU**; category="Foundational Governance"; implementation_status=**Production**; **verification_status=Verified** | impl_status Implemented vs Production; owner+verification only in cons; authority/classification/inheritance only in qiks |
| QRU-CON-0002 | id=**UUID**; standard_id=QRU-CON-0002; name; status=Active; founder_approval=True; related_standards=[QRU-CON-0001]; related_products=[all]; description/purpose | id=QRU-CON-0002; **owner=QRU Press™**; category; impl=**Production**; **verification=Verified** | impl_status None(qiks) vs Production; owner+verification only in cons |
| STD-MFG-0001 | id=**UUID**; standard_id=STD-MFG-0001; status=Active; founder_approval=True; related_standards=[CON-0001,CON-0002]; related_products=[all] | id=STD-MFG-0001; owner=QRU; impl=Production; verification=Verified | same pattern |
| STD-EIP-0002 | id=**UUID**; standard_id=STD-EIP-0002; status=Active; founder_approval=True; related_standards=[CON-0001,CON-0002,MFG-0001,EIP-0001] | id=STD-EIP-0002; owner=QRU; impl=Production; verification=Verified | same pattern |
| STD-RFN-0001 | id=**UUID**; standard_id=STD-RFN-0001; status=Active; founder_approval=True; related_standards=[CON-0001,CON-0002,MFG-0001,EIP-0001,EIP-0002] | id=STD-RFN-0001; owner=QRU; impl=Production; verification=Verified | same pattern |

**Fields unique to `constitutional_registry` (must be preserved):** `owner`, `verification_status` (=Verified), and the constitutional framing of `implementation_status=Production`.
**Fields unique to `qiks_standards` (the richer record):** `authority_level`, `is_founder_document`, `classification`, `promotion_stage`, `related_standards` (inheritance), `founder_approval`, `word_count`, `description/purpose/document_content`, `superseded_versions`.

---

## B. Consumer / dependency map (who reads or writes each collection)

### B1. `qiks_standards` — CANONICAL (read + write authority)
| Consumer | Type | Access | Evidence |
|---|---|---|---|
| `routers/qiks.py` → `/api/qiks/standards` (GET list, GET/{sid}, POST, POST/{sid}/promote, PUT/{sid}) | API/service | **read + write** (full CRUD + promotion) | authoritative standards API |
| `qiks.py` `STD_COL = db["qiks_standards"]` | service | read+write | primary module |
| `publishing_standard.py`, `refinement_engine.py`, `enterprise_architecture.py`, `manufacturing_flow.py` (`seed_*`) | engines | write (self-register their own standard via find_one(standard_id)+insert) | each engine registers into qiks |
| Frontend `InstitutionalKnowledge.js`, `FactoryAgents.js`, `components/qru.js`, `Layout.js` | UI | read (via /api/qiks/*) | standards library UI |

### B2. `constitutional_registry` — INDEX (already projection-like)
| Consumer | Type | Access | Evidence |
|---|---|---|---|
| `manufacturing_flow.constitutional_registry()` → `routers/manufacturing_flow.py` GET | API | **read-only**, returns `{"registry":[…]}`; has a hardcoded fallback | display endpoint |
| `manufacturing_flow.seed_flow()`, `refinement_engine.py`, `enterprise_architecture.py` | engines | write via `update_one($setOnInsert, upsert=True)` — **never overwrites** | additive-only seed |
| `tests/test_iteration51_manufacturing_flow.py::test_constitutional_registry` | test | read | contract test |

### B3. Authority determination
- **`qiks_standards` IS authoritative:** it is the only store with a CRUD API, a promotion lifecycle, engine self-registration, and the richest schema (authority/classification/inheritance/founder_approval).
- **`constitutional_registry` is NOT authoritative:** additive-only (`$setOnInsert`), read via one display endpoint that even carries a hardcoded fallback, and **no manufacturing/governance logic branches on it.** It already behaves as a curated constitutional index.

---

## C. Blast radius of making `qiks_standards` canonical
**LOW and confined to one display endpoint.**
1. **Only breakable contract:** `GET routers/manufacturing_flow → constitutional_registry()` returns rows shaped `{id, name, version, owner, category, implementation_status, verification_status}`. A projection MUST keep returning those exact fields (derive `name`/`version` from the canonical record; keep `owner`/`verification_status`/`category` on the index).
2. **No product/manufacturing branch** depends on `constitutional_registry` — verified by grep (only the display fn + seeders + one test).
3. **`/api/qiks/standards`** unaffected (already canonical).
4. **UI:** the Institutional Knowledge / standards views read qiks; the constitutional list view reads the manufacturing_flow endpoint — both preserved if the projection keeps its field shape.
5. **Data loss risk:** none, provided `owner` + `verification_status` (unique to constitutional_registry) are preserved (see D).

---

## D. Proposed non-destructive transition (constitutional_registry → projection/index)
**Principle:** one canonical identity in `qiks_standards` (keyed by `standard_id`); `constitutional_registry` becomes a thin **index/projection** that *references* the canonical identity and retains only constitutional-tier signals.

**Step 1 — Preserve constitutional signals on the canonical record (additive):**
On the ≤5 canonical `qiks_standards` records, add (never overwrite) the constitutional signals currently unique to the index: `owner`, `verification_status`, and a `constitutional_rank` (e.g., "Foundational"/derived from authority_level). This guarantees no field is lost when the index slims down.

**Step 2 — Reshape `constitutional_registry` into an index (additive flags, non-destructive):**
Each of the 5 rows gains `canonical_ref := <standard_id>` and `projection := true`, and is documented as *derived from* `qiks_standards`. Existing fields (`id, name, version, owner, category, implementation_status, verification_status, created_at`) are **retained** so the display endpoint's contract is unchanged. Optionally, the display function is updated (future, code-side, separate approval) to hydrate `name`/`version` live from the canonical record — but that is NOT part of this metadata pass.

**Preserved by design:** constitutional rank (authority_level/classification/constitutional_rank), Founder approval (`founder_approval`), inheritance (`related_standards`), verification (`verification_status`), ownership (`owner`), and all historical timestamps (`created_at`). Nothing renamed or deleted.

**Identity-key note (FOUNDER_DECISION_REQUIRED):** QRU-CON-0001's `qiks_standards.id` equals its code while the other four use UUIDs. Recommendation: **standardize the join on `standard_id`** and do NOT mutate any existing `id` (changing an `id` is destructive and risks breaking references). Held for Founder ruling.

---

## E. Revised Dry-Run Manifest — based on 39 unique identities (NOT 44), NOT EXECUTED

### E1. Canonical metadata writes → `qiks_standards` (39 unique records)
- DQ-7 lifecycle/enforcement fields apply to **39 unique canonical records** (previously mis-scoped to 44). Per-record proposals unchanged from DQ-7 (`lifecycle_status=ADOPTED` ×39; enforcement: 9 INHERITED_ENFORCED + 2 GATE_ENFORCED evidence-backed + 28 FOUNDER_DECISION_REQUIRED).
- **DQ-7B additive canonical-rank preservation** on the ≤5 constitutional-tier records:
```
+ owner               := <from constitutional_registry, e.g. "QRU" / "QRU Press™">
+ verification_status := "Verified"
+ constitutional_rank := <e.g. "Foundational">   # only where evidenced by authority_level/classification
+ dq7b_canonicalized_at := <UTC>
```
- **Field-write count:** DQ-7 fields = 5 × 39 = 195; DQ-7B rank fields ≈ 4 × 5 = 20 → **≈215 writes**, all **additive**, 0 overwrite / 0 delete / 0 rename.

### E2. Projection / index updates → `constitutional_registry` (5 rows)
```
+ canonical_ref := <standard_id>     # e.g. "QRU-CON-0001"
+ projection    := true
+ dq7b_indexed_at := <UTC>
```
- **Field-write count:** 3 × 5 = **15 additive writes**; existing fields retained; **0 delete / 0 rename**. Endpoint field contract preserved.

**Separation summary:** §E1 = canonical-store metadata (qiks_standards); §E2 = projection/index tagging (constitutional_registry). The two are applied as **distinct, independently-reversible batches**.

---

## F. Rollback, Dependency Verification & Post-Change Integrity

### F1. Pre-flight (before any write)
- Snapshot both collections → `/app/memory/audit/dq7b_preimage_qiks.json` (39) and `dq7b_preimage_constitutional.json` (5), keyed by `_id`+`standard_id`/`id`.

### F2. Rollback (deterministic — additive only)
- Reverse E1: `$unset {owner?, verification_status?, constitutional_rank, dq7b_canonicalized_at, <DQ-7 fields>}` on records tagged `dq7b_canonicalized_at` / `dq7_prepared_at`. (For `owner`/`verification_status`, only unset the copies added by this pass — the pre-image distinguishes pre-existing vs added.)
- Reverse E2: `$unset {canonical_ref, projection, dq7b_indexed_at}` on `constitutional_registry`.
- Because nothing is overwritten/renamed/deleted, rollback restores the exact pre-image.

### F3. Dependency verification (post-apply, before sign-off)
1. `GET /api/qiks/standards` returns 39, unchanged field contract.
2. `GET` manufacturing_flow constitutional endpoint returns 5 rows with the SAME shape `{id,name,version,owner,category,implementation_status,verification_status}`.
3. Run `backend/tests/test_iteration51_manufacturing_flow.py::test_constitutional_registry` → pass.
4. Re-run read-only harvester `_recon_audit.py` → confirm counts and no new orphans.

### F4. Post-change integrity checks
- Every `constitutional_registry.canonical_ref` resolves to exactly one `qiks_standards.standard_id` (0 orphans, 0 duplicates).
- Unique canonical identities remain **39**; projection rows remain **5**; total distinct standard identities still **39**.
- `founder_approval`, `related_standards` (inheritance), `authority_level`/`classification`, `owner`, `verification_status`, and all `created_at` preserved on canonical records.
- No `id` value changed anywhere.

---

## G. STOP — Founder Review
No database, application, registry, or production change has been made. Decisions requested:
1. Confirm **`qiks_standards` as the single canonical standards store** (authority evidence in §B3).
2. Approve the **projection transition** for `constitutional_registry` (§D) preserving rank/approval/inheritance/verification/owner/history.
3. Rule on the **identity-key standardization** (join on `standard_id`; do not mutate `id`) — §D note.
4. Approve the **39-based dry-run manifest** (§E), split into canonical writes (E1) vs projection updates (E2).
DQ-7 enforcement proposals (11 evidence-backed + 28 unresolved) remain unchanged.
