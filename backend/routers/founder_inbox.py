"""Founder Review Inbox™ — one governed approval queue for pre-publication products.

Surfaces everything pending Founder decision (especially products that passed the Library
Auto-Gate™), with per-product readiness + blocker classification, single + bulk actions.

Governance preserved: nothing auto-publishes. "Approve for Store" only publishes when the
QRU publish gates pass (Creative Studio reviewed + Product Protection™ verified); otherwise
it records Founder approval and reports exactly what's still required. Version history and
live/Published products are never modified without explicit Founder action.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database import db
from auth import get_current_user
from models import now_iso, clean

router = APIRouter(prefix="/api/founder-inbox", tags=["founder-inbox"])

FILTERS = ["ready_for_review", "needs_founder_decision", "ready_for_store",
           "needs_design_fix", "needs_knowledge_record", "needs_asset", "blocked"]


def _meta(p):
    design = p.get("design_gate") or {}
    sc = p.get("design_scorecard") or {}
    score = design.get("score") if design.get("score") is not None else sc.get("overall")
    passed = design.get("passed") if design.get("passed") is not None else sc.get("passed", False)
    content = p.get("content") or ""
    has_content = len(content) >= 300
    has_kr = bool(p.get("knowledge_record_id")) or bool(p.get("assembled"))
    deliver_ready = bool(p.get("deliverable_ready"))
    verified = bool(p.get("verified"))
    creative_ok = bool(p.get("creative_brief")) and p.get("creative_status") == "Reviewed"
    preview = bool(p.get("preview_url") or p.get("preview_pdf_url") or p.get("marketing_kit_ready"))
    needs_asset = p.get("asset_mode") in ("founder_selected", "founder") and not p.get("cover_vault_asset")
    marketplace = 0
    for l in sc.get("categories", []):
        if l["category"] == "Marketplace Readiness":
            marketplace = l["score"] * 10

    tags, blockers = [], []
    if not has_content and not has_kr:
        tags.append("needs_knowledge_record"); blockers.append("Needs a Knowledge Record")
    if not has_content and has_kr:
        tags.append("blocked"); blockers.append("Needs AI content (after cap reset)")
    if needs_asset:
        tags.append("needs_asset"); blockers.append("Needs a Founder asset")
    if has_content and not deliver_ready:
        tags.append("blocked"); blockers.append("Deliverable not rendered")
    if deliver_ready and not passed:
        tags.append("needs_design_fix"); blockers.append(f"Design score {score} below threshold")
    ready = bool(passed and deliver_ready)
    if ready:
        tags.append("ready_for_review")
        if verified and creative_ok:
            tags.append("ready_for_store")
        if p.get("status") not in ("Approved", "Published"):
            tags.append("needs_founder_decision")
    publish_blockers = []
    if not creative_ok:
        publish_blockers.append("Creative Studio review")
    if not verified:
        publish_blockers.append("Product Protection™ verification")

    return {
        "design_score": score, "design_passed": passed,
        "treasure_standard": bool(p.get("treasure_standard")),
        "treasure_status": p.get("treasure_standard_status") or ("Certified" if p.get("treasure_standard") else "Pending"),
        "marketplace_readiness": marketplace, "preview_available": preview,
        "publishable": ready and verified and creative_ok,
        "publish_blockers": publish_blockers,
        "blockers": blockers, "filter_tags": sorted(set(tags)),
    }


@router.get("")
async def inbox(user=Depends(get_current_user)):
    prods = await db.products.find({
        "status": {"$nin": ["Published", "Archived"]},
        "founder_hidden": {"$ne": True},
    }).sort("updated_at", -1).to_list(1000)
    items, counts = [], {f: 0 for f in FILTERS}
    for p in prods:
        m = _meta(p)
        for t in m["filter_tags"]:
            if t in counts:
                counts[t] += 1
        items.append({
            "id": p["id"], "product_code": p.get("product_code"), "title": p.get("title"),
            "product_type": p.get("product_type"), "category": p.get("family") or p.get("category"),
            "status": p.get("status"), "cover_url": p.get("cover_url"),
            "preview_url": p.get("preview_url"), "preview_pdf_url": p.get("preview_pdf_url"),
            "customer_files": (p.get("customer_deliverable") or {}).get("files", []),
            **m,
        })
    return {"counts": counts, "total": len(items), "products": items}


async def _apply(pid, action, actor):
    p = await db.products.find_one({"id": pid})
    if not p:
        return {"id": pid, "ok": False, "message": "Not found"}
    if p.get("status") == "Published" and action != "archive":
        return {"id": pid, "ok": False, "message": "Live product — unchanged (needs explicit action)."}
    now = now_iso()
    if action == "approve":
        m = _meta(p)
        if m["publishable"]:
            await db.products.update_one({"id": pid}, {"$set": {"status": "Published", "founder_approved_at": now, "updated_at": now}})
            msg, ok = "Approved & published to the QRU Store™.", True
        else:
            await db.products.update_one({"id": pid}, {"$set": {"status": "Approved", "founder_approved_at": now, "updated_at": now}})
            msg, ok = f"Founder-approved. Still required before Store: {', '.join(m['publish_blockers'])}.", True
    elif action == "return":
        await db.products.update_one({"id": pid}, {"$set": {"status": "Needs Review", "creative_status": "Needs Revision", "updated_at": now}})
        msg, ok = "Returned to Creative Studio™.", True
    elif action == "archive":
        await db.products.update_one({"id": pid}, {"$set": {"status": "Archived", "updated_at": now}})
        msg, ok = "Archived.", True
    elif action == "hide":
        await db.products.update_one({"id": pid}, {"$set": {"founder_hidden": True, "updated_at": now}})
        msg, ok = "Hidden from the inbox.", True
    else:
        return {"id": pid, "ok": False, "message": "Unknown action"}
    await db.activities.insert_one({"actor": actor, "action": f"inbox:{action}", "entity": "Product",
                                    "entity_id": pid, "detail": p.get("product_code", ""), "created_at": now})
    return {"id": pid, "ok": ok, "message": msg}


class ActionInput(BaseModel):
    action: str  # approve | return | archive | hide


@router.post("/{pid}/action")
async def action(pid: str, data: ActionInput, user=Depends(get_current_user)):
    if data.action not in ("approve", "return", "archive", "hide"):
        raise HTTPException(400, "Invalid action")
    return await _apply(pid, data.action, user["name"])


class BulkInput(BaseModel):
    action: str
    ids: List[str]


@router.post("/bulk")
async def bulk(data: BulkInput, user=Depends(get_current_user)):
    if data.action not in ("approve", "return", "archive", "hide"):
        raise HTTPException(400, "Invalid action")
    results = [await _apply(pid, data.action, user["name"]) for pid in data.ids]
    return {"results": results, "processed": len(results), "succeeded": sum(1 for r in results if r["ok"])}
