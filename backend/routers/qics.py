"""QRU Intelligent Companion System™ (QICS) — API surface (MO-018 + FR-096)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from database import db
from auth import get_current_user, require_super_admin
from models import gen_id, now_iso
import qics
import trust_authenticity as ta

router = APIRouter(prefix="/api/qics", tags=["qics"])


def _clean(doc):
    doc.pop("_id", None)
    return doc


def _base_url(request: Request):
    return str(request.base_url).rstrip("/")


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return qics.config()


async def _load(ident):
    return (await db.products.find_one({"id": ident})
            or await db.products.find_one({"product_code": ident})
            or await db.products.find_one({"qics_identity": ident}))


@router.post("/activate/{product_id}")
async def activate(product_id: str, request: Request, user=Depends(require_super_admin)):
    """FR-096 — connect a Gold Standard product to its Companion Portal: mint identity, register trust,
    build the portal, and generate the permanent dynamic QR gateway. Archives the master record."""
    p = await _load(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    identity = await qics.assign_identity(db, p)
    p["qics_identity"] = identity

    # Register in the Trust & Authenticity Registry™ (MO-016).
    rec = await ta.registry_record(p)
    cert = await ta.authenticity_certificate(p, _base_url(request))
    await db.trust_registry.update_one({"product_id": p["id"]},
        {"$set": {"id": gen_id(), "product_id": p["id"], "product_code": p.get("product_code"),
                  "title": p.get("title"), "registry": rec, "certificate_id": cert["authenticity_certificate"],
                  "verify_url": cert["verify_url"], "registered_by": user["name"], "registered_at": now_iso()}}, upsert=True)

    portal = await qics.companion_portal(db, p)
    portal_url = f"{_base_url(request)}/api/qics/portal/{identity}"
    qr = ta.qr_svg_data_url(portal_url)
    doc = {
        "id": gen_id(), "product_id": p["id"], "product_code": p.get("product_code"),
        "qics_identity": identity, "title": p.get("title"), "portal": portal,
        "portal_url": portal_url, "destination_url": portal_url, "qr_code": qr,
        "activated_by": user["name"], "activated_at": now_iso(), "archived": True,
    }
    await db.qics_portals.update_one({"product_id": p["id"]}, {"$set": doc}, upsert=True)
    return _clean(doc)


class DestinationInput(BaseModel):
    destination_url: str


@router.put("/portal/{identity}/destination")
async def update_destination(identity: str, data: DestinationInput, user=Depends(require_super_admin)):
    """Dynamic QR — the QR image is preserved forever; only its destination is updated."""
    r = await db.qics_portals.update_one({"qics_identity": identity}, {"$set": {"destination_url": data.destination_url, "updated_at": now_iso()}})
    if not r.matched_count:
        raise HTTPException(404, "Companion portal not found")
    return {"updated": True, "qics_identity": identity, "destination_url": data.destination_url}


@router.get("/portals")
async def portals(user=Depends(get_current_user)):
    rows = await db.qics_portals.find({}, {"qr_code": 0}).sort("activated_at", -1).to_list(500)
    return {"portals": [_clean(r) for r in rows]}


@router.get("/portal/{identity}")
async def portal(identity: str, request: Request):
    """PUBLIC — the Intelligent Companion Portal™ reached by scanning the product QR. Records a scan."""
    rec = await db.qics_portals.find_one({"qics_identity": identity}) or await db.qics_portals.find_one({"product_code": identity})
    if not rec:
        raise HTTPException(404, "This QRU companion portal was not found.")
    p = await db.products.find_one({"id": rec["product_id"]}, {"content": 0})
    prev = await db.qics_events.count_documents({"product_id": rec["product_id"], "type": "scan"})
    await db.qics_events.insert_one({"id": gen_id(), "product_id": rec["product_id"], "qics_identity": identity,
                                     "type": "scan", "repeat": prev > 0, "at": now_iso()})
    # Refresh portal sections (live — product improves over time).
    fresh = await qics.companion_portal(db, p) if p else rec.get("portal")
    catalog = await db.products.find({}, {"content": 0}).sort("created_at", -1).to_list(300)
    return {
        "qics_identity": identity, "product_code": rec.get("product_code"), "title": rec.get("title"),
        "landing": qics.LANDING, "portal": fresh,
        "authenticity": {"treasure_standard_status": ta.treasure_status(p) if p else None,
                         "gold_standard_status": ta.gold_status(p) if p else None,
                         "qruseal": ta.QRU_SEAL, "verify_url": rec.get("verify_url")},
        "continuation": qics.continuation(p, catalog) if p else [],
    }


class EventInput(BaseModel):
    type: str


@router.post("/portal/{identity}/event")
async def portal_event(identity: str, data: EventInput, request: Request):
    """PUBLIC — record a companion analytics event (resource_download, video_view, audiobook_listen, etc.)."""
    rec = await db.qics_portals.find_one({"qics_identity": identity})
    if not rec:
        raise HTTPException(404, "Companion portal not found")
    if data.type not in qics.ANALYTICS_METRICS and data.type not in (
            "resource_download", "video_view", "audiobook_listen", "assessment_complete", "recommendation_click"):
        raise HTTPException(400, "Unknown event type.")
    await db.qics_events.insert_one({"id": gen_id(), "product_id": rec["product_id"], "qics_identity": identity,
                                     "type": data.type, "at": now_iso()})
    return {"recorded": True, "type": data.type}


@router.get("/analytics/{product_id}")
async def analytics(product_id: str, user=Depends(get_current_user)):
    p = await _load(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    events = await db.qics_events.find({"product_id": p["id"]}).to_list(5000)
    scans = [e for e in events if e["type"] == "scan"]
    counts = {}
    for e in events:
        counts[e["type"]] = counts.get(e["type"], 0) + 1
    return {
        "product_id": p["id"], "product_code": p.get("product_code"), "qics_identity": p.get("qics_identity"),
        "scan_count": len(scans),
        "repeat_scans": sum(1 for e in scans if e.get("repeat")),
        "resource_downloads": counts.get("resource_download", 0),
        "video_views": counts.get("video_view", 0),
        "audiobook_listens": counts.get("audiobook_listen", 0),
        "assessment_completion": counts.get("assessment_complete", 0),
        "recommendations_clicked": counts.get("recommendation_click", 0),
        "total_events": len(events),
        "by_type": counts,
    }
