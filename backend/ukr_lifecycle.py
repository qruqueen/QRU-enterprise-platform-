"""QRU UKR™ Governance Engine — Lifecycle (Section 18) + Gold Standard Review (Section 17).

Operates on the canonical `ukr` object of `knowledge_records` (UKR™ Standard v1.1 — the ONE canonical
standard defined in `ukr_standard.py`). This is the enforcement engine for:
  • the 20-state lifecycle with governed transition rules + full transition history, and
  • the 15-dimension Gold Standard Review (certification blocked until every dimension passes).

Constitutional guards preserved:
  • Founder review is required for final certification + governed exceptions (super-admin gate).
  • Legacy `verification_status` / `approval_status` / `treasure_standard` are NOT mutated here, so
    Knowledge-First™ enforcement and existing product links are undisturbed. Lifecycle + certification
    live authoritatively in the canonical `ukr` layer (additive governance).
"""
from datetime import datetime, timezone
from fastapi import HTTPException

from database import db
import ukr_standard as ukr

CANONICAL = ukr.CANONICAL_COLLECTION

# Governed 20-state transition graph. Every state also implicitly allows → "Archived" (added below).
TRANSITIONS = {
    "Proposed": ["Discovered", "Researching", "Draft"],
    "Discovered": ["Researching", "Draft"],
    "Researching": ["Draft"],
    "Draft": ["Internal Review", "Verification Required", "Revision Required"],
    "Internal Review": ["Verification Required", "Revision Required", "Draft"],
    "Verification Required": ["Verified", "Revision Required", "Draft"],
    "Verified": ["Understanding Review", "Gold Review", "Founder Review Required",
                 "Manufacturing Ready", "Revision Required", "Deprecated"],
    "Understanding Review": ["Gold Review", "Revision Required", "Verified"],
    "Gold Review": ["Founder Review Required", "Gold Certified", "Revision Required", "Verified"],
    "Founder Review Required": ["Approved", "Gold Certified", "Revision Required"],
    "Approved": ["Gold Certified", "Manufacturing Ready", "Published", "Revision Required", "Deprecated"],
    "Gold Certified": ["Manufacturing Ready", "Published", "Reverification Due", "Revision Required",
                       "Deprecated", "Superseded"],
    "Manufacturing Ready": ["Published", "Revision Required", "Deprecated"],
    "Published": ["Under Observation", "Reverification Due", "Revision Required", "Deprecated", "Superseded"],
    "Under Observation": ["Reverification Due", "Revision Required", "Published", "Deprecated"],
    "Reverification Due": ["Verification Required", "Verified", "Revision Required", "Deprecated"],
    "Revision Required": ["Draft", "Internal Review", "Verification Required", "Verified"],
    "Deprecated": ["Superseded"],
    "Superseded": [],
    "Archived": ["Draft"],  # revive
}
# Every non-terminal state may be archived.
for _s in list(TRANSITIONS):
    if _s != "Archived" and "Archived" not in TRANSITIONS[_s]:
        TRANSITIONS[_s] = TRANSITIONS[_s] + ["Archived"]

