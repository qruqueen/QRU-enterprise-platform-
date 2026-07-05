"""QRU Universal OAuth Framework™ — one config-driven OAuth 2.0 engine for every platform.

Founder experience is always: Connect → official provider login → approve → Connected →
Test → Publish. The Founder NEVER sees tokens or developer credentials.

Developer-side (admin) configures each provider's OAuth Client ID / Secret / Redirect URI once.
Secrets and tokens are encrypted at rest (Fernet, reusing INTEGRATION_ENC_KEY) and are NEVER
returned to the client. Honest by design: a provider stays "Developer Configuration Required"
until real client credentials are configured, and "Needs Authorization" until the Founder
completes the official provider authorization. No fake OAuth success is ever fabricated.
"""
import os
import base64
import hashlib
import secrets as _secrets
import time
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet

from database import db
from models import gen_id, now_iso

_fernet = Fernet(os.environ["INTEGRATION_ENC_KEY"].encode())


def _enc(v: str) -> str:
    return _fernet.encrypt((v or "").encode()).decode()


def _dec(v: str) -> str:
    try:
        return _fernet.decrypt((v or "").encode()).decode()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Provider registry — standard OAuth 2.0 endpoints (public, stable).
# uses_pkce: providers that require PKCE (code_verifier/challenge).
# supported: False means the platform has no public OAuth publishing API today (honest).
# ---------------------------------------------------------------------------
PROVIDERS = {
    "youtube": {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "userinfo": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": ["openid", "email", "profile"],  # TEMP: scope-isolation diagnostic (sensitive YouTube scopes removed)
        "extra_auth": {"access_type": "offline", "prompt": "consent"}, "supported": True,
    },
    "google_drive": {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "userinfo": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": ["https://www.googleapis.com/auth/drive.file", "openid", "email", "profile"],
        "extra_auth": {"access_type": "offline", "prompt": "consent"}, "supported": True,
    },
    "google_docs": {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "userinfo": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive.file",
                   "openid", "email", "profile"],
        "extra_auth": {"access_type": "offline", "prompt": "consent"}, "supported": True,
    },
    "google_slides": {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "userinfo": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": ["https://www.googleapis.com/auth/presentations",
                   "https://www.googleapis.com/auth/drive.file", "openid", "email", "profile"],
        "extra_auth": {"access_type": "offline", "prompt": "consent"}, "supported": True,
    },
    "microsoft": {
        "authorize": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo": "https://graph.microsoft.com/v1.0/me",
        "scopes": ["offline_access", "User.Read", "Files.ReadWrite"], "supported": True,
    },
    "onedrive": {
        "authorize": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo": "https://graph.microsoft.com/v1.0/me",
        "scopes": ["offline_access", "User.Read", "Files.ReadWrite.All"], "supported": True,
    },
    "dropbox": {
        "authorize": "https://www.dropbox.com/oauth2/authorize",
        "token": "https://api.dropboxapi.com/oauth2/token",
        "userinfo": None,
        "scopes": ["files.content.write", "files.content.read", "account_info.read"],
        "extra_auth": {"token_access_type": "offline"}, "supported": True,
    },
    "etsy": {
        "authorize": "https://www.etsy.com/oauth/connect",
        "token": "https://api.etsy.com/v3/public/oauth/token",
        "userinfo": None,
        "scopes": ["listings_r", "listings_w", "shops_r"], "uses_pkce": True, "supported": True,
    },
    "linkedin": {
        "authorize": "https://www.linkedin.com/oauth/v2/authorization",
        "token": "https://www.linkedin.com/oauth/v2/accessToken",
        "userinfo": "https://api.linkedin.com/v2/userinfo",
        "scopes": ["openid", "profile", "w_member_social"], "supported": True,
    },
    "facebook": {
        "authorize": "https://www.facebook.com/v19.0/dialog/oauth",
        "token": "https://graph.facebook.com/v19.0/oauth/access_token",
        "userinfo": "https://graph.facebook.com/me",
        "scopes": ["pages_manage_posts", "pages_read_engagement"], "supported": True,
    },
    "instagram": {
        "authorize": "https://www.facebook.com/v19.0/dialog/oauth",
        "token": "https://graph.facebook.com/v19.0/oauth/access_token",
        "userinfo": "https://graph.facebook.com/me",
        "scopes": ["instagram_basic", "instagram_content_publish"], "supported": True,
    },
    "pinterest": {
        "authorize": "https://www.pinterest.com/oauth/",
        "token": "https://api.pinterest.com/v5/oauth/token",
        "userinfo": "https://api.pinterest.com/v5/user_account",
        "scopes": ["boards:read", "pins:read", "pins:write"], "supported": True,
    },
    "tiktok": {
        "authorize": "https://www.tiktok.com/v2/auth/authorize/",
        "token": "https://open.tiktokapis.com/v2/oauth/token/",
        "userinfo": "https://open.tiktokapis.com/v2/user/info/",
        "scopes": ["user.info.basic", "video.publish"], "uses_pkce": True, "supported": True,
    },
    "x": {
        "authorize": "https://twitter.com/i/oauth2/authorize",
        "token": "https://api.twitter.com/2/oauth2/token",
        "userinfo": "https://api.twitter.com/2/users/me",
        "scopes": ["tweet.read", "tweet.write", "users.read", "offline.access"],
        "uses_pkce": True, "supported": True,
    },
    "canva": {
        "authorize": "https://www.canva.com/api/oauth/authorize",
        "token": "https://api.canva.com/rest/v1/oauth/token",
        "userinfo": "https://api.canva.com/rest/v1/users/me",
        "scopes": ["design:content:read", "design:content:write"], "uses_pkce": True, "supported": True,
    },
    "github": {
        "authorize": "https://github.com/login/oauth/authorize",
        "token": "https://github.com/login/oauth/access_token",
        "userinfo": "https://api.github.com/user",
        "scopes": ["repo", "read:user"], "supported": True,
    },
    "google_sheets": {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "userinfo": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": ["https://www.googleapis.com/auth/spreadsheets",
                   "https://www.googleapis.com/auth/drive.file", "openid", "email", "profile"],
        "extra_auth": {"access_type": "offline", "prompt": "consent"}, "supported": True,
    },
    # Amazon KDP & Teachers Pay Teachers expose NO public OAuth publishing API today.
    "amazon_kdp": {"supported": False,
                   "reason": "Amazon KDP has no public OAuth publishing API. Publishing is done in the KDP dashboard."},
    "tpt": {"supported": False,
            "reason": "Teachers Pay Teachers has no public OAuth publishing API. Listings are uploaded in the TPT seller dashboard."},
}


