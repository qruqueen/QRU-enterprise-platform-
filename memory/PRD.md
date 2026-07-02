# QRU FACTORY™ — Product Requirements Document

## Original Problem Statement
Build QRU Factory™, an enterprise Knowledge Manufacturing Operating System for QRU (Quest for Real Understanding). Mission: "QRU manufactures understanding from verified knowledge. QRU does not simplify the truth — it simplifies the path to understanding the truth." The system runs the full workflow: Idea → Research → Verification → Knowledge Record™ → Understanding Translation → Manufacturing Order™ → AI Collaboration → Product Manufacturing → Quality Review → Approval → Publication → Delivery → Continuous Improvement.

## User Choices
- AI: **GPT-5.5** (via Emergent LLM key)
- Auth: **JWT email/password with roles**
- Product content: **Full AI-generated content**
- Design: **Light, clean, minimal enterprise** (Outfit + IBM Plex Sans, primary #0047FF)

## Architecture
- **Backend**: FastAPI (modular routers) + MongoDB (motor). Bearer-token JWT auth, role dependency (`require_roles`). AI via `emergentintegrations` LlmChat (openai/gpt-5.5). All routes under `/api`.
  - Files: `server.py`, `auth.py`, `database.py`, `models.py`, `ai_service.py`, `seed.py`, `routers/{knowledge,manufacturing,workforce,products,analytics,command,misc}.py`
- **Frontend**: React (CRA + craco), react-router v7, Tailwind + shadcn/ui, recharts, sonner. Sidebar Layout + ProtectedRoute. Bearer token in `localStorage['qru_token']`.

## User Personas / Roles
Administrator, Executive, Researcher, Reviewer, Designer, Publisher, Teacher, Customer, ReadOnly.

## Implemented (2026-07-02)
- JWT auth (login/register/me/logout), admin + executive seeded, RBAC on user management.
- Executive Command Center dashboard (KPIs, pipeline, workflow visualization, activity feed).
- Conversational Command Console — AI interprets commands and auto-creates Knowledge Records / Manufacturing Orders / runs research.
- Knowledge Records: data grid, create, detail, AI Understanding Translation, Verify/Approve.
- Research Center (AI research → draft record) and Verification Center.
- Manufacturing Orders: 6-stage Kanban with stage advancement.
- Product Manufacturing: AI generates full Markdown products (18 product types); Product Library + detail with publish/review/archive.
- Digital Workforce: 13 seeded AI Digital Employees with mission/permissions/tools/metrics + detail dialog.
- QRU Health University (7 colleges), Analytics (recharts), Customers/Licensing, Notifications, Global Search, Settings, User Management.
- Verified by testing agent: backend 30/30, frontend 100% of flows.

## Implemented — Iteration 2 (2026-07-02)
- **QRU Teaching Methodology**: Knowledge Records now carry the full 11-part structure (The Question, Simple Answer, Why It Matters, Real-World Example, QRU Translation™, Everyday Analogy, Memory Sentence™, Practice/Application, Key Vocabulary, Deep Roots™, Verification Status) with per-section status (Empty/Draft/Verified). Existing records auto-migrated (content preserved; missing sections AI-fillable, marked Draft).
- **QRU Translation Engine™** (flagship): dedicated page (paste technical text → full methodology) + per-record "Manufacture Understanding" that fills only empty sections, never overwriting verified content.
- **Verification Center redesign**: reviewer evaluates Evidence, Sources, Confidence, Observed Facts, Calculated Data, Analytical Judgment, Conflicting Evidence, Open Questions, Comments → Approve / Reject / Request Revision. Approval promotes Draft sections to Verified and can grant Knowledge Master File™ + Treasure Standard™.
- **AI Director Departments**: workforce cards open department view (metrics, current orders, assigned records, product output, team activity).
- **Executive Command Center expanded**: Enterprise Health, Revenue, Treasure Standard, Verification Queue, Marketplace Ops, workforce status.
- **Understanding Colleges** (modular): Health division active with per-college workspace tabs; future divisions (Trading, Finance, AI, Programming, Parenting, Business, Government) seeded as Coming Soon — all plug into the same OS.
- **Full QRU rebrand**: Royal Purple / Gold / Navy / White, QRU Shield logo, mission statement throughout.
- **QRU Focus Audio**: Web-Audio player (Off/Focus/Calm/Nature/Orchestra/Lo-Fi/Solfeggio/Instrumental), muted by default, header + Settings controls (swappable for licensed audio later).
- **Search** now indexes Colleges. Verified by testing agent: frontend 40/40, backend iteration-2 15/15.

## Implemented — Iteration 4 (2026-07-02) · QRU Enterprise Organization™
- **Executive Board** — 13 AI directors (Kingdom Lion™, Legacy Eagle™, Legacy Bear™, Queen Unity™, Crowned Bull™, Royal Phoenix™, Consumer Advocate™, Marketing/Sales/Brand/Manufacturing/Health, Creative Studio Director™) in an **Expertise Registry** (`registry_agents`) with expertise, workload, availability, projects.
- **Emergent collaboration** — 13 Emergent platform specialists (Software Architect, Security, Testing, Deployment, UX, etc.) registered as origin=Emergent; QRU extends, not replaces them.
- **Collaborative review teams** — `POST /registry/assemble` assembles the most qualified specialists per task type.
- **Live Organization Activity feed** — department-voiced entries emitted during manufacturing (per batch) and verification; polled on the Organization page.
- **QRU Creative Studio™** — brand standards (color system, typography, principles, QRU Shield master asset), AI product-page **creative briefs** (who-for, problem, skills, what's included, reading level, time, next path, related products), a Creative Quality Review queue, and a **publication gate** (products can't publish until Creative-reviewed).
- Verified by testing agent: backend 10/10, frontend 100%. Fixed related-product link projection, publish-gate tightening, and background-job None-guard.


## Implemented — Iteration 3 (2026-07-02) · "Research Once. Verify Once. Manufacture Forever."
- **Expanded Knowledge Record** — ~46 AI-manufacturable fields across 7 batches (Core Understanding, Comprehension Aids, Vocabulary & FAQ, Assessment, Audience Versions, Guidance Notes, Media & Product Assets): incl. Kingdom Lion Verification Questions™, Vocabulary Decoder™, Cheat Sheet™, Conversation Starter™, quiz, FAQ, story/children/teen/adult/professional versions, poster/video/podcast/presentation scripts, lesson plans. Each field has status (Empty/Draft/Verified/Approved) + version history.
- **AI Manufacturing Pipeline** — background job (`manufacturing_engine.py`) runs 7 sequential GPT-5.5 batches with live progress; `POST /knowledge-records/{id}/manufacture-all` → poll `GET /manufacturing-jobs/{id}`; auto-triggers on verification approval. Frontend shows live progress + accordion of manufactured fields with per-field regenerate/approve.
- **Manufacturing Recipes** — `POST /products/assemble` composes products from EXISTING KR fields (no regeneration); assembled products stamped with `kr_version`.
- **Traceability** — editing a KR bumps version and flips dependent products to "Needs Regeneration" (+ notification); `GET /knowledge-records/{id}/dependents`.
- **Dashboard** — Live Manufacturing Jobs panel, Recently Updated Records, needs-regeneration count.
- Verified by testing agent: backend 10/10 (incl. real full-pipeline run), frontend 100%.


## Implemented — Iteration 5 & 6 (2026-07-02) · V2.0 Evolution + Manufacturing Engine 2.0

### Enterprise Mode vs Consumer Mode (role-driven)
- `ModeContext` (frontend): Customer/ReadOnly roles are LOCKED to Consumer Mode; staff default to Enterprise with a header toggle to preview Consumer Mode ("Preview Consumer Mode" / "Enterprise" buttons). `App.js` ModeRouter renders `EnterpriseRoutes` or `ConsumerRoutes`.
- Consumer test user: learner@qru.com / qru-learn-2026 (Customer).

### Consumer Learning Platform (customer-facing, at /learn)
- `ConsumerLayout` + pages: Discover/Catalog, Learn (product), My Learning, Favorites, Certificates, Learning Paths.
- Backend `routers/consumer.py`: catalog, product understanding (assembled from the verified Knowledge Record — no regeneration), enroll, progress, favorite, certificates, pathways, recommendations. Collections: `consumer_enrollments`, `consumer_certificates`.
- Learn page renders: Kingdom Lion™ Verification card (expandable refs), 4-layer Layered Understanding selector (Quick Understanding/Understand It/Scientific Explanation/Professional Resources), 6 Learning Modes (Child/Consumer/Student/Professional/Scientific/Story), the full ordered QRU branded educational structure, Mark Complete → certificate.
- Demo data: 3 fully-populated verified records + published Treasure Standard products seeded via `consumer_seed.py` (is_demo=True, marked with "Demo Data" badges).

### Executive Command Center — Mission-First (Enterprise Mode only)
- New `MissionControl.js` (index dashboard) + `routers/command_center.py`: Daily Executive Briefing, Understanding Impact™ KPIs (people reached, lives helped, master records, understanding assets, lessons completed, certificates, treasure products, etc.) beside business metrics, transparent Enterprise Health breakdown (10 systems, expandable: why/owner/recommendation/urgency/next action), Department Status cards, intelligent Alerts & Recommendations panel, live org activity. ENTERPRISE MODE badge; mission copy "Verified knowledge enters. Understanding grows. Lives improve."
- `EnterpriseHealth.js` full dashboard page; `ExperienceLab.js` (AI experience evaluation).

### Manufacturing Engine 2.0 + Automatic Treasure Standard™ Quality Control
- `manufacturing2.py` + `routers/pipeline.py` (/api/manufacturing2/*): 13 Manufacturing Recipes™ (required KR fields + stages + deliverables), Missing-Content Detection, assembly-first `assemble` (composes from verified fields), `manufacture-missing` (fills only missing fields), Product Assembly stage + deliverables, 8 Release Gates.
- Automatic QC loop: scores product (GPT), routes each failing criterion to its owning department (routing rules), auto-improves (real GPT content rewrite + Creative Studio deterministic branding for Visual/Accessibility/Brand), re-scores monotonically until Treasure Standard™ thresholds met → certifies → unlocks gated Release. Release is LOCKED until all gates pass. `ManufacturingStudio.js` frontend with live stages/gates/QC panel.
- Verified: backend 11/11 (real GPT QC certified in 2 rounds), frontend 100%.

## Backlog / Next (updated 2026-07-02)
- **P0 — Memory Engineering™ / Music Studio™ / Character Voices™** (spec received): memory hooks/chants, music manufacturing recipe, character voice personalities, Legacy Learners™ children's division, adaptive memory formats. NOT yet built.
- **P1 — QRU Design Intelligence™ / Brand Library™** (spec received): Design Library, Master Asset Library, design language learning, design checklist, Creative Studio autonomy. NOT yet built.
- **P1 — Deep Product Assembly visual assets**: real print/mobile layouts, thumbnails, QR code images, store graphics (currently represented as assembly artifacts, not rendered binaries).
- P2: WebSocket/SSE for live org activity (currently polling); Recipe editor UI; wire director→order assignment; future divisions content.



## Backlog / Next (iteration 1 — superseded items kept for history)
- P1: Stream AI responses (SSE) in Command Console & product generation for token-by-token UX.
- P1: Real knowledge-growth time-series in Analytics (currently synthetic).
- P2: Product export (PDF/print), asset management + AI image generation for posters/infographics.
- P2: Licensing records & revenue analytics, pagination on large lists, version history UI for records.
- P2: Marketplace Intelligence + Reports modules, notification generation on workflow events.
