"""QRU Distribution Architecture™ — Phase 0 foundation.

Enterprise principles (Founder-approved 2026-07-29):

  1. ONE GOVERNED CATALOG — QRU Store™ is the single source of truth. The Factory
     publishes to the catalog; the catalog distributes to customer experiences.

  2. AUTOMATIC DISTRIBUTION — every product type has recommended default destinations.
     At publish time the Factory auto-selects them; the Founder may override. Publishing
     stays fast while remaining flexible.

  3. EXPERIENCES ARE PLUG-INS — a customer experience (Books, Learn, Resources, Media,
     Bundles, and any future one like QRU Academy™ / QRU Kids™) is REGISTERED, not
     hard-wired. Adding an experience never changes the Factory: it declares itself here
     and immediately begins consuming the catalog. QRU Learn™ is preserved exactly as-is
     and is simply described in this model as the experience that consumes `learn`.
"""
from datetime import datetime, timezone
from database import db

EXPERIENCES_COLL = "distribution_experiences"


def _now():
    return datetime.now(timezone.utc).isoformat()


# ── Default experiences (seed). New experiences are REGISTERED, never coded in. ──
DEFAULT_EXPERIENCES = [
    {"id": "books", "name": "Books", "icon": "book", "audience": "General readers",
     "description": "The public bookstore — full-length titles by imprint (QRU Press™, E.Q. Rothwell™).",
     "public": True, "order": 1},
    {"id": "learn", "name": "Learn", "icon": "graduation-cap", "audience": "Learners, classrooms",
     "description": "QRU Learn™ — courses, guides and lessons. Preserved exactly as it functions today.",
     "public": True, "order": 2, "protected": True},
    {"id": "resources", "name": "Resources", "icon": "toolbox", "audience": "Educators, self-learners",
     "description": "Printables, workbooks, posters, flash cards and quick references.",
     "public": True, "order": 3},
    {"id": "media", "name": "Media", "icon": "video", "audience": "Viewers & listeners",
     "description": "Motion stories, video and audio (podcasts, narration).",
     "public": True, "order": 4},
    {"id": "bundles", "name": "Bundles", "icon": "gift", "audience": "Value seekers, institutions",
     "description": "First-class bundle products — any mix of books, guides, media and downloads.",
     "public": True, "order": 5},
]


# ── Automatic Distribution map: product type → recommended default destinations ──
# Founder-approved defaults. Anything not listed falls back to DEFAULT_FALLBACK.
DEFAULT_DESTINATIONS = {
    "Book":               ["books"],
    "Course":             ["learn"],
    "Workbook":           ["learn", "resources"],
    "Teacher Guide":      ["learn"],
    "Caregiver Guide":    ["learn"],
    "Student Guide":      ["learn"],
    "Family Guide":       ["learn"],
    "Lesson Plan":        ["learn"],
    "Interactive Lesson": ["learn"],
    "AI Tutor":           ["learn"],
    "Quiz":               ["learn"],
    "Poster":             ["resources"],
    "Infographic":        ["resources"],
    "Printable PDF":      ["resources"],
    "Presentation":       ["resources"],
    "Flash Cards":        ["resources", "learn"],
    "Quick Card":         ["resources"],
    "Quick Guide":        ["resources"],
    "Cheat Sheet":        ["resources"],
    "Certificate":        ["learn"],
    "Motion Story":       ["books", "media"],
    "Podcast":            ["media"],
    "Podcast Script":     ["media"],
    "Video":              ["media"],
    "Video Script":       ["media"],
    "Short-form Content": ["media"],
    "Bundle":             ["bundles"],
}
DEFAULT_FALLBACK = ["resources"]


async def seed_experiences():
    """Idempotent. Founder edits (founder_locked) preserved; descriptive fields refreshed."""
    for e in DEFAULT_EXPERIENCES:
        setter = {k: v for k, v in e.items()}
        setter["updated_at"] = _now()
        await db[EXPERIENCES_COLL].update_one(
            {"id": e["id"]},
            {"$set": setter,
             "$setOnInsert": {"registered_at": _now(), "founder_locked": False, "builtin": True}},
            upsert=True,
        )


async def list_experiences():
    docs = await db[EXPERIENCES_COLL].find({}, {"_id": 0}).sort("order", 1).to_list(200)
    return docs


async def register_experience(exp_id, name, description="", icon="boxes",
                              audience="", public=True, actor="Founder"):
    """PLUG-IN registration — add a new customer experience WITHOUT touching the Factory."""
    exp_id = (exp_id or "").strip().lower().replace(" ", "-")
    if not exp_id or not name:
        return {"error": "An experience id and name are required."}
    existing = await db[EXPERIENCES_COLL].find_one({"id": exp_id})
    if existing:
        return {"error": f"Experience '{exp_id}' already exists."}
    n = await db[EXPERIENCES_COLL].count_documents({})
    doc = {"id": exp_id, "name": name, "description": description, "icon": icon,
           "audience": audience, "public": bool(public), "order": n + 1,
           "builtin": False, "founder_locked": True, "registered_by": actor,
           "registered_at": _now(), "updated_at": _now()}
    await db[EXPERIENCES_COLL].insert_one(dict(doc))
    doc.pop("_id", None)
    return {"ok": True, "experience": doc}


def recommend_destinations(product_type: str):
    """The Factory's automatic recommendation for where a product type should go."""
    return list(DEFAULT_DESTINATIONS.get(product_type or "", DEFAULT_FALLBACK))


def resolve_destinations(product: dict):
    """A product's ACTUAL destinations: an explicit Founder override wins; else the
    recommended defaults for its type. Never empty."""
    dist = (product.get("distribution") or {})
    override = dist.get("experiences")
    if override:
        return list(override)
    return recommend_destinations(product.get("product_type"))


async def destinations_map():
    """The full auto-distribution table for the Founder UI."""
    exps = {e["id"]: e for e in await list_experiences()}
    rows = []
    for ptype, dests in DEFAULT_DESTINATIONS.items():
        rows.append({"product_type": ptype,
                     "destinations": [{"id": d, "name": exps.get(d, {}).get("name", d)} for d in dests]})
    return {"map": rows, "fallback": DEFAULT_FALLBACK}
