"""Little Legacy Learners™ Animation Manufacturing Engine™ — Phase 1 Foundation.

A governed capability inside the QRU Factory™ (inherited by the Product Manufacturing Engine). This phase
establishes the version-controlled data layer, the Universe Bible, the six canonical Character Bibles, the
world map, relationships, continuity ledger, season/episode templates and governance gates. Everything is
seeded as "Draft Pending Founder Approval". Canon is protected: locked character traits cannot change
without explicit Founder approval. Knowledge-first: an episode cannot be built from an unverified topic.
Nothing here falsely certifies legal/trademark clearance.
"""
from database import db
from models import gen_id, now_iso
import kr_inheritance as kri

DRAFT = "Draft Pending Founder Approval"
QRU_COLORS = {"royal_purple": "#35106A", "qru_gold": "#F5B21A", "deep_navy": "#1F1840", "white": "#FFFFFF"}

CHARACTERS = [
    {"key": "nova-sparkle", "name": "Nova Sparkle™", "role": "The Little Star With a Big Heart",
     "strengths": ["leadership", "curiosity", "confidence"], "affirmation": "I can shine, and so can you!",
     "palette": ["#8A5AD6", "#F5B21A"], "identity": "Star-themed child leader with a crown accent.",
     "signature_prop": "“Big Dreams” book", "function": "Begins adventures, asks big questions, encourages belief in ideas."},
    {"key": "sunny-bee", "name": "Sunny Bee™", "role": "The Busy Bee Who Loves to Share",
     "strengths": ["sharing", "kindness", "generosity"], "affirmation": "Sharing makes the world sweet!",
     "palette": ["#F5C518", "#E79A2B"], "identity": "Joyful bee with a heart symbol; warm yellow palette.",
     "signature_prop": "Honey heart", "function": "Models kindness, cooperation and thoughtful service."},
    {"key": "tilly-turtle", "name": "Tilly Turtle™", "role": "The Patient Turtle Who Takes Her Time",
     "strengths": ["patience", "perseverance", "self-control"], "affirmation": "Good things take time!",
     "palette": ["#4FAE5A", "#8A5AD6"], "identity": "Calm turtle with glasses; green and purple palette.",
     "signature_prop": "Practice journal", "function": "Helps the team slow down, practice and persist."},
    {"key": "bella-butterfly", "name": "Bella Butterfly™", "role": "The Beautiful Butterfly Who Believes in Herself",
     "strengths": ["confidence", "self-love", "encouragement"], "affirmation": "Be you, you’re beautiful!",
     "palette": ["#E86FA6", "#8A5AD6"], "identity": "Expressive butterfly with a heart motif; pink and purple.",
     "signature_prop": "Mirror of courage", "function": "Encourages self-worth, expression and creativity."},
    {"key": "eli-elephant", "name": "Eli Elephant™", "role": "The Smart Elephant Who Loves to Learn",
     "strengths": ["learning", "memory", "problem solving"], "affirmation": "I’m smart, I keep learning!",
     "palette": ["#3B7FD4", "#8A5AD6", "#F5B21A", "#FFFFFF"], "identity": "Elephant with a learning cap and book.",
     "signature_prop": "Memory book", "function": "Remembers, organizes information and tests ideas."},
    {"key": "rio-rainbow", "name": "Rio Rainbow™", "role": "The Colorful Friend Who Brings Everyone Together",
     "strengths": ["diversity", "inclusion", "community"], "affirmation": "Together we make magic!",
     "palette": ["#E4572E", "#F5B21A", "#4FAE5A", "#3B7FD4", "#8A5AD6"], "identity": "Human child with a rainbow motif.",
     "signature_prop": "Friendship map", "function": "Includes everyone, recognizes strengths, builds community."},
]

LOCATIONS = ["Little Legacy Village™", "QRU Learning Academy™", "Learning Tree™", "Wonder Library™",
             "Treasure Trail™", "Curiosity Forest™", "Friendship Park™", "Idea Workshop™", "Memory Mountain™",
             "Question Castle™", "Verification Valley™", "Dream Playground™", "Kindness Café™", "Music Meadow™",
             "Adventure River™", "Rainbow Station™"]

VALUES = ["curiosity", "confidence", "kindness", "sharing", "patience", "perseverance", "self-control",
          "self-love", "encouragement", "learning", "memory", "problem solving", "inclusion", "diversity",
          "community", "teamwork", "creativity", "honesty", "evidence", "verification", "responsibility",
          "respect", "courage", "financial confidence", "healthy decision-making", "lifelong learning"]

AGE_BANDS = [
    {"band": "Early Learners", "ages": "3–5"}, {"band": "Growing Learners", "ages": "6–8"},
    {"band": "Emerging Thinkers", "ages": "9–11"}, {"band": "Future Leaders", "ages": "12+"},
]

