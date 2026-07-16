# QRU FACTORY — MODERNIZATION AUDIT (Official Baseline)
Date: 2026-07-16 · Method: evidence-based static + production analysis · Feature dev: FROZEN

## Evidence sources
- Backend: 130 modules, 79 routers registered in `server.py` (lines 40–154), only `routers/__init__` unwired.
- Frontend: 96 page files, **107 `<Route>`s** in `App.js`, 27 sidebar nav items (`layouts/Layout.js`).
- Orphaned modules (imported by nothing): `_run_proof.py`, `backfill_marketing.py`, `qru_governance.py`.
- First-hand production evidence: full publication run of *The Understanding Tree* (this session), including real KDP-rejection fixes.

──────────────────────────────
## CAPABILITY INVENTORY (12-point, at ownership-cluster level)
Auditing at the **responsibility/owner** level per the Constitution (one responsibility, one owner). Sub-modules roll up into their owning capability.

### 1. Knowledge & Decoder Engine
1. Name: Knowledge Records + Decoder Engine™. 2. Purpose: capture/verify source knowledge and decode it into 38-field manufacturing-ready records. 3. Owner: `decoder_engine.py` + `knowledge_record_v2.py` + `kr_inheritance.py`. 4. Status: **Complete** — routers `decoder_engine`, `knowledge`, `knowledge_v2`, `kr_manufacturing` all registered; verified in prior iterations. 5. Production evidence: Decoder→Book bridge used to seed books. 6. Founder value: single source of truth; no re-entry. 7. Automation: **Automatic** (decode) / Assisted (verify). 8. Touchpoints: verify + promote (human gate — correct, keep). 9. Inherits: Treasure Standard, provenance. Should also inherit: the Post-Publish recipe (currently stops at Book). 10. Duplication: `knowledge_extraction.py` overlaps `decoder_engine` — MERGE candidate. 11. Debt: two knowledge extractors. 12. **Recommendation: Keep + Merge extractors.**

### 2. Book Manufacturing System™ (7-button)
1. Name: Book Manufacturing OS. 2. Purpose: turn one approved manuscript into a complete publication package via 7 buttons. 3. Owner: `book_manufacturing.py` (+ `routers/book_manufacturing.py`, `design_studio.py`, `rendering_engine.py`). 4. Status: **Complete for print/ebook; Partial for post-publish** — 7 buttons work; Video mocked; Post-Publish recipe not yet auto-triggered. 5. Production evidence: *The Understanding Tree* fully manufactured + AUTHORIZED this session. 6. Founder value: highest — this is the core product line. 7. Automation: **Assisted→Automatic** (Decoder bridge → 7 buttons). 8. Touchpoints: Upload, approve editorial, pick cover, approve blurb, approve price, Authorize Release. All justified EXCEPT redundant reads (see Friction). 9. Inherits: Treasure Standard, design engine, rendering, recipes. Should inherit: post-publish recipe. 10. Duplication: NONE (well-owned). 11. Debt (fixed this session): A4 interior→6×9, barcode text, ebook PNG→JPEG, package missing wrap, stale deliverables, gate-ready bug. Remaining: Video button mocked. 12. **Recommendation: Complete (post-publish recipe + video).**

### 3. Generic Product / Asset Manufacturing
1. Name: Product Manufacturing + recipes. 2. Purpose: manufacture non-book products (workbooks, posters, scripts). 3. Owner: `routers/products.py` + `manufacturing_recipes.py` + `product_recipes.py` + `inherited_recipes.py` + `asset_manufacturing.py` + `manufacturing_engine.py` + `manufacturing2.py` + `manufacturing_flow.py`. 4. Status: **Partial/overlapping** — many recipe engines. 5. Production evidence: products router live; unclear which recipe engine is canonical. 6. Founder value: medium (future product lines). 7. Automation: Assisted. 8. Touchpoints: many, scattered across pages. 9. Inherits: should inherit Book System's 7-button UX + design/rendering. 10. Duplication: **SEVERE** — `manufacturing`, `manufacturing2`, `manufacturing_engine`, `manufacturing_flow`, `manufacturing_recipes`, `product_recipes`, `inherited_recipes` overlap. 11. Debt: 7 manufacturing modules; unclear canonical owner. 12. **Recommendation: Merge → one recipe engine inheriting the Book System.**

### 4. Design (covers, posters, layout)
1. Name: QRU Design Studio™. 2. Purpose: AI art + PIL typography for print-quality assets. 3. Owner: `design_studio.py`. 4. Status: **Complete** (books) — used for all covers/wraps this session. 5. Production evidence: The Understanding Tree cover + wrap. 6. Founder value: high. 7. Automation: Automatic. 8. Touchpoints: cover selection only. 9. Inherits: `design_language.py`. 10. Duplication: **HIGH** — `design_director`, `design_intelligence`, `creative_director`, `poster_studio`, `visual_studio` all touch design. 11. Debt: 6 design modules; `design_studio` is the proven one. 12. **Recommendation: Keep `design_studio`; Merge/Remove the rest.**

