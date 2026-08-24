"""Secure QRU Online checkout + fulfillment for non-book digital products."""
import os, uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
from database import db
import rendering_engine as re_engine
import order_access, qru_email

router = APIRouter(prefix="/api/public", tags=["qru-online-product-commerce"])
_STRIPE_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET") or None
_PUBLIC_APP_URL = os.environ.get("PUBLIC_APP_URL", "")
_TTL_HOURS, _MAX = 72, 5
_COLL = "product_purchases"
_FORMATS = ("pdf", "png", "jpg", "jpeg", "html", "mp3", "mp4", "pptx", "epub")
_MEDIA = {"pdf":"application/pdf","png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg","html":"text/html","mp3":"audio/mpeg","mp4":"video/mp4","pptx":"application/vnd.openxmlformats-officedocument.presentationml.presentation","epub":"application/epub+zip"}

def _stripe(): return StripeCheckout(api_key=_STRIPE_KEY, webhook_secret=_WEBHOOK_SECRET, webhook_url="")
def _order_ref(): return "QRUP-" + uuid.uuid4().hex[:8].upper()
def _price(p):
    try: return float(p.get("price") or 0)
    except (TypeError, ValueError): return 0.0

def _file(p):
    files = ((p.get("customer_deliverable") or {}).get("files") or [])
    priority = {f:i for i,f in enumerate(_FORMATS)}
    valid = []
    for x in files:
        if not isinstance(x, dict): continue
        fn = os.path.basename(str(x.get("filename") or ""))
        fmt = str(x.get("format") or (fn.rsplit(".",1)[-1] if "." in fn else "")).lower()
        if fn.startswith("deliverable-") and fmt in priority: valid.append({"filename":fn,"format":fmt})
    return sorted(valid, key=lambda x:(priority[x["format"]],x["filename"]))[0] if valid else None

def readiness(p):
    f = _file(p); price = _price(p)
    return {"purchasable": bool(price > 0 and f), "price": price if price > 0 else None,
            "currency":"USD", "purchase_format": f.get("format") if f else None}

def _email(session_id):
    try:
        import stripe; stripe.api_key = _STRIPE_KEY
        s = stripe.checkout.Session.retrieve(session_id); cd = s.get("customer_details") or {}
        return cd.get("email") or s.get("customer_email")
    except Exception: return None

async def _fulfill(session_id):
    now = datetime.now(timezone.utc)
    res = await db[_COLL].update_one({"session_id":session_id,"payment_status":{"$ne":"paid"}}, {"$set":{
        "status":"completed","payment_status":"paid","paid_at":now,"download_expires_at":now+timedelta(hours=_TTL_HOURS),
        "download_count":0,"access_id":uuid.uuid4().hex,"order_ref":_order_ref(),"updated_at":now}})
    return await db[_COLL].find_one({"session_id":session_id}), res.modified_count == 1

async def _notify(order):
    email = order.get("customer_email")
    if not email: return
    token = order_access.mint(order["access_id"], order["product_id"])
    origin = (order.get("origin_url") or _PUBLIC_APP_URL or "").rstrip("/")
    html = qru_email.render_confirmation_html(book_title=order.get("product_title") or "your QRU product",
        amount=float(order.get("amount") or 0),currency=order.get("currency") or "usd",
        purchase_date=(order.get("paid_at") or datetime.now(timezone.utc)).strftime("%B %d, %Y"),
        order_ref=order.get("order_ref") or "",access_url=f"{origin}/api/public/product-order/{token}/download",
        expires_str=order["download_expires_at"].strftime("%B %d, %Y %H:%M UTC"),download_max=_MAX)
    html = html.replace("Your copy of", "Your purchase of").replace("Access your book", "Download your product")
    status = await qru_email.send_confirmation(to=email, subject=f"Your QRU Press purchase — {order.get('product_title') or 'your product'}", html=html)
    await db[_COLL].update_one({"session_id":order["session_id"]},{"$set":{"confirmation_email":{**status,"attempted_at":datetime.now(timezone.utc)}}})

async def _confirm(session_id):
    order, newly = await _fulfill(session_id)
    if order and newly:
        email = _email(session_id)
        if email:
            await db[_COLL].update_one({"session_id":session_id},{"$set":{"customer_email":email}}); order["customer_email"] = email
        await _notify(order)
    return await db[_COLL].find_one({"session_id":session_id})

class CheckoutIn(BaseModel):
    product_id: str
    origin_url: str

