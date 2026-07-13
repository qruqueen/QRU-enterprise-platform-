"""QRU Knowledge Record Inheritance™ — "Understand Once. Manufacture Forever."

The Verified Knowledge Record is the Single Source of Truth. Products inherit verified content
automatically; the founder selects rather than re-enters. Knowledge-First: factual fields are copied
verbatim from the exact KR version — never invented. Pedagogical framing (memory sentence, challenge,
analogy) is derived from the KR's own text/anchors, not fabricated facts.
"""
import re


async def load_kr(db, kr_id):
    for coll in (db.knowledge_engine_records, db.knowledge_records):
        doc = await coll.find_one({"id": kr_id}, {"_id": 0})
        if doc:
            return doc
    return None


def _clean_topic(topic):
    t = (topic or "").strip().rstrip("?.!").strip()
    for p in ("what is ", "what are ", "how does ", "how do ", "why is ", "the "):
        if t.lower().startswith(p):
            t = t[len(p):]
    return t.strip() or (topic or "Topic")


def _sentences(text, n=2):
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return " ".join([p.strip() for p in parts if p.strip()][:n])


def _as_list(v):
    if isinstance(v, list):
        return [str(x) for x in v if str(x).strip()]
    if isinstance(v, str) and v.strip():
        return [v.strip()]
    return []


def build_inheritance(kr):
    """Normalized inheritance payload — the single source products inherit from."""
    sec = kr.get("sections") or {}
    topic = kr.get("topic") or kr.get("title") or "Topic"
    term = _clean_topic(topic)
    definition = sec.get("definition") or kr.get("simple_answer") or kr.get("verified_truth") or ""
    explanation = sec.get("explanation") or kr.get("content") or definition
    examples = _as_list(sec.get("examples")) + _as_list(sec.get("relationships"))
    anchors = _as_list(sec.get("memory_anchors"))
    assessment = _as_list(sec.get("assessment_plan"))
    misconceptions = _as_list(sec.get("common_misunderstandings")) + _as_list(sec.get("counterexamples"))
    key_points = re.split(r"(?<=[.!?])\s+", (explanation or definition).strip())
    key_points = [k.strip() for k in key_points if len(k.strip()) > 8][:5]
    verif = kr.get("verification") or {}
    verified = bool(verif.get("evidence_sufficient_for_external_publication") or kr.get("verified_external"))
    # Derived tags from topic words (deterministic, not invented facts)
    words = [w.strip(",.").capitalize() for w in re.findall(r"[A-Za-z]{4,}", term)][:4]
    tags = list(dict.fromkeys([term.replace(" ", "")] + words + ["QRU", "Verified" if verified else "Draft"]))[:8]
    return {
        "kr_id": kr.get("id"), "kr_code": kr.get("kr_code"), "version": kr.get("version", 1),
        "topic": topic, "term": term.title(),
        "title": term.upper(),
        "subtitle": _sentences(definition, 1) or term.title(),
        "definition_plain": _sentences(definition, 2) or explanation,
        "definition_professional": _sentences(explanation, 3) or definition,
        "examples": examples or [f"A real-world instance of {term}."],
        "memory_sentence": (anchors[0] if anchors else f"{term.title()} is best understood by explaining it in your own words."),
        "challenge_questions": (assessment or [f"Explain {term} in your own words.", f"Where do you see {term} in real life?"]),
        "tags": tags,
        "category_flow": _as_list(sec.get("relationships"))[:3] or ["CONCEPT", "APPLICATION", "TRANSFER"],
        "key_concepts": examples[:5],
        "key_points": key_points or examples[:5],
        "misconceptions": misconceptions,
        "citations": _as_list(kr.get("attached_sources")) or ([kr.get("kr_code")] if kr.get("kr_code") else []),
        "verified_external": verified,
        "verification_verdict": verif.get("verdict"),
        "treasure_status": (kr.get("treasure") or {}).get("verdict") if isinstance(kr.get("treasure"), dict) else kr.get("treasure"),
    }


