"""QRU Universal Knowledge Record™ (UKR™) — Standard v1.1.

CONSTITUTIONAL OWNERSHIP:  UKR™ = TRUTH.
The UKR owns "what is true, valuable, and worth teaching" — and NOTHING about how a product is built.
Product-specific manufacturing metadata lives in a Product Manufacturing Standard™ (PMS™), never here.

Canonical collection: `knowledge_records`. The KR 2.0 `knowledge_engine_records` collection is frozen as
read-only legacy (Decoder may still read it; no new writes).

v1.1 Title Section (governed order):
  1. Knowledge Title       — [Domain] — [Primary Topic]      · human selection / navigation (alphabetical)
  2. Published Title       — audience-facing product title    · may vary per product
  3. Knowledge Record ID   — kr_code (KR-00001)               · immutable machine identity (Option A)
Backward-compat alias:  "Factory Title" / legacy `title` → `knowledge_title` (single source of truth).
"""
import re
from datetime import datetime, timezone

from database import db

SCHEMA_VERSION = "QRU UKR™ Standard v1.1"
STANDARD_ID = "STD-UKR-0001"
CANONICAL_COLLECTION = "knowledge_records"
LEGACY_COLLECTION = "knowledge_engine_records"  # frozen read-only

# Deterministic category → knowledge domain (human-readable, alphabetically sortable).
_DOMAIN_MAP = {
    "heart health": "Health", "health": "Health", "medical": "Health", "brain": "Neuroscience",
    "neuroscience": "Neuroscience", "memory": "Learning", "learning": "Learning", "education": "Learning",
    "forex": "Finance", "trading": "Finance", "finance": "Finance", "money": "Finance", "investing": "Finance",
    "ai": "AI", "artificial intelligence": "AI", "prompt": "AI", "technology": "Technology",
    "communication": "Communication", "critical thinking": "Critical Thinking", "thinking": "Critical Thinking",
    "decision": "Decision Making", "wisdom": "Wisdom", "verification": "Verification", "science": "Science",
    "history": "History", "leadership": "Leadership", "psychology": "Psychology", "mindfulness": "Wellbeing",
    "governance": "Governance", "safety": "Safety", "law": "Legal", "legal": "Legal",
}
_ARTICLES = ("the ", "a ", "an ", "how ", "why ", "what ")


def _now():
    return datetime.now(timezone.utc).isoformat()


def domain_from_category(category, title=""):
    # Prefer the record's own category; fall back to keyword scan with WORD BOUNDARIES so short
    # keys like "ai" never match inside "daily"/"train"/"sustains".
    cat = (category or "").lower()
    for key, dom in _DOMAIN_MAP.items():
        if re.search(r"\b" + re.escape(key) + r"\b", cat):
            return dom
    if category and category.strip():
        return category.strip().title()
    t = (title or "").lower()
    for key, dom in _DOMAIN_MAP.items():
        if re.search(r"\b" + re.escape(key) + r"\b", t):
            return dom
    return "General"


def _primary_topic(title, subtitle=""):
    """Derive a concise, human-selectable primary topic from a statement-style legacy title."""
    src = (subtitle or title or "").strip()
    low = src.lower()
    for a in _ARTICLES:
        if low.startswith(a):
            src = src[len(a):]
            break
    # keep the first clause; cap length for topic-selection menus.
    for sep in [" — ", " – ", ": ", ". ", " that ", " which "]:
        if sep in src:
            src = src.split(sep)[0]
            break
    src = src.strip().rstrip(".").strip()
    if len(src) > 58:
        src = src[:58].rsplit(" ", 1)[0] + "…"
    return src[:1].upper() + src[1:] if src else (title or "Untitled")


def build_knowledge_title(category, title, subtitle=""):
    dom = domain_from_category(category, title)
    topic = _primary_topic(title, subtitle)
    return f"{dom} — {topic}"


def title_section(rec):
    """The governed v1.1 title section for a UKR (order-locked)."""
    return {
        "knowledge_title": rec.get("knowledge_title") or rec.get("title") or "",  # alias: legacy title
        "published_title": rec.get("published_title") or rec.get("title") or "",
        "knowledge_record_id": rec.get("kr_code") or rec.get("id") or "",
        "subtitle": rec.get("subtitle") or "",
        "record_version": rec.get("version", 1),
        "schema_version": rec.get("schema_version") or SCHEMA_VERSION,
        "lifecycle_status": rec.get("lifecycle_status") or rec.get("verification_status") or "Draft",
        "founder_review_status": rec.get("founder_review_status") or ("Approved" if rec.get("approval_status") == "Approved" else "Founder Review Required"),
        "gold_master_status": rec.get("gold_master_status") or ("Certified" if rec.get("treasure_standard") else "Not Yet Certified"),
    }


