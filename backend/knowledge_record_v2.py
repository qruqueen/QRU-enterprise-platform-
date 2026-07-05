"""QRU Knowledge Record 2.0™ (MO-003) — the permanent enterprise knowledge architecture.

A Knowledge Record is a manufacturing blueprint, not a document. Every section is an
independent, versioned, reviewable managed object. Products are manufactured FROM sections
via the Manufacturing Dependency Map — never the other way around. Extensible by design:
adding a new section definition never requires a database redesign.

Deterministic ($0 AI). AI fills section content later; the architecture is built now.
"""
from datetime import datetime, timezone

SCHEMA_VERSION = 2

# --------------------------------------------------------------------------- Section registry
# Extensible: append new definitions here; storage is a keyed map so no migration is needed.
SECTION_DEFS = [
    # key, title, group
    ("executive_summary", "Executive Summary", "Core"),
    ("deep_explanation", "Deep Explanation", "Core"),
    ("consumer_translation", "Consumer Translation™", "Translations"),
    ("teacher_translation", "Teacher Translation™", "Translations"),
    ("child_translation", "Child Translation™", "Translations"),
    ("teen_translation", "Teen Translation™", "Translations"),
    ("adult_translation", "Adult Translation™", "Translations"),
    ("caregiver_translation", "Caregiver Translation™", "Translations"),
    ("professional_translation", "Professional Translation™", "Translations"),
    ("qru_translation", "QRU Translation™", "Translations"),
    ("story_version", "Story Version", "Understanding"),
    ("analogy_library", "Analogy Library", "Understanding"),
    ("examples", "Examples", "Understanding"),
    ("counterexamples", "Counterexamples", "Understanding"),
    ("common_misunderstandings", "Common Misunderstandings", "Understanding"),
    ("verification_notes", "Verification Notes", "Verification"),
    ("scientific_references", "Scientific References", "Verification"),
    ("historical_context", "Historical Context", "Verification"),
    ("biblical_perspective", "Biblical Perspective", "Verification"),
    ("practical_applications", "Practical Applications", "Application"),
    ("memory_sentences", "Memory Sentences™", "Application"),
    ("vocabulary_decoder", "Vocabulary Decoder™", "Application"),
    ("question_library", "Question Library", "Assessment"),
    ("quiz_bank", "Quiz Bank", "Assessment"),
    ("workbook_exercises", "Workbook Exercises", "Assessment"),
    ("social_media_hooks", "Social Media Hooks", "Media"),
    ("podcast_outline", "Podcast Outline", "Media"),
    ("youtube_script", "YouTube Script", "Media"),
    ("presentation_outline", "Presentation Outline", "Media"),
    ("teacher_notes", "Teacher Notes", "Education"),
    ("image_concepts", "Image Concepts", "Visual"),
    ("animation_concepts", "Animation Concepts", "Visual"),
    ("character_opportunities", "Character Opportunities", "Visual"),
    ("related_records", "Related Knowledge Records", "Relationships"),
    ("cross_references", "Cross References", "Relationships"),
    ("future_research", "Future Research Opportunities", "Relationships"),
]
SECTION_TITLES = {k: t for k, t, _ in SECTION_DEFS}
SECTION_KEYS = [k for k, _, _ in SECTION_DEFS]

STATUS_VALUES = ["Pending", "Draft", "Under Review", "Verified", "Approved", "Superseded", "Archived"]
SOURCE_VALUES = ["Founder", "AI", "Deterministic", "Imported", "Human Expert"]
VERIFICATION_VALUES = ["Unverified", "Partially Verified", "Verified", "Treasure Standard Approved"]

# Sections considered "complete" (usable for manufacturing).
COMPLETE_STATUSES = {"Draft", "Under Review", "Verified", "Approved"}

# --------------------------------------------------------------------------- Manufacturing Dependency Map
# product-family keyword -> required section keys. Matched against the lowercased product type.
DEPENDENCY_MAP = {
    "consumer": ["executive_summary", "qru_translation", "practical_applications", "memory_sentences"],
    "teacher": ["executive_summary", "deep_explanation", "teacher_translation", "question_library", "quiz_bank", "scientific_references", "teacher_notes"],
    "child": ["child_translation", "story_version", "image_concepts", "character_opportunities", "memory_sentences"],
    "kids": ["child_translation", "story_version", "image_concepts", "character_opportunities", "memory_sentences"],
    "story": ["story_version", "image_concepts", "character_opportunities"],
    "teen": ["teen_translation", "practical_applications", "question_library"],
    "video": ["youtube_script", "image_concepts"],
    "youtube": ["youtube_script", "image_concepts"],
    "short": ["youtube_script", "social_media_hooks"],
    "podcast": ["podcast_outline", "deep_explanation"],
    "presentation": ["presentation_outline", "deep_explanation"],
    "slide": ["presentation_outline"],
    "powerpoint": ["presentation_outline"],
    "workbook": ["workbook_exercises", "question_library", "vocabulary_decoder"],
    "quiz": ["quiz_bank", "question_library"],
    "flash": ["question_library", "memory_sentences", "vocabulary_decoder"],
    "poster": ["memory_sentences"],
    "social": ["social_media_hooks", "memory_sentences"],
    "lesson": ["executive_summary", "deep_explanation", "question_library"],
    "guide": ["executive_summary", "deep_explanation", "practical_applications"],
    "ebook": ["executive_summary", "deep_explanation", "examples"],
    "book": ["executive_summary", "deep_explanation", "examples"],
    "dictionary": ["vocabulary_decoder"],
    "tutor": ["deep_explanation", "question_library", "common_misunderstandings"],
}
DEFAULT_REQUIRED = ["executive_summary", "deep_explanation"]

