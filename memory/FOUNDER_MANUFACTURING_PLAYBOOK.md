# QRU Factory™ — Founder Manufacturing Playbook
_Audit date: 2026-06 · Method: live/preview inspection + code confirmation + safe cached-asset tests · No production changes made._

**Evidence labels used throughout:**
`✅ VERIFIED (LIVE/PREVIEW)` · `📄 CONFIRMED IN CODE` · `🟡 PARTIALLY VERIFIED` · `⛔ NOT IMPLEMENTED` · `❔ UNKNOWN — REQUIRES FOUNDER TEST`

---

## PART 1 — THE NINE QUALITY GATES (as implemented in `inspection_system.py`)

Weighting: **blocking** gates count double; a product's overall score is a weighted average. Threshold to "pass" a gate = a fixed score bar; the **Treasure Standard™** gate uses a higher bar.

| # | Gate (exact name) | Blocking? | What it checks (from code) | Pass looks like | Failure looks like |
|---|---|---|---|---|---|
| 1 | **Knowledge Completeness** | **BLOCKING** | KR/product content length ≥ minimum; references/citations attached | Score 100, content substantial + citations | "content is thin (N chars)" / "no references" |
| 2 | **Verification Completeness** | **BLOCKING** | KR `verification_status == "Verified"` (or product `verified`) | 100 | "record is 'Unverified' — only Verified records may manufacture" |
| 3 | **Educational Value** | non-blocking | Content depth, sections/examples, product family set | ≥ pass bar | "add depth: structured sections, examples, takeaways" |
| 4 | **Consumer Clarity** | non-blocking | Reviewed Creative brief + preview/marketing kit present | ≥ pass bar | "needs a reviewed Creative Studio™ brief" / "no preview" |
| 5 | **Visual Readiness** | non-blocking | Design Director™ score × cover present | ≥ pass bar | "no branded cover" / "Design Director score below bar" |
| 6 | **Product Eligibility** | **BLOCKING** | `product_type` set + complies with its recipe | recipe score ≥ bar | "product type not set" / "does not comply with recipe" |
| 7 | **Connector Readiness** | non-blocking | ≥1 operational publishing connector (QRU Store is always on) | 100 (Store always available) | "no operational connector" |
| 8 | **Publication Readiness** | **BLOCKING** | `publish_gate()` blockers cleared (pricing, authorization, assets) | 100 | lists specific blockers (e.g. not authorized, no price) |
| 9 | **Treasure Standard™ Compliance** | **BLOCKING** (higher bar) | Factory Confidence™ score — honesty/no-fake/quality composite | certified | "not yet certified (Factory Confidence N)" |

- **Where failures appear:** Quality Gates™ page `/inspection` (and inline on the product), each gate lists `findings`.
- **Can they be bypassed?** No user-facing bypass for blocking gates; publish is gated by `publish_gate()`. Override authority = **Founder / Super-Admin** only (governance).
- **Functional status:** ✅ VERIFIED — gates return real, per-product scores and enforce blocking (tested a live product: 95 overall, passed 8/9, **blocked** by Treasure Standard at 89).

### Gate routing matrix (which gates apply to which product families)
Legend: **R** Required · **C** Conditional · **N/A** Not applicable · **NI** Not implemented

| Product family | G1 Know. | G2 Verify | G3 Edu | G4 Clarity | G5 Visual | G6 Eligible | G7 Connector | G8 PubReady | G9 Treasure |
|---|---|---|---|---|---|---|---|---|---|
| Knowledge Record (pre-mfg) | R | R | C | N/A | N/A | R | N/A | N/A | C |
| Book (Founder-authored) | R | R | R | C | R | R | R | R | R |
| Document products (Workbook, Guides, Lesson Plan, Course, Quiz, Flash Cards, Poster text, Infographic, Presentation) | R | R | R | C | C | R | R | R | R |
| Cover / Poster (design) | C | C | N/A | C | **R** | R | R | R | R |
| Audio (audiobook/podcast) | R | R | C | C | C | R | R | R | R |
| Video (MP4/trailer/short/promo) | R | R | C | C | C | R | R | R | R |
| Motion storybook / animated episode | R | R | C | C | C | R | R | R | R (⛔ pipeline not built) |

