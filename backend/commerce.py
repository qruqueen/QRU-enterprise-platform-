"""QRU Commerce™ — real Stripe checkout for published QRU products.

SECURITY: prices are ALWAYS resolved server-side from the product record / tier table.
The frontend only sends a product_id and its window origin. A payment_transactions
record is created before redirect and updated on status polling / webhook. Fulfillment
(library access + revenue) happens exactly once per session.
"""
import os
import logging

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse, CheckoutStatusResponse,
)

from database import db
from models import gen_id, now_iso
from org_activity import log_org

logger = logging.getLogger("qru.commerce")

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")

# Server-side price catalog (USD). Never trust the frontend for price.
PRICE_TIERS = {
    "Book": 14.99, "Course": 29.99, "AI Tutor": 19.99, "Presentation": 9.99,
    "Workbook": 9.99, "Caregiver Guide": 8.99, "Teacher Guide": 12.99,
    "Interactive Lesson": 7.99, "Lesson Plan": 6.99, "Podcast Script": 4.99,
    "Video Script": 4.99, "Printable PDF": 4.99, "Long Video": 6.99, "Short Video": 4.99,
    "Poster": 3.99, "Infographic": 3.99, "Flash Cards": 3.99, "Quiz": 2.99,
    "Short-form Content": 2.99, "Certificate": 1.99,
}
DEFAULT_PRICE = 9.99


def product_price(product: dict) -> float:
    p = product.get("price")
    if isinstance(p, (int, float)) and p > 0:
        return round(float(p), 2)
    return PRICE_TIERS.get(product.get("product_type"), DEFAULT_PRICE)


def _client(host_url: str) -> StripeCheckout:
    webhook_url = f"{host_url.rstrip('/')}/api/webhook/stripe"
    return StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)


async def ensure_stripe_connection():
    """Register Stripe as a Connected Payment platform in the Integration Hub (env-managed key)."""
    if not STRIPE_API_KEY:
        return
    existing = await db.integrations.find_one({"platform": "Stripe"})
    doc = existing or {"id": gen_id(), "platform": "Stripe", "created_at": now_iso()}
    doc.update({
        "category": "Payment", "auth_type": "api_key", "account_name": "QRU Store (Stripe)",
        "status": "Connected", "connection_health": "healthy", "env_managed": True,
        "last_sync": now_iso(), "updated_at": now_iso(),
    })
    if existing:
        await db.integrations.update_one({"id": doc["id"]}, {"$set": doc})
    else:
        await db.integrations.insert_one(dict(doc))


async def storefront():
    """Published products available for purchase, with server-side prices."""
    products = await db.products.find({"status": "Published"}).sort("updated_at", -1).to_list(200)
    return [{
        "id": p["id"], "product_code": p.get("product_code"), "title": p.get("title"),
        "product_type": p.get("product_type"), "family": p.get("family"),
        "topic": p.get("topic"), "cover_url": p.get("cover_url") or p.get("thumbnail_url"),
        "thumbnail_url": p.get("thumbnail_url"), "audience": p.get("audience"),
        "design_palette": p.get("design_palette"), "treasure_standard": bool(p.get("treasure_standard")),
        "license_type": p.get("license_type"), "price": product_price(p),
        "preview_url": p.get("preview_url"), "preview_pdf_url": p.get("preview_pdf_url"),
    } for p in products]


async def create_checkout(product_id, origin_url, host_url, user):
    product = await db.products.find_one({"id": product_id})
    if not product:
        return None, "Product not found"
    if product.get("status") != "Published":
        return None, "This product is not available for purchase yet."
    amount = product_price(product)
    origin = origin_url.rstrip("/")
    success_url = f"{origin}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/store"
    metadata = {
        "product_id": product_id, "product_code": product.get("product_code", ""),
        "user_id": str(user.get("id", "")), "user_email": user.get("email", ""),
        "source": "qru_store",
    }
    stripe = _client(host_url)
    req = CheckoutSessionRequest(amount=float(amount), currency="usd",
                                 success_url=success_url, cancel_url=cancel_url, metadata=metadata)
    try:
        session: CheckoutSessionResponse = await stripe.create_checkout_session(req)
    except Exception as e:
        logger.error(f"Stripe checkout failed: {e}")
        if not STRIPE_API_KEY:
            return None, "Payments aren't enabled on this store yet. Please check back soon."
        return None, "We couldn't start checkout right now. Please try again in a moment."
    await db.payment_transactions.insert_one({
        "id": gen_id(), "session_id": session.session_id, "product_id": product_id,
        "product_code": product.get("product_code", ""), "title": product.get("title", ""),
        "amount": float(amount), "currency": "usd", "metadata": metadata,
        "user_id": str(user.get("id", "")), "user_email": user.get("email", ""),
        "status": "initiated", "payment_status": "pending",
        "created_at": now_iso(), "updated_at": now_iso(),
    })
    await log_org("Commerce Director™", "Commerce", f"opened checkout for {product.get('product_code','')}", "", "info")
    return {"url": session.url, "session_id": session.session_id, "amount": amount, "title": product.get("title")}, None


