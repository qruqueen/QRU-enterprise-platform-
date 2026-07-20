"""QRU QA Cleanup™ — controlled removal of TEST/QA/PREVIEW products only.

Safeguards (super-admin only; audit-logged):
  • A product is eligible ONLY when qa_status ∈ {test, qa, preview} AND it is not Published,
    not production/live, and not tied to a completed/paid order.
  • Eligibility is NEVER inferred from title, naming, age, or creator.
  • Removal is a SOFT delete to a Trash collection first (full snapshot + references retained).
  • Permanent deletion is a separate, second-confirmation action and is blocked for
    published/purchased/production records.
  • Decoder + Knowledge Record references are cleaned on delete and restored on restore;
    product counts are reconciled and reported.
"""
from datetime import datetime, timezone

from database import db
from models import gen_id, now_iso
from org_activity import log_org

QA_STATUSES = ("test", "qa", "preview")
PRODUCTS = "products"
TRASH = "products_trash"
AUDIT = "qa_cleanup_audit"


def _now():
    return datetime.now(timezone.utc).isoformat()


async def _has_paid_order(pid: str) -> bool:
    if await db.purchases.count_documents({"product_id": pid}) > 0:
        return True
    if await db.book_purchases.count_documents({"product_id": pid}) > 0:
        return True
    if await db.payment_transactions.count_documents(
            {"payment_status": "paid",
             "$or": [{"product_id": pid}, {"metadata.product_id": pid}]}) > 0:
        return True
    return False


async def _blockers(p: dict):
    """Return a list of reasons this product may NOT be QA-removed (empty list = eligible)."""
    reasons = []
    if (p.get("qa_status") or "").lower() not in QA_STATUSES:
        reasons.append("Product is not marked test/qa/preview (qa_status unset).")
    status = (p.get("status") or "").lower()
    if status in ("published", "live", "production"):
        reasons.append(f"Product status is '{p.get('status')}' — published/production records are protected.")
    if p.get("published") is True or p.get("live") is True:
        reasons.append("Product is flagged published/live.")
    if await _has_paid_order(p["id"]):
        reasons.append("Product is associated with a completed/paid order.")
    return reasons


async def audit(action, actor, pid, detail, extra=None):
    doc = {"id": gen_id(), "action": action, "actor": actor, "product_id": pid,
           "detail": detail, "at": _now()}
    if extra:
        doc.update(extra)
    await db[AUDIT].insert_one(dict(doc))
    try:
        await log_org("QRU QA Cleanup™", "Governance", f"{action}: {detail}", pid, "success")
    except Exception:
        pass
    return doc


async def set_qa_status(pid, qa_status, actor):
    p = await db[PRODUCTS].find_one({"id": pid}, {"_id": 0})
    if not p:
        return {"error": "Product not found."}
    if qa_status is not None and qa_status not in QA_STATUSES:
        return {"error": f"qa_status must be one of {QA_STATUSES} or null."}
    prev = p.get("qa_status")
    await db[PRODUCTS].update_one({"id": pid}, {"$set": {"qa_status": qa_status, "updated_at": now_iso()}})
    await audit("mark_qa_status", actor, pid,
                f"qa_status {prev or 'unset'} → {qa_status or 'unset'} for '{p.get('title')}'",
                {"from": prev, "to": qa_status})
    return {"ok": True, "id": pid, "qa_status": qa_status, "title": p.get("title")}


async def eligible_list():
    out = []
    async for p in db[PRODUCTS].find({"qa_status": {"$in": list(QA_STATUSES)}}, {"_id": 0}):
        reasons = await _blockers(p)
        out.append({"id": p["id"], "product_code": p.get("product_code"), "title": p.get("title"),
                    "product_type": p.get("product_type"), "qa_status": p.get("qa_status"),
                    "status": p.get("status"), "knowledge_record_id": p.get("knowledge_record_id"),
                    "decoder_id": (p.get("source_decoder") or {}).get("decoder_id"),
                    "eligible": len(reasons) == 0, "blockers": reasons})
    return {"count": len([x for x in out if x["eligible"]]), "marked_total": len(out), "products": out}


async def _references(p):
    kr_id = p.get("knowledge_record_id")
    dec_id = (p.get("source_decoder") or {}).get("decoder_id")
    return {"knowledge_record_id": kr_id, "decoder_id": dec_id,
            "product_count_before": await db[PRODUCTS].count_documents({})}


