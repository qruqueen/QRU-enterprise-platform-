"""QRU Factory Concierge™ (Phase B) — the conversational guide over Factory OS (Constitution §7/§8).

Turns a plain-language request ("Create a video about financial literacy for beginners") into the
correct governed workflow. Deterministic & $0 by default. Optional light-AI (user-enabled) ONLY parses
the request into outcome + topic + audience + goal — it NEVER authors knowledge or invents a Knowledge
Record. The Knowledge-First check (§3.1/§14E) is ALWAYS deterministic, so the Concierge can never
hallucinate a product's factual basis. Governed by QRU-CON-0001.
"""
import re

from database import db
from models import gen_id, now_iso
import factory_os as fos

# Outcome detection — plain words the operator actually uses → the governed outcome id.
OUTCOME_SYNONYMS = {
    "video": ["video", "film", "movie", "clip", "reel", "short", "youtube"],
    "workbook": ["workbook", "worksheet", "worksheets", "exercises", "practice book"],
    "poster": ["poster", "flyer", "wall chart", "infographic"],
    "presentation": ["presentation", "slides", "slide deck", "deck", "powerpoint", "keynote"],
    "assessment": ["quiz", "assessment", "test", "exam", "questionnaire"],
    "knowledge_card": ["flash card", "flashcard", "flash cards", "flashcards", "knowledge card", "knowledge cards"],
    "book": ["book", "ebook", "e-book", "guidebook", "guide book"],
    "course": ["course", "class", "curriculum", "mini-course", "lessons", "lesson plan"],
    "podcast": ["podcast", "audio show", "episode"],
    "audiobook": ["audiobook", "audio book", "narration", "voice over", "voiceover", "voice-over"],
    "bundle": ["bundle", "package", "complete set", "product suite", "everything"],
}

# Audience detection → catalog labels used by the Create experience.
AUDIENCE_MAP = [
    (["beginner", "novice", "new to", "adult"], "Beginner adult"),
    (["teen", "teenager", "teens", "adolescent"], "Teen learner"),
    (["student", "students", "school", "college", "university", "kid", "kids", "child", "children"], "Student"),
    (["entrepreneur", "business owner", "founder", "startup"], "Entrepreneur"),
    (["professional", "expert", "advanced", "practitioner"], "Professional audience"),
    (["everyone", "general public", "public", "anyone", "general audience"], "General public"),
]

_FILLER = ("create", "make", "build", "design", "generate", "produce", "give me", "i want", "i'd like",
           "i would like", "please", "can you", "could you", "help me", "a", "an", "the", "some", "new",
           "about", "on", "regarding", "covering", "explaining", "teaching", "for teaching")


def _detect_outcome(text):
    t = f" {text.lower()} "
    for oid, syns in OUTCOME_SYNONYMS.items():
        for s in sorted(syns, key=len, reverse=True):
            if f" {s} " in t or t.strip().endswith(f" {s}") or t.strip() == s:
                return oid
    return ""


def _detect_audience(text):
    t = text.lower()
    for keys, label in AUDIENCE_MAP:
        if any(k in t for k in keys):
            return label
    return ""


