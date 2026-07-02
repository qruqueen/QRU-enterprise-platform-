from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean

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
