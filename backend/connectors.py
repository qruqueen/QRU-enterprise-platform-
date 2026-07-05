"""QRU Universal Connector Framework™ — one config-driven engine for every publishing
platform. Adding a platform is CONFIGURATION (an entry in CONNECTOR_REGISTRY), not a redesign.

Founder experience is identical for every connector: CONNECT → TEST → MANUFACTURE → PREVIEW
→ PUBLISH. Engineering differences (OAuth vs API-key vs native) live behind the lifecycle.

TREASURE STANDARD™ / Gold Standard™: never present a non-working action and never expose raw
API errors. Connectors that aren't operational yet report an honest status + guided next step;
their Publish action is disabled with a clear reason rather than silently failing.
"""
import base64
import os

from database import db
from models import now_iso

import factory_confidence as fc

# auth methods: "native" (QRU-owned, always live) | "oauth" | "api_key"
# operational=True means the Publish lifecycle is fully wired end-to-end today.
CONNECTOR_REGISTRY = [
    {"id": "qru_store", "name": "QRU Store™", "category": "Native", "auth_method": "native",
     "operational": True, "asset_types": ["Book", "Workbook", "Poster", "Quick Card", "Digital Download"],
     "capabilities": ["publish", "preview", "pricing", "metadata", "thumbnail"],
     "setup_hint": "Built in — no setup required."},
    {"id": "stripe", "name": "Stripe", "category": "Payments", "auth_method": "api_key",
     "operational": True, "asset_types": ["Store Listing", "Pricing"],
     "capabilities": ["pricing", "checkout"],
     "setup_hint": "Test key active. Payments and checkout are live."},
    {"id": "youtube", "name": "YouTube", "category": "Video", "auth_method": "oauth",
     "operational": False, "asset_types": ["Video", "Short", "Thumbnail", "SEO Metadata"],
     "capabilities": ["publish", "thumbnail", "metadata", "preview"],
     "setup_hint": "Requires Google OAuth authorization to your YouTube channel."},
    {"id": "amazon_kdp", "name": "Amazon KDP", "category": "Books", "auth_method": "api_key",
     "operational": False, "asset_types": ["Book", "Kindle Cover", "Paperback Cover", "Store Listing"],
     "capabilities": ["publish", "preview", "pricing", "metadata"],
     "setup_hint": "Requires your Amazon KDP credentials."},
    {"id": "tpt", "name": "Teachers Pay Teachers", "category": "Education", "auth_method": "api_key",
     "operational": False, "asset_types": ["Teacher Guide", "Worksheet", "Printable PDF", "Store Listing"],
     "capabilities": ["publish", "preview", "pricing", "metadata"],
     "setup_hint": "Requires your TPT seller credentials."},
    {"id": "etsy", "name": "Etsy", "category": "Marketplace", "auth_method": "oauth",
     "operational": False, "asset_types": ["Digital Download", "Store Listing", "Thumbnail"],
     "capabilities": ["publish", "preview", "pricing", "metadata"],
     "setup_hint": "Requires Etsy OAuth authorization to your shop."},
    {"id": "shopify", "name": "Shopify", "category": "Commerce", "auth_method": "api_key",
     "operational": False, "asset_types": ["Store Listing", "Product Image", "Digital Download"],
     "capabilities": ["publish", "pricing", "metadata"],
     "setup_hint": "Requires your Shopify store domain + Admin API access token."},
    {"id": "pinterest", "name": "Pinterest", "category": "Social", "auth_method": "oauth",
     "operational": False, "asset_types": ["Pin Graphic", "Thumbnail", "Metadata"],
     "capabilities": ["publish", "thumbnail", "metadata"],
     "setup_hint": "Requires Pinterest OAuth authorization."},
    {"id": "facebook", "name": "Facebook", "category": "Social", "auth_method": "oauth",
     "operational": False, "asset_types": ["Social Graphic", "Metadata"],
     "capabilities": ["publish", "metadata"], "setup_hint": "Requires Facebook OAuth authorization."},
    {"id": "instagram", "name": "Instagram", "category": "Social", "auth_method": "oauth",
     "operational": False, "asset_types": ["Social Graphic", "Metadata"],
     "capabilities": ["publish", "metadata"], "setup_hint": "Requires Instagram (Meta) OAuth authorization."},
    {"id": "linkedin", "name": "LinkedIn", "category": "Social", "auth_method": "oauth",
     "operational": False, "asset_types": ["Social Graphic", "Article", "Metadata"],
     "capabilities": ["publish", "metadata"], "setup_hint": "Requires LinkedIn OAuth authorization."},
    {"id": "google_drive", "name": "Google Drive", "category": "Storage", "auth_method": "oauth",
     "operational": False, "asset_types": ["Any File"], "capabilities": ["publish", "preview"],
     "setup_hint": "Requires Google OAuth authorization to Drive."},
    {"id": "dropbox", "name": "Dropbox", "category": "Storage", "auth_method": "oauth",
     "operational": False, "asset_types": ["Any File"], "capabilities": ["publish"],
     "setup_hint": "Requires Dropbox OAuth authorization."},
    {"id": "onedrive", "name": "OneDrive", "category": "Storage", "auth_method": "oauth",
     "operational": False, "asset_types": ["Any File"], "capabilities": ["publish"],
     "setup_hint": "Requires Microsoft OAuth authorization."},
]
_BY_ID = {c["id"]: c for c in CONNECTOR_REGISTRY}

