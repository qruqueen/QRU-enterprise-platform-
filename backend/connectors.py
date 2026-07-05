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
import oauth_framework as oauth

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
    {"id": "google_docs", "name": "Google Docs", "category": "Storage", "auth_method": "oauth",
     "operational": False, "asset_types": ["Document"], "capabilities": ["publish", "preview"],
     "setup_hint": "Requires Google OAuth authorization to Docs."},
    {"id": "google_slides", "name": "Google Slides", "category": "Storage", "auth_method": "oauth",
     "operational": False, "asset_types": ["Presentation"], "capabilities": ["publish", "preview"],
     "setup_hint": "Requires Google OAuth authorization to Slides."},
    {"id": "microsoft", "name": "Microsoft 365", "category": "Storage", "auth_method": "oauth",
     "operational": False, "asset_types": ["Any File"], "capabilities": ["publish"],
     "setup_hint": "Requires Microsoft OAuth authorization."},
    {"id": "tiktok", "name": "TikTok", "category": "Social", "auth_method": "oauth",
     "operational": False, "asset_types": ["Short Video", "Metadata"], "capabilities": ["publish", "metadata"],
     "setup_hint": "Requires TikTok OAuth authorization."},
    {"id": "x", "name": "X (Twitter)", "category": "Social", "auth_method": "oauth",
     "operational": False, "asset_types": ["Post", "Social Graphic"], "capabilities": ["publish", "metadata"],
     "setup_hint": "Requires X (Twitter) OAuth authorization."},
    {"id": "canva", "name": "Canva", "category": "Design", "auth_method": "oauth",
     "operational": False, "asset_types": ["Design", "Graphic"], "capabilities": ["publish", "preview"],
     "setup_hint": "Requires Canva OAuth authorization."},
    {"id": "github", "name": "GitHub", "category": "Development", "auth_method": "oauth",
     "operational": False, "asset_types": ["Repository File", "Release Asset"], "capabilities": ["publish"],
     "setup_hint": "Requires GitHub OAuth authorization."},
    {"id": "google_sheets", "name": "Google Sheets", "category": "Storage", "auth_method": "oauth",
     "operational": False, "asset_types": ["Spreadsheet"], "capabilities": ["publish", "preview"],
     "setup_hint": "Requires Google OAuth authorization to Sheets."},
    {"id": "woocommerce", "name": "WooCommerce", "category": "Commerce", "auth_method": "api_key",
     "operational": False, "asset_types": ["Store Listing", "Product Image", "Digital Download"],
     "capabilities": ["publish", "pricing", "metadata"],
     "setup_hint": "Requires your WooCommerce store URL + REST API key/secret."},
]
_BY_ID = {c["id"]: c for c in CONNECTOR_REGISTRY}

# Uniform Founder-facing statuses (Production vocabulary; never raw API errors).
S_HEALTHY = "Ready to Publish"          # native/operational + connected
S_CONNECTED = "Connected"
S_READY = "Ready to Publish"
S_NEEDS_AUTH = "Needs Authorization"
S_DEV_SETUP = "Developer Setup Required"
S_DEV_COMPLETE = "Developer Setup Complete"
S_TEST_PASSED = "Ready to Publish"
S_EXPIRED = "Connection Expired"
S_RECONNECT = "Reconnect Required"
S_PUBLISHING = "Publishing"
S_PUBLISHED = "Published"
S_DISCONNECTED = "Not Connected"
S_SETUP = "Developer Setup Required"
S_FAILED = "Failed"
S_ERROR = "Connection Error"

LIFECYCLE = ["Connect", "Test", "Manufacture", "Preview", "Publish"]


def _obfuscate(secret):
    """At-rest obfuscation for stored credentials (never returned to the client)."""
    return base64.b64encode((secret or "").encode()).decode()


async def _state(platform_id):
    return await db.connectors.find_one({"platform_id": platform_id}) or {}


