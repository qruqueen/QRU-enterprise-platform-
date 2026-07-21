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
        "canonical_specification": CANONICAL_SPEC_NAME,
        "canonical_spec_date": CANONICAL_SPEC_DATE,
        "sections_total": len(SECTIONS),
        "lifecycle_states": LIFECYCLE_STATES,
        "gold_standard_review_states": GOLD_STANDARD_STATES,
        "gold_standard_review_dimensions": REVIEW_DIMENSIONS,
        "validation_results": VALIDATION_RESULTS,
        "standard_name": STANDARD_NAME,
        "frozen": STANDARD_FROZEN,
        "constitution": constitution(),
    }


# =============================================================================
# QRU UKR™ Standard v1.1 — CANONICAL FULL SPECIFICATION (approved doc, 2026-07-18)
# -----------------------------------------------------------------------------
# The Founder-approved UKR document is THE standard. This is a single canonical
# schema (NOT a competing one): the 49 legacy flat fields are preserved as a live
# backward-compatibility surface, while every record also carries the full
# 24-section canonical `ukr` object. Unimplemented sections are present-but-empty
# (never omitted). Migration is non-destructive + idempotent (preserves any
# canonical content already populated by downstream engines).
# =============================================================================

CANONICAL_SPEC_NAME = "QRU UKR™ Standard v1.1 — Canonical Full Specification (24 Sections)"
CANONICAL_SPEC_DATE = "2026-07-18"

# =============================================================================
# STD-UKR-0001 — CONSTITUTIONAL REFINEMENTS (Founder Work Order, 2026-07-21)
# Additive-only. No schema migration. Freezes the standard after adoption.
# =============================================================================
STANDARD_NAME = "STD-UKR-0001 — QRU Executable Universal Knowledge Record™ Enterprise Standard"
STANDARD_FROZEN = True
CONSTITUTIONAL_VERSION = "STD-UKR-0001 · Constitutional Refinement (2026-07-21)"

# Item 1 — enterprise artifact naming (already adopted in code): Standard + Manifest.
ENTERPRISE_ARTIFACTS = {
    "EUKR": {"name": "Executable Universal Knowledge Record™", "owns": "governed knowledge (truth, value, what is worth teaching)"},
    "PMS": {"name": "Product Manufacturing Standard™", "abbr": "PMS™", "owns": "product-specific manufacturing requirements",
            "formerly": "Product Manufacturing Specification™"},
    "PMF": {"name": "Product Manifest™", "abbr": "PMF™", "owns": "manufacturing history, traceability, validations, approvals and audit",
            "formerly": "Product Manufacturing File™"},
}

# Item 2 — Constitutional Ownership: One Responsibility. One Owner.
CONSTITUTIONAL_OWNERSHIP_RULE = (
    "One Responsibility. One Owner. No constitutional artifact may duplicate another artifact's "
    "responsibility. The EUKR owns governed knowledge; the PMS™ owns product-specific manufacturing "
    "requirements; the PMF™ owns manufacturing history and auditability."
)

# Item 3 — Metadata Inclusion Rule.
METADATA_INCLUSION_RULE = [
    "It supports at least one downstream Factory capability.",
    "It has one responsible owner.",
    "It is inherited by at least one governed Factory component.",
]

# Item 4 — Separate Gold Standard review: two gates → Final Gold.
GOLD_STANDARD_GATES = {
    "knowledge_gate": {"evaluates": "the Executable Universal Knowledge Record™", "output": "Knowledge Certified"},
    "product_gate": {"evaluates": "manufactured products against their Product Manufacturing Standard™", "output": "Product Certified"},
    "final_gold_rule": "Final Gold Certification requires BOTH gates to pass when applicable.",
}

# Item 5 — Executable Completion Rule.
EXECUTABLE_COMPLETION_RULE = (
    "An EUKR is complete when every authorized Factory capability can perform its assigned responsibility "
    "using only: the EUKR, the applicable PMS™, and governed enterprise services — without requesting "
    "additional knowledge from the Founder or inventing missing verified information. If additional "
    "knowledge is required, the Factory shall return a GOVERNED DEFICIENCY rather than silently "
    "manufacturing incomplete products."
)


