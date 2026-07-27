# QRU Factory™ — DQ-7 Standards Enforcement Preparation Pass (READ-ONLY PROPOSAL)
**Type:** Founder-reviewable metadata proposal. **NO records modified, stamped, migrated, merged, renamed, or deleted.**
**Date:** 2026-07-26 · **Scope:** all 39 `qiks_standards` + 5 `constitutional_registry` records.
**Governance:** Values below are *proposals only*. Enforcement is **never inferred from mere existence**; anything unsupported by concrete evidence is marked `FOUNDER_DECISION_REQUIRED`.

---

## A. Corrected Reconciliation Totals
- **Capability registry = 101 unique.** The earlier "102" double-counted `production-operations`, which carries the **non-exclusive** `inherited` tag *and* sits in `registered_and_implemented`. Mutually-exclusive lifecycle buckets: 83 implemented + 9 merged + 1 deprecated + 8 future = **101** ✓. (Ledger §0 corrected.)
- **Standards count nuance:** "44" = 39 `qiks_standards` + 5 `constitutional_registry`, **but the 5 constitutional IDs are duplicated inside `qiks_standards`** → only **39 unique standard identities**. The 5 duplicates carry **divergent metadata** across the two collections (see §F, flagged `FOUNDER_DECISION_REQUIRED`).

## B. Current stored state (evidence)
- `qiks_standards` (39): every record has `status="Active"`, `founder_approval=True`. 35 have `implementation_status="Implemented"`; 4 are `None` (QRU-CON-0002, STD-EIP-0002, STD-MFG-0001, STD-RFN-0001). **No `enforced`/`enforcement` field exists on any record.** A `lifecycle` field does not exist.
- `constitutional_registry` (5): schema has `implementation_status="Production"`, `verification_status="Verified"`, `version="1.0"`, `owner`, `name`, `category`. **No lifecycle status field and no enforcement field.**
- **Conclusion:** current *lifecycle status* = only the generic `status="Active"` (qiks) / absent (constitutional); current *enforcement condition* = **none stored anywhere** (0/44).

---

## C. Proposed Controlled Vocabulary (define before assigning)

### C1. Lifecycle Status (mutually exclusive)
| Value | Meaning | Assignment evidence required |
|---|---|---|
| `ADOPTED` | Founder-approved and in force | `founder_approval=True` AND (`status=Active` or `verification=Verified`) |
| `DRAFT` | Recorded, not yet Founder-ratified | founder_approval absent/false |
| `SUPERSEDED` | Replaced by a newer standard | `supersedes`/`superseded_versions` points to a successor |
| `DEPRECATED` | Retired, no longer in force | explicit retirement note |
| `RESERVED` | Placeholder / architecture-ready, not adopted | flagged future/placeholder |
| `FOUNDER_DECISION_REQUIRED` | Status cannot be derived from evidence | default when none of the above hold |

### C2. Enforcement Condition (how/where the standard is actually enforced)
| Value | Meaning | Assignment evidence required |
|---|---|---|
| `CODE_ENFORCED` | A code control blocks violations at runtime | named module/function that rejects non-conformance |
| `GATE_ENFORCED` | Enforced at a manufacturing/quality/governance gate | named gate (inspection / readiness / governance_binding / renderer) |
| `INHERITED_ENFORCED` | Enforced transitively via a Manufacturing Promise™ pillar or a parent standard | cited pillar/parent in `capability_registry.MANUFACTURING_PROMISE` or `inherits_from` |
| `REVIEW_ENFORCED` | Enforced by a human/Founder review checkpoint | named approval record/flow |
| `ADVISORY` | Documented guidance; no automated enforcement | evidence it is a reference/methodology doc AND no control found |
| `NOT_ENFORCED` | Adopted but no enforcement mechanism exists yet | confirmed absence |
| `FOUNDER_DECISION_REQUIRED` | Enforcement class cannot be determined from evidence | **default — never inferred from existence** |