# Canon-locked fields on a character — cannot change without explicit Founder approval.
LOCKED_FIELDS = ("name", "role", "strengths", "affirmation", "identity", "function")

CHECKLISTS = {
    "child_safety": ["age appropriateness", "emotional safety", "imitation risk", "frightening imagery",
                     "bullying/shame/exclusion", "manipulative language", "privacy & child data", "commercial pressure"],
    "accessibility": ["accurate captions", "readable caption timing", "sufficient contrast", "speech clarity",
                      "non-color-only cues", "transcript", "no unsafe flashing", "age-appropriate pacing"],
    "rights_provenance": ["creator", "tool used", "license", "commercial-use permission", "attribution",
                          "territory", "expiration", "checksum", "legal-review status", "Founder approval"],
    "treasure_standard": ["Understanding: lesson clear & explainable", "Craftsmanship: consistent & complete",
                          "Legacy: strengthens human capability & aligns with QRU values"],
    "youtube_publish": ["final title", "child-safe description", "learning objectives", "caption file",
                        "thumbnail", "made-for-kids review", "ad/data-collection review", "rights confirmation",
                        "final human publishing approval"],
    "verification_lion": ["source provenance", "source quality", "independent cross-check", "applicability",
                          "uncertainty disclosed", "human review for high-risk", "audit record"],
}

STATUSES = ["Idea", "Intake", "Knowledge Required", "Draft", "In Review", "Changes Required", "Verified",
            "Approved", "Production Ready", "In Production", "Quality Review", "Founder Review",
            "Publish Ready", "Published", "Paused", "Retired", "Archived"]


async def seed(force=False):
    existing = await db.ll_franchise.find_one({"key": "little-legacy-learners"})
    if existing and not force:
        return {"seeded": False, "reason": "Already seeded."}

    await db.ll_franchise.update_one({"key": "little-legacy-learners"}, {"$set": {
        "id": existing["id"] if existing else gen_id(), "key": "little-legacy-learners",
        "name": "Little Legacy Learners™", "enterprise": "Queen Rothswell Universe™ — QRU™",
        "philosophy": "Quest for Real Understanding™",
        "promise": "Little Lessons Today. Big Impact Tomorrow.™",
        "legacy_statement": "Knowledge Changes Everything. Legacy Changes Generations.™",
        "purpose": "Build character, confidence, understanding and responsible decision-making through entertaining educational stories.",
        "colors": QRU_COLORS, "values": VALUES, "age_bands": AGE_BANDS,
        "status": DRAFT, "version": "0.1", "updated_at": now_iso(),
    }}, upsert=True)

    await db.ll_universe_bible.update_one({"key": "universe-bible"}, {"$set": {
        "id": gen_id(), "key": "universe-bible", "version": "0.1", "status": DRAFT,
        "sections": {
            "franchise_foundation": {"mission": "Teach people to think, not what to think.",
                                     "parent_promise": "Safe, warm, honest learning.",
                                     "educator_promise": "Standards-aligned, classroom-ready.",
                                     "learner_promise": "Learning feels like an adventure."},
            "world_origin": "The Little Legacy Learners became friends at Little Legacy Village™, where every question opens an adventure and every mistake becomes a lesson worth treasuring.",
            "rules_of_the_world": ["Educational 'magic' always has an understandable reason.",
                                   "Imagination is clearly distinct from factual reality.",
                                   "Problems are solved by choices, questions and teamwork — not coincidence.",
                                   "Adults/mentors guide but children lead their own understanding.",
                                   "AI is shown as a helpful tool, never an unquestionable authority."],
            "tone": ["joyful", "warm", "energetic", "playful", "reassuring", "imaginative", "family-friendly"],
            "prohibited": ["humiliation", "cruelty", "appearance-based insults", "stereotypes", "dangerous imitation",
                           "exclusion", "fear-based manipulation", "adult humor"],
            "locations": LOCATIONS,
        },
        "updated_at": now_iso(),
    }}, upsert=True)

    for c in CHARACTERS:
        prev = await db.ll_characters.find_one({"key": c["key"]})
        await db.ll_characters.update_one({"key": c["key"]}, {"$set": {
            "id": prev["id"] if prev else gen_id(), **c, "trademark": "™", "canon_locked": True,
            "status": DRAFT, "version": "0.1", "legal_review_status": "Not started",
            "founder_approved": False, "prohibited_portrayals": ["stereotype", "sidekick-only", "token"],
            "updated_at": now_iso(),
        }}, upsert=True)

    await db.ll_locations.delete_many({})
    for i, name in enumerate(LOCATIONS):
        await db.ll_locations.insert_one({"id": gen_id(), "name": name, "order": i, "status": DRAFT,
                                          "purpose": "Reusable franchise location.", "updated_at": now_iso()})

    await db.ll_seasons.update_one({"key": "season-1"}, {"$set": {
        "id": gen_id(), "key": "season-1", "title": "Season One (Template)", "status": DRAFT, "version": "0.1",
        "central_theme": "Discovering the treasure of understanding.", "episode_count_target": 10,
        "notes": "Draft framework — do not manufacture a full season before the pilot passes validation.",
        "updated_at": now_iso(),
    }}, upsert=True)

    await db.ll_meta.update_one({"key": "checklists"}, {"$set": {"key": "checklists", "checklists": CHECKLISTS,
                                                                 "statuses": STATUSES, "updated_at": now_iso()}}, upsert=True)
    return {"seeded": True}