# Legacy field -> KR 2.0 section (non-destructive migration mapping).
LEGACY_MAP = {
    "simple_answer": "executive_summary",
    "verified_truth": "deep_explanation",
    "deep_explanation": "deep_explanation",
    "qru_translation": "qru_translation",
    "why_it_matters": "practical_applications",
    "real_world_example": "examples",
    "everyday_analogy": "analogy_library",
    "memory_sentence": "memory_sentences",
    "deep_roots": "historical_context",
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def blank_section(key):
    return {
        "section_id": key, "title": SECTION_TITLES.get(key, key), "content": "",
        "status": "Pending", "source": None, "verification_status": "Unverified",
        "confidence_score": 0, "author": None, "reviewer": None,
        "created_at": _now(), "updated_at": _now(), "version": 0,
        "evidence_links": [], "dependencies": [], "manufacturing_ready": False,
    }


def required_sections_for(product_type):
    pt = (product_type or "").lower()
    for kw, sections in DEPENDENCY_MAP.items():
        if kw in pt:
            return sections
    return DEFAULT_REQUIRED


def products_depending_on(section_key):
    """Reverse dependency lookup — which product families require this section."""
    return sorted({kw for kw, secs in DEPENDENCY_MAP.items() if section_key in secs})


def migrate_kr(kr):
    """Non-destructive: builds/refreshes sections_v2 without overwriting existing edits.
    Legacy verified content is mapped into its section; unmapped legacy is preserved.
    Returns the update dict to $set (does not touch legacy top-level fields)."""
    existing = kr.get("sections_v2") or {}
    kr_verified = kr.get("verification_status") == "Verified"
    sections = {}
    for key in SECTION_KEYS:
        if key in existing and existing[key].get("version", 0) > 0:
            sections[key] = existing[key]  # preserve prior edits/AI fills
        else:
            sections[key] = blank_section(key)

    # Map legacy fields into their sections (only if the section is still empty/pending).
    for legacy_field, section_key in LEGACY_MAP.items():
        val = kr.get(legacy_field)
        if val and isinstance(val, str) and sections[section_key]["version"] == 0:
            sec = sections[section_key]
            sec["content"] = val
            sec["source"] = "Imported"
            sec["status"] = "Verified" if kr_verified else "Draft"
            sec["verification_status"] = "Verified" if kr_verified else "Partially Verified"
            sec["confidence_score"] = 90 if kr_verified else 60
            sec["author"] = "Legacy Migration"
            sec["version"] = 1
            sec["manufacturing_ready"] = bool(val) and kr_verified
            sec["updated_at"] = _now()

    # References → scientific_references evidence_links.
    refs = kr.get("references") or kr.get("sources") or []
    if refs and sections["scientific_references"]["version"] == 0:
        sec = sections["scientific_references"]
        sec["content"] = "\n".join(str(r) for r in refs) if isinstance(refs, list) else str(refs)
        sec["evidence_links"] = refs if isinstance(refs, list) else [str(refs)]
        sec["source"] = "Imported"
        sec["status"] = "Verified" if kr_verified else "Draft"
        sec["verification_status"] = "Verified" if kr_verified else "Partially Verified"
        sec["confidence_score"] = 85 if kr_verified else 55
        sec["version"] = 1
        sec["manufacturing_ready"] = kr_verified
        sec["updated_at"] = _now()

    # Preserve any legacy content not mapped, for later review.
    mapped = set(LEGACY_MAP.keys()) | {"references", "sources"}
    unmapped = kr.get("unmapped_legacy") or {}
    for f in ("the_question", "consumer_translation", "notes", "context"):
        if kr.get(f) and f not in mapped and f not in unmapped:
            unmapped[f] = kr[f]

    return {
        "schema_version": SCHEMA_VERSION,
        "sections_v2": sections,
        "unmapped_legacy": unmapped,
        "kr2_migrated_at": kr.get("kr2_migrated_at") or _now(),
    }


def completeness(kr):
    """Section completeness summary for a KR."""
    sections = kr.get("sections_v2") or {}
    total = len(SECTION_KEYS)
    complete = sum(1 for k in SECTION_KEYS if sections.get(k, {}).get("status") in COMPLETE_STATUSES
                   and sections.get(k, {}).get("content"))
    verified = sum(1 for k in SECTION_KEYS if sections.get(k, {}).get("status") in ("Verified", "Approved"))
    return {"total": total, "complete": complete, "verified": verified,
            "percent": round(complete / total * 100) if total else 0}


def manufacturing_readiness(kr, product_type):
    """Which required sections are ready vs missing for a given product type."""
    required = required_sections_for(product_type)
    sections = kr.get("sections_v2") or {}
    ready, missing = [], []
    for key in required:
        sec = sections.get(key) or {}
        ok = bool(sec.get("content")) and sec.get("status") in COMPLETE_STATUSES
        (ready if ok else missing).append(SECTION_TITLES.get(key, key))
    return {
        "product_type": product_type, "required": [SECTION_TITLES.get(k, k) for k in required],
        "ready_sections": ready, "missing_sections": missing,
        "manufacturing_allowed": len(missing) == 0,
    }
