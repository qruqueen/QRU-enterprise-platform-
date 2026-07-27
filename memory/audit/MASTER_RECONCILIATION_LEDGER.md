# QRU Factory™ — Master Reconciliation Ledger
**Type:** Formal, READ-ONLY registry reconciliation
**Environment audited:** Preview (dev) database + full codebase. NOTE: Production (qru-online.com) uses a physically separate database and was NOT accessible; production-only divergences are flagged as `unresolved (prod-scope)`.
**Last validation date:** 2026-07-26
**Method:** Programmatic cross-reference (`/app/backend/_recon_audit.py`, read-only) of the live `capability_registry` collection, all backend routers, `App.js` routes/pages, and every governance/standards/agent/recipe/PMS/PMF collection.
**Governance rule honored:** Nothing was altered, merged, deleted, renamed, or created in any QRU record or collection during this audit. All corrections are deferred to the Founder Decision Queue.

---

## 0. Reconciliation Totals

**Arithmetic correction (2026-07-26):** an earlier draft summed lifecycle categories to 102 against a 101-entry registry. Root cause: `inherited` is a **non-exclusive tag**, not a separate lifecycle bucket — `production-operations` was counted once in `registered_and_implemented` **and** again in `inherited`. Corrected mutually-exclusive lifecycle total = **83 + 9 + 1 + 8 = 101** ✓. `inherited (1)` is a sub-tag *within* the 83 implemented.

| Classification (mutually exclusive) | Count | Domain |
|---|---|---|
| Registered **and** implemented | 83 | Capabilities |
| Superseded / **merged** | 9 | Capabilities |
| **Retired** / deprecated | 1 | Capabilities |
| **Reserved** (future backlog) | 8 | Capabilities |
| **TOTAL (unique registry entries)** | **101** | ✓ matches collection |
| *Non-exclusive tag:* **inherited** | 1 | (production-operations, within the 83) |
| Registered, owner file missing | **0** | Capabilities |
| Registered, route without UI page | **0** | Capabilities |
| Implemented, **not registered** (by design — public surface) | 21 routes | UI |
| **Proposed** (awaiting build approval) | 1 | Governance proposals |
| **Superseded** (replaced by newer capability) | 2 | Migration packages |
| **Unresolved** (needs Founder confirmation) | see Decision Queue | Multiple |

**Integrity headline:** every one of the 101 registry entries resolves to a real owner file and (where it declares a route) a real UI page. No orphaned or phantom capabilities. No route→undefined-component defects remain (the earlier login-crash class is clean; the 3 "wrapper" hits — `ProtectedRoute`, `ModeRouter` — are layout components defined in `App.js`, not pages, and are correct).

---

## 1. Capabilities (spine of the registry)
**Source of truth:** `capability_registry` collection (101 live) ← seeded by `capability_registry.py`. Founder status edits preserved via `$setOnInsert`.

### 1a. Registered & Implemented (83) — status: OK
All 83 have a verified owner module and, where applicable, a mounted UI route. Representative (full list in `_recon_audit.py` output): knowledge-records, kr2, verification, refinement, flow, orchestrator, director, manufacturing, publishing, products, colleges, inspection, store, youtube, distribution, governance, trust, autonomy, command-center, book-mfg, decoder-engine, qru-online-orders, pilot-coordinator, production-operations, …
- **Enforcement status:** live (routers mounted, pages routed).
- **Test evidence:** login→dashboard render verified 2026-07-25; Production Operations endpoints + lineage engine unit-validated (`backend/tests/test_conflict_resolution.py`).
- **Recommended resolution:** none — steady state.

### 1b. Superseded / Merged (9) — status: SUPERSEDED
`manufacturing-studio, mfg-command, product-library, creative-studio, visual-studio, media-starter-kit, command, enterprise-health, blueprint`
- **Evidence:** `status="merged"` in registry; owner files still present (shared with the surviving capability).
- **Recommended resolution:** Founder confirm permanent merge → keep as historical alias (recommended) or formally retire routes. See Decision Queue #3.

