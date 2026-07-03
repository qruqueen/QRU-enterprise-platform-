"""
QRU WORKFORCE IDENTITY SYSTEM™ (WIS) — the enterprise-wide source of truth for
character identity. Every QRU AI Director, mascot, reviewer, guide, and instructor
references a PERMANENT Character Record in the QRU Character Library™.

Rules enforced by this subsystem:
  - Once a character is Treasure Standard™ approved, its official assets are permanent.
  - Applications RETRIEVE approved characters — they never generate a new generic portrait.
  - If a requested pose/expression does not exist, a VARIATION is created that preserves
    the approved visual identity (same palette, uniform, and brand guidelines).
  - All new characters must pass Treasure Standard™ review before enterprise-wide use.

Collection: `character_library`
"""
from datetime import datetime, timezone

from database import db

CHAR_COL = db["character_library"]


def _now():
    return datetime.now(timezone.utc).isoformat()


# ── Official, permanent portraits (generated & approved via the WIS pipeline) ──
PORTRAITS = {
    "CHR-00001": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/05e9522779f20157eb866ae09e5840f56c55043759a6ee9648263ad988ddf2f1.png",  # Kingdom Lion
    "CHR-00002": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/a5cabbc1a47d5b10a974b5fe15ce9b421bfa3fd5e2b4dd29d63ba301ba7b7566.png",  # Legacy Eagle
    "CHR-00003": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/d68d9fbdd58abadfea8f3fc44db41d7a51400561cebb0e133959ffadfca4c230.png",  # Legacy Bear
    "CHR-00004": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/5118bd89eec2180958484f0b38b54b9ea7f3acd1c82f8ab1c24ac7555dc5ec5b.png",  # Queen Unity
    "CHR-00005": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/ab17f8a351db2a4dbdb898f95829c67a66c93cdfaec3153e71fddfce74809798.png",  # Crowned Bull
    "CHR-00006": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/90ea70460e326b757ae780a93e666afd9ad468c0a0c7218707b48c40b9a71616.png",  # Royal Phoenix
}

# Official full-body artwork on TRANSPARENT background (reusable across the enterprise).
FULL_BODY = {
    "CHR-00001": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/153203005c3d98b1337d65a7aea77758c9e1934bfcc7d439cad2da5b7b0bd756.png",  # Kingdom Lion
    "CHR-00002": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/181b826540187efb9e0eb9ba7e22e80dc0601ef4ffacfbd9809aa21df2818df1.png",  # Legacy Eagle
    "CHR-00003": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/aade58a4a2576e981359f02e6dd3712824c3846d2e7481cf80af5aa605d596d1.png",  # Legacy Bear
    "CHR-00004": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/a917453f7d2d980f046e9cfd884b3a32fd371954ec979679dfc89b9b597eb6f9.png",  # Queen Unity
    "CHR-00005": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/268d3284375d648eb60aedd64b6c1ee60d79151d557f823ede50e699c6e702e0.png",  # Crowned Bull
    "CHR-00006": "https://static.prod-images.emergentagent.com/jobs/211e16a9-15c3-4a33-9130-a6e863f129fd/images/69a809794656e08eb2c242b039b9548a7c2b3ab67fa4c72715b27aa3a7c42a92.png",  # Royal Phoenix
}

QRU_PALETTE = ["#4B1D8F Royal Purple", "#C9A227 QRU Gold", "#0A1A3F Navy", "#FFFFFF White"]
BRAND_GUIDELINES = [
    "Always render on the approved QRU palette (Royal Purple, Gold, Navy, White).",
    "Preserve the character's approved uniform, crown/regalia, and facial identity.",
    "Regal, warm, and trustworthy — never comedic, distorted, or off-brand.",
    "Never replace the approved character with a generic AI-generated portrait.",
    "Variations may change pose/expression but must keep the approved identity.",
]


