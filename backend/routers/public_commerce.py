"""QRU Online™ purchase flow — buy an authorized ebook (Stripe Checkout, guest).

Prices are resolved SERVER-SIDE from the canonical book record (never from the client).
Delivery is the authorized EPUB, released only after Stripe confirms payment.

On the FIRST verified transition to paid, a QRU-branded confirmation email is sent (once) with a
signed, expiring access link. Fulfillment never depends on email success; a super-admin can resend
the confirmation without charging the customer again.
"""
import os
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Request, Header, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest,
)

from database import db
from auth import require_super_admin
import rendering_engine as re_engine
import order_access
import qru_email

router = APIRouter(prefix="/api/public", tags=["qru-online-commerce"])

_PUBLISHED_QUERY = {"founder_authorization.authorized": True}
_STRIPE_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET") or None
_PUBLIC_APP_URL = os.environ.get("PUBLIC_APP_URL", "")

# Secure delivery policy
_DOWNLOAD_TTL_HOURS = 72
_DOWNLOAD_MAX = 5


def _stripe() -> StripeCheckout:
    return StripeCheckout(api_key=_STRIPE_KEY, webhook_secret=_WEBHOOK_SECRET, webhook_url="")


def _order_ref() -> str:
    return "QRU-" + uuid.uuid4().hex[:8].upper()


def _customer_email(session_id: str) -> str | None:
    """Best-effort retrieval of the purchaser email captured by Stripe Checkout.
    Uses the raw Stripe SDK (same key as the wrapper). Never raises."""
    try:
        import stripe
        stripe.api_key = _STRIPE_KEY
        s = stripe.checkout.Session.retrieve(session_id)
        cd = (s.get("customer_details") or {}) if isinstance(s, dict) else {}
        return cd.get("email") or (s.get("customer_email") if isinstance(s, dict) else None)
    except Exception:
        return None


def _origin_for(order: dict) -> str:
    return (order.get("origin_url") or _PUBLIC_APP_URL or "").rstrip("/")


async def _fulfill(session_id: str) -> tuple[dict | None, bool]:
    """Idempotently mark an order paid + open a 72h delivery window (once). Returns
    (order, newly_paid). `newly_paid` is True only on the single atomic transition to paid, so
    replayed webhooks/polls never re-fulfill or re-send email."""
    now = datetime.now(timezone.utc)
    res = await db.book_purchases.update_one(
        {"session_id": session_id, "payment_status": {"$ne": "paid"}},
        {"$set": {
            "status": "completed",
            "payment_status": "paid",
            "paid_at": now,
            "download_expires_at": now + timedelta(hours=_DOWNLOAD_TTL_HOURS),
            "download_count": 0,
            "access_id": uuid.uuid4().hex,
            "order_ref": _order_ref(),
            "updated_at": now,
        }},
    )
    order = await db.book_purchases.find_one({"session_id": session_id})
    return order, (res.modified_count == 1)


async def _send_and_record(order: dict) -> dict:
    """Build + send the QRU confirmation and record delivery status on the order.
    Never raises; fulfillment is independent of the outcome."""
    now = datetime.now(timezone.utc)
    prev_attempts = ((order.get("confirmation_email") or {}).get("attempts") or 0)
    email = order.get("customer_email")

    if not email:
        status = {"status": "skipped", "provider": "resend", "provider_message_id": None,
                  "error": "no customer email captured for this order"}
    else:
        token = order_access.mint(order["access_id"], order["book_id"])
        access_url = f"{_origin_for(order)}/access/{token}"
        paid_at = order.get("paid_at") or now
        expires = order.get("download_expires_at") or (now + timedelta(hours=_DOWNLOAD_TTL_HOURS))
        html = qru_email.render_confirmation_html(
            book_title=order.get("book_title") or "your QRU book",
            amount=float(order.get("amount") or 0),
            currency=order.get("currency") or "usd",
            purchase_date=paid_at.strftime("%B %d, %Y") if hasattr(paid_at, "strftime") else str(paid_at),
            order_ref=order.get("order_ref") or "",
            access_url=access_url,
            expires_str=expires.strftime("%B %d, %Y %H:%M UTC") if hasattr(expires, "strftime") else str(expires),
            download_max=_DOWNLOAD_MAX,
        )
        status = await qru_email.send_confirmation(
            to=email, subject=f"Your QRU Press purchase — {order.get('book_title') or 'your book'}", html=html)

    record = {**status, "attempted_at": now, "attempts": prev_attempts + 1}
    await db.book_purchases.update_one(
        {"session_id": order["session_id"]}, {"$set": {"confirmation_email": record}})
    return record