> Note: The gate engine scores **products** and **knowledge records**. Cover/audio/video assets are governed indirectly (through their parent product + the Design Director/Publication gates); there is not yet a separate per-asset gate run for standalone media. `🟡 PARTIALLY VERIFIED`.

---

## PART 2 — PRODUCT INVENTORY (status · source · route · UKR-first?)

**Text/document products are manufactured on `Product Manufacturing` (`/manufacture`)** via `POST /api/products/generate`, using per-type **recipes** (`routers/products.py`). **Media (covers/posters/audio/video)** via the studios. **Books** via the dedicated 7-step line.

| Product | Status | Required source | Menu → Route | UKR-first? |
|---|---|---|---|---|
| **Book (Founder-authored)** | ✅ Proven end-to-end (artifacts + EPUB confirmed on "The Understanding Tree") | Manuscript / Founder-authored exception | Book Manufacturing™ → `/book-manufacturing` | Founder exception (no KR) |
| **eBook / EPUB** | ✅ Proven (EPUB generated in book design step; delivered via storefront) | Book record | Book Manufacturing™ → design/assemble → `/book-manufacturing` | Inherits from book |
| **PDF / Printable PDF** | 🟡 Partial (print-wrap + master package produce print files; "Printable PDF" listed but no dedicated recipe) | Book / KR | Book line (print-wrap) or `/manufacture` | Mixed |
| **Workbook** | 📄 Confirmed in code (recipe: activities, practice, reflection, quiz) | UKR/legacy KR | Product Manufacturing → `/manufacture` | KR-based |
| **Study/Teacher/Caregiver Guide** | 📄 Confirmed (recipe-backed) | UKR/legacy KR | `/manufacture` or Media & Design Studio `/media-division` | KR-based |
| **Lesson Plan** | 📄 Confirmed (recipe: lesson_plan, student_notes, practice) | UKR/legacy KR | `/manufacture` | KR-based |
| **Knowledge Card / Quick Card** | ⛔ Not a distinct type — closest implemented = **Flash Cards** | UKR/legacy KR | `/manufacture` → Flash Cards | KR-based |
| **Poster / Marketing asset** | ✅ Design proven (cover engine); poster *text* recipe confirmed | UKR/legacy KR + design | Poster Studio™ `/poster-studio` / Media & Design Studio | KR + design |
| **Cover** | ✅ VERIFIED (design_studio art direction → composed cover; tested a Poster product) | Product + KR/Decoder | Cover Studio™ `/cover-studio` / auto in Media & Design | KR/Decoder-informed |
| **Infographic / Presentation** | 📄 Confirmed (recipes) | UKR/legacy KR | `/manufacture` | KR-based |
| **Audio / Audiobook / Podcast episode** | ✅ Proven (real OpenAI TTS MP3 in `studio_productions`, e.g. `studio-audiobook-*.mp3`) | Verified KR (+ Voice) or Book | Podcast Studio™ → `/cinema-studio` | KR-based |
| **Video Script / YouTube Video Script** | 📄 Confirmed (recipe: video_script, story_version, CTA) — *text* product | UKR/legacy KR | `/manufacture` | KR-based |
| **Short Video / MP4 video** | ✅ VERIFIED (QRU Video Fulfillment™ renders real MP4 from script/KR; cached; durable object storage) | Script (product) or verified KR | Story & Cinema Studio™ `/cinema-studio`; YouTube Publisher `/youtube` | KR/script |
| **Book trailer** | ✅ VERIFIED (rendered from book; 4 trailers produced; queued for YouTube) | Founder-authored book | YouTube Publisher™ `/youtube` (Generate missing videos) | Book exception |
| **Motion storybook** | 🟡/⛔ Declared in FUTURE_CATALOG; image-based-motion shorts/promos work, but frame-by-frame "animated episode" **not implemented** | Verified KR | Story & Cinema Studio™ `/cinema-studio` | KR-based |
| **Short-form / Social content** | 📄 Confirmed (recipe: social_media_pack) | UKR/legacy KR | `/manufacture` | KR-based |
| **Course / Quiz / Certificate** | 📄 Confirmed (recipes) | UKR/legacy KR | `/manufacture` | KR-based |
| **Interactive Lesson / AI Tutor** | 🟡 Listed in PRODUCT_TYPES but **no recipe** → likely stub | KR | `/manufacture` | ❔ requires Founder test |