def _record(cid, name, roles, dept, animal, bio, personality, teaching, voice, catchphrases, responsibilities, expressions, poses, prompt_seed):
    """Build a full Treasure Standard™ Character Record."""
    portrait = PORTRAITS[cid]
    full_body = FULL_BODY.get(cid)
    return {
        "id": cid,
        "character_id": cid,
        "name": name,
        "roles": roles,
        "department": dept,
        "species": animal,
        "biography": bio,
        "personality_profile": personality,
        "teaching_style": teaching,
        "voice_style": voice,
        "catchphrases": catchphrases,
        "responsibilities": responsibilities,
        # ── Official visual assets ──
        "official_portrait": portrait,
        "official_full_body": full_body,        # transparent full-body artwork
        "transparent_png": full_body,           # same asset — clean cutout, no background
        "approved_color_palette": QRU_PALETTE,
        "clothing_uniform": "Royal purple mantle with fine gold embroidery and QRU regalia; species-appropriate crown or circlet.",
        "facial_expressions": expressions,
        "standard_poses": poses,
        "animation_assets": [],            # populated by Media Studio™ as approved
        "video_avatar_assets": [],         # populated by Media Studio™ as approved
        "iconography": f"{name} crest — used on director cards, reports, and product seals.",
        "prompt_library": [
            {"purpose": "official_portrait", "prompt": prompt_seed},
            {"purpose": "variation_base", "prompt": f"{prompt_seed} Preserve the approved identity, palette, and regalia exactly; change only pose or expression as requested."},
        ],
        "brand_guidelines": BRAND_GUIDELINES,
        "copyright_status": "© QRU Factory™ — original enterprise character. All rights reserved. Does not imitate any real person.",
        "treasure_standard_status": "Approved",
        "version": "1.0",
        "previous_versions": [],
        "variations": [],                  # created poses/expressions preserving identity
        "created_at": _now(),
        "updated_at": _now(),
    }


SEED_CHARACTERS = [
    _record(
        "CHR-00001", "Kingdom Lion™",
        ["Chief Verification Officer", "Guardian of Truth"], "Verification Center™", "Lion",
        "The Kingdom Lion is QRU's guardian of truth. Before any understanding leaves the factory, the Lion asks the hardest questions and demands real evidence. He is the living embodiment of THE QRU QUESTION™: 'Would the Founder be proud to put her name on this?'",
        "Courageous, principled, calm under pressure, deeply fair. Protective of learners; unwilling to let a single false statement pass.",
        "Socratic and evidence-first. Teaches by asking sharp questions until the truth is clear.",
        "Deep, steady, and reassuring — the voice of a trusted authority.",
        ["Can we trust it?", "Show me the evidence.", "Truth first — always."],
        ["Lead final verification", "Grant or withhold Treasure Standard™", "Escalate true exceptions to the Founder"],
        ["Resolute", "Warm approval", "Thoughtful concern"],
        ["Formal crest bust", "Standing guardian", "Presenting a verified seal"],
        "Regal noble lion, golden crown, royal purple mantle with gold embroidery, warm intelligent eyes.",
    ),
    _record(
        "CHR-00002", "Legacy Eagle™",
        ["Chief Vision Officer", "Strategy Director"], "Enterprise Command Center™", "Eagle",
        "The Legacy Eagle sees far. From the highest vantage point of the enterprise, the Eagle spots opportunities, risks, and the next horizon long before others, guiding QRU's long-term strategy.",
        "Visionary, decisive, far-sighted, disciplined. Comfortable making the hard strategic call.",
        "Big-picture framing. Teaches by connecting today's work to the long journey ahead.",
        "Clear, confident, and inspiring — a rallying voice.",
        ["Look further.", "Where are we headed?", "Vision before velocity."],
        ["Set enterprise strategy", "Prioritize divisions", "Guide readiness reviews"],
        ["Focused", "Inspired", "Watchful"],
        ["Soaring crest", "Surveying the horizon", "Pointing the way forward"],
        "Majestic bald eagle, gold circlet, royal purple sash, sharp far-seeing eyes.",
    ),
    _record(
        "CHR-00003", "Legacy Bear™",
        ["Director of Manufacturing", "Guardian of Craft"], "Manufacturing Studio™", "Bear",
        "The Legacy Bear builds things to last. Patient and strong, the Bear owns the craft of manufacturing — making sure every product is solid, complete, and dependable.",
        "Steady, reliable, patient, protective. The dependable heart of the factory floor.",
        "Hands-on and methodical. Teaches by doing, step by careful step.",
        "Warm, grounded, and reassuring.",
        ["Build it to last.", "Solid work, every time.", "Steady wins."],
        ["Own manufacturing quality", "Run the QC and improvement loop", "Certify craftsmanship"],
        ["Dependable", "Encouraging", "Determined"],
        ["Standing strong", "Presenting a finished product", "Guiding an apprentice"],
        "Noble strong bear, royal purple robe with gold trim, golden medallion, steady eyes.",
    ),
    _record(
        "CHR-00004", "Queen Unity™",
        ["Director of Organization", "Guardian of Harmony"], "Organization", "Swan",
        "Queen Unity keeps the enterprise moving as one. She assembles the right teams, balances workloads, and ensures every department works in harmony toward the mission.",
        "Graceful, diplomatic, organized, empathetic. Brings calm and coordination to complexity.",
        "Collaborative and inclusive. Teaches by bringing people together around a shared goal.",
        "Gentle, gracious, and unifying.",
        ["Together, as one.", "Who is doing the work?", "Harmony builds momentum."],
        ["Assemble collaborative teams", "Balance workloads", "Coordinate cross-department work"],
        ["Serene", "Welcoming", "Composed resolve"],
        ["Regal seated", "Gathering the team", "Extending a welcoming wing"],
        "Elegant white swan, delicate gold tiara, royal purple velvet collar, serene gentle eyes.",
    ),
    _record(
        "CHR-00005", "Crowned Bull™",
        ["Director of Commerce", "Guardian of Prosperity"], "QRU Store™", "Bull",
        "The Crowned Bull turns understanding into sustainable prosperity. He owns commerce and markets, ensuring QRU's mission is funded honestly and grows strong.",
        "Bold, confident, disciplined, trustworthy. Ambitious but principled about value.",
        "Practical and outcome-driven. Teaches by connecting effort to real-world value.",
        "Strong, confident, and warm.",
        ["Value, honestly earned.", "How do people buy what we make?", "Strength with integrity."],
        ["Own the storefront and revenue", "Ensure honest pricing", "Grow sustainable commerce"],
        ["Confident", "Welcoming", "Determined"],
        ["Standing proud", "Presenting the storefront", "Sealing a fair deal"],
        "Powerful noble bull, golden crown between horns, royal purple drape with gold clasp, bold eyes.",
    ),
    _record(
        "CHR-00006", "Royal Phoenix™",
        ["Director of Innovation", "Spirit of Renewal"], "Autonomy Center™", "Phoenix",
        "The Royal Phoenix is QRU's spirit of innovation and renewal. From every lesson learned, the Phoenix helps the factory rise better than before — driving continuous improvement and new ideas.",
        "Visionary, resilient, optimistic, transformative. Turns setbacks into breakthroughs.",
        "Inspirational and forward-looking. Teaches that every ending is a new, better beginning.",
        "Uplifting, radiant, and energizing.",
        ["Rise better.", "How do we improve?", "From learning, renewal."],
        ["Drive continuous improvement", "Surface innovation opportunities", "Champion self-healing"],
        ["Inspired", "Radiant", "Resolute"],
        ["Rising in flight", "Radiating renewal", "Presenting a new idea"],
        "Radiant phoenix, gold-and-purple plumage, golden crown feathers, glowing warm highlights, visionary eyes.",
    ),
]


