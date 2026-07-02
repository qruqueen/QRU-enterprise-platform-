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

## Backlog / Next
- Replace placeholder Focus Audio with licensed tracks/QRU frequency collections (URLs pending from client).
- Product Recipe editor per product type; per-section verification rejection; real knowledge-growth time-series.
- Wire director→order/record assignment (department currently shows enterprise-wide ops); college linkage on Manufacturing Orders/Products by `college_id`.
- Stand up future divisions (Trading/Finance/AI/…) content pipelines.

## Backlog / Next (iteration 1 — superseded items kept for history)
- P1: Stream AI responses (SSE) in Command Console & product generation for token-by-token UX.
- P1: Real knowledge-growth time-series in Analytics (currently synthetic).
- P2: Product export (PDF/print), asset management + AI image generation for posters/infographics.
- P2: Licensing records & revenue analytics, pagination on large lists, version history UI for records.
- P2: Marketplace Intelligence + Reports modules, notification generation on workflow events.