def governed_deficiency(capability, missing, kr_id=None):
    """Item 5 — the structured 'governed deficiency' a capability returns instead of silently
    manufacturing an incomplete product. Honest failure surface (Treasure Standard™)."""
    return {
        "governed_deficiency": True,
        "capability": capability,
        "knowledge_record_id": kr_id,
        "missing_information": missing if isinstance(missing, list) else [missing],
        "rule": "STD-UKR-0001 Executable Completion Rule",
        "message": "Manufacturing paused — required verified knowledge is missing. Nothing was faked or invented.",
    }


def constitution():
    """The frozen STD-UKR-0001 constitutional refinements (Work Order 2026-07-21)."""
    return {
        "standard_id": STANDARD_ID,
        "standard_name": STANDARD_NAME,
        "frozen": STANDARD_FROZEN,
        "constitutional_version": CONSTITUTIONAL_VERSION,
        "enterprise_artifacts": ENTERPRISE_ARTIFACTS,
        "constitutional_ownership_rule": CONSTITUTIONAL_OWNERSHIP_RULE,
        "metadata_inclusion_rule": METADATA_INCLUSION_RULE,
        "gold_standard_gates": GOLD_STANDARD_GATES,
        "executable_completion_rule": EXECUTABLE_COMPLETION_RULE,
        "success_criteria": [
            "Existing functionality is preserved.",
            "No migration of existing Knowledge Records is required unless necessary.",
            "All future Knowledge Records automatically inherit these constitutional rules.",
            "PMS™ and PMF™ inherit from the EUKR.",
            "The Factory continues to manufacture products using one canonical knowledge source.",
        ],
        "founder_note": ("The Factory architecture is mature. This is a constitutional refinement for clarity, "
                         "inheritance and long-term maintainability — not a redesign. STD-UKR-0001 is now frozen; "
                         "future improvement comes from manufacturing real EUKRs, not from expanding the standard."),
    }