async def soft_delete(pid, reason, actor):
    p = await db[PRODUCTS].find_one({"id": pid}, {"_id": 0})
    if not p:
        return {"error": "Product not found."}
    blockers = await _blockers(p)
    if blockers:
        return {"error": "Not eligible for QA cleanup.", "blockers": blockers}
    refs = await _references(p)

    # Clean references: pull from decoder.manufactured_products, decrement source KR products_created.
    dec_pulled = 0
    if refs["decoder_id"]:
        r = await db.decoder_records.update_one(
            {"decoder_id": refs["decoder_id"]},
            {"$pull": {"manufactured_products": {"product_id": pid}}})
        dec_pulled = r.modified_count
    kr_dec = False
    if refs["knowledge_record_id"]:
        kr = await db.knowledge_records.find_one({"id": refs["knowledge_record_id"]}, {"products_created": 1})
        if kr and (kr.get("products_created") or 0) > 0:
            await db.knowledge_records.update_one({"id": refs["knowledge_record_id"]},
                                                  {"$inc": {"products_created": -1}})
            kr_dec = True

    trash_id = gen_id()
    trash_doc = {"id": trash_id, "product_id": pid, "product": p, "references": refs,
                 "reference_cleanup": {"decoder_pulled": dec_pulled, "kr_decremented": kr_dec},
                 "reason": reason or "QA cleanup", "deleted_by": actor, "deleted_at": _now(),
                 "restorable": True}
    await db[TRASH].insert_one(dict(trash_doc))
    await db[PRODUCTS].delete_one({"id": pid})
    count_after = await db[PRODUCTS].count_documents({})
    await audit("soft_delete", actor, pid,
                f"soft-deleted '{p.get('title')}' → Trash ({reason or 'QA cleanup'})",
                {"trash_id": trash_id, "count_before": refs["product_count_before"], "count_after": count_after})
    return {"ok": True, "trash_id": trash_id, "product_id": pid,
            "reconciliation": {"product_count_before": refs["product_count_before"],
                               "product_count_after": count_after,
                               "decoder_refs_pulled": dec_pulled, "kr_products_created_decremented": kr_dec}}


async def trash_list():
    rows = await db[TRASH].find({}, {"_id": 0, "product.content": 0}).sort("deleted_at", -1).to_list(200)
    return {"count": len(rows), "trash": rows}


async def restore(trash_id, actor):
    t = await db[TRASH].find_one({"id": trash_id}, {"_id": 0})
    if not t:
        return {"error": "Trash record not found."}
    p = t["product"]
    if await db[PRODUCTS].find_one({"id": p["id"]}, {"_id": 1}):
        return {"error": "A product with this id already exists — cannot restore over it."}
    await db[PRODUCTS].insert_one(dict(p))
    # Best-effort reference restore.
    refs = t.get("references", {})
    if refs.get("knowledge_record_id") and t.get("reference_cleanup", {}).get("kr_decremented"):
        await db.knowledge_records.update_one({"id": refs["knowledge_record_id"]},
                                              {"$inc": {"products_created": 1}})
    if refs.get("decoder_id"):
        await db.decoder_records.update_one(
            {"decoder_id": refs["decoder_id"]},
            {"$push": {"manufactured_products": {"product_type": p.get("product_type"),
                                                 "product_id": p["id"], "product_code": p.get("product_code"),
                                                 "title": p.get("title"), "created_at": _now(),
                                                 "by": f"restored by {actor}"}}})
    await db[TRASH].delete_one({"id": trash_id})
    await audit("restore", actor, p["id"], f"restored '{p.get('title')}' from Trash",
                {"trash_id": trash_id, "product_count_after": await db[PRODUCTS].count_documents({})})
    return {"ok": True, "product_id": p["id"], "title": p.get("title")}


async def permanent_delete(trash_id, actor, confirm_title):
    t = await db[TRASH].find_one({"id": trash_id}, {"_id": 0})
    if not t:
        return {"error": "Trash record not found."}
    p = t["product"]
    if (confirm_title or "").strip() != (p.get("title") or "").strip():
        return {"error": "Confirmation title does not match. Type the exact product title to permanently delete."}
    # Re-assert safety: never permanently delete a record that had been published/paid/production.
    blockers = []
    if (p.get("status") or "").lower() in ("published", "live", "production") or p.get("published") or p.get("live"):
        blockers.append("Record was published/production.")
    if await _has_paid_order(p["id"]):
        blockers.append("Record is associated with a paid order.")
    if blockers:
        return {"error": "Permanent deletion blocked.", "blockers": blockers}
    await db[TRASH].delete_one({"id": trash_id})
    await audit("permanent_delete", actor, p["id"],
                f"PERMANENTLY deleted '{p.get('title')}' ({p.get('product_code')})", {"trash_id": trash_id})
    return {"ok": True, "permanently_deleted": p["id"], "title": p.get("title")}


async def audit_log(limit=100):
    rows = await db[AUDIT].find({}, {"_id": 0}).sort("at", -1).to_list(limit)
    return {"count": len(rows), "audit": rows}