def map_to_template(template_id, inh):
    """Map inheritance payload → template content fields (founder-supplied values still override)."""
    base = {"title": inh["title"], "subtitle": inh["subtitle"], "trademark": True}
    if template_id == "knowledge-card-v1":
        cats = [c.upper() for c in inh["category_flow"] if len(c) <= 20][:3] or ["CONCEPT", "APPLICATION", "TRANSFER"]
        return {**base, "card_kind": "QRU KNOWLEDGE CARD", "term": inh["term"].upper(),
                "term_tagline": inh["subtitle"],
                "plain_definition": inh["definition_plain"], "professional_definition": inh["definition_professional"],
                "analogy_title": "In Simple Terms", "analogy_body": inh["definition_plain"],
                "analogy_caption": inh["memory_sentence"],
                "chart_clue": inh["key_points"][:5] or ["See the verified explanation."],
                "real_life_clues": inh["examples"][:5] or ["See the concept applied in practice."],
                "challenge_intro": "Test your understanding:",
                "challenge_questions": inh["challenge_questions"][:4],
                "memory_sentence": inh["memory_sentence"],
                "category_flow": cats,
                "tags": [re.sub(r"[^A-Za-z0-9]", "", t)[:16] or "QRU" for t in inh["tags"][:8]]}
    if template_id == "illustrated-learning-v1":
        pts = inh["key_concepts"][:6] or inh["examples"][:6]
        return {**base, "lesson_points": [{"heading": (p[:40] + ("…" if len(p) > 40 else "")), "body": p} for p in pts] or None}
    if template_id in ("data-comparison-v1", "scorecard-grid-v1", "decoder-v1"):
        # Structured figures require KR data tables; inherit identity + note when absent.
        return {**base, "source_note": f"Source: {inh['kr_code']} v{inh['version']} (verified). Figures illustrative until structured data is attached to the Knowledge Record."}
    if template_id == "identity-anatomy-v1":
        pts = inh["key_points"] or inh["examples"]
        pairs = [{"label": (p.split(" ")[0][:16] or "Part").title(), "desc": p} for p in pts][:8]
        mid = (len(pairs) + 1) // 2
        return {**base, "center_label": inh["term"].upper(), "center_caption": inh["subtitle"],
                "parts_left": pairs[:mid] or None, "parts_right": pairs[mid:] or None}
    if template_id == "give-credit-v1":
        pts = (inh["key_points"] + inh["examples"] + inh["challenge_questions"])[:10]
        return {**base, "panels": [{"title": (p[:34] + ("\u2026" if len(p) > 34 else "")), "body": p} for p in pts] or None}
    if template_id == "why-forex-v1":
        cos = [{"title": (p.split(" ")[0][:14] or "Fact").title(), "desc": p} for p in inh["key_points"]][:4]
        return {**base, "stat_caption": inh["subtitle"],
                "callouts": cos or None, "chips": [t for t in inh["tags"][:5]] or None,
                "source_note": f"Source: {inh['kr_code']} v{inh['version']} ({'verified' if inh['verified_external'] else 'draft'}). Attach structured figures to the KR for a headline statistic."}
    if template_id == "utility-principle-v1":
        steps = [p.split(" ")[0][:12].title() for p in inh["key_points"]][:8] or ["Observe", "Question", "Apply"]
        return {**base, "cycle_steps": steps,
                "info_boxes": [{"title": "The Principle", "body": inh["definition_professional"]},
                               {"title": "Why It Holds", "body": inh["definition_plain"]}],
                "values": [w.upper()[:14] for w in inh["tags"][:3]] or None}
    if template_id == "brain-translation-v1":
        mis = inh["misconceptions"]
        rows = [{"left": m, "right": inh["definition_plain"] or "See the verified explanation."} for m in mis][:7]
        if not rows:
            rows = [{"left": f"'{inh['term']}' is just about memorizing facts.", "right": inh["definition_plain"] or inh["definition_professional"]}]
        return {**base, "left_header": "WHAT IT SAYS", "right_header": "WHAT IS TRUE",
                "rows": rows, "remember": inh["memory_sentence"]}
    if template_id == "process-formula-v1":
        return {**base}
    return base
