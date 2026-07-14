"""QRU Decoder Engine™ v2.0 (Stone 1) — transform governed KNOWLEDGE into governed UNDERSTANDING.

One responsibility, one owner. Inherits (never replaces) Knowledge Records™, ai_service,
verification_engine, org_activity. Produces a versioned 38-field QRU Decoder Record™ into
`decoder_records`, with a Decoder Scorecard™ (deterministic + AI-advisory, never auto-truth),
Educational Design Rationale (auditable, not hidden chain-of-thought), Enterprise Shelving, and
the Founder Review Shelf™ review lifecycle. Canonical → (future) audience-variant capable.
"""
import logging
from database import db
from models import gen_id, now_iso, clean
from ai_service import llm_generate, parse_json
from media_division import _resolve_kr, _is_verified
from org_activity import log_org
import product_governance

logger = logging.getLogger("qru.decoder")
COLL = "decoder_records"

# Governed lifecycle (§6 of authorization). Treasure Standard™ is earned separately, never auto.
REVIEW_STATES = ["Draft", "Automated Quality Review", "Verification Review", "Educational Review",
                 "Accessibility Review", "Brand Review", "Manufacturing Ready", "Revision Recommended",
                 "Founder Approved", "Treasure Standard Candidate", "Treasure Standard Certified",
                 "Published", "Superseded", "Archived"]

# Governed shelving taxonomy (§27). Founder-authorized additions only.
DOMAINS = ["AI Literacy", "Finance", "Trading", "Health", "Human Capability", "Emotions", "Life Skills",
           "Science", "Technology", "Leadership", "Faith and Philosophy", "Children", "Little Legacy Learners™", "General"]
HIGH_STAKES = ["medical", "medicine", "health", "legal", "law", "financial", "finance", "invest", "trading",
               "forex", "currency", "stock", "crypto", "gambling", "tax",
               "mental health", "safety", "child", "diagnos", "treatment", "dosage", "suicide"]
OVERPROMISE = ["a-z", "a to z", "complete guide", "comprehensive", "everything", "encyclopedia", "mastery", "ultimate", "all you need"]

CONTRACT_FIELDS = [  # the 38-field output contract order (§22)
    "title", "artifact_type", "purpose", "governance_banner", "decoder_id", "source_kr_ids", "decoder_version",
    "domain", "subdomain", "audience", "level", "learning_objective", "confidence_status", "definition",
    "why_it_matters", "how_it_works", "core_mental_model", "analogy", "analogy_mapping", "analogy_limitations",
    "story", "visual_spec", "vocabulary", "misconceptions", "applications", "guided_example", "practice",
    "reflection", "memory_anchor", "verification", "understanding_checks", "next_understanding",
    "downstream_notes", "accessibility_notes", "safety_notes", "provenance", "inheritance", "review_history",
]

GEN_SYSTEM = (
    "You are the QRU Decoder Engine™. Transform the governed, verified knowledge below into governed UNDERSTANDING. "
    "Optimize for Understanding, not Complexity. Truth before presentation. Accuracy before analogy. Use ONLY the "
    "verified knowledge provided — never invent facts; preserve its confidence, limitations and uncertainty. "
    "Establish ONE primary mental model and keep the definition, analogy, story, visual and memory anchor all "
    "consistent with it. Return STRICT JSON (no markdown fences) with keys: "
    "title (concept-first, human-readable), purpose (one sentence), definition, why_it_matters, how_it_works, "
    "core_mental_model, analogy, analogy_mapping, analogy_limitations, story, "
    "visual_spec (object: purpose, primary_subject, relationship, composition, labels[], must_not_appear[], alt_text), "
    "vocabulary (array of {term, definition}), misconceptions (array of {misconception, why_wrong}), "
    "applications (array of strings), guided_example, practice, reflection, "
    "memory_anchor (ONE accurate sentence), verification (how the knowledge is supported + what's uncertain), "
    "understanding_checks (object: explain, recognize, apply, correct, teach — one prompt each), "
    "next_understanding, downstream_notes, accessibility_notes, "
    "rationale (object: mental_model_choice, analogy_intent, analogy_preferred_why, rejected_analogy_risks, "
    "analogy_stops_when, story_choice, example_choice, visual_teaches, memory_anchor_accuracy, accessibility_decisions). "
    "The rationale is reviewable educational documentation — concise, no hidden reasoning."
)


def _now():
    return now_iso()


