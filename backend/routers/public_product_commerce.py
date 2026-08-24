"""Secure QRU Online checkout, fulfillment, and recovery for non-book digital products."""
import os
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest

from auth import require_super_admin
from database import db
import rendering_engine as re_engine
import order_access
import qru_email

router = APIRouter(prefix="/api/public", tags=["qru-online-product-commerce"])

_STRIPE_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET") or None
_PUBLIC_APP_URL = os.environ.get("PUBLIC_APP_URL", "")
_TTL_HOURS = 72
_MAX_DOWNLOADS = 5
_COLL = "product_purchases"
_FORMATS = ("pdf", "png", "jpg", "jpeg", "html", "mp3", "mp4", "pptx", "epub")
_MEDIA = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "html": "text/html",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "epub": "application/epub+zip",
}


def _stripe():
    return StripeCheckout(api_key=_STRIPE_KEY, webhook_secret=_WEBHOOK_SECRET, webhook_url="")


def _order_ref():
    return "QRUP-" + uuid.uuid4().hex[:8].upper()


def _price(product: dict) -> float:
    try:
        return float(product.get("price") or 0)
    except (TypeError, ValueError):
        return 0.0


def _deliverable(product: dict) -> dict | None:
    """Pick one canonical protected customer file, preferring PDF where present."""
    files = ((product.get("customer_deliverable") or {}).get("files") or [])
    priority = {fmt: i for i, fmt in enumerate(_FORMATS)}
    valid = []
    for item in files:
        if not isinstance(item, dict):
            continue
        filename = os.path.basename(str(item.get("filename") or ""))
        fmt = str(item.get("format") or (filename.rsplit(".", 1)[-1] if "." in filename else "")).lower()
        if filename.startswith("deliverable-") and fmt in priority:
            valid.append({"filename": filename, "format": fmt})
    return sorted(valid, key=lambda x: (priority[x["format"]], x["filename"]))[0] if valid else None


def readiness(product: dict) -> dict:
    file = _deliverable(product)
    price = _price(product)
    return {
        "purchasable": bool(price > 0 and file),
        "price": price if price > 0 else None,
        "currency": "USD",
        "purchase_format": file.get("format") if file else None,
    }


def _customer_email(session_id: str):
    try:
        import stripe
        stripe.api_key = _STRIPE_KEY
        session = stripe.checkout.Session.retrieve(session_id)
        details = session.get("customer_details") or {}
        return details.get("email") or session.get("customer_email")
    except Exception:
        return None


def _origin(order: dict) -> str:
    return (order.get("origin_url") or _PUBLIC_APP_URL or "").rstrip("/")


def _public_order(order: dict) -> dict:
    email = order.get("confirmation_email") or {}
    deliverable = order.get("deliverable") or {}
    created = order.get("created_at")
    paid = order.get("paid_at")
    expires = order.get("download_expires_at")
    return {
        "kind": "product",
        "session_id": order.get("session_id"),
        "product_id": order.get("product_id"),
        "product_title": order.get("product_title"),
        "format": deliverable.get("format"),
        "amount": order.get("amount"),
        "currency": order.get("currency") or "usd",
        "status": order.get("status"),
        "payment_status": order.get("payment_status"),
        "order_ref": order.get("order_ref"),
        "customer_email": order.get("customer_email"),
        "download_count": int(order.get("download_count") or 0),
        "download_max": _MAX_DOWNLOADS,
        "email_status": email.get("status"),
        "email_attempts": int(email.get("attempts") or (1 if email else 0)),
        "created_at": created.isoformat() if hasattr(created, "isoformat") else created,
        "paid_at": paid.isoformat() if hasattr(paid, "isoformat") else paid,
        "expires_at": expires.isoformat() if hasattr(expires, "isoformat") else expires,
    }


async def _fulfill(session_id: str):
    now = datetime.now(timezone.utc)
    result = await db[_COLL].update_one(
        {"session_id": session_id, "payment_status": {"$ne": "paid"}},
        {"$set": {
            "status": "completed",
            "payment_status": "paid",
            "paid_at": now,
            "download_expires_at": now + timedelta(hours=_TTL_HOURS),
            "download_count": 0,
            "access_id": uuid.uuid4().hex,
            "order_ref": _order_ref(),
            "updated_at": now,
        }},
    )
    order = await db[_COLL].find_one({"session_id": session_id})
    return order, result.modified_count == 1


