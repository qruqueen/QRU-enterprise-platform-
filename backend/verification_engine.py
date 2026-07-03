"""QRU Verification Team™ — autonomous AI verification of manufactured Knowledge Records.

Default workflow (no Founder involvement required):
    Manufacture → AI Verification Team Review → AI Revisions (if needed)
    → AI Re-Verification → Final Approval → Publish.

The Founder is escalated to ONLY on genuine exceptions:
    1. Human judgment is truly required
    2. There is conflicting evidence
    3. Confidence falls below the required threshold
    4. A policy / governance decision must be made
"""
import os
import logging

from database import db
from models import gen_id, now_iso, QRU_SECTIONS
from ai_service import llm_generate, parse_json
from manufacturing_engine import regenerate_field
from org_activity import log_org

logger = logging.getLogger("qru.verify")

CONFIDENCE_THRESHOLD = int(os.environ.get("VERIFICATION_CONFIDENCE_THRESHOLD", "80"))
MAX_REVISION_ROUNDS = 2

VERIFICATION_SYSTEM = """You are the QRU Verification Team™ — Kingdom Lion™ (evidence & accuracy),
Legacy Bear™ (teaching clarity), and Queen Unity™ (balance & bias). You review a manufactured
Knowledge Record so the Founder does NOT have to verify every record by hand.

QRU manufactures understanding from verified knowledge. Never distort or invent facts.

Review the record against trusted, authoritative knowledge and QRU standards. Score each
dimension 0-100: accuracy, clarity, completeness, readability, qru_standards.

Return ONLY valid JSON (no markdown fences):
{
  "scores": {"accuracy": 0-100, "clarity": 0-100, "completeness": 0-100, "readability": 0-100, "qru_standards": 0-100},
  "confidence_score": 0-100,
  "decision": "approve" | "request_revision" | "reject",
  "issues": ["specific issue", "..."],
  "weak_sections": ["section_key that needs improvement", "..."],
  "reasons": "concise explanation of the decision (2-4 sentences)",
  "conflicting_evidence": false,
  "requires_human_judgment": false,
  "policy_concern": false,
  "escalation_reason": ""
}
Approve only if the record is accurate, clear, complete, and meets QRU standards.
Request revision if specific fixable improvements are needed. Reject only if fundamentally flawed
or factually unsound. Set conflicting_evidence/requires_human_judgment/policy_concern true only
when genuinely warranted."""

# Section keys the verifier may ask to revise (must be regenerable methodology fields).
REVISABLE = set(QRU_SECTIONS)


def _record_context(rec):
    parts = [f"Title: {rec.get('title','')}", f"Category: {rec.get('category','')}",
             f"Verified Truth: {rec.get('verified_truth','')}"]
    for s in QRU_SECTIONS:
        val = rec.get(s)
        if isinstance(val, list):
            val = "; ".join(str(v) for v in val)
        if val:
            parts.append(f"{s}: {str(val)[:500]}")
    return "\n".join(parts)


async def _log_decision(kr, review, round_no):
    entry = {
        "at": now_iso(), "round": round_no, "team": "QRU Verification Team™",
        "decision": review.get("decision"), "confidence_score": review.get("confidence_score"),
        "scores": review.get("scores", {}), "issues": review.get("issues", []),
        "reasons": review.get("reasons", ""),
    }
    log = kr.get("verification_log", [])
    log.append(entry)
    await db.knowledge_records.update_one({"id": kr["id"]}, {"$set": {"verification_log": log}})
    return entry


async def _escalate(kr, review):
    reasons = []
    if review.get("conflicting_evidence"):
        reasons.append("Conflicting evidence detected")
    if review.get("requires_human_judgment"):
        reasons.append("Human judgment required")
    if review.get("policy_concern"):
        reasons.append("Policy / governance decision needed")
    if (review.get("confidence_score") or 0) < CONFIDENCE_THRESHOLD:
        reasons.append(f"Confidence {review.get('confidence_score')} below threshold {CONFIDENCE_THRESHOLD}")
    if review.get("escalation_reason"):
        reasons.append(review["escalation_reason"])
    reason_text = "; ".join(reasons) or "Exception flagged by the Verification Team"

    await db.founder_escalations.insert_one({
        "id": gen_id(), "kr_id": kr["id"], "kr_code": kr.get("kr_code"), "title": kr.get("title"),
        "reason": reason_text, "review": review, "status": "Open",
        "confidence_score": review.get("confidence_score"), "created_at": now_iso(),
    })
    await db.knowledge_records.update_one(
        {"id": kr["id"]},
        {"$set": {"verification_status": "Escalated", "approval_status": "Pending Founder Review",
                  "escalated": True, "escalation_reason": reason_text, "updated_at": now_iso()}})
    await db.notifications.insert_one({
        "id": gen_id(), "level": "warning", "read": False, "created_at": now_iso(),
        "message": f"Founder review needed — {kr.get('kr_code')}: {reason_text}",
    })
    await log_org("Kingdom Lion™", "Verification", f"escalated to Founder — {reason_text}", kr.get("kr_code", ""), "warning")


