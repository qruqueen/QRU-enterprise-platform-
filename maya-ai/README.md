# Maya AI™

Conversational financial-literacy tutor for kids and teens. Part of the **Ascend Financial Literacy Series™** / **QRU Health University™** ecosystem.

Maya doesn't teach static facts — she teaches a transferable interrogation method (**the Maya Method™**) that learners run against real-world money scenarios: debit cards today, game currencies, crypto, or whatever financial product shows up next.

## Run it

```bash
npm install
npm run dev
```

Then open the printed local URL (default `http://localhost:5173`).

```bash
npm run build     # type-check + production build to dist/
npm run preview   # preview the production build
```

## How it's organized

- `src/types.ts` — the fixed eight-category taxonomy, the three developmental layers (Little Maya / Maya Teen / Maya Next), the five fixed Maya Method™ questions, and the `Scenario` type.
- `src/data/scenarios/*.json` — the scenario library, one file per layer, following the JSON schema in the build spec (Section 6). **This is the only place you need to touch to add content** — no UI code changes required. Each scenario tags 2–4 categories and supplies `method_guidance`, one line of Maya's reasoning per question, in the fixed five-question order.
- `src/components/` — `LayerSelect`, `CategoryStrip`, `ScenarioCard`, `MayaMethod` (the five-question flow), `ProgressJournal`, `Header`.
- `src/hooks/useProgress.ts` — localStorage-backed progress: a journal of completed scenarios, per-layer category coverage, and a day streak.
- `src/utils/scenarioEngine.ts` — picks a random scenario for a layer, avoiding an immediate repeat.

## Adding a new scenario

Append an object to the matching layer's JSON file (`little.json`, `teen.json`, or `next.json`):

```json
{
  "id": "teen-example-id",
  "layer": "teen",
  "title": "Short Title",
  "prompt": "A second-person situation, styled like a notification, receipt, or chat message.",
  "categories": [4, 2, 1, 5],
  "method_guidance": [
    "What is this? — one sentence.",
    "Where is the money/value coming from? — one sentence.",
    "What am I agreeing to? — one sentence.",
    "What could happen next? — one sentence.",
    "How can I verify it? — one sentence."
  ]
}
```

`categories` uses the fixed IDs 1–8 from `src/types.ts` (Money Fundamentals, Digital Money, Invisible Debt, Virtual Economies, Money Safety, Banking & Financial Systems, Emerging Money, AI + Money). Use 2–4 per scenario — Maya's scenarios are never single-category by design.

## Status

This ships with 10 hand-written scenarios per layer (30 total), covering all eight categories at every layer, as a curated starting library per the build spec's "ship the curated, hand-reviewed scenario library first" guidance. Expanding coverage toward 5–8 scenarios per category per layer is pure data work from here — add JSON, no code changes.

Open-ended LLM-generated scenarios and a learner-typed "run my real situation through the Method" mode are intentionally out of scope for this build (v2, per the spec).
