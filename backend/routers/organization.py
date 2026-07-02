from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean
from ai_service import llm_generate, parse_json

router = APIRouter(prefix="/api", tags=["organization"])

AV = [
    "https://images.pexels.com/photos/31869537/pexels-photo-31869537.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
    "https://images.pexels.com/photos/29852895/pexels-photo-29852895.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
]

# (name, title, department, expertise[], responsibilities[])
EXECUTIVE_BOARD = [
    ("Kingdom Lion™", "Verification Director", "Verification",
     ["Evidence", "Facts", "Definitions", "Scientific Accuracy", "Confidence Scores"],
     ["Verify evidence", "Set confidence scores", "Uphold verification standards"]),
    ("Legacy Eagle™", "Systems & Strategy Director", "Strategy",
     ["Systems Thinking", "Knowledge Architecture", "Enterprise Design", "Long-term Context"],
     ["Maintain knowledge architecture", "Ensure strategic consistency"]),
    ("Legacy Bear™", "Education Director", "Education",
     ["Teaching Quality", "Learning Psychology", "Examples", "Memory", "Storytelling"],
     ["Craft understanding", "Ensure reading flow", "Design memory aids"]),
    ("Queen Unity™", "Perspective Director", "Perspective",
     ["Balanced Thinking", "Alternative Perspectives", "Bias Detection", "Inclusive Learning"],
     ["Detect bias", "Ensure respectful, inclusive communication"]),
    ("Crowned Bull™", "Application Director", "Application",
     ["Practical Use", "Decision Support", "Actionable Guidance", "Problem Solving"],
     ["Turn understanding into daily application"]),
    ("Royal Phoenix™", "Innovation Director", "Innovation",
     ["Future Opportunities", "Research Expansion", "Emerging Technologies", "Product Innovation"],
     ["Scout opportunities", "Drive continuous improvement"]),
    ("Consumer Advocate™", "Customer Experience Director", "Customer Experience",
     ["Immediate Value", "Ease of Understanding", "Purchase Confidence", "Product Simplicity"],
     ["Champion the learner's experience"]),
    ("Marketing Director™", "Marketing Director", "Marketing",
     ["Messaging", "Campaigns", "Market Positioning", "Audience Growth", "Launch Strategy"],
     ["Prepare launches", "Grow audience"]),
    ("Sales Director™", "Sales Director", "Sales",
     ["Product Value", "Sales Funnels", "Conversion", "Pricing Strategy", "Customer Journey"],
     ["Optimize conversion", "Design pricing"]),
    ("Brand Director™", "Brand Director", "Brand",
     ["Brand Consistency", "Voice", "Mission", "Identity", "Naming", "Brand Standards"],
     ["Guard brand consistency", "Approve identity"]),
    ("Manufacturing Director™", "Manufacturing Director", "Manufacturing",
     ["Production Efficiency", "Automation", "Recipes", "Quality Control", "Release Readiness"],
     ["Run the manufacturing pipeline", "Ensure release readiness"]),
    ("Health Director™", "Health Director", "Health",
     ["Health Knowledge", "Medical Review", "Consumer Safety", "Educational Prioritization"],
     ["Review health knowledge for safety & accuracy"]),
    ("Creative Studio Director™", "Creative Studio Director", "Creative Studio",
     ["Brand Identity", "Product Branding", "Design Systems", "Typography", "Illustration", "Visual Consistency"],
     ["Design every visual asset", "Own QRU design standards", "Creative quality review"]),
    ("Organizational Health Director™", "Organizational Health Director", "Organizational Health",
     ["Enterprise Monitoring", "Bottleneck Detection", "Workload Balancing", "Continuous Improvement"],
     ["Monitor enterprise health", "Detect bottlenecks & idle/overloaded specialists", "Recommend improvements early"]),
    ("Experience Lab Director™", "Experience Lab Director", "Experience Lab",
     ["Customer Journey", "Usability", "Learning Effectiveness", "Delight", "Accessibility"],
     ["Experience QRU as customers do", "Measure clarity & delight", "Recommend experience improvements"]),
]