# 24 governed sections. `implemented` = Phase-1 mapping is wired to real data today.
SECTIONS = [
    {"num": 1, "id": "record_identity", "name": "Record Identity", "implemented": True, "fields": [
        "knowledge_title", "published_title", "knowledge_record_id", "record_type", "version",
        "schema_version", "status", "lifecycle_state", "owner", "steward", "responsible_department",
        "created_date", "modified_date", "effective_date", "last_reviewed_date", "next_scheduled_review_date",
        "approval_status", "founder_review_status", "gold_standard_status", "supersedes", "superseded_by",
        "archive_status", "confidentiality_classification", "rights_classification", "brand_family",
        "applicable_product_families"]},
    {"num": 2, "id": "purpose_and_human_value", "name": "Purpose and Human Value", "implemented": True, "fields": [
        "why_this_knowledge_exists", "human_problem_addressed", "decision_improved", "learner_need_addressed",
        "consequence_if_misunderstood", "consequence_if_never_learned", "educational_importance",
        "societal_importance", "strategic_importance_to_qru", "intended_transformation", "primary_audience",
        "secondary_audiences", "excluded_audiences", "required_prior_knowledge", "expected_learner_outcome"]},
    {"num": 3, "id": "core_knowledge", "name": "Core Knowledge", "implemented": True, "fields": [
        "canonical_definition", "plain_language_definition", "core_explanation", "core_idea",
        "governing_principles", "essential_facts", "mechanisms", "processes", "components", "relationships",
        "conditions", "constraints", "boundaries", "assumptions", "known_limitations", "scope",
        "out_of_scope_claims", "open_questions", "unresolved_disputes", "technical_terminology",
        "key_takeaways", "remember_this_statement", "fact", "interpretation", "hypothesis", "analogy",
        "inference", "opinion", "unresolved_question"]},
    {"num": 4, "id": "evidence_and_verification", "name": "Evidence and Verification", "implemented": True, "fields": [
        "evidence_summary", "source_records", "citations", "source_type", "evidence_type", "evidence_strength",
        "verification_status", "confidence_score", "freshness_score", "last_verified_date",
        "next_reverification_date", "contradictory_evidence", "competing_interpretations",
        "known_counterexamples", "challenge_history", "reviewer_comments", "verification_history",
        "retractions_or_corrections", "evidence_gaps", "legal_or_compliance_concerns",
        "human_review_requirements", "evidence_items"]},
    {"num": 5, "id": "multi_audience_understanding", "name": "Multi-Audience Understanding", "implemented": False, "fields": [
        "required_translations"]},
    {"num": 6, "id": "teaching_and_learning_assets", "name": "Teaching and Learning Assets", "implemented": True, "fields": [
        "learning_objectives", "essential_question", "lesson_purpose", "analogies", "stories", "examples",
        "worked_examples", "counterexamples", "demonstrations", "case_studies", "scenarios", "misconceptions",
        "common_mistakes", "questions_learners_may_ask", "reflection_questions", "discussion_prompts",
        "practice_exercises", "assessments", "answer_keys", "formative_checks", "summative_checks",
        "application_tasks", "transfer_tasks", "memory_aids", "mnemonics", "teacher_notes", "parent_notes",
        "accommodations", "accessibility_considerations", "enrichment_options", "remediation_options"]},
    {"num": 7, "id": "visual_intelligence", "name": "Visual Intelligence", "implemented": False, "fields": [
        "visual_concept_summary", "diagram_specifications", "illustration_descriptions", "infographic_structure",
        "chart_requirements", "poster_concept", "knowledge_card_concept", "scene_descriptions", "image_prompts",
        "visual_hierarchy", "labels", "captions", "alt_text", "accessibility_notes", "brand_requirements",
        "approved_reference_assets", "prohibited_visual_interpretations", "animation_ready_visual_assets",
        "visual_verification_status"]},
    {"num": 8, "id": "audio_and_voice", "name": "Audio and Voice", "implemented": False, "fields": [
        "narration_script", "audiobook_script", "short_form_audio_script", "podcast_script",
        "pronunciation_guide", "emphasis_notes", "pacing", "pauses", "emotional_tone", "voice_characteristics",
        "regional_flavor", "captions_or_transcript", "accessibility_requirements", "music_or_sound_guidance",
        "prohibited_voice_imitation", "audio_asset_status"]},
    {"num": 9, "id": "video_and_animation", "name": "Video and Animation", "implemented": False, "fields": [
        "video_objective", "target_runtime", "scene_order", "storyboard", "scene_descriptions",
        "narration_alignment", "dialogue", "motion_notes", "character_actions", "camera_direction",
        "b_roll_guidance", "transitions", "on_screen_text", "captions", "audio_cues", "visual_dependencies",
        "animation_constraints", "continuity_requirements", "asset_references", "accessibility_requirements",
        "final_call_to_action"]},
    {"num": 10, "id": "ai_and_agent_support", "name": "AI and Agent Support", "implemented": False, "fields": [
        "semantic_search_terms", "synonyms", "alternate_wording", "embeddings_metadata", "related_questions",
        "likely_user_intents", "tutor_responses", "socratic_prompts", "conversation_examples",
        "correction_responses", "uncertainty_responses", "refusal_boundaries", "prompt_pack",
        "prompt_variations", "prompt_evaluations", "retrieval_guidance", "hallucination_risks",
        "agent_permissions", "permitted_actions", "prohibited_actions", "escalation_rules",
        "human_review_triggers"]},
    {"num": 11, "id": "product_bindings", "name": "Product Bindings", "implemented": False, "fields": ["bindings"]},
    {"num": 12, "id": "manufacturing_readiness", "name": "Manufacturing Readiness", "implemented": False, "fields": [
        "eligible_products", "product_readiness_by_type", "required_assets", "missing_assets",
        "blocked_products", "manufacturing_warnings", "specification_compatibility", "schema_compatibility",
        "export_eligibility", "content_completeness", "translation_completeness", "visual_completeness",
        "audio_completeness", "assessment_completeness", "verification_completeness", "certification_state"]},
    {"num": 13, "id": "dependencies_and_knowledge_graph", "name": "Dependencies and Knowledge Graph", "implemented": False, "fields": [
        "upstream_dependencies", "downstream_consumers", "prerequisite_records", "dependent_records",
        "related_records", "conflicting_records", "replacement_records", "evidence_dependencies",
        "visual_dependencies", "legal_dependencies", "product_dependencies", "department_dependencies",
        "agent_dependencies", "fallback_behavior", "criticality", "validation_metrics", "change_impact_rules",
        "dependencies"]},
    {"num": 14, "id": "factory_interface", "name": "Factory Interface (machine-readable)", "implemented": True, "fields": [
        "record_identity", "title", "version", "schema_version", "lifecycle_state", "verification_status",
        "gold_standard_status", "confidence", "audience_availability", "available_teaching_assets",
        "available_visual_assets", "available_audio_assets", "eligible_product_types", "product_bindings",
        "dependencies", "missing_requirements", "active_warnings", "permissions", "last_update",
        "review_due_date", "compatibility_status"]},
    {"num": 15, "id": "human_interface", "name": "Human Interface", "implemented": True, "fields": [
        "knowledge_title", "plain_language_purpose", "status", "version", "core_definition", "core_idea",
        "evidence_status", "audience_translations", "teaching_assets", "products_available",
        "missing_requirements", "dependencies", "gold_standard_status", "review_history", "next_action"]},
    {"num": 16, "id": "agent_interface", "name": "Agent Interface", "implemented": False, "fields": ["query_capabilities"]},
    {"num": 17, "id": "gold_standard_review", "name": "QRU Gold Standard Review", "implemented": False, "fields": [
        "reviews", "review_state"]},
    {"num": 18, "id": "lifecycle", "name": "Lifecycle", "implemented": True, "fields": ["lifecycle_state", "transitions"]},
    {"num": 19, "id": "executable_behaviors", "name": "Executable Behaviors", "implemented": False, "fields": [
        "event_response_rules"]},
    {"num": 20, "id": "intelligence_value_and_priority", "name": "Intelligence Value and Priority", "implemented": False, "fields": [
        "educational_value", "societal_value", "strategic_value", "frequency_of_use", "downstream_consumer_count",
        "risk_if_incorrect", "harm_if_misunderstood", "urgency", "evidence_volatility", "manufacturing_potential",
        "revenue_potential", "community_benefit", "maintenance_cost", "review_priority", "reverification_priority"]},
    {"num": 21, "id": "rights_brand_enterprise_controls", "name": "Rights, Brand, and Enterprise Controls", "implemented": False, "fields": [
        "copyright_owner", "trademark_references", "licensing_rights", "source_permissions",
        "third_party_restrictions", "allowed_product_uses", "prohibited_uses", "attribution_requirements",
        "confidentiality_level", "privacy_classification", "child_safety_requirements", "legal_review_status",
        "compliance_status", "qru_brand_family", "approved_design_system", "distribution_permissions",
        "monetization_permissions", "territory_limitations", "expiration_dates"]},
    {"num": 22, "id": "continuous_improvement", "name": "Continuous Improvement", "implemented": False, "fields": [
        "revision_history", "change_rationale", "user_feedback", "learner_feedback", "educator_feedback",
        "product_performance", "comprehension_results", "assessment_outcomes", "support_questions",
        "manufacturing_failures", "returns_or_complaints", "improvement_proposals", "approved_improvements",
        "rejected_changes", "lessons_learned", "linked_adr"]},
    {"num": 23, "id": "versioning_and_compatibility", "name": "Versioning and Compatibility", "implemented": True, "fields": [
        "version_number", "schema_version", "compatibility_declaration", "migration_history",
        "backward_compatibility_status", "deprecation_status", "supersession_links", "changed_fields",
        "affected_interfaces", "affected_products", "affected_dependencies"]},
    {"num": 24, "id": "validation_rules", "name": "Validation Rules", "implemented": False, "fields": [
        "checks", "last_validation_result", "validation_details"]},
]