def validate(rec):
    """v1.1 validation. Returns (ok, [issues]) in plain language with the responsible owner."""
    issues = []
    kt = rec.get("knowledge_title") or ""
    if not kt.strip():
        issues.append("Knowledge Title is missing. Owner: Knowledge Manufacturing Engine™.")
    elif " — " not in kt:
        issues.append("Knowledge Title must be '[Domain] — [Primary Topic]'. Owner: Knowledge Manufacturing Engine™.")
    if not (rec.get("published_title") or "").strip():
        issues.append("Published Title is missing. Owner: Product Manufacturing Standard™.")
    if not (rec.get("kr_code") or "").strip():
        issues.append("Knowledge Record ID (kr_code) is missing. Owner: Factory (immutable identity).")
    if not (rec.get("schema_version") or "").strip():
        issues.append("Schema version is missing. Owner: UKR™ Standard.")
    if rec.get("migrated_from") and not rec.get("migration"):
        issues.append("Migrated record has no migration history. Owner: Migration.")
    return (len(issues) == 0, issues)


async def migrate_all(actor="Founder", dry_run=False):
    """Governed, NON-DESTRUCTIVE migration of every canonical record to the v1.1 title structure.
    Preserves the original title, kr_code, version history, approvals, provenance and downstream links."""
    docs = await db[CANONICAL_COLLECTION].find({}, {"_id": 0}).to_list(5000)
    migrated, skipped, seen_titles = [], [], {}
    for d in docs:
        legacy_title = d.get("title", "")
        knowledge_title = d.get("knowledge_title") or build_knowledge_title(d.get("category"), legacy_title, d.get("subtitle"))
        # de-duplicate identical knowledge titles (append the immutable id to keep it distinguishable).
        base = knowledge_title
        if seen_titles.get(base) and seen_titles[base] != d.get("id"):
            knowledge_title = f"{base} ({d.get('kr_code')})"
        seen_titles[base] = d.get("id")
        already = bool(d.get("schema_version") == SCHEMA_VERSION and d.get("knowledge_title"))
        set_fields = {
            "knowledge_title": knowledge_title,
            "published_title": d.get("published_title") or legacy_title,
            "schema_version": SCHEMA_VERSION,
            "domain": d.get("domain") or domain_from_category(d.get("category"), legacy_title),
            "factory_title_alias": knowledge_title,  # "Factory Title" → Knowledge Title (compat)
            "legacy_title": d.get("legacy_title") or legacy_title,
            "migration": d.get("migration") or {
                "migrated_at": _now(), "migrated_by": actor, "from_schema": "legacy",
                "to_schema": SCHEMA_VERSION, "preserved_title": legacy_title, "preserved_kr_code": d.get("kr_code"),
            },
        }
        if not dry_run and not already:
            await db[CANONICAL_COLLECTION].update_one({"id": d["id"]}, {"$set": set_fields})
        (skipped if already else migrated).append({
            "kr_code": d.get("kr_code"), "knowledge_title": knowledge_title,
            "published_title": set_fields["published_title"]})
    return {"total": len(docs), "migrated": len(migrated), "already_v11": len(skipped),
            "dry_run": dry_run, "schema_version": SCHEMA_VERSION, "sample": migrated[:8]}


async def registry(verified_only=False):
    """All canonical UKRs, default-sorted alphabetically by Knowledge Title (v1.1 discovery standard)."""
    q = {}
    docs = await db[CANONICAL_COLLECTION].find(q, {"_id": 0}).to_list(5000)
    def verified(d):
        return (d.get("verification_status") == "Verified" or d.get("approval_status") == "Approved"
                or d.get("verified_external") or d.get("treasure_standard"))
    rows = []
    for d in docs:
        if verified_only and not verified(d):
            continue
        kt = d.get("knowledge_title") or build_knowledge_title(d.get("category"), d.get("title"), d.get("subtitle"))
        rows.append({
            "id": d.get("id"), "knowledge_record_id": d.get("kr_code"),
            "knowledge_title": kt, "published_title": d.get("published_title") or d.get("title"),
            "domain": d.get("domain") or domain_from_category(d.get("category"), d.get("title")),
            "verified": verified(d), "schema_version": d.get("schema_version") or "legacy",
            "lifecycle_status": d.get("verification_status") or "Draft",
        })
    # Primary: Knowledge Title · Secondary: Published Title · Tertiary: Knowledge Record ID
    rows.sort(key=lambda r: ((r["knowledge_title"] or "").lower(), (r["published_title"] or "").lower(), r["knowledge_record_id"] or ""))
    return rows


def standard():
    return {
        "standard_id": STANDARD_ID, "name": "QRU Universal Knowledge Record™", "schema_version": SCHEMA_VERSION,
        "constitutional_ownership": "UKR™ = TRUTH (what is true, valuable, and worth teaching).",
        "canonical_collection": CANONICAL_COLLECTION, "legacy_collection_frozen": LEGACY_COLLECTION,
        "title_section_order": ["Knowledge Title", "Published Title", "Knowledge Record ID", "Subtitle",
                                "Record Version", "Schema Version", "Lifecycle Status", "Founder Review Status",
                                "Gold Master Status"],
        "id_policy": "Option A — immutable sequential Knowledge Record IDs (KR-00001). Never reused, never changed.",
        "rules": [
            "The UKR must never duplicate product-specific manufacturing metadata (that is the PMS™).",
            "Knowledge Record ID is machine identity; Knowledge Title is human selection; Published Title is for readers.",
            "The Knowledge Record ID must never appear before the Knowledge Title in human-facing lists.",
            "Default discovery order is alphabetical by Knowledge Title.",
            "Migration is non-destructive: originals, IDs, versions, approvals and links are preserved.",
        ],
    }