async def _fulfill_and_notify(session_id: str):
    """Verified-payment entry point shared by the webhook and the status poll."""
    order, newly_paid = await _fulfill(session_id)
    if not order or not newly_paid:
        return order
    email = _customer_email(session_id)
    if email:
        await db.book_purchases.update_one(
            {"session_id": session_id}, {"$set": {"customer_email": email}})
        order["customer_email"] = email
    await _send_and_record(order)
    return await db.book_purchases.find_one({"session_id": session_id})


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
        "origin_url": (req.origin_url or "").rstrip("/"),
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
                await _fulfill_and_notify(session_id)
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


async def _serve_epub(match: dict):
    """Reserve a download slot atomically and stream the EPUB. `match` selects the order by a
    private key (session_id or access_id) — never a storage path. Requires paid + within window +
    under the download cap."""
    now = datetime.now(timezone.utc)
    reserved = await db.book_purchases.find_one_and_update(
        {**match, "payment_status": "paid",
         "download_expires_at": {"$gt": now}, "download_count": {"$lt": _DOWNLOAD_MAX}},
        {"$inc": {"download_count": 1}, "$set": {"last_download_at": now}},
        return_document=True,
    )
    if not reserved:
        rec = await db.book_purchases.find_one(match, {"_id": 0})
        if not rec or rec.get("payment_status") != "paid":
            raise HTTPException(status_code=403, detail="This download requires a completed purchase.")
        if rec.get("download_count", 0) >= _DOWNLOAD_MAX:
            raise HTTPException(status_code=410, detail="This download link has reached its limit (5 downloads).")
        raise HTTPException(status_code=410, detail="This download link has expired. Please contact QRU Press™.")

    book = await db.book_records.find_one({"id": reserved["book_id"], **_PUBLISHED_QUERY}, {"_id": 0})
    epub = _epub_url(book) if book else None
    path = os.path.join(re_engine.ASSET_DIR, epub.rsplit("/", 1)[-1]) if epub else None
    if path and not os.path.exists(path):
        import storage
        await storage.aensure_local(os.path.basename(path), path)
    if not path or not os.path.exists(path):
        await db.book_purchases.update_one({"session_id": reserved["session_id"]},
                                           {"$inc": {"download_count": -1}})
        raise HTTPException(status_code=404, detail="Ebook file not available.")
    safe = "".join(ch for ch in (reserved.get("book_title") or "book") if ch.isalnum() or ch in " -_").strip()
    return FileResponse(path, media_type="application/epub+zip", filename=f"{safe}.epub")


@router.get("/download/{session_id}")
async def download(session_id: str):
    """Legacy success-page delivery (kept working). Keyed by the session id."""
    return await _serve_epub({"session_id": session_id})


# ---------- Tokenized access (the link that goes in the QRU confirmation email) ----------

def _order_public_view(order: dict) -> dict:
    exp = order.get("download_expires_at")
    return {
        "book_title": order.get("book_title"),
        "order_ref": order.get("order_ref"),
        "amount": order.get("amount"),
        "currency": order.get("currency"),
        "expires_at": exp.isoformat() if hasattr(exp, "isoformat") else exp,
        "downloads_remaining": max(0, _DOWNLOAD_MAX - int(order.get("download_count", 0))),
        "download_max": _DOWNLOAD_MAX,
        "support_email": qru_email.support_email(),
    }