@router.get("/product-purchase-readiness/{product_id}")
async def product_purchase_readiness(product_id: str):
    p = await db.products.find_one({"id":product_id,"status":"Published"},{"_id":0})
    if not p: raise HTTPException(404,"This product is not available.")
    return {"product_id":product_id, **readiness(p)}

@router.post("/product-checkout")
async def product_checkout(data: CheckoutIn, request: Request):
    p = await db.products.find_one({"id":data.product_id,"status":"Published"},{"_id":0})
    if not p: raise HTTPException(404,"This product is not available.")
    amount, deliverable = _price(p), _file(p)
    if amount <= 0 or not deliverable: raise HTTPException(400,"This product cannot be purchased yet.")
    stripe = StripeCheckout(api_key=_STRIPE_KEY, webhook_secret=_WEBHOOK_SECRET, webhook_url=f"{str(request.base_url)}api/public/webhook")
    s = await stripe.create_checkout_session(CheckoutSessionRequest(amount=amount,currency="usd",
        success_url=f"{data.origin_url}/purchase/success?session_id={{CHECKOUT_SESSION_ID}}&kind=product",
        cancel_url=f"{data.origin_url}/product/{p['id']}",metadata={"product_id":p["id"],"kind":"product","title":p.get("title","")}))
    await db[_COLL].insert_one({"session_id":s.session_id,"product_id":p["id"],"product_title":p.get("title"),
        "deliverable":deliverable,"amount":amount,"currency":"usd","origin_url":data.origin_url.rstrip("/"),
        "status":"initiated","payment_status":"pending","created_at":datetime.now(timezone.utc),"updated_at":datetime.now(timezone.utc)})
    return {"checkout_url":s.url,"session_id":s.session_id}

@router.get("/product-checkout/status/{session_id}")
async def status(session_id: str):
    order = await db[_COLL].find_one({"session_id":session_id},{"_id":0})
    if not order: raise HTTPException(404,"Order not found.")
    if order.get("payment_status") != "paid":
        try:
            s = await _stripe().get_checkout_status(session_id)
            if s.payment_status == "paid" or s.status == "complete": order = await _confirm(session_id)
        except Exception: pass
    paid = order.get("payment_status") == "paid"
    return {"session_id":session_id,"payment_status":order.get("payment_status"),"kind":"product",
            "product_id":order.get("product_id"),"product_title":order.get("product_title"),
            "format":(order.get("deliverable") or {}).get("format"),
            "download_url":f"/api/public/product-download/{session_id}" if paid else None}

async def _serve(order):
    now = datetime.now(timezone.utc)
    if order.get("payment_status") != "paid": raise HTTPException(403,"This download requires a completed purchase.")
    if not order.get("download_expires_at") or order["download_expires_at"] <= now: raise HTTPException(410,"This download link has expired.")
    f = order.get("deliverable") or {}; fn = os.path.basename(str(f.get("filename") or "")); fmt = str(f.get("format") or "").lower()
    if not fn.startswith("deliverable-") or fmt not in _FORMATS: raise HTTPException(404,"Purchased file is not available.")
    path = os.path.join(re_engine.ASSET_DIR, fn)
    if not os.path.exists(path):
        import storage; await storage.aensure_local(fn, path)
    if not os.path.exists(path): raise HTTPException(404,"Purchased file is not available.")
    reserved = await db[_COLL].find_one_and_update({"session_id":order["session_id"],"payment_status":"paid","download_expires_at":{"$gt":now},"download_count":{"$lt":_MAX}},
        {"$inc":{"download_count":1},"$set":{"last_download_at":now}},return_document=True)
    if not reserved: raise HTTPException(410,"This secure download is no longer available.")
    title = "".join(c for c in (order.get("product_title") or "QRU Product") if c.isalnum() or c in " ._-").strip() or "QRU Product"
    return FileResponse(path,media_type=_MEDIA.get(fmt,"application/octet-stream"),filename=f"{title}.{fmt}",headers={"Cache-Control":"private, no-store, max-age=0"})

@router.get("/product-download/{session_id}")
async def download(session_id: str):
    order = await db[_COLL].find_one({"session_id":session_id})
    if not order: raise HTTPException(404,"Order not found.")
    return await _serve(order)

@router.get("/product-order/{token}/download")
async def token_download(token: str):
    try: payload = order_access.verify(token)
    except order_access.TokenExpired: raise HTTPException(410,"This access link has expired.")
    except order_access.TokenInvalid: raise HTTPException(403,"This access link is invalid.")
    order = await db[_COLL].find_one({"access_id":payload["aid"]})
    if not order or order.get("product_id") != payload.get("bid"): raise HTTPException(403,"This access link is invalid.")
    return await _serve(order)