### 5. Media / Video
1. Name: Media/Cinema. 2. Purpose: video/audio production. 3. Owner: spread across `media_division`, `media_engine`, `media_production`, `media_render`, `cinema_studio`, `storyboard_master`, `media_intelligence`, `visual_studio`, `media_starter_kit`, `media_library`. 4. Status: **Prototype/Mocked** — video generation produces a manifest, no real animation (acknowledged). 5. Production evidence: audio narration prototype only (honestly labeled). 6. Founder value: low today (paused by Founder). 7. Automation: Manual/Assisted. 8. Touchpoints: many pages (media-studio, media-division, media-library, cinema-studio, media-starter-kit). 9. Inherits: little. 10. Duplication: **SEVERE** — 10+ media modules & 5 media pages. 11. Debt: largest debt cluster; also caused the disk-full incident (2.9 GB `media_masters`). 12. **Recommendation: Simplify → one Media capability; Remove unused engines; cap asset storage.**

### 6. Publishing & Marketplace
1. Name: Publishing/Marketplace. 2. Purpose: produce marketplace listing assets, metadata, keywords, KDP package. 3. Owner: `product_publishing.py` + `publishing_standard.py` + `routers/publishing.py`. 4. Status: **Complete (book)** — KDP package + metadata proven. 5. Production evidence: The Understanding Tree KDP package. 6. Founder value: high. 7. Automation: Assisted. 8. Touchpoints: Publish tab. 9. Inherits: Treasure Standard. 10. Duplication: partial with Book System's own KDP checklist. 11. Debt: two KDP-package paths (`product_publishing.kdp_package` vs book_manufacturing). 12. **Recommendation: Complete + own the Marketplace slice of the post-publish recipe.**

### 7. Marketing
1. Name: Marketing Engine. 2. Purpose: social/launch/store graphics. 3. Owner: `marketing_engine.py` (`build_family`). 4. Status: **Complete but under-used** — engine exists, not auto-triggered on publish. 5. Production evidence: exists; `backfill_marketing.py` is orphaned. 6. Founder value: high (launch). 7. Automation: Assisted (should be Automatic post-publish). 8. Touchpoints: `routers/marketing.py`. 9. Inherits: `design_language`. 10. Duplication: NONE (single owner — do NOT create a new one). 11. Debt: orphaned `backfill_marketing.py`. 12. **Recommendation: Keep; wire into post-publish recipe; Remove `backfill_marketing.py`.**

### 8. Distribution & Partner Integrations
1. Name: Distribution Center + Partner Integration Layer. 2. Purpose: deliver to external platforms. 3. Owner: `routers/distribution.py` + `distribution/` + `integration_hub.py` + `connectors.py`. 4. Status: **Partial** — connectors/routing exist; most external platforms require OAuth not yet configured. 5. Production evidence: connector catalog (Etsy/YouTube/social); `auto_distribute` present. 6. Founder value: medium. 7. Automation: Assisted. 8. Touchpoints: distribution + integration-hub pages. 9. Inherits: governance. 10. Duplication: `connectors.py` vs `distribution/connectors.py` vs `integration_hub.py` overlap. 11. Debt: duplicate connector definitions. 12. **Recommendation: Merge connectors into one Partner Layer under the Distribution Center.**

### 9. Website / Storefront / Consumer Campus (public site owner)
1. Name: QRU Storefront + Consumer Campus. 2. Purpose: public catalog + product/book pages + checkout. 3. Owner: `commerce.py` (`storefront`) + `routers/consumer.py` (`/catalog`) + `Store.js`/`/learn`. 4. Status: **Partial** — catalog + storefront + Stripe checkout exist; per-book public page + author page not rendered from Book Record. 5. Production evidence: `commerce.storefront()`, `consumer.catalog()`. 6. Founder value: high (owned distribution channel). 7. Automation: Manual. 8. Touchpoints: store/products pages. 9. Inherits: pricing/commerce. 10. Duplication: NONE for public site (Distribution Center = external only). 11. Debt: no author page; book page not auto-published from Book Record. 12. **Recommendation: Complete — this is the correct owner for Website Publishing (per Architecture Review). Enhance, don't create new.**

### 10. Verification & Governance
1. Name: Verification + Product Governance + Constitution. 2. Purpose: enforce Treasure Standard, provenance, gates. 3. Owner: `verification_engine.py`, `product_governance.py`, `constitution.py`, `governance_binding.py`. 4. Status: **Complete**. 5. Production evidence: Final Release Gate blocked/authorized correctly this session. 6. Founder value: high (trust). 7. Automation: Automatic. 8. Touchpoints: approval gates (correct). 9. Inherits: Constitution. 10. Duplication: `constitution.py` vs `constitution_v1.py` vs `qru_governance.py` (orphan). 11. Debt: legacy `constitution_v1`, orphan `qru_governance`. 12. **Recommendation: Keep; Remove `constitution_v1`/`qru_governance`.**