async def _notify(order: dict):
    now = datetime.now(timezone.utc)
    previous_attempts = int(((order.get("confirmation_email") or {}).get("attempts") or 0))
    email_address = order.get("customer_email")

    if not email_address:
        status = {
            "status": "skipped",
            "provider": "resend",
            "provider_message_id": None,
            "error": "no customer email captured for this order",
        }
    else:
        token = order_access.mint(order["access_id"], order["product_id"])
        access_url = f"{_origin(order)}/api/public/product-order/{token}/download"
        expires = order.get("download_expires_at") or (now + timedelta(hours=_TTL_HOURS))
        html = qru_email.render_confirmation_html(
            book_title=order.get("product_title") or "your QRU product",
            amount=float(order.get("amount") or 0),
            currency=order.get("currency") or "usd",
            purchase_date=(order.get("paid_at") or now).strftime("%B %d, %Y"),
            order_ref=order.get("order_ref") or "",
            access_url=access_url,
            expires_str=expires.strftime("%B %d, %Y %H:%M UTC") if hasattr(expires, "strftime") else str(expires),
            download_max=_MAX_DOWNLOADS,
        )
        html = html.replace("Your copy of", "Your purchase of").replace("Access your book", "Download your product")
        status = await qru_email.send_confirmation(
            to=email_address,
            subject=f"Your QRU Press purchase — {order.get('product_title') or 'your product'}",
            html=html,
        )

    record = {**status, "attempted_at": now, "attempts": previous_attempts + 1}
    await db[_COLL].update_one(
        {"session_id": order["session_id"]},
        {"$set": {"confirmation_email": record, "updated_at": now}},
    )
    return record


async def _confirm(session_id: str):
    order, newly_paid = await _fulfill(session_id)
    if order and newly_paid:
        email_address = _customer_email(session_id)
        if email_address:
            await db[_COLL].update_one(
                {"session_id": session_id},
                {"$set": {"customer_email": email_address}},
            )
            order["customer_email"] = email_address
        await _notify(order)
    return await db[_COLL].find_one({"session_id": session_id})


async def _reconcile_payment(session_id: str):
    order = await db[_COLL].find_one({"session_id": session_id})
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.get("payment_status") == "paid":
        return order
    try:
        status = await _stripe().get_checkout_status(session_id)
    except Exception as exc:
        raise HTTPException(502, f"Could not verify this payment with Stripe: {type(exc).__name__}")
    if status.payment_status == "paid" or status.status == "complete":
        return await _confirm(session_id)
    return order


async def _recover_access(order: dict):
    """Restore a paid customer's delivery window when a Founder explicitly resends access."""
    now = datetime.now(timezone.utc)
    updates = {}
    if not order.get("access_id"):
        updates["access_id"] = uuid.uuid4().hex
    if not order.get("order_ref"):
        updates["order_ref"] = _order_ref()
    if not order.get("download_expires_at") or order["download_expires_at"] <= now or int(order.get("download_count") or 0) >= _MAX_DOWNLOADS:
        updates["download_expires_at"] = now + timedelta(hours=_TTL_HOURS)
        updates["download_count"] = 0
        updates["access_recovered_at"] = now
    if updates:
        updates["updated_at"] = now
        await db[_COLL].update_one({"session_id": order["session_id"]}, {"$set": updates})
        order = await db[_COLL].find_one({"session_id": order["session_id"]})
    return order


class CheckoutIn(BaseModel):
    product_id: str
    origin_url: str


@router.get("/product-purchase-readiness/{product_id}")
async def product_purchase_readiness(product_id: str):
    product = await db.products.find_one({"id": product_id, "status": "Published"}, {"_id": 0})
    if not product:
        raise HTTPException(404, "This product is not available.")
    return {"product_id": product_id, **readiness(product)}


@router.post("/product-checkout")
async def product_checkout(data: CheckoutIn, request: Request):
    product = await db.products.find_one({"id": data.product_id, "status": "Published"}, {"_id": 0})
    if not product:
        raise HTTPException(404, "This product is not available.")

    amount = _price(product)
    deliverable = _deliverable(product)
    if amount <= 0 or not deliverable:
        raise HTTPException(400, "This product cannot be purchased yet.")

    stripe = StripeCheckout(
        api_key=_STRIPE_KEY,
        webhook_secret=_WEBHOOK_SECRET,
        webhook_url=f"{str(request.base_url)}api/public/webhook",
    )
    session = await stripe.create_checkout_session(CheckoutSessionRequest(
        amount=amount,
        currency="usd",
        success_url=f"{data.origin_url}/purchase/success?session_id={{CHECKOUT_SESSION_ID}}&kind=product",
        cancel_url=f"{data.origin_url}/product/{product['id']}",
        metadata={"product_id": product["id"], "kind": "product", "title": product.get("title", "")},
    ))
    await db[_COLL].insert_one({
        "session_id": session.session_id,
        "product_id": product["id"],
        "product_title": product.get("title"),
        "deliverable": deliverable,
        "amount": amount,
        "currency": "usd",
        "origin_url": data.origin_url.rstrip("/"),
        "status": "initiated",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })
    return {"checkout_url": session.url, "session_id": session.session_id}