LIFECYCLE_STATES = [
    "Proposed", "Discovered", "Researching", "Draft", "Internal Review", "Verification Required",
    "Verified", "Understanding Review", "Gold Review", "Founder Review Required", "Approved",
    "Gold Certified", "Manufacturing Ready", "Published", "Under Observation", "Reverification Due",
    "Revision Required", "Deprecated", "Superseded", "Archived",
]

GOLD_STANDARD_STATES = [
    "Not Reviewed", "Review Scheduled", "Under Review", "Returned for Correction", "Conditionally Approved",
    "Approved", "Gold Certified", "Certification Suspended", "Reverification Required", "Certification Revoked",
]

REVIEW_DIMENSIONS = [
    "Knowledge Integrity", "Evidence and Verification", "Understanding and Clarity", "Educational Effectiveness",
    "Audience Suitability", "Accessibility", "Product Completeness", "Manufacturing Compliance",
    "Technical Validation", "Brand Alignment", "Ethical and Legal Readiness", "Dependency Integrity",
    "Publication Readiness", "Founder Approval", "Treasure Standard Alignment",
]

VALIDATION_RESULTS = ["pass", "warning", "failure", "blocked", "requires_human_review"]

# Sections whose Phase-1 mapping is wired to real data today.
IMPLEMENTED_SECTIONS = [s["id"] for s in SECTIONS if s["implemented"]]
PENDING_SECTIONS = [s["id"] for s in SECTIONS if not s["implemented"]]


