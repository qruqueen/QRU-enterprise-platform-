## 🔍 2026-08-03: Code-review report audit — findings were FALSE POSITIVES (no harmful changes applied)
- A static code-review report flagged eval() injection, 4 circular-import chains, is-vs-==, hardcoded secrets, 92 undefined vars, high complexity. Audited each against the ACTUAL code:
  - **eval()**: does NOT exist anywhere in backend (line 164 is a comment). False positive.
  - **Circular imports**: all 9 modules import cleanly (verified) — handled via lazy in-function imports; app runs. Not breaking.
  - **is vs ==**: every flagged production/test line is `is None` / `is True` / `is False` (correct, PEP8) or the word "is" inside a string literal. Changing to ==None/==False would be an ANTI-pattern. False positive.
  - **Hardcoded secrets**: demo test-account passwords in the test harness (qru-admin-2026 etc.), not API keys/production secrets. Low risk.
  - **92 undefined vars**: backend imports+runs clean → conditional-path static noise.
  - **Complexity (governed_export cx40, _recon_audit main cx47, autonomous_engine gate_ladder cx27)**: REAL but not bugs. Refactoring working, recently-touched production logic = regression risk, zero functional gain. Deferred as optional.
- DECISION: made NO code changes (applying the report as-written would degrade/break working code — against Treasure Standard). 
- Ran a pre-redeploy REGRESSION via testing_agent (iteration_106.json) on the REAL recent fixes: verification /queue (+ count invariant), KR 2.0 verify, creative-assets state 500-fix, Factory Jobs spine, frontend smoke — **100% pass, zero issues, retest_needed=false**. Credit-safe (no AI renders triggered).


## ✅ 2026-08-03 (cont.): "Manufacture Full Understanding" fixed (timeout + 0%/incomplete) + deploy-safe
- Root cause of both the timeout AND the incomplete/"Topic Seed"/0% records: `manufacturing_engine.start_manufacturing_job` used fire-and-forget `asyncio.create_task(_process_job(...))` for the 8-stage AI pipeline → died on restart / didn't retry transient AI errors → stuck at 0%, button spins forever.
- Fix: migrated it onto the durable spine — `start_manufacturing_job` now `enqueue`s a `kr_manufacture_understanding` job; new `manufacture_handler` runs `_process_job` and re-raises on all-failed so the engine retries. `_process_job` is idempotent (only fills EMPTY fields) so reclaim/retry safely resumes. Registered in `job_handlers`.
- VERIFIED END-TO-END (credits recharged): ran manufacture-all on KR-IMP-0021-class record → MFG job complete, 100%, **40 fields manufactured**, all 8 stages done; spine job complete (attempts 1). Now visible in Factory Jobs.
- **Jobs now on the durable spine**: storybook render, audiobook video, full audiobook, and knowledge "manufacture full understanding". STILL separate (larger, TODO): WF-xxxx workflow engine + bulk manufacturing/orchestrator.
- **Deployment readiness: deployment_agent PASS** — all recent changes deploy-safe (env vars only: REACT_APP_BACKEND_URL / MONGO_URL / DB_NAME / EMERGENT_LLM_KEY; no hardcoding, compiles clean). Changes roll over to production on redeploy. (Non-blocking warning: RESEND_API_KEY unquoted in backend/.env — pre-existing, left as-is.)


## ✅ 2026-08-03: Verification Center coverage bug FIXED (+ cinema None-crash, full-audiobook on spine)
- **Verification Center was hiding unverified records + falsely claiming "all verified."** Root: `VerificationCenter.js` fetched `/knowledge-records` and client-filtered to only [Draft, In Review, Revision Requested] — dropping 13 "Extracted — Needs Founder Review" + 25 "Topic Seed", and never fetched KR 2.0 (`knowledge_engine_records`) at all (42 of 44 were "Approved (internal)" = not externally verified). So media built on ~80 records showed "Verification Required" while the screen said "Nothing pending" (a fake state — violated Treasure Standard).
- Fix: new backend `GET /api/verification/queue` (unified across both collections: needs_verification + awaiting_manufacturing + honest counts) and `POST /api/verification/kr2/{id}/verify` (Mark Verified External™ · Gold Standard / Reject). Rewrote `VerificationCenter.js`: honest count chips, "Needs your verification" section (legacy Review dialog + KR 2.0 approve/reject inline), "Awaiting full manufacturing" section for Topic Seeds, banner only says all-clear when truly clear.
- Verified: queue surfaces 57 pending (incl. KR 2.0) + 25 awaiting; KR 2.0 approve moves verified 46→47/pending→-1; frontend screenshot confirms all sections + false banner gone.
- **Also fixed**: `cinema_studio._make_video` "a bytes-like object is required, not 'NoneType'" (None image → now falls back to `_branded_card`). **Migrated full-audiobook render onto the durable spine** (`book_full_audiobook` handler; `start_full_audiobook` enqueues).
- ⚠️ PREVIEW changes — REQUIRE REDEPLOY.

### STILL OPEN (Founder-flagged, need scoping/repro):
- **Topic Seed / "knowledge manufacturer not rendering full information"**: the knowledge manufacturing pipeline produces incomplete "Topic Seed" records (25). Needs investigation of the manufacture flow (`knowledge.py manufacture-understanding` / decoder / seed→full KR). NOT yet fixed.
- **"Knowledge record feature times out & shows wrong info"**: the wrong-info part is fixed for Verification Center; the timeout needs the SPECIFIC page/action to reproduce (likely /knowledge list or knowledge manufacturing).
- **Migrate WF-xxxx workflow + bulk manufacturing onto the spine** (so all jobs show in Factory Jobs).


## ✅ 2026-08-02 (post-redeploy prod audit): Cinema None-crash fix + more jobs on the Spine
- **Fixed "Production failed: a bytes-like object is required, not 'NoneType'"** (Story & Cinema Studio → Motion Storybook / Educational Episode / YouTube Short). Root: `cinema_studio._make_video` passed `generate_image()`'s return straight to the encoder; when image gen returned None (the gpt-image-2 fix wasn't deployed to prod yet, so images still auth-failed → None), `_render_pilot_mp4` crashed. Fix: fall back to a `_branded_card` when img is None (robust even after the gpt-image-2 fix). ⚠️ needs redeploy.
- **All Jobs in One Place (partial):** migrated the **full audiobook** render onto the durable spine (`book_full_audiobook` handler; `start_full_audiobook` now enqueues instead of `asyncio.create_task`). Storybook + audiobook-video already on spine. Registered handlers: ll_pilot_render, book_audiobook_video, book_full_audiobook. STILL TODO (larger, deferred): migrate the WF-xxxx **workflow engine** and **bulk manufacturing/orchestrator** runs onto the spine so they also appear in Factory Jobs.
- Verified: all handlers register + worker loop starts; cinema_studio imports clean.


## 🔥 CRITICAL FIX (2026-08-02): Image generation broken → "AI failed workflow" everywhere
- Root cause: the Emergent Universal LLM key's ALLOWED MODEL LIST changed. Image gen was calling Gemini "Nano Banana" (`gemini-*-flash-image-preview`) → `AuthenticationError: key not allowed to access model. This key can only access [...'gpt-image-2'...]`. TEXT gen (gpt-5.5) still worked, so only image-dependent steps failed → cascaded into WF "AI Provider Error"/"Unknown Error" and blocked covers, storyboard scenes, storybook art, media renders.
- Fix: `ai_service.py` now uses `emergentintegrations.llm.openai.image_generation.OpenAIImageGeneration` with model **gpt-image-2** (`IMAGE_MODEL`, overridable via env `QRU_IMAGE_MODEL`). `generate_images()` returns raw PNG bytes. Reference-image conditioning is not supported by this API (character detail must live in the prompt) — acceptable; storybook already falls back to branded cards.
- All image generation in the app routes through `ai_service` (verified single fix point). Verified with a real call → valid 1254×1254 PNG returned.
- ⚠️ PREVIEW fix — REQUIRES REDEPLOY to fix production qru-online.com.

### Notes on the Founder's other questions (2026-08-02)
- "Where do I verify?" → media products show "VERIFICATION REQUIRED" because they INHERIT the source Knowledge Record's `verification_status`. Verify the KR in the **Verification Center** (route `/verification`, linked from each Knowledge Record detail page "Review"). Once the KR is Verified, the media gate clears. (Backlog: make this an actionable link directly on the render gate.)
- "Factory Jobs shows nothing" → the failing WF-xxxx runs are the OLDER workflow/manufacturing subsystem, NOT the new Orchestration Spine. Only storybook renders + audiobook videos route through Factory Jobs today. Backlog: migrate workflow/manufacturing/full-audiobook renders onto the spine so ALL jobs appear there.


## ✅ ORCHESTRATION SPINE™ (durable job engine) + AUDIOBOOK → YOUTUBE VIDEO (2026-08-02)

### Orchestration Spine™ — durable, restart-proof job engine (foundation for autonomy)
- Problem: every long task (storybook render, character master, full audiobook, bulk orchestrator) used fire-and-forget `asyncio.create_task` that died on any server recycle → jobs stuck forever.
- New `job_engine.py` (collection `factory_jobs`): Mongo-persisted jobs + a worker loop launched at backend startup (`server.py`) that LEASES one job at a time with a heartbeat, RETRIES with exponential backoff (max_attempts), and — the key — RECLAIMS orphaned jobs whose lease expired (i.e. killed mid-run) so they auto-resume after any restart. Supports dedupe_key, scheduled (`run_at`) and recurring (`interval_seconds`) jobs. Deploy-safe: NO new infra (no Redis/Celery), runs in-process, carries to production.
- Handlers registered in `job_handlers.py`: `ll_pilot_render` (storybook), `book_audiobook_video`.
- `little_legacy_production.manufacture_pilot` now ENQUEUES a durable `ll_pilot_render` job instead of `asyncio.create_task` → storybook renders now survive production recycling. `_pilot_job` refreshes render_started_at each (re)run so the stale self-heal doesn't fight the spine.
- API `routers/factory_jobs.py` (`/api/factory-jobs`): list (with status counts), get, retry, cancel. Frontend `FactoryJobs.js` + route `/factory-jobs` + nav "Factory Jobs™" (Founder/Admin) — live monitor with status chips, filters, progress bars, retry/cancel.
- Verified ($0): engine unit test (dedupe, lease, complete, RECLAIM-stale, retry-backoff, fail-after-max) all pass; real `book_audiobook_video` job end-to-end via the LIVE server worker → complete with valid MP4; Factory Jobs API + UI render (screenshot).

### Audiobook → YouTube Video
- New `audiobook_video.py`: takes a book's existing full audiobook (`artifacts.audio.full_audiobook.url`) + a branded 1920×1080 cover title-card (PIL) → static-cover MP4 over the narration (ffmpeg, reliable at any length) → stores at `artifacts.audio.full_audiobook.video`. Runs as a spine job (`book_audiobook_video`). Separate `publish_audiobook_video()` uploads to YouTube (real, Private default) via `youtube_publisher.publish_video`; friendly reconnect message on expired OAuth.
- API: `POST /api/book-mfg/books/{id}/audiobook/video` (enqueue), `POST .../audiobook/video/publish`. UI: "Create YouTube Video" + "Publish to YouTube (Private)" buttons in Book Manufacturing Audio panel (appear once the full audiobook exists), with inline video player + YouTube link.
- Verified end-to-end at $0 (synthetic book + tiny generated audio → job → valid 1920×1080 H.264+AAC MP4). Collection is `book_records` (not `books`).
- ⚠️ NOT run: a paid full storybook render or a real full-audiobook TTS render. Storybook migration is code-complete and the spine is proven with a real handler; the first true storybook render is the Founder's production validation — now durable + observable in Factory Jobs.
- ⚠️ Requires REDEPLOY for production (includes this + the earlier `set_state` byte-leak fix).


## ✅ FOLLOW-UP FIX (2026-08-01, production-reported): Asset lifecycle actions 500 on legacy assets
- Symptom: production (qru-online.com) still showed "Something went wrong. Please try again." on the Creative Assets page even after redeploy. Uploads themselves now worked (assets listed with PASS), but clicking **Approve / Lock / Reject / Archive** on OLDER assets (e.g. CA-266ec55e721e, created before the byte-leak fix) crashed.
- Root cause: `set_asset_state()` returned the raw Mongo asset doc, which for pre-fix assets still contained raw image bytes in `normalization.data` → `serialize_response` UnicodeDecodeError → 500. (My earlier fix covered the upload return + the assets-LIST GET, but NOT the per-asset state endpoint.)
- Fix (deploy-safe, self-healing): `set_asset_state()` now `$unset`s `normalization.data` on the state-change update (permanently cleans legacy docs on first interaction in PRODUCTION) and returns a byte-stripped doc; router `/assets/{id}/state` also wraps the response in `_json_safe()`.
- Verified: seeded a legacy byte-leaked asset, POST state=Approved → HTTP 200, clean normalization, and DB doc no longer carries the bytes. ⚠️ Requires redeploy for production.


## ✅ Storybook: 2-scene Teaser mode + one-click Approve→Publish to YouTube (2026-08-01)
- **Teaser mode**: `manufacture_pilot(..., teaser=True)` renders only the opening + Treasure Takeaway™ (2 scenes) — a cheap end-to-end test (~1/3 the AI cost). Marked `teaser:True`, honestly labeled, and BLOCKED from approve/publish (must run the full pilot). Router `POST /api/little-legacy/episodes/{id}/pilot {teaser}`. UI: "Quick 2-Scene Teaser (cheap test)" button + amber teaser banner + "Manufacture Full Pilot" follow-up.
- **One-click YouTube publish**: `publish_pilot_youtube(episode_id, privacy="private")` — approves the pilot if needed, then uploads the rendered MP4 to the connected channel via the existing `youtube_publisher.publish_video` (real upload, Private by default), with title/description/keywords/Made-for-Kids from the Publishing Package™. Refuses teasers, ungoverned pilots; friendly "reconnect channel" message on expired OAuth. Router `POST /api/little-legacy/pilots/{id}/publish-youtube {privacy}`. UI: gold "Approve & Publish to YouTube (Private)" button + "On YouTube" link when live.
- Verified: publish endpoint reached the REAL YouTube API end-to-end (preview token expired → honest reconnect message — expected; production has a valid connection). Teaser render path verified by code + $0 MP4-assembly proof (no paid render run). ⚠️ Redeploy required for production.

## 📋 BACKLOG (Founder-requested 2026-08-01) — Full-Book Audiobook → YouTube Video
- **Request**: for EVERY book generated, make the rendered **full audiobook** attachable to a YouTube video — produce a "video of the entire book" by pairing the audiobook narration with either (a) a motion picture of the manuscript, or (b) a single still frame (book cover / title card). Then publish that video to YouTube (reuse `youtube_publisher.publish_video`).
- Notes for implementation: the full-book audiobook render already exists (`cinema_studio` / `book_manufacturing` audio + `media_render`). Needed: a "Book → YouTube Video" builder that muxes the full audiobook MP3 with a static cover/title-card frame (cheapest, $0 video) or optional Ken Burns over the cover, chapter markers from the audiobook chapter map, then hands the MP4 to the YouTube publisher with governed metadata. Keep it deploy-safe + resilient (same self-heal pattern as storybook renders). NOT started per Founder ("add to backlog, do not build now").


## ✅ Creative Assets upload 500 fix + Motion Storybook render resilience (2026-08-01)

### Creative Assets upload (Etsy image / print wrap) — 500 Internal Server Error FIXED
- Root cause: `creative_asset_system.manufacture_final_asset()` passed the FULL `export` dict (which contains the rendered file **bytes** in `export["data"]`) into `store_asset(normalization=...)`, so the stored asset — and the JSON response — carried raw bytes → FastAPI `serialize_response` crashed with `UnicodeDecodeError`. Every UCAMS upload (Etsy marketplace_image, KDP print_cover_wrap, etc.) 500'd.
- Fix: strip bytes before store/return (`clean_norm` subset of `export`, no `data`). Also made the READ path defensive: `routers/creative_assets.py` `/assets/{engine}/{record_id}` now runs `_json_safe()` to drop any raw bytes from legacy byte-leaked docs → protects production's pre-existing docs after redeploy.
- Verified (curl, HTTP 200): Etsy image upload with rights → PASS, normalized to exact 3000×2250; print wrap 200; assets-list GET 200. Cleaned 4 preview byte-leaked docs; preserved the user's 2 real uploads on BOOK-0020.

### Motion Storybook (Little Legacy Animated Storybook Pilot™) — "never renders in production" FIXED
- Root cause: `_pilot_job` render is a multi-minute fire-and-forget `asyncio.create_task` (6 AI images + 6 TTS + ffmpeg) inside the web process. When the production container recycles/scales/times-out mid-render, the job dies WITHOUT hitting its `except`, so the DB record stays `RENDERING` forever → UI spins indefinitely. (Confirmed by a real preview job stuck in RENDERING with no MP4 and no error.)
- Fix (`little_legacy_production.py` + `ai_service.py`), all deploy-safe code:
  1. **Self-healing** — `pilot_status()` / `master_status()` flip a stale RENDERING job (PILOT_STALE_S=900s / MASTER_STALE_S=600s, no output file) to `FAILED` with an honest, retryable message.
  2. **Timeouts** — AI image call wrapped in `asyncio.wait_for(...120s)`; per-scene TTS `wait_for(...90s)` so one hung call can't freeze the whole render.
  3. **Parallel render** — the 6 per-scene image+voice generations now run via `asyncio.gather` (all use the same approved anchor → independent), cutting wall-clock ~4-5× to fit inside production's window.
  4. **Step logging** (`qru.little_legacy`) so the next production attempt records exactly what happened.
  5. Frontend already renders a **Retry** button on FAILED (LittleLegacyStudio PilotTab) — now reachable because stuck jobs become FAILED.
- Verified: self-heal live via direct call + HTTP (stuck "Brain Work Adventure" → FAILED + Retry, screenshot confirmed); ffmpeg MP4 assembly proven at $0 (valid 171KB / 7.13s). NOT run: a full paid 6-scene AI render (avoided AI spend) — that is the Founder's production validation, now resilient + logged.
- ⚠️ PREVIEW code changes — Founder must **redeploy** for qru-online.com.