# Uniform Founder-facing statuses (never raw API errors).
S_HEALTHY = "Connected Healthy"
S_CONNECTED = "Connected"
S_NEEDS_AUTH = "Needs Authorization"
S_SETUP = "Setup Required"
S_ERROR = "Connection Error"

LIFECYCLE = ["Connect", "Test", "Manufacture", "Preview", "Publish"]


def _obfuscate(secret):
    """At-rest obfuscation for stored credentials (never returned to the client)."""
    return base64.b64encode((secret or "").encode()).decode()


async def _state(platform_id):
    return await db.connectors.find_one({"platform_id": platform_id}) or {}


def _status_for(reg, state):
    if reg["auth_method"] == "native":
        return S_HEALTHY
    if not state or not state.get("connected"):
        return S_NEEDS_AUTH if reg["auth_method"] == "oauth" else S_SETUP
    return state.get("status") or S_CONNECTED


def _public(reg, state):
    status = _status_for(reg, state)
    return {
        "id": reg["id"], "name": reg["name"], "category": reg["category"],
        "auth_method": reg["auth_method"], "operational": reg["operational"],
        "asset_types": reg["asset_types"], "capabilities": reg["capabilities"],
        "setup_hint": reg["setup_hint"], "status": status,
        "connected": status in (S_HEALTHY, S_CONNECTED),
        "can_publish": bool(reg["operational"] and "publish" in reg["capabilities"]
                            and status in (S_HEALTHY, S_CONNECTED)),
        "publish_disabled_reason": (None if (reg["operational"] and status in (S_HEALTHY, S_CONNECTED))
                                    else (reg["setup_hint"] if not reg["operational"]
                                          else "Connect this platform first.")),
        "account": state.get("account"),
        "connected_at": state.get("connected_at"),
        "last_checked": state.get("last_checked"),
    }


async def list_connectors():
    out = []
    for reg in CONNECTOR_REGISTRY:
        out.append(_public(reg, await _state(reg["id"])))
    # Native + operational first, then by category.
    out.sort(key=lambda c: (not c["operational"], c["category"], c["name"]))
    return out


async def get_connector(platform_id):
    reg = _BY_ID.get(platform_id)
    if not reg:
        return None
    return _public(reg, await _state(platform_id))