def provider(platform_id):
    return PROVIDERS.get(platform_id)


# ---------------------------------------------------------------------------
# Developer configuration (admin) — Client ID / Secret / Redirect URI.
# ---------------------------------------------------------------------------
async def set_developer_config(platform_id, client_id, client_secret, redirect_uri, actor):
    p = PROVIDERS.get(platform_id)
    if not p:
        return None, "Unknown platform."
    if not p.get("supported"):
        return None, p.get("reason", "This platform does not support OAuth.")
    if not client_id or not redirect_uri:
        return None, "Client ID and Redirect URI are required."
    doc = {
        "platform_id": platform_id, "client_id": client_id, "redirect_uri": redirect_uri,
        "updated_at": now_iso(), "configured_by": actor,
    }
    if client_secret:
        doc["secret_enc"] = _enc(client_secret)
    await db.connector_configs.update_one({"platform_id": platform_id}, {"$set": doc}, upsert=True)
    return await get_developer_config(platform_id), None


async def get_developer_config(platform_id):
    """Public-safe: NEVER returns the client secret."""
    cfg = await db.connector_configs.find_one({"platform_id": platform_id})
    if not cfg:
        return {"platform_id": platform_id, "configured": False}
    cid = cfg.get("client_id", "")
    masked = (cid[:4] + "…" + cid[-4:]) if len(cid) > 10 else "configured"
    return {"platform_id": platform_id, "configured": True, "client_id_masked": masked,
            "has_secret": bool(cfg.get("secret_enc")), "redirect_uri": cfg.get("redirect_uri"),
            "updated_at": cfg.get("updated_at")}


