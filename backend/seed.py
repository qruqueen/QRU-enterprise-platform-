import os
from database import db
from auth import hash_password, verify_password
from models import gen_id, now_iso, QRU_SECTIONS

AVATARS = [
    "https://images.pexels.com/photos/31869537/pexels-photo-31869537.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
    "https://images.pexels.com/photos/29852895/pexels-photo-29852895.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
]

DIGITAL_EMPLOYEES = [
    ("Chief Executive Agent", "Chief Executive Agent™", "Orchestrate the entire enterprise toward the mission of manufacturing understanding.",
     ["Strategic oversight", "Cross-division coordination", "Executive reporting"], ["All modules"], ["Command Center", "Analytics"], "Full"),
    ("Research Director", "Research Director™", "Discover and structure verified knowledge from credible evidence.",
     ["Literature review", "Evidence collection", "Source vetting"], ["Knowledge Records", "Research"], ["Web Research", "Summarizer"], "Draft"),
    ("Verification Lion", "Verification Lion™", "Guard the truth. Nothing is verified without rigorous scrutiny.",
     ["Fact verification", "Confidence scoring", "Source auditing"], ["Verification Center"], ["Verifier", "Citation Checker"], "Approve Records"),
    ("Understanding Agent", "Understanding Agent™", "Translate verified truth into understanding without simplifying the truth.",
     ["Consumer translation", "Analogy design", "Memory sentences"], ["Translation Center"], ["Language Model"], "Draft"),
    ("Manufacturing Director", "Manufacturing Director™", "Convert knowledge records into publication-ready products.",
     ["Product manufacturing", "Deliverable QA", "Order execution"], ["Manufacturing", "Products"], ["Content Generator"], "Draft"),
    ("Visual Director", "Visual Director™", "Design visuals, posters, and infographics that clarify understanding.",
     ["Visual concepts", "Poster layout", "Infographic design"], ["Assets", "Products"], ["Image Generation"], "Draft"),
    ("Health Director", "Health Director™", "Lead QRU Health University and health knowledge manufacturing.",
     ["Health curriculum", "College oversight", "Caregiver resources"], ["Health University"], ["Curriculum Builder"], "Draft"),
    ("Marketplace Director", "Marketplace Director™", "Monitor market trends and surface future opportunities.",
     ["Trend analysis", "Opportunity scouting"], ["Marketplace Intelligence"], ["Analytics"], "None"),
    ("Finance Director", "Finance Director™", "Track revenue, licensing, and financial health.",
     ["Revenue tracking", "Licensing finance"], ["Licensing", "Analytics"], ["Reports"], "None"),
    ("Marketing Director", "Marketing Director™", "Grow reach and communicate QRU's mission.",
     ["Campaigns", "Positioning"], ["Publishing"], ["Content Generator"], "Draft"),
    ("Legal Director", "Legal Director™", "Ensure compliance, licensing terms, and governance.",
     ["Compliance review", "License terms"], ["Licensing", "Administration"], ["Policy Checker"], "Approve Legal"),
    ("Curriculum Director", "Curriculum Director™", "Structure knowledge into courses and learning journeys.",
     ["Course design", "Lesson sequencing"], ["Products", "Health University"], ["Curriculum Builder"], "Draft"),
    ("Customer Support", "Customer Support™", "Support customers and gather continuous improvement signals.",
     ["Customer assistance", "Feedback intake"], ["Customer Management"], ["Knowledge Base"], "None"),
]

HEALTH_COLLEGES = [
    ("Heart Health", "Understand the cardiovascular system, prevention, and heart-healthy living.", "#EF4444"),
    ("Brain Health", "Understand cognition, memory, and neurological wellness.", "#8B5CF6"),
    ("Lung Health", "Understand respiratory function and breathing wellness.", "#06B6D4"),
    ("Cancer Understanding", "Understand cancer biology, screening, and treatment paths.", "#F59E0B"),
    ("Metabolic Health", "Understand metabolism, blood sugar, and energy balance.", "#10B981"),
    ("Kidney Health", "Understand renal function, filtration, and kidney care.", "#3B82F6"),
    ("Prevention & Wellness", "Understand preventive care and everyday wellness habits.", "#0047FF"),
]