**Rule applied:** I assign an enforcement class ONLY when a concrete control or a Manufacturing Promise™ pillar is citable. All others are `FOUNDER_DECISION_REQUIRED` with a *candidate* noted for the Founder to confirm — never auto-promoted.

Manufacturing Promise™ pillars (evidence source `capability_registry.MANUFACTURING_PROMISE`): `verified_knowledge`, `constitutional_governance`, `enterprise_memory`, `treasure_standard`, `continuous_craftsmanship`.

---

## D. Proposed Lifecycle Status — summary
All 44 qualify for `ADOPTED` under C1 (evidence: `founder_approval=True` for the 39; `verification_status=Verified` + `implementation_status=Production` for the 5). **0 inferred beyond stored evidence.** No `DRAFT`/`DEPRECATED`/`SUPERSEDED` detected among these records.

## E. Complete 44-Standard Mapping

**Legend — Prop.Enf:** `INH`=INHERITED_ENFORCED, `GATE`=GATE_ENFORCED (candidate), `FDR`=FOUNDER_DECISION_REQUIRED. Current Status = stored `status`; Current Enforcement = **none** for all (no field). Proposed Status = `ADOPTED` for all (evidence per §D). Blast radius = **metadata-only, additive, single-record, reversible, no behavioral change** for every row unless noted.