### 1c. Retired / Deprecated (1) — status: RETIRED
`experience-lab` (owner `routers/enterprise.py`)
- **Recommended resolution:** confirm retirement; hide from all navigation. Decision Queue #4.

### 1d. Reserved / Future (8) — status: RESERVED
`feature-film, streaming, interactive-learning, trending-topics, multi-language, ai-tutor, documentary, cinema-studio-future`
- **Evidence:** `status="future"`; architecture-ready, not built.
- **Recommended resolution:** Founder confirm each remains on roadmap vs retire. Decision Queue #5.

### 1e. Inherited (1) — status: INHERITED
`production-operations` (Production Operations™, `inherited_from=RI-MFG-0002b`, moat=True, owner `routers/migrations.py`, route `/production-operations`)
- **Test evidence:** dry-run/apply/rollback + lineage engine validated in preview 2026-07-25/26.
- **Enforcement:** Founder/Admin-only (`require_super_admin`, verified 403/401).

### 1f. Duplicate / overlap signals (flag only)
- **Duplicate route:** `/cinema-studio` shared by `cinema-studio` + `podcast-studio` (Podcast Studio piggybacks on the Cinema Studio route). → Decision Queue #8.
- **Shared owner files (mostly intentional multi-view):** `routers/misc.py` (customers/users/settings), `routers/command.py` (dashboard/command), `poster_studio.py` (cover-studio/poster-studio), `orchestrator.py` (orchestrator/factory-monitor). The remainder pair an active capability with a merged/deprecated sibling — consistent with consolidation. No action beyond Decision Queue #3.

---

## 2. APIs / Routers
**Source:** `/app/backend/routers/*.py` (88 files) + `server.py`.
- **Registered & implemented:** 88 / 88 routers imported and included in `server.py`. **0 unregistered routers.**
- **Enforcement:** all mounted under `/api/*` prefixes (verified list in audit output).
- **Note (partially-overlapping prefix):** `analytics`, `commerce` both expose a bare `/api` router in addition to namespaced ones — intentional legacy compatibility; not a defect.
- **Test evidence:** representative endpoints exercised via curl (auth, capability-registry, migrations).
- **Recommended resolution:** none.

---

## 3. UI / Frontend Features
**Source:** `App.js` (118 `<Route>`), `src/pages/*.js` (102 pages).
- **Registered & implemented:** all enterprise routes map to a registry capability and an imported page.
- **Implemented — NOT registered (21):** public/consumer + auth/legal surface — `catalog, book/:id, products/:id, knowledge/:id, colleges/:id, access/:token, checkout/success, purchase/success, learn, my-learning, pathways, favorites, certificates, search, notifications, shipping-status, login, terms, privacy, refunds, *`.
  - **Classification:** *Implemented, not registered — out of capability-registry scope by design* (registry tracks Factory capabilities, not the public storefront).
  - **Recommended resolution:** OPTIONAL — register the "QRU Online (Consumer Storefront)" as one umbrella capability for one-identity completeness. Decision Queue #10.
- **Defect scan:** 0 routes reference an undefined/unimported component (the login white-screen root cause is resolved and will not recur for these routes).

---

## 4. Standards & Constitution
**Sources:** `qiks_standards` (39), `constitutional_registry` (5), `factory_constitution` (5), `constitution_versions` (1), `qbos_versions` (1), `qeds_versions` (1), `qics_portals` (8), `trust_registry` (8). Routers: `qiks, qbos, qeds, qics, governance, governance_binding, manufacturing_standards, trust, protection`.

