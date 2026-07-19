# QRU Factory™ — Operations Manual (Manufacturing, UKR, & Capabilities)
_Last updated: 2026-06_

## 1. The Golden Thread — why the Knowledge Record (UKR) governs everything
The Factory's constitutional rule: **no customer-facing content is invented at the product stage.**
Every product inherits from a single verified source, so all formats stay consistent and true.

```
Idea/Topic → Knowledge Record (KR) → VERIFY → Decoder Record™ (understanding layer)
          → Products (book, video, audio, poster, workbook…) → Design → Quality Gates → Publish
```

- **Knowledge Record (KR / "UKR"):** the single source of truth for a subject (facts, verified truth,
  citations). Manufactured at `/kr-manufacturing`; verified at `/verification` (+ autonomous
  `/verification-team`). Only a **Verified** KR may feed products.
- **Decoder Record™ (`/decoder-engine`):** transforms a Verified KR into a governed 38-field
  understanding layer — definition, mental model, everyday analogy, story, memory sentence, and an
  Understanding Test — scored by a Decoder Scorecard™ and approved on the Founder Review Shelf™.
  **Every downstream product inherits its "understanding" from here.** Change the KR/Decoder and the
  content of every derived product changes.
- **Founder-authored books** are the ONE governed exception (you are the author/source of truth);
  they don't require an upstream KR. Book *trailers* use the book itself as the source.

## 2. End-to-end pipeline (every product)
1. **Capture knowledge** — Research Center `/research`, Bulk Library Import `/library-import`,
   Topic Registry `/topic-registry`, Promotion Pipeline `/promotion-pipeline`.
2. **Manufacture the KR** — `/kr-manufacturing` (Idea → Research → Draft → Verify → Founder Review →
   Enterprise Memory™).
3. **Decode for understanding** — `/decoder-engine` → Decoder Record™ + Scorecard, approve on the Shelf.
4. **Create the product** — `/create` (outcome-first: describe the result, the Factory picks the recipe)
   or `/manufacture` (direct). Product inherits KR + Decoder.
5. **Design** — covers/interior/art via Media & Design Studio (routes through `design_studio`, the
   Master Design Standard™ — book-grade art direction for every product family).
6. **Quality Gates™** `/inspection` — 9 objective, blocking gates (a product can't publish until it passes).
7. **Authorize** — Founder approval (`/founder-inbox`) — the Knowledge-First checkpoint.
8. **Publish & distribute** — QRU Store `/store` (Stripe), YouTube `/youtube`, Amazon KDP checklist,
   Publishing Connectors `/connectors`, and the public storefront (qru-online.com).

## 3. Per-product instructions
### Book (flagship 7-step line — `/book-manufacturing`)
Upload/write manuscript → **Proof** (findings) → **Resolve findings** → **Design** (cover concepts) →
**Select cover** → **Audio/Video** deliverables → **Pricing** (`/pricing-advisor`, scenarios) →
**Authorize** → **Publish** → **Post-publish** monitoring → **Assemble master package** + **KDP checklist**
+ **Manifest**. Sharing via signed share tokens.

### Video (products + book trailers — QRU Video Fulfillment™)
Rendered on **publish or explicit request** (never silently per-manufacture). "Video Script" /
"Short Video" / "YouTube Video Script" products render an MP4 **from the script**; other products
render from their verified KR; books render a **trailer** from the book. Technique = image-based
motion (Ken Burns) + AI narration (honestly labeled — NOT frame-by-frame). MP4s are **cached**
(reused unless the source changes) and stored in **durable object storage** (survive redeploys).
YouTube Publisher™ auto-uses these Factory videos; "Generate missing videos" backfills in the background.
Studios: Story & Cinema Studio™ `/cinema-studio`, Flagship Showcase™ `/flagship-showcase`,
Little Legacy Learners™ `/little-legacy`, Storyboard Studio™ `/storyboard-studio`.

### Audio (Podcast Studio™ `/cinema-studio`)
Audiobooks/podcast episodes via real OpenAI TTS narration; inherits verified knowledge + brand Voice.

### Covers / Posters / Marketing (Media & Design Studio, Poster Studio™, Cover Studio™)
`design_studio` art direction → concepts → typographic compose → thumbnails/store graphics.
Deterministic zero-AI fallback guarantees a cover always renders.

## 4. Menu / taskbar capabilities (current status)
**Core (8):** Founder Console `/` · Create `/create` · Knowledge & Decoder™ `/knowledge` ·
Book Manufacturing™ `/book-manufacturing` · Media & Design Studio `/media-division` ·
Publishing & Distribution `/distribution` · Governance & Trust `/governance` · All Capabilities `/factory-map`.

**Sections (via /factory-map):** Knowledge (KR mfg, verification, decoder, research, topics,
translation, memory) · Manufacturing Engine (director, orchestrator, workflows, refinement, decoder) ·
Publishing (products, cover studio, publishing standard, companion) · Learning (colleges, teach) ·
Story & Cinema (characters, flagship showcase, little legacy, media studio, stock media, storyboard) ·
Marketing (poster studio) · Audio (podcast studio) · Video (cinema studio) · Quality (9 gates) ·
Distribution (connectors, QRU Store, YouTube Publisher) · Governance & Trust (constitution, design
director/intelligence, agents, manufacturing foundation, protection, trust) · Mission Control
(analytics, asset vault, autonomy, customers, workforce, command center, health, monitor, readiness,
failure intelligence, first-dollar, founder inbox, economics, projects, organization) ·
Administration (AI services, engineering console, integration hub, portability, settings, users).

**Legacy (marked for consolidation):** Command Console, Creative Studio, Enterprise Blueprint,
Enterprise Health, Experience Lab, Manufacturing Command, Manufacturing Studio, Media Starter Kit,
Product Library, Visual & Media Studio.

## 5. Verified vs. known gaps (honesty)
- ✅ VERIFIED live: public storefront + Stripe (real purchase → EPUB delivery); QRU Video Fulfillment™
  (script/KR/trailer → MP4, cached, durable); Master Design Standard™ Phase 1 (product covers via design_studio).
- ⚠️ KNOWN GAPS (roadmap): (a) UKR-inheritance governance NOT yet enforced on `/generate`,`/assemble`,
  `asset_manufacturing` — ~83 legacy products bypassed the verified-KR rule (P1 fix planned). (b) The
  book `/video` endpoint still emits a plan/package; product/trailer video (fulfillment engine) is the
  real MP4 path. (c) Master Design Standard Phase 2 (interior typography) & Phase 3 (Decoder bridge)
  pending. (d) Live-store EPUBs/covers still on ephemeral disk (Phase B: move to object storage).
