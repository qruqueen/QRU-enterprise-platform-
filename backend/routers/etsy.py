"""QRU × Etsy integration routes — all under /api/integrations/etsy.

Founder-gated everywhere except the browser callback (which is secured by the OAuth state that
was minted for this Founder). Secrets/tokens are NEVER returned to the browser.
"""
import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

from auth import require_super_admin
import etsy_integration as etsy

router = APIRouter(prefix="/api/integrations/etsy", tags=["etsy"])


class ApproveInput(BaseModel):
    approved: bool = False
    taxonomy_id: Optional[int] = None


class PreviewInput(BaseModel):
    taxonomy_id: Optional[int] = None


def _origin(request: Request) -> str:
    # Prefer the forwarded origin (ingress) so preview & production both work.
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}"


@router.get("/status")
async def status(user=Depends(require_super_admin)):
    return await etsy.status()


@router.get("/connect")
async def connect(request: Request, user=Depends(require_super_admin)):
    """Returns the Etsy authorization URL (frontend redirects the browser to it)."""
    res, err = await etsy.build_authorize_url(_origin(request), user.get("name", "Founder"))
    if err:
        return {"error": err}
    return res


@router.get("/callback")
async def callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Browser redirect target from Etsy. Verifies state, exchanges code, then returns to the UI."""
    origin, ok, message = await etsy.handle_callback(state, code, error)
    base = origin or _origin(request)
    from urllib.parse import quote
    return RedirectResponse(f"{base}/etsy?connected={'1' if ok else '0'}&msg={quote(message)}")


@router.post("/disconnect")
async def disconnect(user=Depends(require_super_admin)):
    return await etsy.disconnect(user.get("name", "Founder"))


@router.post("/test")
async def test(user=Depends(require_super_admin)):
    return await etsy.test_connection()


@router.get("/diagnostics")
async def diagnostics(user=Depends(require_super_admin)):
    return await etsy.diagnostics()


@router.get("/listings")
async def listings(user=Depends(require_super_admin)):
    return await etsy.listings()


@router.get("/orders")
async def orders(user=Depends(require_super_admin)):
    return await etsy.orders()


@router.get("/products")
async def products(user=Depends(require_super_admin)):
    return await etsy.eligible_products()


@router.post("/products/{product_id}/preview")
async def preview(product_id: str, body: PreviewInput = PreviewInput(), user=Depends(require_super_admin)):
    return await etsy.preview(product_id, taxonomy_id=body.taxonomy_id)


@router.post("/products/{product_id}/publish")
async def publish(product_id: str, body: ApproveInput = ApproveInput(), user=Depends(require_super_admin)):
    return await etsy.publish_draft(product_id, user.get("name", "Founder"),
                                    approved=body.approved, taxonomy_id=body.taxonomy_id)


@router.post("/products/{product_id}/activate")
async def activate(product_id: str, body: ApproveInput = ApproveInput(), user=Depends(require_super_admin)):
    return await etsy.activate_listing(product_id, user.get("name", "Founder"), approved=body.approved)


@router.patch("/products/{product_id}")
async def update(product_id: str, user=Depends(require_super_admin)):
    return await etsy.update_listing(product_id, user.get("name", "Founder"))


@router.post("/products/{product_id}/sync")
async def sync(product_id: str, user=Depends(require_super_admin)):
    return await etsy.sync_status(product_id)