### E1 — `qiks_standards` (39)
| ID | Title | Cur.Status | Prop.Enf | Evidence / candidate control | Inheritance | Uncertainty |
|---|---|---|---|---|---|---|
| STD-00001 | Treasure Standard™ | Active | **INH** | Manufacturing Promise pillar `treasure_standard` | — | — |
| STD-00005 | QRU Master Constitution™ | Active | **INH** | pillar `constitutional_governance`; parent of UKR chain | →STD-UKR-0001 | — |
| QRU-CON-0001 | QRU Factory™ Constitution | Active | **INH** | pillar `constitutional_governance`; governance/governance_binding routers | — | dup w/ constitutional_registry (§F) |
| QRU-CON-0002 | Enterprise Publishing & Presentation Standard™ | Active | **GATE** | "Publication Quality Standard™" applied in `rendering_engine`/`deliverable_renderer` | — | confirm exact render gate |
| STD-00008 | Verification Principles™ (Kingdom Lion™) | Active | **INH** | pillar `verified_knowledge`; `verification` router | — | — |
| STD-00009 | Manufacturing Recipes™ | Active | **INH** | pillar `enterprise_memory`; `inherited_products`/recipes | — | — |
| STD-00027 | Knowledge Record Master Specification™ | Active | **INH** | pillar `verified_knowledge`; KR verification gate | inherits STD-UKR-0001; impl_by STD-00030 | — |
| STD-00030 | Knowledge Record Template™ | Active | **INH** | pillar `verified_knowledge` | inherits STD-00027 | — |
| STD-UKR-0001 | Universal Knowledge Record™ (UKR™) | Active | **INH** | pillar `verified_knowledge` | inherits STD-00005; impl_by STD-00027 | — |
| STD-RFN-0001 | Enterprise Refinement Initiative™ | Active | **INH** | pillar `continuous_craftsmanship`; `refinement` router | — | impl_status None in qiks; dup (§F) |
| STD-00002 | The One Question Test™ | Active | FDR | Institutional Knowledge doc; candidate: ADVISORY | — | confirm advisory vs gate |
| STD-00003 | QRU Brand Operating System™ (QBOS) | Active | FDR | candidate GATE via `qbos` router / `brand_library` | — | confirm brand enforcement |
| STD-00004 | QRU Educational Design System™ (QEDS) | Active | FDR | candidate GATE via `qeds` router / colleges | — | confirm education enforcement |
| STD-00006 | Workforce Identity System™ / Character Bible™ | Active | FDR | candidate via `character_library`/`workforce` | — | confirm |
| STD-00007 | QRU Teaching Methodology™ (11-part) | Active | FDR | candidate ADVISORY | — | confirm |
| STD-00010 | The QRU Thinking Model™ (8-point) | Active | FDR | candidate ADVISORY | — | confirm |
| STD-00011 | Hands-Free Manufacturing™ / Automation Rules™ | Active | FDR | candidate GATE via `autonomy`/`automation` routers | — | confirm automation gate |
| STD-00012 | Multi-Format Output™ Standards | Active | FDR | candidate GATE via rendering/publishing | — | confirm |
| STD-00013 | Software Architecture™ (Modular Routers) | Active | FDR | candidate ADVISORY (architectural principle) | — | confirm |
| STD-00014 | Database Architecture™ (MongoDB) | Active | FDR | candidate ADVISORY | — | confirm |
| STD-00015 | Extend Before Expand™ | Active | FDR | candidate ADVISORY (leadership principle) | — | confirm |
| STD-00016 | QRU Design Language™ / Creative Standards™ | Active | FDR | candidate GATE via `design_director`/`design`/`design_language` | — | confirm design gate |
| STD-00017 | Agent Training Guide | Active | FDR | candidate ADVISORY | — | confirm |
| STD-00018 | Standard Registry | Active | FDR | candidate CODE via `qiks`/`registry` routers (self-referential) | — | confirm |
| STD-00019 | Defense Portfolio Protection | Active | FDR | candidate via `protection` router | — | confirm |
| STD-00020 | Methodology Manual | Active | FDR | candidate ADVISORY | — | confirm |
| STD-00021 | QRU Experience Design Architecture | Active | FDR | candidate ADVISORY | — | confirm |
| STD-00022 | Intelligence Governance Charter | Active | FDR | candidate REVIEW via governance | — | confirm |
| STD-00023 | Intelligence Growth Index | Active | FDR | candidate ADVISORY (metric) | — | confirm |
| STD-00024 | Ownership and Classification | Active | FDR | candidate ADVISORY | — | confirm |
| STD-00025 | Product Assembly Blueprint | Active | FDR | candidate GATE via manufacturing | — | confirm |
| STD-00026 | Factory Operations Blueprint | Active | FDR | candidate ADVISORY | — | confirm |
| STD-00028 | Factory Agent Governance Manual | Active | FDR | candidate REVIEW via agent governance | — | confirm |
| STD-00029 | Research Intelligence | Active | FDR | candidate via `knowledge`/research | — | confirm |
| STD-00031 | Factory Command Center Dashboard | Active | FDR | candidate ADVISORY (surface) | — | confirm |
| STD-00032 | QRU Visual Intelligence Studio | Active | FDR | candidate via `visual_studio` | — | confirm |
| STD-00033 | QRU Media Intelligence Division | Active | FDR | candidate via `media_division` | — | confirm |
| STD-EIP-0002 | Enterprise Foundation Sprint A™ | Active | FDR | initiative record; no runtime gate | — | impl_status None in qiks; dup (§F) |
| STD-MFG-0001 | Universal Manufacturing Flow Engine™ | Active | FDR | candidate GATE via `manufacturing_flow`/`director` | — | impl_status None in qiks; dup (§F) |

### E2 — `constitutional_registry` (5) — DUPLICATE IDENTITIES of qiks entries above
| ID | Title | Cur.Status | Cur.Enf | Prop.Status | Prop.Enf | Evidence | Uncertainty |
|---|---|---|---|---|---|---|---|
| QRU-CON-0001 | QRU Factory™ Constitution | *(none)* impl=Production, verify=Verified | none | ADOPTED | **INH** | pillar `constitutional_governance` | **FDR:** canonical collection? metadata diverges from qiks copy |
| QRU-CON-0002 | Enterprise Publishing & Presentation Standard™ | *(none)* Production/Verified | none | ADOPTED | **GATE** | renderer Publication Quality Standard™ | **FDR:** canonical collection? |
| STD-MFG-0001 | Universal Manufacturing Flow Engine™ | *(none)* Production/Verified | none | ADOPTED | FDR (candidate GATE) | manufacturing_flow | **FDR:** qiks copy has impl_status None vs Production here |
| STD-EIP-0002 | Enterprise Foundation Sprint A™ | *(none)* Production/Verified | none | ADOPTED | FDR | initiative | **FDR:** divergent metadata |
| STD-RFN-0001 | Enterprise Refinement Initiative™ | *(none)* Production/Verified | none | ADOPTED | **INH** (`continuous_craftsmanship`) | refinement router | **FDR:** divergent metadata |

