"""QRU Manufacturing Director™ (MO-005) — API surface.

Deterministic supervisory review of manufacturing orders. The Director's verdict is always
evidence-based; the optional AI executive brief never changes it (Treasure Standard™).
"""
from fastapi import APIRouter, Depends, HTTPException

from database import db
from auth import get_current_user, require_super_admin
from models import now_iso
import manufacturing_director as director

router = APIRouter(prefix="/api/director", tags=["director"])


@router.post("/manufacture-cleared")
async def manufacture_cleared(user=Depends(require_super_admin)):
    """One-click: launch manufacturing for every Director-CLEARED order. Each launch re-passes the
    deterministic Quality Gates; skipped orders are returned with an explicit reason."""
    return await director.manufacture_cleared(user["id"], user["name"])


@router.get("/queue")
async def queue(user=Depends(get_current_user)):
    """Fast deterministic verdicts for every manufacturing order (no AI)."""
    return await director.review_queue()


@router.get("/review/{order_id}")
async def review(order_id: str, use_ai: bool = False, user=Depends(get_current_user)):
    """Full Director review of one order. Pass use_ai=true to request an LLM executive brief
    (falls back to a deterministic brief when the AI budget is capped)."""
    o = await db.manufacturing_orders.find_one({"id": order_id})
    if not o:
        raise HTTPException(404, "Manufacturing order not found")
    return await director.review_order(o, use_ai=use_ai)


@router.post("/review/{order_id}/decision")
async def apply_decision(order_id: str, user=Depends(get_current_user)):
    """Apply the Director's deterministic recommendation to the order status and record it."""
    o = await db.manufacturing_orders.find_one({"id": order_id})
    if not o:
        raise HTTPException(404, "Manufacturing order not found")
    r = await director.review_order(o, use_ai=False)
    new_status = r["recommended_status"]
    history = o.get("approval_history", [])
    # Idempotency: skip if the order is already at the recommended status via the same Director verdict.
    if o.get("status") == new_status and o.get("director_verdict") == r["verdict"]:
        return {"applied": False, "verdict": r["verdict"], "new_status": new_status,
                "confidence": r["confidence"], "note": "Already applied — no change."}
    history.append({
        "stage": new_status,
        "by": f"Manufacturing Director™ (on behalf of {user['name']})",
        "verdict": r["verdict"],
        "confidence": r["confidence"],
        "at": now_iso(),
    })
    await db.manufacturing_orders.update_one(
        {"id": order_id},
        {"$set": {"status": new_status, "approval_history": history,
                  "director_verdict": r["verdict"], "director_confidence": r["confidence"],
                  "director_reviewed_at": now_iso(), "updated_at": now_iso()}},
    )
    return {"applied": True, "verdict": r["verdict"], "new_status": new_status, "confidence": r["confidence"]}
