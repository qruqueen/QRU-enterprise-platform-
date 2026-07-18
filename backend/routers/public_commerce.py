"""QRU Online™ purchase flow — buy an authorized ebook (Stripe Checkout, guest).

Prices are resolved SERVER-SIDE from the canonical book record (never from the client).
Delivery is the authorized EPUB, released only after Stripe confirms payment.
"""
import os
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest,
)

from database import db
import rendering_engine as re_engine

router = APIRouter(prefix="/api/public", tags=["qru-online-commerce"])

_PUBLISHED_QUERY = {"founder_authorization.authorized": True}
_STRIPE_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET") or None

# Secure delivery policy
_DOWNLOAD_TTL_HOURS = 72
_DOWNLOAD_MAX = 5


def _stripe() -> StripeCheckout:
    return StripeCheckout(api_key=_STRIPE_KEY, webhook_secret=_WEBHOOK_SECRET, webhook_url="")


async def _grant_fulfillment(session_id: str):
    """Idempotently mark an order paid and open a 72h delivery window (once).
    Repeated calls (poll or webhook) never duplicate the order or reset the window."""
    await db.book_purchases.update_one(
        {"session_id": session_id, "payment_status": {"$ne": "paid"}},
        {"$set": {
            "status": "completed",
            "payment_status": "paid",
            "paid_at": datetime.now(timezone.utc),
            "download_expires_at": datetime.now(timezone.utc) + timedelta(hours=_DOWNLOAD_TTL_HOURS),
            "download_count": 0,
            "updated_at": datetime.now(timezone.utc),
        }},
    )


def _price_for(book: dict) -> float:
    """The ebook price (falls back to list price). Server-side source of truth."""
    pr = book.get("pricing") or {}
    return float(pr.get("ebook_price") or pr.get("list_price") or 0)


def _epub_url(book: dict) -> str | None:
    return ((book.get("artifacts") or {}).get("design") or {}).get("ebook", {}).get("epub")


class CheckoutRequest(BaseModel):
    book_id: str
    origin_url: str


@router.post("/checkout")
async def create_checkout(req: CheckoutRequest, request: Request):
    book = await db.book_records.find_one({"id": req.book_id, **_PUBLISHED_QUERY}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="This title is not available.")
    amount = _price_for(book)
    if amount <= 0 or not _epub_url(book):
        raise HTTPException(status_code=400, detail="This title cannot be purchased yet.")

    host_url = str(request.base_url)
    stripe = StripeCheckout(api_key=_STRIPE_KEY, webhook_secret=_WEBHOOK_SECRET,
                            webhook_url=f"{host_url}api/public/webhook")
    session = await stripe.create_checkout_session(CheckoutSessionRequest(
        amount=amount, currency="usd",
        success_url=f"{req.origin_url}/purchase/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{req.origin_url}/book/{req.book_id}",
        metadata={"book_id": req.book_id, "kind": "ebook", "title": book.get("title", "")},
    ))
    await db.book_purchases.insert_one({
        "session_id": session.session_id, "book_id": req.book_id,
        "book_title": book.get("title"), "amount": amount, "currency": "usd",
        "status": "initiated", "payment_status": "pending",
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    })
    return {"checkout_url": session.url, "session_id": session.session_id}


@router.get("/checkout/status/{session_id}")
async def checkout_status(session_id: str):
    record = await db.book_purchases.find_one({"session_id": session_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Order not found.")
    if record.get("payment_status") != "paid":
        try:
            status = await _stripe().get_checkout_status(session_id)
            if status.payment_status == "paid" or status.status == "complete":
                await _grant_fulfillment(session_id)
                record = await db.book_purchases.find_one({"session_id": session_id}, {"_id": 0})
        except Exception:
            pass
    paid = record.get("payment_status") == "paid"
    return {
        "session_id": session_id,
        "payment_status": record.get("payment_status"),
        "book_id": record.get("book_id"),
        "book_title": record.get("book_title"),
        "download_url": f"/api/public/download/{session_id}" if paid else None,
    }


@router.get("/download/{session_id}")
async def download(session_id: str):
    """Secure EPUB delivery: requires paid status, within 72h, max 5 successful downloads.
    Reserves a download slot atomically; never exposes the raw asset path/URL."""
    now = datetime.now(timezone.utc)
    reserved = await db.book_purchases.find_one_and_update(
        {
            "session_id": session_id,
            "payment_status": "paid",
            "download_expires_at": {"$gt": now},
            "download_count": {"$lt": _DOWNLOAD_MAX},
        },
        {"$inc": {"download_count": 1}, "$set": {"last_download_at": now}},
        return_document=True,
    )
    if not reserved:
        # Distinguish why it failed, without leaking anything sensitive.
        rec = await db.book_purchases.find_one({"session_id": session_id}, {"_id": 0})
        if not rec or rec.get("payment_status") != "paid":
            raise HTTPException(status_code=403, detail="This download requires a completed purchase.")
        if rec.get("download_count", 0) >= _DOWNLOAD_MAX:
            raise HTTPException(status_code=410, detail="This download link has reached its limit (5 downloads).")
        raise HTTPException(status_code=410, detail="This download link has expired. Please contact QRU Press™.")

    book = await db.book_records.find_one({"id": reserved["book_id"], **_PUBLISHED_QUERY}, {"_id": 0})
    epub = _epub_url(book) if book else None
    path = os.path.join(re_engine.ASSET_DIR, epub.rsplit("/", 1)[-1]) if epub else None
    if not path or not os.path.exists(path):
        # roll back the reserved slot since we couldn't deliver
        await db.book_purchases.update_one({"session_id": session_id}, {"$inc": {"download_count": -1}})
        raise HTTPException(status_code=404, detail="Ebook file not available.")
    safe = "".join(ch for ch in (reserved.get("book_title") or "book") if ch.isalnum() or ch in " -_").strip()
    return FileResponse(path, media_type="application/epub+zip", filename=f"{safe}.epub")


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(default=None)):
    """Stripe webhook with signature verification + idempotent fulfillment.
    Always returns 200 so Stripe won't retry indefinitely on our own logic errors."""
    payload = await request.body()
    # Fail closed: never accept unsigned webhooks under LIVE keys.
    if _STRIPE_KEY.startswith("sk_live") and not _WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook signing secret not configured.")
    try:
        event = await _stripe().handle_webhook(payload, stripe_signature)
    except Exception:
        # Signature/verification failure — reject so Stripe knows it wasn't accepted.
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    # Idempotency: record the event id once; skip if already processed.
    if event.event_id:
        existing = await db.processed_webhook_events.find_one({"event_id": event.event_id})
        if existing:
            return {"received": True, "duplicate": True}
        await db.processed_webhook_events.insert_one(
            {"event_id": event.event_id, "type": event.event_type, "at": datetime.now(timezone.utc)}
        )

    if event.session_id and event.payment_status == "paid":
        await _grant_fulfillment(event.session_id)
    return {"received": True}