**Evidence-backed enforcement proposed:** 11 of 44 (9 INH + 2 GATE, counting the QRU-CON duplicates once). **FOUNDER_DECISION_REQUIRED:** the remaining 28 unique standards (candidate controls noted, none auto-assigned).

---

## F. Cross-collection duplicate-identity finding (FOUNDER_DECISION_REQUIRED)
The 5 IDs {QRU-CON-0001, QRU-CON-0002, STD-MFG-0001, STD-EIP-0002, STD-RFN-0001} exist in **both** collections with **divergent metadata** (e.g., `qiks_standards.implementation_status=None` vs `constitutional_registry.implementation_status="Production"`; qiks has `status=Active`, constitutional has none). Decision needed: **which collection is canonical for constitutional-tier standards**, and how to reconcile the divergent fields. (Held — no change made.)

---

## G. Dry-Run Change Manifest (NOT EXECUTED)
Upon Founder approval, a single governed pass **would** add these **additive** fields (never overwriting existing values):

**To each `qiks_standards` record (39):**
```
+ lifecycle_status        := <approved value>          # e.g. "ADOPTED"
+ enforcement_condition   := <approved class>          # INHERITED_ENFORCED | GATE_ENFORCED | ... | FOUNDER_DECISION_REQUIRED
+ enforcement_binding     := <cited control or null>   # e.g. "MANUFACTURING_PROMISE.treasure_standard"
+ dq7_prepared_at         := <UTC timestamp>
+ dq7_evidence            := <short evidence string>
```
**To each `constitutional_registry` record (5):** same five fields.

**Manifest scope:** 44 records, 5 additive fields each = **220 field writes**, 0 deletions, 0 overwrites, 0 renames. Distribution of proposed values: `lifecycle_status=ADOPTED` ×44; `enforcement_condition`: INHERITED_ENFORCED ×9, GATE_ENFORCED ×2, FOUNDER_DECISION_REQUIRED ×33 (per-record in §E). **Nothing here has been written.**

## H. Rollback Plan
Because the pass is **purely additive**, rollback is deterministic:
1. **Pre-flight snapshot:** export the 44 records (`_id`, `id`) to `/app/memory/audit/dq7_preimage.json` immediately before any write.
2. **Reverse operation:** `$unset` the 5 DQ-7 fields on records tagged `dq7_prepared_at` (idempotent; a re-run of `$unset` is safe).
3. **Verification:** re-run the read-only harvester (`_recon_audit.py`) to confirm the 44 records match the pre-image on all non-DQ-7 fields.
4. **No collateral:** since no existing field is overwritten, renamed, or deleted, rollback cannot affect any other data or behavior.
5. **Guardrail:** the pass runs only against the connected DB (preview for rehearsal; production only if the Founder later runs it from a governed endpoint) — mirroring the Production Operations dry-run→apply→rollback discipline.

---

## I. STOP — Founder Review
No application, database, or production change has been made. Awaiting Founder decisions on:
1. Approve the controlled vocabulary (C1/C2).
2. Ratify `lifecycle_status=ADOPTED` for all 44.
3. Confirm the 11 evidence-backed enforcement assignments.
4. Rule on the 33 `FOUNDER_DECISION_REQUIRED` enforcement classes (promote candidate → class, or set ADVISORY/NOT_ENFORCED).
5. Resolve the §F canonical-collection question for the 5 duplicated constitutional IDs.