**Master product-type list (code-confirmed, `products.py`):** Book, Poster, Infographic, Presentation, Teacher Guide, Caregiver Guide, Workbook, Lesson Plan, Video Script, Podcast Script, Short-form Content, Interactive Lesson, AI Tutor, Course, Certificate, Flash Cards, Quiz, Printable PDF.
**Media & Design Studio catalog (`media_division.py`):** Book, Workbook, Teacher Guide, Parent/Family Guide, Classroom Slides, Lesson Plan, Learning Poster, Overview Poster, Video Script, Podcast Script, Social Clip Script.
**Studio-declared (FUTURE_CATALOG):** Audiobook, Video Podcast, Motion Storybook™, Animated Episode, YouTube Short, Promotional Video.

---

## PART 3 — FOUNDER WALKTHROUGHS

### PRODUCT: Knowledge-derived document product (Workbook / Guide / Lesson / Poster text / Course)
**Before you begin:** Source = a **Verified** Knowledge Record (UKR). Approval = Founder authorize at the end. Cost ≈ 1 LLM text generation (+ cover image gen if you add a cover). Output = a manufactured product with content + optional cover.
- **Step 1** — Menu: *Knowledge & Decoder™* (`/knowledge`) → confirm your KR exists and is **Verified** (or verify it at Verification Center `/verification`). Expected: status shows "Verified".
- **Step 2** — Menu: *All Capabilities* → *Product Manufacturing* (`/manufacture`). Action: choose **Product type** (e.g. Workbook) and select the **Knowledge Record**. Expected: the recipe fields for that type load.
- **Step 3** — Click **Generate** (`POST /api/products/generate`). Expected: content manufactured from the KR (never invented) per the recipe.
- **Step 4** — Review the content on *My Products* (`/products`).
- **Step 5** — (Optional design) open the product → generate/regenerate cover (routes through design_studio — book-grade).
- **Step 6** — Send through Quality Gates™ (`/inspection` → run on the product). Expected: G1,G2,G6,G8,G9 must pass (blocking).
- **Step 7** — Fix failures where they occur: thin content → re-generate; unverified KR → `/verification`; visual → cover; Treasure/publication → complete pricing + brief. Re-run the gate.
- **Step 8** — Authorize in *Founder Review Inbox™* (`/founder-inbox`), then publish (Part 4).
**Common mistakes:** manufacturing from an unverified KR (G2 blocks). **Recover:** verify the KR, re-generate. **Auto:** content + cover generation, gate scoring. **Should never repeat:** re-generating an unchanged product (it should be cached/stored).
_Status: recipe generation 📄 CONFIRMED IN CODE; gates ✅ VERIFIED; cover ✅ VERIFIED._