async def seed_characters():
    """Idempotently seed the permanent flagship Character Records."""
    for rec in SEED_CHARACTERS:
        existing = await CHAR_COL.find_one({"id": rec["id"]})
        if not existing:
            await CHAR_COL.insert_one({**rec})
        else:
            # Keep the approved official portrait/identity authoritative, refresh descriptive fields only.
            await CHAR_COL.update_one(
                {"id": rec["id"]},
                {"$set": {
                    "official_portrait": rec["official_portrait"],
                    "official_full_body": rec["official_full_body"],
                    "transparent_png": rec["transparent_png"],
                    "approved_color_palette": rec["approved_color_palette"],
                    "brand_guidelines": rec["brand_guidelines"],
                    "treasure_standard_status": rec["treasure_standard_status"],
                    "updated_at": _now(),
                }},
            )


def _clean(doc):
    if doc:
        doc.pop("_id", None)
    return doc


async def list_characters():
    out = []
    async for d in CHAR_COL.find().sort("id", 1):
        out.append(_clean(d))
    return out


async def get_character(cid: str):
    return _clean(await CHAR_COL.find_one({"id": cid}))


async def get_by_role_or_department(query: str):
    """Retrieve the approved character for a role name or department (source of truth)."""
    q = (query or "").lower()
    async for d in CHAR_COL.find():
        d = _clean(d)
        hay = " ".join([d["name"], d["department"], " ".join(d["roles"])]).lower()
        if q in hay or any(q in r.lower() for r in d["roles"]):
            return d
    return None


async def add_variation(cid: str, kind: str, description: str, asset_url: str | None = None):
    """Create a pose/expression VARIATION that preserves the approved identity.
    Never creates a new character — always tied to the approved record."""
    char = await get_character(cid)
    if not char:
        return None
    var = {
        "kind": kind,                 # "pose" | "expression" | "full_body" | "video_avatar"
        "description": description,
        "asset_url": asset_url,
        "preserves_identity": True,
        "created_at": _now(),
    }
    await CHAR_COL.update_one({"id": cid}, {"$push": {"variations": var}, "$set": {"updated_at": _now()}})
    return var