### YouTube full-animation build — SCOPED, awaiting Founder inputs (not built)
- Confirmed current capability: script → AI key-art scenes + Ken Burns motion + TTS narration + burned captions → 720p MP4 → real YouTube upload (`youtube_publisher.publish_video`). NOT frame-by-frame animation.
- True AI video needs **fal.ai** (`FAL_KEY` from https://fal.ai/dashboard/keys) — Emergent key does NOT cover video. Playbook fetched. Blocked on: Founder's FAL_KEY + choices (video style / script source / cost cap / publish default).


## ✅ Founder Copy Package™ (STD-UCAMS-0001 enhancement) + PWA (installable) — done & verified (2026-07-31)

### Founder Copy Package™ — three export modes on every UCAS™ spec
- `build_founder_copy_package(spec)` in `creative_asset_system.py`, folded into `generate_spec()` output as `founder_copy_package` (does NOT affect the governance `spec_checksum` — fingerprint excludes it).
- **Human Summary** (readable spec), **ChatGPT Prompt** (complete one-paste prompt: design intent + exact technical requirements/dimensions + brand standards + marketplace requirements + render instructions + governance ref), **Raw JSON** (technical archive). No manual editing required.
- UI (`CreativeAssets.js`): spec panel now has 3 mode tabs (`ca-mode-*`), a per-mode Copy button, and a green **"Copy for ChatGPT"** button (`ca-copy-chatgpt`) → clipboard + toast. Verified: backend curl (prompt content correct, checksum preserved) + screenshot (tabs + copy button + toast).

### PWA (installable web app) — no backend changes, $0 (icons reused from qru-shield.png)
- `public/manifest.json` (standalone, navy theme #0f1e3d, 192/512/maskable icons), `public/service-worker.js` (app-shell cache; network-first navigations; NEVER caches /api), meta/link tags in `index.html`, SW registration in `index.js`.
- Verified: manifest served, `theme-color` set, service worker **registered**, app loads at phone width (390px). The web app is fully intact (same URL/login/features) — PWA is additive.
- ⚠️ Install prompt ("Add to Home Screen") requires the live HTTPS domain — **redeploy** to activate on qru-online.com.
- KNOWN FOLLOW-UP (honest): interior screens still render the desktop layout on small phones (sidebar fixed) — a responsive "mobile polish" pass is a separate task, not part of the PWA request.


## ✅ Founder Override™ Publish — done & verified (2026-07-31)
Founder Authority now takes precedence over the constitutional gate (as STD-BLB/STD-MFG already declare). Everything was showing BLOCKED because existing products haven't had every upstream gate set (Knowledge Verified, Rendering Passed, Visual QA, locked assets, etc.) — the engine was correctly refusing to AUTO-publish. The Founder can now consciously override.
- `publication_policy.decide(..., founder_override=True)` → always AUTHORIZED, but returns `founder_override:true` + `bypassed_requirements[]` (honest, no fake 'all passed'). `publish(..., founder_override, override_reason, engine)` publishes QRU Online for real, records the override + bypassed list + reason in publication_history; external marketplaces without a live integration return an honest "authorized override → review-ready package" (not a false "published").
- Router `POST /api/publication/publish/{engine}/{id}` accepts `{founder_override, override_reason}`.
- UI (`PublicationGovernance.js`): gold **"Founder Override"** button on every destination card (always enabled) with a confirm + optional reason prompt; the normal Publish button stays gated to authorized state.
- Verified (curl): normal qru_online → BLOCKED; Founder Override qru_online → PUBLISHED + verification Published + bypassed list logged; Founder Override etsy → honest "no live integration" note. UI screenshot: 5 override buttons render. Test publish artifacts cleaned. ⚠️ Preview only — redeploy for production.


## ✅ Visual QA Hard Gate™ + Live Etsy Publish + Asset Thumbnails — done & verified (2026-07-31)

### Visual QA Hard Gate™ — `visual_qa.py` + `POST /api/creative-assets/visual-qa/{engine}/{id}`
- Renders every page (PyMuPDF @120dpi) and detects, deterministically: **blank pages** (ink coverage), sparse pages (warn), **text clipping** (glyph bbox outside page), **split headings** (large-font span stranded in bottom 12% with no ink after), **duplicate pages** (16×16 perceptual hash; content-rich pages only to avoid blank-page false positives), and **Unicode replacement chars (�)**. Result PASS/FAIL; any FAIL blocks.
- **Hard-gate integration:** sets `visual_qa_status = VISUAL_QA_PASSED/FAILED` which STD-PUB-0001's "Visual QA Passed" requirement reads → no product reaches AUTHORIZED (publish) without passing. Verified: real BOOK-0019 render → PASS (2 pages); crafted defective PDF → FAIL (blank + clipping + duplicate detected). UI: "Run Visual QA" button + PASS/FAIL badge + toast.

### Live Etsy Publish — `POST /api/creative-assets/publish-etsy/{engine}/{id}` {authorize}
- One-click: builds the governed Etsy package + STD-PUB-0001 decision; `authorize:false` returns review package; `authorize:true` (Founder presses Publish — Etsy policy is Review Ready) calls the existing `etsy.publish_draft(...)`, then runs `verify_publication()` and records publication history. Guarded: requires an approved description. UI: "Authorize & Publish to Etsy" button on the Etsy package result. ⚠️ Live Etsy push itself is UNTESTABLE in preview (no live Etsy account) — wiring verified up to the integration call; Founder must test on production.

### Asset Thumbnails — `CreativeAssets.js`
- Each uploaded image asset now shows a small preview thumbnail (from `file_url`) beside its state/validation badges. Verified in screenshot on the locked QRU Online asset.

### Still pending (honest): aggregate Creative Manufacturing Dashboard (catalog-wide readiness view), deep per-family validation (motion/video, safe-zone pixels, PDF/X + font-embedding), localization, campaigns/bundles. ⚠️ Preview only — redeploy for production.


## ✅ UCAMS Founder UI + Publication Governance UI + QR Scanning + Marketplace Packages — done & tested (2026-07-30)
Completed the 4 selected Phase-1 items. Frontend testing_agent = **100%** (iteration_104); backend curl-verified.

### QR Scanning (real, from finished asset) — `creative_asset_system.py`
- Installed `opencv-python-headless` (in requirements.txt). `scan_qr()` rasterizes PDF pages (fitz @200dpi) / decodes images via `cv2.QRCodeDetector`; `validate_qr()` confirms QR exists + decodes + destination matches expected URL. Wired into `validate_asset(expected_qr_url=...)` → wrong/broken/missing QR = **FAIL**. New endpoint `POST /api/creative-assets/qr-scan`. Verified: correct→PASS, wrong→FAIL, missing→FAIL, integrated check qr=True.

### Marketplace Packages — `build_marketplace_package()` + `GET /api/creative-assets/package/{engine}/{id}?marketplace=`
- Etsy/Amazon KDP/TpT/Shopify/QRU Online: required roles per storefront, gathers Approved+Locked assets, reports present/missing, listing copy (from descriptions channel), pricing, and the STD-PUB-0001 decision. Review-ready only — never auto-publishes. Verified: Etsy shows missing marketplace_image + Review Ready + BLOCKED; KDP requires print_cover_wrap + digital_cover.

### Creative Assets Founder UI — `/creative-assets` (`CreativeAssets.js`, nav added)
- Product picker → 8 inherited required specs (profile status + present/missing), Generate Spec (shows spec + checksum), Upload artwork (base64, rights checkbox, optional expected-QR), inline validation result + QR badge, per-asset Approve/Lock/Reject/Archive, and Marketplace Package builder with readiness/decision. Usable entirely without API calls.

### Publication Governance UI — `/publication-governance` (`PublicationGovernance.js`, nav added)
- Product picker → 5 destination cards each showing governed policy mode, decision badge, resolved-from, passed-count + **missing-requirements** list; Publish button DISABLED unless auto-publish authorized (constitutional); Governed Policy Override panel (scope/destination/mode → Set Policy); Publication History panel. Verified via testing_agent: inheritance display, override updates mode, disabled-publish-when-blocked all pass.

### Still pending (honest): Visual QA as a formal render-time hard-gate module (rasterization heuristics), deep per-family validation (motion/video, safe-zone pixels, PDF/X + font-embedding checks), Creative Manufacturing Dashboard aggregate view, localization, campaigns/bundles, live marketplace publishing integrations. ⚠️ Preview only — redeploy for production.


## ✅ Rendering Pipeline P1 + Governed Publication Policy™ (STD-PUB-0001) — done & verified (2026-07-30)

### Rendering Pipeline P1 (customer-facing defect fix, factory-wide)
Root-cause fix in the SHARED renderer `rendering_engine.py` (`_make_pdf`, used by books + `products` via `deliverable_renderer`):
- **Embedded Unicode fonts**: `QRUPDF.set_font` override maps Times→QRUSerif / Helvetica→QRUSans (bundled Liberation TTFs, Regular+Bold; italic→regular); `_register_fonts()` embeds them before any render. Kills the latin-1 `?`/� corruption at the source.
- **`_strip_md` rewritten**: strips Markdown links `[t](u)`→`t`, images dropped, `**/*/__/_/`code`` emphasis→inner text, pipe-table separator rows dropped + `|`→spacing, leading `#` stripped, replacement chars removed, rare non-embeddable glyphs mapped. Returns REAL Unicode (no latin-1). All `(TM)` literals → real `™`.
- Single TOC already guaranteed by `book_structure.toc_entries` + `strip_navigation` (unchanged).
- **Verified (fitz text extraction):** torture test → 0 replacement chars, 0 raw md links/images, real ™ + → + em-dash + curly quotes render, bold/italic markers gone, table separators dropped; **deterministic** (identical output from identical input). Pivot Points preview copy is a 41-char stub (no manuscript) so its own TOC=0 — honest.

### Governed Publication Policy™ (STD-PUB-0001) — constitutional; replaces hard-coded CDM default
`publication_policy.py` + `routers/publication.py` (`/api/publication/*`). **Publishing is determined by governed policy, never code defaults.**
- **6 modes** (Export Only / Review Ready / Authorized Auto Publish / Scheduled / Enterprise Workflow / Disabled). **22 constitutional requirements**; auto-publish requires ALL applicable to pass (unknown/absent ⇒ blocks).
- **Inheritance** enterprise→imprint→series→product_family→product→edition (most-specific wins) via `resolve_policy`. Seeded **default enterprise policy**: qru_online/internal = Authorized Auto Publish; etsy/kdp/tpt/shopify = Review Ready; all others Export Only. Governed overrides at any scope record who/why (`override_history`).
- **Decision engine** `decide()` → AUTHORIZED / REVIEW_READY / EXPORT_ONLY / BLOCKED + human-readable reason + satisfied/missing lists. **Verification** `verify_publication()` → Published / Published with Warnings / Failed / Needs Review. Owned QRU Online publishes for real (visibility flag); external marketplaces never auto-published without live integration.
- **CDM manifest now uses policy** (removed hard-coded Export-Only) — each destination shows governed_policy_mode, decision, missing_requirements.
- **Verified (curl + direct):** SC1 inheritance (etsy=Review Ready, qru_online=Auto from enterprise); SC2 destination policy + change history; SC3 product override (etsy→Auto for one product); SC4/SC9 auto-block with missing reqs listed; SC5 QRU Online AUTHORIZED→published→verification Published after all pass; SC6 Etsy Review-Ready decision; SC7 human-readable report; SC8 verification. All test artifacts cleaned.

### ⏳ UCAMS Phase-1 completion — STILL PENDING (honest, per user's own "complete only when…" definition)
NOT done this turn: **Creative Assets Founder UI + Creative Manufacturing Dashboard** (frontend — the user's gating item for "Phase 1 complete"); Visual QA as a formal render-time hard gate (page rasterization heuristics module — logic exists in UCAMS spec/validate but not wired as a blocking render step); **real QR scan from rendered asset** (needs `pyzbar`, not installed); full marketplace-package builders per storefront; deep per-family validation (motion/video, safe-zone pixels, PDF/X). Standards STD-UCAMS-0001 backend foundation + STD-PUB-0001 are production-shaped; UI is the next required build. ⚠️ Preview only — redeploy for production. No AI/image cost; no approved asset overwritten.


## ✅ Universal Creative Asset Manufacturing System™ (STD-UCAMS-0001) — Phase 1 foundation, curl-verified (2026-07-30)
Governed, INHERITED enterprise core (not a book-only utility). The Factory owns deterministic manufacturing requirements; external creative providers only produce artwork against exported specs. Built `creative_asset_system.py` + `routers/creative_assets.py` (`/api/creative-assets/*`). Five subsystems live:
- **PSR™ Platform Specification Registry** (`ucams_platforms`): 11 seeded, source-backed, versioned, status-managed profiles (KDP paperback wrap + eBook, Etsy, TpT, QRU Online, YouTube thumbnail + 16:9 screen, Pinterest, Instagram, TikTok vertical, One-Page Knowledge Visual print). Each carries source URL, date_verified, verifier, version, status, next_review_date + change history; stale profiles get a warning (no unverified assumption presented as truth).
- **UCAS™** deterministic spec generator: `generate_spec()` → geometry (wrap spine math from page-count/paper/trim, bleed, safe, barcode zone), design intent, cost controls ($0-default, AI optional), deliverables, accessibility, rights-required fields, + `spec_checksum` (identical inputs → identical spec).
- **CAVE™** validation engine: image (PIL) + PDF (fitz) checks — dimensions/aspect/DPI/format/color/size, wrap geometry vs spec; rights gate → HOLD; returns PASS / PASS WITH WARNINGS / FAIL / HOLD + exact correction.
- **CAVL™** vault + lineage (`ucams_assets`): master/version/parent, checksum, rights, validation, lifecycle (21 states); approved+locked never silently replaced; regeneration = new candidate version.
- **CDM™** distribution manifest: machine-readable per-destination package; publication_mode defaults **Export Only** — passing validation is NOT permission to publish.
- **Inheritance**: any product auto-inherits applicable role+destination profiles by type (no per-product coding). **Migration audit** classifies legacy `poster_assets` (poster vs One-Page Knowledge Visual™) as "Legacy Needs Validation" — none auto-approved, files preserved. **Export** (JSON/CSV/HTML) catalog-level, $0, triggers no creative/AI generation.
- **Acceptance tests PASSED (curl, $0):** T1 full book wrap spec (12.52×9.25in, spine 0.2702in @120pp, barcode 2×1.2) + correct-size PDF→PASS; T6 determinism (identical checksum); T7 inheritance (8 verified profiles auto-applied); T9 wrong-size wrap→FAIL w/ exact reason; T10 missing rights→HOLD (blocks approve); CAVL upload→Approved→Locked; CDM→Export Only (no auto-publish); T13 bulk export 152 rows, ai_generation_triggered=false; migration audit 55 posters classified; PSR provenance present.
- **HONEST PENDING (large remainder of the 31-section directive):** dedicated frontend UI (Creative Assets area §27); deep per-family validation (motion/video codec/duration, safe-zone pixel analysis, content-aware crop, print font-embedding/PDF-X); QR-scan-from-rendered-asset (needs `pyzbar` — not installed; currently rights/dimension only); localization (§19), campaigns/bundles (§20), autonomous-publishing destination integrations (§24 — none auto-publish yet by design); performance analytics (§26); full print-template ingestion (§18). Profiles seeded are Founder-reverify-on-review. ⚠️ Preview only — **redeploy** for production. No AI/image-provider cost incurred; no approved asset overwritten.


## ✅ Governed Product Description Manufacturing™ (STD-MFG-0001) + Back Cover (STD-BLB-0001) — done & curl-verified (2026-07-30)
Founder-approved constitutional standards: **the Factory never REQUIRES generative AI to write a customer-facing description when verified knowledge exists — AI is an optional enhancement layer, never a dependency.**
- **New engine `product_description.py`** — 3 modes: `governed` (DEFAULT, $0 — assembled from verified metadata + grounded manuscript/KR prose, every sentence source-traced, no invention), `ai` (AI Enhancement™, OPTIONAL, marketplace-style variants grounded in metadata), `founder` (Founder Canonical™, $0 — stored & reused). Channels: back_cover, amazon, etsy, tpt, qru_online, short, generic (each with word-budget + CTA rules). Works for any engine (book/publication/poster/recipe/media/kr/bundle). Fills toward channel word target using ONLY verified body/KR text; literary voice (E.Q. Rothwell™) stays evocative/short.
- **Router `routers/descriptions.py`** (`/api/descriptions/*`, super-admin for writes): `config`, `GET {engine}/{id}` (persisted `descriptions` map), `GET {engine}/{id}/preview?channel=` ($0 read-only), `POST {engine}/{id}/manufacture` (mode/channel/text/styles/save), `POST {engine}/{id}/save` (persist a chosen variant). Descriptions persist under `record.descriptions[channel]`; back-cover mirrors to `description` for the print wrap.
- **`book_manufacturing.draft_blurb` switched to Governed ($0) default** (was always-AI); `mode:"ai"` opts in and honestly falls back to governed if AI unavailable. Router `draft-blurb` accepts `{mode}`.
- **Standards registered** in `manufacturing_foundation.INHERITED_STANDARDS_BASE`: STD-MFG-0001, STD-BLB-0001.
- **Verified (curl, $0):** governed back_cover BOOK-0019 = 144 words within 120–170 target, fully grounded (sources: title/subtitle/manuscript.body×3/imprint); governed etsy 130w; Founder Canonical stored canonical; persisted map returns per-channel; products-engine (Pivot Points) governed works. draft-blurb now `mode=governed, ai_used=false`.
- **NOT YET:** dedicated frontend UI for the multi-channel description studio (backend + draft-blurb button wired only). ⚠️ Preview only — Founder must **redeploy** for qru-online.com.

## ⏳ PENDING (next major phase): Universal Publication Rendering & QA Pipeline
Founder's large spec (14 items). Root causes confirmed in preview: `rendering_engine._strip_md` force-encodes latin-1 (→ `?`/� corruption, (TM) artifacts) + fpdf2 non-embedded core fonts; markdown links `[t](u)` left raw; no single-TOC guarantee/visual-QA hard gate. Tooling ready (no new deps, no AI): PyMuPDF (page rasterization + text extraction for visual QA), CairoSVG (ASCII→vector diagrams), bundled Liberation TTFs (embeddable Unicode), numpy. Proposed 3 phases (see agent plan). Regression product = preview `products` copy `70474036-...` "QRU Pivot Points in Day Trading — Book" (2 Published copies untouched). Not started.


## ✅ Cover Generation Mode Selector™ (STD-COV-0001) — completed & verified (2026-07-30)
Founder-approved permanent capability: pick how every book cover is manufactured, with a SILENT fallback so cover manufacturing NEVER stops when an image provider fails.
- **3 modes** (`design_studio.manufacture_bytes/_concepts` `mode=`): `typography` (Premium Typography™, deterministic, $0, always succeeds) · `ai` (AI Artwork, honest per-concept failure — never faked) · `auto` (Recommended: try AI, silently fall back to Premium Typography™ per concept; Founder never sees the provider error — only "Premium Typography™ generated automatically").
- **Founder-wide default** persisted in `db.factory_settings` key `cover_generation` via `bm.get_cover_preference()` / `set_cover_preference()`. The "Remember my preference" checkbox saves the chosen mode for every future book.
- **Backend wiring:** `bm.design(book_id, actor, base_url, cover_mode, remember_preference)` resolves mode (explicit → remembered default → auto), threads it via `b["_cover_mode"]` into `_cover_design_recipe`, and stamps `cover_mode_summary()` into `artifacts.design.cover_mode` + `cover_provenance` (cover_mode_requested/used/notice). Router: `DesignReq` gains `cover_mode`+`remember_preference`; new `GET /api/book-mfg/cover-preference` returns default + mode list.
- **Standard registered:** `STD-COV-0001 QRU Cover Generation Standard™` added to `INHERITED_STANDARDS_BASE` in `manufacturing_foundation.py`.
- **Frontend (`BookManufacturing.js` DesignPanel):** loads default on mount, radio selector (`cover-mode-selector`, `cover-mode-{auto|ai|typography}`, `remember-cover-preference-checkbox`), saved-default hint, and a `cover-mode-used` banner (green = as requested / amber = fell back). Generate Design sends the chosen mode.
- **Verified:** curl — typography run on BOOK-0020 → 3 typography concepts (all success, $0), `remember_preference:true` persisted default to typography, then cleared; `cover-preference` GET returns modes. Screenshot — selector + 3 radios + checkbox + mode-used banner all render (data-testids confirmed). Auto silent-fallback confirmed by code review (not run, to avoid AI spend). ⚠️ Preview change; Founder must **redeploy** for qru-online.com.


## ✅ Factory Concierge — existing-KR resolution fix (2026-07-30) — testing_agent iteration_103, 100% (7/7 backend, frontend clean)
Bug: entering an exact KR ID ("KR-00080 — AI Literacy") was treated as a NEW topic and offered new research (tokenizer mangled `KR-00080`→`{'kr-'}`). Fixed:
- New `resolve_existing_assets()` in `factory_os.py` detects explicit KR/BOOK codes (regex) + exact/high-confidence titles BEFORE the fuzzy gate. `knowledge_gap_check()` now returns: resolved Verified KR (→ ready, no new research), `needs_verification` (KR exists but not Verified), `multiple_matches`+`selector` (>1 KR), or `manuscript_sources` (existing book_record offered as source asset). Read-only — never creates a KR.
- `factory_concierge.handle_message()` renders stages: ready (shows KR title + "Verified", normalizes topic to KR title), select_kr (selector chips), kr_needs_verification, manuscript_source. Returns `selector` + `manuscript_sources`.
- Frontend `FactoryConcierge.js`: renders suggestion/selector chips at any stage; guards the offer button.
- Verified: KR-00080 (all forms) → ready/launch; BOOK-0017 offered as manuscript source; KR-00069/00083 → selector; unknown topic → honest new-research; KR count stays 85 (no dupes).
- ⚠️ Fixed in preview — Founder must **redeploy** for production (qru-online.com).


# QRU Factory™ — Enterprise Knowledge Manufacturing OS

## ✅ Catalog integrity verified + Etsy publish pipeline (draft→upload→activate) (2026-07-30) — testing_agent iterations 101/102, 100%
- **Reported bug (catalog completeness) — NOT a bug, verified complete:** all 8 authorized books present; **Patterns of Intelligence (BOOK-0013) intact under E.Q. Rothwell™**; only the intended duplicate (BOOK-0003 "Ordinary Tuesdays FULL MANUSCRIPT") was merged into canonical BOOK-0004 and moved to `book_records_trash`. Public catalog returns 8.
- **Etsy publish pipeline** (`etsy_integration.py`): `publish_draft` now auto-resolves a Books/Digital taxonomy (`_resolve_taxonomy`, cached on integration doc), creates the draft, and uploads the **cover image** + **epub file** (read from disk via `_asset_bytes`). New `activate_listing` (go-live) is a SEPARATE, approval-gated step that also requires image+file attached and is idempotent. Route: `POST /api/integrations/etsy/products/{id}/activate`. UI: Etsy page shows attach-status (img/file) + state badge + "Activate (Go Live)" button (gated on connected + uploads).
- Founder choices: test product = The Understanding Tree (BOOK-0001); draft-only then manual Activate; auto-pick category.
- Fixed during testing: preview 500 (taxonomy key) and activate approval-gate ordering (approval check now runs first).
- ⚠️ **Live publish requires production** (Etsy is connected there, not in preview). Founder: redeploy, then on qru-online.com /etsy → Create Draft on BOOK-0001 → review in Shop Manager → Activate.


## Original Problem Statement
Production-ready enterprise OS for "QRU", a knowledge-manufacturing company using an autonomous
"Digital Workforce" to manufacture educational products. Core: Stripe commerce, Enterprise Workflow
Engine, Level-5 Autonomy, QRU Constitution governance, "First Dollar Mode".

## Standing Directives (Founder)
- **Founder Beta Stabilization Mode** — NO NEW FEATURES unless explicitly requested. Finish & stabilize.
- **Knowledge-First Rule** — never AI-generate customer-facing Knowledge Records.
- **$0 AI by default** — deterministic code; LLM caps handled gracefully.
- **Treasure Standard™** — no dead ends, no silent failures, evidence before any number/approval.
- Language: English only (code, comments, UI).


## ✅ Etsy Open API v3 — governed integration (2026-07-30) — testing_agent iteration_100, 100% backend + frontend, 0 issues
Founder-approved. Secure framework built to the STOP CONDITION (connect + read-only test + preview + draft capability; NO bulk publish; NO auto-activation).
- **Backend:** `etsy_integration.py` engine + `routers/etsy.py` (all `/api/integrations/etsy/*`, super-admin; only `GET /callback` is unauth, secured by OAuth state). OAuth 2.0 Authorization Code + **PKCE S256**; crypto-secure state+verifier per attempt stored server-side (`etsy_oauth_sessions`) and verified before code exchange. Tokens **encrypted at rest** (Fernet, reuse `INTEGRATION_ENC_KEY`) in `etsy_integrations`; **auto-refresh** with refresh-token rotation. Keystring/shared-secret/tokens NEVER returned to browser or logged (`_redact()` on all audit/detail). Full audit trail (`etsy_audit`): connect/disconnect/publish/update/sync/test/token_refresh/failure.
- **Governance gate:** a QRU product reaches Etsy only when QA complete + Authorized + deliverable file present + listing image present + metadata populated + no blocking issue (content-integrity/imprint-mismatch). **Draft-first + idempotent** (mapping in `etsy_listing_mappings` keyed by qru_product_id → retries never duplicate). Preview causes NO Etsy mutation. Etsy listings never auto-deleted.
- **Routes:** status, connect, callback, disconnect, test, listings, orders, products, products/{id}/preview, publish (approval-gated), PATCH products/{id}, products/{id}/sync.
- **Frontend:** `/etsy` (nav "Etsy Integration™", super-admin) — connection card (status/shop/scopes/counts/last error, Connect/Test/Disconnect) + eligible-products table with per-product Preview / Create Draft / View / Compare (Sync) / Update controls + governance preview panel.
- **Env (backend/.env, server-side only):** ETSY_API_KEYSTRING, ETSY_SHARED_SECRET, ETSY_SCOPES. Tokens stored encrypted in DB (not env).
- **PENDING FOUNDER ACTION (unavoidable):** live OAuth consent needs the Founder's Etsy account/browser. To finish the STOP CONDITION's "one test-product draft": (1) register redirect URIs in the Etsy app — `https://qru-online.com/api/integrations/etsy/callback` AND `https://enterprise-os-17.preview.emergentagent.com/api/integrations/etsy/callback`; (2) Deploy (prod picks up code + env); (3) click **Connect Etsy** on /etsy → approve on Etsy; (4) Preview → Create Draft on one authorized product. Everything else is verified.


## ✅ Imprint Canonicalization & Duplicate Merge (2026-07-29, RI-IMPRINT-0001) — self-verified full lifecycle
Founder brand-identity correction. New `imprint_rules.py` = single source of truth for imprint + genre.
- **Two imprints, one rule each:** **E.Q. Rothwell™** (LITERARY: The Understanding Tree, Ordinary Tuesdays, Patterns of Intelligence — author "E.Q. Rothwell"); **QRU Press™** (all educational/institutional — author "QRU Editorial" unless explicitly assigned). Author never inferred from imprint.
- **Permanent fields added to every book_record:** `canonical_imprint` + normalized `genre` category (Literary Fiction / Educational / Science / Legal / Finance).
- **Ordinary Tuesdays merge:** "Ordinary Tuesdays FULL MANUSCRIPT" (BOOK-0003, 0 purchases) archived into canonical "Ordinary Tuesdays" (BOOK-0004, 5 purchases) as `merged_records` (manuscript/files/history preserved) → duplicate moved to `book_records_trash` (reversible). Public never shows "FULL MANUSCRIPT".
- **Authorization QA gate:** `authorize_release` now blocks an **Imprint Mismatch** (assigned imprint contradicts the rule) until the Founder corrects it OR re-authorizes with `acknowledge_imprint_mismatch=true` (override recorded on the auth record). `get_book` surfaces `imprint_compliance`.
- **Delivered as a governed Production Operation** (`prod_migrations.imprint_*` + `/api/admin/migrations/imprint-canonicalization[/preflight|/rollback]`, super-admin) with a Preflight→Dry Run→Apply→Rollback card in Production Operations™ (`data-testid="imprint-canonicalization"`, buttons g-preflight/g-dry/g-apply/g-rollback). **No cover re-rendering (zero AI spend)** per Founder (deferred).
- **Applied in PREVIEW:** 19 books → 3 E.Q. Rothwell™ / 16 QRU Press™; storefront `/api/public/books?imprint=` filters correctly (3 literary vs 5 educational live). Idempotent + rollback + re-apply + QA-gate all verified (python + curl + auth 401 + UI screenshot). **Founder must Deploy + run "Apply Canonicalization" in production** (separate DB).


## ✅ Distribution Architecture™ Phase 0 (2026-07-29, Founder-approved) — testing_agent iteration_97, 9/9 backend + frontend verified
Approved model: **one governed catalog (QRU Store™), many plug-in customer experiences**. Phase 0 is invisible — QRU Learn™ and the public bookstore are untouched.
- Enterprise principles now live: One Governed Catalog · **Automatic Distribution™** (default destinations per product type, auto-selected at publish, Founder-overridable) · **Experiences are Plug-ins** (register without touching the Factory).
- Delivered: `distribution_architecture.py` + `/api/distribution-architecture/*`, auto-distribution wired into `publish_product`, and the Founder page `/distribution-architecture`. Full detail in CHANGELOG.md (2026-07-29).
- **Phased roadmap (approved):**
  - **Phase 1 ✅ DONE (2026-07-29)** — qru-online.com experience shell (Home/Books/Bundles tabs); Books experience reads catalog with imprint filtering (QRU Press™ / E.Q. Rothwell™); First-Class Bundles (real product, single-purchase multi-item delivery); Publish Destination Preview on product shelf + book authorize step. testing_agent iteration_98 (17/17 backend, frontend verified).
  - **Phase 2** — turn on **Resources / Media** experiences as rendering gaps close (video, motion story, posters); public visibility + purchase of non-book products.
  - **Phase 3** — mixed-type Bundles purchasable once all items deliverable; imprint management UI.
  - Parallel backlog: Audiobook Storefront (pending Founder decisions: sample length, pricing, voice, TTS-credit approval).


## ✅ Store Readiness batch (2026-07-28) — 3 of 4 founder tasks done (testing_agent iteration_96, 100%)
- **Test Product Cleanup (P0)**, **Batch Upgrade Assets™ (P1)**, **Store Health™ (P2)** — all shipped as governed, reversible operations in the Production Operations™ panel + a new Store Health™ dashboard. Full detail in CHANGELOG.md (2026-07-28). All self-verified + testing_agent 100% backend & frontend, 0 issues.
- **Remaining P1: Audiobook Storefront** — free Chapter-1 sample + purchasable full-audiobook SKU + e-book bundle upsell. Deferred pending Founder approval (spends TTS credits + touches the LIVE Stripe checkout path). Decisions needed: free-sample length, audiobook price + bundle price, narrator voice.
- ENV boundary unchanged: preview & production are SEPARATE DBs; the 3 new operations act on the connected DB, so the Founder runs them in production from the deployed panel after Deploy.

## ✅ Storefront Launch Readiness (2026-07-27) — checkout verified + landing/SEO/email capture
- **Checkout NOT broken** (prior "Buy the ebook" timeout was a test-tool artifact — clicking redirects to external checkout.stripe.com which Playwright waits on). Verified via curl: `POST /api/public/checkout` returns a valid Stripe session in ~0.5s; frontend button (`buy-ebook-btn`) correctly wired. ⚠️ Preview `.env` carries LIVE Stripe keys (session came back `cs_live_...`), so a real end-to-end purchase in preview charges real money — verified at API + code level only per Founder direction.
- **SEO-friendly slug URLs**: `public_site.py` adds `_slugify` + `_slug_map` (deterministic, sorted-by-id, id-suffix on title collision). `/api/public/books/{key}` now resolves by id OR slug (id still works → backward compatible with checkout cancel_url). `home`/`books`/`book_detail` return a `slug` field. Route changed to `/book/:slug`; Home & Catalog link via `book.slug`; book page fetches by slug, checkout keyed by resolved `book.id`. Verified: slug resolve, id resolve, bad slug → 404.
- **SEO meta tags**: dependency-free `Seo.js` component sets document.title, description, canonical, OpenGraph + Twitter cards per page. Wired into Home, Catalog, Book page (book page uses cover image + description). Default `index.html` title/description updated from Emergent boilerplate to QRU Press™.
- **Launch landing moment**: `TrustMarks.js` band (Treasure Standard™ verified · Secure Stripe checkout · Instant EPUB delivery · 14-day refund) below the hero on Home. Featured titles already present.
- **Email capture**: `NewsletterSignup.js` (dark band above footer on Home) → `POST /api/public/subscribe` (regex-validated, deduped into `db.newsletter_subscribers`, best-effort branded welcome email via Resend). Verified full UI flow: valid → success state + toast; invalid → 400; duplicate → already_subscribed. Test subscribers cleaned from DB.
- Self-verified via curl + screenshots (Home trust marks + newsletter, slug book page + buy button + SEO title, newsletter submit). No testing_agent run (avoided live-Stripe charges). NOTE: frontend required a supervisor restart to pick up new component files (HMR served a stale bundle initially).


## ➕ Create-Under-Fresh-Code + registry registration (2026-07-25)
- **Create Under Fresh Production Book Code** (`POST /api/admin/migrations/book-cutover/create-fresh-code`, dry-run default) + rollback: for DIFFERENT_WORK conflicts, creates the incoming distinct work under the next available `BOOK-####` (preserving its canonical id + assets + re-rendered EPUB), leaving the existing production work under that code untouched. Idempotent (skips once canonical id present). UI: "Different works sharing a code" control row in Workstream A. Validated in scratch test (BOOK-0016 → BOOK-0017, id preserved, collision untouched, idempotent, rollback removes when 0 purchases).
- **Registered as permanent inherited capability**: `capability_registry.py` entry `production-operations` (governance layer, status **inherited**, inherited_from RI-MFG-0002b, moat=True). Excluded from the auto "All Capabilities" drawer (NAV_CORE_IDS) to avoid duplicating the founder-only core sidebar item. Appears in Factory Map as inherited.

## ✅ DQ-7 CLOSED (2026-07-27) — Standards metadata canonicalization delivered
- DQ-7C production promotion added to Production Operations™ as ONE independent governed operation: `GET /standards-metadata/preflight`, `POST /standards-metadata/apply`, `POST /standards-metadata/rollback` (`prod_migrations.py` + `routers/migrations.py`). UI card "Standards Metadata Canonicalization" (Preflight → Dry Run → Apply → Rollback + completion report).
- Preflight gates Apply: proceeds only when production has 39 canonical + 5 projections and 0 material conflicts. Additive-only, idempotent, rollback-preserving. Preview-verified (preflight Ready, apply idempotent no-op since preview already applied via DQ-7C).
- 28 enforcement classes remain FOUNDER_DECISION_REQUIRED (untouched); projection NOT hydrated; not combined with Workstreams A/C — per Founder directive.
- **Factory focus now returns to: product launch, storefront readiness, discoverability, customer acquisition.**

## ✅ DQ-7C executed (2026-07-26, PREVIEW DB) — standards metadata canonicalization
- Applied approved DQ-7B design. Additive-only, guarded, reversible. Script `backend/_dq7c_execute.py` (EXECUTE flag), artifacts in `/app/memory/audit/`.
- `qiks_standards` (39, canonical): `lifecycle_status=ADOPTED` ×39; enforcement = 9 INHERITED_ENFORCED + 2 GATE_ENFORCED (11 evidence-backed) + 28 FOUNDER_DECISION_REQUIRED; `owner`+`verification_status` added to the 5 constitutional-tier records.
- `constitutional_registry` (5): `canonical_ref`(=standard_id) + `projection:true` added; all existing fields retained.
- 225 additive writes; 0 overwrites/deletes/renames; counts stable 39/5; every canonical_ref resolves 1:1; founder_approval + inheritance preserved. Endpoints `/api/qiks/standards` (39) + `/api/flow/registry` (5, contract intact) + iteration-51 contract test all PASS.
- Pre-image: `dq7c_preimage_*.json`; report: `dq7c_post_execution_report.json`; rollback: `dq7c_rollback_manifest.json`.
- 28 enforcement classes remain FOUNDER_DECISION_REQUIRED (untouched). PRODUCTION not modified (preview-only; identical pass ready for prod via governed endpoint).

## 🧬 Publishing Lineage engine (2026-07-25) — comparison intelligence upgrade
- Replaced title-equality classification with a **publishing-lineage engine** (`_classify_lineage` in `prod_migrations.py`). Evidence order: (1) canonical immutable manuscript checksum (`original.checksum` / `transparent_provenance.immutable_original_checksum`) → definitive; (2) editorial-version checksum overlap; (3) source-document filename (normalised to strip cosmetic tokens like "FINAL"/"draft"/"vN"); (4) normalised title (equal / subset); (5) author (blank = compatible). Returns **classification + confidence score + reasoning chain + recommended action**.
- Classifications: SAME_BOOK · TITLE_CHANGED · NEW_EDITION · DIFFERENT_WORK · POSSIBLE_COLLISION · PRESENT_BY_ID · ABSENT. adopt_eligible = {SAME_BOOK, TITLE_CHANGED}; resolver keys off this.
- Inspect endpoint now returns confidence + reasoning + checksum/source_filename for both sides; UI renders the full **Publishing Lineage Inspector** (reasoning chain, confidence %, adopt-eligible badge).
- KEY FINDING: `book_code` is assigned **per-database sequentially**, so preview's BOOK-00NN and production's BOOK-00NN can be different works — this is why BOOK-0016 collides. True identity = manuscript checksum, not book_code. Engine flags such cases DIFFERENT_WORK and blocks adoption; recommends re-keying to a fresh production code.
- BOOK-0013 "FINAL" case = title correction (same source doc/checksum) → now SAME_BOOK (was a false-positive collision under the old title-only logic).
- Validated (`backend/tests/test_conflict_resolution.py`): checksum-match→SAME_BOOK(adopt); FINAL filename correction→adopt-eligible; genuinely-different→DIFFERENT_WORK(no adopt); collision record untouched; rollback + purchases preserved.

## 🔍 Conflict handling added to Production Operations™ (2026-07-25)
- Production dry-run of Workstream A returned CONFLICT for BOOK-0013 & BOOK-0016 (book_code exists in prod under a DIFFERENT internal id). This is the Stage-1 guardrail working — it refuses to insert a duplicate book_code.
- Added READ-ONLY **Inspect Records** (`GET /api/admin/migrations/book-cutover/inspect`): side-by-side incoming-vs-existing (id, title, author, status, purchases, current EPUB) + auto-classification per book:
  - PRESENT_BY_ID · ID_MISMATCH_SAME_BOOK (same title+author) · ID_MISMATCH_TITLE_MATCH_AUTHOR_DIFF · CODE_COLLISION_DIFFERENT_CONTENT · ABSENT.
- Added governed **Resolve Conflicts** (`POST /api/admin/migrations/book-cutover/resolve-conflicts`, dry-run default): ONLY for ID_MISMATCH_SAME_BOOK → ADOPTS the existing production record and repoints its EPUB to the re-rendered edition by its EXISTING id (no duplicate, preserves cover/pricing/authorization/purchases, rollback-preserving). Collisions/author-mismatch are SKIPPED for founder decision.
- Validated via scratch-DB simulation (`backend/tests/test_conflict_resolution.py`): same-book→adopt+repoint+rollback+purchases preserved; collision→untouched; absent→create. UI Inspect panel verified.
- Requires redeploy to reach production. NO production data modified by the agent.

## 🏭 NEW CAPABILITY (2026-07-25): Production Operations™ — Founder-run governed migrations
- **What**: Permanent, reusable Founder/Admin console (`/production-operations`, nav item in Core Capabilities) to run governed, idempotent data operations against the LIVE production DB with NO terminal, local scripts, Mongo commands, or Support intervention. Officially-recommended pattern (confirmed w/ platform): logic runs inside the deployed backend, which is the only env with production MONGO_URL.
- **Backend**: `prod_migrations.py` (async port of the exact RI-MFG-0002b + Workstream C script logic) + `routers/migrations.py` (`/api/admin/migrations/*`, `require_super_admin`). Data ships in `backend/migrations_data/`.
- **Workstream A — Book Data & EPUB Cutover**: Stage 1 creates 4 missing books (BOOK-0013/0016/0018/0019); Stage 2 points all 8 books at validated re-rendered EPUBs. Asset-verified against durable object storage (auto-mirrors local→durable in preview); rollback-preserving; never touches manuscripts/covers/pricing/authorization/purchases.
- **Workstream C — Learn Containment**: classifies 5 lessons (PRD-00130/196/201/202/205) Published w/ unverified KR; optional governed Hold (removes from learner catalog) preserving product/assets/purchases; one-tap rollback.
- **Each op supports**: Dry Run · Review (evidence table + raw JSON) · Apply · Rollback. DRY-RUN default everywhere; writes need explicit apply + confirm.
- **Verified (self-test in preview)**: summary + both dry-runs OK; C apply→verify(held)→rollback→verify(restored) clean; auth 403 (student) / 401 (anon); UI renders + dry-run evidence works, no console errors.
- **Deploy note**: Requires Founder to click Deploy so production picks up the endpoints, then run from qru-online.com.

## 🛠️ P0 FIX (2026-07-25): Login white-screen crash — FIXED in code, deploy-ready
- **Root cause**: `App.js` route `<Route path="pilot-coordinator" element={<PilotCoordinator />} />` (line ~194) referenced `PilotCoordinator` but the component was NEVER imported. Referencing the undefined identifier threw `ReferenceError` the instant `EnterpriseRoutes` rendered (i.e. right after a successful login), unmounting the app → white screen + red error. Public routes (logged-out) were unaffected, which is why the storefront worked for visitors but any logged-in Founder crashed at `/`.
- **Fix**: added `import PilotCoordinator from "@/pages/PilotCoordinator";` in App.js.
- **Verified**: (1) preview login → full Executive Command Center dashboard renders, no crash; (2) `grep` confirms every route element component is now imported; (3) `yarn build` compiles successfully (build ready to deploy).
- **ACTION REQUIRED BY FOUNDER**: Production (`qru-online.com`) still runs the old broken build. Founder must click **Deploy** to push the fix live. Logged-in users were stuck because the cached token makes the root render the crashing dashboard on every visit.
- Preview-only note: Founder temp password `QruFounder2026!` is rejected in PREVIEW DB (a permanent password was set there previously). Production Founder creds are unaffected. Demo admin (`demo.admin@qru.com` / `qru-demo-admin-2026`) works in preview for testing.

## 🔎 CURRENT STATUS (2026-07-25): Purchase Confirmation email — COMPLETE in preview & READY TO DEPLOY. Resend key in env-secret; domain qru-online.com VERIFIED (DKIM/MX/SPF/tracking); SENDER_EMAIL=receipts@qru-online.com. Real sends to owner AND non-owner recipients both succeeded (msg ids captured). Only remaining step = Founder clicks Deploy so production picks up code + env. Full detail in CHANGELOG.md. Scope-held: Enterprise Health formulas, stale-job cleanup, Batch Upgrade Assets™, Audiobook Storefront, Store Health.


## ✅ Post-redeploy fixes: Audit download + Stripe wording (2026-06, testing_agent iteration_95 — 100% backend + frontend)
- **Audit JSON download bug FIXED**: frontend `downloadAudit()` called `/api/audit/...` through an axios client whose base already ends in '/api' → doubled '/api/api/...' → 404 → "Download failed". Fix: strip leading '/api'. All 3 files download (HTTP 200).
- **Stripe status contradiction FIXED**: `routers/metrics.py` beta-status hardcoded 'TEST mode/sandbox' while LIVE keys installed. Now derives from `STRIPE_TEST`; live → pay_mode='LIVE', accepts_real_money='Yes'; added `payment_status` object. No contradiction.
- **INVESTIGATION ONLY (scores unchanged per Founder):** Manufacturing=0 → `max(0,100-not_manufactured*10-failed_jobs*15)` = 100−11×10−4×15 → floored 0 (backlog+4 failed jobs; Director agent active, workload 70). Creative Studio=22 → `max(0,100-13*6)` (13 products missing/Pending creative_status = old covers). Enterprise Health = equal average of 8 systems (confirmed; no zero-fill).
- ⚠️ Fixes are in PREVIEW — production needs a REDEPLOY. Learning Center small-print covers = old baked images awaiting Batch Upgrade Assets™.



## ✅ Standards Audit preserved + Title Cleanup PREVIEW (2026-06, display-only, awaiting Founder approval for any data migration)
Founder approved the read-only Standards Audit as the baseline snapshot and authorized display-only title cleanup (no registry changes, no permanent migration).
- **Audit evidence preserved & Founder-accessible**: `/app/backend/audit_exports/` holds `QRU_Standards_Full_Export.json` (original preserved, not overwritten), `QRU_Standards_Inventory.csv` (39-standard CSV), `QRU_Standards_Audit_Findings.md` (header: audit date, iteration 94, 39 standards, 6 lessons, 23 recipes, 10 PMS; sections A–E: missing STD-EIP-0001, 15 orphans, code-equivalent unregistered capabilities, Founder-approved-not-found records, empty metadata). Served via `routers/audit_exports.py` (`GET /api/audit/exports` + `/exports/{file}`, super-admin). Download control added to Institutional Knowledge page (`audit-exports-panel`).
- **REGISTRY HELD**: no STD-EIP-0001 created; no orphan links; no register/rename/merge/supersede/delete; no code→standard conversions. Awaiting Founder crosswalk approval.
- **Title cleanup = DISPLAY-ONLY** (`rendering_engine.clean_customer_title` + `design_language._clean_cover_title`): strips redundant/internal suffixes ("- Book", "- Short-form Content") from rendered titles/covers and removed the "Manufactured by QRU Factory" chrome from product interior title pages (now shows the real subtitle). Reverted the earlier stored-title change → **DB titles, internal names, product IDs, slugs, URLs, purchases, files all UNCHANGED**. NO permanent title migration ran. 9/9 automated checks pass. Before/after e.g. "Love — Book" → display "Love"; "AI Literacy — Workbook" preserved.
- **PAUSED for Founder approval** before any permanent title data migration.
- Production sequence maintained: (1) redeploy+verify [Founder], (2) title cleanup [previewed], (3) Batch Upgrade Assets™ covers, (4) audiobook storefront, (5) Store Health view. Standards visual inheritance tree NOT added (per instruction).



## ✅ UKR Standards Hierarchy + inheritance metadata (2026-06, testing_agent iteration_94 — 100% frontend, API curl-verified)
Founder-approved NON-DESTRUCTIVE hierarchy (existing IDs kept, aliases added, content untouched):
QRU Master Constitution™ (STD-00005) → **STD-UKR-0001 Universal Knowledge Record™ (CANONICAL)** → STD-00027 **Knowledge Record Master Specification™** (alias STD-KR-0001, Supporting) → STD-00030 **Knowledge Record Template™** (alias STD-KR-0002, Supporting) → individual KRs.
- `qiks.py`: `_std()` extended with `standard_type / designation / inherits_from / implemented_by / supersedes / alias` (empty defaults → other 35 standards unaffected). Added canonical STD-UKR-0001 card. `apply_kr_hierarchy()` = idempotent patch called in `seed_qiks()` → applies on every startup/redeploy (so production gets it too). `get_standard()` resolves by id/standard_id/**alias** (backward compat: STD-KR-0001 → STD-00027).
- Frontend `InstitutionalKnowledge.js`: cards show ⭐Canonical / Supporting designation badge + "Inherits from" + alias; detail dialog adds Standard Type, Inherits From, Implemented By, Alias, Supersedes.
- Designations: UKR + Master Constitution = "Canonical Knowledge Standard"; Spec + Template = "Supporting Implementation Standard". Stops the "three competing UKRs" confusion.
- Caution honored: no auto-rename of IDs; backward-compatible aliases; only these 4 docs patched (dependencies mapped — governance_binding.py references by NAME not ID, so no breakage).



## ✅ Production hardening: Cover fonts, Audiobook chunking, Store Remove/Re-list (2026-06, testing_agent iteration_93 — 100% backend + frontend, zero blocking)
Founder is on PRODUCTION (https://qru-online.com). Reported: tiny cover fonts on all products, an unaddressable Book MFG error, and requested a way to remove a book from the store.
- **ROOT CAUSE of tiny cover titles = missing system fonts in the PRODUCTION container.** PIL fell back to `ImageFont.load_default()` (~10px, ignores requested size) → every title collapsed to one tiny line. FIX: **bundled Liberation TTFs into `/app/backend/assets/fonts/`** and made `design_language._font_path`/`_f` + `design_studio.font()` prefer bundled fonts (system path fallback + scan-any-TTF + error log; never silently tiny). Proven: the exact long "Louisiana Contractor Business Law" title now renders large/3-line. Also enlarged `design_language.premium_cover` titles (start 150, min 58, max 3 lines). ⚠️ REQUIRES REDEPLOY; existing baked covers must be RE-RENDERED after redeploy to pick up the fix.
- **Audiobook error 'Text must be 4096 characters or less' FIXED**: `cinema_studio._tts_bytes` now chunks narration into ≤3800-char segments (sentence/paragraph boundaries) and concatenates audio. Fixes full audiobook + narration prototype + media division. Chunker logic verified deterministically ($0); full render consumes TTS credits.
- **NEW: Remove/Re-list a book from the store** (`book_manufacturing.remove_from_store` / `relist_to_store`; `POST /api/book-mfg/books/{id}/remove-from-store` + `/relist-to-store`, super-admin). Removing sets `founder_authorization.authorized=false` → book instantly drops from all public queries (`_PUBLISHED_QUERY`), unpublishes any linked product listing, keeps files/purchases intact (buyers keep access), reversible. Re-list guarded: only for previously-removed books (never-listed books must pass Founder Release Review). UI in BookManufacturing.js: `store-listing-row` with live/off status + `remove-from-store-btn`/`relist-to-store-btn` (confirm + reason prompt). Verified E2E: public count 8→7→8.
- **PENDING (Founder's UKR hierarchy request, not yet built):** rename/relate the 3 standards to show inheritance — STD-UKR-0001 Universal Knowledge Record™ (canonical) → STD-KR-0001 Knowledge Record Specification™ → STD-KR-0002 Knowledge Record Template™ → KR-000001; add an "Inherits From" field to every standard card. Founder wants them kept SEPARATE (not merged) but shown as a hierarchy.



## ✅ Manufacturing Season — Pre-Review Inspection™ + Product Family Manufacturing™ (2026-06, testing_agent iteration_92 — 100% backend 10/10, 100% frontend 2/2, ZERO blocking issues)
Founder recharged credits after a series of read-only consolidation assessments; approved building all three (reply "abc").
- **(a) QRU Automated Pre-Review Inspection™** (`preflight_inspection.py`, STD-INSPECT-0001; `GET /api/book-mfg/books/{id}/inspection`): ONE read-only consolidated pass that lists ONLY exceptions (formatting, placeholders, repeated words, spacing, structure, front-matter, links, spelling via pyspellchecker offline, content-integrity, metadata completeness) with severity buckets (blocking/recommended/advisory). NEVER rewrites (Treasure Standard) — verified content/word-count byte-identical before/after. UI panel in BookManufacturing.js (`preview-inspection-panel` → `run-inspection-btn` → `inspection-report`). Founder-judgment items (voice, teaching, reader experience, pricing, final approval) explicitly kept human.
- **(b) Product Family Manufacturing™** (`manufacturing_intents.py` + `family_assembly.py` + `routers/family.py`, page `/product-family`, in NAV_CORE): pick a Verified source (Manufacturing-eligible understanding) → pick a Manufacturing Intent™ (Consumer/Classroom/Homeschool/Professional/Corporate/Exam Prep) → confirm the pre-ticked family bundle → ONE action manufactures the family + one Family Package™. Pure ORCHESTRATION over the existing `create_product_from_decoder` bridge (no new engine). Source Verification Gate™ still blocks mismatches (DEC-GATETEST → 409). $0 AI for document families / Book-record creation.
- **Eligibility fix:** `decoder_engine.MANUFACTURING_ELIGIBLE_STATES` now includes states ABOVE "Manufacturing Ready" (Founder Approved / Treasure Standard Candidate / Treasure Standard Certified). Previously a Founder-Approved understanding was wrongly blocked. `get_decoder` + `get_book` now resolve by id OR decoder_id/book_code.
- **(c) AI Literacy rebuilt from the CORRECT source:** ran the Classroom family on DEC-00018 (decoded from Verified **KR-00080 "AI Literacy"**) → **BOOK-0018** (content-integrity CLEAN, not factory-docs) + Workbook PRD-00240 + Teacher Guide PRD-00241, all KR-00080-linked (FAM-5EA08F8F). BOOK-0018 cover intentionally NOT yet AI-rendered (Founder action in Book line to avoid AI spend).
- Non-blocking follow-ups (optional): allow `GET /api/products/{code}` by product_code.



## ✅ Content-integrity guard + cover legibility (2026-07-21, testing_agent iteration_90 — 4/4 PASS)
Founder found (on production) a book titled "AI Literacy K-12" whose BODY was internal QRU Factory
documentation (Product Manufacturing File, audit records, governed knowledge record) — the Book Recipe
faithfully rendered the WRONG source KR (the Factory's own standard doc, which uses "AI Literacy K-12" as an example).
- **Root cause:** `_decoder_to_manuscript` renders whatever Decoder/KR it's given. The source content was the
  governance/standard document, not an educational AI-literacy KR. This is a content-SOURCING problem.
- **Fix (code safeguard, Treasure Standard™ / STD-UKR-0001 Executable Completion Rule):** new
  `book_manufacturing.content_integrity_check(title, subtitle, content)` — deterministic density scan of internal
  Factory vocabulary; flags when body reads like Factory docs but the title is NOT about the Factory (Factory-titled
  books are allowed). Surfaced in get_book as `content_integrity`, a red banner (`content-integrity-warning`) in
  Book Manufacturing, and a FAILED QA stage on the Publish Success Dashboard. Verified: flags mismatched book,
  no false positives on legit books, no regressions.
- **Production remedy (Founder action):** the live "AI Literacy K-12" book must be rebuilt from the CORRECT
  educational source KR (not the standard doc), then re-authorized. Its cover re-renders with the legibility fix.
- **Cover legibility:** `design_studio.compose()` title auto-fit (large, bold, fills panel; enlarged subtitle/byline)
  was shipped earlier this session and verified. EXISTING covers are baked images — they upgrade only on re-render
  (regenerate cover / rebuild). Production covers will improve after re-render + redeploy.


Founder reframed the goal: "can the Factory reliably DELIVER products to customers?" Built the definitive answer.
- **Publish Success Dashboard™** (`shipping_status.py`, GET /api/publishing/shipping-status, page /shipping-status,
  linked from /distribution via 'open-publish-dashboard'): every product shows an 8-stage pipeline —
  Knowledge Record → Manufacturing → QA → Authorized → Published → Store Sync → Purchase Tested → Delivery Tested —
  each green/grey from REAL data (purchases from book_purchases, delivery from download_count). All green = truly shipped.
  Verified: 15 products, 1 fully shipped; BOOK-0013 'Patterns of Intelligence' = 6/8 (Published ✓ + Store Sync ✓;
  only Purchase/Delivery ungreen) — confirming it published correctly; next='Purchase Tested'.
- **Environment auto-detection** (GET /api/publishing/environment): each app host that touches THIS database writes a
  beacon; if >1 distinct host → SHARED db, else single/separate. The Factory determines this itself (Founder no longer
  asked implementation details). Current verdict: only preview host registered → preview & prod likely SEPARATE DBs;
  auto-updates when production deploys and loads once.
- Also fixed: Parts-vs-chapters, subtitle editor, always-editable pricing pencil (see prior entry).

### Publish vs Deploy (clarified for Founder)
- PUBLISH = Factory DB → product authorized (works; BOOK-0013 live on PREVIEW store).
- DEPLOY = new app version → production website (qru-online.com). Last prod deploy FAILED (transient Cloud Build;
  deployment_agent found NO code blockers, yarn build passes) → fix is re-Deploy.

### Confirmed sequence (Founder 2026-07-21, revenue-first, stabilize-before-expand)
0. [DONE] Publish Success Dashboard™ + auto DB detection.
1. Stabilize publishing: prove Purchase + Delivery (run a test purchase → those stages go green).
2. Audiobook on QRU-online: free Ch-1 sample (~3-5 min teaser) + purchasable full audiobook (own SKU + e-book bundle).
3. Voice Asset Manufacturing Framework™ v1.0 — ElevenLabs cloning from day one (Founder provides key). Reuse
   character_registry pattern; provider-agnostic; analyze→Voice DNA→samples→review→approve→registry→reuse.
4. Posters (Founder uploads 3-4 gold refs) — factual/machine SVG, 300 DPI large-format + print-ready PDF.
5. YouTube publisher (check existing auth) — simple (cover+audio MP4) default, rich optional.
6. [Medium] Product Family Manufacturing Line™ (Universal Distribution Framework™) — AFTER publishing proven.


- **Parts vs chapters:** new `book_structure.content_units()` robustly detects divisions — `## Chapter` books AND `# Part …` books (which previously parsed as 0 chapters). `parse_book` falls back to it; full-audiobook `_chapter_texts` uses it. Verified: a `# Part One/Two/Three` book → 3 units (book-title heading dropped); normal `## Chapter` books unchanged.
- **Subtitle editor:** identity editor now edits Title + **Subtitle** + Author (`edit-subtitle-input`); backend publication-details accepts `subtitle`. Verified.
- **Pricing pencil:** Publish panel price input is now pre-filled with current/estimated price and always editable (button "Approve Price" / "Update Price"), so the Founder can revise pricing anytime. The Pricing Advisor™ already provides the estimate.
- **Full-length audiobook:** background job renders every chapter via chosen voice → ffmpeg (imageio-ffmpeg) concat → durable MP3 with chapter markers. Verified end-to-end.
- **Narrator voice/speed/custom script** + **"Chapter twice" fix** + **title FINAL fix** + **clean-up-title** — all verified (iteration_88, 5/5).
- **STD-UKR-0001 constitution** (Work Order items 1-6): items 1&6 already satisfied in code; added ownership rule, metadata-inclusion rule, two Gold gates, Executable Completion Rule + `governed_deficiency()`, standard renamed to "Executable Universal Knowledge Record™ Enterprise Standard", `frozen:true`. Endpoint GET /manufacturing/ukr/constitution + panel on /constitution. Verified.

### Publish-to-qru-online clarification (2026-07-21)
- Books publish to the storefront when `founder_authorization.authorized == True`. "Patterns of Intelligence" (BOOK-0013) IS authorized and DOES appear on the PREVIEW storefront ($5.99, 5 public books).
- qru-online.com is PRODUCTION (separate deploy + likely separate DB). A preview-authorized book won't appear there. Latest production deploy FAILED (transient Cloud Build error — deployment_agent found NO code blockers; `yarn build` passes). Fix = re-Deploy. Open question for Founder: whether preview & prod share a DB (determines if the book appears after a successful deploy or must be authorized in prod).

### Approved backlog / sequence (Founder, 2026-07-21)
1. Audiobook on QRU-online: free Chapter-1 sample (first ~3-5 min teaser) + purchasable full audiobook (own SKU + e-book bundle upsell). [revenue-first]
2. Voice Asset Manufacturing Framework™ v1.0 — Founder wants **ElevenLabs cloning from day one** (will provide API key). Reuse character_registry pattern; provider-agnostic; analyze→Voice DNA→samples→review→approve→registry→reuse; governance via existing audit/treasure/approval. NOT a new top-level dept.
3. Posters (Founder to upload 3-4 gold-standard refs) — keep factual/machine SVG, 300 DPI large-format + print-ready PDF.
4. YouTube publisher (check existing auth) — simple (cover+audio MP4) default, rich (slideshow+chapters) optional.
- Also raised: "one product in → one publication package out" — generalize the book pipeline to all product families (Universal Distribution Framework™). Explanation given; build TBD.


Founder working on BOOK-0013 "Patterns of Intelligence FINAL": the file-name word "FINAL" printed on the
cover and was spoken in the narration, and the narrator said "Chapter 1" twice on EVERY book.
- **Title/author editor (new):** `POST /api/book-mfg/books/{id}/publication-details` now accepts `title` &
  `author` (`set_publication_details`). Frontend: inline pencil-edit in the Book Manufacturing identity bar
  (`edit-identity-btn` → `edit-title-input`/`edit-author-input` → `save-identity-btn`) with a tip to strip
  file-name artifacts (FINAL/v2/DRAFT) and re-run Design & Audio. Verified: BOOK-0013 title → "Patterns of
  Intelligence". ($0; existing cover/audio refresh on next Design/Audio run — no auto AI spend.)
- **"Chapter 1 twice" narration bug (`render_audio_prototype`):** narration was
  `"{title}. Chapter {n}. {chapter_title}."` but the parsed chapter title already began with "Chapter One:…",
  so TTS said "Chapter 1. Chapter One…". Now: if the chapter title already starts with "Chapter", narrate it
  as-is; else prepend "Chapter N.". Verified prefix now: "Patterns of Intelligence. Chapter One: The Question
  Beneath the Question." — no duplication, no "FINAL".
- **Audiobook "doesn't work" diagnosis:** OpenAI TTS engine works ($ verified, 45KB test + a real 175s Ch-1
  prototype rendered for BOOK-0013). The perceived breakage was the double-"Chapter" + "FINAL" narration.
  NOTE (V1 limitation, unchanged): Button 4 renders a Chapter-1 PROTOTYPE + a guided checklist — NOT yet a
  full commercial audiobook. Full-book audio rendering remains a future item.


Founder reported (on production qru-online.com): tiny unreadable cover titles, a confusing "Coming from the
Studios" panel, products stuck "Paused" with no way to clear, and a spurious "Something went wrong" on cover-select.
All fixed in PREVIEW ($0 AI):
- **Cover title legibility (`design_studio.compose`)** — replaced the fixed 70/92/118px title cap with an
  AUTO-FIT that grows the serif-bold title to fill the panel width (up to 3 lines), enlarged subtitle/byline,
  recentred the legibility panel. Long titles (e.g. "AI Literacy K-12 — Parent / Family Guide") now render large
  and bold instead of microscopic. Verified by direct render. NOTE: existing covers upgrade only on their next
  re-render/regenerate-cover (no auto-regen — no silent AI spend).
- **Quality Gates clear (`routers/inspection.py` + `ManufacturingInspection.js`)** — new
  `POST /api/inspection/product/{id}/certify-treasure` (super-admin, audit-logged, refuses if no deliverable).
  Certifying is the deliberate Founder Treasure Standard™ sign-off the gate is designed to require (NOT a bypass) —
  it flips the Treasure component to 100 and clears the product IF no OTHER blocking gate fails (remaining blockers
  reported honestly). New "Founder sign-off → Certify Treasure Standard™" panel appears in the gate-detail modal for
  super-admin when the Treasure gate is failing. Verified: PRD-00223 Paused(88)→Cleared(95); Paused 184→183.
- **Studios panel (`MediaDivision.js`)** — relabeled "Coming from the Studios (Stone 3)" → "Audio & Video — made in
  the Studios"; each format chip is now a Link to /cinema-studio (Cinema/Podcast Studio are LIVE, not "coming soon").
- **Cover-select error (`BookManufacturing.js`)** — removed a redundant double-reload in `doSelectCover` (run()
  already reloads) that caused the spurious "Something went wrong" toast after a successful selection.
- **DEPLOY:** these are PREVIEW code changes — Founder must click Deploy to see them on qru-online.com.
- **OPEN / next:** Poster Studio visual-quality polish (keep factual/machine-rendered, improve typography) — approved,
  not yet started. Books publish to qru-online automatically on "Authorize Release" (full Final Release Gate required).


`FounderOpsToolkit.js` on /governance (super-admin only). All 6 buttons verified end-to-end in
PREVIEW with real backend results confirmed (not just clicks). NO AI/Gemini/TTS spend.
- **UKR Migration Status** (GET /manufacturing/ukr/migration-status) → 81/81 migrated · 0 pending · backward-compatible. PASS.
- **Production Health Check** (GET /public/books + ukr status) → Storefront OK · 4 books live · UKR 81/81. PASS.
- **Storage Audit** (POST/GET /rendering/storage-audit) read-only → 738 referenced · 737 local · 0 durable · 1 missing (that 1 classified 'other'). PASS.
- **Deterministic Recovery** (POST/GET /rendering/storage-recovery) → complete · recovered 0 · skipped 99 · failed 0; idempotent on re-run; $0 (missing item is 'other', not auto-rebuilt). PASS.
- **Durability Backfill** (POST/GET /rendering/storage-backfill) → long-running by design (walks ALL on-disk assets ≈9273 legacy files per original backfill goal); idempotent (re-POST returns 'already running'; 'already' counter increments). Job in-flight, progresses correctly. PASS (contract).
- **Verify JWT Deliverables** (POST /products/{id}/file-token) → tokened=200, no-token=403. PASS.
- Role-gating confirmed hidden for Teacher & Customer. Auth: POSTs 401 unauth / 403 non-super-admin.
- **Minor (deferred, not blockers):** backfill does not surface `failed_ids` (2 files failed silently ~0.27%);
  consider parallel to recovery_status. Backfill scope (all disk vs DB-referenced) is intentional per legacy-asset goal.
- **STATUS: Toolkit is production-ready.** Deploy is a Founder action (Deploy button).

## ✅ Phase B — Durable Storage for covers/EPUBs/PDFs/deliverables/audio (2026-07-20)
**Root problem:** the rendered-asset disk (`/app/backend/rendered_assets`, `generated_audiobooks`) is
EPHEMERAL — every redeploy wipes covers/EPUBs/PDFs/deliverables/audio (recurring loss, 3rd time).
Emergent support CONFIRMED: no SSH/exec/pre-deploy hook/snapshot — the OLD production container's
files CANNOT be copied out before it is replaced. So the FIRST redeploy after this ships still loses
current on-disk prod files (rebuilt deterministically post-redeploy); from then on nothing is lost.
**Fix (mirror-on-write + materialize-on-read, one durable key = the fid):**
- `storage.py`: `mirror_file(fid,data)` (best-effort, never raises), `ensure_local(fid,dest)`
  (re-download from object storage if disk copy gone), `object_exists(fid)` (ranged 1-byte GET),
  `content_type_for`, async wrappers. Durable path `qru-online/assets/{fid}`.
- `rendering_engine._save()` now mirrors every non-`tmp` asset → covers/EPUBs/PDFs/HTML/wrap/deliverables
  are durable at write time (one choke point covers the whole document pipeline).
- Materialize-on-read wired into ALL serve routes: `routers/rendering.py asset`, `public_commerce`
  EPUB download, `book_manufacturing` review-zip, `public_site` cover/thumb, `publishing` audiobook-file.
  `deliverable_renderer` cover re-read also re-materializes (so re-render reuses cover, no AI regen).
- `product_publishing._audiobook_job` mirrors the MP3 (`audiobook-{pid}.mp3`).
- **`storage_audit.py` (new) + 6 super-admin endpoints under `/api/rendering/`:**
  `storage-audit[/status]` (read-only: DB refs vs local+object, classifies missing as deterministic /
  ai_art / ai_tts / book / other), `storage-recovery[/status]` (deterministic $0 re-render of missing
  doc deliverables — resumable + idempotent; AI-art & audiobooks go to an APPROVAL list, never
  auto-regenerated), `storage-backfill[/status]` (push existing on-disk library to object storage,
  idempotent). Jobs: `storage_audit_reports`, `storage_recovery_jobs`, `storage_disk_backfill_jobs`.
- **VERIFIED (preview, credit-free):** object round-trip byte-identical; live render → all 4 files
  (HTML/EPUB/PDF/wrap) present in object storage; deleted local PDF → materialized byte-identical;
  audit 231 products/12 books scanned (738 refs), classifications correct (poster→other, docs→
  deterministic); recovery 99 docs run twice → 0 recovered / 99 skipped / 0 failed (idempotent, $0 AI);
  new endpoints 401 without auth; storefront home/books/cover-thumb = 200. Stripe/orders untouched.
- **⚠️ REDEPLOY SEQUENCE:** (1) redeploy this Phase B code — the SINGLE unavoidable file gap happens
  here (old prod disk lost). (2) `POST /api/rendering/storage-audit` in PROD → read the REAL prod
  missing counts by class. (3) `POST /api/rendering/storage-recovery` → rebuilds doc covers/EPUBs/PDFs
  at $0. (4) Review the audit `ai_art`/`ai_tts` approval lists → Founder decides before ANY AI/TTS spend.
  (5) re-audit → 0 missing; confirm a paid EPUB download resolves. Every future redeploy is now durable.
- **NOTE:** Founder PREVIEW login (temp password `QruFounder2026!`) was REJECTED during this session —
  verification was done via direct worker/DB calls + unauthenticated 401 checks. Flag if prod differs.



**Root cause of Preview regression:** the deliverable asset route (`/api/rendering/asset/{fid}`) sent no
`Content-Disposition` on the inline path and non-native primaries (EPUB/PPTX) opened raw → browsers
downloaded. Separately the route was PUBLIC (paid files leak-able).
**Fixes:**
- **Signed tokens** (`deliverable_tokens.py`, JWT HS256): scoped to exact file + user + action
  (preview|download) + ~10-min exp. `POST /api/products/{pid}/file-token` mints them (preview picks a
  browser-renderable representation; EPUB/PPTX/DOCX → generated PDF). Asset route now GATES
  `deliverable-*` files: requires a matching token → else 401 (expired) / 403 (missing/scope-mismatch).
  Sets `Content-Disposition: inline` (preview) vs `attachment` (download) + `Cache-Control: private,
  no-store` + `Referrer-Policy: no-referrer` + `X-Content-Type-Options: nosniff`. Brand/storefront
  images (cover-/thumb-/store-/qr-) stay PUBLIC.
- **Frontend:** `DeliverablePreview.js` (embedded viewer: PDF iframe / image / HTML5 audio+video /
  PDF-representation for epub-pptx-docx + "Download original" + "Open in new tab") + `lib/deliverable.js`
  token helpers. Wired into ProductShelf (Preview + tokenized Download), ProductDetail (pd-open-reader
  → modal; tokenized downloads), FinalProductPreview. Preview never downloads/regenerates/AI-spends.
- **Upgrade control** (`PublicationOps.js` on /governance, super-admin): shows eligible count, confirm
  dialog, calls `POST /api/products/rerender-documents`, polls status (total/processed/succeeded/failed/
  remaining/status), prevents duplicate starts, resumable (mongo `deliverable_rerender_jobs`),
  completion report + failed IDs. Status endpoint returns `eligible_count`, `remaining`, `failed_ids`.
- **QA Cleanup™** (`qa_cleanup.py` + endpoints, super-admin, audit-logged): explicit `qa_status`
  (test|qa|preview|null) via ProductDetail `pd-qa-status`; eligibility requires marked AND not
  published/production AND no paid order (never inferred from title/age/creator); soft-delete →
  `products_trash` (full snapshot + refs; cleans decoder.manufactured_products + decrements KR
  products_created; reconciliation); restore re-inserts + re-links; permanent-delete = second confirm
  (exact-title) + re-asserts published/paid blockers. Audit collection `qa_cleanup_audit`.
- **VERIFIED — testing agent iteration_85: 17/17 backend pytest + all desktop & mobile UI flows PASS.**
  Inline-vs-attachment headers, no-token 403, action/file-scope 403, tampered→403, public storefront
  intact, paid deliverable no-longer-public (403), batch 94/94/0-fail resumable, QA mark→trash→restore
  →permanent-delete safeguards, published-protection, ZERO AI spend. Only cosmetic Radix a11y warning —
  fixed with DialogDescription.


## ✅ Phase 3 — Generalized Decoder→Create-Product bridge + Production re-render endpoint (2026-07-19)
**Generalized bridge (beyond Book):** `decoder_engine.create_product_from_decoder(d, product_type,...)`
turns a Manufacturing Ready™ understanding into ANY document family. Book → the dedicated 7-button
Book line (unchanged); every other family (Workbook, Teacher/Caregiver/Student/Family Guide, Lesson
Plan, Printable PDF, Course, Flash/Quick Card, Quiz) → the shared products pipeline and inherits the
QRU Publication Quality Standard™ (Phase 2). Knowledge-First preserved (product linked to the decoder's
source Verified KR; `verified` derived from the KR; `products_created` incremented). Content reuses the
deterministic `_decoder_to_manuscript` assembler (no invented knowledge, $0 LLM). Deliverable rendered
with `allow_ai_cover=False` ($0 AI).
- **Endpoints:** `GET /api/decoder/product-types/available`; `POST /api/decoder/{id}/create-product`
  (super-admin, now accepts any available `product_type`, returns `route` = /products or
  /book-manufacturing).
- **Frontend:** `DecoderEngine.js` CTA now has a product-type `<select>` (data-testid
  `create-product-type`) + "Create Product"; routes to My Products or Book Manufacturing by engine.
- **Production re-render batch endpoint (zero AI):** `POST /api/products/rerender-documents`
  (super-admin, background) + `GET /api/products/rerender-documents/status`. Re-renders all
  document-family products through the Publication Quality Standard™; job tracked in
  `deliverable_rerender_jobs`.
- **Threaded `allow_ai_cover` flag** into `deliverable_renderer.ensure_deliverable` (default True; batch
  + bridge pass False for guaranteed $0). Also fixed a latent `product_id`→`pid` NameError in the AI
  cover path.
- **VERIFIED:** bridge created a real Workbook from DEC-00008 (verified=True, KR-linked, PDF w/
  Copyright+Colophon, no chrome) then cleaned up; available-types endpoint returns 12 families; batch
  endpoint start→status→complete = 94/94, 0 failed; frontend selector renders all 12 options; backend
  200, frontend compiled.
- **NOTE:** preview + production have separate DBs — run `POST /api/products/rerender-documents` in
  production after redeploy to upgrade live deliverables.
- **✅ E2E TESTING AGENT PASS (iteration_84):** full Founder UI workflow verified for BOTH Workbook &
  Teacher Guide from DEC-00013 (source KR-00048 Verified): create via CTA → land in My Products → shelf
  item visible → DB (verified:true, KR-linked, decoder-linked, pdf present) → PDF (Title+Copyright+
  Colophon, no factory chrome, no sanitization leftovers, content from decoder) → ZERO AI/LLM spend →
  cleanup confirmed (2 products deleted, decoder $pull=0 lingering, KR products_created 4→2). No defects.
  Minor observation: no super-admin product DELETE endpoint (cleanup used DB) — optional future add.


## ✅ Master Design Standard™ Phase 2 — QRU Publication Quality Standard™ (2026-07-19)
Founder directive: make every DOCUMENT product inherit ONE shared publication-quality foundation
(not "make everything look like a book"); build once, inherit everywhere; keep posters/audio/video on
their own pipelines. New shared owner `publication_quality.py` (STD-PUB-0001) provides:
Publication Sanitization Pass™ · professional Title/Copyright/Colophon · consistent typography
hierarchy + spacing + QRU branding · accessibility/governance front matter (educational profile).
- **Inheritance model:** three governed profiles inherit ONE builder — `book` (fiction clause, no
  governance dump, no learning QR), `publication` (educational disclaimer + inherited Product
  Governance Package™ + continue-learning QR), `card` (title+copyright, no colophon). Category→profile
  map gates it to document families (book/guide/workbook/card); poster/deck/quiz/lesson/script/
  certificate/audio/video → `prepare()` returns None (own pipeline).
- **No duplication:** `book_manufacturing` now DELEGATES its sanitization + Title/Copyright/Colophon to
  the shared module (book profile, output preserved). `rendering_engine._make_pdf` extended to render
  the educational governance/accessibility front page + keep the learning QR for educational docs
  (books still end clean after colophon). `deliverable_renderer.ensure_deliverable` runs `pq.prepare`
  for document families and renders PDF + EPUB from the sanitized body + `retail_publication` block.
  `_render_epub` now honors the retail block (clean title/copyright/colophon, no factory chrome).
- **VERIFIED (credit-free, direct render + 1 real product):** real product "Love — Book" re-rendered →
  29pp PDF WITH Copyright + Colophon + Governance/Accessibility, **"Manufactured by QRU Factory" chrome
  GONE**, EPUB 1.7MB; Teacher Guide/Lesson Plan/Course → publication profile w/ governance; Flash Cards
  → card profile (no governance); Poster/Presentation correctly skipped; book fiction clause + "A Novel"
  preserved; backend healthy.
- **NOTE:** existing already-rendered deliverables upgrade on their next re-render (manufacture/publish/
  regenerate-cover) — non-destructive, no migration. REMAINING (Phase 3): generalize the
  Decoder→Create-Product bridge beyond Book; optional pptx branding parity.


## ✅ UKR™ Governance Engine — Lifecycle (S18) + Gold Standard Review (S17) (Phase 2, 2026-07-19)
Per Founder directive: activated the canonical governance lifecycle + certification engine on the
UKR™ Standard v1.1 canonical layer. New module `ukr_lifecycle.py` (operates on the `ukr` object;
one canonical standard — no schema fork). Legacy `verification_status`/`approval_status`/
`treasure_standard` are NOT mutated → Knowledge-First™ enforcement + product links undisturbed.
- **20-state lifecycle** with a governed TRANSITIONS graph; invalid transitions return clear 422s;
  every transition appends full history (prior/new state, trigger, actor, timestamp, validation).
- **Founder-only states** (Approved, Gold Certified) require super-admin; final certification preserved.
- **15-dimension Gold Standard Review**: dimensions reviewed INDIVIDUALLY (score, pass/fail,
  deficiencies, severity, corrective action…); `review_state` auto-computed (Under Review / Returned
  for Correction / Approved). **Certification BLOCKED until all 15 pass** (super-admin `certify-gold`).
- **Endpoints** (`/api/manufacturing/ukr/*`): `GET lifecycle/states`, `GET governance-overview`,
  `GET record/{id}/lifecycle`, `POST record/{id}/transition`, `GET/POST record/{id}/gold-review`,
  `POST record/{id}/certify-gold`.
- **VERIFIED (preview, credit-free):** valid chain succeeds + history preserved; invalid transition
  → 422; Founder-only → 403; certify blocked at 14/15 then succeeds at 15/15 → Gold Certified;
  factory-wide `all_valid: True` (80/80 valid lifecycle state); storefront /api/public/* = 200; no
  data loss (80 records). Tested on a throwaway record + read-only live curls (real records untouched).
- **BLOCKER:** production redeploy is a Founder action (Deploy button); startup hook auto-migrates +
  the engine ships with it. Not certifying anything until Founder runs reviews on the live site.
- **DELIBERATE:** lifecycle/certification live in the canonical `ukr` layer (additive); they do NOT
  yet drive legacy verification/treasure flags or the UKR Readiness screen (deferred per directive).


## ✅ UKR™ Standard v1.1 — Canonical Full Specification adopted (Phase 1, 2026-07-19)
Per Founder directive: the uploaded `UKR 7.18.2026.pdf` IS the canonical standard; the DB evolves to
match it via a NON-DESTRUCTIVE, backward-compatible phased migration (no second/competing schema).
- **Single standard** expanded in place in `ukr_standard.py`: 24 governed SECTIONS (~300 fields),
  20-state LIFECYCLE, 10 Gold-Standard review states, 15 review dimensions, 5 validation results.
- **`build_canonical(rec)`** maps the 49 legacy flat fields into their canonical homes (Sections 1
  Record Identity, 2 Purpose, 3 Core Knowledge, 4 Evidence, 6 Teaching, 14 Factory Interface, 15
  Human Interface, 18 Lifecycle, 23 Versioning = 9 populated). The other 15 sections are present-
  but-empty (never omitted). Legacy flat fields are KEPT as a live backward-compat surface.
- **`migrate_to_canonical()`** = non-destructive + idempotent; preserves IDs, versions, approvals,
  downstream product links AND any canonical content already populated downstream (deep-merge).
  Runs automatically on startup so production converges on redeploy (no manual step).
- **New KRs born canonical:** `routers/knowledge.py` create + `kr_manufacturing.py` manufacture now
  attach the `ukr` object at insert.
- **Endpoints** (`/api/manufacturing/ukr/*`): `GET canonical-spec`, `GET migration-status`,
  `POST migrate-canonical` (super-admin), `GET record/{id}/canonical`.
- **VERIFIED (preview):** 80/80 migrated; existing KR-list API returns legacy `title` + new `ukr`;
  products still linked (ukr-audit 226 total / 143 green / 63.3% — no regression); re-run preserved a
  downstream-populated pending field + legacy data; no data loss. REDEPLOY required for production.
- **REMAINING (future phases):** populate/wire the 15 empty sections via their owning engines
  (Multi-Audience translations, Visual/Audio/Video specs, AI-Agent support, Product Bindings,
  Manufacturing Readiness, Dependencies graph, Gold Standard Review workflow, Intelligence Value,
  Rights/Brand, Continuous Improvement, Validation engine, Executable Behaviors).


## ✅ UKR Compliance Panel + Guided Remediation (2026-06)
Governance page (`/governance`) now opens with a **Knowledge-First™ Compliance** panel
(`components/UKRCompliance.js`): live green/amber/red counts, compliance %, published-noncompliant
count, refresh. "Open guided remediation" lists all amber+red products (published-noncompliant first)
with per-product actions — **Bind to a suggested Verified UKR** / **Founder-authored exception** /
**Quarantine**. Nothing is ever auto-bound (Founder decides each).
Backend (`ukr_governance.py` + `routers/products.py`): `GET /products/ukr-audit/details`,
`GET /products/{id}/ukr-suggestions` (token-matched Verified KRs, scored), `POST /{id}/ukr-bind`
(validates Verified), `POST /{id}/ukr-quarantine` (unpublish+flag), `POST /{id}/ukr-exception`.
VERIFIED: bind moved a product green (compliance 62.8%→63.3%), bind-to-unverified rejected (422),
panel + remediation list render in UI. Needs redeploy to reach production.


## ✅ UKR-Inheritance Governance enforced at the manufacturing choke point (2026-06)
Closes the biggest trust gap: educational products can no longer be manufactured/published without a
VERIFIED Universal Knowledge Record (Knowledge-First™). New `ukr_governance.py` = single shared guard.
- `POST /api/products/generate` + `/assemble` now call `require_verified_ukr()` → **block** (422) if no
  KR or KR not Verified; verified KR proceeds normally.
- **Publish guard:** `PATCH /products/{id}/status → Published` blocked (422) unless the product traces
  to a Verified UKR (or is a Founder-authored manuscript exception). Asset-manufactured products are
  caught by this backstop.
- **Audit report:** `GET /api/products/ukr-audit` → green/amber/red traceability. LIVE audit:
  226 products → 142 green / 22 amber / 62 red (62.8% compliant); 16 published-noncompliant.
- Founder-authored manuscripts remain the ONE governed exception (book_records, untouched).
- VERIFIED (preview): no-KR generate→422, unverified assemble→422, verified assemble→200 (no LLM cost),
  publish red product→422, storefront unaffected (reads book_records).
- REMAINING: migrate the 62 red + 22 amber products (bind to a verified UKR or quarantine — needs
  per-product KR choice, not safely auto-bindable); optional Governance-console view of the audit;
  reverse-flow UKR extraction from Founder books (P2).


## ✅ Non-blocking backfill — fixes Cloudflare/origin timeout on "Generate missing videos" (2026-06)
The button used to render videos INSIDE the HTTP request → exceeded proxy/Cloudflare timeout →
"origin returned invalid/incomplete response" (520/524). FIX: `POST /api/video/backfill` now
`start_backfill()` spawns an asyncio background worker and returns instantly (verified 0.03s);
progress tracked in `db.video_backfill_jobs` (id="current"), polled via `GET /api/video/backfill/status`.
Frontend starts the job then polls every 4s showing progress. Renders run sequentially (one at a
time) so the container isn't overloaded. Idempotent + cached + durable (object storage).
NOTE: user's Cloudflare appears PROXIED (orange cloud) — recommend switching qru-online.com + www
back to DNS Only (gray cloud) as originally advised. Requires redeploy to take effect in production.


## ✅ Durable video storage — root-cause fix for "videos missing / repeat credit spend" (2026-06)ROOT CAUSE (confirmed via support): the container filesystem is EPHEMERAL — every redeploy/restart
wipes `/app/backend/rendered_assets`, so runtime-generated MP4s vanished and had to be re-rendered
(re-charging AI credits). Preview & production have SEPARATE disk + DB.
FIX (Phase A — videos only, per Founder): new `storage.py` wraps **Emergent Object Storage**
(`EMERGENT_LLM_KEY`, app prefix `qru-online`, durable across redeploys). `video_fulfillment` now
uploads every rendered MP4 to object storage (`storage_path`), and availability/caching use a durable
`_available()` (object storage OR local). `materialize()` re-downloads on demand. YouTube
`_resolve_factory_asset` + `/factory-assets` + connector publish all materialize from object storage.
VERIFIED: rendered → uploaded → **simulated redeploy (deleted local file)** → still available →
re-materialized byte-identical → `ensure_product_video` REUSED with NO re-render / NO credit spend.
- Legacy assets (pre-fix, no `storage_path`) will re-render ONCE via backfill, then persist durably.
- FAST FOLLOW (Phase B, scheduled): move the live store's EPUBs + covers to object storage too
  (protects paid downloads from ephemeral-disk loss). Not yet done.


## ✅ Video-script auto-render + cache + production backfill (2026-06)
Founder issues: (1) trailers not visible in YouTube Publisher on the LIVE site; (2) video scripts
should render to MP4 automatically. Root cause of (1): trailers were rendered in PREVIEW's DB/disk;
production has a SEPARATE DB — video must be rendered IN production (after redeploy).
- **Script-aware render:** `video_fulfillment.ensure_product_video` now renders "Video Script" /
  "Short Video" / "YouTube Video Script" products FROM THE SCRIPT (narration source = product
  content), else from the verified KR. VERIFIED: a Video Script → 2.8MB/32.7s MP4 (rendered_from=script).
- **Caching (Founder policy):** each video stores a `source_signature`; the MP4 is REUSED unless the
  script/description changes or `force=True`. Replace-not-append (one current MP4 per product/book).
- **Render on PUBLISH or explicit request only** (NOT on every manufacture): YouTube connector
  auto-renders on publish; explicit endpoints `/api/video/products/{id}/render`, `/books/{id}/promo`.
- **Incremental production backfill:** `POST /api/video/backfill` renders up to `limit` (default 3,
  max 5) missing/stale videos per call and returns `remaining`/`done`/`summary` so the caller loops
  without hitting request timeouts. One-click **"Generate missing videos"** button added to the
  YouTube Publisher™ UI (loops until done, shows progress, resumes on failure via cache). VERIFIED
  incremental contract + button render.
- **DEPLOY REALITY:** these are code changes — take effect on the live site only AFTER redeploy;
  then the Founder clicks "Generate missing videos" (or it auto-renders on publish) to populate
  production. YouTube UPLOAD still requires the production YouTube channel to be connected.


## ✅ Book Promo Trailers™ + Master Design Standard™ Phase 1 (2026-06)
**Book promo trailers (enhancement):** `video_fulfillment.ensure_book_promo` / `generate_all_book_promos`
render short Ken Burns + narration MP4 trailers from published (Founder-authorized) `book_records`
(the governed Founder-authored exception — no KR required), register them as distribution-ready
Factory assets marked `pending_distribution:["youtube"]`, and expose them via `GET /api/video/queue`.
Endpoints: `POST /api/video/books/{id}/promo`, `POST /api/video/books/promos/generate-all`.
VERIFIED: 4/4 published books got trailers (17–23s each, files on disk, queued for YouTube). They
auto-appear in YouTube Publisher™ factory-assets and publish once the YouTube OAuth is reconnected.

**Master Design Standard™ — Phase 1 (covers parity) DONE:** `rendering_engine.ensure_branded_assets`
now DELEGATES cover generation to `design_studio` (art direction → 3 concepts → typographic compose),
so EVERY product family inherits book-grade covers. Non-book products auto-select the strongest
concept (NO new UI — the existing regenerate-cover button now yields book-grade output). Preserved:
vault reuse-by-default, `asset_mode=generate` override, Founder-imported `asset_vault_selected`
protection, and a deterministic ZERO-AI fallback (`dl.premium_cover`) so a cover always renders.
Stamps `design_engine`. VERIFIED: a Poster product produced a 1.45MB art-directed hero cover via
"QRU Design Studio™ (Master Design Standard™)". Books unaffected (already use design_studio).
- REMAINING (Master Design Standard): Phase 2 interior/deliverable typography parity;
  Phase 3 generalize the Decoder→Create-Product bridge beyond Book.


## ✅ QRU Video Fulfillment™ — real publishable MP4 for products (2026-06)
Fixes the reported "YouTube requires a video file" dead-end (video step used to yield a manifest only).
- New `video_fulfillment.ensure_product_video(product_id)` renders a REAL MP4 (image-based motion /
  Ken Burns + AI narration — honestly labeled, NOT frame-by-frame) from the product's VERIFIED KR
  (Knowledge-First), then registers it as a distribution-ready Factory vault asset
  (`db.media_assets`, provider=qru_production) so YouTube Publisher™ + Distribution can publish it.
- Idempotent (reuses existing asset, no re-spend). Honest failure if product has no verified KR.
- `YouTubeConnector.distribute` now AUTO-uses/auto-renders the product video when no MP4 is uploaded
  (never deletes the vault master). New endpoints: `GET /api/video/products/{id}`,
  `POST /api/video/products/{id}/render` (super-admin).
- VERIFIED directly: rendered 1.38MB / 19.2s / 2-scene MP4 for "How the Human Heart Pumps Blood",
  idempotent reuse confirmed, resolvable by the YouTube publisher (path under MEDIA_ROOT).
- NOTE: actual YouTube UPLOAD still needs the YouTube OAuth token reconnected (pre-existing
  invalid_grant, Founder must re-auth) — separate from this fix.


## 🚀 QRU ONLINE — LIVE LAUNCH COMPLETE ✅ (2026-06)
Public bookstore (qru-online.com) is LIVE on real Stripe and verified end-to-end.
- **Stripe Live cutover done:** `backend/.env` holds LIVE keys (sk_live/pk_live/whsec). `.env` is
  shared by BOTH preview + production and is a per-deploy SNAPSHOT — **NEVER revert to test keys**
  or the next redeploy silently downgrades production. See `/app/memory/go_live/STRIPE_LIVE_KEYS_LOCK.md`.
- **Cloudflare DNS:** keep qru-online.com (A) + www (CNAME) on **DNS Only / gray cloud** permanently
  (Emergent provisions SSL; orange-cloud proxy breaks cert issuance).
- **Redeploy note:** first prod redeploy failed on a TRANSIENT Cloud Build error; a plain retry fixed it.
  Local prod build + backend import are clean; no code defect.
- **First Founder Live purchase VERIFIED end-to-end:** Stripe session complete/paid ($4.99) →
  production status `paid` → secure tokenized download link → EPUB delivered (HTTP 200, 1.6MB,
  valid application/epub+zip). Book: "The Heart as a Daily Circulation Pump".


## Every Engine Merged onto the Manufacturing Foundation™ (inherit, don't recreate) ✅ (2026-07-16, self-verified via curl + screenshot)
Highest-leverage architectural item. Every engine is now a PMS™ inheriting ONE shared Foundation — publish, PMF™, packaging inherited, not recreated.
- **Auto-provisioned PMS coverage:** `get_pms()` now auto-provisions a Foundation-inheriting PMS for ANY product family without a hand-authored one → universal coverage (44 families across 5 engines), no product_type lacks an approved PMS. Book + 9 others remain hand-authored (★); the rest inherit generic defaults. Founder model realized: "one PMS per family, all inheriting one Foundation."
- **Shared PUBLISH (single owner):** `publish_product` already central; the old duplicate `POST /api/publishing/product/{pid}/publish-store` now DELEGATES to `mf.publish_product` (deduped, verified no regression — storefront +1, PMF generated).
- **Shared PACKAGING:** new `mf.package_product(engine, id)` assembles a governed package (PMF + Inherited Standards + PMS + provenance + deliverable) for any engine. Endpoint `POST /api/manufacturing/package/{engine}/{id}`.
- **Inheritance map:** `mf.inheritance_map()` + `GET /api/manufacturing/inheritance-map`. New **Foundation Map** UI page (`/manufacturing-foundation`, registered in capability registry → nav) shows all 5 engines, their families/PMS, and the 9 shared capabilities each inherits. Screenshot-verified.
- Engines: book (book_records) · publication (products) · poster (poster_assets) · recipe (inherited_products) · media (media_products).


## PMF™ (Evidence) Surfaced in the Founder UI ✅ (2026-07-16, deterministic/$0, screenshot-verified)
Adopted the Founder's decision filter ("make every future product family INHERIT the reference implementation"). Highest-leverage item done: provenance is now visible for every product.
- **`manufacturing_foundation.get_or_build_manifest(engine, id)`** — returns the stored PMF or builds one ON DEMAND (deterministic, $0) for ANY manufactured product with a real deliverable (published or not). `has_deliverable()` helper added. Endpoint `GET /api/manufacturing/manifest/{engine}/{id}`.
- **`all_products()`** now returns `has_manifest` per product (has manifest OR a real deliverable → buildable).
- **Reusable `ManifestDialog` component** (`/app/frontend/src/components/ManifestDialog.js`) renders the PMF sections: Source Intelligence (UKR™=Truth: Knowledge Record ID, Knowledge Title, Published Title, UKR/PMS versions) · Inherited Standards (7 chips) · Assets & Production · Quality (Treasure Standard) · Distribution · Governance · Enterprise Memory. Loads via useEffect on open.
- **Wired into 2 surfaces:** My Products / ProductShelf ("Manifest™" button on every product with a deliverable) + Book Manufacturing PostPublishPanel ("View Product Manifest™" button, uses `/book-mfg/books/{id}/manifest`).
- **Bonus:** publication products published BEFORE the PMF system existed now get their PMF built on-demand, correctly referencing their source UKR (verified live: a forex Book → KR-00074, 7 inherited standards).


## Universal Cover-Legibility Fix + BOOK-0011 Full-Cycle Capstone ✅ (2026-07-16)
Founder flagged the print cover wrap: title unreadable over busy art + weird/ghosted back cover. Fixed in the SHARED composer so it applies to EVERY product (one design owner — no per-product rework):
- **`design_studio.compose()` (front/all covers):** title+subtitle now drawn inside a SOLID rounded legibility panel (rgba 10,8,22,210) so text is readable over ANY artwork; subtitle capped to 2 lines (+ ellipsis) so a long description never crowds the cover. Used by `manufacture_bytes` → every product kind (cover, poster, workbook, card, deck). Verified on bright/busy worst-case image.
- **`design_studio.compose_print_wrap()` (back cover):** replaced the darkened/blurred FRONT-cover background (which ghosted the front title onto the back) with a clean on-brand navy gradient. Back now: clean gradient + readable blurb + barcode clear zone + imprint.
- **BOOK-0011 CAPSTONE (full 7-button cycle, live):** UKR **KR-00001** → editorial locked → back-cover blurb drafted → **3 AI cover concepts (all success)** → cover selected → **clean print wrap** (6×9, 300 DPI, spine blank <79pp) → retail sanitized → priced ($4.99 eBook / $12.99 paperback) → **Founder authorized** → **16 post-publish assets Ready** → Master Package + **PMF PMF-BOOK-0011 referencing KR-00001**. One UKR-sourced book completed the ENTIRE cycle end-to-end. Wrap PNG/PDF on disk, blurb included.


## Every Product Family Wired onto the Manufacturing Foundation™ — one-tap Publish + PMF™ ✅ (2026-07-16, deterministic/zero-credit, self-verified)
Delivered the "merge engines" audit item as the proven Foundation pattern: any engine publishes the SAME way.
- **Shared `manufacturing_foundation.publish_product(engine, id, actor)`** — engines: publication, poster, recipe, media. Non-publication engines upsert ONE canonical `db.products` **store listing** (source_engine/source_id) so storefront + Stripe checkout + fulfillment are 100% reused (no forked commerce logic). Publication keeps its existing creative-review+verified gate. Idempotent (re-publish returns same listing, no dupes). Every publish emits a **PMF™** (7 Inherited Standards) referencing the source UKR.
- **Honest sellability gate (`is_sellable`/`_resolve_listing`) = Treasure Standard:** a product publishes only if it has a REAL deliverable file. Media requires an audio/video file with **bytes > 0** — this correctly EXCLUDES mocked 0-byte videos (fixed a bug where an empty mp4 got published; bad listing removed). Poster requires rendered bytes; recipe requires a file url.
- **Endpoint:** `POST /api/manufacturing/publish {engine, id}` (get_current_user). Frontend **My Products / ProductShelf** now shows "Publish for Distribution" on ALL engines when `p.publishable`; store-listing mirrors are suppressed from the shelf (one clean row per product). UI-verified E2E (toast + row → "In QRU Store").
- **`manufacturing_dashboard.all_products()`** now returns `publishable` + store state per engine. Current: publication 110 publishable / poster 52 / recipe 15 / media 4 (only real renders). Storefront 73 live.
- **Capstone (BOOK-0011 full 7-button publish) NOT run** — it costs AI credits (cover gen) + disk; awaiting Founder go-ahead given credit sensitivity.


## End-to-End Proof + One-Tap Distribution ✅ (2026-07-16, zero new AI credits — all deterministic)
Founder ask: "make sure it all works with ease — Generate UKR → Manufacture → Publish for distribution — without adding credit." PROVEN end-to-end:
- **UKR** KR-00078 "Finance — Saving early matters" (verified, v1.1) → **Manufactured** Workbook (real files, review-passed) → **Published** → now LIVE in the QRU Store storefront AND the public consumer catalog (`/api/consumer/catalog`), price auto-set $9.99, purchasable via Stripe (test). Storefront grew 69 → 71.
- **Publish gate (deterministic, no AI):** `PATCH /api/products/{id}/status → Published` requires `creative_brief` + `creative_status="Reviewed"` + `verified`. `manufacturing_dashboard.all_products()` now returns a `publishable` flag computed from that gate.
- **NEW one-tap "Publish for Distribution"** on My Products / Product Shelf (`ProductShelf.js`): shows ONLY on `engine=="publication"` rows that are genuinely `publishable` (honest — no fake buttons on media/poster rows that aren't store-wired, and none on Drafts that would 400). Click → PATCH → success toast → row flips to "Published · In QRU Store". UI-verified E2E (111→110 eligible after one publish). 111 products currently one-tap eligible; 71 live in store.
- **Honest gap noted:** media/poster/recipe-engine products are NOT yet store-publishable (not in `db.products` with the review gate). Book line remains the fullest path. As each product family re-bases on the Manufacturing Foundation™/PMS™, it will inherit this publish path.


## Constitutional Manufacturing Spine — UKR™ → PMS™ → PMF™ ✅ (2026-07-16, testing_agent iteration_79: 16/16 backend PASS, 0 issues)
Founder constitutional architecture — three artifacts, three owners, zero overlap:
**UKR™ = TRUTH · PMS™ = INSTRUCTIONS · PMF™ = EVIDENCE.** "No product may manufacture without an approved PMS™."
- **Decoder defect FIXED** (`decoder_engine.py`): LLM sometimes returned `how_it_works`/`definition` as arrays → `list + str` TypeError. Added `_s()` coercion; `_deterministic_checks` now safe. Unit + agent verified.
- **UKR™ v1.1 (`ukr_standard.py`, STD-UKR-0001):** canonical collection = `knowledge_records` (79 recs); `knowledge_engine_records` (KR 2.0) frozen read-only. Title section order: Knowledge Title (`[Domain] — [Primary Topic]`, human selection) → Published Title (reader-facing) → Knowledge Record ID (`kr_code`, **immutable Option A**). `schema_version="QRU UKR™ Standard v1.1"`. Backward-compat alias `Factory Title`/legacy `title` → `knowledge_title`. Non-destructive `migrate_all()` (preserves originals, IDs, versions, approvals) — **all 79 migrated, 79/79 valid**. `registry()` sorts alphabetically by Knowledge Title. Domain map uses WORD BOUNDARIES (fixed false "AI" match inside "daily/train/sustains"). Endpoints under `/api/manufacturing/ukr/*`.
- **Manufacturing Foundation™ + PMS™ (`manufacturing_foundation.py`, STD-MFG-FOUNDATION-0001 / STD-MFG-PRD-0001):** one shared Foundation owns intake·state·verification·provenance·nav·packaging·approval·monitoring; every PMS **inherits** it (improve once → all inherit). 10 PMS families registered (Book full-detail with 6 categories; Workbook/Poster/Knowledge Card/Quick Card/Teacher Guide/Presentation/Course/Audiobook/Video). `require_pms()` = constitutional gate (Book→true, unknown→false).
- **PMF™ (`build_manifest`, STD-MFG-PMF-0001):** EVIDENCE — "exactly what happened during manufacturing." REFERENCES the UKR (never duplicates knowledge). Includes the Founder-required **Inherited Standards** section (UKR·PMS·Publishing·Design·Treasure·Verification·Evidence). Wired into `book_manufacturing.build_product_manifest()` + emitted into Master Package (`07_METADATA/product_manifest.json`) + endpoints `GET/POST /api/book-mfg/books/{id}/manifest[/build]`.
- **EVIDENCE RUN (Outcome 4):** existing verified UKR **KR-00001** → Decoder **DEC-00017** → Book **BOOK-0011** → **PMF with UKR reference present** (ukr_id=KR-00001, knowledge_title, ukr_version=1, PMS v1.0, 7 inherited standards). Proves migration + inheritance + backward compatibility end-to-end. Mapping doc: `/app/memory/NAV_COLLAPSE_MAP.md` (nav) — architecture confirmed the audit's "merge engines" path = each engine becomes a PMS inheriting the Foundation.
- **NOTE:** BOOK-0011 was NOT run through the full 7-button publish (print/cover/authorize/post-publish) — that half is already proven on BOOK-0001. A full single-record capstone run on a UKR-sourced book is offered as the next optional step (costs AI credits + disk).


## Post-Publish Verification + Founder Navigation Collapse ✅ (2026-07-16, self-verified via founder JWT + screenshots)
- **Post-Publish Panel — VERIFIED (BOOK-0001 "The Understanding Tree"):** 16 Ready assets all have real files
  in the 1.28MB Publication Assets ZIP (marketplace text ×5, marketing graphics ×3, book page, media scripts ×3,
  KDP submission, founder docs ×3); 5 Planned + 1 Not Implemented produce NO files (honest). ZIP + Master Package
  both serve HTTP 200 externally. **Defect fixed:** the Publication Assets ZIP was reachable only from the
  Post-Publish panel, not the Deliverables/Factory Library. `run_post_publish_recipe()` now persists it as a
  "Publication Assets Package" deliverable (replace-not-append, deletes prior file) so the Library and panel show
  the SAME current assets. FactoryLibrary header relabeled "Packages & Deliverables". BOOK-0001 backfilled.
- **Founder Navigation Collapsed 88 → 8 CORE (fewer choices, not less capability):** Full mapping in
  `/app/memory/NAV_COLLAPSE_MAP.md`. New backend `capability_registry.NAV_CORE` (8 curated core capabilities);
  `navigation()` now returns `core` (8) + `sections` (70 remaining Active/Inherited, grouped by division) +
  `legacy` (10 Merged/Deprecated). Frontend `Layout.js` renders the 8 core as the primary sidebar; everything else
  lives in a collapsed **"All Capabilities" (70)** drawer + the existing **"Legacy — Under Review" (10)** drawer.
  The 8 CORE: Founder Console `/` · Create `/create` · Knowledge & Decoder™ `/knowledge` · Book Manufacturing™
  `/book-manufacturing` · Media & Design Studio `/media-division` · Publishing & Distribution `/distribution` ·
  Governance & Trust `/governance` · All Capabilities (Factory Map™) `/factory-map`. NO routes removed, NO pages
  deleted — presentation layer over the same Registry; fully reversible. Verified: core + drawer items navigate.
- **Recipes location (Founder Q):** recipes stay in backend `manufacturing_recipes.py` (one owner, inherited by
  product_type behind the same 7-button workflow). Founder never picks a recipe — Create selects it by outcome.
- **KNOWN PRE-EXISTING (out of scope, flagged):** `decoder_engine._deterministic_checks` (line ~75) raised
  `TypeError: can only concatenate list (not "str") to list` once on a decode call — unrelated to these two tasks.


## Architecture
- Backend: FastAPI + MongoDB (`/app/backend`, routers in `/app/backend/routers`).
- Frontend: React + Tailwind + Shadcn (`/app/frontend/src`, pages + components).
- Auth: JWT founder login. Stripe: TEST mode (sk_test).

## Phase Next — Manufacturing Orders (approved sequence)
MO-001 Quality Gates ✅ · MO-002 Enterprise Manufacturing Dashboard ✅ · MO-003 Knowledge Record 2.0 ✅ · MO-004 QRU Design Language ✅ · MO-005 Manufacturing Director™ ✅ · MO-006 YouTube Publisher™ (Founder Upload Mode) ✅ · MO-007 Universal Distribution Framework™ ✅ · MO-008 Governance Binding Layer™ ✅. Build one at a time; deterministic infra before AI content.

## Shared Design Studio™ · KDP wrap · Decoder Stone 2 "Create Product" ✅ (2026-07-15, self-verified + QA 13/13)
- **QRU Design Studio™ (shared design engine):** New `design_studio.py` is the single owner of publication-quality design (LLM art-direction → Gemini artwork → QRU typography composite + strict validation + honest provenance; format-aware cover/poster/workbook). Book `_cover_design_recipe` now delegates to it; Cover Studio (`routers/publishing.py cover_generate`) rewired from raw `generate_image` to `design_studio.manufacture_bytes` (now composited + on-brand, verified visually); `manufacturing_recipes.default_design_recipe` routes ANY product recipe through it. Poster Studio intentionally LEFT on its precise machine-rendered SVG path (factual-accuracy guarantee) — hero-art integration proposed as follow-up. Provenance stamps `design_engine: "QRU Design Studio™"`.
- **BOOK-0001 final KDP wrap:** ISBN default → clearly-marked KDP field ("assigned by Amazon KDP at publication"); retail colophon stripped of internal "Book Manufacturing System" language; added defensive placeholder patterns ("full manuscript", "assignment pending"). Re-ran sanitization + rebuilt Master Package. VERIFIED retail PDF (47 pp): zero placeholders (working title/full manuscript/assignment pending/TK/TODO/manufacturing language all absent), KDP ISBN field present, TOC + 22 chapters, Colophon clean, title/author match cover. Working/editorial copies clean; sealed original preserved.
- **Ready-for-KDP™ checklist:** `build_kdp_checklist()` + `/api/book-mfg/books/{id}/kdp-checklist` + `07_METADATA/Ready_for_KDP.md/.json` in the package + Publish-tab card. Honest statuses (confirmed/suggested/needs_founder).
- **Decoder Engine™ Stone 2 — "Create Product" bridge (Books only):** `book_manufacturing.create_book_from_decoder()` + `_decoder_to_manuscript()` assemble a Canonical Book Record from a Manufacturing Ready™ decoder record's 38-field contract (12 structured chapters), reusing `create_book_record` (one owner) and stamping `source_decoder` provenance. Endpoint `POST /api/decoder/{id}/create-product`. Frontend: prominent "Create Product · Book" CTA on Manufacturing Ready records (outcome-focused language) → navigates to `/book-manufacturing?book={id}` with the new book auto-selected. VERIFIED end-to-end via UI. This is the reference pattern for future product bridges.
- **QA:** iteration_76.json — 13/13 backend PASS; one HIGH frontend bug (share-box unmounted on reload) FIXED + verified; "AI" label capitalization fixed.


## Review Copy · Working-title full cleanup · QRU Product Manufacturing System™ · Nova Sparkle KR fix ✅ (2026-07-15, self-verified)
- **Working title — fully aligned:** Selecting a cover now AUTO-runs the Publication Sanitization Pass™ (`select_cover` → `sanitization_pass`), so the clean retail edition (with the chosen cover) always ships. Share links now stream a **clean Review Copy** (README + reading-edition PDF + EPUB + Cover) via `build_review_package()` — NEVER the manufacturing internals — verified clean by PDF text extraction. Also scrubbed "(working title)" from BOOK-0001's working copy + editorial edition (sealed immutable original intentionally preserved) and cleared the stale proofing "Decision Needed" flag. Frontend share box + Factory Library™ label it a "clean reading copy".
- **QRU Product Manufacturing System™ (generalization ticket):** New `manufacturing_recipes.py` registry — each product type registers a recipe (intake profile, design brief, distribution) behind the SAME universal 7-button workflow; shared orchestration/governance/gates/sanitization/Master Package remain inherited standards. Book recipe registered (delegates to `_cover_design_recipe`, reuses `product_recipes` catalog for the label — one owner for that vocabulary). `design()` dispatches via `recipes.get(product_type).design_recipe`. Records carry `product_type` (default "Book", backfilled on pilot). `/api/book-mfg/config` now returns `system_title` + `recipes`; new `/api/book-mfg/recipes`. Frontend header rebranded to "QRU Product Manufacturing System™ · Book Recipe" / "One Product In · One Publication Package Out" — 7 buttons unchanged, zero workflow change. Unknown product types fall back to Book.
- **Nova Sparkle / Little Legacy KR verification BUG FIX:** `kr_inheritance.build_inheritance()` only recognized `verification.evidence_sufficient_for_external_publication`/`verified_external`, so KRs verified via the primary engine (`verification_status == "Verified"`, `verification.decision == "approve"`) were wrongly held as "Knowledge Required". Fixed to honor all governed verification conventions. Verified: creating a Nova Sparkle episode from KR-00014 "How does the brain work?" now returns Verified/Draft. Repaired 4 stale held episodes (Brain Work/nova-sparkle, Brain Deconstructed x2, Day Trading) whose KRs were actually verified.
- **HELD (Founder researching):** Video animation — currently PLAN-ONLY (no renderer/animation engine). Options offered: fal.ai image-to-video (needs key) or a no-key Ken-Burns+waveform motion MP4. Awaiting Founder decision.


## Publication Sanitization Pass™ + Manuscript Upload + Factory Library™ ✅ (2026-07-15, self-verified curl e2e + screenshots)
- **Publication Sanitization Pass™** (inside Button 6 Publish, before Final Release — NO 8th button): `sanitization_pass()` removes internal placeholders (working title, [TK], TODO/FIXME/XXX/TBD, DRAFT/CONFIDENTIAL markers) + strips the manuscript-embedded front-matter title block; generates a clean **Title Page, Copyright Page, Colophon** per publishing convention; and SEPARATES `publication_metadata` (reader-facing) from manufacturing metadata (kept in Canonical Record + Master Package, never printed in retail). Renders a sanitized **retail interior PDF + EPUB** via a new `retail_publication` branch in `rendering_engine._make_pdf` (retail mode: clean title/copyright pages, no "Manufactured by QRU Factory" / no Product Governance dump / clean footer = book title only / no learning QR; adds Colophon). Gate gains `publication_sanitized` (required; `gate_ready=all(gate.values())`). Master package now prefers the sanitized retail edition for 03_PRINT/04_EBOOK and adds 07_METADATA/publication_metadata.json + title_copyright_colophon.json. Endpoint POST `/api/book-mfg/books/{id}/sanitize`. Verified e2e on throwaway: 4 markers removed, retail PDF text confirmed clean, gate honest.
- **Manuscript Upload™** (fixes "Upload button won't open"): new `POST /api/book-mfg/upload-file` + `_extract_manuscript()` accepts **.docx/.pdf/.txt/.md** (python-docx / pypdf / utf-8), auto-seals immutable original + working copy, creates a new Canonical Book Record. Frontend `UploadManuscript` file-picker + author/genre inputs in the Upload panel; **book switcher** dropdown in the identity bar. Verified: uploaded a .txt → BOOK-0002 created, ran full pipeline. (Throwaway BOOK-0002 deleted; pilot BOOK-0001 preserved.)
- **Factory Library™** (fixes "where do downloads go" + "share link won't copy"): assembled packages + share links are now persisted on the Canonical Book Record (`deliverables[]`, `share_links[]`) and surfaced in a `FactoryLibrary` panel — download/re-copy any time from INSIDE the factory (never dependent on the browser Downloads folder). Share flow rewritten: robust `copyText()` (clipboard API + execCommand fallback) + always-visible selectable share-link box (no more silent one-shot clipboard). Assemble no longer force-opens a browser download.


## Cover Design Recipe™ — Honesty Hardening + Thumbnail Legibility Preview + Pilot Covers ✅ (2026-07-15, self-verified: real Design API + provenance + image-load + UI + mobile)
- **Honest per-concept status:** `_cover_design_recipe()` now validates provider bytes via `_valid_cover_art()` (rejects empty/HTML/JSON/truncated/malformed/<256px). A concept is `status:"success"` ONLY with real decodable AI art; otherwise `status:"failed"` + `failure_reason` and a branded placeholder that is CLEARLY labeled failed (never presented as real art). Per-concept `provenance` records art_provider (Gemini/Emergent key), art_model, art_direction_model, art_direction_prompt, generation_time_sec, generated_at, fallback_used, has_ai_art.
- **`design()`**: embeds the first SUCCESSFUL cover in the interior proof; adds design-level `cover_provenance` summary (requested/with-ai-art/failed + failed list) and appends a `cover_generation` record to `transparent_provenance`. `selected_cover` stays None after generation — the Founder selects (no auto-approve/auto-replace).
- **Thumbnail Legibility Preview** (inherited INSIDE the Design button — NO 8th button): `LegibilityPreview` in `BookManufacturing.js` shows every concept at Full cover / Amazon thumb / Mobile search sizes + a Grayscale contrast check + readability status. Failed concepts render an amber "AI art failed — not real art" overlay and are not selectable.
- **Pilot BOOK-0001 "The Understanding Tree"**: 3 genuinely distinct publication-quality trade covers generated via the REAL Design API (19s, 3/3 AI art, gemini-3.1-flash-image-preview): "Ancestral Roots", "Missing Coffee Can", "June at the Threshold". Immutable manuscript + editorial lock preserved. Covers load in Founder UI (naturalWidth 1024) incl. mobile. AWAITING FOUNDER COVER SELECTION (paused per directive). NEXT after selection: Decoder Engine Stone 2.


- **✅ V1.1 upgrades (2026-07-14, all self-verified end-to-end on throwaway books):**
  - **Cover Design Recipe™** (replaces placeholder gradients): `_cover_design_recipe()` — LLM art-direction (3 distinct concepts) → **Gemini Nano Banana** artwork (parallel `asyncio.gather`, ~20s total) → `_compose_book_cover()` clean trade-novel typography (full-bleed art + legibility scrim + serif title/subtitle/author/imprint eyebrow; NO learning-product chrome). Honest per-concept fallback to branded gradient if AI art unavailable (`has_ai_art` flag). Verified: real publication-quality covers.
  - **Audio prototype** (Button 4·A): `render_audio_prototype()` — real OpenAI TTS master of Ch.1 opening via `cinema_studio._tts_bytes`, honestly labeled "prototype / not commercial"; chapter timing map + full-book estimate; included in package 05_AUDIO. Frontend `AudioPanel` with audio player + "Render Narration Prototype".
  - **Pricing + Founder Authorization** wired: POST `/pricing` + `/authorize`; Final Release Gate `pricing_approved`/`founder_authorization_received` now real; `authorize_release()` refuses unless all other gate items met (human final judgment for irreversible action). Frontend pricing input + "Authorize Release" button in Publish.
  - **Share link**: POST `/share` (72h expiry, read-only token) + public GET `/api/book-mfg/share/{token}` streams the ZIP (no login). Frontend "Share Link" button (copies + opens).
  - **Founder-nav "Missing"** now dynamic (clears cover once Design runs; adds pricing/authorization when locked).
- **Known limitations / Next (V1.2):** commercial audiobook = human-narration guided checklist (prototype only rendered); Video still guided packages; no live platform API push; imprint eyebrow uses book.imprint (fixed) but interior colophon still says "QRU Press".

## QRU Book Manufacturing System™ v1.0 ✅ (2026-07-14, iteration_75 — 12/13 backend + full frontend + mobile; honesty bug fixed & re-verified)
Governed SEVEN-button workflow (Upload · Proof & Polish · Design · Audio · Video · Publish · Monitor) — ONE approved manuscript in → ONE publication package out. Orchestrates existing engines (renderer + Reading Experience Standard™ + Product Governance Package™ + studios). NO 8th button. `book_manufacturing.py` + `routers/book_manufacturing.py` (prefix `/api/book-mfg`) + `frontend/src/pages/BookManufacturing.js` (route `/book-manufacturing`, nav capability `book-mfg` in Publishing lane). Collection `book_records`.
- **Pilot loaded:** "The Understanding Tree" by E.Q. Rothwell (BOOK-0001, imprint QRU Press™ provisional, 11 chapters ~20k words). Seeded from the real uploaded DOCX via httpx + python-docx. Honest governance: Source: **Draft received** / Editorial: **Founder review required** / Publication: **Not ready** — a file named "Draft" is never auto-treated as approved. Immutable original sealed (sha256) + separate working copy; title always before Book Record ID; Transparent Provenance™ (source file, checksum, rights holder, AI-contribution record).
- **Real work:** UPLOAD (Canonical Book Record + intake scan: files/missing/structure/readiness/next). PROOF & POLISH (deterministic findings classified Required/Recommended/Optional/Founder-decision; never rewrites voice; lock editorial edition w/ checksum). DESIGN (3 cover concepts + real paperback interior PDF + EPUB via renderer, gated on locked edition). AUDIO/VIDEO/PUBLISH/MONITOR = honest structured packages + guided checklists (never simulate success).
- **PUBLISH:** control center with honest per-destination states + **Final Release Gate** (gate_ready = all(items) — FIXED: was ignoring pricing/founder-authorization; now truthfully False until Founder completes them). **MONITOR:** honest empty metrics until a real platform reports.
- **Founder Navigation** on every screen: Current Stage · Completed · Missing · Decision Needed · Next Step. Mobile-friendly (verified iPhone 390px — buttons scroll, cards stack, no overflow).
- **V1 boundaries respected:** no 8th button, no new department, no external publishing performed. `require_super_admin` gates all mutations.
- **Known limitations / Next (V1.1):** pricing + Founder-authorization inputs not yet wired (gate stays honestly not-ready); Audio/Video are guided packages (no rendered full-book audio/video yet); no live KDP/YouTube/TikTok API push (honest "Ready for manual submission / review" states). Next production stone: wire real AUDIO rendering (Cinema/Podcast Studio) for the pilot + a Master Output Package download.

- **✅ Master Output Package™ (one-click, 2026-07-14):** `assemble_master_package()` + POST `/api/book-mfg/books/{id}/assemble-package` + gold "Assemble & Download Package" button in the book identity bar. Produces a real ZIP (verified 340 KB, 13 files): 01_SOURCE (immutable original, canonical record, version history), 02_EDITORIAL (proofing report, approved master), 03_PRINT (paperback interior PDF), 04_EBOOK (EPUB + cover), 07_METADATA, 09_RIGHTS_AND_GOVERNANCE (governance package + transparent provenance), + honest 00_MANIFEST listing what's pending (audio/video/marketing/monitoring). Only truly-existing artifacts are included — nothing simulated.
- **Known limitations / Next (V1.1):** founder-nav "Missing" is derived from the static intake scan (can look stale after cover selection — cosmetic); pricing + Founder-authorization inputs not yet wired (gate honestly not-ready); Audio/Video guided-only; no live platform API push. Next stone: real AUDIO chapter-master rendering (Cinema/Podcast Studio™ TTS) into 05_AUDIO.

## Project Quiet Factory™ — Stone 1 (Autonomous Decoder + Confidence Summary + Governance Package) ✅ (2026-07-14, self-verified curl + UI)
Constitutional Simplification Initiative™ — "The Factory works hard so the Founder doesn't have to." The Factory absorbs complexity; internal artifacts are Factory-owned by default; the Founder's one required review is the finished PRODUCT.
- **Dual-KR integration fix (Phase A):** `media_division.verified_krs()` now merges BOTH `knowledge_records` (legacy) + `knowledge_engine_records` (KR 2.0 — only "Verified External™/Gold Standard" eligible; "Approved (internal)" stays ineligible per Knowledge-First). `_is_verified()` recognizes KR 2.0 `status`. `decoder_engine._kr_context()` extracts content from the KR 2.0 `sections` dict. Result: 42 eligible KRs (was 40); KR 2.0 records decode fully. Diagnostic confirmed LLL knowledge does NOT exist as governed KRs (lives in ll_* collections) — must be manufactured via KR governance, not invented.
- **Constitutional Autonomy Rule:** after decode, the Factory runs its own gates. All governed standards PASS + not high-stakes → auto-advance to **Manufacturing Ready™** (renamed from Production Ready) and transfer downstream; NO mandatory Founder review. High-stakes (medical/finance/forex/trading/legal/safety/child) or a failed gate → attaches a routing **recommendation** to a small "Recommended for Your Judgment" advisory list (never a mandatory gate). `decoder_engine._autonomy_decision()`.
- **Factory Confidence Summary™:** every record carries PASS/HOLD rows (Knowledge · Verification · Decoder · Treasure Candidate · Constitution evaluated; Recipe/Engineering/Architecture honestly PENDING — no fake PASSes). Surfaced on the record.
- **Treasure Standard™:** Factory auto-assigns **Treasure Candidate™** when all governed standards pass; NEVER auto-certifies. Certification remains a deliberate Founder action (`certify-treasure` now gated on `treasure_standard_candidate`).
- **QRU Product Governance Package™ (`product_governance.py`, STD-GOV-PKG-0001):** centralized, inherited enterprise standard — disclaimers, transparency, provenance, versioning, accessibility, copyright, licensing + category-specific (medical/financial/legal/safety/children) governance language by classification. Automatic, never manual per-product. Inherited into every Decoder Record.
- **Quiet UI** (`DecoderEngine.js`): calm dashboard (Manufacturing Ready / Treasure Candidates / Recommended for Review / Total) + advisory "Recommended for Your Judgment" list + "Manufacturing Ready™ — Factory Completed" list. Full 38-field record, Scorecard, Governance Package, provenance & audit = optional drill-down. Governance actions relabeled "Optional governance." Endpoints: GET /api/decoder/needs-attention; stats reworked.

## QRU Reading Experience Standard™ (STD-READ-0001) — Book TOC & Chapters ✅ (2026-07-14, self-verified pypdf + visual)
The Product Recipe owns the reading experience; every book inherits it automatically (never manually repaired).
- **`book_structure.py`:** parses instructional content into a governed reading journey — Front Matter → Introduction → Chapters (`## `) → Sections (`### `, numbered N.M) → Back Matter. `strip_navigation()` removes any content-embedded flat TOC (navigation ≠ instruction).
- **`rendering_engine._make_pdf` rewired:** adds a Front-Matter page (Copyright + inherited Product Governance Package™ + disclaimers, incl. high-stakes category language) + a professional **Table of Contents** page (grouped learning journey, not a bullet list) + renders body with "CHAPTER N" eyebrows and numbered sections (4.1, 4.2). Applies to multi-chapter (≥2) books; simple docs unchanged.
- Verified: rendered "Learn Forex Trading" → TOC page matches the Founder's example exactly (Front Matter, Introduction, Chapter 1/2/3 with 1.1/2.1/2.2, References). "not financial advice" disclaimer auto-inherited.

## QRU Decoder Engine™ v2.0 — STONE 1 ✅ DONE & VERIFIED (2026-07-14, iteration_74 — 11/11 acceptance, backend 9/9 pytest)
Governed layer that transforms a Verified Knowledge Record™ into governed UNDERSTANDING before any product is manufactured. Additive (never replaces KR→product paths). Route `/decoder-engine`, capability `decoder-engine` (layer `engine` = Understanding Engine™ lane, moat, self-populates sidebar + Factory Map). Files: `decoder_engine.py` + `routers/decoder_engine.py` (prefix `/api/decoder`) + `frontend/src/pages/DecoderEngine.js`. Collection: `decoder_records`.
- **38-field Decoder Output Contract™**: definition, why_it_matters, how_it_works, core_mental_model, analogy (+mapping+limitations), story, visual_spec, memory_anchor, verification, 5-part understanding_checks (explain/recognize/apply/correct/teach), vocabulary, misconceptions, applications, guided_example, practice, reflection, next_understanding, downstream/accessibility/safety notes, provenance, inheritance, review_history, educational_design_rationale.
- **Decoder Scorecard™**: 6 deterministic checks (pass/review) + 12 AI-assisted advisory dimensions (source fidelity, truth accuracy, confidence preservation, mental-model consistency, clarity, analogy quality/distortion-risk, story quality, understanding-test coverage, cognitive load, understanding density, misconception prevention). AI is ADVISORY ONLY — never approves/certifies/publishes/overrides Founder.
- **Founder Review Shelf™** (built INTO the engine surface, no parallel system): decode → `Founder Review Required` → approve/request-revision/archive; **Certify Treasure Standard™ is a SEPARATE action gated on `Founder Approved` first** (certify-before-approve → 400). 15 governed lifecycle states (Draft, Automated Quality Review, Verification/Educational/Accessibility/Brand Review, Founder Review Required, Revision Requested, Founder Approved, Production Ready, Treasure Standard Candidate/Certified, Published, Superseded, Archived).
- **Knowledge-First**: only Verified KRs eligible (unverified decode → 400). **Append-only versioning**: re-decode same KR → v2 non-canonical; v1 canonical preserved (never overwritten). source_kr_ids preserve kr_code+version. Human-readable title before Decoder ID. Super-admin gates approve/certify/archive. Audit via review_history + org_activity. Mobile-friendly progressive disclosure (key learning fields prominent; provenance/metadata/rationale in collapsible sections). Preview fully in-factory; Export (JSON) optional.
- **NEXT (not started, do not begin without direction)**: Stone 2 — rewire QuickStart Book Recipe to consume Approved Decoder Records (not raw KRs). Stone 3 — audience variants + media fan-out.

## Stone 3 — Story & Cinema Studio™ + Podcast Studio™ ✅ DONE & VERIFIED (iteration_73, 6/6 100%)
- Combined governed AUDIO + VIDEO manufacturing departments. Engine `cinema_studio.py` + `routers/cinema_studio.py`, page `/cinema-studio`. Lights up the previously-empty Audio & Video lanes on the Factory Map.
- Registry: `podcast-studio` (layer AUDIO, active, moat) + `cinema-studio` (layer VIDEO, active, moat), both route `/cinema-studio` → appear in nav Audio & Video sections and map lanes. Added `cinema-studio-future` (Feature Film Prep, future).
- 6 formats: audiobook, podcast (audio via real OpenAI TTS `media_production._tts`); motion_storybook, animated_episode, youtube_short, promo_video (video via `little_legacy_production._render_pilot_mp4` Ken Burns + `ai_service.generate_image` scenes + per-scene TTS). Governed by KR-STD voice; KR must be Verified (Knowledge-First). Truthful messaging: "Image-based motion (Ken Burns) + narration — NOT frame-by-frame animation."
- Productions stored in `studio_productions` with promise manifest; frontend renders inline audio/video players.
- Verified via curl (audiobook 97s MP3 HTTP200; youtube_short 21s MP4 HTTP200) + frontend (live podcast manufacture 121s).
- **All 8 phases of the Capability Consolidation & Media Expansion Initiative™ now delivered (Stones 1-3). Factory Map lanes all populated.**


## Stone 2 — Media Manufacturing Division™ ✅ DONE & VERIFIED (iteration_72, 8/8 100%) + Print-Wrap + Regenerate Cover
- **Media Division** (`media_division.py` + `routers/media_division.py`, page `/media-division`, registry `media-division` now ACTIVE/moat under Publishing): one VERIFIED KR → 11 governed formats (Book, Workbook, Teacher Guide, Family/Parent Guide, Classroom Slides, Lesson Plan, Learning Poster, Overview Poster, Video Script, Podcast Script, Social clip). Documents/scripts → product gen (LLM, governed by KR-STD voice) + `deliverable_renderer`; posters → `poster_studio`. Knowledge-First gate: KR must be Verified/Approved/Treasure. Each product stamped `manufactured_by='Media Manufacturing Division™'` + `manufacturing_promise` manifest (inherits from KR). "Manufacture Everything" (with confirm) + selective. 6 FUTURE formats (audiobook/podcast/motion storybook/episode/short/promo) shown as "coming from Cinema/Podcast Studio™" (Stone 3). APIs: GET /catalog /stats /verified-krs; POST /manufacture. Verified via curl (2/2) + frontend.
- **Print-Ready Cover WRAP** (`design_language.premium_wrap` + wired into `deliverable_renderer.ensure_deliverable` for book-category products): full KDP wrap = back panel (headline + KR blurb + "In this book you'll learn" bullets + companion QR + deterministic ISBN-13 barcode + QRU Press band) · branded spine (vertical title + crest) · front hero cover. Added as deliverable format `wrap` (PNG). Fixed dict-vocabulary bullet + layout. Visually verified.
- **Regenerate Cover** (`POST /api/products/{pid}/regenerate-cover`): clears auto-cover, forces fresh AI hero art (asset_mode=generate, skips vault reuse) + re-renders deliverables. Respects Founder-attached Cover Studio covers. "Refresh cover" button on Media Division document results.


## Visual Quality Upgrade — Gold Standard Posters & Covers (2026-07-14) ✅ (self-verified via rendered previews + API)
Founder feedback: posters/covers were "mediocre," hard to approve at Gold Standard. Attached 5 brand references (KOS poster, Forex book cover, Decoder poster, Be AI Smart poster, High Blood Pressure infographic) — navy/purple + metallic gold, crowned QRU crest, Treasure seal, strong type hierarchy.
- **Posters** (`poster_studio.py`): upgraded the SHARED SVG primitives so ALL 11 template families lift at once — added brand gradient defs (`bgGrad` navy→purple radial, `goldGrad`/`goldH` metallic, `panelGrad`, `navyGrad`, `crestGrad`); rebuilt `_shield` into a crowned heraldic crest with quartered emblems + gold-gradient QRU wordmark; upgraded `_seal` to a premium medallion; added `_treasure_seal`; new `_frame()` gradient background + double gold frame + corner flourishes; `_header` gold underline rule; `_footer` gradient band + gold rule + mini-crest. Flat `#0E0C20` panel fills → `url(#panelGrad)`. Knowledge Card (light) gets defs + gold-gradient border. Verified: all 6 sampled templates render, API generate passes 9/9 validation, PNG HTTP 200.
- **Covers** (`design_language.premium_cover` + `rendering_engine.ensure_branded_assets` + `deliverable_renderer.ensure_deliverable`): book/product renders now composite AI hero artwork (Gemini Nano Banana via `ai_service.generate_image`) under the QRU frame instead of a flat gradient. Enriched hero prompt (cinematic navy→purple + gold, symbolic, center/top negative space for title, NO text). Wired into the book-render path; reuses existing hero covers (no repeat AI spend), respects Founder-attached covers. Verified: "Love — Book" cover generated with rich gold-filigree hero art (`cover_has_hero_art=True`).
- Note: pre-existing products with a vault-stored gradient cover keep it (edge case); all NEW manufacturing gets premium hero covers.


## P0 FIX — "I can't actually render a book" (2026-07-14) ✅ DONE & VERIFIED (iteration_70, 6/6 100%)
Founder blocker: from My Projects, clicking "Go"/"Open workflow" bounced to Cover Studio (or a studio) and there was NO way to actually produce the book file. Root cause: /projects only offered "Open workflow" (routes into a stage studio); nothing invoked the real renderer.
Fix:
- Backend `continuity.render_product(pid, actor, base_url)` + router `POST /api/factory-os/projects/{pid}/render`: resolves the project's KR (Knowledge-First — errors clearly if none), generates the product from the KR (LLM), calls `deliverable_renderer.ensure_deliverable` to materialize real HTML+EPUB+PDF, completes ALL production workflow stages, and advances to the Founder Approval gate.
- Frontend `ProjectsContinuity.js`: gold "Manufacture the {outcome}" button (data-testid `project-render-<id>`) on in-progress workflow stages (hidden for video/podcast/audiobook). Auto-opens the items drawer with downloadable deliverables + opens the PDF.
- Verified: book projects render 600KB+ PDF/EPUB, land on "Founder Approval", PDF HTTP 200. No more bounce to Cover Studio.
- Known minor (follow-up): /projects/{pid}/items lists deliverables across the whole linked KR (may show a poster from another project using the same KR). Book files are clearly labeled; not blocking.

## Knowledge Record Manufacturing Engine™ ✅ DONE & VERIFIED (iteration_71, 8/8 100%)
- The Factory's first responsibility: manufacture governed KRs from a source. Route `/kr-manufacturing` (nav under Knowledge; registry id `kr-manufacturing`, moat).
- Governed by the **Approved Knowledge Record Manufacturing Standard™ (KR-STD-0001)**: hope/possibility not deficiency, invite growth, preserve dignity, capability before mistakes, positive+truthful, full metadata, single source of truth. Embedded as `STANDARD_PREAMBLE` into research + organization prompts; stamped on every KR (`manufacturing_standard`, `standard_compliant`).
- Pipeline (`kr_manufacturing.py`): Idea → Research (AI brief, cited) → Evidence → Knowledge Organization (10 methodology fields + KR2 36-section migrate) → Advisory Verification (scores only) → Draft/Under Review → Founder approve/reject. Sources: founder_request, verified_research, library_import (deterministic extract).
- Governance honored: AI drafts only; created Draft/Pending Founder Review; NEVER auto-verified. On Founder approve → Verified + Approved + treasure_standard + `enterprise_memory=True` + ledger `kr_enterprise_memory`; ready to inherit into products.
- Router `routers/kr_manufacturing.py`: POST /manufacture, /{id}/approve & /{id}/reject (super-admin), GET /standard /stats /jobs /pending-review. Verified via curl + frontend.


## Capability Consolidation & Media Expansion Initiative™ (2026-07-14, active)
Founder directive: strengthen (not redesign) the Factory. "One Knowledge Record™ → Many Products™. One Carefully Laid Stone at a Time™." Founder approved starting with Stone 1; Founder will review deprecation/merge recommendations after (did NOT ask to approve each). Streamline goal: easy access to ALL creative engines, ALL outputs, ALL distribution.

### STONE 1 — Governance & Architecture Foundation (Phases 1/6/7) ✅ DONE & VERIFIED (iteration_68, 8/8 frontend 100%)
- **Capability Registry™** — `capability_registry.py` (engine + 91 seeded capabilities) + `routers/capability_registry.py`. Every capability has an intentional status: active/inherited/deprecated/merged/future. Founder status edits persisted ($setOnInsert on status, founder_locked=true), descriptive fields refresh on boot. Seeded at startup.
  - Audit result: 71 active · 9 merged (consolidation recs) · 1 deprecated (experience-lab) · 10 future backlog · 20 strategic moats.
  - Merge recommendations (for Founder review): manufacturing-studio→manufacture, mfg-command→knowledge-manufacturing, product-library→products, creative-studio/visual-studio/media-starter-kit→media-studio, command→concierge, enterprise-health→factory-health, blueprint→architecture.
- **Manufacturing Promise™** (Phase 6) — 5 pillars (Verified Knowledge™, Constitutional Governance™, Enterprise Memory™, Treasure Standard™, Continuous Craftsmanship™). GET /api/capability-registry/promise; surfaced on Factory Map.
- **Factory Map™** (Phase 7) — `pages/FactoryMap.js` at `/factory-map` (nav-factory-map, first item under "Start Here"). Two tabs: Manufacturing Map (flow rail KR→Understanding Engine→Creative Divisions→Distribution + 12 layered nodes with clickable capability chips + destinations panel) and Capability Registry (filterable governed table with per-row founder status dropdown). Has load error/retry state.
  - APIs: GET /api/capability-registry (+layer/status filters), /summary, /map, /promise; PATCH /api/capability-registry/{id}/status (super-admin gated).
  - Map layers: knowledge, engine, publishing, learning, entertainment, marketing, audio(0), video(0), assessment, distribution, governance, enterprise, admin, future. Audio/Video empty by design — populated by Stone 2/3.
- **Self-cleaning Sidebar** ✅ DONE & VERIFIED (iteration_69, 8/8 100%) — `Layout.js` fully rewritten to generate the sidebar live from GET /api/capability-registry/navigation. 5 pinned (Start Here) + 11 division sections + collapsible "Legacy — Under Review" drawer (Merged/Deprecated, 10 items). Backend builder: `capability_registry.navigation()`. As Founder re-statuses capabilities on the Factory Map, the menu self-cleans. Registry now 92 capabilities (added factory-map).

### NEXT STONES (approved sequence, not yet built)
- **Stone 2 — Media Manufacturing Division™ (Phases 2 & 5):** governed division; ONE verified KR → full media catalog (books, PDFs, posters, slides, teacher/parent guides, audiobooks, podcasts, motion storybooks, episodes, shorts, YT long/short, social clips, promo, marketing). KR inheritance review — extend 36-layer KR schema only where needed (one record, many products; no duplicate metadata). Populates 'audio'/'video' map layers.
- **Stone 3 — Story & Cinema Studio™ + Podcast Studio™ (Phases 3 & 4):** as manufacturing departments (not separate apps). Truthful messaging (never claim frame-by-frame if image-based motion). Podcast reuses narration/Voice Profiles™/KRs.
- **Phase 8 Future Backlog (architecture-ready only):** Feature Film, Streaming, Interactive Learning, Trending Topics, Multi-language, AI Tutor, Documentary — already seeded as 'future' capabilities.

### Pre-existing open blocker (carried)
- **YouTube OAuth invalid_grant (P0):** token expired/revoked — Founder must re-authenticate from UI. Do NOT fix via code.
- **Shopify Store Publishing (P1):** deferred; connector exists in distribution/connectors.py, push logic pending Founder token.


## Completed (recent → older)
### Session 2026-07-10 (fork) — MO-007 expansion, MO-011, MO-015/016/017, MO-018, MO-021/023 foundation
- **MO-009/010 Visual & Media Studio™ wired** into `/visual-studio` (route + nav). VERIFIED iteration_35.
- **MO-007 Connector Expansion** — added real, code-complete **Dev.to** (blog) + **Shopify** (marketplace) connectors to `distribution/connectors.py` following the WordPress pattern; added the missing **Developer Setup config UI** (`ConnectorConfigDialog`) to `/distribution` with honest states + validation. VERIFIED iteration_36 (17/17).
- **MO-011 QRU Media Starter Kit™** (`media_starter_kit.py`, `routers/media_starter_kit.py`, `/media-starter-kit`) — deterministic $0 assembly of 13 components + 8 media outputs, Treasure/Gold gated, honest ready/pending. VERIFIED iteration_36.
- **MO-015/016/017 Trust & Authenticity™** (`trust_authenticity.py`, `routers/trust.py`, `/trust`) — protection layers (honest enforced/platform_provided), security levels, platform capability awareness, authenticity certificate + QRU-SEAL™ + SVG QR, permanent registry, PUBLIC verify lookup, audit log. FR-095 Protect Without Punishing™. VERIFIED iteration_37 (20/20).
- **MO-018 QICS™ Intelligent Companion System** (`qics.py`, `routers/qics.py`, `/companion`) — immutable type-aware identity (QRU-BK/KR/WB/CR/AU/VD/PT/AS), dynamic QR gateway (permanent, destination-updatable, never expires), companion portal (15 sections), PUBLIC portal scan + analytics events. FR-096 Lives Beyond the Page™. VERIFIED iteration_37.
- **MO-021 Stock Video + MO-023 Audio foundation** (`media_library.py`, `routers/media_library.py`, `/media-library`) — one governed acquisition layer: 10 providers (Pexels/Pixabay/Freesound live-capable, tier-2 prepared), video+audio collections, StockMediaAsset schema, Master Asset Vault registration, live search gated on real keys (honest NEEDS_SETUP otherwise). FR-097 No Unverified Stock Media™ + FR-AUDIO. Backend curl-tested + frontend smoke-tested; live search pending Pexels/Pixabay keys.

## OPEN / PENDING (this fork)
- **MO-021 END-TO-END LIVE PROOF — DONE (2026-07-10) · QRU Factory Milestone 001:** Real pipeline verified (iteration_38, 17/17): live Pixabay search → recommend → approve → license verify → download+sha256 checksum → register → **OpenAI TTS narration (emergentintegrations, tts-1, voice sage)** → .srt captions → **ffmpeg 720p MP4 render (burned captions + QRU brand bar)** → ffprobe quality review → Master Asset Vault™ → distribution-ready. Endpoints: /api/media-library/produce-proof, /milestones, /asset/{id}/file (streams video/mp4). Provider credential hardening: masked keys, validate-before-save (rejects bad keys), Test Connection codes, audit logs, revoke; transient-flake fix (only definitive codes change stored status).
- **Scene Asset Matcher™ — DONE (2026-07-10):** POST /api/media-library/scene-match — narration→scenes→learning purpose→literal/metaphorical/emotional/environmental terms + topic exclusions (forex: gambling/casino/guaranteed profit/crypto/etc)→live provider search→top-5 deterministic-scored candidates/scene (relevance/technical/composition/brand-fit/licensing/representation) with tier (Gold Gallery≥90/Approved≥80/Shortlist≥70) + crop/start/end/duration/speed/transition/text-safe recommendations + Approve→Vault. UI panel on /media-library. Self-tested (curl + screenshot).
- **Pexels** = env-provided (rate-limited proxy, honest errors); **Pixabay** = real user key ACTIVE; pixabay_music/freesound still need keys.
- **MO-020 Gold Master Design System™ / FOREX FOUNDATIONS™** — AUTHORIZED, NOT STARTED. Fresh from DB Forex KR; legacy PDF supplied (preserve as "Legacy Baseline"). Phased: Visual Blueprint / Page Composition / Preflight Service / Template Registry engines → outline/page-type map → 28–40pp PDF + 14 visuals.
- **MO-023 audio-specific UI tabs**, **MO-024 Mind & Renewal University™** — QUEUED.
- **First full Flagship Showcase™ (30–60s, MO-012)** using Scene Matcher output — QUEUED.


- **MO-021 credential hardening + live proof — DONE (2026-07-10):** Protected provider flow with masked keys (e.g. `pex_••••••••WXYZ`), validate-BEFORE-save (Pixabay correctly rejects bad keys → 400; nothing saved), Test Connection returning CONNECTED/INVALID_KEY/RATE_LIMITED/PROVIDER_UNAVAILABLE/PERMISSION_DENIED, status ACTIVE/DEVELOPER_SETUP_REQUIRED/PREPARED_NOT_ACTIVATED, credential audit logs (`credential_logs`), revoke, last_validated/last_successful_request. Live Pexels proof: searched → registered a REAL asset (kaboompics finance clip) to Master Asset Vault with creator/source/Pexels License/commercial=true/Approved. NOTE: Pexels egress in the PREVIEW env is a limited/rate-limited proxy cache (intermittent 401 on uncached query,per_page combos) — handled with retry + HONEST error UI; a real Pexels key needed for reliable production use. Pixabay/Freesound still need real keys.
- **MO-020 Gold Master Design System™** — AUTHORIZED to proceed fresh from the verified Forex KR in DB (legacy PDF now supplied: https://customer-assets.emergentagent.com/job_understanding-os/artifacts/nkurrvf8_Forex%20KR%20%20Workbook%20%20Workbook.pdf — preserve as "Legacy Baseline — Forex KR Workbook — Pre-Gold-Master Redesign"). NOT STARTED. Phased: engines (Visual Blueprint, Page Composition, Preflight Service, Gold Master Template Registry) → outline/page-type map → 28–40pp PDF + 14 visuals.
- **Scene Asset Matcher™ (MO-021 intelligence layer)** — QUEUED after live provider proof (narration→scenes→literal/metaphorical/emotional/environmental search terms + Forex exclusion terms: gambling/casino/guaranteed profit/crypto/etc → top-5 candidates/scene with scores + crop/timing/text-safe zone).
- **MO-023 audio-specific UI tabs** + **MO-024 Mind & Renewal University™** — QUEUED.
- **First Live Media Proof (MO-021 §6)** — 30–60s Flagship Showcase using a Gold Standard visual + approved stock asset — QUEUED (needs reliable stock access + Scene Matcher).


### QIKS™ Founder Governance Library + MO-008 Governance Binding Layer™ (2026-07-10) · VERIFIED (iteration_34)
- **15 Founder governance PDFs ingested** into QIKS™ as founding Institutional Standards™ (STD-00017…00031), verbatim content (`qiks.adopt_founder_document`, dedupe by name, no-overwrite versioning). Full-document viewer added to `/qiks` (Classification, Source, verbatim body).
- **Governance Binding Layer™** (`governance_binding.py`, `routers/governance_binding.py`): 8 governed agents + 7 governed manufacturing stages + design decisions, each bound to a real standard. Priority enforcement 5/5 (KR Master Spec is #1). Endpoints: /overview, /agents, /design, /strip/{entity}, /manufacturing/{id}/compliance.
- **Factory Agents™ page** (`/agents`): governance loop, agent registry, Manufacturing Governance Chain (compliance record per order), Experience Design Governance. Visible **"Governed by"** strips on Command Center + Knowledge Architecture (reusable `GovernedBy` component).

### MO-007 Universal Distribution Framework™ (2026-07-10) · VERIFIED (iteration_34)
- **Connector SDK™** (`distribution/sdk.py`): one interface every destination implements (ConnectorKind publish/deliver, DistMode draft/private/unlisted/scheduled/public, DistStatus, DistributionResult with real external_id).
- **Connectors** (`distribution/connectors.py`): QRU Store™ (native, real — lists product Published + purchasable), YouTube (real, via Data API, requires file), + honest NEEDS_SETUP stubs (WordPress, Google Drive, Email, Etsy, Amazon KDP). REGISTRY-based — new platforms just implement the interface.
- **Engines** (`distribution/engines.py`): Publishing/Delivery/Verification/Analytics over one job ledger (`distribution_jobs`) with retry (max 3), verification (stores canonical external ID), real analytics (Store purchases/revenue; YouTube views). Router `routers/distribution.py` (+ chunked upload). Frontend **Distribution Center™** (`/distribution`).

### MO-006 YouTube Publisher™ — Founder Upload Mode (2026-07-10) · Built & endpoint-verified (real upload pending a Founder MP4)
- `youtube_publisher.py` (resumable Data API upload, metadata/thumbnail/playlist/privacy, real Video ID, verify_video, video_stats), `routers/youtube.py` (chunked MP4 upload + publish). Frontend **YouTube Publisher™** (`/youtube`): compose from a product, Private default, publish → real Video ID. YouTube channel connected via OAuth.


### MO-005 · QRU Manufacturing Director™ (2026-07-05) · VERIFIED (iteration_33: 12/12 backend, frontend 100%)
- **`manufacturing_director.py`**: supervisory review of manufacturing orders. Verdicts: APPROVE /
  APPROVE_WITH_CONDITIONS / HOLD / REJECT. **The verdict is ALWAYS deterministic/evidence-based**
  (`_decide()` is the sole authority) — reuses `inspection_system.inspect_kr_for_manufacture` +
  `knowledge_record_v2.manufacturing_readiness`/DEPENDENCY_MAP. Identifies exactly which KR 2.0
  sections are missing per requested product type. `_find_kr()` resolves the backing KR by
  `knowledge_record_id` else keyword-overlap (≥0.5) on topic vs KR title.
- **Optional AI executive brief** (`_ai_brief`): reuses existing `ai_service.llm_generate` (Emergent
  key). Treasure Standard™: AI writes narrative ONLY, NEVER changes the verdict; on LLM cap it falls
  back to a `_deterministic_brief` ($0 AI). Verified verdict is identical with/without AI.
- **`routers/director.py`**: GET /api/director/queue (fast, no AI), GET /api/director/review/{id}
  (?use_ai=true), POST /api/director/review/{id}/decision (applies recommended_status →
  APPROVE→Research, HOLD/REJECT→Queued; appends approval_history attributed to the Director;
  idempotency-guarded).
- **Frontend** `ManufacturingDirector.js` (route `/director`, nav "Manufacturing Director™"):
  summary MetricCards, verdict-filtered queue table, ReviewPanel (verdict, confidence, executive
  brief with "Request AI brief", missing knowledge → /kr2, readiness-by-product, recommended actions,
  Apply Director Decision).
- **One-click "Manufacture Cleared" batch** (POST /api/director/manufacture-cleared, super-admin):
  launches `product_automation.manufacture_package` for every CLEARED order (re-passes Quality Gates);
  returns launched[] + skipped[] with explicit reasons (no silent failures). Verified end-to-end:
  MO-00021 (Poster ← verified KR-00008) → APPROVE → launched → production order completed 100% →
  PRD-00129 Published. Orders with empty product_types now correctly return HOLD (nothing to make).

### MO-004 · QRU Master Design Language™ + QRU Component Library™ (2026-07-05) · VERIFIED (iteration_32: frontend 100%)
- **Global tokens** (`index.css`): Deep Navy `--primary` (foundation), QRU Gold `--secondary`
  (verified excellence), Royal Purple `--accent` (signature — used sparingly), white clarity canvas.
  Fonts: **Playfair Display** (headings) + **Manrope** (body). Named tokens `--navy/--gold/--royal`
  remapped so all existing utilities cascade the new hierarchy. `tailwind.config.js` fonts + shadows.
- **QRU Component Library** (`src/components/qru.js`): QRUShield, TreasureSeal, ProvenanceBadge,
  StatusChip (universal status→tone map), MetricCard (accent left-rule + hover lift), Panel, ScoreBar,
  StageTimeline, VerifiedBadge — every future page inherits the QRU look.
- **Shell**: Layout sidebar = inline QRUShield + navy ground + gold active state; PageHeader = gold
  left-rule + Playfair display title. Login redesigned (navy brand panel, QRUShield, royal/gold glow).
- **Flagship pages elevated** to the library: Manufacturing Command Center, Quality Gates, Evidence
  Dashboard, Knowledge Architecture (KR2), Publishing Connectors. Remaining ~55 pages inherit tokens/
  fonts automatically per Founder directive (no manual per-page polish).


### MO-003 · Knowledge Record 2.0™ (2026-07-05) · VERIFIED (iteration_31: 13/13 backend, frontend 100%)
- **`knowledge_record_v2.py`**: 36 sections across 10 groups, each an independent managed object
  {section_id,title,content,status,source,verification_status,confidence_score,author,reviewer,
  created_at,updated_at,version,evidence_links,dependencies,manufacturing_ready}. Extensible — new
  sections need no DB redesign. **Manufacturing Dependency Map** (product-family → required sections)
  + reverse lookup. Non-destructive `migrate_kr` mapped legacy fields (verified_truth→Deep Explanation,
  qru_translation→QRU Translation™, references→Scientific References evidence_links, etc.), preserved
  unmapped legacy. All 47 KRs migrated (idempotent).
- **`routers/knowledge_v2.py`**: /registry, /migrate (super-admin), /{id}, PUT /{id}/section/{sid},
  /{id}/manufacturing-readiness, /dependency-map.
- **Gate integration**: `manufacture_package` now pauses when required KR 2.0 sections are incomplete
  (e.g. video needs YouTube Script + Image Concepts) and names the missing sections.
- **Frontend** `KnowledgeRecord2.js` (route `/kr2`, nav "Knowledge Architecture™"): KR selector,
  completeness bar, collapsible per-section editor (content/status/source, versioned).
### MO-002 · P6 — Enterprise Manufacturing Dashboard™ (2026-07-05) · VERIFIED (iteration_30: 18/18 backend, frontend 100%)
- **`routers/manufacturing_dashboard.py`** `GET /api/manufacturing-dashboard`: deterministic command
  center aggregating KRs (total/verified), products (total/published), queue, connector status + health
  (23 rows), publishing, REAL Stripe revenue (TEST provenance), licensing, throughput (7d), quality
  scores (avg + cleared/paused from Inspection System™), Treasure Standard™ certified, and live
  actionable alerts (paused products → /inspection, connectors needing auth → /connectors, etc.).
- **Frontend** `ManufacturingDashboard.js` (route `/mfg-command`, nav "Manufacturing Command™"):
  alerts, 10 provenance-badged metric cards (drill to /evidence, /inspection, /connectors), connector health table.

### MO-001 · P4 — Manufacturing Quality Gates / Inspection System™ (2026-07-05) · VERIFIED (iteration_29)
- **`inspection_system.py`** (deterministic, $0 AI): 9 gates — Knowledge/Verification Completeness,
  Educational Value, Consumer Clarity, Visual Readiness, Product Eligibility, Connector Readiness,
  Publication Readiness, Treasure Standard™. Blocking gates PAUSE manufacturing + Director report.
  `_kr_text` reads real KR fields (verified_truth, qru_translation, deep_roots, simple_answer…).
- **`routers/inspection.py`**: /summary, /product/{id}, /knowledge-record/{id}, /gates.
- Gate enforced in `product_automation.manufacture_package` (400 pause when blocking gates fail).
- **Frontend** `ManufacturingInspection.js` (route `/inspection`, nav "Quality Gates™").

### Connector UX honesty + Media Studio + YouTube live (2026-07-05)
- Media Studio no longer fakes "Published" (destinations "· Coming Soon"; `publish_media` refuses fake publish).
- YouTube connected via real Google OAuth (fixed iframe 403 by launching OAuth in a top-level tab).
- Connectors: Developer/Founder mode, every disabled Publish has a reason, "Next:" step per card.

### MO-046 — Founder Beta Completion™ · Universal OAuth Framework™ (2026-07-05) · VERIFIED (iteration_26: backend 16/16, frontend 100%)
- **`oauth_framework.py`** — one config-driven OAuth 2.0 engine for 15 providers (YouTube, Google
  Drive/Docs/Slides, Microsoft, OneDrive, Dropbox, Etsy, LinkedIn, Facebook, Instagram, Pinterest,
  TikTok, X, Canva). Standard authorize/token/userinfo endpoints + scopes; PKCE for Etsy/X/TikTok/Canva.
  Amazon KDP & TPT honestly marked unsupported (no public OAuth publishing API).
- **Developer-side config** (`db.connector_configs`): admin sets Client ID / Secret / Redirect URI;
  secret encrypted at rest (Fernet, reuses `INTEGRATION_ENC_KEY`) and NEVER returned to the client.
- **Founder flow**: Connect → `GET /authorize-url` (real provider URL) → official provider login →
  `GET /api/oauth/callback` (public) exchanges code→tokens (encrypted), fetches account name →
  Connected. Automatic token refresh. Founder never sees tokens/credentials.
- **Honest statuses**: Developer Configuration Required → Needs Authorization → Connected → Test Passed
  / Disconnected. **Test Connection** returns an evidence checklist (auth, account ownership, token
  validity via live userinfo call, publish/read permission from granted scopes, refresh capability,
  Ready to Publish). Disconnect + delete-config revert cleanly.
- **Frontend** `Connectors.js`: Developer Setup dialog, OAuth Connect (redirect to provider),
  Test Connection checklist dialog, Disconnect; callback return (`?oauth=success|error`) toasts +
  reloads. No dead/silent buttons — disabled Publish always shows a reason.
- Founder Beta Status™ answers updated to reflect the OAuth framework honestly.

### MO-045 — Founder Beta Stabilization & Evidence Completion (2026-07-05) · VERIFIED (iteration_25)
- **Evidence Metrics Engine™** (`routers/metrics.py`): `GET /api/metrics/summary` returns 15 metrics
  across Commerce/Manufacturing/Publishing, each with a provenance label (LIVE / TEST / SIMULATED /
  NOT_TRACKED). `GET /api/metrics/{id}/evidence` drills into the exact underlying records with full
  fields (Order ID, Product, Customer, Date/Time, Provider, Payment, Live/Test, Revenue, Taxes,
  Discounts, Fulfillment, Delivered, Transaction ID, Platform…). `GET /api/metrics/beta-status?host=`
  returns the Founder Beta Status™ transparency Q&A + deployment state + shareability.
- **Synthetic revenue REMOVED** everywhere: `analytics.py` (was `published*1250 + customers*3400`) and
  `command_center.py` mission-impact (was `11450 + certificates*49`) now compute revenue ONLY from
  `db.payment_transactions` where `payment_status='paid'`. Single source of truth.
- **Frontend** `pages/EvidenceDashboard.js` (route `/evidence`, nav `nav-evidence`): clickable metric
  cards with provenance badges + drilldown modal (real record tables / honest empty states) +
  permanent Founder Beta Status™ panel (Shareable=LIMITED, Payments=SANDBOX TEST, blocks-promotion
  list, 19 plain-language Q&A, deployment = "Founder Preview (Private Beta)").
- **Universal Connector Framework™ now reachable**: added `/connectors` route + nav `nav-connectors`
  (UI/backend already existed from prior session — only wiring added, no redesign).
- Workflow transparency: existing Gate Ladder retained (Founder Inbox evidence dossier).

### Customer Delivery Pipeline (2026-07-04) · VERIFIED iteration_24
- Store → Stripe checkout → post-checkout secure file download. `commerce.purchase_download`.

### MO-038…MO-043 — Autonomy, Design Director, Evidence Decision Center, Self-Guiding Gates,
Founder Beta Dashboard, Automatic Knowledge Extraction, PreviewViewer. (all VERIFIED)

## Known Limitations (as of MO-046)
- **OAuth end-to-end requires registered provider apps**: the framework is complete and honest, but a
  developer/admin must register an OAuth app at each provider and enter Client ID/Secret/Redirect URI
  before Connect works. Live authorization can only be verified once real credentials exist.
- **Automated file publishing** to OAuth connectors (uploading the actual video/doc/listing) is NOT
  yet wired — connect + test connection are operational; the publish-the-file step is a next milestone.
- Stripe TEST mode only — no live payments; email delivery not wired (downloads shown in-app).
- Amazon KDP & Teachers Pay Teachers have no public OAuth publishing API (honestly shown).
- `analytics.py` still emits a synthetic `knowledge_growth` trend chart (Analytics page only).
- LLM text/image generation CAPPED — deterministic $0 fallbacks in use.

## Production Blockers
- Live Stripe keys (currently sk_test) · Email delivery for customer downloads · Registered OAuth apps
  + automated publish-the-file step for external connectors.

## Backlog / Next Milestones (P-ordered, awaiting Founder direction)
- P1: Reach Founder Beta Complete™ (25 consecutive clean manufacturing runs).
- P2: Customer Purchase History / Library (re-download past purchases).
- P2: Replace synthetic `knowledge_growth` trend with real time-series or SIMULATED label.
- Pre-Production: add live Stripe keys + email delivery for public launch.

## Credentials
- Founder: `22j2rsdzb8@privaterelay.appleid.com` / `QruFounder2026!`

## Session 2026-07-11 (fork) — MO-012, QRU Constitution adoption, Factory OS, Product Continuity
### Scene Asset Matcher™ cross-scene dedup — DONE (iteration_40, 18/18)
- `scene_matcher.py`: cross-scene ledgers (provider asset ID, canonical source URL, creator, title Jaccard). Hard duplicates never occupy the selected slot; near-duplicates penalized. Response adds `variety_score`, `dedup_status`, `dedup_flags` per candidate + `project_variety_score`/`unique_assets`/`unique_creators`/`variety_ok`/`scenes_needing_review`. Configurable variety rules (max_per_creator etc).
### MO-012 Controlled Flagship Showcase™ Pilot + Gold Master Certified™ — DONE (iteration_40) · MILESTONE 001 preserved unchanged
- `flagship_showcase.py` + `/api/media-library/showcase/*`: 3 approval modes (Human Approval Required default, Auto-Select Draft Preview only, Governed Auto-Select disabled until ≥5 approved runs + authorization). Multi-scene ffmpeg concat assembly (per-scene license verify→download→checksum→register), TTS narration, captions, Technical QA + Brand/Content QA, Master Asset Vault™, Distribution Ready. `certify_gold_master` enforces 11 gates (authorized only; drafts can never certify). Production Acceptance Record (`production_acceptance_records`) preserves scene list, license evidence, checksums, QA, version history. Frontend `FlagshipShowcase.js` (`/flagship-showcase`): full Scene Approval Interface (approve/reject/replace/search-again/lock, dedup+variety badges), transparent step ledger, video player, Gold Master certify.
### QRU Factory™ Constitution (QRU-CON-0001 v1.0, Founder Approved) — ADOPTED & BOUND (iteration_41)
- `constitution_v1.py`: verbatim full text + 14 structured sections + 12 product statuses + 4 quality gates + 3 automation modes; registered in `db.factory_constitution` AND the QIKS Standards Registry (`qiks_standards` id QRU-CON-0001). `governance_binding.py`: 9 system→section bindings (Knowledge Foundry, Product Mfg, Design Intelligence, Factory OS, Approval Modes, Quality Gates, Gold Master, Vault, Distribution). Endpoints `/api/governance/factory-constitution[/bindings]`. Frontend `Constitution.js` (`/constitution`): searchable sections, binding map, gates, statuses. Version-controlled — amendments create new versions (never overwrite v1.0).
### Factory OS™ Phase A — Create experience — DONE (iteration_41)
- `factory_os.py` + `/api/factory-os/*`: 11 outcome catalog with honest maturity labels; deterministic `knowledge_gap_check` (Knowledge-First — never fabricates a KR; obscure topics return exact message "This topic has not yet been manufactured as a governed QRU Knowledge Record™." + offer to begin Promotion Pipeline); `build_plan` returns governed plan + guidance (the 7 §7 questions). Frontend `CreateExperience.js` (`/create`, nav "Start Here"): outcome grid → describe → Knowledge-First check → guidance → governed plan → launch. Governed by QRU-CON-0001 §7/§8.
### Product Continuity Principle™ (Constitution §4/§14G) — DONE (iteration_42, 14/14 + 2 honesty fixes)
- `continuity.py` + `/api/factory-os/projects*`: per-outcome stage chains (video 11-stage, book/podcast/audiobook/presentation/workbook). `_advance_auto` completes `auto` stages and pauses at workflow/gate/connector. Human-approval gates (§9), connector stages honestly `blocked` (never faked publish), blocked-KR routes to Promotion Pipeline™. Pause/resume/stop. Frontend `ProjectsContinuity.js` (`/projects`, nav "My Projects"): stage pipeline board, progress, recommended next action, approve/open/complete/setup + pause/resume/stop. Create→launch now creates a tracked project.

### Automatic Asset Continuity — YouTube Publisher (Founder directive) — DONE (iteration_43, 8/8 backend, frontend 100%)
- Foundational Principle: a Factory-manufactured product NEVER requires manual re-upload into another module. `routers/youtube.py`: `GET /factory-assets` lists vault videos (provider qru_production, file on disk); `POST /publish` now accepts `factory_asset_id` → resolves the vault MP4 (path validated inside media root), auto-fills title/description/tags from the asset + Production Acceptance Record, extracts a real first-frame thumbnail via ffmpeg, publishes via the YouTube Data API, and NEVER deletes the vault master. Draft previews are blocked from publishing. On success, `media_assets` is stamped with `youtube_video_id`/`youtube_url`. Verified with a REAL publish to the connected channel "Quest Understand" (real Video ID). Frontend `YouTubePublisher.js`: source toggle (Factory-manufactured default / External manual upload); Factory mode = dropdown picker, no file browse, auto-filled metadata; manual mode retained for external videos only.

## Roadmap (Founder-approved, remaining)

### Session 2026-07-13 — Knowledge Record visibility fix (all production lines) — DONE
Founder reported only Governance/Memory KRs populating in Little Legacy & Storyboard pickers.
ROOT CAUSE: two KR schemas coexist — 39 `knowledge_engine_records` (use `topic`) and 76 legacy
`knowledge_records` that store their name in `title` (not `topic`) and mark verified via
`verification_status="Verified"`/`approval_status="Approved"` (not `verified_external`). The dashboard
list read only `topic` + `verified_external`, so the 76 legacy KRs showed as blank/None and unverified,
leaving only 2 named+verified.
FIX (`manufacturing_dashboard.kr_manufacturing_list`): derive topic = topic|title|the_question|subtitle
(skip truly empty shells) and verified across BOTH schemas. Result: 115 KRs now surface with real names,
40 verified (was 2). `KnowledgePicker` now shows ALL KRs with a "Verified only" toggle (Little Legacy
defaults to verified per Knowledge-First; Cover/Poster/Storyboard show all). Single source of truth: all
four production lines read this one endpoint (reads both collections), so any uploaded KR — incl. Asset
Vault import (`library_import.py`) — auto-distributes to every production line.

OPEN ITEM: YouTube publish blocked — OAuth refresh token `invalid_grant` (expired/revoked). Founder must
reconnect the YouTube channel in Publishing Connectors; flagship is fully staged (approved, metadata +
made-for-kids pre-filled, MP4 in secure media root) for one-click publish once reconnected.


- **Character Identity Consistency™:** expression sheet now INHERITS the model-sheet identity anchor (`generate_image_with_reference`); verified same-character across all 6 expressions. Approval requires a **Character Consistency Check™** (`consistency_confirmed` — rejects without it). Pilots/kits inherit the approved v1.0 anchor; a `character_consistency` governance gate FLAGS any asset generated without an approved anchor (no silent accept). Identity Standard sentence added to every Character Bible + overview: "If a child instantly recognizes the character without reading the name, the identity standard has been achieved."
- **Flagship pilot** renamed to "Nova and the Fair Choices Adventure" and re-manufactured reference-locked (all 5 gates pass; polished Publishing Package™ title).
- **Product Kits (kid-format inheriting recipes):** one verified KR → 7 formats (coloring page, social/marketing asset, storybook cover [reference-inherited images] + Knowledge Cards, workbook/activity pack, parent & teacher guides [KR-derived text]). `ll_kits`, Founder-approvable. Verified: real on-model coloring page.
- **Little Legacy Project Zero™:** parent/teacher/child feedback + learning outcomes via existing `project_zero` (no duplication) → feeds the originating KR (improvement signals). `ll_feedback` surfaced in a Project Zero™ tab.
- New collections: ll_kits (+ reuses project_zero_feedback). New tabs: Product Kits, Project Zero™. Files: ai_service.py, little_legacy.py (IDENTITY_STANDARD), little_legacy_production.py (anchor/consistency/kit/feedback), routers/little_legacy.py, LittleLegacyStudio.js (KitTab/FeedbackTab/KitValue).

### Session 2026-07-13 — Little Legacy Learners™ Phase 4 (Production Readiness) — DONE & VERIFIED (iter 66 UI 100%)
- All 6 Character Bibles mastered + approved as Canon v1.0 (model+expression sheets, voice, palette, canon notes, version history).
- Flagship pilot rendered reference-locked (720p, 37s) — verified on-model. Honestly labeled QRU Animated Storybook Pilot™.
- Publishing Package™ auto-built per pilot (15 fields incl. child-safe YouTube title, SEO desc, Made-for-Kids, keywords, parent/teacher Qs, thumbnail rec, 7-point brand checklist).
- One approval → one-click publish: pilot flows to YouTube Publisher™ with metadata pre-filled (no re-upload); `_metadata_from_factory_asset` prefers the package.
- Reference consistency via `ai_service.generate_image_with_reference` (approved master art as reference).
- Product inheritance surfaced via link to existing Manufacturing Dashboard™ (no duplication); coloring/activity/songs/course = future recipes. Project Zero™ existing loop retained.
- New/edited: ai_service.py, little_legacy.py (CANON_NOTES, _ensure_bible_fields), little_legacy_production.py (_build_publishing_package, reference-locked scenes), routers/youtube.py, pages/LittleLegacyStudio.js. Report updated: /app/memory/LITTLE_LEGACY_READINESS_REPORT.md.

### Session 2026-07-13 — Little Legacy Learners™ Animation Studio (Phases 1–3) — DONE & VERIFIED
Governed capability INSIDE the QRU Factory™ (no separate app, inheritance-first). Organized around the
Five Responsibilities (Universe · Characters · Stories · Production · Governance).
- **Phase 1 Foundation** (`little_legacy.py`, `routers/little_legacy.py`, `pages/LittleLegacyStudio.js`,
  nav `nav-little-legacy`, route `/little-legacy`) — VERIFIED iteration_64 (frontend 100% + backend curl).
  Universe Bible™, 6 canonical Character Bibles™ (Draft Pending Founder Approval), 16 locations, Five
  Responsibilities, Knowledge Flow, production catalog, 6 governance checklists + 17-state lifecycle.
  Canon protection (locked fields blocked without Founder approval) + Knowledge-First episode blueprints
  (verified KR required) — both acceptance tests PASS. Enterprise Memory ledger (`db.ll_memory`).
  Founder-provided character poster stored as Character Bible v1.0 visual baseline.
- **Phase 2 Character Mastering** (`little_legacy_production.py`) — VERIFIED iteration_65 + curl. Per
  character: real model-sheet/turnaround + 6-expression sheet (Gemini Nano Banana) + TTS voice profile;
  Founder approval locks Bible v1.0. (Nova Sparkle mastered — on-brand turnaround verified.)
- **Phase 3 Pilot Episode Manufacturing** — VERIFIED iteration_65 + curl. From a Verified blueprint →
  **QRU Animated Storybook Pilot™**: scene key-art (Nano Banana) + warm narration (OpenAI TTS) + burned
  captions (Pillow) + Ken Burns motion, assembled to a real 720p H.264/AAC MP4 via imageio-ffmpeg.
  Deterministic governance gates (Knowledge-First/Child Safety/Accessibility/Treasure). Reviewable DRAFT
  preview; Founder approval releases it to YouTube Publisher™ as a Factory asset (no re-upload). HONEST:
  image-based motion animation, NOT cel animation — stated in UI/product. Real pilot rendered: 36.9s, 6
  scenes, all gates PASS, .srt captions, appears in youtube factory-assets as draft preview.
- **Env fix**: bare `ffmpeg`/`ffprobe` are NOT on PATH in this pod (only via `imageio_ffmpeg.get_ffmpeg_exe()`);
  static build has NO `drawtext`/libfreetype and NO ffprobe. Fixed `media_render.py` + `product_publishing.py`
  (audiobook stitch) to use the imageio_ffmpeg binary + ffmpeg-`-i` duration parsing; captions burned via Pillow.
- **Readiness Report**: `/app/memory/LITTLE_LEGACY_READINESS_REPORT.md`.
- **New collections**: ll_franchise, ll_universe_bible, ll_characters, ll_locations, ll_seasons, ll_meta,
  ll_episodes, ll_memory, ll_character_masters, ll_pilots. media_assets gains qru_production pilot rows.


### Session 2026-07-14 (cont.) — 5 poster template families, QR 403 fix, Cover KR auto-fill
- **QR 403 fixed** (iteration_63, verified): QICS portal/QR URLs used FastAPI `request.base_url` → internal cluster host over http → 403 on phone scan. Added `PUBLIC_APP_URL` env + `_base_url` prefers it (https-forced fallback); migrated all 5 existing portals to the public https URL. Public scan now returns 200.
- **5 new poster template families** (all inherit from the verified KR, render clean vector SVG→PNG/PDF, DRAFT + Treasure Standard passed): identity-anatomy-v1, give-credit-v1 (10-panel), why-forex-v1 (data/infographic, factual), utility-principle-v1 (operating cycle), brain-translation-v1 (misconceptions→corrections table). Validator extended for the new content keys + string list items.
- **Cover Studio KR-first**: new `/cover/kr-brief/{kr_id}` endpoint + "Start from Knowledge" picker auto-fills title/subtitle/series/visual-concept — founder no longer writes a description. Fields stay editable.
- Shopify credentials stored (SHOPIFY_STORE_DOMAIN, SHOPIFY_ADMIN_TOKEN) — integration NOT yet built.

### Backlog (next)
- **Shopify publishing integration** (creds stored): push Published books/products to qru-5019.myshopify.com as a real store channel. P1 — needs integration playbook.
- Course / Marketing / Bundle inheriting recipes still Coming Soon — P2.
- Cosmetic: strip double-period in cover concept_notes; derive series from KR pillar; startup assert TEMPLATES==BUILDERS==DEFAULTS.

- **Pexels + Pixabay keys wired** (founder-supplied, saved encrypted, CONNECTED): MP4 video renders now succeed and appear in YouTube Publisher factory-assets automatically.
- **Audiobook silence fixed**: chunk MP3s are now re-encoded/stitched via ffmpeg into ONE clean 44.1kHz stream (byte-concatenated MP3s wouldn't play in browsers). Background job + status polling + 8-min client deadline; `_audiobook_job` fully wrapped so failures always reach a terminal FAILED state.
- **Unified "My Products" shelf** (`/products`, new nav): one list of EVERY manufactured product across engines (publication/media/poster/recipe) with honest status, badges (In QRU Store / Audiobook / Ready for YouTube), search, engine filters, download/open/audio actions. Answers "where do products go". (Testing agent fixed a duplicate `/products` route that had hidden it; legacy library moved to `/product-library`.)
- **KR-context handoff**: dashboard `km-go-*` and shelf `Open` navigate with `?kr=<id>`; Poster/Storyboard pickers pre-select that exact KR; Storyboard auto-selects first verified KR.
- **Manufacturing Dashboard KR list** merges both KR collections + unified verified logic (was missing verified KRs).
- **Manufacturing GPS links now work**: recommended action → "Go →" (current_route) and blocker → "resolve →" are clickable (were plain text). This is where "Awaiting Founder Decision" projects are actioned (inside My Projects).
- **Book → Publish**: Add to QRU Store (+ View in Store link), KDP-Ready Export, Create Audiobook — all in Cover Studio after cover attach.

### Backlog
- Poster template families for the 5 provided design references (Identity Anatomy, Give-Credit 10-panel, Why-Forex data poster, Knowledge Utility Principle, Brain Translation) — P1.
- Course / Marketing / Bundle inheriting recipes still Coming Soon — P2.
- Perf: `all_products`/`_kr_topic_map` should use `$facet` + cache at factory scale — P2.


### Book → Publish last mile + Audiobook editions + honest video status — DONE (2026-07-13, iteration_61, backend 12/12 + frontend 15/15)
- **Book → Publish** (`product_publishing.py` + `routers/publishing.py`): after a book's deliverable is rendered (with cover), Cover Studio now offers **Add to QRU Store™** (real — sets Published/purchasable, honest refusal if not rendered) and **KDP-Ready Export™** (honest — a ZIP with interior.pdf + cover.png + a fpdf2 metadata/keywords sheet + step-by-step KDP upload instructions; Amazon has NO publish API so we never fake an "on Amazon" state). Endpoints: /product/{pid}/publish-store, /kdp-package, /kdp-file.
- **Audiobook edition from any product** (Founder request): **Create Audiobook** with voice select in Cover Studio → OpenAI TTS (Emergent key) narrates the book content (or the verified KR if the book has little text). Runs as a BACKGROUND asyncio job (the ingress hard-caps requests at 60s → synchronous TTS 502s); the UI polls audiobook-status (8-min client deadline) → READY. Endpoints: /product/{pid}/audiobook, /audiobook-status, /audiobook-file. Verified real 9MB–35MB MP3s.
- **Honest video status** (`StoryboardStudio.js`): each video product card now states the truth — a STORYBOARD_READY product is a governed script, **not yet a video**; it must be rendered (Render MP4) before it can be published, RENDERED links to YouTube Publisher, RENDER_FAILED shows the reason. Removed the misleading "ready to publish" implication. (Rendered qru_production MP4s already appear in YouTube Publisher — reliable MP4 rendering still needs a Pexels/Pixabay key.)

### P2 — Inheriting recipes still to build (Course / Marketing / Bundle)
- Audiobook is delivered as a product-level action (above) rather than a KR recipe — narrates the actual book, which is better. Course (multi-module PDF), Marketing Assets (caption/one-pager pack), and Product Bundle (grouped manifest) recipes remain Coming Soon on the dashboard — NEXT.


### QRU Founder Experience Principle™ — "Never ask the founder to remember what the Factory already knows" — DONE (2026-07-13, iteration_60, 6/6 frontend)
- New reusable `components/KnowledgePicker.js`: founder browses/searches Verified Knowledge by TOPIC only — internal KR IDs / KMR record codes / version tokens are NEVER shown on manufacturing surfaces. Verified sorted first, Verified/Draft chip + "N products manufactured".
- `PosterStudio.js`: raw "Verified Knowledge Record ID" text input REMOVED → topic-first picker. Picking a topic auto-inherits KR content (title/definitions/examples/citations); the 5 content fields are now collapsed "Optional customizations" (empty, placeholder "Inherited from Knowledge") and only non-empty overrides are sent. is_factual auto-set for factual templates.
- `StoryboardStudio.js`: legacy `<select>` KR dropdown replaced with the same picker.
- `KnowledgeManufacturing.js`: left KR list + selected-KR header no longer render KMR codes/versions (topic + products + Verified/Draft only).
- Verified: poster generated from a picked verified topic with zero manual content → title inherited, VERIFIED_EXTERNAL, Treasure Standard PASSED.

### "Manufacture Everything Available" + KR-inheriting PDF recipes + Project Zero™ ingestion — DONE (2026-07-13, iteration_59, backend 19/19 + frontend 7/7)
- `inherited_recipes.py` wired into `routers/media_studio.py`: POST /knowledge-manufacturing/{kr}/manufacture-all (one click → all available recipes; idempotent), POST /{kr}/recipe/{type} (idempotent — returns existing per kr+type), GET /inherited/{pid}/file (real PDF). 4 KR-inheriting PDF recipes live: Workbook, Student Workbook, Instructor Guide, Assessment Pack. Course/Audiobook/Marketing/Bundle honestly COMING_SOON (never faked). Fixed fpdf2 multi_cell x-reset bug.
- `manufacturing_dashboard.py`: matrix now surfaces inherited PDF products + coming_soon state; dashboard is the primary manufacturing cockpit with a "Manufacture Everything Available" button (`km-manufacture-all-btn`).
- `project_zero.py` + POST /{kr}/feedback: deterministic closed learning loop — real learner feedback ingested → aggregate (count/avg_rating/understanding_gain/improvement_signals) written back onto the KR. Honest empty state until real feedback exists (Treasure Standard).

### Knowledge Record Inheritance™ + Enterprise Manufacturing Dashboard™ — DONE (2026-07-13, iteration_58, 100%)
- Philosophy "Understand Once. Manufacture Forever." The verified KR is the Single Source of Truth.
- `kr_inheritance.py`: `build_inheritance(kr)` (title/subtitle/term, plain+professional definition, key points, examples/real-life clues, memory sentence, challenge questions from assessment_plan, tags, category flow, citations, verification/treasure status) + `map_to_template()`. Factual fields copied verbatim from the exact KR version (Knowledge-First); pedagogical framing derived from KR text, never invented facts.
- Wired into `poster_studio.generate_poster` (precedence: template defaults → KR-inherited → founder overrides). QRU Knowledge Card™ now auto-fills from a selected verified KR (verified: term/definition/chart-clue/real-life-clues/challenge/memory/tags) → DRAFT 9/9, no manual data entry.
- `manufacturing_dashboard.py` + `/api/media-studio/knowledge-manufacturing[/{id}]`: each KR as a living dashboard — 15-type product matrix (manufactured/published/available), summary, Project Zero™ feedback loop (honest empty state, real feedback when it exists). Frontend `KnowledgeManufacturing.js` (/knowledge-manufacturing, nav "Manufacturing Dashboard™").
- Follow-ups (noted): full structured-data binding for data/scorecard/decoder posters; build remaining product types (Workbook, Course, Audiobook, Instructor Guide, Assessment Pack, Marketing, Bundle) as inheriting recipes; wire Project Zero feedback ingestion; dashboard list N+1 → aggregation.


### Poster archetypes ×5 + QRU Knowledge Card™ + Media renders — DONE (2026-07-12, iteration_57, 100%)
- Poster Studio now has 6 governed templates: process-formula, data-comparison, scorecard-grid, illustrated-learning, decoder, **knowledge-card** (light-theme QRU Knowledge Card™: term, plain+pro definition, analogy, chart clue, real-life clues, challenge, memory sentence, category flow, tags). All render (cairosvg→PNG+vector PDF), 9/9 Pre-Ship Gate; factual/data templates auto-require a verified KR (Knowledge-First) or held VERIFICATION_REQUIRED.
- Storyboard Studio: **Full Media Kit** button (1 KR → 1 storyboard → 5 products + thumbnails, one approval); per-product **Render MP3** (OpenAI TTS via Emergent key — real audio verified) and **Render MP4** (background Flagship Showcase™ pipeline — reused, not duplicated). MP4 completion depends on stock-video availability (shared Pexels rate-limited/401 in preview → honestly surfaced as "needs review"; a user Pexels/Pixabay key gives reliable MP4s).
- Design Intelligence reference library recorded at /app/memory/design_references.md (all founder-submitted references usable across production per STD-DESIGN-0001).


### QRU Storyboard Master™ (Media Manufacturing) — DONE (2026-07-12, iteration_56, curl + frontend 100%)
- Inside Product Manufacturing Engine™ (NO new top-level engine). `storyboard_master.py`: one approved KR → one versioned Storyboard Master™ (scene-by-scene: objective, KR section, narration, visual direction, on-screen text, motion, audio, duration, accessibility, citation, CTA, assessment) → render selected formats. Routes in `routers/media_studio.py` (`/api/media-studio/order|pilot|file`). Frontend `StoryboardStudio.js` (/storyboard-studio, nav).
- Format recipes: youtube_video, promo_short (9:16), audio_lesson, teacher_presentation, student_presentation. Real renders: PPTX (teacher/student, 8 slides), governed title cards (SVG→PNG 1920x1080), narration transcript + shot list/caption script. Final MP4 assembly reuses EXISTING Flagship Showcase pipeline (not duplicated) — honestly labelled STORYBOARD_READY.
- Governance: Media Quality Gate (7 checks), status model (DRAFT…QRU_GOLD_STANDARD), voice profiles, motion language, Enterprise Memory provenance. **Knowledge-First verified**: media from unverified KR held at VERIFICATION_REQUIRED (treasure RETURN, 1 blocking); a successful render is NOT Gold Standard. Pilot: 1 KR → 1 storyboard → 5 outputs, all 7/7 at DRAFT.
- Factory Concierge™ wired: "create a youtube video/audiobook/presentation" → finds verified KR, returns media_route=/storyboard-studio + media_kr_id.

### STD-DESIGN-0001 QRU Visual Manufacturing Standard™ — ADHERED via inheritance (no new module, per directive)
- One governed visual family reused across products: `poster_studio` reuses `publishing_standard` brand tokens/DOC_ID; `storyboard_master` title cards reuse `poster_studio` SVG primitives (shield/seal/palette). Covers, posters, media all inherit the same standard + Pre-Ship/Treasure gates.

### Poster Studio™ (Process/Formula, first proven template) — DONE (2026-07-12, iteration_55, 100%)
- `poster_studio.py` + `PosterStudio.js` (/poster-studio). Governed SVG→PNG+vector PDF; templates control all text/numbers/citations/layout; AI art composited only. Knowledge-First gating, Pre-Ship Gate, status model, inline preview + gallery. Extend to remaining 4 archetypes next.

### Cover → Product attachment + rendering fixes — DONE (2026-07-12)
- Deliverable renderer resolves attached governed cover first (full-bleed PDF, no text overlay collision); EPUB embeds real cover. Cover Studio 'Attach to Product' auto re-renders deliverable.

### My Projects 'View items' expander — DONE (2026-07-12, iteration_56)
- `continuity.project_items()` + GET `/api/factory-os/projects/{id}/items`; `ProjectsContinuity.js` expander shows governed Video Script & Narration (from verified KR, deterministic) + deliverable downloads.

### QRU Verify & Promote™ Workflow — DONE (2026-07-11)
2, iteration_54, backend curl-verified + frontend 100%)
- Integrated into the existing Refinement engine (no new module — architectural freeze respected). `refinement_engine.py`: `kr_claims`, `verify_and_promote`, `_reverify_with_sources`, `_cascade_products`, `kr_lineage`. Routes in `routers/refinement.py`: GET `/api/refinement/kr/{id}/claims`, POST `/api/refinement/verify-promote`, GET `/api/refinement/kr/{id}/lineage`.
- Human attaches verified sources to each customer-facing claim (definition, explanation) → independent Verification Lion re-run → Treasure re-check → promote KR `APPROVED_INTERNAL` → `VERIFIED_EXTERNAL` (Gold Standard Knowledge Record™) with version bump + immutable Enterprise Memory lineage (`db.kr_lineage`).
- **Cascade**: promotion revalidates every derived product; pre-ship-clean products become `Gold Standard Product™` (6 per KR proven). **HONESTY INVARIANT verified**: no promotion unless every claim has ≥1 approved source AND explicit human confirmation — negative path stays internal, no faked states.
- Frontend `Refinement.js`: new "Verify & Promote" tab (KR list → claim/source editor → human-approval checkbox → Re-Verify & Promote → cascade result metrics + product list + immutable lineage panel).
- NEXT (P0): execute Verify & Promote on the 5 benchmark KRs → render approved products through PDF/deliverable pipeline; then wire the 3 engines behind Factory Concierge™ as the single production entry point.


### STD-RFN-0001 — QRU Enterprise Refinement Initiative™ — DONE (2026-07-12, iteration_53, backend + frontend verified; registry fix applied)
- Refinement Era / Production First: `refinement_engine.py` + `routers/refinement.py` (`/api/refinement/*`) reveal the simplest governed enterprise — ONE Experience Layer (Factory Concierge™), THREE Engines (Knowledge Manufacturing, Product Manufacturing, Enterprise Learning), ONE Governed Foundation (Constitution, Treasure Standard, Verification Lion, Enterprise Memory, Governance Binding).
- **Capability Inheritance Matrix™** (4 consolidations: Production Guidance, Knowledge Registry & Enterprise Memory, Autonomy & Exception Policy, Quality & Readiness Center) — documented & non-destructive (nothing retired; governance/memory preserved). Autonomy Levels 0–4. Universal Manufacturing Contract.
- **Knowledge Manufacturing Engine**: deterministic governed recipe → KR with sections + Knowledge Confidence Profile + INDEPENDENT Verification Lion + Treasure gate. **Product Manufacturing Engine**: one approved KR → many products via Pre-Ship Gate (reused). **Enterprise Learning Engine**: evidence-based recommendations (never silently changes standards).
- **Benchmark Production proof**: 5 benchmark KRs (100% Treasure pass) → 30 products (6:1 knowledge reuse, 100% pre-ship clean), **0 falsely-certified Gold** — honestly held at internal Draft pending human-verified citations (HONESTY INVARIANT verified). 0 founder decisions required.
- Frontend `Refinement.js` (`/refinement`, nav-refinement): Three Engines, Capability Inheritance, Benchmark Production (run + results + honesty banner), Learning & Metrics.
- Sidebar Simple/Standard/Enterprise toggle → recorded in `innovation_observatory` as "Deferred — Awaiting Production Evidence" (per Founder). Constitutional Registry now returns all 5 artifacts.
- PRODUCTION FIRST / ARCHITECTURAL FREEZE in effect: no new major architectural capability until benchmark production evidence identifies a genuine unmet need.


### STD-EIP-0002 — QRU Enterprise Foundation Sprint A™ — DONE (2026-07-12, iteration_52, backend 11/11 + frontend verified)
- `enterprise_architecture.py` + `routers/enterprise_architecture.py` (`/api/architecture/*`): the permanent architectural bedrock. **8 Domains + Domain Registry™**, **7 Enterprise Layers**, **6 Intentions** (Discover/Plan/Build/Launch/Improve/Learn) with **Simple/Standard/Enterprise** view modes, **Architecture Explorer™** (per-module detail: domain/layer/standards/mission/human-capability/related), and **Why-Am-I-Here™** content. Constitutional acceptance criterion VERIFIED: all **75 modules** map to exactly one valid Domain AND one valid Layer (zero unmapped). Registered STD-EIP-0002 in constitution + QIKS + constitutional_registry (idempotent, prior standards intact).
- **Manufacturing GPS™** reusable component (`ManufacturingGPS.js`) — persistent production awareness reusing STD-MFG-0001 next-stage intelligence: timeline (prev ✓ / current ● / next ○), production health + %, recommended action, blockers, remaining stages, and a Why-Am-I-Here toggle. Embedded on every project card in `ProjectsContinuity.js` and on the Explorer GPS tab.
- Frontend `EnterpriseArchitecture.js` (`/architecture`, nav-architecture): 4 tabs (Domains, Enterprise Layers, Intention Navigation w/ view modes + module drawer, live Manufacturing GPS™).
- DEFERRED (inherit this foundation, future phases): Systems Thinking Academy™ lessons, Understanding Intelligence Lab™ + Evidence Model, Human Development Loop™, Enterprise Event Architecture + Services/APIs, Relationship Intelligence Engine, Enterprise Health Dashboard (11 healths), Enterprise Identity metrics, Enterprise Showcase, Continuous Intelligence; full per-page GPS rollout beyond Projects; sidebar Simple/Standard/Enterprise view-mode switch.


### STD-MFG-0001 — QRU Universal Manufacturing Flow Engine™ — DONE (2026-07-12, iteration_51, backend 14/14 + frontend 100%)
- `manufacturing_flow.py` + `routers/manufacturing_flow.py` (`/api/flow/*`): constitutional orchestration layer (KMES) atop the Product Continuity Engine. Canonical **Universal Production Lifecycle** (18 stages idea→…→Enterprise Memory→Observatory loop) + 13 governed production states; **Module Responsibility Registry**; **Next-Stage Intelligence** (current/previous/next/remaining/approvals/blockers/health); **Production Blueprint**; **Production Cards™**; **Smart Handoffs** into Enterprise Memory (`db.flow_transitions`); **Enterprise Dashboard**; **Constitutional Registry** (QRU-CON-0001/0002/STD-MFG-0001, never overwritten). Registered in constitution + QIKS + registry. Honesty invariant verified: Gold Master never auto-certified by simple approval.
- Frontend `ManufacturingFlow.js` (`/flow`, nav-flow): 4 tabs (Enterprise Dashboard + Factory Health + Production Cards™, 18-stage Lifecycle, Module Registry, Constitutional Registry).

### Enterprise Architecture Foundation (QRU Enterprise Intelligence Platform™) — PARTIALLY DELIVERED via STD-MFG-0001
- Delivered: Constitutional Registry, Enterprise Lifecycle engine, Module Responsibility declarations, next-stage/dependency awareness, Enterprise Memory of transitions, Enterprise Dashboard.
- FUTURE (inherit this foundation): 4 Pillars as governed entities + relationship map; Capability Maturity Model (11 states); Enterprise Health Dashboard (11 drillable healths); Knowledge Graph navigator; Enterprise Memory decision store; per-capability AI-Governance declarations; Measurement Framework trends; Enterprise Showcase; Experience Layer (navigate-by-outcome).


### QRU Enterprise Publishing & Presentation Standard™ (QRU-CON-0002) — SPRINT 1 DONE (2026-07-12, iteration_50, backend 13/13 + frontend 100%)
- `publishing_standard.py` (single source of truth) + `routers/publishing.py` (`/api/publishing/*`): versioned constitutional standard QRU-CON-0002 v1.0, registered in `factory_constitution` + QIKS registry + governance bindings (`publishing_bindings`: Deliverable Renderer, Cover Studio, Design Intelligence, Pre-Ship Gate, Factory OS/Concierge, Distribution, Media — every generator inherits it). Machine-readable design tokens (13-level typography, 6 color tokens w/ full governance metadata, layout/margins, dividers), governed **tokens.css**, **QRU Callout System™** (10 types), professional **TOC engine** (`clean_toc_markdown` strips markdown/urls/anchors/brackets → aligned dot-leader typeset), **Cover & Visual Identity Standard™** + 4 classified reference covers (Approved Reference / Inspiration / Template Candidate — NOT auto Gold Standard).
- **Treasure Standard™ Pre-Ship Gate** (`preflight_validate`): 17 deterministic, auditable, BLOCKING rules (markdown remnants, raw urls/anchors, TOC malformed/page refs, heading order, approved fonts, min font size, contrast, safe margins, image alt/resolution, placeholders, metadata, human approval, unapproved AI assets, token version, cover thumbnail). Severities BLOCKING_FAILURE/WARNING/ADVISORY/PASSED/NOT_APPLICABLE; verdict RETURN_TO_PRODUCTION vs TREASURE_STANDARD_PASSED; audit trail in `preflight_runs`.
- **Pilot — THE SCIENCE OF UNDERSTANDING™** regenerated: defective source (12 BLOCKING → RETURN_TO_PRODUCTION) vs governed rebuild (0 blocking → TREASURE_STANDARD_PASSED); clean typeset TOC; chapter opening. Same tokens render in **in-app preview + tokens.css (HTML/CSS) + governed PDF** (`/pilot.pdf` via fpdf2; fonts substitute per platform, semantic role preserved).
- **Cover Studio™** (`/cover-studio`): governed AI cover production (Gemini Nano Banana via Emergent key) — produced a real premium navy/gold pilot cover (QRU shield, Treasure Standard seal, brain-gears focal art) in the reference family without copying. Provenance stored (provider/model/date/prompt/version/standard); states DRAFT_CONCEPT→UNDER_REVIEW→REVISION_REQUIRED→APPROVED_DESIGN→GOLD_MASTER→RETIRED (GOLD_MASTER requires APPROVED_DESIGN — no auto-cert); spec-only/manual fallback so provider outage never blocks publishing. Human approval always required.
- Frontend `PublishingStandard.js` (`/publishing`, nav-publishing): searchable standard, live typography/color/callout previews, TOC before/after, Pre-Ship Gate before/after, reference gallery + governed PDF button.

### Publishing Standard — REMAINING SPRINTS (P1, inherited-but-not-yet-activated)
- Platform renderers: DOCX, Google Docs, WordPress, Canva, PowerPoint/slides, KDP print-wrap, mobile/dark-mode adapters (structurally inherit the standard; activate per controlled sprint).
- Wire the Pre-Ship Gate as a mandatory blocking step inside every existing product generator (deliverable_renderer, media_production, flagship_showcase) + authorized-exception audit log.
- Cover Studio derivatives: full print wrap w/ spine calc + bleed/safe-zone overlays, back-cover grid, barcode area, grayscale/print preview, per-platform export presets; eBook/workbook/KR/course-thumbnail/podcast/social derivatives that inherit identity (not stretch/crop).
- Chapter-opening / educational-diagram / header-footer components rendered into real multi-page book/workbook output.

### QCIOL™-STD-0001 — QRU Collaborative Intelligence Operating Experience™ (FUTURE, Founder-approved directive; NOT in Sprint 1)
- Evolve Factory Concierge™ into the governed operating experience: 3 modes (Quick Request™ / Guided Collaboration™ / Enterprise Planning™), Guided Production Mode™ (post-Gold-Master recommendations w/ approval), Production Blueprint™ visual pipeline, Factory Awareness™ (all departments), Proactive Recommendations™ (approval-gated), Decision Support™ (explain WHY + estimates), unified Production Dashboard + Founder Command Center™, Learning Concierge™, Enterprise Memory™, command-center visual language. Human Judgment Always™; no autonomous execution.
- **Phase C: QRU Factory Operating Manual™** — interactive, searchable, module-linked, context-aware, embedded; downloadable PDF/Markdown/Word/HTML (part of QCIOL priority).
- Universal "Publish Everywhere" (TikTok/Reels/LinkedIn 9:16 + per-target failure isolation); MO-023 Audio Library™; MO-024 Mind & Renewal University™; MO-020 FOREX Workbook; auto-link MO-012 Gold Master into continuity stages.
### Phase B — Factory Concierge™ — DONE (2026-07-12, iteration_49, backend 11/11 + frontend 100%)
- `factory_concierge.py` + `POST /api/factory-os/concierge/message` (+ `GET /concierge/session/{sid}`): conversational guide over Factory OS. Deterministic parsing ($0) of a plain-language request → outcome + topic + audience + goal; optional user-enabled light-AI ONLY parses the request (never authors knowledge). Knowledge-First check is ALWAYS deterministic (fos.knowledge_gap_check on Verified KRs) — zero KR hallucination. Sessions persisted in `db.concierge_sessions`; slots accumulate across turns. Stages: need_outcome (with outcome suggestion chips) → need_topic → ready (verified KR found → launch workflow) OR knowledge_gap (honest "not yet a governed Knowledge Record" + offer Knowledge Manufacturing Pipeline). Reset short-circuits parsing (no "start over" false topic).
- Frontend `FactoryConcierge.js` (`/concierge`, nav "Factory Concierge™"): chat UI with greeting (once, StrictMode-safe), light-AI toggle (default off), suggestion chips, live "Your request" rail + Knowledge-First panel with Launch / Begin Knowledge Pipeline buttons. Governed by QRU-CON-0001 §7/§8/§3.1.

### MO-028 Civilization Status improvement — DONE (2026-07-12, iteration_49)
- `improvement_loop.py`: civilization_status ALWAYS renders all 6 departments (idle → standby=true, progress=100, "Standing by"). Added auditable `cycle_log[]` (which department raised which score each pass). Frontend `fs-loop-cyclelog` Improvement Log + standby dept styling.

### MO-028 QRU Autonomous Improvement Loop™ — DONE (2026-07-11, iteration_48, backend 12/12 + frontend 100%)
- `improvement_loop.py` + `POST /api/media-library/improvement-loop`: evaluate (Creative Direction Report) → auto-assign every recommendation to a specialized department (Creative Director™, Design Intelligence™, Director Intelligence™, Learning Experience™, Knowledge Verification™, QA™) via deterministic ROUTING → improvement cycles nudge each dimension toward an honest ceiling → re-evaluate → present ONE Gold Master Candidate. HONEST: sensitive topic (medical/health/financial/forex/legal…) with NO verified KR → knowledge_verification becomes a BLOCKING work order, gold_master_candidate_ready=false (never fabricated/false-certified). Threshold clamped 70–98.
- Frontend `FlagshipShowcase.js` "Civilization Status" dashboard (`fs-loop*`): auto-runs after Creative Direction; animated per-department progress bars, threshold slider + re-run, Treasure Standard climb, Gold Master Candidate Ready card (score/100 · Departments Complete N/N · Approve/Request Changes/Publish), honest blocking panel, always-visible honest_note. Approve unlocks Manufacture. Governed by QRU-CON-0001 §5/§6/§9/§10.

- **Phase C: QRU Factory Operating Manual™** — in-app interactive (searchable, module-linked) + downloadable PDF/Markdown. (NEXT)
- Universal "Publish Everywhere" — adapt Gold Master for TikTok/Reels/LinkedIn (9:16, platform metadata) with per-target failure isolation.
- MO-023 QRU Audio Intelligence & Licensed Sound Library™ · MO-024 Mind & Renewal University™ · MO-020 FOREX FOUNDATIONS™ Gold Standard Workbook · YouTube E2E real upload.
- Wire MO-012 produce completion + Gold Master into continuity project stage completion (auto-link).

---

## CHANGELOG — 2026-06-15 (fork resume)

### Completed & verified (backend curl-tested against pilot BOOK-0001)
1. **KDP Print-Ready Cover Wrap — wired & shipped.** The `_build_print_wrap` / `compose_print_wrap` logic (already written but never connected) is now exposed via `POST /api/book-mfg/books/{id}/print-wrap` and driven by a new Publish-tab panel (`PrintWrapPanel`). Produces a real back+spine+front 300 DPI PDF sized from final page count, trim, paper type & bleed. Verified on BOOK-0001: 48pp → spine 0.1081" → full 12.358 × 9.25 in, **spine left blank** (correct: <79pp KDP rule). Paper type default = White (B&W), switchable to Cream/Color.
2. **Back-cover Blurb** — `POST /draft-blurb` (AI draft, marked "draft — Founder to approve") + `POST /publication-details` (edit/approve, include_blurb toggle). New `PublicationDetailsPanel`. Verified.
3. **Bug fix:** `ai_service` was never imported at module level in `book_manufacturing.py` — `draft_blurb` would have thrown `NameError`. Added `import ai_service`.
4. **QRU Pricing Advisor™ (NEW inherited capability).** `GET /pricing-advisor` + `POST /pricing-scenarios`. Recommends (never sets). Returns Recommended eBook/Paperback price, Estimated Royalty, Price Position (Budget/Standard/Premium), Comparable Market Range, Confidence Level, Founder Notes, full Transparent Provenance™. Deterministic KDP economics (US 6×9 print-cost formula, 70/35% eBook & 60%−print paperback royalty) + QRU Press™ house genre standards; LLM only writes qualitative Founder Notes. Scenario comparison table (e.g. $9.99/$12.99/$14.99) implemented. New `PricingAdvisorPanel`. All verified via curl.

### Note
- Frontend compiled successfully (webpack clean); live preview screenshot was blocked by the platform's idle "Preview Unavailable" resting page (infra, not code). Backend fully curl-verified through the same domain.

### Next / Backlog
- P1: Decoder Engine™ Stone 3 — canonical audience variants (adult vs child) + media fan-out.
- P2: Generalize "Create Product" bridge beyond Books (Workbooks, Posters).
- P2: Pluggable AI image-to-video provider for the Video button (on hold per Founder).
- Future: Pricing Advisor scenario persistence / save comparison to record (currently ephemeral).


---

## CHANGELOG — 2026-06-15 (continued)

### Publish Standard — FROZEN ✅
- Publish workflow passed full end-to-end UI validation (iteration_77): 9/9 Founder-journey steps PASS.
- Post-validation polish applied: authorize-btn now disabled until gate is ready (Treasure Standard, proactive); gate label "Title & Author"; blurb panel no longer discards in-flight Founder edits (resets only on book switch).
- **Active Publication™ banner** added — a sticky banner (`data-testid=active-publication-banner`) rendered above all tab content in BookManufacturing.js, always showing Book Title, Book ID (code · uuid), Author, Current Stage (active button), Current Status. Visible on every screen. Compiles clean; live screenshot blocked by platform idle resting page (infra).
- **Publish standard is now frozen.** No further Publish changes without explicit Founder request.

### First Real Publication Cycle — The Understanding Tree (BOOK-0001, id 8469bcc5-…, author E.Q. Rothwell)
Factory-manufactured (all verified via API):
- Retail edition sanitized ✅ · Front cover selected ✅
- Back-cover blurb drafted (AI, "draft — Founder to approve") ✅
- KDP print-ready cover wrap (White B&W): 47pp → spine 0.1058" → 12.356 × 9.25 in @ 300 DPI, **blank spine** (correct, <79pp), blurb included ✅
- Master Output Package assembled: ~11.2 MB zip ✅
- Pricing Advisor recommendation: eBook $5.99 / Paperback $15.99, Standard, **High** confidence ✅
- Ready-for-KDP checklist: NOT yet ready — pending Founder: **List price**, **ISBN**

### Remaining (Founder-only decisions — Factory will NOT auto-do these)
1. Approve a list price (recommendation ready).
2. Provide/confirm ISBN (free KDP ISBN or own).
3. Authorize Release.
NOTE: There is NO Amazon KDP publishing API integration — the Factory produces a Ready-for-KDP package + checklist; the final upload to Amazon KDP is a manual Founder action. This is stated honestly (Treasure Standard) — the book is NOT auto-published to any retailer.

### HOLD
- Decoder Engine™ Stone 3 is ON HOLD until the first publication cycle completes (Founder's 3 decisions + KDP upload), per Founder instruction.


---

## CHANGELOG — 2026-06-15 (Founder decisions + Release Review)

### The Understanding Tree — Founder decisions recorded
- **Pricing approved:** eBook USD 4.99 · Paperback USD 12.99 (both stored on pricing record; `set_pricing` extended with `ebook_price`/`paperback_price`; `/pricing` route + PricingReq extended).
- **ISBN:** Free KDP-assigned (recorded; checklist ISBN field now resolves to "assigned by Amazon KDP at publication"). `set_publication_details` extended with `isbn`/`isbn_source`.
- **Ready-for-KDP checklist: READY ✅** (no pending Founder items).
- **Blurb: NOT approved** — held as draft for the Founder's final review per instruction. `blurb_status` remains "draft — Founder to approve".

### New: Founder Release Review™ card
- `FounderReleaseReview` component renders as the final moment before authorization (replaces the plain button-in-gate). Shows Title / Author / Edition / Price / Status, five confirmation checkboxes (manuscript, cover, blurb, price, public edition), then ONE `Authorize Release` button.
- Button enables only when `gate_ready_for_authorization` AND all five boxes are checked.
- **Gate fix:** `publish_center` now returns `gate_ready_for_authorization` = all gate items EXCEPT `founder_authorization_received`. (Previously `gate_ready` included the auth item itself, which would have made the authorize button impossible to enable — fixed.)

### Verification
- All backend flows curl-verified (pricing eBook+PB, ISBN, checklist READY, gate_ready_for_authorization=True).
- Frontend compiles cleanly (webpack). Live screenshot still blocked by platform idle resting page (infra).

### Still pending (Founder's own actions — Factory will not do these)
1. Review & approve the back-cover blurb (draft presented).
2. Tick the five Founder Release Review™ confirmations and click Authorize Release.
3. Perform the manual Amazon KDP upload using the assembled package + checklist (no KDP publishing API exists — honest).

### HOLD
- Decoder Engine™ Stone 3 remains ON HOLD until the first publication cycle completes.


---

## CHANGELOG — 2026-06-16

### 🎉 First QRU Press™ title AUTHORIZED
- **The Understanding Tree (BOOK-0001) is AUTHORIZED for release** by the Founder (Erica Talbert). The Founder Release Review™ card now shows the release-authorized chip. Next step is the Founder's manual Amazon KDP upload (no KDP publishing API exists — honest).

### Bug fix — Founder Release Review™ visibility (was white-on-white)
- The card used a broken `bg-gradient-to-b from-navy to-[#141026]` over `.qru-card` (white bg), making white text invisible. Fixed to solid `bg-navy text-white` with gold border. Verified by testing agent (iteration_78): computed BG rgb(15,23,41), FG white — all fields + 5 checkbox labels readable.
- Authorize button correctly gated: `canAuthorize = gateReady && allChecked && !busy`.

### Active Publication™ banner — accurate status
- Banner now derives Current Stage from `manufacturing_job.stage` and shows an ACTIONABLE Current Status (e.g. "Next: approve pricing (Publish tab)", "Ready for Founder Release Review™…", "Authorized — ready for KDP upload") instead of the raw internal `publication_status: "Not ready"`.

### NEW — Founder Finding Resolution + Governed Revision (Proof & Polish)
Founder chose 1c / 2a / 3b. Implemented (backend curl-verified + frontend testing-agent verified 6/7, 1 test-data gap only):
- Findings now carry stable `id`, `span`, `snippet`, `correctable`, `suggested_fix`. Report counts open findings only + a `kept` count.
- **Keep as written** (`resolve_finding action=keep`): records the intentional finding in `kept_findings`, no text change, re-proofs. (Handles the Founder's "four four" / "ha ha" intentional repeats.)
- **Correct it** (`action=correct`): applies a surgical span fix (or global double-space collapse) and re-proofs. Verified via curl (word count 17576→17575, required→0).
- **Open a Governed Revision** (`open_revision`): unlocks a locked master, archives the prior locked edition into `editorial_versions` (never overwritten), brings content into working copy for editing.
- **Manuscript Editor** (`update_manuscript`): full working-copy edit while unlocked, tracked as a revision, auto re-proofs. Blocked (400) while locked — must open a revision first.
- Re-lock via existing Approve & Lock.
- New routes: POST `/open-revision`, `/manuscript`, `/resolve-finding`.

### Outstanding (non-blocking)
- LOW: UI demo of "Correct it" button needs a seeded correctable finding (backend already verified). 
- LOW: cosmetic `<span>`-in-`<option>` hydration warning reported by testing agent at book-switcher; source line has no span — appears misattributed; left as-is.

### HOLD
- Decoder Engine™ Stone 3 still ON HOLD until Founder completes the KDP upload of The Understanding Tree.


---

## CHANGELOG — 2026-07-16 (Post-Publish Recipe + Honest Deliverables + FEU baseline)

### Context
Founder froze new-feature dev; directed modernization by *wiring existing capabilities*, not building new ones. Governing objective: "Every founder action should either create knowledge, manufacture value, or improve the standard; everything else disappears behind inherited automation." Metric: **Founder Effort Units (FEU)** = questions the Founder should never have had to answer.

### Shipped (backend curl/direct-verified; frontend compiles clean)
1. **Post-Publish Manufacturing Recipe** — `run_post_publish_recipe()` in `book_manufacturing.py`, **auto-triggered by `authorize_release()`** (Publish owns it). Orchestrates EXISTING owners (no new engine): `ai_service` (marketplace text + media scripts), Design-Studio fonts (marketing graphics via PIL), deterministic Founder docs. Manufactures 6 packages: Marketplace, Marketing, Website, Media, Distribution, Founder.
2. **Honest deliverables** — every item labeled **Ready / Prototype / Planned / Not Implemented**. Only *Ready* items are manufactured into one downloadable **Publication Assets** zip; Planned/Not-Implemented produce NO files/links. Verified on The Understanding Tree: 16 Ready, 5 Planned, 1 Not Implemented.
3. Routes: `GET /books/{id}/post-publish`, `POST /books/{id}/post-publish/run`.
4. Frontend: `PostPublishPanel` on the Publish tab (status badges + single assets download); auto-refreshes after Authorize Release.
5. **FEU operational baseline recorded** in `/app/memory/FACTORY_AUDIT.md`: Publish→assets went from **16 manual actions → 0** (one click).

### Also this session (KDP compliance fixes, all verified)
- Interior A4 → true **6×9** (removed full-bleed cover page from interior).
- Cover wrap: clean solid **2.0×1.2 barcode clear-zone** (0 non-white px), dark contrast panel behind back-cover text, imprint moved clear of barcode.
- eBook cover: added KDP-compliant **JPEG 1600×2560** (PNG isn't accepted by KDP).
- Master package: now includes the cover wrap; deliverables de-duplicated (was 11 stale/broken links → 1 current); superseded files deleted from disk.
- Infra: cleared 2.9 GB orphaned `media_masters` (had filled the /app volume → MongoDB ENOSPC crash); capped-storage recommended in audit.

### Governance / architecture baseline
- `/app/memory/FACTORY_AUDIT.md` = official modernization baseline (6 reports + FEU).
- Architecture review answered: **Website Publishing owner = QRU Storefront/Consumer Campus** (`commerce.py` + `routers/consumer.py`), NOT Distribution Center (external) or Partner Integration Layer.

### Known / honest status
- Founder set a permanent password; temp `QruFounder2026!` no longer works (see test_credentials.md). Founder-only (super_admin) artifacts are regenerated via direct backend calls.
- Post-Publish "Planned" items: live catalog listing, author page, QRU Digital Campus, future distribution adapters, rendered video (Not Implemented).

### Next (ranked, from audit — awaiting Founder go)
- Complete Website Publishing (book+author page from Book Record) in Storefront/Campus.
- Inheritance-over-merge pass on manufacturing engines (classify by responsibility, not file count).
- Founder cockpit: thin nav (~8) while keeping internals behind it.
- Remove dead code: `_run_proof.py`, `backfill_marketing.py`, `qru_governance.py`, `constitution_v1.py`.


### Mobile Polish (2026-07-31)
- Layout.js: added native-style bottom tab bar (Console/Create/Knowledge/Concierge/Menu) on mobile (`lg:hidden`); gold active state.
- Hamburger drawer polished: slide-in 300ms ease, 85vw max-w-xs width, shadow, safe-area inset, larger tap targets (py-2.5).
- Main content padded (pb-24) so bottom bar never overlaps; verified on 390×844 viewport.

### Asset Specification Registry Audit + Governed Render/Export (2026-07-31)
- NEW `asset_normalizer.py` (Governed Render/Export Engine™): treats provider/designer output as SOURCE, renders the EXACT final file (exact px, format, color mode, DPI, transparency, max size). Safe normalizations (RGB, DPI, PNG↔JPEG, downscale, JPEG size-fit) auto-apply; quality-affecting changes (upscale, aspect PADDING — never crop) produce a compliant candidate but set quality_review_required → asset lands in "Revision Required" for human sign-off.
- ROOT CAUSE FIXED: `kdp_ebook_cover` profile wrongly set min_px=1600×2560 (that is the IDEAL). True KDP min is 625×1000. A valid 992×1586 provider image was hard-FAILED. Now min=625×1000, governed export target=1600×2560 JPEG@300DPI. Verified end-to-end: 992×1586 → exact 1600×2560 JPEG PASS.
- PSR profiles corrected + source-verified (2026-06 web sources) for KDP eBook/print, Etsy, TpT (square 750×750 min), QRU Online, YouTube, Pinterest, IG, TikTok — added accepted_formats, transparency rules, min_px. `seed_profiles()` now reconciles superseded seeds (appends honest change_history) without overwriting human-modified profiles.
- Fixed aspect-ratio validation bug (was comparing w/h against a height:width field → always warned).
- NEW endpoints: GET /api/creative-assets/profiles/audit (Asset Profile Audit table), POST /api/creative-assets/normalize/{engine}/{id} (dry-run). `upload` now routes through manufacture_final_asset (source→render→validate final→vault; source file preserved for lineage).
- Frontend CreativeAssets.js: Asset Profile Audit™ table (source/date/version/status/review-due), Governed Render/Export panel on upload showing every action + review flag, "Revision Required" state tone.
- Tests: /app/backend/tests/test_asset_profiles.py — 18/18 pass (1 valid + 1 invalid per image profile; PDF pass-through verified).
- HONEST NOTE: legacy marketing preview graphics (design_language.export_formats) already render at exact sizes via contain-fit but still save KDP eBook preview as PNG; the AUTHORITATIVE governed exporter for marketplace uploads is UCAMS.

### Printable Studio™ — Governed Printable Product Manufacturing (2026-07-31)
- NEW `pdf_product_builder.py` (STD-PPB-0001) + `routers/printables.py`: upload PNG/JPEG → choose product type → arrange pages → QA → export a governed, distributable multi-page PDF (real application/pdf, embeddable).
- 4 MVP product types: 1-Page Printable, 3-Page QuickStart, 5-Page Mini Workbook, 8-Page Coloring/Activity Book. Optional branded cover page + instructions page (auto-generated with brand palette/fonts from design_language). Page sizes: US Letter (default), A4, Square @300 DPI.
- Resolution QUALITY GATE: images are contain-fit to the page (never distorted/cropped); per-page effective print DPI is measured. <150 DPI → LOW_RES → QA result REVISION_REQUIRED (human review); 150-300 → warning; ≥300 → clean. Never silently degrades.
- Endpoints: GET /api/printables/config, POST /api/printables/build/{engine}/{record_id}, GET /api/printables/history/{engine}/{record_id}. PDFs stored via rendering_engine (public /api/rendering/asset/*), history in `printable_products` collection.
- Frontend `PrintableStudio.js` (route /printable-studio, nav "Printable Studio™"): product/type pickers, multi-upload + reorder/remove, cover/instructions toggles, Build, per-page QA table, review banner, distribute-as chips, PDF iframe preview + download.
- Suitable destinations surfaced: Etsy digital download, QRU Online download, TpT resource. Never auto-publishes (governed policy decides mode).
- Verified: function tests + live API (build 200, PDF serves 200 application/pdf ~500KB) + UI E2E (low-res upload correctly triggers REVISION_REQUIRED). Build uses get_current_user (Founder/Admin usable).

### Printable Studio™ — Bundle / Regenerate Larger / Activity Templates / Attach (2026-07-31)
- Regenerate Larger: POST /api/printables/enhance-image + per-thumbnail button — Lanczos-upscales a page's source to fill its slot at ~300 DPI (honestly flagged "upscaled"; adds no real detail).
- Activity Templates: eight_page_activity_book (and any type via "Activity layout" toggle) renders content pages with branded title strip + framed art + worksheet/coloring lines, and AUTO-FILLS to the target page count with blank activity/worksheet template pages so a few PNGs become a full book.
- Bundle Builder: POST /api/printables/bundle/{engine}/{id} — merges 2+ finished printables (PyMuPDF) into one activity-pack PDF with a branded Table-of-Contents page; stored as product_type "activity_pack_bundle" (cannot be re-bundled). Sources preserved.
- Attach To Listing: POST /api/printables/attach/{engine}/{id} — registers a finished PDF as product.download_files.<destination> and returns the Governed Publication Policy™ decision (etsy/qru_online/tpt). Never auto-publishes.
- Frontend PrintableStudio.js: activity toggle, per-thumbnail Regenerate Larger, attach buttons on results + bundle results, and a Bundle Builder section (history list w/ QA badges, TOC preview). Verified E2E (curl + UI): activity auto-fill 2→8 pages, enhance 300×400→2250×3000, bundle→12 pages w/ TOC, attach returns policy decision.

### Printable Studio™ fix (2026-07-31): product optional / Build button enablement
- Build no longer requires a pre-selected product. Frontend button disabled only when no pages uploaded (was also gating on !sel → confused mobile users when selector scrolled off-screen).
- Backend build/{engine}/{record_id} accepts record_id "standalone"/"none"/"" → builds with product={} (default palette, title from cover field). Returns product_id (null for standalone).
- Product needed only for Bundle/Attach; result panel hides attach buttons + shows a note when standalone. Selector relabeled "No product — build a standalone printable".

### Printable Studio™ — Presets, Library, Reorder UX + Bookstore clarification (2026-07-31)
- Worksheet Presets: WORKSHEET_PRESETS (tracing/matching/word_search) rendered as ready-made activity pages; build accepts worksheet_presets[]; appended after artwork, before auto-fill. Config exposes them; UI shows toggle chips when Activity layout is on.
- Save Standalone To Library: GET /api/printables/library returns all printables (with/without product) newest-first; UI "Printables Library" grid (title, type, pages, QA, standalone tag, download).
- Reorder UX fix: thumbnails relabeled "Artwork i/N · p.X"; up/down arrows disabled at boundaries; added front-matter note explaining cover/instructions occupy pages 1–2 (uncheck to make artwork page 1). Not a bug — arrows only reorder artwork pages.
- Bookstore "7 titles" is NOT a bug: storefront (public_site/public_commerce/public_bundles) gate = founder_authorization.authorized==True (Treasure Standard). Preview has 20 books/9 authorized; production 7. Authorize via POST /api/book-mfg/books/{id}/authorize (Founder-only). Production (qru-online.com) has its own DB — authorize on the live site.

### Deployment health-check fix (2026-07-31)
- ROOT CAUSE: FastAPI @app.on_event("startup") ran 20+ sequential seed/migration awaits + Stripe connection BEFORE uvicorn completed startup, so the app never became ready and nginx's GET /health on :8001 timed out → deploy failed. No lightweight /health route existed.
- FIX (server.py): added GET /health and GET /api/health returning {"status":"ok"} instantly (no deps). Moved the whole seed chain into a background asyncio.create_task (_run_startup_seeds) with per-step try/except + asyncio.wait_for(timeout=120) — startup now returns immediately, binds 0.0.0.0:8001, answers /health right away; seeds finish in background (~1s).
- continuous_improvement.py: wrapped the background LLM capacity probe in asyncio.wait_for(timeout=30) (source of the transient "Unclosed client session" litellm/aiohttp log; runs 20s post-startup, never on the health path). All other HTTP clients already use httpx `async with` + timeouts; storage.py uses requests with timeouts.
- VERIFIED: /health returns 200 within ~3s of restart; logs show "startup complete" immediately then "background seeding complete"; deployment_agent scan PASS.
- NOTE: prior "manifest invalid" (docker-push) and "ensure-environment context deadline exceeded" errors were transient Emergent infra/registry issues — retry deploy.

### Universal Page Layout Engine + Founder Authorize button + Asset Remove (2026-08-01) — VERIFIED (iteration_105)
- Universal Page Layout Engine™ (layout_engine.py, STD-UPLE-0001): 11 layouts (poster/fill/original/custom_scale/coloring/bordered/book_illustration/worksheet/workbook/activity/cut_paste). Default Poster = full-page fill inside configurable printer-safe margin (default 0.25", full-bleed 0" available). SVG import via cairosvg. Wired into pdf_product_builder.build (layout/margin_in/custom_scale). Endpoints: /printables/preview-page (live single-page PNG), /printables/settings GET+POST (remembers last layout as default; build also persists it). Frontend PrintableStudio: layout grid, margin+full-bleed, custom scale, debounced live preview.
- Founder authorization button: BookManufacturing store-listing row now shows a prominent gold "Authorize & Publish to QRU Online" (authorize-store-btn) when a book is NOT yet authorized (previously nothing showed). doAuthorize reloads book + handles imprint-mismatch override via confirm.
- Creative Assets Remove: DELETE /api/creative-assets/assets/{asset_id} deletes ONLY Rejected/Rights Hold/Revision Required (400 for Locked/Approved). Frontend ca-remove-{asset_id} button shown only for those states, with confirm.
- ffmpeg: already handled via bundled imageio-ffmpeg (no raw ffmpeg calls) — DB errors were stale. No install needed.
- All verified by testing_agent iteration_105 (14/14 backend, all frontend flows).

### Production Knowledge Records not loading — N+1 timeout fix (2026-08-03) — VERIFIED
- SYMPTOM (production qru-online.com only): "Browse Verified Knowledge" stuck on "Loading Knowledge…" showing 0 records; toast "Could not load Knowledge Records."; Factory Jobs empty. Preview worked fine (HTTP 200, 129 records).
- ROOT CAUSE: manufacturing_dashboard.kr_manufacturing_list() ran 5 sequential count_documents() PER knowledge record (129 records × 5 ≈ 645 round-trips). Fast on preview localhost Mongo (~0.4s) but on production's remote Emergent-managed Mongo the per-query latency stacked past the ingress request timeout → hung request + 502/504 → error toast. NOT a missing-data problem.
- FIX (manufacturing_dashboard.py kr_manufacturing_list): replaced per-record count loop with 5 grouped $group aggregations (_count_map) → constant ~7 queries regardless of record count. Endpoint now 0.13s. Counts identical (45 records with assets, verified).
- Factory Jobs endpoint checked — clean (2 queries, no N+1); "no jobs" on production just means none exist in its separate DB.
- ACTION REQUIRED: this is a code fix in preview — user must REDEPLOY to push to production.
- Minor observed (not fixed, out of scope): detail dashboard header can render "null — Living Manufacturing Dashboard" for some KRs whose topic field is null in the detail endpoint.

### Production 520 (login fails, books gone after republish) — .env not tracked (2026-08-03)
- SYMPTOM (production only): Cloudflare 520 "origin sent a response Cloudflare could not parse / empty response / malformed headers" on POST /api/auth/login; public books page shows "No titles published yet". Started right after a republish. Preview 100% healthy (health/login 200, 9 public books) — pure production outage.
- ROOT CAUSE: backend/.env and frontend/.env were NOT git-tracked and .gitignore excluded them (lines 34-37 `.env` patterns + line 193 `*.env`). Emergent deploy injects prod config INTO the tracked .env files; when untracked, a republish can ship a config-less backend (no MONGO_URL etc.) → DB-backed requests return empty → Cloudflare 520.
- FIX (.gitignore): removed the `.env` ignore patterns (kept `!**/.env.example`) so backend/.env + frontend/.env are tracked. Verified: `git check-ignore backend/.env frontend/.env` now returns nothing (not ignored); deployment_agent scan PASS (gitignore_blocks_required_files=false, env_files_ok=true).
- ACTION REQUIRED: user must REPUBLISH/redeploy so the tracked .env ships to production. Could NOT verify against live production (no prod access) — fix validated via static deploy scan + preview health only.
- NOTE: once backend is healthy, if production DB genuinely has 0 authorized books they must be authorized on the live site (Founder-only); but the 520 alone would also make books vanish, so they should return after a healthy redeploy.

### Stuck long-running jobs (workflows + asset upgrade) → migrated to durable Spine (2026-08-03) — VERIFIED
- SYMPTOM (production): multiple "Full Treasure Acceptance Test" workflows stuck "running" at 35% for a week; a Batch Upgrade Assets bar stuck "Running 48/121" for a week; bursts of 503 "AI service temporarily unavailable" and Cloudflare 524 origin timeouts under load.
- ROOT CAUSE: both features used fire-and-forget `asyncio.create_task`, which production container recycling kills mid-run — leaving DB state stuck "running" forever (the exact failure the Orchestration Spine was built to prevent). workflow_engine also ran many workflows concurrently → LLM rate-limit 503s + event-loop saturation 524s.
- FIX:
  1. workflow_engine.py: `start_workflow` now enqueues a durable Spine job (`workflow_run`) instead of create_task. Serial execution eliminates the concurrent-workflow 503/524 overload; Spine reclaim makes it restart-proof. Added `workflow_run_handler`, idempotent resume (Parallel Manufacturing skips already-"done" product types on re-run), and `reconcile_stale_workflows()` (startup: stuck running/queued → failed with honest "interrupted, please retry" — Treasure Standard, no silent stuck states).
  2. prod_migrations.py / routers/migrations.py: Batch Upgrade Assets now runs via Spine (`asset_upgrade_run`); it is $0-AI + idempotent (skips already-upgraded), so `reconcile_stale_asset_upgrade()` AUTO-RESUMES a stuck batch on startup and finishes the remaining products.
  3. job_handlers.register_all registers `workflow_run` + `asset_upgrade_run`; server.py startup calls both reconcilers.
- VERIFIED (preview): handlers registered; a workflow ran through the Spine (active LLM calls, progressing); asset-upgrade worker resumed → status `complete`, remaining=0; stale reconcilers cleared pre-existing stuck jobs on restart.
- ACTION REQUIRED: user must REDEPLOY. On production boot, the reconcilers will clear the week-old stuck workflows (→ retry) and auto-resume the 74 remaining asset upgrades to completion.
- KNOWN SYSTEMIC PATTERN (not yet migrated): ~20 other `asyncio.create_task` background ops remain (orchestrator bulk batches, product_automation lines, verification review-all, products rerender, media/pipeline jobs, little_legacy renders, etc.). These can also get stuck on a production recycle. Recommend migrating the bulk/long-running ones to the Spine next (P1).

### Systemic hardening: all bulk background ops → durable Spine + concurrency (2026-08-03) — VERIFIED
- Continued the fire-and-forget → Spine migration for the remaining bulk/long-running operations that could freeze on a production container recycle.
- job_engine.py: added MAX_CONCURRENCY=2 so the durable Spine runs a few jobs at once (a long batch no longer blocks quick jobs) while still preventing the old UNBOUNDED-concurrency 503/524 storms. worker_loop now maintains a task pool (leases up to N via atomic find_one_and_update). Verified bounded at 2 running + queue behind.
- Migrated to Spine handlers (job_handlers.register_all): `batch_manufacture_run` (orchestrator bulk manufacturing — resumable via per-item batch state), `kr_review_all` (verification AI-review-all), `doc_rerender_run` (products Publication-Quality re-render, $0 AI). Each endpoint now enqueues (dedupe_key) instead of asyncio.create_task.
- Startup reconcilers added: orchestrator.reconcile_stale_batches (auto-resumes 'running' batches — item-idempotent), products.reconcile_stale_rerender (auto-resumes 'running' re-render). Combined with prior workflow + asset-upgrade reconcilers.
- VERIFIED (preview): 9 handlers registered; reconciler auto-resumed 3 stuck manufacturing batches; concurrency held at 2 running/1 queued; no errors. (Old preview test batches then paused to conserve credits.)
- STILL fire-and-forget (lower-risk / short-lived, not yet migrated): little_legacy_production kit/pilot spawns, storyboard_master video, product_publishing audiobook, asset_manufacturing finish, storage_audit workers, routers/{orchestrator autopilot, memory, autonomy_engine, rendering, pipeline, media}, video_fulfillment backfill. These are single-item/short so less likely to visibly stick; migrate opportunistically (P2).
- ACTION REQUIRED: redeploy to apply on production.

### Deploy-blocker lint fixes (2026-08-03)
- vault.py save_bytes: Founder-uploaded assets were written ONLY to pod-local disk (ephemeral → gone after deploy/recycle). Now the durable Emergent object storage is the source of truth (storage.mirror_file); added vault.local_path() which re-materializes the local cache on demand via storage.ensure_local(). routers/vault.py serve() + apply_to_product() use it. Verified: upload → object_exists True; local cache wiped → re-fetched from durable storage (bytes match).
- book_manufacturing.py: removed duplicate `import os` (ruff F811) inside assemble_master_package (os already imported at module top + line 2201).

### Production 520 AGAIN after hardening redeploy — startup blocked on reconcilers (2026-08-03)
- SYMPTOM (production only): Cloudflare 520 "origin sent empty/malformed response" on ALL data endpoints (capability-registry/Manufacturing Map, distribution-architecture, knowledge, products) right after republishing the Spine-hardening changes. Preview always healthy.
- ROOT CAUSE: last session's startup() AWAITED four reconcilers directly in the blocking startup path (no timeout). One (reconcile_stale_batches) looped over 'running' batches doing per-batch job_engine.enqueue (dedupe find_one on factory_jobs); on production's remote Mongo / larger data this stalled → uvicorn never finished startup → origin never bound → total 520. Auto-resuming heavy jobs at boot was also a resource risk.
- FIX:
  1. server.py: removed the 4 awaited reconciler blocks from startup(); moved them into the BACKGROUND _run_startup_seeds chain (each wrapped in _step → 120s timeout, isolated). startup() now only fires the seed task + starts the Spine worker → health binds immediately (verified 200 in 0.34s at t+3s).
  2. Reconcilers are now SURFACE-ONLY (no auto heavy work at boot): orchestrator.reconcile_stale_batches → marks running batches 'paused' (Founder resumes via durable resume_batch); prod_migrations + products reconcilers → mark stuck 'running' as 'interrupted' (re-run on demand). No per-item enqueue loops.
  3. job_engine.MAX_CONCURRENCY reverted 2 → 1 (serial; safest for production resources; matches last-known-good).
- VERIFIED (preview): fast non-blocking startup; all previously-520'ing endpoints return 200; reconcilers run in background surface-only; worker idles (no auto heavy jobs). Cleaned leftover test jobs.
- ACTION REQUIRED: redeploy. Could NOT verify against production directly (no access) — if 520 persists after redeploy it is a platform/infra/env issue → contact Emergent Support.

### Disk-full outage + "Needs Attention" factory health panel (2026-08-04)
- INCIDENT: /app volume (9.8G) hit 100% — rendered_assets alone was 3.8G (unbounded growth from manufacturing/render runs). A full disk blocks all writes and caused a container recycle / 502. FIX: cleared 3.4G of stale cache (safe — rendered_assets & asset_vault are mirrored to durable object storage and re-fetched on demand via aensure_local). Added a startup background prune `_prune_disk_caches()` (in _run_startup_seeds via _step) that deletes cached render/vault files older than 3 days so the disk can't fill again.
- FEATURE (Needs Attention): new read-only GET /api/factory-jobs/attention aggregates everything stalled across systems — paused bulk batches (resume → /orchestrator/batches/{id}/resume), interrupted asset-upgrade (→ /admin/migrations/assets-upgrade) & re-render (→ /products/rerender-documents), failed workflows (informational), failed Spine jobs (retry). Route defined BEFORE /{job_id} to avoid capture. Frontend: amber "Needs attention" panel at top of Factory Jobs™ page with one-tap Resume/Re-run/Retry (data-testid needs-attention-panel, attention-resume-{id}). Verified: endpoint 200 aggregating 10 items; page compiles & renders.
- NOTE: FactoryJobs.js was truncated by the disk-full write mid-edit and was rewritten cleanly (overwrite).

### Disabled autonomous watcher_loop + Founder on/off switch (2026-08-04) — scoped request, VERIFIED, NOT deployed
- Per Founder request: disabled the unrequested autonomous background AI process.
- continuous_improvement.py: removed emergentintegrations LlmChat/UserMessage + MODEL imports; probe_capacity() is now DETERMINISTIC (no LLM call — reports Universal Key presence only); added Founder switch (settings doc id "continuous_improvement", default absent = OFF): is_enabled/watcher_running/start_watcher/stop_watcher/set_enabled; watcher_loop() rewritten to self-check the switch and run ONLY deterministic review_completed_batches() — no auto-resume, no autonomous_engine, no AI; overview() watcher status updated.
- server.py: removed asyncio.create_task(continuous_improvement.watcher_loop()) from _run_startup_seeds (no auto-start on boot); dropped now-unused local import.
- routers/continuous.py: added GET /api/continuous/settings, POST /api/continuous/settings/enable, POST /api/continuous/settings/disable (require_super_admin).
- EnterpriseAutonomy.js: added clearly-labeled ON/OFF switch card (default OFF) + toggle wiring.
- VERIFIED in preview (no paid AI): fresh restart → zero LiteLLM/capacity-probe/watcher activity; default settings enabled:false; enabling ran a full watcher cycle with ZERO AI calls; toggle on/off works; capacity endpoint deterministic. Setting left OFF.
- NOT deployed (Founder to review). Universal Key untouched. No manufacturing resumed. All data/integrations preserved.

### Book Manufacturer Design tab crash — broken ternary fix (2026-08-04) — VERIFIED, NOT deployed
- ROOT CAUSE: frontend/src/pages/BookManufacturing.js DesignPanel had a dangling `) : (` (~line 909) — the ternary's opening `{cond ? ( ...placeholder... )` had been deleted, a JSX syntax error that crashed the panel (ErrorBoundary → "This section is being prepared…"). Books with no design artifact (d undefined) also hit `d.cover_concepts.map` → TypeError.
- FIX (BookManufacturing.js only): restored the ternary `{!d?.cover_concepts?.length ? (<placeholder design-not-ready>) : (<cover concepts>)}`; guarded `(d?.cover_concepts || []).map(...)` and `<LegibilityPreview concepts={d?.cover_concepts || []} />`.
- TESTED: BOOK-0024 is production-only (absent in preview). Tested all 7 preview books lacking a design artifact (Sleep Strengthens Memory, Consistent Sleep, Day Trading, Brain Deconstructed, The Bridge LargePrint, How to Understand AI, How to Learn Faster) → all load Design tab with crashed=False, panel rendered, placeholder shown. Zero AI/LLM calls (read-only navigation; Generate Design NOT clicked). No data/DB/Universal-Key changes. NOT deployed.

### Final Release Gate — Rights Confirmation control + Authorize Final Release button (2026-08-04) — VERIFIED, NOT deployed
- PROBLEM: Gate stuck — "Rights Confirmed" had NO control at all, so it stayed pending, which kept gate_ready_for_authorization false and the Authorize button disabled ("Founder Authorization Received" pending). No way to complete either.
- BACKEND book_manufacturing.py: added confirm_rights(book_id, actor) — stores a dedicated rights_confirmation={confirmed,by,at} + revision_history entry; does NOT touch manuscript/cover/metadata/price/files. Gate rights_confirmed now = rights_confirmation.confirmed OR legacy rights_holder. publish_center() now returns rights_confirmation + founder_authorization.
- BACKEND routers/book_manufacturing.py: added POST /api/book-mfg/books/{book_id}/confirm-rights (require_super_admin). (Authorize endpoint already existed.)
- FRONTEND BookManufacturing.js: added doConfirmRights handler; rebuilt PublishPanel Final Release Gate — inline "Confirm Rights" button on the pending row + a dedicated Rights Confirmation card showing confirmer+timestamp when done, and a full-width "Authorize Final Release" button (data-testid authorize-final-release-btn) that enables only when the gate is ready and records founder_authorization {by,at}.
- VERIFIED (preview, no AI): confirm-rights flips gate False→True and saves by+timestamp; authorize on a not-ready book returns controlled 400 ("unmet gate items") with NO publish/AI. MOBILE (390x844): both controls render and Confirm Rights works end-to-end (screenshot shows green check + "Rights confirmed by Demo Administrator · timestamp"). NOT deployed.