async def _fulfill(txn):
    """Grant access + record the sale exactly once."""
    await db.purchases.insert_one({
        "id": gen_id(), "session_id": txn["session_id"], "product_id": txn["product_id"],
        "product_code": txn.get("product_code"), "title": txn.get("title"),
        "user_id": txn.get("user_id"), "user_email": txn.get("user_email"),
        "amount": txn.get("amount"), "currency": txn.get("currency", "usd"),
        "granted_at": now_iso(),
    })
    await db.products.update_one({"id": txn["product_id"]},
                                 {"$inc": {"sales_count": 1, "revenue_cents": int(round(txn.get("amount", 0) * 100))}})
    await log_org("Fulfillment™", "Commerce", f"completed sale of {txn.get('product_code','')}", "", "success")


async def checkout_status(session_id, host_url):
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn:
        return None, "Transaction not found"
    stripe = _client(host_url)
    status: CheckoutStatusResponse = await stripe.get_checkout_status(session_id)
    already_paid = txn.get("payment_status") == "paid"
    if status.payment_status == "paid" and not already_paid:
        await _fulfill(txn)
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"status": status.status, "payment_status": status.payment_status, "updated_at": now_iso()}})
    return {"status": status.status, "payment_status": status.payment_status,
            "amount_total": status.amount_total, "currency": status.currency,
            "title": txn.get("title"), "product_id": txn.get("product_id")}, None


async def handle_webhook(body: bytes, signature: str, host_url: str):
    stripe = _client(host_url)
    resp = await stripe.handle_webhook(body, signature)
    txn = await db.payment_transactions.find_one({"session_id": resp.session_id})
    if txn and resp.payment_status == "paid" and txn.get("payment_status") != "paid":
        await _fulfill(txn)
        await db.payment_transactions.update_one(
            {"session_id": resp.session_id},
            {"$set": {"status": "complete", "payment_status": "paid", "updated_at": now_iso()}})
    return {"received": True}


import rendering_engine as _re


async def purchase_download(session_id, user):
    """Deliver the manufactured product files to a paying customer.
    Verifies the payment is paid, then returns only files that actually exist on disk.
    Returns (payload, error) — error is a clear, customer-facing message, never generic."""
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn:
        return None, "We couldn't find this purchase."
    if txn.get("payment_status") != "paid":
        return None, "This payment hasn't completed yet. Once it clears, your download will appear here."
    product = await db.products.find_one({"id": txn.get("product_id")})
    if not product:
        return None, "This product is no longer available. Please contact support for a copy."

    cd = product.get("customer_deliverable") or {}
    raw_files = list(cd.get("files") or [])
    # Fall back to the primary customer file / cover if the deliverable list is empty.
    if not raw_files:
        for k, fmt in (("customer_url", "html"), ("preview_pdf_url", "pdf"), ("cover_url", "png")):
            if product.get(k):
                raw_files.append({"format": fmt, "url": product[k], "label": fmt.upper()})

    files = []
    for f in raw_files:
        url = f.get("url") or ""
        fname = url.rsplit("/", 1)[-1] if url else ""
        exists = bool(fname) and os.path.exists(os.path.join(_re.ASSET_DIR, fname))
        if exists:
            label = f.get("label") or f.get("format", "File").upper()
            dl = f"{url}?download=true&name={product.get('title','QRU Product')} - {label}"
            files.append({"format": f.get("format"), "label": label, "url": url, "download_url": dl})

    if not files:
        return None, "Your product file is being finalized — it will be ready in a moment. Please refresh shortly."
    return {"title": product.get("title"), "product_code": product.get("product_code"),
            "files": files, "primary_format": cd.get("primary_format")}, None


async def revenue_summary():
    paid = await db.payment_transactions.find({"payment_status": "paid"}).to_list(2000)
    total = round(sum(t.get("amount", 0) for t in paid), 2)
    connected = await db.integrations.count_documents({"category": "Payment", "status": "Connected"}) > 0
    return {
        "connected": connected, "provider": "Stripe" if STRIPE_API_KEY else None,
        "paid_orders": len(paid), "revenue_usd": total,
        "pending_orders": await db.payment_transactions.count_documents({"payment_status": "pending"}),
        "aov_usd": round(total / len(paid), 2) if paid else 0.0,
    }