def _classify(kr, gen):
    text = f"{kr.get('title','')} {kr.get('category','')} {gen.get('domain','')}".lower()
    domain = next((d for d in DOMAINS if d.lower() in text), None) or (kr.get("category") if kr.get("category") in DOMAINS else "General")
    return domain


def _deterministic_checks(kr, gen, audience, level):
    title = (gen.get("title") or "").lower()
    words = len((gen.get("how_it_works", "") + " " + gen.get("definition", "")).split())
    has_all = all(gen.get(k) for k in ["definition", "why_it_matters", "how_it_works", "core_mental_model",
                                       "analogy", "story", "memory_anchor", "understanding_checks"])
    uc = gen.get("understanding_checks") or {}
    five = all(uc.get(k) for k in ["explain", "recognize", "apply", "correct", "teach"])
    overpromise = any(k in title for k in OVERPROMISE) and len(kr_ids_of(kr)) <= 1
    high_stakes = any(k in f"{kr.get('title','')} {kr.get('category','')}".lower() for k in HIGH_STAKES)
    mem = str(gen.get("memory_anchor", "")).strip()
    return {
        "checks": [
            {"item": "All required Decoder components present", "pass": has_all, "type": "deterministic"},
            {"item": "Five-part Understanding Test present (explain/recognize/apply/correct/teach)", "pass": five, "type": "deterministic"},
            {"item": "Memory Anchor™ is a single concise sentence", "pass": 4 <= len(mem.split()) <= 40, "type": "deterministic"},
            {"item": "Analogy states its limitation (no false equivalence)", "pass": bool(str(gen.get("analogy_limitations", "")).strip()), "type": "deterministic"},
            {"item": "Provenance attached (source KR + version)", "pass": bool(kr.get("id")), "type": "deterministic"},
            {"item": "Title does not overpromise scope vs. available knowledge", "pass": not overpromise, "type": "deterministic"},
        ],
        "high_stakes": high_stakes,
        "overpromise": overpromise,
    }


def kr_ids_of(kr):
    return [kr.get("id")]


ADVISORY_SYSTEM = (
    "You are a QRU educational quality reviewer. Given the SOURCE verified knowledge and a DECODER draft, score "
    "each dimension 0-100 and note risks. Do NOT be generous; flag distortion. Return STRICT JSON: "
    "{source_fidelity, truth_accuracy, confidence_preservation, mental_model_consistency, plain_language_clarity, "
    "analogy_quality, analogy_distortion_risk, story_quality, understanding_test_coverage, cognitive_load, "
    "understanding_density, misconception_prevention, notes}. analogy_distortion_risk and cognitive_load are RISK "
    "scores where LOWER is better. 'notes' is a short reviewer comment."
)


async def _advisory(kr, gen):
    src = f"SOURCE: {kr.get('title')} — {kr.get('verified_truth','')}"
    draft = (f"DECODER definition: {gen.get('definition','')}\nmental_model: {gen.get('core_mental_model','')}\n"
             f"analogy: {gen.get('analogy','')}\nstory: {gen.get('story','')}\nmemory_anchor: {gen.get('memory_anchor','')}")
    try:
        r = parse_json(await llm_generate(ADVISORY_SYSTEM, f"{src}\n\n{draft}", f"decoder-adv-{gen.get('decoder_id','x')}")) or {}
    except Exception as e:
        logger.warning(f"advisory unavailable: {e}")
        r = {}
    return r


def _scorecard(det, adv):
    def row(name, value, etype):
        return {"dimension": name, "score": value, "evaluator": etype, "status": "advisory" if etype == "AI-assisted advisory" else "pass" if value else "review"}
    det_pass = {c["item"]: c["pass"] for c in det["checks"]}
    rows = [row(c["item"], c["pass"], "deterministic") for c in det["checks"]]
    for k, label in [("source_fidelity", "Source Fidelity"), ("truth_accuracy", "Truth and Accuracy"),
                     ("confidence_preservation", "Confidence Preservation"), ("mental_model_consistency", "Core Mental Model Consistency"),
                     ("plain_language_clarity", "Plain-Language Clarity"), ("analogy_quality", "Analogy Quality"),
                     ("analogy_distortion_risk", "Analogy Distortion Risk (lower=better)"), ("story_quality", "Story Quality"),
                     ("understanding_test_coverage", "Five-Part Understanding Test Coverage"), ("cognitive_load", "Cognitive Load (lower=better)"),
                     ("understanding_density", "Understanding Density™"), ("misconception_prevention", "Misconception Prevention")]:
        rows.append(row(label, adv.get(k), "AI-assisted advisory"))
    deterministic_ok = all(det_pass.values())
    return {"rows": rows, "deterministic_ok": deterministic_ok, "advisory_notes": adv.get("notes", ""),
            "model_note": "Advisory scores are AI-assisted and support—never replace—Founder judgment."}


