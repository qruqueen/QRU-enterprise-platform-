"""QRU Commerce™ — API surface (Stripe checkout, storefront, revenue) + Stripe webhook."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from database import db
from auth import get_current_user
from models import clean
import commerce

router = APIRouter(prefix="/api/commerce", tags=["commerce"])
webhook_router = APIRouter(prefix="/api", tags=["commerce"])


@router.get("/storefront")
async def storefront(user=Depends(get_current_user)):
    return await commerce.storefront()


@router.get("/revenue")
async def revenue(user=Depends(get_current_user)):
    return await commerce.revenue_summary()


@router.get("/purchases")
async def purchases(user=Depends(get_current_user)):
    q = {"user_id": str(user["id"])}
    return clean(await db.purchases.find(q).sort("granted_at", -1).to_list(200))


class CheckoutInput(BaseModel):
    product_id: str
    origin_url: str


@router.post("/checkout")
async def checkout(data: CheckoutInput, request: Request, user=Depends(get_current_user)):
    res, err = await commerce.create_checkout(
        data.product_id, data.origin_url, str(request.base_url), user)
    if err:
        raise HTTPException(400, err)
    return res


@router.get("/checkout/status/{session_id}")
async def checkout_status(session_id: str, request: Request, user=Depends(get_current_user)):
    res, err = await commerce.checkout_status(session_id, str(request.base_url))
    if err:
        raise HTTPException(404, err)
    return res


@router.get("/download/{session_id}")
async def purchase_download(session_id: str, user=Depends(get_current_user)):
    res, err = await commerce.purchase_download(session_id, user)
    if err:
        raise HTTPException(404, err)
    return res


@router.get("/transactions")
async def transactions(user=Depends(get_current_user)):
    return clean(await db.payment_transactions.find().sort("created_at", -1).to_list(300))


@webhook_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        return await commerce.handle_webhook(body, signature, str(request.base_url))
    except Exception as e:
        raise HTTPException(400, f"Webhook error: {e}")