async def _order_from_token(token: str) -> dict:
    """Verify the token and resolve the paid order — fails safely on any tamper/expiry."""
    try:
        payload = order_access.verify(token)
    except order_access.TokenExpired:
        raise HTTPException(status_code=410, detail="This access link has expired.")
    except order_access.TokenInvalid:
        raise HTTPException(status_code=403, detail="This access link is invalid.")
    order = await db.book_purchases.find_one({"access_id": payload["aid"]})
    if not order or order.get("book_id") != payload["bid"]:
        raise HTTPException(status_code=403, detail="This access link is invalid.")
    if order.get("payment_status") != "paid":
        raise HTTPException(status_code=403, detail="This order is not paid.")
    return order


@router.get("/order/{token}")
async def order_access_info(token: str):
    """Metadata for the QRU access page (no file, no private ids)."""
    order = await _order_from_token(token)
    return _order_public_view(order)


@router.get("/order/{token}/download")
async def order_token_download(token: str):
    """Secure EPUB delivery via the signed email link (never exposes session id / file path)."""
    order = await _order_from_token(token)
    return await _serve_epub({"access_id": order["access_id"]})


class ResendRequest(BaseModel):
    session_id: str


@router.post("/orders/{session_id}/resend-confirmation")
async def resend_confirmation(session_id: str, user=Depends(require_super_admin)):
    """Authorized resend of the QRU confirmation — mints a FRESH access token and re-sends.
    Never contacts Stripe and never charges the customer again."""
    order = await db.book_purchases.find_one({"session_id": session_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    if order.get("payment_status") != "paid":
        raise HTTPException(status_code=400, detail="Only paid orders can be re-sent a confirmation.")
    if not order.get("access_id"):
        await db.book_purchases.update_one(
            {"session_id": session_id},
            {"$set": {"access_id": uuid.uuid4().hex, "order_ref": order.get("order_ref") or _order_ref()}})
        order = await db.book_purchases.find_one({"session_id": session_id})
    if not order.get("customer_email"):
        email = _customer_email(session_id)
        if email:
            await db.book_purchases.update_one({"session_id": session_id}, {"$set": {"customer_email": email}})
            order["customer_email"] = email
    record = await _send_and_record(order)
    return {"session_id": session_id, "confirmation_email": {
        "status": record["status"], "provider_message_id": record.get("provider_message_id"),
        "attempts": record["attempts"], "error": record.get("error")}}


@router.get("/orders")
async def list_orders(user=Depends(require_super_admin)):
    """QRU Online storefront orders (super-admin) — powers the Founder console + one-tap resend."""
    rows = await db.book_purchases.find({}, {"_id": 0}).sort("created_at", -1).to_list(300)
    out = []
    for o in rows:
        ce = o.get("confirmation_email") or {}
        paid_at, created = o.get("paid_at"), o.get("created_at")
        att = ce.get("attempted_at")
        out.append({
            "session_id": o.get("session_id"),
            "book_title": o.get("book_title"),
            "order_ref": o.get("order_ref"),
            "amount": o.get("amount"), "currency": o.get("currency"),
            "payment_status": o.get("payment_status"),
            "customer_email": o.get("customer_email"),
            "paid_at": paid_at.isoformat() if hasattr(paid_at, "isoformat") else paid_at,
            "created_at": created.isoformat() if hasattr(created, "isoformat") else created,
            "download_count": o.get("download_count", 0),
            "download_max": _DOWNLOAD_MAX,
            "email_status": ce.get("status"),
            "email_message_id": ce.get("provider_message_id"),
            "email_attempts": ce.get("attempts", 0),
            "email_attempted_at": att.isoformat() if hasattr(att, "isoformat") else att,
            "email_error": ce.get("error"),
        })
    return {"orders": out, "total": len(out),
            "paid": sum(1 for r in out if r["payment_status"] == "paid"),
            "provider_configured": qru_email.provider_configured(), "sender": qru_email.sender()}


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
        await _fulfill_and_notify(event.session_id)
    return {"received": True}