async def overview():
    fr = await db.ll_franchise.find_one({"key": "little-legacy-learners"}, {"_id": 0})
    chars = await db.ll_characters.count_documents({})
    locs = await db.ll_locations.count_documents({})
    eps = await db.ll_episodes.count_documents({})
    meta = await db.ll_meta.find_one({"key": "checklists"}, {"_id": 0})
    return {"franchise": fr, "counts": {"characters": chars, "locations": locs, "episodes": eps},
            "governance": {"statuses": (meta or {}).get("statuses", STATUSES), "checklists": (meta or {}).get("checklists", CHECKLISTS)},
            "phase": "Phase 1 — Foundation", "note": "All records are Draft Pending Founder Approval. Voice, music, animation render and the pilot episode are later governed phases."}


async def list_characters():
    return [c async for c in db.ll_characters.find({}, {"_id": 0}).sort("key", 1)]


async def get_universe_bible():
    return await db.ll_universe_bible.find_one({"key": "universe-bible"}, {"_id": 0})


async def list_locations():
    return [l async for l in db.ll_locations.find({}, {"_id": 0}).sort("order", 1)]


async def update_character(char_id, changes, founder_approved=False):
    """Canon protection (Acceptance Test 1): locked fields cannot change without explicit Founder approval."""
    c = await db.ll_characters.find_one({"id": char_id})
    if not c:
        return None
    locked_attempts = [k for k in changes if k in LOCKED_FIELDS and changes[k] != c.get(k)]
    if locked_attempts and not founder_approved:
        return {"ok": False, "blocked": True, "locked_fields": locked_attempts,
                "message": f"Canon-protected fields {locked_attempts} require explicit Founder approval and a new governed version. Change blocked (Treasure Standard™)."}
    changes = {k: v for k, v in changes.items() if k not in ("id", "key", "canon_locked")}
    if locked_attempts:
        changes["version"] = f"{c.get('version','0.1')}+founder"
        changes["founder_approved"] = True
    changes["updated_at"] = now_iso()
    await db.ll_characters.update_one({"id": char_id}, {"$set": changes})
    return {"ok": True, "blocked": False, "message": "Character updated.", "versioned": bool(locked_attempts)}


async def create_episode_blueprint(kr_id, title, age_band, featured_character_key, actor="Founder"):
    """Knowledge-first (Acceptance Test 2): an episode cannot be built from an unverified/absent KR."""
    kr = await kri.load_kr(db, kr_id) if kr_id else None
    if not kr:
        return {"ok": False, "status": "Knowledge Required",
                "message": "No verified Knowledge Record supplied. Route this topic through Knowledge Manufacturing first — the Factory never invents facts for children."}
    inh = kri.build_inheritance(kr)
    verified = inh["verified_external"]
    ep = {
        "id": gen_id(), "title": title or f"{inh['term']} Adventure", "season": "season-1",
        "age_band": age_band or "Early Learners", "primary_kr": kr_id, "kr_topic": inh["topic"],
        "featured_character": featured_character_key, "learning_objective": inh["definition_plain"],
        "central_question": (inh["challenge_questions"] or ["What can we discover today?"])[0],
        "treasure_takeaway": inh["memory_sentence"],
        "story_beats": ["Opening", "Curiosity hook", "Problem", "First attempt", "Discovery",
                        "Real-world connection", "Application", "Resolution", "Treasure Takeaway™"],
        "verification_status": "Verified" if verified else "Knowledge Required",
        "status": "Draft" if verified else "Knowledge Required",
        "child_safety_review": "Pending", "accessibility_review": "Pending", "treasure_status": "Pending",
        "founder_approved": False, "created_by": actor, "version": "0.1", "created_at": now_iso(),
        "note": "Draft blueprint. Not Publish Ready — requires knowledge verification, child-safety, accessibility, Treasure Standard and Founder gates."
        if verified else "Source KR is not externally verified — blueprint held at Knowledge Required.",
    }
    await db.ll_episodes.insert_one(dict(ep))
    ep.pop("_id", None)
    return {"ok": True, **ep}


async def list_episodes():
    return [e async for e in db.ll_episodes.find({}, {"_id": 0}).sort("created_at", -1).limit(100)]