### PRODUCT: Book (Founder-authored) — flagship 7-step line
**Before you begin:** Source = your **manuscript** (Founder-authored exception, no KR required). Approval = authorize edition. Cost ≈ cover image gen + optional audio/video TTS/render. Output = print + EPUB + governance package.
- **Step 1** — *Book Manufacturing™* (`/book-manufacturing`). Click **Upload / New**, then **Manuscript** (`/manuscript` or `/upload-file`). Enter title + manuscript.
- **Step 2** — Click **Proof** (`/proof`). Review findings.
- **Step 3** — Click **Resolve finding** for each issue (`/resolve-finding`); or **Open revision** to edit.
- **Step 4** — Click **Design** (`/design`) → review **cover concepts** → **Select cover** (`/select-cover`).
- **Step 5** — (Optional) **Audio** (`/audio-prototype`, `/audio`) and **Video/trailer** (via YouTube Publisher). 
- **Step 6** — Click **Pricing** (`/pricing`, advisor `/pricing-advisor`) → set price.
- **Step 7** — Run **Quality Gates™** (`/inspection`) — all blocking gates must pass.
- **Step 8** — Click **Authorize** (`/authorize`) → **Publish** (`/publish`) → **Assemble master package** (`/assemble-package`) + **KDP checklist** (`/kdp-checklist`).
**Common mistakes:** publishing before authorize (G8 blocks). **Recover:** authorize, re-check. **Auto:** proof, cover concepts, EPUB/print build, packaging. **Should never repeat:** re-rendering the cover/EPUB once approved.
_Status: ✅ VERIFIED — "The Understanding Tree" carries full design (cover, print, ebook+EPUB, governance), audio, sanitization artifacts; live purchase delivered its EPUB._

### PRODUCT: Cover / Poster (design)
**Before you begin:** Source = the product + its KR/Decoder. Cost ≈ up to 3 concept image gens. Output = branded cover + thumbnail + store graphic.
- **Step 1** — *Media & Design Studio* (`/media-division`) or *Cover Studio™* (`/cover-studio`).
- **Step 2** — Select the product → **Generate cover** (routes through `design_studio` Master Design Standard™; auto-selects the strongest concept for non-book products).
- **Step 3** — Review; **regenerate** if desired (deterministic zero-AI fallback guarantees a cover always renders).
- **Step 4** — Gate: **Visual Readiness (G5)** + Design Director™ (`/design-director`).
_Status: ✅ VERIFIED (Poster product produced a 1.45MB art-directed hero cover via design_studio)._

### PRODUCT: Audio (Audiobook / Podcast episode)
**Before you begin:** Source = Verified KR (+ brand Voice) or a Book. Cost ≈ OpenAI TTS narration. Output = MP3.
- **Step 1** — *Podcast Studio™* (`/cinema-studio`).
- **Step 2** — Select the Verified KR / format → **Manufacture** (real OpenAI TTS).
- **Step 3** — Review the MP3; gate via Publication Readiness.
- **Step 4** — Distribute (Store / connectors).
_Status: ✅ VERIFIED existence of real audiobook MP3 (`studio-audiobook-*.mp3`) in `studio_productions`. ⚠️ Currently stored on local disk (not yet object storage) — see gaps._

### PRODUCT: Video / MP4 / Book trailer / Short
**Before you begin:** Source = a video-**script** product (uses the script), a verified KR, or a Founder-authored book (trailer). Cost ≈ 2–3 image gens + TTS per video. Output = MP4 (image-based motion + narration; honestly labeled).
- **Step 1** — *YouTube Publisher™* (`/youtube`) → **Generate missing videos** (background render, backfills trailers + script videos), **or** Story & Cinema Studio™ (`/cinema-studio`) for a specific render.
- **Step 2** — Wait for the progress to complete (runs in background; cached; durable object storage).
- **Step 3** — Select the video in **"Select a factory-owned video"**.
- **Step 4** — Publish to YouTube (requires the YouTube channel connected in `/connectors`).
**Auto:** render on publish/request, caching, durable storage. **Should never repeat:** re-rendering unchanged videos (fixed — cached + durable).
_Status: ✅ VERIFIED (render from script + trailer + durable-across-redeploy reuse). Actual YouTube upload ❔ requires connected channel._

### PRODUCT: Storefront publishing (QRU Online / QRU Store™ + Stripe)
- **Step 1** — Authorize the book/product.
- **Step 2** — QRU Store™ (`/store`) / storefront lists Founder-authorized items.
- **Step 3** — Customer buys via Stripe → webhook → order paid → secure EPUB download.
_Status: ✅ VERIFIED LIVE — real production purchase captured, order paid, EPUB delivered (1.6MB, valid application/epub+zip)._