### 11. Autonomy / Director / Orchestration
1. Name: Autonomy & Directors. 2. Purpose: autonomous manufacturing/decisioning. 3. Owner: 11 modules (`autonomous_engine`, `autonomy`, `autonomy_ai`, `orchestrator`, `*_director`, `continuous_improvement`, `improvement_loop`, `self_healing`, `director_intelligence`). 4. Status: **Partial/Prototype** — many overlapping "brains". 5. Production evidence: sparse; several pages exist (autonomy, director, orchestrator, enterprise-autonomy). 6. Founder value: unclear/low today. 7. Automation: mixed. 8. Touchpoints: multiple dashboards. 9. Inherits: unclear. 10. Duplication: **SEVERE** — 11 modules, overlapping intent. 11. Debt: largest conceptual sprawl; unclear ownership. 12. **Recommendation: Simplify → one autonomy owner; Remove/Merge the rest.**

### 12. Enterprise Memory
1. Name: Memory Engineering. 2. Purpose: persistent factory memory. 3. Owner: `memory_engineering.py` + `routers/memory.py`. 4. Status: **Partial**. 5. Production evidence: memory router live. 6. Founder value: medium. 7. Automation: Assisted. 8. Touchpoints: memory-engineering page. 9. Inherits: n/a. 10. Duplication: overlaps `continuity.py`. 11. Debt: two memory concepts. 12. **Recommendation: Merge continuity into memory.**

### 13. Founder Experience (navigation surface)
1. Name: Founder UI. 2. Purpose: single pane to run the factory. 3. Owner: `layouts/Layout.js` + 96 pages. 4. Status: **Partial — over-built** — 107 routes, 96 pages, 27 nav items. 5. Production evidence: many pages are dashboards for prototype/duplicate engines (agents, blueprint, companion, concierge, engineering-console, experience-lab, factory-monitor, enterprise-autonomy…). 6. Founder value: LOW where pages front unfinished engines. 7. Automation: n/a. 8. Touchpoints: too many — this is the #1 Founder friction. 9. Inherits: n/a. 10. Duplication: many near-identical dashboards. 11. Debt: dozens of low-value pages. 12. **Recommendation: Simplify → collapse to the ~8 capabilities the Founder actually uses.**

──────────────────────────────
## REPORT 1 — FACTORY CAPABILITY MAP
```
KNOWLEDGE (Decoder Engine, KR v2)
   └─inherits→ Treasure Standard, Provenance
        ↓ bridge
BOOK MANUFACTURING SYSTEM™ (owner: book_manufacturing.py)
   ├─inherits→ Design Studio (covers/wraps)
   ├─inherits→ Rendering Engine (PDF/EPUB)
   ├─inherits→ Recipes (manufacturing_recipes)
   ├─inherits→ Verification/Governance (Final Release Gate)
        ↓ Publish (Authorize Release)
   [PLANNED] POST-PUBLISH RECIPE →
        ├─ Marketplace  → product_publishing.py        [Ready]
        ├─ Marketing    → marketing_engine.py           [Ready, not wired]
        ├─ Website      → commerce.py + consumer catalog [Partial]
        ├─ Media scripts→ ai_service                     [Ready as text]
        ├─ Distribution → distribution/ + integration_hub[Partial]
        └─ Founder pkg  → book_manufacturing.py          [Ready]
CROSS-CUTTING: Governance, Verification, Enterprise Memory, Cost Meter
```

## REPORT 2 — FACTORY HEALTH SCORE (evidence-based, /10)
- **Architecture 6** — clean ownership for Book/Design/Governance; severe duplication in manufacturing(7), media(10), design(6), autonomy(11).
- **Founder Experience 4** — 107 routes/96 pages/27 nav = cognitive overload; many pages front prototypes.
- **Automation 6** — Decoder→Book automatic; publish→assets NOT automatic (manual re-triggers).
- **Manufacturing 8** — Book line proven end-to-end (The Understanding Tree).
- **Publishing 7** — KDP package works after this session's fixes (6×9, JPEG cover, barcode zone).
- **Distribution 4** — connectors exist, mostly unconfigured; duplicate connector defs.
- **Design 8** — `design_studio` proven; peers redundant.
- **Knowledge 8** — Decoder Engine complete; one duplicate extractor.
- **Verification 9** — gates enforced correctly in production.
- **Enterprise Memory 5** — exists, overlaps continuity.
- **Partner Integrations 4** — catalog present, OAuth not set up.
- **Website Publishing 5** — storefront+catalog exist; no auto book/author page.
- **OVERALL 6.0** — strong core, over-built periphery, automation gap at publish.