SEED_RECORDS = [
    ("The Human Heart Pumps ~2,000 Gallons of Blood Daily", "Heart Health",
     "The adult human heart beats roughly 100,000 times per day, circulating about 2,000 gallons (7,570 liters) of blood through a closed vascular system.",
     "Verified", 96),
    ("Sleep Consolidates Memory", "Brain Health",
     "During deep and REM sleep, the brain replays and consolidates newly formed memories, strengthening synaptic connections essential for learning.",
     "Verified", 94),
    ("Insulin Regulates Blood Glucose", "Metabolic Health",
     "Insulin, produced by pancreatic beta cells, enables cells to absorb glucose from the bloodstream, maintaining stable blood sugar levels.",
     "Verified", 95),
    ("Vaccines Train the Immune System", "Prevention & Wellness",
     "Vaccines expose the immune system to a harmless component of a pathogen, prompting it to build memory cells that enable a rapid response upon future exposure.",
     "In Review", 88),
    ("The Kidneys Filter ~180 Liters of Blood Daily", "Kidney Health",
     "The kidneys filter about 180 liters of blood each day, reabsorbing water and nutrients while excreting waste as roughly 1-2 liters of urine.",
     "Draft", 0),
]

SEED_ORDERS = [
    ("Understanding the Human Heart", "General public", ["Poster", "Book", "Quiz"], "High", "Manufacturing"),
    ("How Sleep Builds Memory", "Students", ["Infographic", "Lesson Plan"], "Medium", "Research"),
    ("Diabetes Prevention Basics", "Caregivers", ["Caregiver Guide", "Workbook"], "High", "Quality Review"),
    ("Immune System 101", "Teachers", ["Presentation", "Teacher Guide"], "Medium", "Queued"),
    ("Kidney Care Essentials", "General public", ["Poster"], "Low", "Published"),
]


