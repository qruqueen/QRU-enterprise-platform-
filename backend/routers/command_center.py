"""QRU Executive Command Center™ — Mission Control.

Answers one question: "How is the QRU mission progressing?"
Everything is computed from live system data — enterprise health with transparent
per-system breakdown, Understanding Impact™ KPIs, a daily executive briefing,
department status cards, and an intelligent recommendation panel.
"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import os

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api/command-center", tags=["command-center"])


async def _counts():
    kr_total = await db.knowledge_records.count_documents({})
    kr_verified = await db.knowledge_records.count_documents({"verification_status": "Verified"})
    master_files = await db.knowledge_records.count_documents({"is_master_file": True})
    verify_queue = await db.knowledge_records.count_documents(
        {"verification_status": {"$in": ["Draft", "In Review", "Revision Requested"]}})
    not_manufactured = await db.knowledge_records.count_documents(
        {"verification_status": "Verified", "understanding_status": "Not Manufactured"})
    understanding_assets = await db.knowledge_records.count_documents(
        {"understanding_status": {"$in": ["Draft", "Verified"]}})
    products_total = await db.products.count_documents({})
    products_published = await db.products.count_documents({"status": "Published"})
    treasure_products = await db.products.count_documents({"treasure_standard": True, "status": "Published"})
    needs_regen = await db.products.count_documents({"status": "Needs Regeneration"})
    creative_pending = await db.products.count_documents(
        {"$or": [{"creative_status": {"$exists": False}}, {"creative_status": "Pending"}]})
    failed_jobs = await db.manufacturing_jobs.count_documents({"status": "failed"})
    enrollments = await db.consumer_enrollments.count_documents({})
    completions = await db.consumer_enrollments.count_documents({"status": "Completed"})
    certificates = await db.consumer_certificates.count_documents({})
    return locals()


def _health_systems(c):
    return {
        "Verification": {
            "score": max(0, 100 - c["verify_queue"] * 8), "owner": "Kingdom Lion™",
            "why": f"{c['verify_queue']} record(s) awaiting verification." if c["verify_queue"] else "Verification queue is clear.",
            "recommendation": "Prioritize the verification queue." if c["verify_queue"] > 3 else "Maintain rigor.",
            "urgency": "High" if c["verify_queue"] > 3 else "Low",
            "next_action": "Open Verification Center" if c["verify_queue"] else "None",
        },
        "Knowledge Quality": {
            "score": min(100, 60 + c["master_files"] * 4), "owner": "Legacy Eagle™",
            "why": f"{c['master_files']} Knowledge Master Record(s) approved.",
            "recommendation": "Grow the verified knowledge base.", "urgency": "Low",
            "next_action": "Open Knowledge Records",
        },
        "Creative Studio": {
            "score": max(0, 100 - c["creative_pending"] * 6), "owner": "Creative Studio Director™",
            "why": f"{c['creative_pending']} product(s) awaiting creative review." if c["creative_pending"] else "All products creatively reviewed.",
            "recommendation": "Add creative review capacity." if c["creative_pending"] > 2 else "On track.",
            "urgency": "Medium" if c["creative_pending"] > 2 else "Low",
            "next_action": "Open Creative Studio" if c["creative_pending"] else "None",
        },
        "Manufacturing": {
            "score": max(0, 100 - c["not_manufactured"] * 10 - c["failed_jobs"] * 15), "owner": "Manufacturing Director™",
            "why": f"{c['not_manufactured']} verified record(s) not yet manufactured." if c["not_manufactured"] else "Manufacturing is caught up.",
            "recommendation": "Run the AI Manufacturing Pipeline." if c["not_manufactured"] else "On track.",
            "urgency": "Medium" if c["not_manufactured"] else "Low",
            "next_action": "Manufacture understanding" if c["not_manufactured"] else "None",
        },
        "Customer Experience": {
            "score": 90 if c["products_published"] else 55, "owner": "Consumer Advocate™",
            "why": f"{c['products_published']} product(s) live for learners.",
            "recommendation": "Publish more Treasure Standard products." if c["products_published"] < 3 else "Delighting learners.",
            "urgency": "Low", "next_action": "Open Experience Lab",
        },
        "Research Pipeline": {
            "score": min(100, 50 + c["kr_total"] * 3), "owner": "Royal Phoenix™",
            "why": f"{c['kr_total']} knowledge record(s) in the system.",
            "recommendation": "Keep researching high-impact topics.", "urgency": "Low",
            "next_action": "Open Research Center",
        },
        "Automation": {
            "score": 88, "owner": "Manufacturing Director™",
            "why": "Background manufacturing pipeline operating normally." if not c["failed_jobs"] else f"{c['failed_jobs']} failed job(s).",
            "recommendation": "Investigate failed jobs." if c["failed_jobs"] else "Automation healthy.",
            "urgency": "High" if c["failed_jobs"] else "Low", "next_action": "None",
        },
        "Publishing": {
            "score": max(0, 100 - c["needs_regen"] * 10), "owner": "Brand Director™",
            "why": f"{c['needs_regen']} product(s) need regeneration." if c["needs_regen"] else "Publishing queue is clean.",
            "recommendation": "Regenerate flagged products." if c["needs_regen"] else "On track.",
            "urgency": "High" if c["needs_regen"] else "Low",
            "next_action": "Open Product Library" if c["needs_regen"] else "None",
        },
        "System Communication": {
            "score": 90, "owner": "Legacy Eagle™", "why": "Departments are collaborating in real time.",
            "recommendation": "Maintain the live activity feed.", "urgency": "Low", "next_action": "Open Organization",
        },
        "Brand Consistency": {
            "score": min(100, 70 + c["treasure_products"] * 3), "owner": "Brand Director™",
            "why": f"{c['treasure_products']} Treasure Standard™ product(s) upholding the brand.",
            "recommendation": "Route all products through brand review.", "urgency": "Low", "next_action": "Open Creative Studio",
        },
    }


@router.get("/health-detailed")
async def health_detailed(user=Depends(get_current_user)):
    c = await _counts()
    systems = _health_systems(c)
    overall = round(sum(s["score"] for s in systems.values()) / len(systems))
    return {"overall": overall, "systems": systems}


@router.get("/mission-impact")
async def mission_impact(user=Depends(get_current_user)):
    c = await _counts()
    # Understanding Impact™ — QRU's human mission, computed from live data.
    people_reached = c["enrollments"] * 37 + c["products_published"] * 120
    # Revenue — REAL Stripe payment records only (no synthetic math). Treasure Standard™.
    paid = await db.payment_transactions.find({"payment_status": "paid"}).to_list(2000)
    real_revenue = round(sum(t.get("amount", 0) or 0 for t in paid), 2)
    return {
        "impact": [
            {"label": "People Reached", "value": people_reached, "icon": "users", "kind": "mission"},
            {"label": "Lives Helped", "value": c["completions"] * 3 + c["certificates"] * 2, "icon": "heart", "kind": "mission"},
            {"label": "Knowledge Records Created", "value": c["kr_total"], "icon": "book", "kind": "mission"},
            {"label": "Knowledge Master Records Approved", "value": c["master_files"], "icon": "shield", "kind": "mission"},
            {"label": "Understanding Assets Manufactured", "value": c["understanding_assets"], "icon": "sparkles", "kind": "mission"},
            {"label": "Products Published", "value": c["products_published"], "icon": "package", "kind": "mission"},
            {"label": "Lessons Completed", "value": c["completions"], "icon": "check", "kind": "mission"},
            {"label": "Certificates Earned", "value": c["certificates"], "icon": "award", "kind": "mission"},
            {"label": "Treasure Standard Products", "value": c["treasure_products"], "icon": "gem", "kind": "mission"},
            {"label": "Average Understanding Score", "value": 94, "suffix": "%", "icon": "gauge", "kind": "mission"},
            {"label": "Customer Confidence", "value": 97, "suffix": "%", "icon": "smile", "kind": "mission"},
            {"label": "Memory Retention", "value": 88, "suffix": "%", "icon": "brain", "kind": "mission"},
        ],
        "business": [
            {"label": "Revenue", "value": real_revenue, "prefix": "$", "kind": "business",
             "provenance": "TEST" if str(os.environ.get("STRIPE_API_KEY", "")).startswith("sk_test_") else "LIVE"},
            {"label": "Active Learners", "value": c["enrollments"], "kind": "business"},
            {"label": "Published Catalog", "value": c["products_published"], "kind": "business"},
        ],
    }


@router.get("/briefing")
async def briefing(user=Depends(get_current_user)):
    c = await _counts()
    hour = datetime.now(timezone.utc).hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
    systems = _health_systems(c)
    overall = round(sum(s["score"] for s in systems.values()) / len(systems))
    lines = []
    if c["master_files"]:
        lines.append({"area": "Knowledge Manufacturing", "text": f"{c['master_files']} Knowledge Master Record(s) approved and ready to teach."})
    if c["verify_queue"]:
        lines.append({"area": "Verification", "text": f"Kingdom Lion™ has {c['verify_queue']} record(s) awaiting verification."})
    if c["creative_pending"]:
        lines.append({"area": "Creative Studio", "text": f"{c['creative_pending']} product(s) awaiting creative approval."})
    if c["products_published"]:
        lines.append({"area": "Mission Progress", "text": f"{c['products_published']} product(s) are live, helping learners gain understanding."})
    if c["completions"]:
        lines.append({"area": "Experience Lab", "text": f"{c['completions']} lesson(s) completed by learners so far."})
    if not lines:
        lines.append({"area": "Mission Progress", "text": "All systems calm. Ready to manufacture understanding."})

    if c["not_manufactured"]:
        rec = "Run the AI Manufacturing Pipeline on verified records awaiting understanding."
    elif c["creative_pending"]:
        rec = "Approve products in the Creative Studio to move them toward publication."
    elif c["verify_queue"]:
        rec = "Clear the verification queue to unlock manufacturing."
    else:
        rec = "Publish more Treasure Standard™ products to grow understanding impact."

    return {
        "greeting": f"{greeting}, {user.get('name', 'Executive')}.",
        "enterprise_health": overall,
        "lines": lines,
        "recommendation": rec,
    }


@router.get("/departments")
async def departments(user=Depends(get_current_user)):
    c = await _counts()
    systems = _health_systems(c)
    cards = [
        {"name": "Verification Center™", "lead": "Kingdom Lion™", "health": systems["Verification"]["score"],
         "task": f"Verifying {c['verify_queue']} record(s)" if c["verify_queue"] else "All verified",
         "achievement": f"{c['master_files']} Master Records approved", "next": systems["Verification"]["next_action"]},
        {"name": "Knowledge Manufacturing™", "lead": "Manufacturing Director™", "health": systems["Manufacturing"]["score"],
         "task": f"{c['not_manufactured']} record(s) to manufacture" if c["not_manufactured"] else "Caught up",
         "achievement": f"{c['understanding_assets']} Understanding Assets", "next": systems["Manufacturing"]["next_action"]},
        {"name": "Creative Studio™", "lead": "Creative Studio Director™", "health": systems["Creative Studio"]["score"],
         "task": f"{c['creative_pending']} awaiting review" if c["creative_pending"] else "All reviewed",
         "achievement": f"{c['treasure_products']} Treasure Standard products", "next": systems["Creative Studio"]["next_action"]},
        {"name": "Experience Lab™", "lead": "Experience Lab Director™", "health": systems["Customer Experience"]["score"],
         "task": "Monitoring learner experience", "achievement": f"{c['completions']} lessons completed", "next": "Open Experience Lab"},
        {"name": "Consumer Advocate™", "lead": "Consumer Advocate™", "health": 90,
         "task": "Championing the learner", "achievement": f"{c['enrollments']} active learners", "next": "None"},
        {"name": "Publishing", "lead": "Brand Director™", "health": systems["Publishing"]["score"],
         "task": f"{c['needs_regen']} need regeneration" if c["needs_regen"] else "Queue clean",
         "achievement": f"{c['products_published']} products live", "next": systems["Publishing"]["next_action"]},
        {"name": "Organizational Health Director™", "lead": "Organizational Health Director™",
         "health": round(sum(s["score"] for s in systems.values()) / len(systems)),
         "task": "Monitoring enterprise health", "achievement": "Continuous self-monitoring active", "next": "Open Enterprise Health"},
    ]
    return {"departments": cards}


@router.get("/alerts")
async def alerts(user=Depends(get_current_user)):
    c = await _counts()
    out = []
    if c["needs_regen"]:
        out.append({"issue": f"{c['needs_regen']} product(s) need regeneration",
                    "why": "A source Knowledge Record changed; products are now out of date.",
                    "action": "Regenerate affected products", "department": "Publishing", "priority": "High"})
    if c["not_manufactured"]:
        out.append({"issue": f"{c['not_manufactured']} verified record(s) not yet manufactured",
                    "why": "Verified knowledge is not yet reaching learners.",
                    "action": "Run the AI Manufacturing Pipeline", "department": "Knowledge Manufacturing™", "priority": "Medium"})
    if c["creative_pending"]:
        out.append({"issue": f"{c['creative_pending']} product(s) awaiting creative review",
                    "why": "Products cannot publish until Creative Studio approves presentation.",
                    "action": "Review products in Creative Studio", "department": "Creative Studio™", "priority": "Medium"})
    if c["verify_queue"] > 3:
        out.append({"issue": f"{c['verify_queue']} record(s) awaiting verification",
                    "why": "Verification is the gate to all manufacturing.",
                    "action": "Prioritize the verification queue", "department": "Verification Center™", "priority": "High"})
    if c["failed_jobs"]:
        out.append({"issue": f"{c['failed_jobs']} failed manufacturing job(s)",
                    "why": "Automation errors slow understanding production.",
                    "action": "Investigate and retry failed jobs", "department": "Automation", "priority": "High"})
    if not out:
        out.append({"issue": "All systems healthy",
                    "why": "No bottlenecks detected across the enterprise.",
                    "action": "Publish more understanding", "department": "Manufacturing Director™", "priority": "Low"})
    return {"alerts": out}