EMERGENT_SPECIALISTS = [
    ("Software Architect", "Architecture", ["System Design", "Scalability", "Patterns"]),
    ("Coding Specialist", "Engineering", ["Implementation", "Code Quality", "Refactoring"]),
    ("Database Engineer", "Data", ["Schema Design", "Indexing", "Query Optimization"]),
    ("Security Specialist", "Security", ["AuthN/AuthZ", "Threat Modeling", "Secrets"]),
    ("Performance Engineer", "Performance", ["Profiling", "Caching", "Load"]),
    ("Testing Specialist", "Quality", ["E2E Testing", "Regression", "Coverage"]),
    ("Deployment Engineer", "DevOps", ["CI/CD", "Release", "Rollback"]),
    ("Accessibility Specialist", "Accessibility", ["WCAG", "ARIA", "Inclusive UX"]),
    ("UX Designer", "UX", ["Flows", "Usability", "Interaction"]),
    ("Product Designer", "Design", ["Product Design", "Prototyping", "Systems"]),
    ("Infrastructure Engineer", "Infrastructure", ["Kubernetes", "Networking", "Reliability"]),
    ("Documentation Specialist", "Docs", ["Technical Writing", "Guides", "API Docs"]),
    ("Automation Specialist", "Automation", ["Pipelines", "Bots", "Workflow"]),
]

# task type -> departments to assemble into a review team
TASK_TEAMS = {
    "Verify Knowledge": ["Verification", "Education", "Perspective", "Health"],
    "Manufacture Product": ["Manufacturing", "Creative Studio", "Brand", "Education"],
    "Launch Product": ["Marketing", "Sales", "Brand", "Customer Experience"],
    "New Research": ["Innovation", "Strategy", "Verification"],
    "Design & Branding": ["Creative Studio", "Brand", "UX", "Design"],
    "Technical / Deployment": ["Architecture", "Security", "Quality", "DevOps"],
}


async def seed_registry():
    if await db.registry_agents.count_documents({}) > 0:
        return
    docs = []
    for i, (name, title, dept, exp, resp) in enumerate(EXECUTIVE_BOARD):
        docs.append({
            "id": gen_id(), "name": name, "title": title, "department": dept,
            "expertise": exp, "responsibilities": resp, "origin": "QRU", "is_board": True,
            "availability": "Available", "workload": 20 + (i * 5) % 60, "projects_assigned": (i % 4) + 1,
            "performance": 90 + (i % 10), "last_activity": now_iso(),
            "avatar": AV[i % len(AV)],
        })
    for i, (name, dept, exp) in enumerate(EMERGENT_SPECIALISTS):
        docs.append({
            "id": gen_id(), "name": f"Emergent {name}", "title": name, "department": dept,
            "expertise": exp, "responsibilities": [f"Provide {dept} expertise to QRU"],
            "origin": "Emergent", "is_board": False,
            "availability": "Available", "workload": 10 + (i * 7) % 50, "projects_assigned": i % 3,
            "performance": 92 + (i % 8), "last_activity": now_iso(), "avatar": None,
        })
    await db.registry_agents.insert_many(docs)


@router.get("/registry")
async def registry(user=Depends(get_current_user)):
    agents = await db.registry_agents.find().sort("is_board", -1).to_list(200)
    return clean(agents)


class AssembleTeam(BaseModel):
    task_type: str


@router.post("/registry/assemble")
async def assemble_team(data: AssembleTeam, user=Depends(get_current_user)):
    depts = TASK_TEAMS.get(data.task_type, [])
    team = await db.registry_agents.find({"department": {"$in": depts}}).to_list(50)
    return {"task_type": data.task_type, "departments": depts, "team": clean(team), "task_types": list(TASK_TEAMS.keys())}


@router.get("/registry/task-types")
async def task_types(user=Depends(get_current_user)):
    return {"task_types": list(TASK_TEAMS.keys())}


@router.get("/org-activity")
async def org_activity(user=Depends(get_current_user)):
    items = await db.org_activity.find().sort("created_at", -1).to_list(40)
    return clean(items)