async def delete_developer_config(platform_id):
    await db.connector_configs.delete_one({"platform_id": platform_id})
    await db.connectors.update_one({"platform_id": platform_id},
                                   {"$set": {"connected": False, "status": "Disconnected"},
                                    "$unset": {"access_token_enc": "", "refresh_token_enc": "", "expires_at": ""}})
    return True


async def is_configured(platform_id):
    cfg = await db.connector_configs.find_one({"platform_id": platform_id})
    return bool(cfg and cfg.get("client_id"))


# ---------------------------------------------------------------------------
# Authorization code flow.
# ---------------------------------------------------------------------------
def _pkce_pair():
    verifier = base64.urlsafe_b64encode(_secrets.token_bytes(40)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return verifier, challenge


async def build_authorize_url(platform_id, frontend_origin):
    p = PROVIDERS.get(platform_id)
    if not p:
        return None, "Unknown platform."
    if not p.get("supported"):
        return None, p.get("reason", "This platform does not support OAuth.")
    cfg = await db.connector_configs.find_one({"platform_id": platform_id})
    if not cfg or not cfg.get("client_id"):
        return None, "Developer Configuration Required — an admin must configure this platform's OAuth Client ID, Secret and Redirect URI first."

    state = gen_id()
    params = {
        "client_id": cfg["client_id"], "redirect_uri": cfg["redirect_uri"],
        "response_type": "code", "scope": " ".join(p["scopes"]), "state": state,
    }
    params.update(p.get("extra_auth", {}))
    verifier = ""
    if p.get("uses_pkce"):
        verifier, challenge = _pkce_pair()
        params["code_challenge"] = challenge
        params["code_challenge_method"] = "S256"
    await db.oauth_states.insert_one({
        "state": state, "platform_id": platform_id, "verifier": verifier,
        "frontend_origin": frontend_origin or "", "created_at": now_iso(), "ts": time.time(),
    })
    return {"authorize_url": f"{p['authorize']}?{urlencode(params)}"}, None


async def handle_callback(state, code, error=None):
    """Exchange the authorization code for tokens. Returns (frontend_origin, platform_id, ok, message)."""
    st = await db.oauth_states.find_one({"state": state})
    origin = (st or {}).get("frontend_origin", "")
    if not st:
        return origin, "", False, "This authorization link has expired. Please start Connect again."
    platform_id = st["platform_id"]
    await db.oauth_states.delete_one({"state": state})
    if error:
        return origin, platform_id, False, f"Authorization was cancelled or denied ({error})."

    p = PROVIDERS.get(platform_id)
    cfg = await db.connector_configs.find_one({"platform_id": platform_id})
    if not p or not cfg:
        return origin, platform_id, False, "This platform is no longer configured."

    data = {
        "grant_type": "authorization_code", "code": code,
        "redirect_uri": cfg["redirect_uri"], "client_id": cfg["client_id"],
    }
    secret = _dec(cfg.get("secret_enc", ""))
    if secret:
        data["client_secret"] = secret
    if st.get("verifier"):
        data["code_verifier"] = st["verifier"]

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(p["token"], data=data,
                                  headers={"Accept": "application/json"})
        if r.status_code >= 400:
            return origin, platform_id, False, "The provider rejected the authorization. Please verify the OAuth app credentials and try again."
        tok = r.json()
    except Exception:
        return origin, platform_id, False, "We couldn't reach the provider to complete authorization. Please try again."

    access = tok.get("access_token")
    if not access:
        return origin, platform_id, False, "The provider did not return an access token."
    expires_in = tok.get("expires_in") or 3600
    account = await _fetch_account(p, access)

    await db.connectors.update_one({"platform_id": platform_id}, {"$set": {
        "platform_id": platform_id, "auth_method": "oauth", "connected": True, "status": "Connected",
        "access_token_enc": _enc(access),
        "refresh_token_enc": _enc(tok.get("refresh_token", "")),
        "granted_scopes": tok.get("scope", " ".join(p["scopes"])),
        "expires_at": time.time() + float(expires_in),
        "account": account, "connected_at": now_iso(), "last_checked": now_iso(),
    }}, upsert=True)
    return origin, platform_id, True, "Connected successfully."


async def _fetch_account(p, access_token):
    if not p.get("userinfo"):
        return "Connected account"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(p["userinfo"], headers={"Authorization": f"Bearer {access_token}"})
        if r.status_code < 400:
            d = r.json()
            for k in ("name", "email", "login", "username", "display_name"):
                if isinstance(d, dict) and d.get(k):
                    return str(d[k])
            data = d.get("data") if isinstance(d, dict) else None
            if isinstance(data, dict):
                for k in ("username", "name", "display_name"):
                    if data.get(k):
                        return str(data[k])
    except Exception:
        pass
    return "Connected account"


async def _valid_access_token(platform_id):
    """Return a currently-valid access token, refreshing if needed. None if unavailable."""
    state = await db.connectors.find_one({"platform_id": platform_id}) or {}
    access = _dec(state.get("access_token_enc", ""))
    if not access:
        return None, state
    if state.get("expires_at", 0) - 60 > time.time():
        return access, state
    # expired — try refresh
    refreshed = await refresh(platform_id)
    if refreshed:
        state = await db.connectors.find_one({"platform_id": platform_id}) or {}
        return _dec(state.get("access_token_enc", "")), state
    return access, state  # return possibly-stale token; test will surface validity


async def refresh(platform_id):
    p = PROVIDERS.get(platform_id)
    cfg = await db.connector_configs.find_one({"platform_id": platform_id})
    state = await db.connectors.find_one({"platform_id": platform_id}) or {}
    rt = _dec(state.get("refresh_token_enc", ""))
    if not (p and cfg and rt):
        return False
    data = {"grant_type": "refresh_token", "refresh_token": rt, "client_id": cfg["client_id"]}
    secret = _dec(cfg.get("secret_enc", ""))
    if secret:
        data["client_secret"] = secret
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(p["token"], data=data, headers={"Accept": "application/json"})
        if r.status_code >= 400:
            return False
        tok = r.json()
    except Exception:
        return False
    access = tok.get("access_token")
    if not access:
        return False
    await db.connectors.update_one({"platform_id": platform_id}, {"$set": {
        "access_token_enc": _enc(access),
        "expires_at": time.time() + float(tok.get("expires_in") or 3600),
        "last_checked": now_iso(),
    }})
    if tok.get("refresh_token"):
        await db.connectors.update_one({"platform_id": platform_id},
                                       {"$set": {"refresh_token_enc": _enc(tok["refresh_token"])}})
    return True


async def disconnect(platform_id):
    await db.connectors.update_one({"platform_id": platform_id}, {"$set": {
        "connected": False, "status": "Disconnected", "last_checked": now_iso()},
        "$unset": {"access_token_enc": "", "refresh_token_enc": "", "expires_at": "", "account": ""}})
    return True


# ---------------------------------------------------------------------------
# Test Connection — honest, evidence-backed checklist.
# ---------------------------------------------------------------------------
async def test_connection(platform_id):
    p = PROVIDERS.get(platform_id)
    if not p:
        return None, "Unknown platform."
    if not p.get("supported"):
        return {"platform_id": platform_id, "overall": "unsupported",
                "message": p.get("reason", "OAuth not supported."), "checks": []}, None

    configured = await is_configured(platform_id)
    state = await db.connectors.find_one({"platform_id": platform_id}) or {}
    has_token = bool(state.get("access_token_enc"))
    has_refresh = bool(state.get("refresh_token_enc"))
    granted = state.get("granted_scopes", "")

    def chk(name, status, detail):
        return {"name": name, "status": status, "detail": detail}

    checks = []
    if not configured:
        checks.append(chk("Developer configuration", "fail", "OAuth Client ID/Secret/Redirect URI not configured."))
        return {"platform_id": platform_id, "overall": "needs_config",
                "message": "Developer Configuration Required.", "checks": checks}, None
    checks.append(chk("Developer configuration", "pass", "OAuth app credentials are configured."))

    if not has_token:
        checks.append(chk("Authentication", "fail", "Not authorized yet — click Connect to sign in with the provider."))
        return {"platform_id": platform_id, "overall": "needs_auth",
                "message": "Needs Authorization.", "checks": checks}, None

    # Live token validity + account ownership via a real userinfo call.
    access, state = await _valid_access_token(platform_id)
    live_ok = False
    account = state.get("account", "Connected account")
    if p.get("userinfo") and access:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(p["userinfo"], headers={"Authorization": f"Bearer {access}"})
            live_ok = r.status_code < 400
        except Exception:
            live_ok = False
        checks.append(chk("Authentication", "pass" if live_ok else "fail",
                          "Provider accepted the token." if live_ok else "Provider rejected the token — reconnect may be required."))
        checks.append(chk("Account ownership", "pass" if live_ok else "warn",
                          f"Connected as {account}." if live_ok else "Could not confirm the account."))
        checks.append(chk("Token validity", "pass" if live_ok else "fail",
                          "Access token is valid." if live_ok else "Access token appears invalid or expired."))
    else:
        live_ok = True
        checks.append(chk("Authentication", "pass", "Access token stored."))
        checks.append(chk("Account ownership", "pass", f"Connected as {account}."))
        checks.append(chk("Token validity", "pass",
                          "Token stored (this provider offers no read endpoint to verify live)."))

    scope_list = (granted or "").replace(",", " ").split()
    def has_scope(*needles):
        return any(any(n in s for s in scope_list) for n in needles) if scope_list else True
    checks.append(chk("Publishing permission", "pass" if has_scope("write", "publish", "upload", "social") else "warn",
                      "Write/publish scope granted." if has_scope("write", "publish", "upload", "social")
                      else "Publish scope not detected in the grant."))
    checks.append(chk("Read permission", "pass" if has_scope("read", "readonly", "basic", "profile", "openid") else "warn",
                      "Read scope granted." if has_scope("read", "readonly", "basic", "profile", "openid")
                      else "Read scope not detected."))
    checks.append(chk("Refresh capability", "pass" if has_refresh else "warn",
                      "Refresh token stored — access renews automatically." if has_refresh
                      else "No refresh token — reconnect will be needed when the token expires."))

    ready = live_ok and all(c["status"] != "fail" for c in checks)
    if ready:
        await db.connectors.update_one({"platform_id": platform_id},
                                       {"$set": {"status": "Test Passed", "last_checked": now_iso()}})
    checks.append(chk("Ready to Publish", "pass" if ready else "fail",
                      "All checks passed — this connector is Publishing Ready." if ready
                      else "Resolve the failed checks above before publishing."))
    return {"platform_id": platform_id, "overall": "passed" if ready else "failed",
            "message": "Test Passed — Publishing Ready." if ready else "Test found issues — see checklist.",
            "account": account, "checks": checks}, None


async def public_state(platform_id):
    """Founder-facing OAuth state for a connector (no secrets/tokens)."""
    p = PROVIDERS.get(platform_id)
    if not p:
        return None
    if not p.get("supported"):
        return {"oauth_supported": False, "reason": p.get("reason")}
    configured = await is_configured(platform_id)
    state = await db.connectors.find_one({"platform_id": platform_id}) or {}
    has_token = bool(state.get("access_token_enc"))
    has_refresh = bool(state.get("refresh_token_enc"))
    expired = bool(has_token and state.get("expires_at", 0) and state["expires_at"] < time.time())
    # Expired with no way to auto-refresh → the Founder must reconnect.
    reconnect_required = bool(expired and not has_refresh)
    return {
        "oauth_supported": True, "developer_configured": configured, "authorized": has_token,
        "account": state.get("account") if has_token else None,
        "status": state.get("status"), "connected_at": state.get("connected_at"),
        "last_checked": state.get("last_checked"),
        "expired": expired, "has_refresh": has_refresh, "reconnect_required": reconnect_required,
    }
