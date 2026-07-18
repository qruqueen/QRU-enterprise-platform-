"""QRU Online™ purchase flow — buy an authorized ebook (Stripe Checkout, guest).

Prices are resolved SERVER-SIDE from the canonical book record (never from the client).
Delivery is the authorized EPUB, released only after Stripe confirms payment.
"""
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
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
    stripe = StripeCheckout(api_key=_STRIPE_KEY, webhook_url=f"{host_url}api/webhook/stripe")
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
        stripe = StripeCheckout(api_key=_STRIPE_KEY, webhook_url="")
        try:
            status = await stripe.get_checkout_status(session_id)
            if status.payment_status == "paid" or status.status == "complete":
                await db.book_purchases.update_one(
                    {"session_id": session_id, "payment_status": {"$ne": "paid"}},
                    {"$set": {"status": "completed", "payment_status": "paid",
                              "updated_at": datetime.now(timezone.utc)}},
                )
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
    record = await db.book_purchases.find_one({"session_id": session_id}, {"_id": 0})
    if not record or record.get("payment_status") != "paid":
        raise HTTPException(status_code=403, detail="This download requires a completed purchase.")
    book = await db.book_records.find_one({"id": record["book_id"], **_PUBLISHED_QUERY}, {"_id": 0})
    epub = _epub_url(book) if book else None
    if not epub:
        raise HTTPException(status_code=404, detail="Ebook file not available.")
    path = os.path.join(re_engine.ASSET_DIR, epub.rsplit("/", 1)[-1])
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Ebook file not available.")
    safe = "".join(ch for ch in (record.get("book_title") or "book") if ch.isalnum() or ch in " -_").strip()
    return FileResponse(path, media_type="application/epub+zip", filename=f"{safe}.epub")