# States that require Founder (super-admin) authority — final certification / approval.
FOUNDER_ONLY_STATES = {"Approved", "Gold Certified"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def allowed_next(state):
    return TRANSITIONS.get(state, [])


async def _load(rid):
    rec = await db[CANONICAL].find_one({"id": rid}) or await db[CANONICAL].find_one({"kr_code": rid})
    if not rec:
        raise HTTPException(404, "Knowledge Record not found.")
    return rec


def _ensure_ukr(rec):
    u = rec.get("ukr") or ukr.build_canonical(rec)
    # guarantee a valid lifecycle state
    cur = (u.get("lifecycle") or {}).get("lifecycle_state") or ukr.derive_lifecycle_state(rec)
    if cur not in ukr.LIFECYCLE_STATES:
        cur = "Draft"
    u.setdefault("lifecycle", {})["lifecycle_state"] = cur
    u["lifecycle"].setdefault("transitions", [])
    u.setdefault("gold_standard_review", {})
    u["gold_standard_review"].setdefault("reviews", [])
    u["gold_standard_review"].setdefault("review_state", "Not Reviewed")
    return u, cur


# ---------------------------------------------------------------- Lifecycle ----

async def lifecycle_state(rid):
    rec = await _load(rid)
    u, cur = _ensure_ukr(rec)
    return {
        "kr_code": rec.get("kr_code"), "id": rec.get("id"),
        "lifecycle_state": cur,
        "allowed_transitions": allowed_next(cur),
        "founder_only_next": [s for s in allowed_next(cur) if s in FOUNDER_ONLY_STATES],
        "transitions": u["lifecycle"].get("transitions", []),
        "transition_count": len(u["lifecycle"].get("transitions", [])),
    }


async def transition(rid, to_state, actor, trigger="manual", note="", is_super=False):
    rec = await _load(rid)
    u, cur = _ensure_ukr(rec)

    if to_state not in ukr.LIFECYCLE_STATES:
        raise HTTPException(422, f"Unknown lifecycle state '{to_state}'. Valid states: {ukr.LIFECYCLE_STATES}")
    if to_state == cur:
        raise HTTPException(422, f"Record is already in '{cur}'.")
    allowed = allowed_next(cur)
    if to_state not in allowed:
        raise HTTPException(422, f"Invalid transition '{cur}' → '{to_state}'. Allowed from '{cur}': "
                                 f"{allowed or ['(terminal — no transitions)']}.")
    if to_state in FOUNDER_ONLY_STATES and not is_super:
        raise HTTPException(403, f"'{to_state}' is a Founder-only governed action (final certification/"
                                 "approval). Founder / super-admin authorization required.")
    if to_state == "Gold Certified":
        summary = _gold_summary(u)
        if not summary["all_passed"]:
            raise HTTPException(422, "Gold Standard certification blocked — not all 15 review dimensions "
                                     f"pass. Pending: {summary['pending']}. Failed: {summary['failed']}.")

    entry = {
        "prior_state": cur, "new_state": to_state, "trigger": trigger, "actor": actor,
        "timestamp": _now(), "validation_result": "pass", "unresolved_issues": [],
        "required_next_action": note or "", "note": note or "",
    }
    u["lifecycle"]["lifecycle_state"] = to_state
    u["lifecycle"]["transitions"] = (u["lifecycle"].get("transitions") or []) + [entry]
    u.setdefault("record_identity", {})["lifecycle_state"] = to_state
    u.setdefault("factory_interface", {})["lifecycle_state"] = to_state
    if to_state == "Gold Certified":
        u["record_identity"]["gold_standard_status"] = "Gold Certified"
        u["gold_standard_review"]["review_state"] = "Gold Certified"

    await db[CANONICAL].update_one({"id": rec["id"]}, {"$set": {"ukr": u, "lifecycle_state": to_state,
                                                                "updated_at": _now()}})
    return {"ok": True, "kr_code": rec.get("kr_code"), "from": cur, "to": to_state,
            "entry": entry, "allowed_next": allowed_next(to_state)}


# ------------------------------------------------------- Gold Standard Review ----

def _latest_reviews(u):
    latest = {}
    for r in (u.get("gold_standard_review", {}).get("reviews") or []):
        latest[r.get("dimension")] = r  # appended in order → last wins
    return latest


def _gold_summary(u):
    latest = _latest_reviews(u)
    dims, passed = [], 0
    pending, failed = [], []
    for d in ukr.REVIEW_DIMENSIONS:
        r = latest.get(d)
        if not r:
            status = "not_reviewed"; pending.append(d)
        elif r.get("pass"):
            status = "pass"; passed += 1
        else:
            status = "fail"; failed.append(d)
        dims.append({"dimension": d, "status": status,
                     "score": (r or {}).get("score"), "reviewer": (r or {}).get("reviewer"),
                     "deficiencies": (r or {}).get("deficiencies"), "date": (r or {}).get("date")})
    total = len(ukr.REVIEW_DIMENSIONS)
    return {"dimensions": dims, "passed_count": passed, "total": total,
            "all_passed": passed == total, "pending": pending, "failed": failed}


async def gold_review(rid):
    rec = await _load(rid)
    u, _ = _ensure_ukr(rec)
    s = _gold_summary(u)
    s.update({"kr_code": rec.get("kr_code"), "id": rec.get("id"),
              "review_state": u["gold_standard_review"].get("review_state") or "Not Reviewed",
              "certified": u["gold_standard_review"].get("review_state") == "Gold Certified"})
    return s


async def review_dimension(rid, dimension, score, passed, reviewer, reviewer_type="Founder",
                           deficiencies="", severity="", corrective_action="", department="",
                           due_date="", resolution=""):
    rec = await _load(rid)
    u, _ = _ensure_ukr(rec)
    if dimension not in ukr.REVIEW_DIMENSIONS:
        raise HTTPException(422, f"Unknown Gold Standard dimension '{dimension}'. "
                                 f"Valid dimensions: {ukr.REVIEW_DIMENSIONS}")
    entry = {
        "dimension": dimension, "reviewer": reviewer, "reviewer_type": reviewer_type,
        "date": _now(), "criteria": dimension, "score": score, "pass": bool(passed),
        "deficiencies": deficiencies, "severity": severity, "required_corrective_action": corrective_action,
        "responsible_department": department, "due_date": due_date, "resolution": resolution,
        "re_review_result": "", "certification_decision": "",
    }
    u["gold_standard_review"]["reviews"] = (u["gold_standard_review"].get("reviews") or []) + [entry]
    summary = _gold_summary(u)
    # Governed review_state (never auto-certify — that is a separate Founder action).
    if summary["all_passed"]:
        state = "Approved"  # all dimensions pass → eligible for Founder certification
    elif summary["failed"]:
        state = "Returned for Correction"
    else:
        state = "Under Review"
    if u["gold_standard_review"].get("review_state") != "Gold Certified":
        u["gold_standard_review"]["review_state"] = state
    await db[CANONICAL].update_one({"id": rec["id"]}, {"$set": {"ukr": u, "updated_at": _now()}})
    return {"ok": True, "kr_code": rec.get("kr_code"), "dimension": dimension, "recorded": entry,
            "review_state": u["gold_standard_review"]["review_state"], "summary": summary}


async def certify_gold(rid, actor):
    """Founder-only final certification. Blocked unless ALL 15 dimensions pass."""
    rec = await _load(rid)
    u, cur = _ensure_ukr(rec)
    summary = _gold_summary(u)
    if not summary["all_passed"]:
        raise HTTPException(422, "Gold Standard certification blocked — not all 15 dimensions pass. "
                                 f"Pending: {summary['pending']}. Failed: {summary['failed']}.")
    if "Gold Certified" not in allowed_next(cur):
        raise HTTPException(422, f"Cannot certify from lifecycle state '{cur}'. Move the record to a state "
                                 f"that allows Gold certification first (e.g. Verified / Gold Review / "
                                 f"Founder Review Required / Approved). Allowed from '{cur}': {allowed_next(cur)}.")
    res = await transition(rid, "Gold Certified", actor=actor, trigger="gold_certification",
                           note="All 15 Gold Standard dimensions passed; Founder-certified.", is_super=True)
    return {"ok": True, "kr_code": rec.get("kr_code"), "certified": True,
            "review_state": "Gold Certified", "lifecycle": res, "summary": summary}


async def governance_overview():
    """Read-only factory-wide lifecycle + certification distribution."""
    docs = await db[CANONICAL].find({}, {"_id": 0, "ukr": 1, "kr_code": 1}).to_list(5000)
    life, gold, invalid = {}, {"Gold Certified": 0, "Under Review": 0, "Not Reviewed": 0, "other": 0}, []
    for d in docs:
        u = d.get("ukr") or {}
        st = (u.get("lifecycle") or {}).get("lifecycle_state") or ""
        if st not in ukr.LIFECYCLE_STATES:
            invalid.append(d.get("kr_code")); st = st or "(missing)"
        life[st] = life.get(st, 0) + 1
        gs = (u.get("gold_standard_review") or {}).get("review_state") or "Not Reviewed"
        gold[gs if gs in gold else "other"] = gold.get(gs if gs in gold else "other", 0) + 1
    return {"total": len(docs), "lifecycle_distribution": dict(sorted(life.items())),
            "gold_review_distribution": gold, "records_with_invalid_state": invalid,
            "all_valid": len(invalid) == 0}