def _blank_section(section):
    return {f: "" for f in section["fields"]}


def blank_canonical():
    """Full 24-section canonical object with every field present-but-empty."""
    return {s["id"]: _blank_section(s) for s in SECTIONS}


def derive_lifecycle_state(rec):
    """Map the current governance status onto a canonical lifecycle state (non-destructive read)."""
    if rec.get("treasure_standard"):
        return "Gold Certified"
    if rec.get("approval_status") == "Approved":
        return "Approved"
    vs = (rec.get("verification_status") or "").strip()
    if vs == "Verified":
        return "Verified"
    if vs in ("Under Review", "In Review"):
        return "Internal Review"
    if vs in ("Pending", "Pending Founder Review", "Founder Review Required"):
        return "Founder Review Required"
    if vs in ("Archived",):
        return "Archived"
    return "Draft"


def _nonempty(v):
    return v not in (None, "", [], {}, ())


def build_canonical(rec, existing=None):
    """Build the canonical `ukr` object for a legacy record, mapping the 49 flat fields into their
    canonical homes. Non-destructive: any already-populated canonical value in `existing` wins."""
    u = blank_canonical()
    lifecycle = derive_lifecycle_state(rec)

    # --- Section 1: Record Identity ---
    s1 = u["record_identity"]
    s1["knowledge_title"] = rec.get("knowledge_title") or rec.get("title") or ""
    s1["published_title"] = rec.get("published_title") or rec.get("title") or ""
    s1["knowledge_record_id"] = rec.get("kr_code") or ""
    s1["record_type"] = "Knowledge Record"
    s1["version"] = rec.get("version", 1)
    s1["schema_version"] = SCHEMA_VERSION
    s1["status"] = rec.get("verification_status") or "Draft"
    s1["lifecycle_state"] = lifecycle
    s1["owner"] = rec.get("owner_id") or rec.get("created_by") or ""
    s1["responsible_department"] = rec.get("division") or ""
    s1["created_date"] = rec.get("created_at") or ""
    s1["modified_date"] = rec.get("updated_at") or ""
    s1["approval_status"] = rec.get("approval_status") or ""
    s1["founder_review_status"] = "Approved" if rec.get("approval_status") == "Approved" else "Founder Review Required"
    s1["gold_standard_status"] = "Gold Certified" if rec.get("treasure_standard") else "Not Reviewed"
    s1["archive_status"] = "Active"
    s1["brand_family"] = "QRU"

    # --- Section 2: Purpose and Human Value ---
    s2 = u["purpose_and_human_value"]
    s2["why_this_knowledge_exists"] = rec.get("why_it_matters") or ""
    s2["educational_importance"] = rec.get("why_it_matters") or ""
    s2["learner_need_addressed"] = rec.get("the_question") or ""

    # --- Section 3: Core Knowledge ---
    s3 = u["core_knowledge"]
    s3["canonical_definition"] = rec.get("verified_truth") or ""
    s3["plain_language_definition"] = rec.get("simple_answer") or ""
    s3["core_explanation"] = rec.get("qru_translation") or rec.get("consumer_translation") or ""
    s3["core_idea"] = rec.get("memory_sentence") or ""
    s3["governing_principles"] = rec.get("deep_roots") or ""
    s3["technical_terminology"] = rec.get("key_vocabulary") or []
    s3["analogy"] = rec.get("everyday_analogy") or ""
    s3["remember_this_statement"] = rec.get("memory_sentence") or ""

    # --- Section 4: Evidence and Verification ---
    s4 = u["evidence_and_verification"]
    s4["source_records"] = rec.get("references") or []
    s4["citations"] = rec.get("sources") or []
    s4["verification_status"] = rec.get("verification_status") or ""
    s4["confidence_score"] = rec.get("confidence_score") or ""
    s4["reviewer_comments"] = rec.get("reviewer") or ""
    s4["verification_history"] = [rec["verification"]] if _nonempty(rec.get("verification")) else []

    # --- Section 6: Teaching and Learning Assets ---
    s6 = u["teaching_and_learning_assets"]
    s6["essential_question"] = rec.get("the_question") or ""
    s6["examples"] = rec.get("real_world_example") or ""
    s6["stories"] = rec.get("story") or ""
    s6["practice_exercises"] = rec.get("practice_activities") or []
    s6["application_tasks"] = rec.get("practice_application") or []

    # --- Section 14: Factory Interface (machine-readable projection) ---
    s14 = u["factory_interface"]
    s14["record_identity"] = rec.get("kr_code") or ""
    s14["title"] = s1["knowledge_title"]
    s14["version"] = rec.get("version", 1)
    s14["schema_version"] = SCHEMA_VERSION
    s14["lifecycle_state"] = lifecycle
    s14["verification_status"] = rec.get("verification_status") or ""
    s14["gold_standard_status"] = s1["gold_standard_status"]
    s14["confidence"] = rec.get("confidence_score") or ""
    s14["eligible_product_types"] = []
    s14["last_update"] = rec.get("updated_at") or ""
    s14["compatibility_status"] = "compatible"

    # --- Section 15: Human Interface projection ---
    s15 = u["human_interface"]
    s15["knowledge_title"] = s1["knowledge_title"]
    s15["plain_language_purpose"] = rec.get("why_it_matters") or ""
    s15["status"] = rec.get("verification_status") or "Draft"
    s15["version"] = rec.get("version", 1)
    s15["core_definition"] = rec.get("verified_truth") or ""
    s15["core_idea"] = rec.get("memory_sentence") or ""
    s15["gold_standard_status"] = s1["gold_standard_status"]

    # --- Section 18: Lifecycle ---
    u["lifecycle"]["lifecycle_state"] = lifecycle
    u["lifecycle"]["transitions"] = []

    # --- Section 23: Versioning and Compatibility ---
    s23 = u["versioning_and_compatibility"]
    s23["version_number"] = rec.get("version", 1)
    s23["schema_version"] = SCHEMA_VERSION
    s23["backward_compatibility_status"] = "backward-compatible (legacy flat fields preserved)"
    s23["migration_history"] = rec.get("migration") or {}

    # Non-destructive merge: preserve any canonical values already populated downstream.
    if existing:
        for sec_id, fields in u.items():
            prev = existing.get(sec_id) or {}
            for fk in fields:
                if _nonempty(prev.get(fk)) and not _nonempty(fields[fk]):
                    fields[fk] = prev[fk]
    return u


