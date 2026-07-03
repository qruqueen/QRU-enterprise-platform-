"""Seed the 16 QRU Legacy Knowledge Records (KR-QRU-####). Idempotent — upserts by kr_code.
These are QRU-created records: Founder Approved / QRU Legacy Seed / Ready for Manufacturing
(except records explicitly noted, e.g. KR-QRU-0012 = Future Initiative)."""
import asyncio

from database import db
from models import gen_id, now_iso, QRU_SECTIONS

OWNER_ID = "1fac7f6d-8dab-4ae8-bf37-a2ff30fe3c8f"
CREATED_BY = "Erica Talbert"

# (code, title, category, division, audience, level, summary, key_principle, product_types, readiness)
RECORDS = [
    ("KR-QRU-0001", "QRU Trading Decoder™", "Finance / Trading", "Finance", "General Public", "Foundational",
     "Teaches trading through simple conversation-first explanations using analogies such as dating, battlefield/tug-of-war, sports, and marketplace behavior.",
     "You do not have to know trading yet. You just have to know how to have a conversation with the market.",
     ["Book", "Poster", "Workbook", "Student Guide", "Teacher Guide", "Presentation", "Quick Guide"], "Ready for Manufacturing"),
    ("KR-QRU-0002", "QRU Chart Language Decoder™", "Finance / Trading", "Finance", "Beginners", "Foundational",
     "Helps learners understand charts as a language of price, volume, support, resistance, candles, trend, and momentum.",
     "Observation comes before vocabulary.",
     ["Book", "Poster", "Workbook", "Flash Cards", "Presentation"], "Ready for Manufacturing"),
    ("KR-QRU-0003", "QRU Support and Resistance Decoder™", "Finance / Trading", "Finance", "Beginners", "Foundational",
     "Explains support and resistance as areas where buyers or sellers previously showed strength.",
     "Support is where buyers may step in; resistance is where sellers may push back.",
     ["Poster", "Quick Guide", "Workbook", "Practice Charts"], "Ready for Manufacturing"),
    ("KR-QRU-0004", "QRU Pivot Points in Day Trading", "Finance / Trading", "Finance", "Beginners", "Introductory",
     "Teaches how traders locate important turning points and draw key lines on charts using simple sports and football-field analogies.",
     "", ["Poster", "Quick Guide", "Practice Sheet"], "Ready for Manufacturing"),
    ("KR-QRU-0005", "QRU AI Literacy Foundations™", "AI Literacy / Education", "AI Literacy",
     "Students, Parents, Teachers, General Public", "Foundational",
     "Teaches people how to use AI as a tool while remembering that the human remains the thinker.",
     "Use AI as a tool. You are the thinker.",
     ["Poster", "Worksheet", "Teacher Guide", "Parent Handout", "Mini Lesson", "Workbook"], "Ready for Manufacturing"),
    ("KR-QRU-0006", "QRU Prompt Library for Consumers™", "AI Literacy", "AI Literacy", "General Public", "Introductory",
     "Provides copy-and-paste prompts that help everyday users communicate clearly with AI tools.",
     "", ["Prompt Pack", "Quick Guide", "Poster", "Workbook"], "Ready for Manufacturing"),
    ("KR-QRU-0007", "QRU Health University™", "Health Education", "Health",
     "General Public", "Foundational",
     "Umbrella educational system for QRU health products organized into colleges such as Heart Health, Brain Health, Lung Health, Cancer Understanding, Metabolic Health, and Kidney Health.",
     "", ["University Guide", "Course Map", "Presentation", "Poster"], "Ready for Manufacturing"),
    ("KR-QRU-0008", "QRU Heart Health Library™", "Health / Heart Health", "Health", "General Public", "Foundational",
     "Health education library focused on heart attack understanding, blood pressure, cholesterol, heart function, and prevention awareness.",
     "", ["Book", "Poster", "Workbook", "Student Guide", "Teacher Guide", "Presentation"], "Ready for Manufacturing"),
    ("KR-QRU-0009", "Heart Attack Journey™", "Health / Heart Health", "Health", "General Public", "Introductory",
     "Explains the heart attack experience in simple, consumer-friendly language from risk factors to symptoms, emergency response, treatment, recovery, and prevention.",
     "", ["Book", "Workbook", "Poster", "Quick Guide", "Family Guide", "Presentation"], "Ready for Manufacturing"),
    ("KR-QRU-0010", "Brain Deconstructed™", "Health / Brain Health", "Health", "General Public", "Foundational",
     "Helps learners understand the brain through plain-language explanations, analogies, memory aids, and visual teaching.",
     "", ["Book", "Poster", "Workbook", "Presentation"], "Ready for Manufacturing"),
    ("KR-QRU-0011", "QRU Root Principle™", "Faith / Philosophy / Personal Growth", "Faith", "General Public", "Foundational",
     "Teaches the principle: Don’t obsess over the fruit. Deepen the roots.",
     "Roots → Trunk → Branches → Fruit. Faith → Understanding → Action → Results.",
     ["Poster", "Journal Page", "Reflection Guide", "Meditation Script"], "Ready for Manufacturing"),
    ("KR-QRU-0012", "QRU Bible Stories™", "Faith / Bible Education", "Faith",
     "Children, Teens, Families, Churches, Homeschool", "Future Initiative",
     "Future QRU mission line for creating free, easy-to-understand Bible story videos, scripts, storyboards, narration, discussion guides, and printable lessons.",
     "", ["Video", "Script", "Storyboard", "Family Guide", "Discussion Guide", "Printable Lesson"], "Future Initiative"),
    ("KR-QRU-0013", "Guided Understanding System™", "QRU Methodology", "QRU Core", "Internal / Education Design", "Foundational",
     "QRU lesson architecture organized around learner questions: The Question, Simple Answer, Why It Matters, Real-World Example, QRU Translation™, Memory Sentence, Vocabulary, Deep Roots, and Status Label.",
     "", ["Teaching Template", "Course Template", "Workbook Template"], "Ready for Manufacturing"),
    ("KR-QRU-0014", "QRU Treasure Standard™", "QRU Governance / Quality", "QRU Core", "Internal / Founder / Production", "Foundational",
     "QRU quality standard requiring products to be accurate, clear, useful, memorable, customer-ready, and worthy of publication.",
     "", ["Checklist", "Quality Gate", "Review Template"], "Ready for Manufacturing"),
    ("KR-QRU-0015", "QRU Factory Orchestrator™", "QRU Architecture", "QRU Core", "Internal", "Foundational",
     "QRU is the orchestrator that coordinates best-in-class tools through governed workflows rather than replacing every specialized tool.",
     "Build the factory once. Improve it forever.",
     ["Architecture Record", "Founder Guide"], "Ready for Manufacturing"),
    ("KR-QRU-0016", "QRU Knowledge-First Manufacturing™", "QRU Manufacturing", "QRU Core", "Internal", "Foundational",
     "Verified knowledge is the permanent asset. Products are manufactured repeatedly from that verified knowledge.",
     "Think once. Store forever. Manufacture many times. Sell repeatedly. Improve continuously.",
     ["Manufacturing Standard", "Workflow Poster"], "Ready for Manufacturing"),
]