---

## PART 4 — QUICK REFERENCE: "Which button do I press?"
| I want to… | Go to | Press |
|---|---|---|
| Capture/verify knowledge | Knowledge & Decoder™ `/knowledge` → `/kr-manufacturing` → `/verification` | Manufacture KR → Verify |
| Turn knowledge into understanding | QRU Decoder Engine™ `/decoder-engine` | Decode → approve on Shelf |
| Make a workbook/guide/poster/course | Product Manufacturing `/manufacture` | Select type + KR → **Generate** |
| Make/write a book | Book Manufacturing™ `/book-manufacturing` | Manuscript → Proof → Design → Select cover → Pricing → Authorize → Publish |
| Make a cover/poster art | Cover Studio™ `/cover-studio` / Media & Design `/media-division` | Generate cover |
| Make an audiobook/podcast | Podcast Studio™ `/cinema-studio` | Manufacture (TTS) |
| Make a video/trailer/short | YouTube Publisher™ `/youtube` | **Generate missing videos** → Publish |
| Check quality | Quality Gates™ `/inspection` | Run on product/KR |
| Approve | Founder Review Inbox™ `/founder-inbox` | Authorize |
| Sell it | QRU Store™ `/store` / storefront | Publish |

## Product-to-route map (primary path)
Book→`/book-manufacturing` · Document products→`/manufacture` · Cover→`/cover-studio` · Poster→`/poster-studio` · Audio→`/cinema-studio` · Video/trailer→`/youtube`+`/cinema-studio` · KR→`/kr-manufacturing` · Decoder→`/decoder-engine` · Quality→`/inspection` · Approve→`/founder-inbox` · Sell→`/store` · Full registry→`/factory-map`.

---

## PART 5 — GAPS & REDUNDANCIES (verified)
1. **UKR/Decoder not enforced** ⚠️ — `POST /products/generate` and assembly accept a `topic` with no verified KR; **62 of 226 products have no linked KR** (bypass the Knowledge-First chain). The 9 gates *score* verification but generation itself isn't blocked at the choke point. → **P1 UKR Governance Gap.**
2. **Ephemeral storage for audio/covers/EPUBs** ⚠️ — audio MP3s + covers live on local disk (wiped on redeploy). Videos are now durable (object storage); audio/covers/EPUBs are **not yet** → Phase B.
3. **Book `/video` endpoint = plan only** 🟡 — the real MP4 path is QRU Video Fulfillment™; the book-line video button still emits a package/plan. Menu label implies a video; function produces a manifest.
4. **Duplicate manufacturing paths** — document products can be made from both `/manufacture` and Media & Design Studio; several **legacy screens** duplicate live ones (Creative Studio, Visual/Media Studio, Manufacturing Studio/Command, Product Library, Enterprise Blueprint/Health, Command Console, Media Starter Kit, Experience Lab) — marked "consolidate."
5. **Motion storybook / animated episode** ⛔ — declared but frame-by-frame animation not implemented (only Ken Burns motion).
6. **Interactive Lesson / AI Tutor** 🟡 — listed as types but have **no recipe** (likely stubs).
7. **Gate ↔ media coupling** 🟡 — standalone media assets (audio/video) aren't individually gate-scored; governance is via the parent product.
8. **Manual steps that could be director-automated** — running the gate + authorizing are manual per product; the Manufacturing/Publishing Director could auto-route passing products to the Founder Inbox.

---

## PART 6 — RECOMMENDED NEXT ENGINEERING ACTION (highest leverage)
**Enforce the UKR/Decoder inheritance at the single manufacturing choke point** (`products.generate` / assemble): refuse to manufacture customer-facing content unless a **Verified KR** (or the Founder-authored book exception) is present, and **migrate the 62 bypassed products**. This is the highest-leverage move because it makes the constitutional "Knowledge-First" promise structurally true for *every* current and future product, closes the biggest trust gap, and directly protects content quality you flagged as high-impact. (Durable storage Phase B is the fast second.)
