"""QRU UKR-Inheritance Governance™ — the single enforcement choke point.

Constitution: every EDUCATIONAL product must trace to exactly one VERIFIED Universal Knowledge
Record (Verified UKR → Decoder → Manufacturing → Publishing). The ONE governed exception is a
Founder-authored manuscript (handled in book_manufacturing / book_records — a different collection,
not governed here). This module is used by every product-creation + publish path so the rule is
enforced in ONE place, invisibly, with no new Founder buttons.
"""
from fastapi import HTTPException
from database import db

_KR_COLLECTIONS = ("knowledge_records", "knowledge_engine_records")


def is_verified(kr) -> bool:
    if not kr:
        return False
    return kr.get("verification_status") == "Verified" or kr.get("approval_status") == "Approved"


async def resolve_kr(kr_id):
    if not kr_id:
        return None
    for coll in _KR_COLLECTIONS:
        kr = await db[coll].find_one({"id": kr_id})
        if kr:
            return kr
    return None


async def require_verified_ukr(kr_id, product_type=""):
    """Raise 422/404 unless kr_id points to a VERIFIED Knowledge Record. Returns the KR on success."""
    label = f" for this {product_type}" if product_type else ""
    if not kr_id:
        raise HTTPException(422, "Knowledge-First™: this product must inherit from a Verified Knowledge "
                                 f"Record{label}. Select a Verified KR (or verify one at the Verification "
                                 "Center) before manufacturing.")
    kr = await resolve_kr(kr_id)
    if not kr:
        raise HTTPException(404, "Knowledge Record not found — cannot manufacture without a verified source.")
    if not is_verified(kr):
        raise HTTPException(422, f"Knowledge Record '{kr.get('title','')}' is not Verified yet — only "
                                 "Verified records may manufacture (Knowledge-First™). Verify it at the "
                                 "Verification Center first.")
    return kr


def is_founder_exception(product) -> bool:
    """Founder-authored manuscripts are the ONE governed exception."""
    return bool(product.get("founder_authored") or product.get("manuscript_origin")
                or (product.get("source") or "").lower() == "manuscript")


async def traceability(product) -> dict:
    """Per-product UKR-traceability status: green (verified UKR) / amber (unverified/dangling) / red (none)."""
    if is_founder_exception(product):
        return {"status": "green", "reason": "Founder-authored manuscript (governed exception)"}
    kr_id = product.get("knowledge_record_id") or (product.get("inherits_from") or {}).get("kr_id")
    if not kr_id:
        return {"status": "red", "reason": "No Knowledge Record linked"}
    kr = await resolve_kr(kr_id)
    if not kr:
        return {"status": "amber", "reason": "Linked Knowledge Record is missing (dangling)"}
    if not is_verified(kr):
        return {"status": "amber", "reason": f"Knowledge Record '{kr.get('title','')}' not Verified"}
    return {"status": "green", "reason": "Traces to a Verified Knowledge Record", "kr_code": kr.get("kr_code")}


async def audit_report() -> dict:
    """Factory-wide UKR-traceability audit for the Founders Console."""
    prods = await db.products.find({}, {"_id": 0}).to_list(5000)
    green = amber = red = 0
    published_red = []
    for p in prods:
        t = await traceability(p)
        if t["status"] == "green":
            green += 1
        elif t["status"] == "amber":
            amber += 1
        else:
            red += 1
        if t["status"] != "green" and str(p.get("status", "")).lower() == "published":
            published_red.append({"id": p.get("id"), "code": p.get("product_code"),
                                  "title": p.get("title"), "issue": t["reason"]})
    total = len(prods)
    return {
        "total": total, "green": green, "amber": amber, "red": red,
        "compliant_pct": round(green / total * 100, 1) if total else 100,
        "published_noncompliant": published_red,
        "published_noncompliant_count": len(published_red),
    }