| Item | Registered | Implemented | Enforcement status | Classification |
|---|---|---|---|---|
| qiks_standards (STD-00001…39) | ✅ 39 | ✅ router `qiks` | ⚠️ `enforced` flag not set on records | **Unenforced / undetermined** — enforcement condition not explicitly recorded |
| constitutional_registry (QRU-CON-0001/0002, STD-MFG/EIP/RFN) | ✅ 5 | ✅ | ⚠️ no `status` field | Registered, **lifecycle status undocumented** |
| factory_constitution / constitution_versions | ✅ 5 / 1 | ✅ | versioned | Registered & implemented |
| qbos_versions / qeds_versions | ✅ 1 / 1 | ✅ routers `qbos`,`qeds` | versioned | Registered & implemented |
| qics_portals | ✅ 8 | ✅ router `qics` | active | Registered & implemented |
| trust_registry | ✅ 8 | ✅ router `trust` | per-product attestations | Registered & implemented |

- **Test evidence:** routers present and mounted; enforcement bindings exist (`governance_binding`) but per-standard `enforced` condition is not stored on each `qiks_standards`/`constitutional_registry` record.
- **Recommended resolution:** define an explicit `enforced` condition + `status` on every standard so each has "one defined enforcement condition." Decision Queue #7.

---

## 5. Agents / Digital Workforce
**Sources:** `digital_employees` (13, Active), `registry_agents` (26), `ll_pilots` (5), `pilot_reports` (3), capability `agents`, `pilot-coordinator`.

| Item | Count | Status field | Classification | Recommended resolution |
|---|---|---|---|---|
| digital_employees (Chief Executive Agent, Research Director, Verification Lion, Manufacturing Director, …) | 13 | Active | **Registered & implemented** | none |
| registry_agents (Kingdom Lion™, Legacy Eagle™, Royal Phoenix™, …) | 26 | ⚠️ `status`/`mode` = null | **Registered, lifecycle-status undocumented** (brand/mascot agents) | assign status/mode; confirm not duplicative of digital_employees. Decision Queue #6 |
| ll_pilots / pilot_reports | 5 / 3 | mixed | Registered & implemented (Little Legacy pilots) | none |
| PILOT-MFG-0001 (pilot-coordinator, Shadow Mode) | 1 | active | Registered & implemented | continue shadow→write governance path |

- **Note:** `registry_agents` (brand characters) and `digital_employees` (operational workforce) are **distinct** concepts — NOT a duplicate — but the 26 brand agents lack an intentional lifecycle status.

---

## 6. Engines & Workflows
**Sources:** engine modules (`rendering_engine, deliverable_renderer, book_manufacturing, decoder_engine, refinement_engine, workflow_engine, manufacturing_flow, orchestrator, prod_migrations`), `workflow_jobs` (14), `flow_transitions` (3), capabilities in the `engine` layer.
- **Registered & implemented:** decoder-engine, refinement, workflows, flow, orchestrator, director, manufacture, knowledge-manufacturing, publishing, book-mfg — all resolve to owner modules.
- **Publishing Lineage Engine™** (new): implemented in `prod_migrations.py`, surfaced under `production-operations`, **registered as inherited**. Test evidence: `backend/tests/test_conflict_resolution.py` (all branches pass).
- **Recommended resolution:** none; consider registering the Lineage Engine as its own sub-capability for granular traceability (optional). Decision Queue #7 (extension).

---

## 7. Lessons / Products / Knowledge Records
**Sources:** `products` (243), `engine_products` (242), `media_products` (50), `qiks_lessons` (6), `knowledge_records` (85), `knowledge_engine_records` (44), `book_records` (20), `decoder_records` (21), `colleges` (17), `topic_registry` (20).

| Item | Count | Classification | Note |
|---|---|---|---|
| products vs engine_products | 243 / 242 | **Potential duplicate surface — unresolved** | near-parity suggests a mirror/dual-write; confirm canonical source. Decision Queue #9 |
| knowledge_records vs knowledge_engine_records | 85 / 44 | Partially overlapping — unresolved | confirm which is canonical KR store |
| book_records | 20 | Registered & implemented | Workstream A concerns 4 create + 8 EPUB re-points (prod-scope, pending) |
| qiks_lessons / colleges / topic_registry | 6 / 17 / 20 | Registered & implemented | learner content |
| Workstream C targets (PRD-00130/196/201/202/205) | 5 | **Unresolved (prod-scope)** — Published w/ unverified KR | governed hold pending on production |

