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

## Backlog / Next
- P1: Stream AI responses (SSE) in Command Console & product generation for token-by-token UX.
- P1: Real knowledge-growth time-series in Analytics (currently synthetic).
- P2: Product export (PDF/print), asset management + AI image generation for posters/infographics.
- P2: Licensing records & revenue analytics, pagination on large lists, version history UI for records.
- P2: Marketplace Intelligence + Reports modules, notification generation on workflow events.
