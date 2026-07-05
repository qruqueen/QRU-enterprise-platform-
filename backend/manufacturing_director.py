"""QRU Manufacturing Director™ (MO-005) — supervisory review of manufacturing orders.

The Director reviews every manufacturing order BEFORE production and issues one of four
verdicts: APPROVE, APPROVE_WITH_CONDITIONS, HOLD, REJECT. It identifies exactly which
Knowledge Record sections are missing for the requested products and prescribes the next
actions.

Treasure Standard™ / Knowledge-First: the DECISION is always DETERMINISTIC and evidence-based.
The optional LLM layer only writes a human-readable executive brief — it can NEVER change the
verdict or invent knowledge. When the AI budget is capped, a deterministic brief is used
($0 AI fallback), and the Director keeps operating with zero loss of authority.
"""
import logging

from database import db
import inspection_system as insp
import knowledge_record_v2 as kr2

logger = logging.getLogger("qru.director")

# Verdicts (ordered by severity)
APPROVE = "APPROVE"
APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"
HOLD = "HOLD"
REJECT = "REJECT"

VERDICT_LABEL = {
    APPROVE: "Approved — cleared to manufacture.",
    APPROVE_WITH_CONDITIONS: "Approved with conditions — manufacture, but address the noted gaps.",
    HOLD: "On Hold — required knowledge is missing. Fill it before manufacturing.",
    REJECT: "Rejected — no verified knowledge foundation to manufacture from.",
}

# Which order status the Director recommends for each verdict.
VERDICT_TO_STATUS = {
    APPROVE: "Research",
    APPROVE_WITH_CONDITIONS: "Research",
    HOLD: "Queued",
    REJECT: "Queued",
}


_STOPWORDS = {"the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "how", "what",
              "why", "you", "your", "with", "from", "into", "much", "need", "start", "safely",
              "is", "are", "it", "this", "that", "guide", "lesson", "course", "intro",
              "introduction", "basics", "understanding", "overview"}


def _words(text):
    import re
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
            if len(w) > 2 and w not in _STOPWORDS}


async def _find_kr(order):
    """Resolve the Knowledge Record backing an order — by explicit id, else keyword overlap on topic."""
    kr_id = order.get("knowledge_record_id")
    if kr_id:
        kr = await db.knowledge_records.find_one({"id": kr_id})
        if kr:
            return kr, "linked"
    topic_words = _words(order.get("topic"))
    if not topic_words:
        return None, "none"
    best_id, best_score = None, 0.0
    candidates = await db.knowledge_records.find({}, {"id": 1, "title": 1}).to_list(500)
    for c in candidates:
        tw = _words(c.get("title"))
        if not tw:
            continue
        overlap = len(topic_words & tw) / len(tw)
        if overlap > best_score:
            best_score, best_id = overlap, c.get("id")
    if best_id and best_score >= 0.5:
        full = await db.knowledge_records.find_one({"id": best_id})
        if full:
            return full, "matched_by_topic"
    return None, "none"


def _kr_has_any_content(kr):
    if not kr:
        return False
    if insp._kr_text(kr).strip():
        return True
    sections = kr.get("sections_v2") or {}
    return any((s or {}).get("content") for s in sections.values())


def _review_readiness(kr, product_types):
    """Per-product-type section readiness + aggregated missing knowledge."""
    by_product = []
    missing_index = {}  # section title -> set(product types needing it)
    for pt in (product_types or []):
        r = kr2.manufacturing_readiness(kr, pt)
        by_product.append({
            "product_type": pt,
            "required": r["required"],
            "ready_sections": r["ready_sections"],
            "missing_sections": r["missing_sections"],
            "manufacturing_allowed": r["manufacturing_allowed"],
        })
        for m in r["missing_sections"]:
            missing_index.setdefault(m, set()).add(pt)
    missing_knowledge = [
        {"section": title, "needed_by": sorted(products), "action": f"Fill '{title}' in Knowledge Architecture™"}
        for title, products in sorted(missing_index.items())
    ]
    return by_product, missing_knowledge


