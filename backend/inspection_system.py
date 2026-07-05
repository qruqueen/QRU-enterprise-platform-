"""QRU Manufacturing Inspection System™ (MO-001 / Priority P4) — deterministic ($0 AI).

The permanent quality authority of the factory. Before any product is manufactured or
published, it must pass objective Quality Gates. Nothing proceeds automatically if
Treasure Standard™ requirements are not met — manufacturing PAUSES and the system produces
a Manufacturing Director report describing exactly what is missing.

Purely deterministic: computed from existing product / Knowledge Record data. No LLM budget
is ever spent. Reuses Factory Confidence™ / Data Health™ primitives.
"""
import factory_confidence as fc

MIN_KR_CHARS = 400          # a manufacturable Knowledge Record needs real substance
MIN_PRODUCT_CHARS = 180

PASS = 70                   # default gate threshold
TREASURE_PASS = 90          # Treasure Standard™ threshold

# Gate registry — order = display order. `blocking` gates PAUSE manufacturing when failed.
GATES = [
    {"key": "knowledge_completeness", "label": "Knowledge Completeness", "threshold": PASS, "blocking": True},
    {"key": "verification_completeness", "label": "Verification Completeness", "threshold": PASS, "blocking": True},
    {"key": "educational_value", "label": "Educational Value", "threshold": PASS, "blocking": False},
    {"key": "consumer_clarity", "label": "Consumer Clarity", "threshold": PASS, "blocking": False},
    {"key": "visual_readiness", "label": "Visual Readiness", "threshold": PASS, "blocking": False},
    {"key": "product_eligibility", "label": "Product Eligibility", "threshold": PASS, "blocking": True},
    {"key": "connector_readiness", "label": "Connector Readiness", "threshold": PASS, "blocking": False},
    {"key": "publication_readiness", "label": "Publication Readiness", "threshold": PASS, "blocking": True},
    {"key": "treasure_standard", "label": "Treasure Standard™ Compliance", "threshold": TREASURE_PASS, "blocking": True},
]


def _kr_text(kr):
    keys = ("content", "summary", "executive_summary", "deep_explanation", "body",
            "verified_truth", "qru_translation", "deep_roots", "simple_answer",
            "why_it_matters", "real_world_example", "everyday_analogy", "the_question")
    parts = [kr.get(k, "") or "" for k in keys]
    return "\n".join(str(p) for p in parts)


# --------------------------------------------------------------------------- KR-level gates
def _g_knowledge_kr(kr):
    text = _kr_text(kr)
    n = len(text)
    findings = []
    if n == 0:
        findings.append("Knowledge Record has no written content yet.")
    elif n < MIN_KR_CHARS:
        findings.append(f"Knowledge Record content is thin ({n} chars; need ≥ {MIN_KR_CHARS}).")
    score = 100 if n >= MIN_KR_CHARS else round(min(n / MIN_KR_CHARS, 1) * 100)
    if not kr.get("references") and not kr.get("scientific_references"):
        findings.append("No references attached — add source citations for Treasure Standard™.")
        score = min(score, 85)
    return score, findings


def _g_verification_kr(kr):
    status = kr.get("verification_status", "")
    if status == "Verified":
        return 100, []
    return (30 if status else 0), [f"Knowledge Record is '{status or 'Unverified'}' — only Verified records may manufacture."]


def _g_eligibility_kr(kr, product_types, valid_recipes):
    findings = []
    valid = [p for p in (product_types or []) if p in valid_recipes]
    if not product_types:
        return 100, []  # eligibility of types is checked only when types are requested
    if not valid:
        findings.append("None of the requested product types match a known manufacturing recipe.")
        return 0, findings
    invalid = [p for p in product_types if p not in valid_recipes]
    if invalid:
        findings.append(f"Unknown product types skipped: {', '.join(invalid)}.")
    if not kr.get("title") or not kr.get("category"):
        findings.append("Knowledge Record is missing a title or category.")
        return 60, findings
    return 100, findings


# --------------------------------------------------------------------------- product-level gates
def _g_knowledge_product(p):
    content = p.get("content") or ""
    n = len(content)
    has_kr = bool(p.get("knowledge_record_id")) or bool(p.get("assembled"))
    findings = []
    if n < MIN_PRODUCT_CHARS and not has_kr:
        findings.append("Product has no manufactured content and no linked Knowledge Record.")
        return 0, findings
    score = 100 if n >= MIN_PRODUCT_CHARS else (70 if has_kr else 40)
    if n < MIN_PRODUCT_CHARS:
        findings.append("Content not yet fully manufactured from the Knowledge Record.")
    return score, findings


def _g_verification_product(p):
    if p.get("verified"):
        return 100, []
    return 30, ["Product Protection™ verification not complete."]


def _g_educational_value(p):
    content = p.get("content") or ""
    score = 40
    if len(content) >= MIN_PRODUCT_CHARS:
        score += 30
    if len(content) >= 1200:
        score += 15
    if p.get("product_type") or p.get("family"):
        score += 15
    findings = [] if score >= PASS else ["Add depth: structured sections, examples and takeaways strengthen educational value."]
    return min(score, 100), findings


def _g_consumer_clarity(p):
    findings = []
    score = 40
    if p.get("creative_brief") and p.get("creative_status") == "Reviewed":
        score += 35
    else:
        findings.append("Needs a reviewed Creative Studio™ brief for consumer-facing clarity.")
    if p.get("preview_url") or p.get("marketing_kit_ready"):
        score += 25
    else:
        findings.append("No preview / marketing kit for the buyer to evaluate.")
    return min(score, 100), findings


