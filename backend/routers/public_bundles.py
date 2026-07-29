"""QRU Online™ Bundle purchase flow — buy one bundle, receive every included item.

A bundle price is resolved SERVER-SIDE from the published bundle (never the client). On the
first verified transition to paid, one confirmation email is sent with a single access link;
that link lists every included item's secure, expiring download. Fulfillment never depends on
email success. Phase 1 items are authorized EPUB books.
"""
import os
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest

from database import db
import rendering_engine as re_engine
import order_access
import qru_email
import bundles as bundle_engine

router = APIRouter(prefix="/api/public", tags=["qru-online-bundles"])

_PUBLISHED_BOOK = {"founder_authorization.authorized": True}
_STRIPE_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET") or None
_PUBLIC_APP_URL = os.environ.get("PUBLIC_APP_URL", "")
_DOWNLOAD_TTL_HOURS = 72
_DOWNLOAD_MAX = 5

BUNDLE_PURCHASES = "bundle_purchases"


def _order_ref() -> str:
    return "QRUB-" + uuid.uuid4().hex[:8].upper()


def _epub_url(book: dict):
    return ((book.get("artifacts") or {}).get("design") or {}).get("ebook", {}).get("epub")


def _customer_email(session_id: str):
    try:
        import stripe
        stripe.api_key = _STRIPE_KEY
        s = stripe.checkout.Session.retrieve(session_id)
        cd = (s.get("customer_details") or {}) if isinstance(s, dict) else {}
        return cd.get("email") or (s.get("customer_email") if isinstance(s, dict) else None)
    except Exception:
        return None


class BundleCheckoutRequest(BaseModel):
    bundle_id: str
    origin_url: str


@router.get("/bundles")
async def public_bundles():
    items = await bundle_engine.public_list()
    return {"bundles": items, "count": len(items)}


@router.get("/bundles/{key}")
async def public_bundle(key: str):
    b = await bundle_engine.public_get(key)
    if not b:
        raise HTTPException(404, "This bundle is not available.")
    return b


@router.post("/bundle-checkout")
async def bundle_checkout(req: BundleCheckoutRequest, request: Request):
    b = await bundle_engine.public_get(req.bundle_id)
    if not b:
        raise HTTPException(404, "This bundle is not available.")
    amount = float(b.get("price") or 0)
    if amount <= 0 or not b.get("items"):
        raise HTTPException(400, "This bundle cannot be purchased yet.")
    host_url = str(request.base_url)
    stripe = StripeCheckout(api_key=_STRIPE_KEY, webhook_secret=_WEBHOOK_SECRET,
                            webhook_url=f"{host_url}api/public/webhook")
    session = await stripe.create_checkout_session(CheckoutSessionRequest(
        amount=amount, currency="usd",
        success_url=f"{req.origin_url}/purchase/success?session_id={{CHECKOUT_SESSION_ID}}&kind=bundle",
        cancel_url=f"{req.origin_url}/bundle/{b['id']}",
        metadata={"bundle_id": b["id"], "kind": "bundle", "title": b.get("title", "")},
    ))
    await db[BUNDLE_PURCHASES].insert_one({
        "session_id": session.session_id, "bundle_id": b["id"], "bundle_title": b.get("title"),
        "item_ids": [i["id"] for i in b["items"]], "amount": amount, "currency": "usd",
        "origin_url": (req.origin_url or "").rstrip("/"),
        "status": "initiated", "payment_status": "pending",
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    })
    return {"checkout_url": session.url, "session_id": session.session_id}


async def _fulfill(session_id: str):
    now = datetime.now(timezone.utc)
    res = await db[BUNDLE_PURCHASES].update_one(
        {"session_id": session_id, "payment_status": {"$ne": "paid"}},
        {"$set": {"status": "completed", "payment_status": "paid", "paid_at": now,
                  "download_expires_at": now + timedelta(hours=_DOWNLOAD_TTL_HOURS),
                  "downloads": {}, "access_id": uuid.uuid4().hex, "order_ref": _order_ref(),
                  "updated_at": now}})
    order = await db[BUNDLE_PURCHASES].find_one({"session_id": session_id})
    return order, (res.modified_count == 1)


async def _send_email(order: dict):
    now = datetime.now(timezone.utc)
    email = order.get("customer_email")
    if not email:
        rec = {"status": "skipped", "provider": "resend", "error": "no customer email", "attempted_at": now}
        await db[BUNDLE_PURCHASES].update_one({"session_id": order["session_id"]}, {"$set": {"confirmation_email": rec}})
        return
    token = order_access.mint(order["access_id"], order["bundle_id"])
    origin = (order.get("origin_url") or _PUBLIC_APP_URL or "").rstrip("/")
    access_url = f"{origin}/bundle-access/{token}"
    expires = order.get("download_expires_at") or now
    html = qru_email.render_confirmation_html(
        book_title=f"{order.get('bundle_title') or 'your bundle'} ({len(order.get('item_ids') or [])} items)",
        amount=float(order.get("amount") or 0), currency=order.get("currency") or "usd",
        purchase_date=(order.get("paid_at") or now).strftime("%B %d, %Y"),
        order_ref=order.get("order_ref") or "", access_url=access_url,
        expires_str=expires.strftime("%B %d, %Y %H:%M UTC") if hasattr(expires, "strftime") else str(expires),
        download_max=_DOWNLOAD_MAX)
    status = await qru_email.send_confirmation(
        to=email, subject=f"Your QRU Press bundle — {order.get('bundle_title') or 'your bundle'}", html=html)
    await db[BUNDLE_PURCHASES].update_one({"session_id": order["session_id"]},
                                          {"$set": {"confirmation_email": {**status, "attempted_at": now}}})


