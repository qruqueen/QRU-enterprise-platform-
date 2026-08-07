export type Layer = "little" | "teen" | "next";

export interface LayerInfo {
  id: Layer;
  name: string;
  ageBand: string;
  focus: string;
}

export const LAYERS: LayerInfo[] = [
  {
    id: "little",
    name: "Little Maya",
    ageBand: "~6–10",
    focus: "Money, value, choices, digital spending in games, saving, basic safety.",
  },
  {
    id: "teen",
    name: "Maya Teen",
    ageBand: "~11–16",
    focus:
      "Banking, debit, subscriptions, first paychecks, credit, BNPL, scams, virtual economies, intro crypto.",
  },
  {
    id: "next",
    name: "Maya Next",
    ageBand: "~17+",
    focus:
      "Credit, taxes, debt, financial systems, investing, digital assets, AI finance, emerging payments.",
  },
];

/** The fixed eight-category taxonomy. IDs are stable and referenced by scenario data. */
export type CategoryId = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;

export interface Category {
  id: CategoryId;
  emoji: string;
  name: string;
  covers: string;
}

export const CATEGORIES: Category[] = [
  {
    id: 1,
    emoji: "💵",
    name: "Money Fundamentals",
    covers:
      "What money is, earning, spending, saving, needs vs. wants, budgeting, opportunity cost",
  },
  {
    id: 2,
    emoji: "📱",
    name: "Digital Money",
    covers:
      "Debit cards, mobile wallets, apps, P2P payments, subscriptions, balances, pending transactions",
  },
  {
    id: 3,
    emoji: "💳",
    name: "Invisible Debt",
    covers:
      "Credit cards, interest, APR, BNPL, minimum payments, overdrafts — future income already committed",
  },
  {
    id: 4,
    emoji: "🎮",
    name: "Virtual Economies",
    covers: 'Game currencies, virtual goods, gift cards, points, loot boxes, "do I actually own this?"',
  },
  {
    id: 5,
    emoji: "🛡️",
    name: "Money Safety",
    covers: "Scams, phishing, identity theft, fake investments, impersonation, AI-generated scams/deepfakes",
  },
  {
    id: 6,
    emoji: "🏦",
    name: "Banking & Financial Systems",
    covers: "Checking/savings, FDIC insurance, payment networks, transfers, holds, fees, interest",
  },
  {
    id: 7,
    emoji: "🌐",
    name: "Emerging Money",
    covers: "Crypto, stablecoins, blockchain, tokenization, CBDCs — what's real today vs. speculative",
  },
  {
    id: 8,
    emoji: "🤖",
    name: "AI + Money",
    covers:
      'AI shopping assistants, algorithmic pricing, AI scams, agentic payments — "what authority did you give the machine?"',
  },
];

export const categoryById = (id: CategoryId): Category =>
  CATEGORIES.find((c) => c.id === id)!;

/** The five fixed Maya Method questions, in order. This sequence never changes. */
export const MAYA_METHOD_QUESTIONS = [
  "What is this?",
  "Where is the money/value coming from?",
  "What am I agreeing to?",
  "What could happen next?",
  "How can I verify it?",
] as const;

export interface Scenario {
  id: string;
  layer: Layer;
  title: string;
  /** Second-person prompt styled like a notification, receipt, or chat message. */
  prompt: string;
  /** 2–4 category IDs this scenario touches. */
  categories: CategoryId[];
  /** Maya's model reasoning for each of the five Maya Method questions, in order. */
  method_guidance: [string, string, string, string, string];
}
