#!/usr/bin/env python3
"""QRU LEARN GOVERNANCE CONTAINMENT — Workstream C (SEPARATE from A/B).

REVIEW PACKAGE. Runs where MONGO_URL/DB_NAME point (Support, in PRODUCTION). Read-only by default.

Step 1 (--verify, default): classify the 5 products in the ACTUAL production database.
Step 2 (--apply-hold): place ONLY products classified PRODUCTION_HOLD_REQUIRED into a governed hold.
       Changes ONLY the availability/publication state; preserves product, assets, purchases, provenance.
Rollback (--rollback-hold): restore the prior publication state.

This does NOT implement the immutable-snapshot architecture. Containment only.
"""
import os, sys, json, argparse, datetime

TARGETS = ["PRD-00130", "PRD-00196", "PRD-00201", "PRD-00202", "PRD-00205"]
HOLD_STATUS = "On Hold (Governance)"
MARK = "RI-MFG-C-CONTAINMENT"


def _db():
    from pymongo import MongoClient
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def classify(db):
    rows = []
    for code in TARGETS:
        p = db.products.find_one({"product_code": code})
        if not p:
            rows.append((code, None, None, None, None, "NOT_PRESENT_IN_PRODUCTION")); continue
        krid = p.get("knowledge_record_id")
        kr = db.knowledge_records.find_one({"id": krid}) if krid else None
        kr_status = (kr or {}).get("verification_status") if kr else ("MISSING_KR" if krid else "NO_KR_LINK")
        pub = p.get("status")
        learner_accessible = (pub == "Published")
        verified = kr_status == "Verified"
        if not learner_accessible:
            cls = "NOT_LEARNER_ACCESSIBLE"
        elif kr and not verified:
            cls = "PRODUCTION_HOLD_REQUIRED"     # live to learners + KR not Verified
        elif not kr:
            cls = "FOUNDER_REVIEW_REQUIRED"      # published but KR missing/unlinked
        else:
            cls = "FOUNDER_REVIEW_REQUIRED"      # published + verified: not a containment target
        rows.append((code, p.get("id"), pub, kr_status, learner_accessible, cls))
    return rows


def print_table(rows):
    print(f"{'PRODUCT':12} {'PROD?':6} {'PUB STATUS':22} {'KR STATUS':26} {'LEARNER?':9} CLASSIFICATION")
    for code, pid, pub, krs, acc, cls in rows:
        present = "no" if pid is None else "yes"
        print(f"{code:12} {present:6} {str(pub):22} {str(krs):26} {str(acc):9} {cls}")


def apply_hold(db, rows, apply):
    print("\n=== APPLY GOVERNED HOLD (PRODUCTION_HOLD_REQUIRED only) ===")
    for code, pid, pub, krs, acc, cls in rows:
        if cls != "PRODUCTION_HOLD_REQUIRED":
            print(f"  {code}: {cls} -> not a hold target, skip"); continue
        if apply:
            db.products.update_one({"id": pid}, {"$set": {
                "status": HOLD_STATUS,
                "status_before_hold": pub,
                "governance_hold": {"reason": "Linked Knowledge Record not Verified",
                                    "by": MARK, "at": datetime.datetime.utcnow().isoformat(),
                                    "unavailable_message": "This lesson is temporarily unavailable pending verified approval."}}})
            print(f"  {code}: HELD (status {pub} -> {HOLD_STATUS}); assets/purchases/provenance preserved")
        else:
            print(f"  {code}: WOULD HOLD (status {pub} -> {HOLD_STATUS}) [dry-run]")


def rollback_hold(db, apply):
    print("\n=== ROLLBACK GOVERNED HOLD ===")
    for code in TARGETS:
        p = db.products.find_one({"product_code": code})
        if not p or not p.get("governance_hold"):
            continue
        prior = p.get("status_before_hold", "Published")
        if apply:
            db.products.update_one({"id": p["id"]}, {"$set": {"status": prior},
                                                     "$unset": {"governance_hold": "", "status_before_hold": ""}})
            print(f"  {code}: RESTORED -> {prior}")
        else:
            print(f"  {code}: WOULD RESTORE -> {prior} [dry-run]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply-hold", action="store_true")
    ap.add_argument("--rollback-hold", action="store_true")
    ap.add_argument("--apply", action="store_true", help="perform writes (with --apply-hold/--rollback-hold)")
    a = ap.parse_args()
    db = _db()
    rows = classify(db)
    print_table(rows)
    if a.apply_hold:
        apply_hold(db, rows, a.apply)
    if a.rollback_hold:
        rollback_hold(db, a.apply)


if __name__ == "__main__":
    main()
