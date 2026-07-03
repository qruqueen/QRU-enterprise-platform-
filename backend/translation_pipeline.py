"""
QRU TRANSLATION ENGINE™ — a complete manufacturing workflow (not a single AI prompt).

Pipeline: Intent Analyzer™ → Audience Analyzer™ → Knowledge Retrieval™ →
QRU Translation Engine™ → Memory Engineering™ → Verification Lion™ → Treasure Standard™ Output.

Design: intent, audience, retrieval-from-verified-records, memory, and verification are
DETERMINISTIC, so a question about a verified topic produces Treasure Standard™ output even
when the AI provider is capped. Only draft generation for UNKNOWN topics needs the LLM — and
if that stage fails, the workflow reports the EXACT failed stage and preserves the input so the
user can retry from that stage instead of restarting.
"""
import re
import logging

from database import db
from ai_service import llm_generate, parse_json, QRU_METHODOLOGY_SYSTEM

logger = logging.getLogger("qru.translation")

STAGES = [
    "Intent Analyzer™", "Audience Analyzer™", "Knowledge Retrieval™",
    "QRU Translation Engine™", "Memory Engineering™", "Verification Lion™", "Treasure Standard™ Output",
]

AUDIENCES = {
    "Child (8–10)": "Very simple words, short sentences, playful concrete examples.",
    "Teen": "Clear and relatable, light depth, real-life relevance.",
    "Adult": "Clear general-audience explanation with useful depth.",
    "Teacher": "Includes teaching angle and how to explain it to others.",
    "Healthcare Professional": "Accurate, includes mechanism and clinical relevance.",
    "Investor": "Focuses on why it matters, implications, and outcomes.",
    "General Public": "Clear, warm, accessible to anyone.",
}


def _stage(name, status, detail=""):
    return {"stage": name, "status": status, "detail": detail}


def _err(stage, reason, retry_from=None):
    return {"failed_stage": stage, "reason": reason, "retry_from": retry_from or stage}


def _detect_audience(text):
    t = text.lower()
    if any(w in t for w in ["my kid", "child", "8 year", "explain to a kid", "for kids"]):
        return "Child (8–10)"
    if any(w in t for w in ["invest", "stock", "market", "roi", "return"]):
        return "Investor"
    if any(w in t for w in ["patient", "clinical", "diagnosis", "treatment", "nurse", "doctor"]):
        return "Healthcare Professional"
    if any(w in t for w in ["teach", "classroom", "students", "lesson"]):
        return "Teacher"
    return "General Public"


def _clean_topic(text):
    t = text.strip()
    t = re.sub(r"^(what is|what are|explain|tell me about|how does|how do|why is|why does|understand)\s+", "", t, flags=re.I)
    t = t.rstrip("?. ").strip()
    return t or text.strip()


async def _find_verified(topic):
    words = [w for w in re.split(r"\W+", topic) if len(w) > 3]
    query = {"verification_status": "Verified"}
    if words:
        pattern = "|".join(re.escape(w) for w in words[:4])
        query["$or"] = [{"title": {"$regex": pattern, "$options": "i"}},
                        {"category": {"$regex": pattern, "$options": "i"}},
                        {"verified_truth": {"$regex": pattern, "$options": "i"}}]
    kr = await db.knowledge_records.find_one(query)
    return kr


def _assemble_from_kr(kr):
    """Deterministically build the 10-section output from a verified Knowledge Record."""
    truth = kr.get("verified_truth") or kr.get("qru_translation") or ""
    vocab = kr.get("key_vocabulary") or []
    if vocab and isinstance(vocab[0], dict):
        vocab = [{"term": v.get("term", ""), "definition": v.get("definition", "")} for v in vocab if v.get("term")]
    return {
        "simple_answer": kr.get("simple_answer") or (truth[:220] if truth else ""),
        "why_it_matters": kr.get("why_it_matters") or "Understanding this helps you make better everyday decisions.",
        "everyday_example": kr.get("real_world_example") or kr.get("story") or "",
        "visual_analogy": kr.get("everyday_analogy") or "",
        "qru_translation": kr.get("qru_translation") or kr.get("consumer_translation") or truth,
        "memory_sentence": kr.get("memory_sentence") or "",
        "key_vocabulary": vocab,
        "deep_roots": kr.get("deep_roots") or "",
        "source": "verified",
        "source_label": f"Verified Knowledge Record™ · {kr.get('kr_code','')}",
        "kr_id": kr.get("id"),
    }


def _from_ai(draft):
    return {
        "simple_answer": draft.get("simple_answer") or draft.get("the_question") or "",
        "why_it_matters": draft.get("why_it_matters", ""),
        "everyday_example": draft.get("real_world_example", ""),
        "visual_analogy": draft.get("everyday_analogy", ""),
        "qru_translation": draft.get("qru_translation", ""),
        "memory_sentence": draft.get("memory_sentence", ""),
        "key_vocabulary": draft.get("key_vocabulary", []),
        "deep_roots": draft.get("deep_roots", ""),
        "source": "ai_draft",
        "source_label": "AI-Generated Draft (not yet verified)",
    }


