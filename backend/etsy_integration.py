"""QRU × Etsy Open API v3 — governed integration engine.

Security (Treasure Standard™ + task mandate):
- Etsy keystring / shared secret / OAuth tokens live ONLY server-side; encrypted at rest (Fernet,
  reusing INTEGRATION_ENC_KEY). They are NEVER returned to the browser, printed, or logged.
- OAuth 2.0 Authorization Code + PKCE (S256). Cryptographically-secure state + verifier per attempt,
  stored server-side (etsy_oauth_sessions) and verified before the code exchange.
- Access tokens auto-refresh server-side; Etsy rotates refresh tokens, so the newest is persisted.
- Every connect / disconnect / publish / update / sync / failure / retry / token-refresh writes a
  redacted audit record (etsy_audit).

Publication is DRAFT-FIRST and idempotent: a QRU product maps to at most one Etsy listing; retries
never create duplicates. Nothing on Etsy is ever auto-deleted.
"""
import os
import time
import base64
import hashlib
import logging
import secrets as _secrets
from urllib.parse import urlencode, quote

import httpx
from cryptography.fernet import Fernet

from database import db
from models import gen_id, now_iso

logger = logging.getLogger("etsy")

# ------------------------------------------------------------------ config ----
KEYSTRING = os.environ.get("ETSY_API_KEYSTRING", "")
SHARED_SECRET = os.environ.get("ETSY_SHARED_SECRET", "")
SHOP_NAME_HINT = os.environ.get("ETSY_SHOP_NAME", "")
SCOPES = (os.environ.get("ETSY_SCOPES") or "shops_r listings_r listings_w transactions_r").replace(",", " ").strip()
REDIRECT_OVERRIDE = os.environ.get("ETSY_REDIRECT_URI", "")
DEFAULT_TAXONOMY_ID = int(os.environ.get("ETSY_DEFAULT_TAXONOMY_ID", "1") or 1)

_fernet = Fernet(os.environ["INTEGRATION_ENC_KEY"].encode())

CONNECT_URL = "https://www.etsy.com/oauth/connect"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
API = "https://openapi.etsy.com/v3/application"

INTEG = "etsy_integrations"
MAP = "etsy_listing_mappings"
SESS = "etsy_oauth_sessions"
AUDIT = "etsy_audit"
INTEG_ID = "etsy"  # single-shop integration singleton


# ---------------------------------------------------------------- crypto ------
def _enc(v: str) -> str:
    return _fernet.encrypt((v or "").encode()).decode()


def _dec(v: str) -> str:
    if not v:
        return ""
    try:
        return _fernet.decrypt(v.encode()).decode()
    except Exception:
        return ""


def _redact(text: str) -> str:
    """Strip any known secret material from a string before it is stored/returned."""
    if not text:
        return text
    out = str(text)
    for val, tag in [(KEYSTRING, "«keystring»"), (SHARED_SECRET, "«shared_secret»")]:
        if val:
            out = out.replace(val, tag)
    # redact bearer tokens / long opaque strings
    import re
    out = re.sub(r"(Bearer\s+)[A-Za-z0-9._\-]+", r"\1«redacted»", out)
    out = re.sub(r"[A-Za-z0-9]{6,}\.[A-Za-z0-9._\-]{20,}", "«redacted-token»", out)
    return out


# ----------------------------------------------------------------- audit ------
async def _audit(action, status, detail="", meta=None):
    rec = {
        "id": gen_id(), "action": action, "status": status,
        "detail": _redact(detail)[:500],
        "meta": {k: _redact(str(v))[:200] for k, v in (meta or {}).items()},
        "at": now_iso(), "ts": time.time(),
    }
    await db[AUDIT].insert_one(dict(rec))
    return rec


# ------------------------------------------------------------------ headers ---
def _headers(access_token: str):
    # Etsy Open API v3: x-api-key = app keystring; Bearer = user access token.
    return {"x-api-key": KEYSTRING, "Authorization": f"Bearer {access_token}"}


def is_configured():
    return bool(KEYSTRING and SHARED_SECRET)


def _redirect_uri(origin: str) -> str:
    if REDIRECT_OVERRIDE:
        return REDIRECT_OVERRIDE
    base = (origin or "").rstrip("/")
    return f"{base}/api/integrations/etsy/callback"


