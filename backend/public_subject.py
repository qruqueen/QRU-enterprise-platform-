"""QRU Public Subject Reconciliation™ — storefront-facing subject classification.

Two upstream systems already write into book_records.genre with incompatible meanings:
  - decoder_engine.DOMAINS (14 real subject domains, set once at book creation from the
    source Decoder Record — see book_manufacturing.create_book_from_decoder()).
  - imprint_rules.canonical_genre() (5 pricing/imprint buckets: Literary Fiction,
    Educational, Science, Legal, Finance — written by the Imprint Canonicalization
    production operation when it runs against a book).

Because both writers target the same field, a stored `genre` value alone doesn't reliably
tell you which vocabulary produced it. That collision is existing Factory technical debt
and is intentionally NOT fixed here — no historical data is rewritten, no migration is run
against genre itself, and neither upstream writer is changed. This module only reconciles
the ambiguity at the storefront read boundary, deterministically, using the two vocabularies
that already exist. It introduces no third authoritative taxonomy — DOMAINS remains
canonical; this is a read-time normalization function over it.

DOMAINS is intentionally duplicated here (not imported from decoder_engine) to keep this
module free of decoder_engine's heavier import chain (ai_service, product_governance,
media_division, database) — it's a read-only public API concern, not a manufacturing one.
Keep this list in sync with decoder_engine.DOMAINS if that list ever changes.
"""

DOMAINS = [
    "AI Literacy", "Finance", "Trading", "Health", "Human Capability", "Emotions",
    "Life Skills", "Science", "Technology", "Leadership", "Faith and Philosophy",
    "Children", "Little Legacy Learners™", "General",
]

GENERAL = "General"

# imprint_rules.canonical_genre() bucket -> nearest existing DOMAINS value. Only mapped
# where the match is genuinely confident; everything else falls through to General rather
# than guess a relationship that isn't really there.
_BUCKET_TO_DOMAIN = {
    "Science": "Science",
    "Finance": "Finance",
    # "Literary Fiction", "Educational", "Legal" have no confident 1:1 DOMAINS equivalent.
}


def reconcile_subject(record: dict) -> str:
    """Deterministic storefront subject for a book/product record. Pure function — reads
    the record's existing `genre` field, never writes anything.

    Resolution order (Founder-approved):
      1. genre is already a recognized DOMAINS value -> use it as-is.
      2. genre is a recognized canonical_genre() bucket -> map to the nearest DOMAINS value.
      3. unknown / empty / anything else -> General.
    """
    raw = (record.get("genre") or "").strip()
    if raw in DOMAINS:
        return raw
    if raw in _BUCKET_TO_DOMAIN:
        return _BUCKET_TO_DOMAIN[raw]
    return GENERAL