async def ai_verify_record(kr_id: str, actor: str = "QRU Verification Team™") -> dict:
    """Run the full autonomous verification workflow for one Knowledge Record."""
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        return {"error": "not found"}
    await log_org("Kingdom Lion™", "Verification", "began autonomous review of", kr.get("kr_code", ""))

    review = None
    for round_no in range(0, MAX_REVISION_ROUNDS + 1):
        kr = await db.knowledge_records.find_one({"id": kr_id})
        raw = await llm_generate(VERIFICATION_SYSTEM, _record_context(kr), f"verify-{kr_id}-{round_no}")
        review = parse_json(raw) or {"decision": "request_revision", "confidence_score": 0,
                                     "reasons": "Verifier response could not be parsed.", "weak_sections": []}
        await _log_decision(kr, review, round_no)

        exception = (review.get("conflicting_evidence") or review.get("requires_human_judgment")
                     or review.get("policy_concern"))
        decision = review.get("decision")
        conf = review.get("confidence_score") or 0

        # Reject → escalate for governance.
        if decision == "reject":
            await db.knowledge_records.update_one(
                {"id": kr_id}, {"$set": {"verification_status": "Rejected", "approval_status": "Rejected",
                                         "confidence_score": conf, "updated_at": now_iso()}})
            await _escalate(kr, review)
            return {"decision": "reject", "escalated": True, "review": review}

        # Approve + confident + no exception → final approval, no Founder needed.
        if decision == "approve" and conf >= CONFIDENCE_THRESHOLD and not exception:
            await _approve(kr, review, actor)
            return {"decision": "approve", "escalated": False, "review": review}

        # Exception (even on approve) → escalate.
        if exception:
            await _escalate(kr, review)
            return {"decision": decision, "escalated": True, "review": review}

        # request_revision or low confidence → AI revises weak sections and re-verifies.
        if round_no < MAX_REVISION_ROUNDS:
            weak = [s for s in review.get("weak_sections", []) if s in REVISABLE]
            if not weak:
                weak = [s for s in QRU_SECTIONS if not _is_filled(kr.get(s))]
            await log_org("Legacy Bear™", "Education",
                          f"revising {len(weak)} section(s) after verification", kr.get("kr_code", ""))
            for s in weak[:6]:
                try:
                    await regenerate_field(kr_id, s, "QRU Verification Team™ (auto-revision)")
                except Exception as e:
                    logger.error(f"auto-revision of {s} failed: {e}")
            continue

    # Exhausted revision rounds. Per QRU standards, escalate ONLY on true triggers:
    # low confidence, conflicting evidence, human judgment, or policy concerns.
    # A high-confidence "request_revision" with no conflicts is safe for the AI to approve.
    review = review or {}
    exception = (review.get("conflicting_evidence") or review.get("requires_human_judgment")
                 or review.get("policy_concern"))
    conf = review.get("confidence_score") or 0
    if exception or conf < CONFIDENCE_THRESHOLD:
        await _escalate(kr, review)
        return {"decision": "escalated", "escalated": True, "review": review}
    kr = await db.knowledge_records.find_one({"id": kr_id})
    review.setdefault("reasons", "Auto-approved after AI revisions — high confidence, no conflicts.")
    await _approve(kr, review, actor)
    return {"decision": "approve", "escalated": False, "review": review}


def _is_filled(v):
    if isinstance(v, list):
        return len(v) > 0
    return bool(v and str(v).strip())


async def _approve(kr, review, actor):
    conf = review.get("confidence_score") or 90
    section_status = kr.get("section_status", {})
    for s in QRU_SECTIONS:
        if section_status.get(s) in ("Draft", "Empty") and _is_filled(kr.get(s)):
            section_status[s] = "Verified"
    treasure = all(_is_filled(kr.get(s)) for s in QRU_SECTIONS) and conf >= CONFIDENCE_THRESHOLD
    verification = {
        "reviewer": "QRU Verification Team™", "reviewed_at": now_iso(), "decision": "approve",
        "confidence_score": conf, "scores": review.get("scores", {}),
        "reviewer_comments": review.get("reasons", ""), "autonomous": True,
    }
    await db.knowledge_records.update_one(
        {"id": kr["id"]},
        {"$set": {"verification_status": "Verified", "approval_status": "Approved",
                  "is_master_file": True, "treasure_standard": treasure, "confidence_score": conf,
                  "section_status": section_status, "verification": verification,
                  "verified_autonomously": True, "escalated": False, "updated_at": now_iso()}})
    await log_org("Kingdom Lion™", "Verification",
                  f"auto-approved ({conf}% confidence)", kr.get("kr_code", ""), "success")