async def _status_for(reg, state):
    if reg["auth_method"] == "native":
        return S_READY
    if reg["auth_method"] == "oauth":
        os_state = await oauth.public_state(reg["id"]) or {}
        if not os_state.get("oauth_supported", True):
            return S_DEV_SETUP
        if not os_state.get("developer_configured"):
            return S_DEV_SETUP
        if not os_state.get("authorized"):
            return S_NEEDS_AUTH
        if os_state.get("reconnect_required"):
            return S_RECONNECT
        if os_state.get("expired"):
            return S_EXPIRED
        st = os_state.get("status")
        if st == "Test Passed":
            return S_CONNECTED  # honest: connected+tested, but automated file-publish not yet wired
        return st or S_CONNECTED
    # api_key — the key is a developer credential; not set means admin setup pending.
    if reg["id"] == "stripe" and os.environ.get("STRIPE_API_KEY"):
        return S_CONNECTED  # Stripe is configured via environment (test mode active)
    if not state or not state.get("connected"):
        return S_DEV_SETUP
    return state.get("status") or S_CONNECTED


def _publish_reason(reg, connected, can_publish):
    if can_publish:
        return None
    if "publish" not in reg["capabilities"]:
        if reg["id"] == "stripe":
            return "Stripe powers checkout & payments for QRU Store™ products — it isn't a publishing destination, so there's nothing to publish here."
        return f"{reg['name']} isn't a publishing destination — it handles {', '.join(reg['capabilities'])}."
    if reg["auth_method"] != "native" and not reg["operational"]:
        return (f"Connect & Test work today, but automated publishing of the finished file to {reg['name']} "
                f"isn't wired yet. Publish to QRU Store™ now; {reg['name']} auto-publishing is a planned milestone.")
    if not connected:
        return f"Connect {reg['name']} first (complete Developer Setup, then Connect)."
    return f"{reg['name']} isn't ready to publish yet."


def _next_step(reg, status, connected):
    if reg["auth_method"] == "native":
        return "Select a review-passed product and click Publish."
    return {
        S_DEV_SETUP: f"An administrator must complete Developer Setup for {reg['name']} in Developer Mode (add the required credentials).",
        S_NEEDS_AUTH: f"Click Connect to sign in with {reg['name']} and approve access — no tokens to copy.",
        S_CONNECTED: "Click Test Connection to verify authentication, permissions and readiness.",
        S_READY: "Ready — select a review-passed product and click Publish.",
        S_RECONNECT: f"Click Reconnect to re-authorize {reg['name']} (the previous session expired).",
        S_EXPIRED: f"Click Reconnect to refresh access to {reg['name']}.",
        S_DISCONNECTED: f"Click Connect to authorize {reg['name']}.",
    }.get(status, reg["setup_hint"])


def _credential_needs(reg):
    if reg["auth_method"] == "oauth":
        return "OAuth Client ID, Client Secret and the exact Redirect URI (from the provider's developer console)."
    if reg["auth_method"] == "api_key":
        return reg["setup_hint"]
    return None


async def _public(reg, state):
    status = await _status_for(reg, state)
    connected = status in (S_HEALTHY, S_CONNECTED, S_READY)
    os_state = await oauth.public_state(reg["id"]) if reg["auth_method"] == "oauth" else {}
    os_state = os_state or {}
    oauth_supported = os_state.get("oauth_supported") if reg["auth_method"] == "oauth" else None
    developer_configured = (os_state.get("developer_configured") if reg["auth_method"] == "oauth"
                            else bool(state.get("connected"))
                                 or (reg["id"] == "stripe" and bool(os.environ.get("STRIPE_API_KEY"))))
    can_publish = bool(reg["operational"] and "publish" in reg["capabilities"] and connected)
    # A connector can hold credentials (Developer Setup) if it uses oauth (supported) or an api key.
    configurable = (reg["auth_method"] == "oauth" and oauth_supported is not False) or reg["auth_method"] == "api_key"
    return {
        "id": reg["id"], "name": reg["name"], "category": reg["category"],
        "auth_method": reg["auth_method"], "operational": reg["operational"],
        "asset_types": reg["asset_types"], "capabilities": reg["capabilities"],
        "setup_hint": reg["setup_hint"], "status": status, "connected": connected,
        "configurable": configurable,
        "oauth_supported": oauth_supported,
        "oauth_unsupported_reason": os_state.get("reason"),
        "developer_configured": developer_configured,
        "authorized": os_state.get("authorized"),
        "reconnect_required": os_state.get("reconnect_required"),
        "can_publish": can_publish,
        "publish_disabled_reason": _publish_reason(reg, connected, can_publish),
        "credential_needs": _credential_needs(reg),
        "next_step": _next_step(reg, status, connected),
        "account": os_state.get("account") or state.get("account"),
        "connected_at": os_state.get("connected_at") or state.get("connected_at"),
        "last_checked": os_state.get("last_checked") or state.get("last_checked"),
    }


