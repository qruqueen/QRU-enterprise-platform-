"""QRU Factory Operating System™ (Factory OS) — the outcome-first operating layer (Constitution §7).

Turns "What would you like to create today?" into a governed manufacturing workflow. It never asks
the operator to understand agents, pipelines, providers or checksums. It performs the Knowledge-Gap
Check (§3.1/§14E): when an approved Knowledge Record does not exist it says so honestly and offers to
begin the Knowledge Manufacturing Pipeline — knowledge always comes before products.

Deterministic & $0 by default. Governed by QRU-CON-0001.
"""
import re

from database import db

# Manufacturing maturity — honest labels (Founder directive). Never overstate automation.
MATURITY = {
    "gold_master_ready": "Gold Master Ready",
    "fully_automated": "Fully Automated",
    "guided_workflow": "Guided Workflow",
    "draft_generation": "Draft Generation",
    "script_narration": "Script + Narration",
    "experimental": "Experimental",
    "coming_soon": "Coming Soon",
}

# Outcome catalog — every outcome maps to a real governed workflow + constitutional section(s).
OUTCOMES = [
    {"id": "video", "name": "Video", "icon": "Film", "family": "Creation",
     "description": "A governed multi-scene video built scene-by-scene from licensed footage with narration, captions and QA.",
     "maturity": "gold_master_ready", "route": "/flagship-showcase", "workflow": "MO-012 Controlled Flagship Showcase™",
     "recipe": "Short Video", "sections": ["3", "6", "9", "10"]},
    {"id": "workbook", "name": "Workbook", "icon": "BookOpenCheck", "family": "Creation",
     "description": "A printable workbook with warm-up, guided practice, independent exercises and an answer key.",
     "maturity": "guided_workflow", "route": "/manufacture", "workflow": "Workbook Builder™",
     "recipe": "Workbook", "sections": ["2", "3", "5"]},
    {"id": "poster", "name": "Poster", "icon": "Image", "family": "Design",
     "description": "A bold educational poster in QRU brand colors with a single unmistakable visual hero.",
     "maturity": "draft_generation", "route": "/manufacture", "workflow": "Poster Designer™",
     "recipe": "Poster", "sections": ["6", "10"]},
    {"id": "presentation", "name": "Presentation", "icon": "Presentation", "family": "Creation",
     "description": "A slide deck with clear hierarchy, speaker notes and QRU art direction.",
     "maturity": "guided_workflow", "route": "/manufacture", "workflow": "Presentation Designer™",
     "recipe": "Presentation", "sections": ["3", "6"]},
    {"id": "assessment", "name": "Assessment", "icon": "ClipboardList", "family": "Creation",
     "description": "A quiz or assessment with an answer key and explanations, aligned to the Knowledge Record.",
     "maturity": "guided_workflow", "route": "/manufacture", "workflow": "Quiz Builder™",
     "recipe": "Quiz", "sections": ["2", "5"]},
    {"id": "knowledge_card", "name": "Knowledge Cards", "icon": "Layers", "family": "Creation",
     "description": "Front/back knowledge cards covering the key terms and ideas.",
     "maturity": "guided_workflow", "route": "/manufacture", "workflow": "Workbook Builder™",
     "recipe": "Flash Cards", "sections": ["2", "3"]},
    {"id": "book", "name": "Book", "icon": "BookOpen", "family": "Creation",
     "description": "A companion book outline with chapters and summaries, ready for the Gold Master build.",
     "maturity": "draft_generation", "route": "/manufacture", "workflow": "Book Publisher™",
     "recipe": "Book", "sections": ["2", "3", "6"]},
    {"id": "course", "name": "Course", "icon": "GraduationCap", "family": "Creation",
     "description": "A mini-course with modules, lessons and learning outcomes.",
     "maturity": "draft_generation", "route": "/manufacture", "workflow": "Lesson Builder™",
     "recipe": "Course", "sections": ["3", "4"]},
    {"id": "podcast", "name": "Podcast", "icon": "Mic", "family": "Creation",
     "description": "A conversational podcast script with intro and outro, plus OpenAI TTS narration.",
     "maturity": "script_narration", "route": "/manufacture", "workflow": "Script Writer™ + Voice Narrator™",
     "recipe": "Podcast Script", "sections": ["3", "9"]},
    {"id": "audiobook", "name": "Audiobook", "icon": "Headphones", "family": "Creation",
     "description": "A narration script optimized for voice-over with OpenAI TTS audio.",
     "maturity": "script_narration", "route": "/manufacture", "workflow": "Voice Narrator™",
     "recipe": "Audio Narration", "sections": ["3", "9"]},
    {"id": "bundle", "name": "Complete Product Bundle", "icon": "Boxes", "family": "Creation",
     "description": "A coordinated package of products manufactured together from one verified Knowledge Record.",
     "maturity": "guided_workflow", "route": "/manufacture", "workflow": "Package Manufacturing™",
     "recipe": "Core Package", "sections": ["3", "4", "10"]},
]

_OUTCOME_BY_ID = {o["id"]: o for o in OUTCOMES}

