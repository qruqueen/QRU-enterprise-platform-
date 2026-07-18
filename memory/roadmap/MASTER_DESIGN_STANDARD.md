# QRU Master Design Standard™ — Post-Launch Initiative #1 (PLAN ONLY)

> Status: APPROVED, DEFERRED to after QRU Online launch. No code changes yet (launch freeze).
> Founder decisions: timing = after launch (1a); scope = full program (2d); item 3
> (auto-surface products lacking a verified KR into the Decoder) = PAUSED for now.
> Principle: "Improve the standard, not the product. One owner. Inheritance over duplication."
>
> HARD CONSTRAINT (Founder, 2026-06): "Hide complexity, increase quality." NO new buttons, NO
> alternate workflows, NO added Founder steps. Keep the CURRENT button structure exactly. The
> higher quality must arrive purely through stronger INHERITANCE behind the existing interface.
> Where books have a Founder cover-concept selection, that stays for books; for other products
> the strongest concept is chosen AUTOMATICALLY behind the scenes (no new selection UI). If the
> Founder wants to intervene, they use the buttons that already exist (e.g. regenerate-cover),
> which now simply yield book-grade output.

## The problem (verified in code, 2026-06)
Two parallel design pipelines produce two quality tiers:

| | Books (Gold Standard) | All other products |
|---|---|---|
| Engine | `book_manufacturing.py` → `design_studio.manufacture_design_concepts` | `routers/products.py` → `rendering_engine.ensure_branded_assets` → `design_language.premium_cover` |
| Cover | `art_direction(n=3)` + 3 AI hero concepts + typographic `compose()` + Founder selection + print wrap | ONE generic hardcoded hero prompt, or deterministic placeholder frame |
| Decoder bridge | `POST /decoder/{did}/create-product` supports **Book only** | not supported ("more product types are coming") |

Result: e.g. the Sports Intelligence *workbook* cover is visibly lower quality than the *book*
cover, because workbooks never touch `design_studio`.

## The goal
`design_studio` becomes the **single Master Design Standard** that EVERY product family inherits
(covers + interiors/deliverables), and the Decoder → Create Product bridge works for all families.

## Target architecture
- `design_studio` is the one owner of art direction, hero-concept generation, composition, and
  print/wrap. Every family's manufacturing recipe *inherits* it (Manufacturing Foundation),
  rather than `rendering_engine` maintaining a second, weaker cover path.
- `rendering_engine.ensure_branded_assets` is refactored to DELEGATE cover generation to
  `design_studio` (keeping vault-reuse + deterministic fallback for zero-AI/budget-capped cases),
  so there is one code path and one quality bar.
- The Decoder `create-product` bridge routes every product type into the shared engine.

## Implementation plan (phased, post-launch)

### Phase 1 — Covers parity (Scope 2a, the visible gap)
1. Extract a reusable `design_studio.manufacture_product_cover(product, kr, n=3)` that books and
   products both call (art direction + concepts + compose + Founder selection).
2. Refactor `rendering_engine.ensure_branded_assets` to call it (preserve: vault reuse-by-default,
   `asset_mode=generate` override, deterministic fallback when AI capacity/budget unavailable,
   Founder-imported `asset_vault_selected` protection).
3. NO new UI: non-book products auto-select the strongest concept behind the scenes (no added
   selection step). The existing `POST /products/{pid}/regenerate-cover` button stays and now
   yields book-grade output. Books keep their existing selection flow unchanged.
4. Upgrade existing product covers on demand via the existing regenerate-cover button.

### Phase 2 — Interior/deliverable parity (Scope 2b)
5. Route product interiors/deliverables through the same design_studio composition + typography
   standard used for book interiors (`deliverable_renderer` inherits design_studio typography).
6. Ensure print specs (trim, bleed, DPI) come from one shared spec source per product family.

### Phase 3 — Generalize the Decoder → Product bridge (Scope 2c)
7. Expand `POST /decoder/{did}/create-product` beyond "Book" to Workbook, Poster, Infographic,
   Teacher/Caregiver Guide, Lesson Plan, etc., each mapped to its manufacturing recipe.
8. Each family inherits the shared design standard automatically (no per-family cover code).

## Files in scope
- `design_studio.py` (owner of the standard — add product-cover entrypoint)
- `rendering_engine.py` (delegate covers to design_studio; keep vault + fallback)
- `routers/products.py` (cover selection UX; regenerate-cover)
- `deliverable_renderer.py` / `design_language.py` (interior typography parity)
- `routers/decoder_engine.py` (generalize create-product bridge)
- `book_manufacturing.py` (extract shared cover fn; books keep behavior)

## Testing / Definition of Done
- A workbook and a poster generated for the same topic have cover quality visually equal to the
  book (art-directed hero + typographic compose + Founder-selectable concepts).
- Decoder Create Product works for at least Workbook + Poster end-to-end.
- No regression to book manufacturing or to vault reuse / zero-AI fallback / Founder-imported covers.
- Existing products can be upgraded via regenerate-cover without data loss.

## Explicitly PAUSED (revisit later)
- Item 3: auto-surfacing products that were created WITHOUT a verified Knowledge Record into the
  Decoder. Current rule stands: topics should start as verified Knowledge Records (KR-first), which
  then flow to Decoder → proofing → publishing.

## Sequencing
Do NOT start until: bookstore is live, one Founder Live purchase succeeds, and the Founder says go.
This is Post-Launch Initiative #1 (before the QRU Publishing Intelligence Dashboard™, unless the
Founder reprioritizes).