async def _fulfill_and_notify(session_id: str):
    order, newly = await _fulfill(session_id)
    if not order or not newly:
        return order
    email = _customer_email(session_id)
    if email:
        await db[BUNDLE_PURCHASES].update_one({"session_id": session_id}, {"$set": {"customer_email": email}})
        order["customer_email"] = email
    await _send_email(order)
    return await db[BUNDLE_PURCHASES].find_one({"session_id": session_id})


def _stripe():
    return StripeCheckout(api_key=_STRIPE_KEY, webhook_secret=_WEBHOOK_SECRET, webhook_url="")


@router.get("/bundle-checkout/status/{session_id}")
async def bundle_status(session_id: str):
    record = await db[BUNDLE_PURCHASES].find_one({"session_id": session_id}, {"_id": 0})
    if not record:
        raise HTTPException(404, "Order not found.")
    if record.get("payment_status") != "paid":
        try:
            st = await _stripe().get_checkout_status(session_id)
            if st.payment_status == "paid" or st.status == "complete":
                await _fulfill_and_notify(session_id)
                record = await db[BUNDLE_PURCHASES].find_one({"session_id": session_id}, {"_id": 0})
        except Exception:
            pass
    paid = record.get("payment_status") == "paid"
    return {"session_id": session_id, "payment_status": record.get("payment_status"),
            "kind": "bundle", "bundle_id": record.get("bundle_id"),
            "bundle_title": record.get("bundle_title"),
            "access_token": order_access.mint(record["access_id"], record["bundle_id"]) if paid and record.get("access_id") else None}


@router.get("/bundle-access/{token}")
async def bundle_access(token: str):
    try:
        payload = order_access.verify(token)
    except order_access.TokenExpired:
        raise HTTPException(410, "This access link has expired. Please contact QRU Press™.")
    except order_access.TokenInvalid:
        raise HTTPException(403, "Invalid access link.")
    order = await db[BUNDLE_PURCHASES].find_one({"access_id": payload["aid"], "payment_status": "paid"}, {"_id": 0})
    if not order:
        raise HTTPException(403, "This link requires a completed purchase.")
    books = {b["id"]: b async for b in db.book_records.find({"id": {"$in": order.get("item_ids", [])}}, {"_id": 0})}
    items = []
    for iid in order.get("item_ids", []):
        b = books.get(iid)
        if not b:
            continue
        items.append({"id": iid, "title": b.get("title"), "author": b.get("author"),
                      "cover_thumb": f"/api/public/books/{iid}/cover-thumb",
                      "download_url": f"/api/public/bundle-download/{order['access_id']}/{iid}"})
    return {"bundle_title": order.get("bundle_title"), "order_ref": order.get("order_ref"),
            "expires_at": order.get("download_expires_at"), "download_max": _DOWNLOAD_MAX, "items": items}


@router.get("/bundle-download/{access_id}/{book_id}")
async def bundle_download(access_id: str, book_id: str):
    now = datetime.now(timezone.utc)
    order = await db[BUNDLE_PURCHASES].find_one(
        {"access_id": access_id, "payment_status": "paid", "download_expires_at": {"$gt": now}}, {"_id": 0})
    if not order:
        rec = await db[BUNDLE_PURCHASES].find_one({"access_id": access_id}, {"_id": 0})
        if not rec or rec.get("payment_status") != "paid":
            raise HTTPException(403, "This download requires a completed purchase.")
        raise HTTPException(410, "This download link has expired. Please contact QRU Press™.")
    if book_id not in (order.get("item_ids") or []):
        raise HTTPException(404, "That item is not part of this bundle.")
    used = int((order.get("downloads") or {}).get(book_id, 0))
    if used >= _DOWNLOAD_MAX:
        raise HTTPException(410, "This item has reached its download limit (5 downloads).")
    book = await db.book_records.find_one({"id": book_id, **_PUBLISHED_BOOK}, {"_id": 0})
    epub = _epub_url(book) if book else None
    path = os.path.join(re_engine.ASSET_DIR, epub.rsplit("/", 1)[-1]) if epub else None
    if path and not os.path.exists(path):
        import storage
        await storage.aensure_local(os.path.basename(path), path)
    if not path or not os.path.exists(path):
        raise HTTPException(404, "Ebook file not available.")
    await db[BUNDLE_PURCHASES].update_one({"access_id": access_id},
                                          {"$set": {f"downloads.{book_id}": used + 1, "last_download_at": now}})
    safe = "".join(ch for ch in (book.get("title") or "book") if ch.isalnum() or ch in " -_").strip()
    return FileResponse(path, media_type="application/epub+zip", filename=f"{safe}.epub")
