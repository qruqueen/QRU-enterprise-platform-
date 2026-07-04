// QRU Data Integrity Gate™ / Safe Render™
// Validate required product fields before rendering. Missing fields never crash the UI —
// they get a safe placeholder and are logged for Founder maintenance.

export const PLACEHOLDERS = {
  title: "Untitled Product",
  subtitle: "",
  product_type: "Not Yet Assigned",
  who_for: "General Audience",
  description: "Coming Soon",
  price: 0,
  status: "Draft",
  thumbnail: "No Thumbnail",
  preview: "No Preview Available",
  knowledge_record_id: "Not Yet Assigned",
};

const REQUIRED = [
  "title", "subtitle", "product_type", "who_for", "description",
  "price", "status", "thumbnail", "preview", "knowledge_record_id",
];

// Return a normalized product with safe defaults + a list of missing fields (logged).
export function normalizeProduct(p) {
  if (!p || typeof p !== "object") {
    console.warn("[QRU Data Integrity Gate™] product is missing entirely — rendering safe shell.");
    return { ...PLACEHOLDERS, creative_brief: safeBrief(null), _missing: [...REQUIRED], _safe: true };
  }
  const brief = p.creative_brief || {};
  const resolved = {
    title: p.title,
    subtitle: p.subtitle,
    product_type: p.product_type,
    who_for: p.who_for ?? brief.who_for,
    description: p.description ?? p.tagline ?? brief.will_understand,
    price: p.price,
    status: p.status,
    thumbnail: p.thumbnail_url,
    preview: p.preview_url ?? p.preview_pdf_url,
    knowledge_record_id: p.knowledge_record_id,
  };
  const missing = REQUIRED.filter((f) => resolved[f] === undefined || resolved[f] === null || resolved[f] === "");
  if (missing.length) {
    console.warn(`[QRU Data Integrity Gate™] "${p.product_code || p.id || "product"}" missing: ${missing.join(", ")}. Rendering with safe placeholders.`);
  }
  return { ...p, creative_brief: safeBrief(p.creative_brief), _missing: missing, _safe: missing.length > 0 };
}

// A creative brief that is always safe to render (no undefined field access).
export function safeBrief(b) {
  const s = b && typeof b === "object" ? b : {};
  return {
    who_for: s.who_for || PLACEHOLDERS.who_for,
    problem_solved: s.problem_solved || "Coming Soon",
    will_understand: s.will_understand || "Coming Soon",
    skills_gained: Array.isArray(s.skills_gained) ? s.skills_gained : [],
    whats_included: Array.isArray(s.whats_included) ? s.whats_included : [],
    reading_level: s.reading_level || "Not Yet Assigned",
    completion_time: s.completion_time || "Not Yet Assigned",
    next_path: s.next_path || "Coming Soon",
    _present: !!(b && typeof b === "object" && Object.keys(b).length),
  };
}

// Simple field-level guard for any value.
export function safe(value, fallback = "Not Yet Assigned") {
  if (value === undefined || value === null || value === "") return fallback;
  return value;
}