@router.get("/product-checkout/status/{session_id}")
async def product_checkout_status(session_id: str):
    order = await db[_COLL].find_one({"session_id": session_id}, {"_id": 0})
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.get("payment_status") != "paid":
        try:
            order = await _reconcile_payment(session_id)
        except HTTPException:
            pass
    paid = order.get("payment_status") == "paid"
    return {
        "session_id": session_id,
        "payment_status": order.get("payment_status"),
        "kind": "product",
        "product_id": order.get("product_id"),
        "product_title": order.get("product_title"),
        "format": (order.get("deliverable") or {}).get("format"),
        "download_url": f"/api/public/product-download/{session_id}" if paid else None,
    }


async def _serve(order: dict):
    now = datetime.now(timezone.utc)
    if order.get("payment_status") != "paid":
        raise HTTPException(403, "This download requires a completed purchase.")
    if not order.get("download_expires_at") or order["download_expires_at"] <= now:
        raise HTTPException(410, "This download link has expired. Please contact QRU Press™.")

    deliverable = order.get("deliverable") or {}
    filename = os.path.basename(str(deliverable.get("filename") or ""))
    fmt = str(deliverable.get("format") or "").lower()
    if not filename.startswith("deliverable-") or fmt not in _FORMATS:
        raise HTTPException(404, "Purchased file is not available.")

    path = os.path.join(re_engine.ASSET_DIR, filename)
    if not os.path.exists(path):
        import storage
        await storage.aensure_local(filename, path)
    if not os.path.exists(path):
        raise HTTPException(404, "Purchased file is not available.")

    reserved = await db[_COLL].find_one_and_update(
        {
            "session_id": order["session_id"],
            "payment_status": "paid",
            "download_expires_at": {"$gt": now},
            "download_count": {"$lt": _MAX_DOWNLOADS},
        },
        {"$inc": {"download_count": 1}, "$set": {"last_download_at": now}},
        return_document=True,
    )
    if not reserved:
        raise HTTPException(410, "This secure download is no longer available.")

    title = "".join(
        c for c in (order.get("product_title") or "QRU Product") if c.isalnum() or c in " ._-"
    ).strip() or "QRU Product"
    if not title.lower().endswith(f".{fmt}"):
        title = f"{title}.{fmt}"
    return FileResponse(
        path,
        media_type=_MEDIA.get(fmt, "application/octet-stream"),
        filename=title,
        headers={"Cache-Control": "private, no-store, max-age=0", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/product-download/{session_id}")
async def product_download(session_id: str):
    order = await db[_COLL].find_one({"session_id": session_id})
    if not order:
        raise HTTPException(404, "Order not found.")
    return await _serve(order)


@router.get("/product-order/{token}/download")
async def product_token_download(token: str):
    try:
        payload = order_access.verify(token)
    except order_access.TokenExpired:
        raise HTTPException(410, "This access link has expired.")
    except order_access.TokenInvalid:
        raise HTTPException(403, "This access link is invalid.")
    order = await db[_COLL].find_one({"access_id": payload["aid"]})
    if not order or order.get("product_id") != payload.get("bid"):
        raise HTTPException(403, "This access link is invalid.")
    return await _serve(order)


@router.get("/product-orders")
async def list_product_orders(user=Depends(require_super_admin)):
    rows = await db[_COLL].find({}, {"_id": 0}).sort("created_at", -1).to_list(300)
    orders = [_public_order(row) for row in rows]
    return {
        "orders": orders,
        "total": len(orders),
        "paid": sum(1 for row in orders if row["payment_status"] == "paid"),
        "provider_configured": qru_email.provider_configured(),
        "sender": qru_email.sender(),
    }


@router.post("/product-orders/{session_id}/reconcile")
async def reconcile_product_order(session_id: str, user=Depends(require_super_admin)):
    order = await _reconcile_payment(session_id)
    return {"order": _public_order(order)}


@router.post("/product-orders/{session_id}/resend-confirmation")
async def resend_product_confirmation(session_id: str, user=Depends(require_super_admin)):
    order = await _reconcile_payment(session_id)
    if order.get("payment_status") != "paid":
        raise HTTPException(400, "Only paid orders can receive product access.")

    if not order.get("customer_email"):
        email_address = _customer_email(session_id)
        if email_address:
            await db[_COLL].update_one({"session_id": session_id}, {"$set": {"customer_email": email_address}})
            order["customer_email"] = email_address

    order = await _recover_access(order)
    record = await _notify(order)
    return {
        "session_id": session_id,
        "confirmation_email": {
            "status": record.get("status"),
            "provider_message_id": record.get("provider_message_id"),
            "attempts": record.get("attempts"),
            "error": record.get("error"),
        },
        "order": _public_order(await db[_COLL].find_one({"session_id": session_id})),
    }