def _kr_context(kr, audience, level):
    """Schema-aware source context — supports legacy KR (flat fields) and KR 2.0 (sections dict)."""
    def _fmt(v):
        if isinstance(v, (list, tuple)):
            return "; ".join(str(x) for x in v)
        if isinstance(v, dict):
            return "; ".join(f"{k}: {x}" for k, x in v.items())
        return str(v or "")
    head = (f"Title: {kr.get('title')}\nDomain: {kr.get('category') or kr.get('recipe') or ''}\n"
            f"Audience: {audience or 'General learner'}\nLevel: {level or 'Introductory'}\n")
    sections = kr.get("sections")
    if isinstance(sections, dict) and sections:  # KR 2.0 (knowledge_engine_records)
        body = "".join(f"{k.replace('_', ' ').title()}: {_fmt(v)}\n" for k, v in sections.items() if v)
        conf = _fmt(kr.get("confidence_profile"))
        return head + body + (f"Confidence Profile: {conf}\n" if conf else "") + \
            f"Verification: {_fmt(kr.get('verification'))}\n"
    # legacy KR
    return head + (
        f"Verified Truth: {kr.get('verified_truth','')}\n"
        f"Why It Matters: {kr.get('why_it_matters','')}\nHow/Analogy: {kr.get('everyday_analogy','')}\n"
        f"Example: {kr.get('real_world_example','')}\nMemory: {kr.get('memory_sentence','')}\n"
        f"Confidence: {kr.get('confidence_score','')}")


def _confidence_summary(gen, det):
    """Factory Confidence Summary™ — the standard PASS/HOLD summary. Honest: only gates the
    Understanding Engine actually evaluates are scored; downstream gates are marked PENDING."""
    det_ok = all(c["pass"] for c in det["checks"])
    constitution_ok = det_ok and not det["overpromise"]
    verification_ok = bool(gen.get("verification"))
    treasure_candidate = det_ok and constitution_ok and verification_ok

    def row(gate, status, detail, owner="Factory"):
        return {"gate": gate, "status": status, "detail": detail, "owner": owner}

    rows = [
        row("Knowledge", "PASS", "Inherits a Verified Knowledge Record™ (Knowledge-First)."),
        row("Verification", "PASS" if verification_ok else "HOLD", "Source support & uncertainty carried into the Decoder."),
        row("Decoder", "PASS" if det_ok else "HOLD", "38-field contract, 5-part Understanding Test, honest analogy."),
        row("Treasure Candidate", "PASS" if treasure_candidate else "HOLD",
            "All governed standards passed — candidate for Founder certification." if treasure_candidate else "Not yet a candidate."),
        row("Constitution", "PASS" if constitution_ok else "HOLD", "Knowledge-First, no overpromise, provenance attached."),
        row("Recipe", "PENDING", "Evaluated at product manufacturing.", "Product Engine"),
        row("Engineering", "PENDING", "Evaluated at product manufacturing.", "Product Engine"),
        row("Architecture", "PENDING", "Evaluated at product manufacturing.", "Product Engine"),
    ]
    all_governed_pass = det_ok and constitution_ok and verification_ok
    return rows, all_governed_pass, treasure_candidate


def _autonomy_decision(det, all_governed_pass):
    """Constitutional Autonomy Rule: the Factory autonomously executes every decision governed by
    established standards. Only genuine human/expert judgment leaves the Factory (as a recommendation)."""
    if all_governed_pass:
        if det["high_stakes"]:
            return {"state": "Manufacturing Ready",
                    "recommendation": "MANUFACTURING READY · Expert Review Recommended",
                    "human_review_recommended": True,
                    "review_recommendation": "High-stakes domain — the Factory recommends qualified expert review before publication. Ownership has still transferred to the Product Manufacturing Engine."}
        return {"state": "Manufacturing Ready", "recommendation": "MANUFACTURING READY",
                "human_review_recommended": False, "review_recommendation": ""}
    return {"state": "Revision Recommended", "recommendation": "REVISION RECOMMENDED",
            "human_review_recommended": True,
            "review_recommendation": "One or more governed standards did not pass — the Factory recommends revision before manufacturing."}


