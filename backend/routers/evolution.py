"""QRU Enterprise Evolution Governance™ — "Extend Before Expand™".

This EXTENDS the Organizational Health Director™ (it deliberately does NOT create a new
department, honoring its own principle). It provides:
- Enterprise Evolution Review™: for any proposed capability, decide EXTEND vs CREATE.
- Continuous Refactoring insights computed from live enterprise data.
- Enterprise Memory: approved architectural decisions inform future recommendations.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean
from ai_service import llm_generate, parse_json

router = APIRouter(prefix="/api/evolution", tags=["evolution"])

# The existing QRU enterprise capabilities the review considers before proposing anything new.
QRU_CAPABILITIES = {
    "Verification Center™ (Kingdom Lion™)": "Verifies evidence, confidence scoring, truth protection.",
    "Knowledge Manufacturing™": "Manufactures Understanding Assets™ from verified Knowledge Master Records via staged AI + recipes.",
    "Creative Studio™ / Design Intelligence™": "Brand Library, Design Library, Master Assets, design language, templates, visual identity.",
    "Manufacturing Engine 2.0": "Recipes, assembly, missing-content detection, Quality Control auto-improve loop, release gates.",
    "Experience Lab™": "Evaluates customer experience — clarity, engagement, delight, accessibility.",
    "Consumer Learning Platform": "Customer-facing catalog, layered understanding, learning modes, progress, certificates.",
    "Executive Command Center": "Mission-first dashboard: health, Understanding Impact, briefing, alerts.",
    "Organizational Health Director™": "Continuous self-monitoring, bottleneck detection, workload balancing, evolution governance.",
    "Digital Workforce / Expertise Registry": "AI directors + Emergent specialists assembled into task teams.",
    "Understanding Colleges": "Modular knowledge divisions (Health active; others planned).",
}

EVOLUTION_SYSTEM = """You are the QRU Organizational Health Director™ applying the "Extend Before Expand™" governance principle.
QRU becomes more powerful by becoming more intelligent, not more complicated. The DEFAULT recommendation is to EXTEND an existing system unless there is substantial evidence a new capability is necessary.
Given a proposed objective and the list of EXISTING QRU capabilities, return ONLY JSON:
{
 "problem": "one-sentence restatement of the problem being solved",
 "questions": [
   {"q": "Is this already partially solved by an existing department?", "a": "..."},
   {"q": "Can an existing department reasonably absorb this responsibility?", "a": "..."},
   {"q": "Would extending simplify the enterprise?", "a": "..."},
   {"q": "Would a new department create duplicated responsibilities?", "a": "..."},
   {"q": "Does this support Research Once, Verify Once, Manufacture Forever?", "a": "..."}
 ],
 "impact": {"Mission Alignment": 0-100, "Customer Value": 0-100, "Educational Value": 0-100, "Operational Simplicity": 0-100, "Maintainability": 0-100, "Scalability": 0-100, "Brand Consistency": 0-100, "Knowledge Reuse": 0-100},
 "recommendation": "EXTEND EXISTING SYSTEM" or "CREATE NEW SYSTEM",
 "target_capability": "which existing capability to extend (if EXTEND), else the proposed new capability name",
 "rationale": "2-3 sentences explaining the decision, biased toward elegant simplicity"
}"""


class ReviewInput(BaseModel):
    objective: str
    save: Optional[bool] = False


@router.post("/review")
async def evolution_review(data: ReviewInput, user=Depends(get_current_user)):
    caps = "\n".join(f"- {k}: {v}" for k, v in QRU_CAPABILITIES.items())
    prompt = f"PROPOSED OBJECTIVE:\n{data.objective}\n\nEXISTING QRU CAPABILITIES:\n{caps}"
    raw = await llm_generate(EVOLUTION_SYSTEM, prompt, f"evo-{gen_id()[:8]}")
    result = parse_json(raw) or {}
    if data.save and result:
        doc = {"id": gen_id(), "objective": data.objective,
               "recommendation": result.get("recommendation"), "target": result.get("target_capability"),
               "rationale": result.get("rationale"), "by": user["name"], "created_at": now_iso()}
        await db.evolution_log.insert_one(dict(doc))
    return result


@router.get("/memory")
async def evolution_memory(user=Depends(get_current_user)):
    items = await db.evolution_log.find().sort("created_at", -1).to_list(100)
    return {"decisions": clean(items)}


@router.get("/capabilities")
async def capabilities(user=Depends(get_current_user)):
    return {"capabilities": [{"name": k, "does": v} for k, v in QRU_CAPABILITIES.items()]}


@router.get("/refactoring")
async def refactoring(user=Depends(get_current_user)):
    """Continuous Refactoring — the Organizational Health Director scans for complexity to simplify."""
    insights = []

    # Traceability gaps: products not linked to a Knowledge Master Record
    orphan_products = await db.products.count_documents({"$or": [{"knowledge_record_id": None}, {"knowledge_record_id": {"$exists": False}}]})
    if orphan_products:
        insights.append({"area": "Traceability", "finding": f"{orphan_products} product(s) are not linked to a Knowledge Master Record™.",
                         "recommendation": "Re-link or retire orphan products to preserve Research Once, Verify Once.", "severity": "warning"})

    # Overlap: legacy digital_employees vs registry_agents (two workforce models)
    emp = await db.digital_employees.count_documents({})
    reg = await db.registry_agents.count_documents({})
    if emp and reg:
        insights.append({"area": "Workforce Model", "finding": f"Two workforce collections coexist: digital_employees ({emp}) and registry_agents ({reg}).",
                         "recommendation": "Consolidate onto the Expertise Registry to remove duplicated responsibilities.", "severity": "info"})

    # Unmanufactured verified knowledge
    stale = await db.knowledge_records.count_documents({"verification_status": "Verified", "understanding_status": "Not Manufactured"})
    if stale:
        insights.append({"area": "Knowledge Reuse", "finding": f"{stale} verified record(s) have not been manufactured into products.",
                         "recommendation": "Run the Manufacturing Engine to reuse verified knowledge (Manufacture Forever).", "severity": "info"})

    # Products stuck below release
    stuck = await db.products.count_documents({"status": {"$in": ["Manufacturing", "Quality Control", "Improving"]}})
    if stuck:
        insights.append({"area": "Flow", "finding": f"{stuck} product(s) are mid-pipeline and not yet released.",
                         "recommendation": "Run Quality Control to certify and release, or resume the failed stage.", "severity": "info"})

    if not insights:
        insights.append({"area": "Enterprise Health", "finding": "No duplication or complexity detected.",
                         "recommendation": "Maintain elegant simplicity. Extend before you expand.", "severity": "success"})

    decisions = await db.evolution_log.count_documents({})
    return {"principle": "Extend Before Expand™", "insights": insights, "decisions_recorded": decisions}
