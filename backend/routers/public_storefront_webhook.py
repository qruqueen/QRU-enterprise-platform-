"""Unified Stripe webhook for QRU Online storefront commerce.

This handler routes a verified paid Checkout session to the correct idempotent fulfillment engine
(book, bundle, or non-book digital product). It marks an event processed only AFTER fulfillment
succeeds so Stripe can retry transient failures safely.
"""
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request
from emergentintegrations.payments.stripe.checkout import StripeCheckout

from database import db

router = APIRouter(prefix="/api/public", tags=["qru-online-webhook"])

_STRIPE_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET") or None


def _stripe():
    return StripeCheckout(api_key=_STRIPE_KEY, webhook_secret=_WEBHOOK_SECRET, webhook_url="")


async def _order_kind(session_id: str) -> str | None:
    if await db.product_purchases.find_one({"session_id": session_id}, {"_id": 1}):
        return "product"
    if await db.bundle_purchases.find_one({"session_id": session_id}, {"_id": 1}):
        return "bundle"
    if await db.book_purchases.find_one({"session_id": session_id}, {"_id": 1}):
        return "ebook"
    return None


async def _dispatch_verified_payment(session_id: str, kind: str):
    # Lazy imports avoid startup cycles while still reusing each commerce engine's proven,
    # idempotent paid-transition + customer-email logic.
    if kind == "product":
        from routers import public_product_commerce as commerce
        return await commerce._confirm(session_id)
    if kind == "bundle":
        from routers import public_bundles as commerce
        return await commerce._fulfill_and_notify(session_id)
    if kind == "ebook":
        from routers import public_commerce as commerce
        return await commerce._fulfill_and_notify(session_id)
    raise RuntimeError(f"unsupported storefront order kind: {kind}")


@router.post("/webhook")
async def storefront_webhook(request: Request, stripe_signature: str = Header(default=None)):
    payload = await request.body()

    # Live commerce must never accept unsigned payment events.
    if _STRIPE_KEY.startswith("sk_live") and not _WEBHOOK_SECRET:
        raise HTTPException(503, "Stripe webhook signing secret is not configured.")

    try:
        event = await _stripe().handle_webhook(payload, stripe_signature)
    except Exception:
        raise HTTPException(400, "Invalid Stripe webhook signature or payload.")

    # Only a verified paid Checkout session can fulfill an order.
    if not event.session_id or event.payment_status != "paid":
        return {"received": True, "ignored": True}

    event_id = event.event_id
    if event_id:
        prior = await db.processed_webhook_events.find_one({"event_id": event_id, "status": "processed"})
        if prior:
            return {"received": True, "duplicate": True}

    kind = await _order_kind(event.session_id)
    if not kind:
        # Do not acknowledge a paid-but-unregistered session as complete. A non-2xx response keeps
        # the event eligible for Stripe retry while the checkout/order write catches up or is repaired.
        raise HTTPException(503, "Paid Stripe session is not registered in a QRU storefront order yet.")

    try:
        order = await _dispatch_verified_payment(event.session_id, kind)
        if not order or order.get("payment_status") != "paid":
            raise RuntimeError("fulfillment did not reach paid state")
    except HTTPException:
        raise
    except Exception as exc:
        # Keep transient fulfillment/storage/database failures retryable by Stripe.
        raise HTTPException(503, f"Storefront fulfillment failed: {type(exc).__name__}")

    if event_id:
        await db.processed_webhook_events.update_one(
            {"event_id": event_id},
            {"$set": {
                "event_id": event_id,
                "type": event.event_type,
                "status": "processed",
                "session_id": event.session_id,
                "order_kind": kind,
                "processed_at": datetime.now(timezone.utc),
            }},
            upsert=True,
        )

    return {"received": True, "fulfilled": True, "kind": kind}