def _decide(kr, kr_source, gate, by_product, missing_knowledge):
    """Deterministic verdict — the single source of Director authority."""
    if kr is None:
        return REJECT, ["No Knowledge Record is linked to this order and none matched the topic."]
    if not _kr_has_any_content(kr):
        return REJECT, ["The Knowledge Record has no written content to manufacture from."]

    reasons = []
    verification = kr.get("verification_status", "Unverified")
    blocking = gate.get("blocking_failures", [])

    if blocking:
        reasons.append(f"Blocking Quality Gate(s) failed: {', '.join(blocking)}.")
    if missing_knowledge:
        reasons.append(f"{len(missing_knowledge)} required knowledge section(s) are missing for the requested products.")

    # HOLD when knowledge is missing or a blocking gate fails (the KR has content, so it is fillable).
    if blocking or missing_knowledge:
        return HOLD, reasons

    # Everything required is present. Distinguish full approval from conditional.
    if verification == "Verified":
        return APPROVE, ["All required knowledge sections are ready and the Knowledge Record is Verified."]
    reasons.append(f"Knowledge Record verification is '{verification}' (not fully Verified) — proceed but complete verification.")
    if kr_source == "matched_by_topic":
        reasons.append("Knowledge Record was matched by topic, not explicitly linked — confirm it is the correct source.")
    return APPROVE_WITH_CONDITIONS, reasons


def _confidence(gate, by_product):
    base = gate.get("overall_score", 0)
    if by_product:
        ready = sum(len(p["ready_sections"]) for p in by_product)
        req = sum(len(p["required"]) for p in by_product) or 1
        ratio = ready / req
        return round(base * 0.5 + ratio * 100 * 0.5)
    return base


def _recommended_actions(verdict, missing_knowledge, gate):
    actions = []
    if verdict == REJECT:
        actions.append({"label": "Link or create a verified Knowledge Record for this topic", "link": "/kr2"})
        return actions
    for m in missing_knowledge[:8]:
        actions.append({"label": f"Fill '{m['section']}' (needed by: {', '.join(m['needed_by'])})", "link": "/kr2"})
    for b in gate.get("blocking_failures", []):
        if "Verification" in b:
            actions.append({"label": "Complete verification for this Knowledge Record", "link": "/verification"})
    if verdict in (APPROVE, APPROVE_WITH_CONDITIONS):
        actions.append({"label": "Advance order to Research & begin manufacturing", "link": "/manufacturing"})
    return actions


def _deterministic_brief(order, verdict, reasons, missing_knowledge, confidence):
    topic = order.get("topic", "this topic")
    n = len(order.get("product_types") or [])
    head = {
        APPROVE: f"The knowledge foundation for “{topic}” is verified and complete for all {n} requested product(s). Manufacturing is cleared to proceed.",
        APPROVE_WITH_CONDITIONS: f"“{topic}” can enter manufacturing, but the Director notes conditions that should be resolved in parallel.",
        HOLD: f"Manufacturing of “{topic}” is held: the Knowledge Record is missing required sections for the requested products.",
        REJECT: f"“{topic}” cannot be manufactured — there is no verified knowledge foundation to build from.",
    }[verdict]
    tail = ""
    if missing_knowledge:
        titles = ", ".join(m["section"] for m in missing_knowledge[:4])
        tail = f" Missing knowledge: {titles}{'…' if len(missing_knowledge) > 4 else ''}."
    return f"{head}{tail} Director confidence: {confidence}%. (Deterministic review — $0 AI.)"


