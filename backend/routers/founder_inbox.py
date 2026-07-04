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
import factory_confidence as fc
import autonomous_engine as ae
import product_recipes as pr

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

    # MO-038 — Data Health™ + Factory Confidence™ + un-bypassable publish gate.
    confidence = fc.factory_confidence(p)
    dh = confidence["data_health"]
    publishable, publish_blockers = fc.publish_gate(p)
    # MO-041 — self-guiding guidance so no row is ever a dead end.
    lad = ae.gate_ladder(p, 91)
    guidance = {"next_action": lad["next_action"], "mode": lad["mode"],
                "founder_action_required": lad["founder_action_required"],
                "progress_pct": lad["progress_pct"], "current_gate": lad["current_gate"],
                "after_completion": lad["after_completion"]}

    return {
        "design_score": score, "design_passed": passed,
        "treasure_standard": bool(p.get("treasure_standard")),
        "treasure_status": p.get("treasure_standard_status") or ("Certified" if p.get("treasure_standard") else "Pending"),
        "marketplace_readiness": marketplace, "preview_available": preview,
        "data_health": dh["status"], "data_health_label": dh["label"],
        "data_health_emoji": dh["emoji"], "data_health_reasons": dh["reasons"],
        "factory_confidence": confidence["score"], "confidence_band": confidence["band"],
        "confidence_components": confidence["components"],
        "publishable": publishable,
        "publish_blockers": publish_blockers,
        "guidance": guidance,
        "design_escalation": p.get("design_escalation"),
        "design_result": (p.get("design_gate") or {}).get("result_summary"),
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


def _preview_item(key, label, available, url=None, reason=None, files=None):
    return {"key": key, "label": label, "available": bool(available),
            "url": url, "files": files, "reason": None if available else (reason or "Not available yet.")}


async def _evidence(p):
    """MO-040 — the complete Evidence-Based Decision Center™ dossier for one product.
    Everything the Founder needs to decide in 30-60s without opening other screens."""
    m = _meta(p)
    cd = p.get("customer_deliverable") or {}
    files = cd.get("files", [])
    kit = p.get("marketing_kit") or {}

    def _file_url(fmt):
        return next((f.get("url") for f in files if f.get("format") == fmt), None)

    html_url = _file_url("html") or p.get("preview_url")
    pdf_url = _file_url("pdf") or p.get("preview_pdf_url")
    png_url = _file_url("png") or p.get("cover_url")

    kr = None
    if p.get("knowledge_record_id"):
        krd = await db.knowledge_records.find_one({"id": p["knowledge_record_id"]})
        if krd:
            kr = {"id": krd.get("id"), "code": krd.get("kr_code") or krd.get("record_code"),
                  "title": krd.get("title"), "record_class": krd.get("record_class"),
                  "verification_status": krd.get("verification_status"),
                  "treasure_standard_status": krd.get("treasure_standard_status"),
                  "source_label": krd.get("source_label")}

    src_asset = p.get("manufacturing_asset") or p.get("cover_vault_asset")
    src_url = src_asset.get("url") or src_asset.get("file_url") if isinstance(src_asset, dict) else None

    social = kit.get("social_kit")
    marketing_files = (kit.get("marketing_graphics") or []) + (
        list(social.values()) if isinstance(social, dict) else (social or []))

    previews = [
        _preview_item("html", "HTML Preview", bool(html_url), html_url, "HTML edition not rendered yet."),
        _preview_item("pdf", "PDF Preview", bool(pdf_url), pdf_url, "PDF not rendered yet."),
        _preview_item("png", "PNG Preview", bool(png_url), png_url, "No cover/PNG rendered yet."),
        _preview_item("mobile", "Mobile Preview", bool(html_url), html_url, "Needs the responsive HTML edition."),
        _preview_item("print", "Print Preview", bool(pdf_url), pdf_url, "Needs the print-ready PDF."),
        _preview_item("marketplace", "Marketplace Listing Preview", bool(p.get("store_graphic_url")),
                      p.get("store_graphic_url"), "Marketing kit not built yet."),
        _preview_item("thumbnail", "Thumbnail Preview", bool(p.get("thumbnail_url")),
                      p.get("thumbnail_url"), "Thumbnail not generated yet."),
        _preview_item("marketing", "Marketing Assets", bool(p.get("marketing_kit_ready")),
                      None, "Marketing kit not built yet.", files=marketing_files),
        _preview_item("product_files", "Product Files", bool(files), None,
                      "Customer deliverable not rendered yet.", files=files),
        _preview_item("source_assets", "Source Assets", bool(src_url), src_url,
                      "No Founder/vault source asset — cover was generated deterministically."),
        _preview_item("knowledge_record", "Knowledge Record", kr is not None, None,
                      "No Knowledge Record linked to this product."),
    ]

    na = ae.next_action(p, 91)
    esc = p.get("design_escalation")
    ver = p.get("verification") or {}
    recipe = pr.RECIPES.get(p.get("product_type"), {}).get("label", p.get("product_type"))

    escalation_reason = (esc or {}).get("stopped_reason") or (
        na["reason"] if na["needs_founder"] else "Ready for your publication decision.")
    root_cause = (esc or {}).get("stopped_reason")
    if not root_cause:
        root_cause = ("Outstanding publication requirements: " + ", ".join(m["publish_blockers"])
                      if m["publish_blockers"] else "No defects — product met the QRU Gold Standard™ automatically.")
    recommended_resolution = (esc or {}).get("decision_needed") or (
        "Approve for Publication — all gates pass." if m["publishable"]
        else "Complete the remaining requirements, then approve for publication.")

    if m["publishable"]:
        ai_recommendation = "Approve for Publication"
    elif esc and esc.get("category") == "knowledge_content":
        ai_recommendation = "Send to Verification / add Knowledge Record"
    elif esc and esc.get("category") == "creative_direction":
        ai_recommendation = "Request Revision (creative direction)"
    else:
        ai_recommendation = "Return to Factory"

    manufacturing_report = {
        "assembled": bool(p.get("assembled")),
        "manufactured_from_asset": p.get("manufactured_from_asset"),
        "content_chars": len(p.get("content") or ""),
        "formats_rendered": [f.get("format") for f in files],
        "primary_format": cd.get("primary_format"),
        "deliverable_ready": bool(p.get("deliverable_ready")),
        "deliverable_validated": bool(cd.get("validated")),
        "marketing_kit_ready": bool(p.get("marketing_kit_ready")),
        "autonomous_improvements": (p.get("design_gate") or {}).get("improvement_count", 0),
        "improved_categories": (p.get("design_gate") or {}).get("improved_categories", []),
        "created_at": p.get("created_at"), "updated_at": p.get("updated_at"),
        "manufactured_by": p.get("created_by"),
    }

    return {
        "id": p["id"], "product_code": p.get("product_code"),
        "title": p.get("title"), "product_type": p.get("product_type"),
        "product_status": p.get("status"), "recipe_used": recipe,
        "knowledge_record": kr, "manufacturing_report": manufacturing_report,
        "design_score": m["design_score"], "design_passed": m["design_passed"],
        "treasure_standard_status": m["treasure_status"], "treasure_standard": m["treasure_standard"],
        "factory_confidence": m["factory_confidence"], "confidence_band": m["confidence_band"],
        "confidence_components": m["confidence_components"],
        "data_health": m["data_health"], "data_health_label": m["data_health_label"],
        "data_health_emoji": m["data_health_emoji"], "data_health_reasons": m["data_health_reasons"],
        "marketplace_readiness": m["marketplace_readiness"],
        "escalation_reason": escalation_reason,
        "ai_confidence": ver.get("confidence_score"),
        "ai_recommendation": ai_recommendation,
        "root_cause": root_cause, "recommended_resolution": recommended_resolution,
        "verification_notes": ({
            "reviewer": ver.get("reviewer"), "decision": ver.get("decision"),
            "issues": ver.get("issues", []), "reasons": ver.get("reasons"),
            "autonomous": ver.get("autonomous"),
        } if ver else None),
        "publishable": m["publishable"], "publish_blockers": m["publish_blockers"],
        "before_after": (p.get("design_gate") or {}).get("before_after"),
        "gate_ladder": ae.gate_ladder(p, 91),
        "previews": previews, "cover_url": p.get("cover_url"),
    }


@router.get("/{pid}/evidence")
async def evidence(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    return await _evidence(p)



async def _apply(pid, action, actor, note=None):
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
        msg, ok = "Returned to Factory — Creative Studio™ & Design Director™ will re-run.", True
    elif action == "revise":
        upd = {"status": "Needs Revision", "creative_status": "Needs Revision", "founder_revision_requested_at": now, "updated_at": now}
        if note:
            upd["founder_revision_note"] = note
        await db.products.update_one({"id": pid}, {"$set": upd})
        msg = "Revision requested" + (" with your note." if note else " — routed back for correction.")
        ok = True
    elif action == "verify":
        await db.products.update_one({"id": pid}, {"$set": {"status": "Needs Verification", "verified": False, "updated_at": now}})
        msg, ok = "Sent to Verification™ — Product Protection™ will re-verify before it returns.", True
    elif action == "reject":
        await db.products.update_one({"id": pid}, {"$set": {"status": "Rejected", "founder_rejected_at": now, "updated_at": now}})
        msg, ok = "Product rejected — removed from the manufacturing line.", True
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


_ACTIONS = ("approve", "return", "revise", "verify", "reject", "archive", "hide")


class ActionInput(BaseModel):
    action: str
    note: Optional[str] = None


@router.post("/{pid}/action")
async def action(pid: str, data: ActionInput, user=Depends(get_current_user)):
    if data.action not in _ACTIONS:
        raise HTTPException(400, "Invalid action")
    return await _apply(pid, data.action, user["name"], data.note)


class BulkInput(BaseModel):
    action: str
    ids: List[str]


@router.post("/bulk")
async def bulk(data: BulkInput, user=Depends(get_current_user)):
    if data.action not in _ACTIONS:
        raise HTTPException(400, "Invalid action")
    results = [await _apply(pid, data.action, user["name"]) for pid in data.ids]
    return {"results": results, "processed": len(results), "succeeded": sum(1 for r in results if r["ok"])}