def _populated_sections(u):
    """List of section ids that have at least one populated field."""
    out = []
    for s in SECTIONS:
        data = u.get(s["id"], {})
        if any(_nonempty(data.get(f)) for f in s["fields"]):
            out.append(s["id"])
    return out


def canonical_spec():
    """The single canonical UKR specification (the approved doc, as implemented)."""
    return {
        "standard_id": STANDARD_ID,
        "name": "QRU Universal Knowledge Record™",
        "canonical_specification": CANONICAL_SPEC_NAME,
        "canonical_spec_date": CANONICAL_SPEC_DATE,
        "schema_version": SCHEMA_VERSION,
        "canonical_collection": CANONICAL_COLLECTION,
        "sections_total": len(SECTIONS),
        "implemented_sections": IMPLEMENTED_SECTIONS,
        "pending_sections": PENDING_SECTIONS,
        "sections": [{"num": s["num"], "id": s["id"], "name": s["name"],
                      "implemented": s["implemented"], "field_count": len(s["fields"]),
                      "fields": s["fields"]} for s in SECTIONS],
        "lifecycle_states": LIFECYCLE_STATES,
        "gold_standard_review_states": GOLD_STANDARD_STATES,
        "gold_standard_review_dimensions": REVIEW_DIMENSIONS,
        "validation_results": VALIDATION_RESULTS,
        "governance": [
            "One governed source of truth; knowledge separated from product formatting.",
            "Structured, machine-readable, version-controlled, governable knowledge object.",
            "Legacy 49 flat fields preserved as a live backward-compatibility surface.",
            "Unimplemented sections are present-but-empty, never omitted.",
            "Product-specific manufacturing metadata stays outside the canonical UKR (that is the PMS™).",
            "Knowledge-First™ enforced; Founder-authored book exception preserved.",
        ],
    }


