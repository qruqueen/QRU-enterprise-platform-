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