def _memory_optimize(out, audience):
    """Deterministic clarity pass — never blocks; records what was optimized."""
    notes = []
    if not out.get("memory_sentence") and out.get("simple_answer"):
        out["memory_sentence"] = out["simple_answer"].split(".")[0].strip() + "."
        notes.append("Generated a Memory Sentence™ from the simple answer.")
    out["audience"] = audience
    out["reading_guidance"] = AUDIENCES.get(audience, "")
    notes.append(f"Optimized for retention and the {audience} audience.")
    return notes


def _verify(out):
    required = ["simple_answer", "why_it_matters", "everyday_example", "visual_analogy",
                "qru_translation", "memory_sentence", "deep_roots"]
    missing = [k for k in required if not out.get(k)]
    checks = {
        "factual_grounding": "Verified Knowledge Record™" if out["source"] == "verified" else "AI draft — verification recommended",
        "completeness": f"{len(required) - len(missing)}/{len(required)} core sections present",
        "readability": "Clear" if out.get("simple_answer") and len(out["simple_answer"]) < 400 else "Review",
        "audience_appropriate": bool(out.get("audience")),
    }
    treasure = out["source"] == "verified" and not missing
    status = "Treasure Standard™ — Verified" if treasure else ("Verified content" if out["source"] == "verified" else "AI Draft — pending verification")
    return {"checks": checks, "missing_sections": missing, "treasure_standard": treasure, "verification_status": status}


async def run(user_input, audience=None, resume_from=None, context=None):
    """Run the pipeline; returns stages, result, or a precise per-stage error."""
    stages = []
    ctx = context or {}
    text = (user_input or "").strip()

    # 1) Intent Analyzer™
    if len(text) < 3:
        stages.append(_stage("Intent Analyzer™", "needs_input", "Please describe what you're curious about."))
        return {"ok": False, "stages": stages, "clarifying_question": "What would you like to understand today? Describe it in your own words.",
                "error": _err("Intent Analyzer™", "Input too short to determine intent.", "Intent Analyzer™"), "input": user_input}
    topic = _clean_topic(text)
    ctx["topic"] = topic
    stages.append(_stage("Intent Analyzer™", "done", f"Understanding goal: “{topic}”."))

    # 2) Audience Analyzer™
    aud = audience if audience in AUDIENCES else _detect_audience(text)
    ctx["audience"] = aud
    stages.append(_stage("Audience Analyzer™", "done", f"Audience: {aud}."))

    # 3) Knowledge Retrieval™
    kr = await _find_verified(topic)
    if kr:
        out = _assemble_from_kr(kr)
        stages.append(_stage("Knowledge Retrieval™", "done", f"Matched verified record {kr.get('kr_code','')}."))
    else:
        # No verified record → generate an AI draft (requires the AI provider).
        try:
            raw = await llm_generate(QRU_METHODOLOGY_SYSTEM, f"Topic to explain for a {aud} audience: {topic}", f"te-{abs(hash(topic))%99999}")
            draft = parse_json(raw) or {}
            if not draft:
                raise ValueError("empty draft")
            out = _from_ai(draft)
            stages.append(_stage("Knowledge Retrieval™", "done", "No verified record — generated an AI draft (clearly marked)."))
        except Exception as e:
            msg = str(e)
            if "spend limit" in msg.lower():
                reason = "AI provider quota exceeded — the daily spend limit has been reached. Try a topic QRU has already verified, or retry after the limit resets."
            elif "Budget" in msg:
                reason = "AI provider budget exceeded — add balance, then retry from this stage."
            elif "503" in msg or "unavailable" in msg:
                reason = "AI provider temporarily unavailable — please retry from this stage in a moment."
            else:
                reason = f"AI provider error: {msg[:140]}"
            stages.append(_stage("Knowledge Retrieval™", "failed", reason))
            return {"ok": False, "stages": stages, "error": _err("Knowledge Retrieval™", reason, "Knowledge Retrieval™"),
                    "input": user_input, "context": ctx}

    # 4) QRU Translation Engine™ (assembly into QRU format)
    stages.append(_stage("QRU Translation Engine™", "done", "Assembled into the QRU educational format."))

    # 5) Memory Engineering™
    notes = _memory_optimize(out, aud)
    stages.append(_stage("Memory Engineering™", "done", "; ".join(notes)))

    # 6) Verification Lion™
    v = _verify(out)
    out.update({"verification_status": v["verification_status"], "verification_checks": v["checks"],
                "treasure_standard": v["treasure_standard"]})
    stages.append(_stage("Verification Lion™", "done", v["verification_status"]))

    # 7) Treasure Standard™ Output
    out["suggested_next_question"] = f"What is one way {topic} affects daily life?"
    stages.append(_stage("Treasure Standard™ Output", "done", "Customer-ready explanation produced."))

    return {"ok": True, "stages": stages, "result": out, "topic": topic, "audience": aud,
            "verified": out["source"] == "verified"}
