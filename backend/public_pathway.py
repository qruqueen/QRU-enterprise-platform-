"""QRU Public Pathway Classification™ — storefront merchandising classification.

A product may appear in more than one public pathway when its existing metadata provides
deterministic evidence for multiple customer uses (Founder decision, 2026-08). This is a
merchandising view over the product, never a duplication of it: one Factory record, zero or
more pathway labels attached at read time by this module. Nothing here is stored as new
authoritative data unless the caller chooses to cache the result (see public_subject.py's
docstring for the same principle applied to subject).

Explore All is not a stored label. It is the inclusive default surface a product that
resolves to zero pathways (or any product at all) is always discoverable under — never an
exclusive classification, never something a product needs to "qualify" for.

Resolution order for the ambiguous Adult/Adults/beginner adult audience family
(Founder-approved priority): audience -> product type/recipe -> reconciled subject ->
imprint -> Explore All fallback.
"""
import product_recipes as recipes
import public_subject as psub
import imprint_rules as ir

READ = "Read"
LEARNING_RESOURCES = "Learning Resources"
TEACH = "Teach"
FAMILIES = "Families"
PROFESSIONAL = "Professional"
EXPLORE_ALL = "Explore All"

PATHWAYS = [READ, LEARNING_RESOURCES, TEACH, FAMILIES, PROFESSIONAL]

# Exact audience string (lowercased) -> base pathway set. Founder-approved 2026-08.
_AUDIENCE_MAP = {
    "educators, self-learners": {TEACH, LEARNING_RESOURCES},
    "teachers & students": {TEACH, LEARNING_RESOURCES},
    "children": {FAMILIES},
    "youth": {FAMILIES},
    "parents & learners at home": {FAMILIES, LEARNING_RESOURCES},
    "aspiring traders": {PROFESSIONAL},
    "working professionals": {PROFESSIONAL},
    "executives": {PROFESSIONAL},
    "practitioners": {PROFESSIONAL},
    "corporate learners": {PROFESSIONAL},
    "general reader": {READ},
    "general readers": {READ},
    # Real values written by existing manufacturing interfaces (Round 1 normalization,
    # conservative & explainable — no free-text guessing):
    "professional audience": {PROFESSIONAL},
    "entrepreneur": {PROFESSIONAL},
    "teen learner": {LEARNING_RESOURCES},
    "student": {LEARNING_RESOURCES},
}

# Carries no pathway signal on its own -> Explore All, unless the product-type overlay
# below adds something. Distinct from the Adult family, which gets its own resolution path.
_NO_SIGNAL = {"", "general", "general public"}

_ADULT_FAMILY = {"adult", "adults", "beginner adult"}

# product_recipes RECIPES keys that always add Learning Resources as an additional
# pathway, regardless of which audience-driven pathway was assigned (Founder examples:
# "professional workbook" -> Professional + Learning Resources; "teacher educational
# resource" -> Teach + Learning Resources).
_LEARN_TYPES = {
    "Course", "Workbook", "Teacher Guide", "Caregiver Guide", "Student Guide",
    "Family Guide", "Lesson Plan", "Interactive Lesson", "AI Tutor", "Quiz",
    "Printable PDF", "Flash Cards",
}

# Reconciled subjects treated as Professional-leaning for Adult-family resolution.
_PROFESSIONAL_SUBJECTS = {"Finance", "Trading", "Leadership"}


def _resolve_adult_family(record: dict, product_type: str) -> set:
    """audience carries no signal for this family by design -> fall through the
    Founder-approved priority chain: product type/recipe -> reconciled subject -> imprint
    -> Explore All (empty set)."""
    recipe = recipes.get_recipe(product_type) if product_type else None
    if recipe and recipe.get("category") in ("guide", "workbook", "lesson", "quiz"):
        return {LEARNING_RESOURCES}
    subject = psub.reconcile_subject(record)
    if subject in _PROFESSIONAL_SUBJECTS:
        return {PROFESSIONAL}
    imprint = record.get("canonical_imprint") or record.get("imprint")
    if imprint == ir.EQ_ROTHWELL:
        return {READ}
    return set()


def classify(record: dict, product_type: str) -> list:
    """Return the sorted list of pathway labels for a book/product record.

    `product_type` is passed explicitly rather than read from the record, because
    book_records don't carry a product_type field the way db.products does — callers
    reading book_records pass "Book" explicitly; callers reading db.products pass the
    record's actual product_type.
    """
    audience_raw = (record.get("audience") or "").strip().lower()
    pathways = set()

    if audience_raw in _ADULT_FAMILY:
        pathways |= _resolve_adult_family(record, product_type)
    elif audience_raw not in _NO_SIGNAL:
        pathways |= set(_AUDIENCE_MAP.get(audience_raw, set()))

    # Product-type overlay — additive, independent of the audience-driven base set.
    if product_type == "Book":
        pathways.add(READ)
    elif product_type in _LEARN_TYPES:
        pathways.add(LEARNING_RESOURCES)

    return sorted(pathways)