# --------------------------------------------------------------- PKCE + state -
def _pkce_pair():
    verifier = base64.urlsafe_b64encode(_secrets.token_bytes(40)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return verifier, challenge


async def build_authorize_url(origin: str, actor: str):
    if not is_configured():
        return None, "Etsy is not configured — the app keystring and shared secret must be set server-side first."
    state = base64.urlsafe_b64encode(_secrets.token_bytes(32)).decode().rstrip("=")
    verifier, challenge = _pkce_pair()
    redirect_uri = _redirect_uri(origin)
    await db[SESS].insert_one({
        "state": state, "verifier": verifier, "redirect_uri": redirect_uri,
        "origin": (origin or "").rstrip("/"), "actor": actor,
        "created_at": now_iso(), "ts": time.time(),
    })
    params = {
        "response_type": "code", "client_id": KEYSTRING, "redirect_uri": redirect_uri,
        "scope": SCOPES, "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
    }
    await _audit("connect", "started", "Authorization URL generated (PKCE).", {"actor": actor})
    return {"authorize_url": f"{CONNECT_URL}?{urlencode(params)}"}, None


async def handle_callback(state: str, code: str, error: str = None):
    """Verify state, exchange code (with PKCE verifier) for tokens, resolve shop, store encrypted."""
    sess = await db[SESS].find_one({"state": state}) if state else None
    origin = (sess or {}).get("origin", "")
    if not sess:
        await _audit("connect", "failure", "State verification failed (unknown/expired state).")
        return origin, False, "This Etsy authorization link is invalid or has expired. Please start Connect again."
    await db[SESS].delete_one({"state": state})
    if error:
        await _audit("connect", "failure", f"Authorization denied ({error}).")
        return origin, False, f"Etsy authorization was cancelled or denied ({error})."

    data = {
        "grant_type": "authorization_code", "client_id": KEYSTRING,
        "redirect_uri": sess["redirect_uri"], "code": code, "code_verifier": sess["verifier"],
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(TOKEN_URL, data=data, headers={
                "Content-Type": "application/x-www-form-urlencoded", "x-api-key": KEYSTRING})
        if r.status_code >= 400:
            await _audit("connect", "failure", f"Token exchange rejected (HTTP {r.status_code}).")
            return origin, False, "Etsy rejected the authorization. Please verify the app credentials and redirect URI, then try again."
        tok = r.json()
    except Exception as e:
        await _audit("connect", "failure", f"Token exchange error: {e}")
        return origin, False, "We couldn't reach Etsy to complete authorization. Please try again."

    access = tok.get("access_token")
    refresh = tok.get("refresh_token")
    if not access:
        await _audit("connect", "failure", "No access token returned.")
        return origin, False, "Etsy did not return an access token."

    ident = await _resolve_identity(access)
    user_id = ident.get("user_id")
    shop_id = ident.get("shop_id")
    shop_name = ident.get("shop_name")
    if shop_id and not shop_name:
        try:
            shop_name = (await _get_shop(access, shop_id)).get("shop_name")
        except Exception:
            pass

    await db[INTEG].update_one({"id": INTEG_ID}, {"$set": {
        "id": INTEG_ID,
        "shop_id": shop_id,
        "shop_name": shop_name,
        "etsy_user_id": user_id,
        "connection_status": "connected",
        "encrypted_access_token": _enc(access),
        "encrypted_refresh_token": _enc(refresh or ""),
        "token_expires_at": time.time() + float(tok.get("expires_in") or 3600),
        "granted_scopes": tok.get("scope", SCOPES),
        "connected_at": now_iso(),
        "last_verified_at": now_iso(),
        "last_error": None,
        "updated_at": now_iso(),
    }, "$setOnInsert": {"created_at": now_iso()}}, upsert=True)
    await _audit("connect", "success", "Etsy shop connected.", {"shop_id": shop_id, "user_id": user_id})
    return origin, True, "Etsy shop connected successfully."


# ------------------------------------------------------------ token lifecycle -
async def _integration():
    return await db[INTEG].find_one({"id": INTEG_ID})


async def _refresh(doc):
    payload = {"grant_type": "refresh_token", "client_id": KEYSTRING,
               "refresh_token": _dec(doc.get("encrypted_refresh_token", ""))}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(TOKEN_URL, data=payload, headers={
            "Content-Type": "application/x-www-form-urlencoded", "x-api-key": KEYSTRING})
    if r.status_code >= 400:
        await db[INTEG].update_one({"id": INTEG_ID}, {"$set": {
            "connection_status": "expired", "last_error": "Token refresh failed — reconnect required.",
            "updated_at": now_iso()}})
        await _audit("token_refresh", "failure", f"Refresh rejected (HTTP {r.status_code}).")
        raise RuntimeError("Etsy token refresh failed — please reconnect.")
    tok = r.json()
    await db[INTEG].update_one({"id": INTEG_ID}, {"$set": {
        "encrypted_access_token": _enc(tok["access_token"]),
        "encrypted_refresh_token": _enc(tok.get("refresh_token", _dec(doc.get("encrypted_refresh_token", "")))),
        "token_expires_at": time.time() + float(tok.get("expires_in") or 3600),
        "connection_status": "connected", "last_error": None, "updated_at": now_iso(),
    }})
    await _audit("token_refresh", "success", "Access token refreshed (refresh token rotated).")
    return tok["access_token"]


async def _access_token():
    doc = await _integration()
    if not doc or not doc.get("encrypted_access_token"):
        raise RuntimeError("Etsy is not connected.")
    if float(doc.get("token_expires_at", 0)) - 60 <= time.time():
        return await _refresh(doc)
    return _dec(doc["encrypted_access_token"])


# ------------------------------------------------------------- Etsy API calls -
async def _api(method, path, access=None, **kw):
    access = access or await _access_token()
    url = path if path.startswith("http") else f"{API}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.request(method, url, headers=_headers(access), **kw)
    return r


async def _get_me(access):
    r = await _api("GET", "/users/me", access=access)
    r.raise_for_status()
    return r.json()


def _uid_from_token(access):
    """Etsy v3 access tokens embed the numeric user id as a prefix: '{user_id}.{token}'."""
    if access and "." in access:
        pre = access.split(".", 1)[0]
        if pre.isdigit():
            return int(pre)
    return None


async def _resolve_identity(access):
    """Return {user_id, shop_id, shop_name, _diag}. /users/me can 403 on many apps, so derive the
    user id from the token prefix and read the user's shop directly. _diag captures the raw outcome
    of the shop lookup so failures are diagnosable instead of silently swallowed."""
    user_id = _uid_from_token(access)
    shop_id, shop_name, diag = None, None, {}
    if user_id:
        try:
            r = await _api("GET", f"/users/{user_id}/shops", access=access)
            diag = {"endpoint": f"/users/{user_id}/shops", "status": r.status_code}
            if r.status_code < 400:
                j = r.json()
                if isinstance(j, dict) and j.get("shop_id"):
                    shop = j
                elif isinstance(j, dict) and isinstance(j.get("results"), list) and j["results"]:
                    shop = j["results"][0]
                else:
                    shop = {}
                    diag["note"] = "empty"
                shop_id = shop.get("shop_id")
                shop_name = shop.get("shop_name")
            else:
                diag["body"] = _redact(r.text)[:180]
        except Exception as e:
            diag = {"error": _redact(str(e))[:180]}
    if shop_id is None:
        try:
            me = await _get_me(access)
            user_id = user_id or me.get("user_id")
            shop_id = shop_id or me.get("shop_id")
        except Exception as e:
            diag.setdefault("me_error", _redact(str(e))[:120])
    if shop_id is None and SHOP_NAME_HINT:
        # Fallback: public shop search by name (getShopByOwnerUserId can be unreliable).
        try:
            r = await _api("GET", f"/shops?shop_name={quote(SHOP_NAME_HINT)}", access=access)
            diag["findShops_status"] = r.status_code
            if r.status_code < 400:
                results = (r.json() or {}).get("results") or []
                if results:
                    match = next((s for s in results
                                  if (s.get("shop_name", "").lower() == SHOP_NAME_HINT.lower())), results[0])
                    shop_id = match.get("shop_id")
                    shop_name = match.get("shop_name") or shop_name
            else:
                diag["findShops_body"] = _redact(r.text)[:180]
        except Exception as e:
            diag.setdefault("findShops_error", _redact(str(e))[:120])
    if shop_id is None:
        env_shop = os.environ.get("ETSY_SHOP_ID")
        if env_shop and env_shop.isdigit():
            shop_id = int(env_shop)
    logger.info("ETSY identity resolve: user_id=%s shop_id=%s diag=%s", user_id, shop_id, diag)
    return {"user_id": user_id, "shop_id": shop_id, "shop_name": shop_name, "_diag": diag}


async def diagnostics():
    """Raw, redacted probe of every relevant Etsy endpoint — for Founder-visible debugging.
    Logs full status + body server-side and returns them (secrets/tokens redacted)."""
    doc = await _integration()
    out = {"has_integration": bool(doc),
           "stored_shop_id": (doc or {}).get("shop_id"),
           "stored_shop_name": (doc or {}).get("shop_name"),
           "stored_user_id": (doc or {}).get("etsy_user_id"),
           "shop_name_hint": SHOP_NAME_HINT or None, "calls": []}
    if not doc or not doc.get("encrypted_access_token"):
        out["error"] = "Not connected."
        return out
    try:
        access = await _access_token()
    except Exception as e:
        out["error"] = _redact(str(e))[:200]
        return out
    uid = _uid_from_token(access)
    out["user_id_from_token"] = uid
    probes = [("getMe", "/users/me")]
    if uid:
        probes.append(("getShopByOwnerUserId", f"/users/{uid}/shops"))
        probes.append(("getUser", f"/users/{uid}"))
    if SHOP_NAME_HINT:
        probes.append(("findShops(shop_name)", f"/shops?shop_name={quote(SHOP_NAME_HINT)}"))
    for name, path in probes:
        entry = {"name": name, "endpoint": path}
        try:
            r = await _api("GET", path, access=access)
            entry["status"] = r.status_code
            entry["body"] = _redact(r.text)[:800]
            logger.info("ETSY DIAG %s %s -> HTTP %s | %s", name, path, r.status_code, _redact(r.text)[:400])
        except Exception as e:
            entry["error"] = _redact(str(e))[:300]
            logger.info("ETSY DIAG %s %s -> ERROR %s", name, path, _redact(str(e))[:200])
        out["calls"].append(entry)
    return out


async def _get_shop(access, shop_id):
    r = await _api("GET", f"/shops/{shop_id}", access=access)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------- status ------
async def status():
    doc = await _integration()
    if not doc or not doc.get("encrypted_access_token"):
        return {"status": "disconnected", "configured": is_configured(),
                "connected_shop": None, "granted_scopes": None,
                "last_synced_at": None, "last_error": None,
                "mapped_products": 0, "draft_listings": 0, "active_listings": 0}
    expired = float(doc.get("token_expires_at", 0)) < time.time() and not doc.get("encrypted_refresh_token")
    st = "expired" if expired else (doc.get("connection_status") or "connected")
    mapped = await db[MAP].count_documents({})
    drafts = await db[MAP].count_documents({"etsy_listing_state": "draft"})
    active = await db[MAP].count_documents({"etsy_listing_state": "active"})
    last_map = await db[MAP].find_one({}, sort=[("last_synced_at", -1)])
    return {
        "status": st, "configured": True,
        "connected_shop": doc.get("shop_name") or (str(doc.get("shop_id")) if doc.get("shop_id") else None),
        "shop_id": doc.get("shop_id"),
        "granted_scopes": doc.get("granted_scopes"),
        "connected_at": doc.get("connected_at"),
        "last_verified_at": doc.get("last_verified_at"),
        "last_synced_at": (last_map or {}).get("last_synced_at"),
        "last_error": _redact(doc.get("last_error") or "") or None,
        "mapped_products": mapped, "draft_listings": drafts, "active_listings": active,
    }


async def disconnect(actor):
    doc = await _integration()
    if not doc:
        return {"ok": True, "status": "disconnected"}
    await db[INTEG].update_one({"id": INTEG_ID}, {"$set": {
        "connection_status": "disconnected",
        "encrypted_access_token": "", "encrypted_refresh_token": "",
        "token_expires_at": 0, "disconnected_at": now_iso(), "updated_at": now_iso()}})
    await _audit("disconnect", "success", "Etsy integration disconnected by Founder.", {"actor": actor})
    return {"ok": True, "status": "disconnected"}


async def test_connection():
    """Read-only: ping (getMe) + a read-only shop fetch. Returns a sanitized report."""
    doc = await _integration()
    if not doc or not doc.get("encrypted_access_token"):
        return {"ok": False, "checks": [{"name": "Connected", "ok": False, "detail": "Etsy is not connected."}]}
    checks = []
    ok_all = True
    try:
        access = await _access_token()
        checks.append({"name": "Access token", "ok": True, "detail": "Valid (auto-refreshed if needed)."})
    except Exception as e:
        return {"ok": False, "checks": [{"name": "Access token", "ok": False, "detail": _redact(str(e))}]}
    ident = await _resolve_identity(access)
    if ident.get("user_id"):
        checks.append({"name": "Ping (identity)", "ok": True,
                       "detail": f"Authenticated user #{ident['user_id']}."})
    else:
        ok_all = False
        checks.append({"name": "Ping (identity)", "ok": False,
                       "detail": "Could not resolve the authenticated Etsy user from the token."})
    shop_id = ident.get("shop_id") or doc.get("shop_id")
    shop_name = ident.get("shop_name") or doc.get("shop_name")
    if shop_id:
        try:
            shop = await _get_shop(access, shop_id)
            shop_name = shop.get("shop_name") or shop_name
            checks.append({"name": "Read shop", "ok": True, "detail": f"Shop: {shop_name} (#{shop_id})"})
        except Exception as e:
            ok_all = False
            checks.append({"name": "Read shop", "ok": False, "detail": _redact(str(e))})
    else:
        ok_all = False
        diag = ident.get("_diag") or {}
        parts = []
        if diag.get("status"):
            parts.append(f"owner-lookup HTTP {diag['status']}" + (f" {diag.get('body','')}" if diag.get("body") else ""))
        if diag.get("findShops_status"):
            parts.append(f"findShops HTTP {diag['findShops_status']}" + (f" {diag.get('findShops_body','')}" if diag.get("findShops_body") else ""))
        for k in ("error", "findShops_error", "me_error"):
            if diag.get(k):
                parts.append(f"{k}: {diag[k]}")
        if diag.get("note") == "empty" and not diag.get("findShops_status"):
            parts.append("owner-lookup returned no shop")
        detail = "Shop not resolved. " + (" | ".join(parts) if parts else "No shop returned.") + " — open /api/integrations/etsy/diagnostics for raw responses."
        checks.append({"name": "Read shop", "ok": False, "detail": detail})
    # Heal the stored identity so publish/listings work without a reconnect.
    await db[INTEG].update_one({"id": INTEG_ID}, {"$set": {
        "shop_id": shop_id, "shop_name": shop_name, "etsy_user_id": ident.get("user_id"),
        "last_verified_at": now_iso(),
        "last_error": None if ok_all else "Test connection reported issues."}})
    await _audit("test", "success" if ok_all else "failure", "Read-only connection test.")
    return {"ok": ok_all, "checks": checks}


# --------------------------------------------------------- QRU product bridge -
async def _load_qru_product(product_id):
    """Normalize a QRU product (book_record or product) to an Etsy-mappable shape."""
    b = await db.book_records.find_one({"id": product_id}) or await db.book_records.find_one({"book_code": product_id})
    if b:
        import imprint_rules as ir
        art = (b.get("artifacts") or {}).get("design") or {}
        sel = art.get("selected_cover") or {}
        epub = (art.get("ebook") or {}).get("epub")
        pricing = b.get("pricing") or {}
        content = (b.get("editorial_edition") or b.get("working_copy") or {}).get("content", "")
        desc = (b.get("description") or b.get("subtitle") or " ".join(content.split()[:120])).strip()
        ci = None
        try:
            import book_manufacturing as bm
            ci = bm.content_integrity_check(b.get("title"), b.get("subtitle"), content)
        except Exception:
            ci = {"ok": True}
        comp = ir.imprint_compliance(b)
        version = (b.get("editorial_edition") or {}).get("checksum") or b.get("updated_at")
        return {
            "found": True, "source": "book", "id": b["id"], "code": b.get("book_code"),
            "title": b.get("title"), "description": desc,
            "price": pricing.get("ebook_price") or pricing.get("list_price"),
            "currency": pricing.get("currency", "USD"),
            "product_type": "download", "imprint": b.get("canonical_imprint") or b.get("imprint"),
            "tags": _tags_from(b.get("genre"), b.get("title")),
            "images": [sel.get("url")] if sel.get("url") else [],
            "files": [epub] if epub else [],
            "authorized": bool((b.get("founder_authorization") or {}).get("authorized")),
            "qa_complete": bool(b.get("editorial_locked")),
            "content_integrity_ok": bool(ci.get("ok", True)),
            "imprint_mismatch": bool(comp.get("mismatch")),
            "version": version,
        }
    p = await db.products.find_one({"id": product_id}) or await db.products.find_one({"product_code": product_id})
    if p:
        pricing = p.get("pricing") or {}
        cover = p.get("cover_url") or (p.get("assets") or {}).get("cover_url")
        deliv = p.get("deliverables") or []
        return {
            "found": True, "source": "product", "id": p["id"], "code": p.get("product_code"),
            "title": p.get("title") or p.get("name"), "description": (p.get("description") or "").strip(),
            "price": pricing.get("price") or p.get("price"), "currency": pricing.get("currency", "USD"),
            "product_type": "download", "imprint": p.get("imprint") or "QRU Press™",
            "tags": _tags_from(p.get("category") or p.get("product_type"), p.get("title")),
            "images": [cover] if cover else [],
            "files": [d.get("url") for d in deliv if d.get("url")][:1],
            "authorized": p.get("status") in ("Published", "Authorized"),
            "qa_complete": p.get("status") in ("Published", "Authorized", "Ready"),
            "content_integrity_ok": True, "imprint_mismatch": False,
            "version": p.get("updated_at") or p.get("version"),
        }
    return {"found": False}


def _tags_from(genre, title):
    base = []
    if genre:
        base.append(str(genre))
    for w in (title or "").replace(":", " ").split():
        if len(w) > 3 and w.lower() not in base and len(base) < 13:
            base.append(w)
    return [t[:20] for t in base[:13]]


def eligibility(prod):
    """Return the governed publish-eligibility checklist for a normalized QRU product."""
    if not prod.get("found"):
        return {"eligible": False, "checks": [{"name": "Product exists", "ok": False, "detail": "Not found."}]}
    checks = [
        {"name": "QA complete", "ok": prod["qa_complete"], "detail": "Editorial locked / QA passed." if prod["qa_complete"] else "QA not complete."},
        {"name": "Authorized for Publication", "ok": prod["authorized"], "detail": "Founder authorized." if prod["authorized"] else "Not authorized for release."},
        {"name": "Deliverable file present", "ok": bool(prod["files"]), "detail": "File present & referenced." if prod["files"] else "No deliverable file."},
        {"name": "Listing image present", "ok": bool(prod["images"]), "detail": "Cover/image present." if prod["images"] else "No cover/listing image."},
        {"name": "Metadata populated", "ok": bool(prod["title"] and prod["description"] and prod["price"] and prod["imprint"]),
         "detail": "Title, description, price, imprint present." if (prod["title"] and prod["description"] and prod["price"] and prod["imprint"]) else "Missing title/description/price/imprint."},
        {"name": "No blocking issue", "ok": prod["content_integrity_ok"] and not prod["imprint_mismatch"],
         "detail": "No content-integrity or imprint-mismatch block." if (prod["content_integrity_ok"] and not prod["imprint_mismatch"]) else "Blocked: content-integrity or imprint mismatch."},
    ]
    return {"eligible": all(c["ok"] for c in checks), "checks": checks}


def _listing_payload(prod, taxonomy_id=None):
    return {
        "quantity": 999, "title": (prod["title"] or "")[:140],
        "description": prod["description"] or prod["title"],
        "price": float(prod["price"]) if prod["price"] else 0.0,
        "who_made": "i_did", "when_made": "2020_2025",
        "taxonomy_id": int(taxonomy_id or DEFAULT_TAXONOMY_ID),
        "type": "download", "is_supply": False,
        "tags": prod["tags"], "state": "draft",
        "should_auto_renew": False,
    }


def _sync_hash(prod):
    import json
    return hashlib.sha256(json.dumps({
        "title": prod["title"], "description": prod["description"], "price": prod["price"],
        "tags": prod["tags"], "images": prod["images"], "files": prod["files"],
    }, sort_keys=True, default=str).encode()).hexdigest()


async def preview(product_id, taxonomy_id=None):
    """Build the Etsy publication preview. NEVER mutates Etsy."""
    prod = await _load_qru_product(product_id)
    if not prod.get("found"):
        return {"error": "QRU product not found."}
    elig = eligibility(prod)
    payload = _listing_payload(prod, taxonomy_id)
    mapping = await db[MAP].find_one({"qru_product_id": prod["id"]}, {"_id": 0})
    changes = None
    if mapping:
        prev = mapping.get("last_sync_hash")
        changes = {"already_mapped": True, "etsy_listing_id": mapping.get("etsy_listing_id"),
                   "changed_since_publish": prev != _sync_hash(prod)}
    return {
        "product": {"id": prod["id"], "code": prod["code"], "source": prod["source"],
                    "imprint": prod["imprint"], "version": str(prod["version"])},
        "eligibility": elig,
        "listing_preview": {
            "title": payload["title"], "description": payload["description"],
            "price": payload["price"], "currency": prod["currency"], "quantity": payload["quantity"],
            "taxonomy_id": payload["taxonomy_id"], "tags": payload["tags"],
            "type": payload["type"], "state": "draft (on publish)",
            "renewal": "manual (auto-renew off)",
            "images": prod["images"], "files": prod["files"],
            "shipping": "N/A — digital download",
        },
        "mapping": mapping, "change_preview": changes,
        "note": "Preview only — nothing is created or changed on Etsy.",
    }


async def publish_draft(product_id, actor, approved=False, taxonomy_id=None):
    prod = await _load_qru_product(product_id)
    if not prod.get("found"):
        return {"error": "QRU product not found."}
    elig = eligibility(prod)
    if not elig["eligible"]:
        await _audit("publish", "failure", "Blocked by governance.", {"product": prod.get("code")})
        return {"error": "Product is not eligible for Etsy publication.", "eligibility": elig}
    if not approved:
        return {"error": "Founder approval required to create the Etsy draft.", "eligibility": elig,
                "requires_approval": True}
    # Idempotency: never create a second listing for the same QRU product.
    existing = await db[MAP].find_one({"qru_product_id": prod["id"]})
    if existing and existing.get("etsy_listing_id"):
        await _audit("publish", "skipped", "Idempotent — listing already exists.", {"product": prod.get("code")})
        return {"ok": True, "idempotent": True, "mapping": {k: v for k, v in existing.items() if k != "_id"},
                "message": "An Etsy draft already exists for this product (no duplicate created)."}
    doc = await _integration()
    if not doc or not doc.get("encrypted_access_token"):
        return {"error": "Etsy is not connected."}
    shop_id = doc.get("shop_id")
    payload = _listing_payload(prod, taxonomy_id)
    # Reserve the mapping first (idempotency guard against concurrent retries).
    idem = existing.get("id") if existing else gen_id()
    await db[MAP].update_one({"qru_product_id": prod["id"]}, {"$set": {
        "id": idem, "qru_product_id": prod["id"], "qru_product_code": prod["code"],
        "etsy_shop_id": shop_id, "qru_product_version": str(prod["version"]),
        "sync_status": "publishing", "updated_at": now_iso()},
        "$setOnInsert": {"created_at": now_iso()}}, upsert=True)
    try:
        r = await _api("POST", f"/shops/{shop_id}/listings", data=payload)
        if r.status_code >= 400:
            await db[MAP].update_one({"qru_product_id": prod["id"]}, {"$set": {
                "sync_status": "error", "last_error": f"HTTP {r.status_code}", "updated_at": now_iso()}})
            await _audit("publish", "failure", f"Etsy create draft failed (HTTP {r.status_code}): {r.text}",
                         {"product": prod.get("code")})
            return {"error": "Etsy rejected the draft listing. The QRU product was not changed.",
                    "detail": _redact(r.text)[:200]}
        listing = r.json().get("results", [r.json()])[0] if isinstance(r.json(), dict) and "results" in r.json() else r.json()
        listing_id = listing.get("listing_id")
        url = listing.get("url") or f"https://www.etsy.com/listing/{listing_id}"
    except Exception as e:
        await db[MAP].update_one({"qru_product_id": prod["id"]}, {"$set": {
            "sync_status": "error", "last_error": _redact(str(e))[:200], "updated_at": now_iso()}})
        await _audit("publish", "failure", f"Create draft error: {e}", {"product": prod.get("code")})
        return {"error": "Failed to create the Etsy draft. The QRU product was not changed."}
    mapping = {
        "id": idem, "qru_product_id": prod["id"], "qru_product_code": prod["code"],
        "etsy_listing_id": listing_id, "etsy_shop_id": shop_id, "etsy_listing_state": "draft",
        "qru_product_version": str(prod["version"]), "etsy_url": url,
        "last_published_at": now_iso(), "last_synced_at": now_iso(),
        "last_sync_hash": _sync_hash(prod), "sync_status": "in_sync", "last_error": None,
        "updated_at": now_iso(),
    }
    await db[MAP].update_one({"qru_product_id": prod["id"]}, {"$set": mapping})
    await _audit("publish", "success", "Etsy DRAFT created.", {"product": prod.get("code"), "listing_id": listing_id})
    return {"ok": True, "mapping": mapping, "message": "Etsy draft listing created (not active)."}


async def update_listing(product_id, actor):
    prod = await _load_qru_product(product_id)
    mapping = await db[MAP].find_one({"qru_product_id": product_id}) or await db[MAP].find_one({"qru_product_id": (prod or {}).get("id")})
    if not mapping or not mapping.get("etsy_listing_id"):
        return {"error": "No Etsy listing is mapped to this product yet."}
    doc = await _integration()
    shop_id = doc.get("shop_id")
    payload = _listing_payload(prod)
    payload.pop("state", None)
    payload.pop("type", None)
    try:
        r = await _api("PATCH", f"/shops/{shop_id}/listings/{mapping['etsy_listing_id']}", data=payload)
        if r.status_code >= 400:
            await _audit("update", "failure", f"Update failed (HTTP {r.status_code}).", {"product": prod.get("code")})
            return {"error": "Etsy rejected the update.", "detail": _redact(r.text)[:200]}
    except Exception as e:
        await _audit("update", "failure", f"Update error: {e}", {"product": prod.get("code")})
        return {"error": "Failed to update the Etsy listing."}
    await db[MAP].update_one({"id": mapping["id"]}, {"$set": {
        "last_synced_at": now_iso(), "last_sync_hash": _sync_hash(prod),
        "qru_product_version": str(prod["version"]), "sync_status": "in_sync", "updated_at": now_iso()}})
    await _audit("update", "success", "Etsy listing updated.", {"product": prod.get("code")})
    return {"ok": True, "message": "Etsy listing updated."}


async def sync_status(product_id):
    """Compare QRU vs Etsy; return proposed changes. Never overwrites silently."""
    prod = await _load_qru_product(product_id)
    mapping = await db[MAP].find_one({"qru_product_id": (prod or {}).get("id")}, {"_id": 0})
    if not prod.get("found"):
        return {"error": "QRU product not found."}
    if not mapping:
        return {"mapped": False, "proposed": "publish_draft",
                "detail": "Not yet on Etsy — create a draft to map it."}
    cur = _sync_hash(prod)
    drift = cur != mapping.get("last_sync_hash")
    await _audit("sync", "success", "Sync compared (read-only).", {"product": prod.get("code")})
    return {
        "mapped": True, "etsy_listing_id": mapping.get("etsy_listing_id"),
        "etsy_listing_state": mapping.get("etsy_listing_state"),
        "in_sync": not drift,
        "proposed_changes": (["Update Etsy title/description/price/tags to match QRU"] if drift else []),
        "qru_version": str(prod["version"]),
        "last_published_at": mapping.get("last_published_at"),
        "last_synced_at": mapping.get("last_synced_at"),
        "note": "Read-only comparison — no system is overwritten automatically.",
    }


async def listings():
    doc = await _integration()
    if not doc or not doc.get("shop_id"):
        return {"error": "Etsy is not connected."}
    r = await _api("GET", f"/shops/{doc['shop_id']}/listings", params={"limit": 100, "state": "draft"})
    r.raise_for_status()
    raw = r.json().get("results", [])
    return {"count": len(raw), "listings": [{
        "listing_id": x.get("listing_id"), "title": x.get("title"), "state": x.get("state"),
        "price": (x.get("price") or {}).get("amount"), "url": x.get("url"),
    } for x in raw]}


async def orders():
    doc = await _integration()
    if not doc or not doc.get("shop_id"):
        return {"error": "Etsy is not connected."}
    r = await _api("GET", f"/shops/{doc['shop_id']}/receipts", params={"limit": 50})
    r.raise_for_status()
    raw = r.json().get("results", [])
    return {"count": len(raw), "orders": [{
        "receipt_id": x.get("receipt_id"), "status": x.get("status"),
        "total": (x.get("grandtotal") or {}).get("amount"), "created": x.get("create_timestamp"),
    } for x in raw]}


async def eligible_products(limit=100):
    """List QRU products with Etsy eligibility + mapping (for the Founder UI)."""
    out = []
    async for b in db.book_records.find({}, {"_id": 0, "id": 1, "book_code": 1, "title": 1}).limit(limit):
        prod = await _load_qru_product(b["id"])
        elig = eligibility(prod)
        mapping = await db[MAP].find_one({"qru_product_id": b["id"]}, {"_id": 0})
        out.append({
            "id": b["id"], "code": b.get("book_code"), "title": b.get("title"),
            "eligible": elig["eligible"], "imprint": prod.get("imprint"),
            "etsy_listing_id": (mapping or {}).get("etsy_listing_id"),
            "etsy_state": (mapping or {}).get("etsy_listing_state"),
            "etsy_url": (mapping or {}).get("etsy_url"),
            "sync_status": (mapping or {}).get("sync_status"),
        })
    out.sort(key=lambda r: (not r["eligible"], r["code"] or ""))
    return {"count": len(out), "products": out}