async def migrate_to_canonical(actor="Founder", dry_run=False):
    """Phase-1 NON-DESTRUCTIVE + idempotent migration: attach the full 24-section canonical `ukr`
    object to every record, mapping the legacy flat fields into their canonical homes. Preserves
    IDs, versions, approvals, downstream links and any canonical content already populated."""
    docs = await db[CANONICAL_COLLECTION].find({}, {"_id": 0}).to_list(5000)
    migrated, sample = 0, []
    section_pop_totals = {s["id"]: 0 for s in SECTIONS}
    for d in docs:
        u = build_canonical(d, existing=d.get("ukr"))
        populated = _populated_sections(u)
        for sid in populated:
            section_pop_totals[sid] += 1
        set_fields = {
            "ukr": u,
            "schema_version": SCHEMA_VERSION,
            "canonical_spec": CANONICAL_SPEC_NAME,
            "canonical_spec_date": CANONICAL_SPEC_DATE,
            "canonical_migration": {
                "migrated_at": _now(), "migrated_by": actor,
                "sections_total": len(SECTIONS), "sections_populated": len(populated),
                "populated_sections": populated,
                "preserved_kr_code": d.get("kr_code"), "preserved_version": d.get("version", 1),
                "from_schema": d.get("schema_version") or "legacy",
                "non_destructive": True,
            },
        }
        if not dry_run:
            await db[CANONICAL_COLLECTION].update_one({"id": d["id"]}, {"$set": set_fields})
        migrated += 1
        if len(sample) < 6:
            sample.append({"kr_code": d.get("kr_code"),
                           "knowledge_title": u["record_identity"]["knowledge_title"],
                           "lifecycle_state": u["record_identity"]["lifecycle_state"],
                           "sections_populated": len(populated)})
    sections_completed = sorted({sid for sid, n in section_pop_totals.items() if n > 0})
    return {
        "total": len(docs), "migrated": migrated, "dry_run": dry_run,
        "schema_version": SCHEMA_VERSION, "canonical_specification": CANONICAL_SPEC_NAME,
        "sections_total": len(SECTIONS),
        "sections_completed": sections_completed,
        "sections_completed_count": len(sections_completed),
        "sections_remaining": [s["id"] for s in SECTIONS if s["id"] not in sections_completed],
        "section_population_counts": section_pop_totals,
        "compatibility_status": "backward-compatible — legacy flat fields untouched; no production behavior changed",
        "redeploy_required": True,
        "sample": sample,
    }


async def migration_status():
    """Factory-wide canonical migration status (read-only)."""
    docs = await db[CANONICAL_COLLECTION].find({}, {"_id": 0, "ukr": 1, "canonical_migration": 1}).to_list(5000)
    total = len(docs)
    migrated = sum(1 for d in docs if d.get("ukr"))
    dist = {}
    for d in docs:
        cm = d.get("canonical_migration") or {}
        n = cm.get("sections_populated", 0) if d.get("ukr") else 0
        dist[n] = dist.get(n, 0) + 1
    return {
        "total": total, "migrated": migrated, "not_migrated": total - migrated,
        "canonical_specification": CANONICAL_SPEC_NAME, "sections_total": len(SECTIONS),
        "sections_populated_distribution": dict(sorted(dist.items())),
        "fully_backward_compatible": True,
    }