- **Recommended resolution:** confirm products↔engine_products and KR↔KR-engine canonicity (Decision Queue #9); complete Workstream A & C on production via Production Operations panel.

---

## 8. Recipes / Inheritance
**Sources:** `inherited_products` (20), `kr_lineage` (5), `kr_enterprise_memory` (3), `product_families` (2), `inherited_recipes`/`kr_inheritance` modules.
- **Classification:** Registered & implemented.
- **Enforcement:** inheritance applied at manufacture time (Manufacturing Promise™ pillars).
- **Recommended resolution:** none; extend lineage-checksum identity to recipes for full traceability (roadmap).

---

## 9. PMS / PMF & Manufacturing Records
**Interpretation:** PMS = Production Manufacturing System records; PMF = Production/Manufacturing Fit (acceptance) records.
**Sources:** `manufacturing_orders` (22), `manufacturing_jobs` (29), `production_orders` (7), `production_line_runs` (4), `manufacturing_batches` (5), `production_acceptance_records` (21), `distribution_acceptance_records` (6).
- **Classification:** Registered & implemented; acceptance records constitute the PMF evidence trail.
- **Enforcement:** acceptance gates enforced via `readiness`, `inspection`, `governance_binding` routers.
- **Recommended resolution:** none.

---

## 10. Database Objects
- **121 collections** enumerated (full counts in audit output). All map to a router/engine owner or are event/telemetry logs (`org_activity` 3670, `activities` 604, `design_telemetry` 196, `ai_usage` 1092, `autonomy_actions` 237).
- **Empty/reserved collections:** `distributions` (0), `processed_webhook_events` (0), `products_trash` (0) — reserved/behavioral, not defects.
- **Recommended resolution:** none.

---

## 11. Founder Approvals & Proposals
**Sources:** `founder_escalations` (20), `production_acceptance_records` (21), `distribution_acceptance_records` (6), `after_action_reviews` (2), `factory_audits` (16), `qa_cleanup_audit` (16); disk proposals in `/app/memory/proposals/` and `/app/migration_packages/`.

| Item | Classification | Recommended resolution |
|---|---|---|
| RI-MFG-0003 publish-snapshot proposal (`/app/memory/proposals/`) | **Proposed / unresolved** | Founder approve to build Workstream C immutable snapshots. Decision Queue #2 |
| Migration ZIP: RI-MFG-0002b (`/app/migration_packages/`) | **Superseded** by Production Operations panel | retire the ZIP-for-Support path. Decision Queue #1 |
| Migration ZIP: WORKSTREAM_C containment | **Superseded** by Production Operations (Learn Containment) | retire. Decision Queue #1 |
| founder_escalations / acceptance records | Registered & implemented (approval evidence trail) | none |

---

## 12. Completion-Standard Check
The reconciliation is complete when every approved capability has **one identity, one status, one implementation location, one enforcement condition, one accountable next action.**

| Criterion | State |
|---|---|
| One official identity | ✅ 101/101 unique registry ids (aliases only via `merged`) |
| One documented status | ⚠️ capabilities ✅; **standards (44) & registry_agents (26) lack explicit status/enforcement** → Decision Queue #6/#7 |
| One traceable implementation location | ✅ 0 missing owner files, 0 routes without pages |
| One defined enforcement condition | ⚠️ capabilities/routers ✅; per-standard `enforced` condition not stored → Decision Queue #7 |
| One accountable next action | ✅ every non-clean item has an entry in the Founder Decision Queue |

**Verdict:** Capability, API, and UI layers are fully reconciled and clean. Residual open items are concentrated in (a) standards/agents lifecycle+enforcement metadata, (b) products↔engine_products / KR canonicity, and (c) production-scope execution of Workstreams A & C — all captured in the Founder Decision Queue. No corrections applied; all held for Founder review.