def _extract_topic(text):
    """Pull the subject matter out of the request, stripping verbs, the outcome noun and audience."""
    t = f" {text.lower().strip()} "
    m = re.search(r"\b(?:about|on|regarding|covering|explaining|teaching)\b(.+)", t)
    if m:
        t = f" {m.group(1).strip()} "
    t = re.split(r"\bfor\b", t)[0]  # drop the "for <audience>" tail
    for syns in OUTCOME_SYNONYMS.values():
        for s in syns:
            t = re.sub(rf"\b{re.escape(s)}\b", " ", t)
    for keys, _ in AUDIENCE_MAP:
        for k in keys:
            t = re.sub(rf"\b{re.escape(k)}\b", " ", t)
    for w in _FILLER:
        t = re.sub(rf"\b{re.escape(w)}\b", " ", t)
    t = re.sub(r"[^a-z0-9\-\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) < 3 or not re.search(r"[a-z]", t):
        return ""
    return " ".join(w.capitalize() for w in t.split())


def _deterministic_parse(message):
    slots = {}
    oid = _detect_outcome(message)
    if oid:
        slots["outcome_id"] = oid
    aud = _detect_audience(message)
    if aud:
        slots["audience"] = aud
    topic = _extract_topic(message)
    if topic:
        slots["topic"] = topic
    return slots


async def _ai_parse(message):
    """Optional light-AI parse. Falls back to None on any failure or spend cap (never blocks the flow)."""
    try:
        import ai_service as ai
        system = (
            "You are the QRU Factory Concierge request parser. Extract the user's product request into JSON. "
            "Do NOT invent facts, knowledge, or a Knowledge Record. Return ONLY JSON: "
            '{"outcome_id": one of [video, workbook, poster, presentation, assessment, knowledge_card, book, '
            'course, podcast, audiobook, bundle] or "", "topic": string, "audience": string, "goal": string}. '
            "Leave a field empty when it is not clearly stated."
        )
        raw = await ai.llm_generate(system, message, session_id=f"concierge-{gen_id()[:8]}")
        parsed = ai.parse_json(raw) or {}
        out = {}
        if parsed.get("outcome_id") in fos._OUTCOME_BY_ID:
            out["outcome_id"] = parsed["outcome_id"]
        for k in ("topic", "audience", "goal"):
            v = (parsed.get(k) or "").strip()
            if v:
                out[k] = v
        return out or None
    except Exception:
        return None


async def _get_session(session_id):
    if session_id:
        s = await db.concierge_sessions.find_one({"session_id": session_id}, {"_id": 0})
        if s:
            return s
    sid = session_id or gen_id()
    s = {"session_id": sid, "slots": {"outcome_id": "", "topic": "", "audience": "", "goal": ""},
         "messages": [], "created_at": now_iso(), "updated_at": now_iso()}
    await db.concierge_sessions.insert_one(dict(s))
    s.pop("_id", None)
    return s


def _outcome_suggestions():
    return [{"label": o["name"], "value": f"Create a {o['name'].lower()}", "outcome_id": o["id"]}
            for o in fos.OUTCOMES]


async def handle_message(session_id, message, use_ai=False, name="Founder"):
    session = await _get_session(session_id)
    slots = session["slots"]
    message = (message or "").strip()

    # Reset short-circuit: clear slots and render the greeting WITHOUT parsing "start over" as a topic.
    if re.search(r"\b(start over|restart|reset|new request|clear)\b", message.lower()):
        slots = {"outcome_id": "", "topic": "", "audience": "", "goal": ""}
        await db.concierge_sessions.update_one(
            {"session_id": session["session_id"]},
            {"$set": {"slots": slots, "updated_at": now_iso()}})
        message = ""

    # Parse this turn — AI (optional) first, deterministic always as the reliable fallback.
    parsed = (await _ai_parse(message)) if (use_ai and message) else None
    ai_used = bool(parsed)
    if not parsed:
        parsed = _deterministic_parse(message)
    for k in ("outcome_id", "topic", "audience", "goal"):
        if parsed.get(k):
            slots[k] = parsed[k]

    outcome = fos._OUTCOME_BY_ID.get(slots["outcome_id"]) if slots["outcome_id"] else None
    outcome_view = {**outcome, "maturity_label": fos.MATURITY[outcome["maturity"]]} if outcome else None

    plan = None
    stage = "need_outcome"
    reply = ""
    suggestions = []
    can_launch = False

    if not slots["outcome_id"]:
        stage = "need_outcome"
        reply = (f"Hello {name.split()[0] if name else ''}. I'm the Factory Concierge. "
                 "Tell me what you'd like to create and I'll set up the governed workflow for you — "
                 "for example, \u201cCreate a video about financial literacy for beginners.\u201d "
                 "What would you like to make today?")
        suggestions = _outcome_suggestions()
    elif not slots["topic"]:
        stage = "need_topic"
        reply = (f"Great choice \u2014 a {outcome['name']}. What should it be about? "
                 "Give me the subject and, if you like, who it's for.")
    else:
        plan = await fos.build_plan(slots["outcome_id"], slots["topic"], slots["audience"], slots["goal"])
        gap = plan.get("knowledge_gap", {})
        if gap.get("knowledge_record_found"):
            stage = "ready"
            can_launch = True
            kr = gap["knowledge_record"]
            reply = (f"I found a verified Knowledge Record for this: {kr['kr_code']} \u2014 {kr['title']}. "
                     f"Your {outcome['name']} on \u201c{slots['topic']}\u201d"
                     + (f" for {slots['audience']}" if slots['audience'] else "")
                     + f" will be manufactured from it \u2014 never invented. "
                     f"I'll run it through {plan['launch']['workflow']} with design, QA and human approval "
                     "where required. Shall I start? You can also just say \u201cchange it to a workbook\u201d "
                     "or give me a different topic.")
        else:
            stage = "knowledge_gap"
            reply = (f"Honest answer: \u201c{slots['topic']}\u201d has not yet been manufactured as a governed "
                     "QRU Knowledge Record\u2122. Knowledge always comes before products, so I can't create a "
                     f"{outcome['name']} from it yet \u2014 I won't invent the facts. I can begin the Knowledge "
                     "Manufacturing Pipeline to research, verify and approve the knowledge first. Want me to start that?")

    # Persist the turn.
    turn = [{"role": "user", "text": message, "ts": now_iso()}] if message else []
    turn.append({"role": "concierge", "text": reply, "ts": now_iso(), "stage": stage})
    await db.concierge_sessions.update_one(
        {"session_id": session["session_id"]},
        {"$set": {"slots": slots, "updated_at": now_iso()}, "$push": {"messages": {"$each": turn}}})

    return {
        "session_id": session["session_id"],
        "stage": stage,
        "reply": reply,
        "slots": slots,
        "outcome": outcome_view,
        "plan": plan,
        "can_launch": can_launch,
        "suggestions": suggestions,
        "ai_used": ai_used,
        "governed_by": ["QRU-CON-0001 §7", "§8", "§3.1"],
    }


async def get_history(session_id):
    s = await db.concierge_sessions.find_one({"session_id": session_id}, {"_id": 0})
    return s or None