async def seed():
    await db.users.create_index("email", unique=True)

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@qru.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "qru-admin-2026")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": gen_id(), "email": admin_email, "password_hash": hash_password(admin_password),
            "name": "QRU Administrator", "role": "Administrator", "avatar": None, "created_at": now_iso(),
        })
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})

    # Demo executive user
    exec_email = "executive@qru.com"
    if not await db.users.find_one({"email": exec_email}):
        await db.users.insert_one({
            "id": gen_id(), "email": exec_email, "password_hash": hash_password("qru-exec-2026"),
            "name": "Jordan Ellis", "role": "Executive", "avatar": None, "created_at": now_iso(),
        })

    if await db.digital_employees.count_documents({}) == 0:
        for i, (name, title, mission, resp, perms, tools, auth) in enumerate(DIGITAL_EMPLOYEES):
            await db.digital_employees.insert_one({
                "id": gen_id(), "name": name, "title": title, "mission": mission,
                "responsibilities": resp, "permissions": perms, "tools": tools,
                "approval_authority": auth, "status": "Active",
                "avatar": AVATARS[i % len(AVATARS)],
                "current_assignments": [], "tasks_completed": 12 + i * 7,
                "performance": 88 + (i % 12),
                "activity_history": [{"action": "Activated", "at": now_iso()}],
                "created_at": now_iso(),
            })

    if await db.health_colleges.count_documents({}) == 0:
        for name, desc, color in HEALTH_COLLEGES:
            await db.health_colleges.insert_one({
                "id": gen_id(), "name": name, "description": desc, "color": color,
                "records": 0, "products": 0, "created_at": now_iso(),
            })

    if await db.knowledge_records.count_documents({}) == 0:
        for i, (title, cat, truth, status, conf) in enumerate(SEED_RECORDS):
            await db.knowledge_records.insert_one({
                "id": gen_id(), "kr_code": f"KR-{i + 1:05d}", "title": title, "subtitle": "",
                "category": cat, "verified_truth": truth,
                "consumer_translation": "", "everyday_analogy": "", "story": "",
                "memory_sentence": "", "references": [], "sources": [], "practice_activities": [],
                "confidence_score": conf, "verification_status": status,
                "approval_status": "Approved" if status == "Verified" else "Pending",
                "reviewer": "Verification Lion" if status == "Verified" else None,
                "products_created": 0, "version": 1, "created_by": "QRU Administrator",
                "created_at": now_iso(), "updated_at": now_iso(),
            })

    if await db.manufacturing_orders.count_documents({}) == 0:
        for i, (topic, aud, ptypes, prio, status) in enumerate(SEED_ORDERS):
            await db.manufacturing_orders.insert_one({
                "id": gen_id(), "mo_code": f"MO-{i + 1:05d}", "topic": topic, "audience": aud,
                "learning_level": "General", "product_types": ptypes, "priority": prio,
                "due_date": None, "verification_level": "Standard", "assigned_employees": [],
                "knowledge_record_id": None, "status": status, "deliverables": [],
                "approval_history": [{"stage": "Created", "by": "QRU Administrator", "at": now_iso()}],
                "created_by": "QRU Administrator", "created_at": now_iso(), "updated_at": now_iso(),
            })

    if await db.customers.count_documents({}) == 0:
        demo = [
            ("Lincoln Public Schools", "procurement@lps.org", "Lincoln Public Schools", "Institution", "Enterprise"),
            ("Dr. Amara Okafor", "amara@clinic.com", "Wellness Clinic", "Individual", "Professional"),
            ("Bright Minds Academy", "hello@brightminds.edu", "Bright Minds Academy", "Institution", "Standard"),
        ]
        for name, email, org, typ, tier in demo:
            await db.customers.insert_one({
                "id": gen_id(), "name": name, "email": email, "organization": org,
                "type": typ, "license_tier": tier, "status": "Active",
                "products_licensed": 0, "created_at": now_iso(),
            })

    if await db.notifications.count_documents({}) == 0:
        notifs = [
            ("Verification Lion verified a Knowledge Record", "success"),
            ("New Manufacturing Order MO-00001 entered Manufacturing", "info"),
            ("3 products awaiting human approval before publication", "warning"),
        ]
        for msg, level in notifs:
            await db.notifications.insert_one({
                "id": gen_id(), "message": msg, "level": level, "read": False, "created_at": now_iso(),
            })

    # Unified Understanding Colleges (modular divisions)
    if await db.colleges.count_documents({}) == 0:
        for name, desc, color in HEALTH_COLLEGES:
            await db.colleges.insert_one({
                "id": gen_id(), "name": name, "division": "Health", "description": desc,
                "color": color, "status": "Active", "created_at": now_iso(),
            })
        future = [
            ("Trading", "Understand markets, risk, and disciplined decision-making.", "#F5B21A"),
            ("Finance", "Understand money, compounding, and financial freedom.", "#10B981"),
            ("AI", "Understand artificial intelligence from first principles.", "#35106A"),
            ("Programming", "Understand how software and computation truly work.", "#3B82F6"),
            ("Parenting", "Understand child development and confident parenting.", "#EC4899"),
            ("Business", "Understand how enterprises create and capture value.", "#0EA5E9"),
            ("Government", "Understand civics, policy, and how systems govern.", "#6366F1"),
        ]
        for div, desc, color in future:
            await db.colleges.insert_one({
                "id": gen_id(), "name": f"College of {div}", "division": div, "description": desc,
                "color": color, "status": "Coming Soon", "created_at": now_iso(),
            })

    # Migrate existing Knowledge Records into the QRU methodology structure (idempotent)
    to_migrate = await db.knowledge_records.find({"section_status": {"$exists": False}}).to_list(1000)
    for doc in to_migrate:
        verified = doc.get("verification_status") == "Verified"
        upd = {"division": doc.get("division", "Health")}
        # preserve legacy content
        if not doc.get("qru_translation") and doc.get("consumer_translation"):
            upd["qru_translation"] = doc["consumer_translation"]
        if not doc.get("practice_application") and doc.get("practice_activities"):
            upd["practice_application"] = doc["practice_activities"]
        for s in QRU_SECTIONS:
            if s not in doc and s not in upd:
                upd[s] = [] if s in ("practice_application", "key_vocabulary") else ""
        merged = {**doc, **upd}
        section_status = {}
        for s in QRU_SECTIONS:
            val = merged.get(s)
            filled = (len(val) > 0) if isinstance(val, list) else bool(val and str(val).strip())
            section_status[s] = ("Verified" if verified else "Draft") if filled else "Empty"
        upd["section_status"] = section_status
        all_filled = all(section_status[s] != "Empty" for s in QRU_SECTIONS)
        upd["understanding_status"] = "Verified" if (verified and all_filled) else "Not Manufactured"
        upd["is_master_file"] = verified
        upd["treasure_standard"] = verified and all_filled
        upd.setdefault("verification", None)
        await db.knowledge_records.update_one({"id": doc["id"]}, {"$set": upd})


    # write test credentials
    try:
        with open("/app/memory/test_credentials.md", "w") as f:
            f.write(
                "# QRU Factory Test Credentials\n\n"
                "## Admin\n"
                f"- Email: {admin_email}\n- Password: {admin_password}\n- Role: Administrator\n\n"
                "## Executive (test user)\n"
                "- Email: executive@qru.com\n- Password: qru-exec-2026\n- Role: Executive\n\n"
                "## Auth endpoints\n"
                "- POST /api/auth/register\n- POST /api/auth/login\n- GET /api/auth/me\n- POST /api/auth/logout\n\n"
                "Auth uses Bearer tokens (Authorization: Bearer <token>) returned by login/register.\n"
            )
    except Exception:
        pass