_STOP = set("the a an and or of to in for with on at is are be by from this about into over under how "
            "what why when where which who your you our we it as will can basic basics intro introduction".split())


def _tokens(text):
    return {w for w in re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", (text or "").lower()) if w not in _STOP}


def outcomes_view():
    return {"outcomes": [{**o, "maturity_label": MATURITY[o["maturity"]]} for o in OUTCOMES],
            "maturity_legend": MATURITY,
            "operating_question": "What would you like to create today?"}


async def knowledge_gap_check(topic, audience="", goal=""):
    """Constitution §3.1/§14E. Find an APPROVED (Verified) Knowledge Record for the topic.
    Never fabricates a KR. If none exists, returns the honest message + pipeline offer."""
    topic_tokens = _tokens(topic)
    goal_tokens = _tokens(goal)
    best, best_score = None, 0.0
    candidates = []
    async for r in db.knowledge_records.find(
            {"verification_status": "Verified"},
            {"_id": 0, "kr_code": 1, "id": 1, "title": 1, "topic": 1, "verification_status": 1}):
        r_tokens = _tokens(f"{r.get('title')} {r.get('topic')}")
        if not r_tokens or not topic_tokens:
            continue
        # Score primarily on topic overlap; goal overlap is a small bonus (never dilutes the topic).
        topic_overlap = len(topic_tokens & r_tokens)
        goal_bonus = 0.15 * len(goal_tokens & r_tokens) if goal_tokens else 0
        score = topic_overlap / len(topic_tokens) + goal_bonus
        if topic_overlap:
            candidates.append({"kr_code": r.get("kr_code"), "id": r.get("id"), "title": r.get("title"), "score": round(min(score, 1.0), 2)})
        if score > best_score:
            best, best_score = r, score
    candidates.sort(key=lambda c: -c["score"])
    found = bool(best and best_score >= 0.34)
    if found:
        return {
            "knowledge_record_found": True,
            "knowledge_record": {"kr_code": best.get("kr_code"), "id": best.get("id"), "title": best.get("title")},
            "match_score": round(best_score, 2),
            "alternatives": candidates[:4],
            "message": f"Approved Knowledge Record found: {best.get('kr_code')} — {best.get('title')}.",
        }
    return {
        "knowledge_record_found": False,
        "alternatives": candidates[:4],
        "message": "This topic has not yet been manufactured as a governed QRU Knowledge Record\u2122.",
        "offer": {"action": "begin_knowledge_manufacturing", "route": "/promotion-pipeline",
                  "label": "Begin the Knowledge Manufacturing Pipeline",
                  "note": "Knowledge always comes before products. QRU will research, verify and manufacture a "
                          "governed Knowledge Record before any product is created from this topic."},
    }


async def build_plan(outcome_id, topic, audience="", goal=""):
    """Assemble a governed plan the operator can launch. Honest about KR status and maturity."""
    outcome = _OUTCOME_BY_ID.get(outcome_id)
    if not outcome:
        return {"ok": False, "error": f"Unknown outcome '{outcome_id}'."}
    gap = await knowledge_gap_check(topic, audience, goal)
    steps = [
        "Confirm the outcome and audience",
        "Verify an approved Knowledge Record exists (Knowledge-First)",
        f"Manufacture the {outcome['name']} via {outcome['workflow']}",
        "Design & Art Direction review (Constitution §6)",
        "Technical QA + Content/Brand QA (§10)",
        "Human approval where required (§9)",
        "Register in the Master Asset Vault™ (§11)",
        "Distribute / publish (§4 Legacy)",
    ]
    can_launch = gap["knowledge_record_found"]
    return {
        "ok": True,
        "outcome": {**outcome, "maturity_label": MATURITY[outcome["maturity"]]},
        "topic": topic, "audience": audience, "goal": goal,
        "knowledge_gap": gap,
        "can_launch": can_launch,
        "launch": {"route": outcome["route"], "workflow": outcome["workflow"],
                   "context": {"outcome_id": outcome_id, "topic": topic, "audience": audience,
                               "goal": goal, "recipe": outcome["recipe"],
                               "knowledge_record": gap.get("knowledge_record")}},
        "governed_by": [f"QRU-CON-0001 §{s}" for s in outcome["sections"]],
        "steps": steps,
        "guidance": {
            "where_am_i": "Factory OS — Create",
            "what_am_i_creating": f"A {outcome['name']} about “{topic}”" + (f" for {audience}" if audience else ""),
            "whats_happening_now": "Planning — confirming knowledge and workflow before manufacturing.",
            "what_happens_next": (f"Launch the {outcome['workflow']} workflow." if can_launch
                                  else "Begin the Knowledge Manufacturing Pipeline first (no approved KR yet)."),
            "what_needs_my_approval": "Scene/section approvals and Gold Master certification (§9/§10).",
            "where_is_my_product": "It will be registered in the Master Asset Vault™ (§11).",
            "how_do_i_publish": "Through the Distribution Center™ once Distribution Ready (§4).",
        },
    }