async def _ai_brief(order, verdict, reasons, missing_knowledge, confidence):
    """Optional LLM executive brief. Verdict is NEVER derived from this — narrative only."""
    try:
        import ai_service
        if not ai_service.EMERGENT_LLM_KEY:
            return None, "deterministic"
        system = (
            "You are the QRU Manufacturing Director™. You write a concise executive brief for the Founder "
            "explaining a manufacturing decision that has ALREADY been made deterministically. "
            "Never change the verdict, never invent facts, never claim knowledge exists that is listed as missing. "
            "3 sentences maximum, professional and direct."
        )
        prompt = (
            f"Order topic: {order.get('topic')}\n"
            f"Requested products: {', '.join(order.get('product_types') or []) or 'none'}\n"
            f"VERDICT (fixed): {verdict}\n"
            f"Reasons: {'; '.join(reasons) or 'none'}\n"
            f"Missing knowledge sections: {', '.join(m['section'] for m in missing_knowledge) or 'none'}\n"
            f"Confidence: {confidence}%\n"
            "Write the executive brief."
        )
        text = await ai_service.llm_generate(system, prompt, session_id=f"director-{order.get('id')}")
        return (text or "").strip() or None, "ai"
    except Exception as e:
        logger.info(f"Director AI brief unavailable, using deterministic fallback: {str(e)[:80]}")
        return None, "deterministic"


async def review_order(order, use_ai=False):
    """Full Director review of a single manufacturing order."""
    import product_automation as pa
    kr, kr_source = await _find_kr(order)
    product_types = order.get("product_types") or []

    if kr:
        gate = insp.inspect_kr_for_manufacture(kr, None, getattr(pa, "RECIPES", {}))
        by_product, missing_knowledge = _review_readiness(kr, product_types)
    else:
        gate = {"overall_score": 0, "manufacturing_allowed": False, "blocking_failures": ["No Knowledge Record"],
                "gates": [], "director_report": {"missing_information": ["No Knowledge Record linked."]}}
        by_product, missing_knowledge = [], []

    verdict, reasons = _decide(kr, kr_source, gate, by_product, missing_knowledge)
    confidence = _confidence(gate, by_product)
    actions = _recommended_actions(verdict, missing_knowledge, gate)

    brief, brief_source = None, "deterministic"
    if use_ai:
        brief, brief_source = await _ai_brief(order, verdict, reasons, missing_knowledge, confidence)
    if not brief:
        brief = _deterministic_brief(order, verdict, reasons, missing_knowledge, confidence)

    return {
        "order_id": order.get("id"),
        "mo_code": order.get("mo_code"),
        "topic": order.get("topic"),
        "product_types": product_types,
        "current_status": order.get("status"),
        "knowledge_record": ({"id": kr.get("id"), "kr_code": kr.get("kr_code"), "title": kr.get("title"),
                              "verification_status": kr.get("verification_status", "Unverified"),
                              "source": kr_source} if kr else None),
        "verdict": verdict,
        "verdict_label": VERDICT_LABEL[verdict],
        "recommended_status": VERDICT_TO_STATUS[verdict],
        "confidence": confidence,
        "reasons": reasons,
        "knowledge_gate": {
            "overall_score": gate.get("overall_score", 0),
            "blocking_failures": gate.get("blocking_failures", []),
            "gates": gate.get("gates", []),
        },
        "readiness_by_product": by_product,
        "missing_knowledge": missing_knowledge,
        "recommended_actions": actions,
        "executive_brief": brief,
        "brief_source": brief_source,
    }


async def review_queue():
    """Fast deterministic verdicts for every order (no AI) for the Director queue view."""
    orders = await db.manufacturing_orders.find().sort("created_at", -1).to_list(500)
    rows, counts = [], {APPROVE: 0, APPROVE_WITH_CONDITIONS: 0, HOLD: 0, REJECT: 0}
    for o in orders:
        r = await review_order(o, use_ai=False)
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        rows.append({
            "order_id": r["order_id"], "mo_code": r["mo_code"], "topic": r["topic"],
            "product_types": r["product_types"], "current_status": r["current_status"],
            "verdict": r["verdict"], "verdict_label": r["verdict_label"],
            "recommended_status": r["recommended_status"], "confidence": r["confidence"],
            "missing_count": len(r["missing_knowledge"]),
            "kr_code": (r["knowledge_record"] or {}).get("kr_code"),
        })
    return {
        "total": len(orders),
        "counts": counts,
        "cleared": counts[APPROVE] + counts[APPROVE_WITH_CONDITIONS],
        "held": counts[HOLD] + counts[REJECT],
        "orders": rows,
    }
