# QRU Factory™ — Founder Decision Queue
**Companion to:** Master Reconciliation Ledger (2026-07-26)
**Rule:** All items are HELD pending Founder governance approval. No corrections have been or will be applied without your decision. Each item states: the matter, the evidence, options, the recommended resolution, and the blast radius.

---

### DQ-1 — Retire the superseded migration ZIP packages
- **Matter:** `RI-MFG-0002b` and `WORKSTREAM_C_containment` ZIP packages were built for the (now-obsolete) "email a script to Support" path. They are superseded by the in-app **Production Operations™** panel + Publishing Lineage Engine.
- **Evidence:** `/app/migration_packages/*`, `/app/frontend/public/downloads/*.zip`; capability `production-operations` (inherited).
- **Options:** (a) Archive/retire the ZIPs and mark superseded; (b) keep as historical artifacts; (c) delete downloads.
- **Recommended:** (a) mark **superseded**, keep on disk as history, remove the public download links.
- **Impact:** cosmetic; no data effect.

### DQ-2 — Approve build of Workstream C immutable snapshots (RI-MFG-0003)
- **Matter:** Proposal for QRU Learn publish-time **immutable snapshots** of Verified KRs is `proposed/unresolved`.
- **Evidence:** `/app/memory/proposals/RI-MFG-0003_publish_snapshot_proposal.md`.
- **Options:** (a) Approve to implement now; (b) defer; (c) supersede with a different design.
- **Recommended:** (a) approve — it directly enforces "no silent mutation of published learner content" (Treasure Standard).
- **Impact:** new capability; backend + learner-serving path; medium effort.

### DQ-3 — Confirm permanent status of the 9 merged capabilities
- **Matter:** `manufacturing-studio, mfg-command, product-library, creative-studio, visual-studio, media-starter-kit, command, enterprise-health, blueprint` are `merged`.
- **Options:** (a) Keep as permanent historical aliases (no nav); (b) formally retire their routes.
- **Recommended:** (a) — preserves lineage without clutter.
- **Impact:** navigation only.

### DQ-4 — Confirm retirement of `experience-lab` (deprecated)
- **Options:** (a) Retire + hide; (b) revive.
- **Recommended:** (a) retire.
- **Impact:** navigation only.

### DQ-5 — Reconfirm the 8 reserved/future capabilities
- **Matter:** `feature-film, streaming, interactive-learning, trending-topics, multi-language, ai-tutor, documentary, cinema-studio-future` are `future`.
- **Options:** (a) Keep on roadmap; (b) retire any no longer wanted.
- **Recommended:** keep unless you name ones to drop.
- **Impact:** roadmap hygiene only.

### DQ-6 — Assign lifecycle status to the 26 `registry_agents` (brand agents)
- **Matter:** Brand/mascot agents (Kingdom Lion™, Legacy Eagle™, Royal Phoenix™, …) have `status`/`mode` = null → no intentional lifecycle state. They are distinct from the 13 operational `digital_employees` (Active).
- **Options:** (a) Assign each a status (active/reserved/retired) + confirm they are brand identities, not workforce; (b) merge concept with digital_employees if intended to be the same.
- **Recommended:** (a) — set explicit status; keep separate from digital workforce.
- **Impact:** metadata only (governed edit, done via a future write-approved pass).

### DQ-7 — Define one enforcement condition + status per standard (44 records)
- **Matter:** `qiks_standards` (39) and `constitutional_registry` (5) records do not store an explicit `enforced` condition or lifecycle `status`. The completion standard requires "one defined enforcement condition" per approved capability/standard.
- **Evidence:** sampled records show `enforced=None`, `status=None` (constitutional_registry).
- **Options:** (a) Add an `enforced` (where/how it's checked) + `status` field to every standard; (b) accept current implicit enforcement via `governance_binding`.
- **Recommended:** (a) — makes enforcement auditable and satisfies the completion standard. (Optional extension: register the **Publishing Lineage Engine™** as its own sub-capability.)
- **Impact:** governed metadata pass across 44 records; no behavioral change.

### DQ-8 — Resolve the shared `/cinema-studio` route
- **Matter:** `cinema-studio` and `podcast-studio` both map to route `/cinema-studio`.
- **Options:** (a) Give Podcast Studio its own route (`/podcast-studio`); (b) confirm intentional shared studio surface.
- **Recommended:** (a) distinct route for clarity.
- **Impact:** one frontend route + nav entry.

### DQ-9 — Confirm canonicity: `products` (243) vs `engine_products` (242); `knowledge_records` (85) vs `knowledge_engine_records` (44)
- **Matter:** Near-parity between `products`/`engine_products` suggests a mirror or dual-write; two KR stores exist.
- **Options:** (a) Declare one canonical store + document the other as a projection/cache; (b) investigate for true duplication.
- **Recommended:** (a) document canonical source; keep the derived one clearly labeled.
- **Impact:** documentation now; potential consolidation later (governed).

### DQ-10 — Optionally register the public "QRU Online" consumer storefront as a capability
- **Matter:** 21 public routes (catalog, book/:id, checkout, learn, legal…) are implemented but not in the capability registry (by design).
- **Options:** (a) Register one umbrella "QRU Online (Consumer Storefront)" capability for one-identity completeness; (b) leave out of scope.
- **Recommended:** (a) — gives the consumer surface a single official identity in the registry.
- **Impact:** one registry entry.

### DQ-11 — Complete Workstreams A & C on PRODUCTION (execution, not code)
- **Matter:** Code is ready and deployed-pending. Actual production data changes require you to run them from the Production Operations panel on qru-online.com (I cannot access production).
- **Steps:** Deploy → **Inspect Records** → **Apply Migration** (creates absent books) → **Resolve Conflicts** (adopts BOOK-0013 same-book) → **Apply New Code** (publishes BOOK-0016 distinct work) → **Apply Governance Hold** (Workstream C).
- **Recommended:** proceed after reviewing the lineage evidence per book.
- **Impact:** production data (governed, dry-run-first, rollback-protected).

---

## Priority order (recommended)
1. **DQ-11** (complete the live migration — the active operational goal)
2. **DQ-7** (enforcement/status on standards — closes the completion-standard gap)
3. **DQ-2** (immutable snapshots — Treasure Standard integrity)
4. **DQ-9** (canonicity of products/KR stores)
5. **DQ-6, DQ-1, DQ-8, DQ-10** (metadata & hygiene)
6. **DQ-3, DQ-4, DQ-5** (lifecycle confirmations)