async def decode(kr_id, audience, level, actor):
    kr = await _resolve_kr(kr_id)
    if not kr:
        return {"ok": False, "flag": "Source Record Incomplete", "error": "Knowledge Record not found."}
    if not _is_verified(kr):
        return {"ok": False, "flag": "Verification Required",
                "error": "This Knowledge Record is not Verified. It must be an approved source of truth before decoding."}
    ctx = _kr_context(kr, audience, level)
    try:
        gen = parse_json(await llm_generate(GEN_SYSTEM, ctx, f"decoder-{kr_id}")) or {}
    except Exception:
        return {"ok": False, "flag": "Founder Decision Required", "error": "Decoder author temporarily unavailable. Try again shortly."}
    if not gen.get("definition") or not gen.get("core_mental_model"):
        return {"ok": False, "flag": "Source Record Incomplete", "error": "Draft incomplete — please retry."}

    domain = _classify(kr, gen)
    det = _deterministic_checks(kr, gen, audience, level)
    adv = await _advisory(kr, gen)
    scorecard = _scorecard(det, adv)
    conf_rows, all_governed_pass, treasure_candidate = _confidence_summary(gen, det)
    decision = _autonomy_decision(det, all_governed_pass)

    # versioning: append-only; canonical is never overwritten.
    existing = await db[COLL].count_documents({"source_kr_ids.kr_id": kr.get("id")})
    did = f"DEC-{await db[COLL].count_documents({}) + 1:05d}"
    version = existing + 1
    safety = ("HIGH-STAKES TOPIC: education only, not individualized professional advice. Specialist review recommended."
              if det["high_stakes"] else "")
    rationale = gen.get("rationale") or {}
    governance_package = product_governance.build_package(
        "Decoder Record™", title=gen.get("title") or kr.get("title"), version=version, domain=domain,
        audience=audience or "General learner",
        source={"kr_code": kr.get("kr_code"), "kr_id": kr.get("id"), "version": kr.get("version", 1)},
        decoded_by=actor, high_stakes=det["high_stakes"], accessibility_notes=gen.get("accessibility_notes"))
    factory_confidence = {
        "rows": conf_rows, "recommendation": decision["recommendation"],
        "all_governed_pass": all_governed_pass, "generated_by": "Factory (autonomous)",
        "note": "Advisory scores support — never replace — human/constitutional judgment.",
    }
    rec = {
        "id": gen_id(), "decoder_id": did, "artifact_type": "QRU Decoder Record™",
        "title": gen.get("title") or kr.get("title"), "purpose": gen.get("purpose", ""),
        "governance_banner": "Governed · inherits a Verified Knowledge Record™ · Factory-owned (Quiet Factory™)",
        "source_kr_ids": [{"kr_id": kr.get("id"), "kr_code": kr.get("kr_code"), "version": kr.get("version", 1)}],
        "decoder_version": version, "is_canonical": existing == 0,
        "domain": domain, "subdomain": kr.get("category", ""), "audience": audience or "General learner",
        "level": level or "Introductory", "learning_objective": gen.get("purpose", ""),
        "confidence_status": kr.get("verification_status", "Verified"),
        "definition": gen.get("definition"), "why_it_matters": gen.get("why_it_matters"),
        "how_it_works": gen.get("how_it_works"), "core_mental_model": gen.get("core_mental_model"),
        "analogy": gen.get("analogy"), "analogy_mapping": gen.get("analogy_mapping"),
        "analogy_limitations": gen.get("analogy_limitations"), "story": gen.get("story"),
        "visual_spec": gen.get("visual_spec"), "vocabulary": gen.get("vocabulary", []),
        "misconceptions": gen.get("misconceptions", []), "applications": gen.get("applications", []),
        "guided_example": gen.get("guided_example"), "practice": gen.get("practice"),
        "reflection": gen.get("reflection"), "memory_anchor": gen.get("memory_anchor"),
        "verification": gen.get("verification"), "understanding_checks": gen.get("understanding_checks", {}),
        "next_understanding": gen.get("next_understanding"), "downstream_notes": gen.get("downstream_notes"),
        "accessibility_notes": gen.get("accessibility_notes"), "safety_notes": safety,
        "provenance": {"source": "KR", "kr_code": kr.get("kr_code"), "decoded_by": actor, "at": _now()},
        "inheritance": {"canonical_of": None, "variants": []},
        "educational_design_rationale": rationale,
        "scorecard": scorecard,
        "factory_confidence": factory_confidence,
        "governance_package": governance_package,
        "flags": ([("Medical, Financial, or Safety Review Required") ] if det["high_stakes"] else []) + (["Title overpromises scope"] if det["overpromise"] else []),
        "review_state": decision["state"],
        "human_review_recommended": decision["human_review_recommended"],
        "review_recommendation": decision["review_recommendation"],
        "shelf_location": f"{domain} › QRU Decoder Record™ › {audience or 'General'} › {decision['state']}",
        "treasure_standard_candidate": treasure_candidate,
        "treasure_standard_certified": False,
        "review_history": [
            {"state": "Automated Quality Review", "by": "Decoder Engine™", "at": _now(),
             "note": f"deterministic {'passed' if scorecard['deterministic_ok'] else 'flagged'}"},
            {"state": decision["state"], "by": "Factory (autonomous)", "at": _now(),
             "note": decision["recommendation"]},
        ],
        "created_by": actor, "created_at": _now(), "updated_at": _now(),
    }
    await db[COLL].insert_one(dict(rec))
    await log_org("Decoder Engine™", "Knowledge",
                  f"decoded {did} from {kr.get('kr_code')} → {decision['state']} (autonomous)", did,
                  "success" if all_governed_pass else "warning")
    return {"ok": True, "decoder": clean(rec)}


