"""QRU Universal Connector Framework™ — API surface (one uniform lifecycle for all platforms)
plus the Universal OAuth Framework™ (developer config, authorize, callback, test, disconnect)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from auth import get_current_user, require_super_admin
import connectors as cx
import oauth_framework as oauth

router = APIRouter(prefix="/api/connectors", tags=["connectors"])
# Public router — the OAuth provider redirects the browser here (no auth header available).
oauth_router = APIRouter(prefix="/api/oauth", tags=["connectors"])


@router.get("")
async def list_connectors(user=Depends(get_current_user)):
    items = await cx.list_connectors()
    return {"connectors": items, "lifecycle": cx.LIFECYCLE, "count": len(items)}


@router.get("/{platform_id}")
async def get_connector(platform_id: str, user=Depends(get_current_user)):
    c = await cx.get_connector(platform_id)
    if not c:
        raise HTTPException(404, "Unknown connector")
    return c


class ConnectInput(BaseModel):
    credentials: Optional[Dict[str, Any]] = None


@router.post("/{platform_id}/connect")
async def connect(platform_id: str, data: ConnectInput, user=Depends(get_current_user)):
    res, err = await cx.connect(platform_id, data.credentials or {}, user["name"])
    if err:
        raise HTTPException(400, err)
    return res


@router.post("/{platform_id}/verify")
async def verify(platform_id: str, user=Depends(get_current_user)):
    res, err = await cx.verify(platform_id)
    if err:
        raise HTTPException(404, err)
    return res


@router.get("/{platform_id}/manufacture-plan")
async def manufacture_plan(platform_id: str, user=Depends(get_current_user)):
    res, err = await cx.manufacture_plan(platform_id)
    if err:
        raise HTTPException(404, err)
    return res


class PublishInput(BaseModel):
    product_id: str


@router.post("/{platform_id}/publish")
async def publish(platform_id: str, data: PublishInput, user=Depends(get_current_user)):
    res, err = await cx.publish(platform_id, data.product_id, user["name"])
    if err:
        raise HTTPException(400, err)
    return res


# ----------------------- Universal OAuth Framework™ -----------------------
class DeveloperConfigInput(BaseModel):
    client_id: str
    client_secret: Optional[str] = ""
    redirect_uri: str


@router.get("/{platform_id}/developer-config")
async def get_developer_config(platform_id: str, user=Depends(require_super_admin)):
    if not oauth.provider(platform_id):
        raise HTTPException(404, "Unknown platform")
    return await oauth.get_developer_config(platform_id)


@router.post("/{platform_id}/developer-config")
async def set_developer_config(platform_id: str, data: DeveloperConfigInput, user=Depends(require_super_admin)):
    res, err = await oauth.set_developer_config(
        platform_id, data.client_id, data.client_secret, data.redirect_uri, user["name"])
    if err:
        raise HTTPException(400, err)
    return res


@router.delete("/{platform_id}/developer-config")
async def delete_developer_config(platform_id: str, user=Depends(require_super_admin)):
    await oauth.delete_developer_config(platform_id)
    return {"deleted": True}


@router.get("/{platform_id}/authorize-url")
async def authorize_url(platform_id: str, frontend_origin: str = "", user=Depends(get_current_user)):
    res, err = await oauth.build_authorize_url(platform_id, frontend_origin)
    if err:
        raise HTTPException(400, err)
    return res


@router.post("/{platform_id}/disconnect")
async def disconnect(platform_id: str, user=Depends(get_current_user)):
    await oauth.disconnect(platform_id)
    return await cx.get_connector(platform_id)


@oauth_router.get("/callback")
async def oauth_callback(request: Request, state: str = "", code: str = "", error: str = ""):
    origin, platform_id, ok, message = await oauth.handle_callback(state, code, error)
    base = origin or ""
    from urllib.parse import quote
    target = f"{base}/connectors?oauth={'success' if ok else 'error'}&platform={platform_id}&message={quote(message)}"
    return RedirectResponse(url=target)