async def list_connectors():
    out = []
    for reg in CONNECTOR_REGISTRY:
        out.append(await _public(reg, await _state(reg["id"])))
    # Native + operational first, then by category.
    out.sort(key=lambda c: (not c["operational"], c["category"], c["name"]))
    return out


async def get_connector(platform_id):
    reg = _BY_ID.get(platform_id)
    if not reg:
        return None
    return await _public(reg, await _state(platform_id))


async def connect(platform_id, credentials, actor):
    """CONNECT. Native = always healthy. api_key = store (obfuscated) + mark connected.
    oauth = handled by the Universal OAuth Framework™ (authorize-url → provider login → callback)."""
    reg = _BY_ID.get(platform_id)
    if not reg:
        return None, "Unknown connector."
    if reg["auth_method"] == "native":
        return await get_connector(platform_id), None
    if reg["auth_method"] == "oauth":
        os_state = await oauth.public_state(platform_id) or {}
        if not os_state.get("oauth_supported", True):
            return None, os_state.get("reason", "This platform does not support OAuth.")
        if not os_state.get("developer_configured"):
            return {"needs_developer_config": True, "auth_method": "oauth",
                    "message": f"{reg['name']} needs its OAuth app configured by an admin "
                               f"(Client ID, Secret, Redirect URI) before the Founder can connect.",
                    "connector": await get_connector(platform_id)}, None
        # Configured — the Founder should use the authorize-url flow.
        return {"use_authorize_url": True, "auth_method": "oauth",
                "connector": await get_connector(platform_id)}, None
    # api_key
    key = (credentials or {}).get("api_key")
    if not key:
        return None, f"{reg['name']} needs an API key to connect."
    await db.connectors.update_one({"platform_id": platform_id}, {"$set": {
        "platform_id": platform_id, "connected": True, "status": S_CONNECTED,
        "auth_method": "api_key", "secret": _obfuscate(key),
        "account": (credentials or {}).get("account") or "Connected account",
        "connected_at": now_iso(), "last_checked": now_iso(), "connected_by": actor,
        "updated_at": now_iso()}}, upsert=True)
    return {"connector": await get_connector(platform_id)}, None


async def verify(platform_id):
    """TEST / MONITOR. OAuth connectors run the full Universal OAuth Framework™ checklist;
    others return a uniform health status, never a raw API error."""
    reg = _BY_ID.get(platform_id)
    if not reg:
        return None, "Unknown connector."
    if reg["auth_method"] == "oauth":
        res, err = await oauth.test_connection(platform_id)
        if err:
            return None, err
        healthy = res.get("overall") == "passed"
        msg = res.get("message", "")
        return {"id": platform_id, "status": (await _status_for(reg, await _state(platform_id))),
                "healthy": healthy, "message": msg, "checks": res.get("checks", []),
                "overall": res.get("overall"), "account": res.get("account")}, None
    state = await _state(platform_id)
    status = await _status_for(reg, state)
    await db.connectors.update_one({"platform_id": platform_id},
                                   {"$set": {"last_checked": now_iso()}}, upsert=True)
    healthy = status in (S_HEALTHY, S_CONNECTED, S_TEST_PASSED)
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