# ---------- Founder Review Shelf™ (Decoder review lifecycle) ----------
async def shelf(state=None):
    q = {} if not state else {"review_state": state}
    docs = await db[COLL].find(q, {"_id": 0}).sort("created_at", -1).to_list(300)
    return docs


async def needs_attention():
    """Records the Factory recommends for human/expert judgment (never a mandatory Founder gate)."""
    docs = await db[COLL].find(
        {"$or": [{"human_review_recommended": True}, {"review_state": "Revision Recommended"}]},
        {"_id": 0}).sort("created_at", -1).to_list(300)
    return docs


async def get_decoder(did):
    return await db[COLL].find_one({"id": did}, {"_id": 0})


async def _transition(did, state, actor, note=""):
    d = await db[COLL].find_one({"id": did})
    if not d:
        return None
    hist = d.get("review_history", [])
    hist.append({"state": state, "by": actor, "at": _now(), "note": note})
    upd = {"review_state": state, "updated_at": _now(), "review_history": hist}
    dom = d.get("domain", "General")
    aud = d.get("audience", "General")
    stage = {"Founder Approved": "Founder Approved", "Revision Requested": "Revision Shelf",
             "Revision Recommended": "Revision Shelf", "Manufacturing Ready": "Manufacturing Ready",
             "Archived": "Archive", "Treasure Standard Certified": "Treasure Vault"}.get(state, "Review")
    upd["shelf_location"] = f"{dom} › QRU Decoder Record™ › {aud} › {stage}"
    if state == "Treasure Standard Certified":
        upd["treasure_standard_certified"] = True
    await db[COLL].update_one({"id": did}, {"$set": upd})
    await log_org("Founder", "Knowledge", f"{state}: {d.get('decoder_id')}", d.get("decoder_id"), "success")
    return clean(await db[COLL].find_one({"id": did}, {"_id": 0}))


async def approve(did, actor):
    return await _transition(did, "Founder Approved", actor, "Educational quality approved by Founder.")


async def request_revision(did, actor, notes):
    return await _transition(did, "Revision Requested", actor, notes or "Please revise.")


async def archive(did, actor):
    return await _transition(did, "Archived", actor)


async def certify_treasure(did, actor):
    d = await db[COLL].find_one({"id": did})
    if not d:
        return None
    if not d.get("treasure_standard_candidate"):
        return {"error": "Treasure Standard™ certification requires an eligible Treasure Candidate™ "
                "(all governed standards passed). The Factory has not yet marked this record as a candidate."}
    return await _transition(did, "Treasure Standard Certified", actor, "Treasure Standard™ certified by Founder.")


async def stats():
    total = await db[COLL].count_documents({})
    manufacturing_ready = await db[COLL].count_documents({"review_state": "Manufacturing Ready"})
    needs_attention = await db[COLL].count_documents(
        {"$or": [{"human_review_recommended": True}, {"review_state": "Revision Recommended"}]})
    treasure_candidates = await db[COLL].count_documents({"treasure_standard_candidate": True})
    certified = await db[COLL].count_documents({"treasure_standard_certified": True})
    return {"total": total, "manufacturing_ready": manufacturing_ready, "needs_attention": needs_attention,
            "treasure_candidates": treasure_candidates, "certified": certified}


TAXONOMY = {"domains": DOMAINS, "review_states": REVIEW_STATES}