async def seed():
    created, updated = 0, 0
    for code, title, category, division, audience, level, summary, principle, ptypes, readiness in RECORDS:
        existing = await db.knowledge_records.find_one({"kr_code": code})
        base = {
            "kr_code": code, "title": title, "subtitle": "", "category": category, "division": division,
            "verified_truth": summary, "consumer_translation": summary, "everyday_analogy": "",
            "story": "", "memory_sentence": principle, "the_question": "", "simple_answer": summary,
            "why_it_matters": "", "real_world_example": "", "qru_translation": "", "deep_roots": "",
            "references": [], "sources": [], "practice_activities": [], "key_vocabulary": [],
            "practice_application": [],
            "audience": audience, "level": level, "product_types": ptypes,
            "source_label": "QRU Legacy Seed", "readiness": readiness,
            "confidence_score": 95, "verification_status": "Verified",
            "approval_status": "Founder Approved", "reviewer": "Founder",
            "is_master_file": True, "treasure_standard": False,
            "understanding_status": "Not Manufactured",
            "owner_id": OWNER_ID, "created_by": CREATED_BY, "updated_at": now_iso(),
        }
        base["section_status"] = {s: ("Verified" if base.get(s) else "Empty") for s in QRU_SECTIONS}
        if existing:
            await db.knowledge_records.update_one({"kr_code": code}, {"$set": base})
            updated += 1
        else:
            base.update({"id": gen_id(), "products_created": 0, "version": 1, "created_at": now_iso(),
                         "verification": None})
            await db.knowledge_records.insert_one(dict(base))
            created += 1
    print(f"QRU KR seed complete — created {created}, updated {updated}")


if __name__ == "__main__":
    asyncio.run(seed())