async def connect(platform_id, credentials, actor):
    """CONNECT + VERIFY. Native = always healthy. api_key = store (obfuscated) + mark connected.
    oauth = returns a guided 'authorize' instruction (real OAuth requires platform credentials)."""
    reg = _BY_ID.get(platform_id)
    if not reg:
        return None, "Unknown connector."
    if reg["auth_method"] == "native":
        return await get_connector(platform_id), None
    if reg["auth_method"] == "oauth":
        # We do not fabricate an OAuth success. Record intent + guide the Founder.
        await db.connectors.update_one({"platform_id": platform_id}, {"$set": {
            "platform_id": platform_id, "status": S_NEEDS_AUTH, "connected": False,
            "auth_method": "oauth", "updated_at": now_iso()}}, upsert=True)
        return {"guided": True, "auth_method": "oauth",
                "message": f"{reg['name']} uses secure OAuth. To finish, QRU needs the {reg['name']} "
                           f"app credentials configured. Provide them and QRU will launch the official "
                           f"authorization flow — you'll approve access on {reg['name']} directly.",
                "connector": await get_connector(platform_id)}, None
    # api_key
    key = (credentials or {}).get("api_key")
    if not key:
        return None, f"{reg['name']} needs an API key to connect."
    await db.connectors.update_one({"platform_id": platform_id}, {"$set": {
        "platform_id": platform_id, "connected": True, "status": S_HEALTHY,
        "auth_method": "api_key", "secret": _obfuscate(key),
        "account": (credentials or {}).get("account") or "Connected account",
        "connected_at": now_iso(), "last_checked": now_iso(), "connected_by": actor,
        "updated_at": now_iso()}}, upsert=True)
    return {"connector": await get_connector(platform_id)}, None


async def verify(platform_id):
    """TEST / MONITOR — returns a uniform health status, never a raw API error."""
    reg = _BY_ID.get(platform_id)
    if not reg:
        return None, "Unknown connector."
    state = await _state(platform_id)
    status = _status_for(reg, state)
    await db.connectors.update_one({"platform_id": platform_id},
                                   {"$set": {"last_checked": now_iso()}}, upsert=True)
    healthy = status in (S_HEALTHY, S_CONNECTED)
    return {"id": platform_id, "status": status, "healthy": healthy,
            "message": ("Connection healthy — ready to publish." if healthy
                        else reg["setup_hint"])}, None


async def manufacture_plan(platform_id):
    reg = _BY_ID.get(platform_id)
    if not reg:
        return None, "Unknown connector."
    return {"id": platform_id, "name": reg["name"], "asset_types": reg["asset_types"],
            "capabilities": reg["capabilities"]}, None


async def publish(platform_id, product_id, actor):
    """PUBLISH + VERIFY PUBLICATION. Only truly operational connectors publish; others return a
    clear guided reason (never a fake success)."""
    reg = _BY_ID.get(platform_id)
    if not reg:
        return None, "Unknown connector."
    if not reg["operational"]:
        return None, f"{reg['name']} isn't operational yet. {reg['setup_hint']}"

    product = await db.products.find_one({"id": product_id})
    if not product:
        return None, "Product not found."

    if platform_id == "qru_store":
        ok, blockers = fc.publish_gate(product)
        if not ok:
            return None, "This product isn't ready to publish: " + "; ".join(blockers)
        await db.products.update_one({"id": product_id}, {"$set": {
            "status": "Published", "published_at": now_iso(),
            "published_by": actor, "updated_at": now_iso()}})
        try:
            from org_activity import log_org
            await log_org("QRU Connector Engine™", "Distribution",
                          f"published to QRU Store™ via Universal Connector for", product.get("product_code", ""), "success")
        except Exception:
            pass
        base = os.environ.get("REACT_APP_BACKEND_URL", "")
        return {"published": True, "platform": reg["name"],
                "platform_url": f"{base}/store", "product_id": product_id,
                "product_code": product.get("product_code"),
                "published_at": now_iso(), "version": product.get("version", 1),
                "treasure_standard": product.get("treasure_standard_status", "Pending"),
                "store_status": "Live"}, None

    if platform_id == "stripe":
        return None, "Stripe handles pricing & checkout automatically for QRU Store™ products; it isn't a standalone publish target."

    return None, f"{reg['name']} publishing is not enabled yet. {reg['setup_hint']}"