@router.get("/enterprise-health")
async def enterprise_health(user=Depends(get_current_user)):
    """Organizational Health Director™ — continuous self-monitoring."""
    kr_total = await db.knowledge_records.count_documents({})
    kr_verified = await db.knowledge_records.count_documents({"verification_status": "Verified"})
    verify_queue = await db.knowledge_records.count_documents(
        {"verification_status": {"$in": ["Draft", "In Review", "Revision Requested"]}})
    not_manufactured = await db.knowledge_records.count_documents(
        {"verification_status": "Verified", "understanding_status": "Not Manufactured"})
    needs_regen = await db.products.count_documents({"status": "Needs Regeneration"})
    creative_pending = await db.products.count_documents(
        {"$or": [{"creative_status": {"$exists": False}}, {"creative_status": "Pending"}]})
    failed_jobs = await db.manufacturing_jobs.count_documents({"status": "failed"})

    agents = await db.registry_agents.find().to_list(200)
    idle = [a["name"] for a in agents if a.get("workload", 0) < 15]
    overloaded = [a["name"] for a in agents if a.get("workload", 0) > 85]

    systems = {
        "Verification": max(0, 100 - verify_queue * 8),
        "Manufacturing": max(0, 100 - not_manufactured * 10 - failed_jobs * 15),
        "Creative Studio": max(0, 100 - creative_pending * 6),
        "Knowledge Database": min(100, 40 + kr_total * 5),
        "Publishing": max(0, 100 - needs_regen * 10),
        "Customer Experience": 90,
        "Communication": 95,
        "Innovation": 88,
    }
    overall = round(sum(systems.values()) / len(systems))

    bottlenecks = []
    if verify_queue > 3:
        bottlenecks.append({"area": "Verification", "detail": f"{verify_queue} records awaiting verification", "severity": "warning"})
    if not_manufactured > 0:
        bottlenecks.append({"area": "Manufacturing", "detail": f"{not_manufactured} verified records not yet manufactured", "severity": "warning"})
    if needs_regen > 0:
        bottlenecks.append({"area": "Publishing", "detail": f"{needs_regen} products need regeneration after a record changed", "severity": "critical"})
    if creative_pending > 0:
        bottlenecks.append({"area": "Creative Studio", "detail": f"{creative_pending} products awaiting creative review", "severity": "info"})
    if failed_jobs > 0:
        bottlenecks.append({"area": "Manufacturing", "detail": f"{failed_jobs} failed manufacturing job(s)", "severity": "critical"})

    recommendations = []
    if not_manufactured > 0:
        recommendations.append("Run the AI Manufacturing Pipeline on verified records that have not been manufactured.")
    if needs_regen > 0:
        recommendations.append("Regenerate products flagged after their source Knowledge Record changed.")
    if creative_pending > 0:
        recommendations.append("Route pending products through the Creative Studio before publication.")
    if idle:
        recommendations.append(f"{len(idle)} specialist(s) are idle — assign them to open work.")
    if not recommendations:
        recommendations.append("All systems healthy. Continue manufacturing understanding.")

    return {
        "overall": overall,
        "systems": systems,
        "bottlenecks": bottlenecks,
        "recommendations": recommendations,
        "idle_specialists": idle,
        "overloaded_specialists": overloaded,
        "metrics": {"knowledge_records": kr_total, "verified": kr_verified, "verification_queue": verify_queue,
                    "not_manufactured": not_manufactured, "needs_regeneration": needs_regen,
                    "creative_pending": creative_pending, "failed_jobs": failed_jobs},
    }


EXPERIENCE_CRITERIA = ["Clarity", "Understanding", "Engagement", "Visual Quality", "Accessibility", "Learning Effectiveness", "Customer Delight"]

EXPERIENCE_SYSTEM = """You are the QRU Experience Lab Director™. Experience this educational product exactly as a customer would.
Return ONLY JSON:
{
 "scores": {"Clarity": 0-100, "Understanding": 0-100, "Engagement": 0-100, "Visual Quality": 0-100, "Accessibility": 0-100, "Learning Effectiveness": 0-100, "Customer Delight": 0-100},
 "strengths": ["..."],
 "friction_points": ["..."],
 "recommendations": ["actionable improvement", "..."]
}"""


@router.get("/experience-lab/criteria")
async def experience_criteria(user=Depends(get_current_user)):
    return {"criteria": EXPERIENCE_CRITERIA}


@router.post("/experience-lab/evaluate")
async def experience_evaluate(body: dict, user=Depends(get_current_user)):
    pid = body.get("product_id")
    p = await db.products.find_one({"id": pid})
    if not p:
        from fastapi import HTTPException
        raise HTTPException(404, "Product not found")
    prompt = f"Product: {p['title']}\nType: {p['product_type']}\nAudience: {p.get('audience','')}\nContent excerpt:\n{(p.get('content') or '')[:1200]}"
    raw = await llm_generate(EXPERIENCE_SYSTEM, prompt, f"exp-{pid}")
    result = parse_json(raw) or {}
    await log_org_safe("Experience Lab Director™", "Experience Lab", "evaluated the customer experience for", p.get("product_code", ""))
    return {"product": {"id": p["id"], "title": p["title"], "product_type": p["product_type"]}, "evaluation": result}


@router.get("/consumer/products")
async def consumer_products(user=Depends(get_current_user)):
    prods = await db.products.find({"status": "Published"}, {"content": 0}).sort("updated_at", -1).to_list(200)
    return clean(prods)


async def log_org_safe(agent, dept, action, entity):
    try:
        from org_activity import log_org
        await log_org(agent, dept, action, entity, "success")
    except Exception:
        pass