## REPORT 3 — FOUNDER FRICTION (proof → simplest fix)
1. **Navigation overload** — 96 pages/27 nav items (proof: `App.js` 107 routes). → Collapse nav to the ~8 used capabilities; archive the rest.
2. **Manual re-triggering of publish assets** — Authorize Release does not manufacture assets (proof: `authorize_release()` only sets flags, lines 676–694). → Auto-run post-publish recipe.
3. **Duplicate work across manufacturing engines** — 7 manufacturing modules (proof: file listing). → One recipe engine.
4. **Repeated re-generation loops** (this session: 6× wrap/package rebuilds) — caused by spec bugs surfacing at KDP + no pre-validation. → Validate against KDP spec before returning (now in place).
5. **Reading/decision overload on Publish tab** — pricing, blurb, wrap, package, checklist, review all stacked. → Progressive disclosure; keep the single Founder Release Review™ as the one gate.
6. **Broken/stale links** — 11 stale package deliverables + placeholder marketing links (proof: this session). → Show only manufactured deliverables (fixed for packages; apply pattern everywhere).

## REPORT 4 — PRODUCTION FLOW AUDIT: *The Understanding Tree* (first-hand)
| Step | Evidence | Finding |
|---|---|---|
| Upload/Editorial lock | editorial_status "Approved & locked" | ✅ clean |
| Design (cover) | selected_cover set | ✅ clean |
| Sanitize (retail interior) | rebuilt 6×9, 77pp | ⚠️ was A4 (bug, fixed) |
| Cover wrap | spine 0.1734", blank spine, clean barcode | ⚠️ 3 KDP bugs (fixed) |
| Pricing | $4.99/$12.99 recorded | ✅ Founder decision honored |
| Blurb | AI draft, Founder-approved | ✅ |
| Master package | interior+wrap+**ebook JPEG**+guide+metadata | ⚠️ wrap missing + PNG cover (fixed) |
| Authorize Release | authorized by Founder | ✅ gate enforced |
| Post-publish assets | none produced | ❌ missing automation (recipe not wired) |
Findings: unnecessary re-gen (no pre-validation), missing automation (post-publish), disk incident (media bloat), broken inheritance (publish→assets). All root-caused with evidence above.

## REPORT 5 — MODERNIZATION ROADMAP (ranked; impact × low-effort × Founder-time × dedup × automation)
1. **Wire Post-Publish Recipe into Authorize Release** — inherits existing engines; one click → all assets. (highest impact, low effort, biggest automation gain)
2. **Show only manufactured deliverables everywhere; kill placeholder links** — trust + friction. (low effort)
3. **Collapse Founder nav to ~8 real capabilities; archive prototype pages.** (huge Founder-time saved)
4. **Merge 7 manufacturing engines → 1 recipe engine inheriting Book System.** (largest dedup)
5. **Consolidate media (10→1) + cap asset storage** — prevents disk incidents. (reliability)
6. **Merge design peers into `design_studio` (6→1).** (dedup)
7. **Complete Website Publishing** in Storefront/Campus (book+author page from Book Record). (owned channel)
8. **Merge connectors (3→1) under Distribution Center.** (dedup)
9. **Remove dead code:** `_run_proof.py`, `backfill_marketing.py`, `qru_governance.py`, `constitution_v1.py`. (hygiene)
10. **Consolidate autonomy (11→1) or shelve until needed.** (clarity)

## REPORT 6 — EXECUTIVE SUMMARY
- **Remain as-is:** Book Manufacturing System™, Design Studio™, Verification/Governance gates, Decoder Engine.
- **Complete:** Post-publish recipe, Website Publishing (Storefront), Marketplace/Marketing wiring.
- **Simplify:** Founder navigation (96→~8), Publish tab disclosure.
- **Merge:** manufacturing engines (7→1), design peers (6→1), media (10→1), connectors (3→1), memory+continuity.
- **Remove:** `_run_proof`, `backfill_marketing`, `qru_governance`, `constitution_v1`; prototype dashboards fronting nothing.
- **Become automatic:** publish → all publication assets (Marketplace/Marketing/Website/Media/Distribution/Founder).
- **Never require Founder again:** asset re-triggering, package re-assembly, deliverable cleanup, format/spec validation.

### Final Question — if rebuilt today (for simplification only, NOT a redesign)
One manufacturing recipe engine + one design engine + one media engine + one distribution layer, all inherited by product lines; a single Founder surface of ~8 capabilities; and publishing as an event that fans out the full asset set automatically. Everything the current Factory proved valuable (Book System, Design Studio, gates, Decoder) stays; the periphery collapses into these owners.
