import uuid
from datetime import datetime, timezone


def gen_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(doc):
    """Strip Mongo _id so documents are JSON serializable."""
    if not doc:
        return doc
    if isinstance(doc, list):
        return [clean(d) for d in doc]
    doc.pop("_id", None)
    return doc


ROLES = [
    "Founder & CEO",
    "Administrator",
    "Executive",
    "Researcher",
    "Reviewer",
    "Designer",
    "Publisher",
    "Teacher",
    "Customer",
    "ReadOnly",
]

# The QRU teaching methodology — every Knowledge Record is built from these sections.
QRU_SECTIONS = [
    "the_question",
    "simple_answer",
    "why_it_matters",
    "real_world_example",
    "qru_translation",
    "everyday_analogy",
    "memory_sentence",
    "practice_application",
    "key_vocabulary",
    "deep_roots",
]

# Modular Understanding Colleges — every division plugs into the same OS.
DIVISIONS = [
    "Health", "Faith", "Trading", "Finance", "AI", "Programming",
    "Parenting", "Business", "Government",
]

# Roles with permanent super-administrator authority over the whole OS.
SUPER_ADMIN_ROLES = ["Founder & CEO", "Administrator"]
