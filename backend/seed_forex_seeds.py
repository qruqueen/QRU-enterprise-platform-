"""Seed the 10 QRU Forex Fundamentals™ Topic Seeds (KR-FX-####). Idempotent — upserts by kr_code.

Founder directive (Knowledge-First Manufacturing):
- These are PLACEHOLDER Topic Seeds only. NO educational content is generated.
- NO definitions are fabricated. NO missing information is inferred.
- They will be promoted to Imported Verified Knowledge Records via the
  Knowledge Record Promotion Pipeline™ (MT-031) once QFC-001_Master_Manuscript_v0.5.docx
  is uploaded.

Each record is created as:
  • record_class            = "Topic Seed"
  • verification_status     = "Topic Seed"
  • approval_status         = "Founder Approved"
  • source_label            = "QRU Legacy Seed"
  • customer_facing         = True
  • readiness               = "Topic Seed — Not Ready for Manufacturing"
  • treasure_standard       = False
  • treasure_standard_status= "Pending"
  • ai_content              = "None"
  • promotion_ready         = True   (Ready for Promotion Pipeline™)
"""
import asyncio

from database import db
from models import gen_id, now_iso, QRU_SECTIONS

OWNER_ID = "1fac7f6d-8dab-4ae8-bf37-a2ff30fe3c8f"
CREATED_BY = "Erica Talbert"

# QRU Forex Fundamentals™ — the previously approved 10 titles, in order.
TITLES = [
    "What Is Forex?",
    "What Is Money?",
    "What Is Currency?",
    "What Is a Currency Pair?",
    "What Is a Base Currency?",
    "What Is a Quote Currency?",
    "What Is an Exchange Rate?",
    "Why Do Exchange Rates Change?",
    "What Is a Pip?",
    "What Is the Spread?",
]


def _empty_sections():
    # Every QRU methodology section is intentionally empty — no fabricated content.
    return {s: "Empty" for s in QRU_SECTIONS}


async def seed():
    created, updated = 0, 0
    for i, title in enumerate(TITLES, start=1):
        code = f"KR-FX-{i:04d}"
        existing = await db.knowledge_records.find_one({"kr_code": code})
        base = {
            "kr_code": code,
            "title": title,
            "subtitle": "",
            "category": "Finance / Forex",
            "division": "Finance",
            # Knowledge-First: no content, no fabricated truth.
            "verified_truth": "",
            "consumer_translation": "",
            "everyday_analogy": "",
            "story": "",
            "memory_sentence": "",
            "the_question": "",
            "simple_answer": "",
            "why_it_matters": "",
            "real_world_example": "",
            "qru_translation": "",
            "deep_roots": "",
            "plain_language_definition": "",
            "professional_definition": "",
            "common_beginner_mistakes": [],
            "knowledge_connections": [],
            "references": [],
            "sources": [],
            "practice_activities": [],
            "practice_application": [],
            "key_vocabulary": [],
            # Curriculum classification
            "curriculum": "QRU Forex Fundamentals™",
            "curriculum_order": i,
            "audience": "General Public",
            "level": "Foundational",
            "product_types": [],
            # Governance / status flags
            "record_class": "Topic Seed",
            "verification_status": "Topic Seed",
            "approval_status": "Founder Approved",
            "source_label": "QRU Legacy Seed",
            "customer_facing": True,
            "readiness": "Topic Seed — Not Ready for Manufacturing",
            "treasure_standard": False,
            "treasure_standard_status": "Pending",
            "ai_content": "None",
            "promotion_ready": True,
            "confidence_score": 0,
            "reviewer": "Founder",
            "is_master_file": False,
            "understanding_status": "Not Manufactured",
            "section_status": _empty_sections(),
            "owner_id": OWNER_ID,
            "created_by": CREATED_BY,
            "updated_at": now_iso(),
        }
        if existing:
            await db.knowledge_records.update_one({"kr_code": code}, {"$set": base})
            updated += 1
        else:
            base.update({
                "id": gen_id(),
                "products_created": 0,
                "version": 1,
                "created_at": now_iso(),
                "verification": None,
            })
            await db.knowledge_records.insert_one(dict(base))
            created += 1
    print(f"QRU Forex Fundamentals™ seed complete — created {created}, updated {updated}")


if __name__ == "__main__":
    asyncio.run(seed())