def _g_visual_readiness(p):
    findings = []
    ds = fc._design_score(p)
    design = ds if isinstance(ds, (int, float)) else 40
    has_cover = bool(p.get("cover_url"))
    score = round(design * 0.7 + (100 if has_cover else 30) * 0.3)
    if not has_cover:
        findings.append("No branded cover / key visual attached.")
    if not fc._design_passed(p):
        findings.append(f"Design Director™ score {ds if ds is not None else '—'} below publishing bar.")
    return min(score, 100), findings


def _g_product_eligibility(p):
    findings = []
    if not p.get("product_type"):
        findings.append("Product type not set.")
        return 40, findings
    recipe = fc._recipe_score(p)
    if recipe < PASS:
        findings.append("Does not yet comply with its product-type recipe.")
    return round(recipe), findings


def _g_connector_readiness(operational_count):
    # QRU Store™ (native) is always operational, so a product can always reach at least one destination.
    if operational_count > 0:
        return 100, []
    return 50, ["No operational publishing connector available."]


def _g_publication_readiness(p):
    publishable, blockers = fc.publish_gate(p)
    if publishable:
        return 100, []
    return max(20, 100 - len(blockers) * 20), blockers


def _g_treasure_standard(p):
    conf = fc.factory_confidence(p)
    findings = []
    if p.get("treasure_standard"):
        return 100, []
    findings.append(f"Treasure Standard™ not yet certified (Factory Confidence™ {conf['score']}).")
    return conf["score"], findings


def _assemble(rows):
    """rows: list of (key, score, findings). Returns full inspection report."""
    by_key = {k: (s, f) for k, s, f in rows}
    gates = []
    blockers, missing = [], []
    weighted, total_w = 0, 0
    for g in GATES:
        score, findings = by_key.get(g["key"], (0, ["Not evaluated."]))
        passed = score >= g["threshold"]
        w = 2 if g["blocking"] else 1
        weighted += score * w
        total_w += w
        gates.append({**g, "score": score, "passed": passed, "findings": findings})
        if not passed:
            missing.extend(findings)
            if g["blocking"]:
                blockers.append(f"{g['label']} ({score}/{g['threshold']})")
    overall = round(weighted / total_w) if total_w else 0
    manufacturing_allowed = len(blockers) == 0
    return {
        "overall_score": overall,
        "manufacturing_allowed": manufacturing_allowed,
        "status": "Cleared" if manufacturing_allowed else "Paused",
        "gates": gates,
        "blocking_failures": blockers,
        "director_report": {
            "verdict": "APPROVED — cleared to manufacture." if manufacturing_allowed
                       else "PAUSED — Treasure Standard™ requirements not met.",
            "missing_information": missing,
            "blocking_gates": blockers,
        },
    }


def inspect_product(p, operational_connectors=1):
    rows = [
        ("knowledge_completeness", *_g_knowledge_product(p)),
        ("verification_completeness", *_g_verification_product(p)),
        ("educational_value", *_g_educational_value(p)),
        ("consumer_clarity", *_g_consumer_clarity(p)),
        ("visual_readiness", *_g_visual_readiness(p)),
        ("product_eligibility", *_g_product_eligibility(p)),
        ("connector_readiness", *_g_connector_readiness(operational_connectors)),
        ("publication_readiness", *_g_publication_readiness(p)),
        ("treasure_standard", *_g_treasure_standard(p)),
    ]
    report = _assemble(rows)
    report["subject"] = {"type": "product", "id": p.get("id"), "code": p.get("product_code"),
                         "title": p.get("title"), "status": p.get("status")}
    return report


def inspect_kr_for_manufacture(kr, product_types, valid_recipes):
    """Pre-manufacture eligibility gate. Only the gates that can be judged from a Knowledge
    Record are evaluated as blocking; the rest are produced downstream per product."""
    k_score, k_find = _g_knowledge_kr(kr)
    v_score, v_find = _g_verification_kr(kr)
    e_score, e_find = _g_eligibility_kr(kr, product_types, valid_recipes)
    rows = [
        ("knowledge_completeness", k_score, k_find),
        ("verification_completeness", v_score, v_find),
        ("product_eligibility", e_score, e_find),
    ]
    # Only evaluate the three KR-judgeable blocking gates here.
    gates, blockers, missing, weighted, total_w = [], [], [], 0, 0
    for g in GATES:
        if g["key"] not in dict((k, 1) for k, _, _ in rows):
            continue
        score, findings = next((s, f) for k, s, f in rows if k == g["key"])
        passed = score >= g["threshold"]
        weighted += score; total_w += 1
        gates.append({**g, "score": score, "passed": passed, "findings": findings})
        if not passed:
            missing.extend(findings)
            blockers.append(f"{g['label']} ({score}/{g['threshold']})")
    allowed = len(blockers) == 0
    return {
        "overall_score": round(weighted / total_w) if total_w else 0,
        "manufacturing_allowed": allowed,
        "status": "Cleared" if allowed else "Paused",
        "gates": gates,
        "blocking_failures": blockers,
        "director_report": {
            "verdict": "APPROVED — Knowledge Record cleared to manufacture." if allowed
                       else "PAUSED — Knowledge Record does not meet manufacturing requirements.",
            "missing_information": missing,
            "blocking_gates": blockers,
        },
        "subject": {"type": "knowledge_record", "id": kr.get("id"),
                    "code": kr.get("kr_code"), "title": kr.get("title")},
    }
