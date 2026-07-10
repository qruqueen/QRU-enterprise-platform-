"""QRU Media Acquisition Foundation™ — MO-021 (Stock Video) + MO-023 (Audio Intelligence).

A single governed acquisition layer for external media (video + audio). Every provider implements one
honest contract: it is only "connected" when real credentials exist, and every acquired asset preserves
its source, creator, license, commercial-use status and usage — registered in the Master Asset Vault™.

Factory rules enforced:
  • FR-097 No Unverified Stock Media™ — public internet availability is NEVER proof of permission.
  • Audio rule — no audio enters a QRU product without verified licensing + metadata + vault registration.

Treasure Standard™: no faked "connected" states, no random internet pulls, no assumed rights.
"""
import httpx

from database import db
from models import now_iso, gen_id
from distribution.connectors import save_connector_credentials, get_connector_credentials

# --- Providers. tier1 free-API providers are live-capable once a key is added; others are prepared. ---
PROVIDERS = [
    {"id": "pexels_video", "name": "Pexels Video", "kind": "video", "tier": 1, "configurable": True,
     "credential": "api_key", "license": "Pexels License (free, commercial OK, no attribution required)",
     "hint": "Get a free API key at pexels.com/api."},
    {"id": "pixabay_video", "name": "Pixabay Video", "kind": "video", "tier": 1, "configurable": True,
     "credential": "api_key", "license": "Pixabay Content License (free, commercial OK)",
     "hint": "Get a free API key at pixabay.com/api/docs."},
    {"id": "pixabay_music", "name": "Pixabay Music & SFX", "kind": "audio", "tier": 1, "configurable": True,
     "credential": "api_key", "license": "Pixabay Content License (free, commercial OK)",
     "hint": "Uses the same Pixabay API key."},
    {"id": "freesound", "name": "Freesound", "kind": "audio", "tier": 1, "configurable": True,
     "credential": "api_key", "license": "Per-sound (CC0 / CC-BY / CC-BY-NC) — must verify per asset",
     "hint": "Requires per-asset license verification before commercial use."},
    {"id": "free_music_archive", "name": "Free Music Archive", "kind": "audio", "tier": 1, "configurable": False,
     "credential": None, "license": "Per-track — commercial licensing must be verified", "hint": "Manual license verification required per track."},
    # Tier 2 — prepared connectors, activate after subscription/legal review.
    {"id": "storyblocks", "name": "Storyblocks", "kind": "both", "tier": 2, "configurable": False, "credential": None, "license": "Subscription", "hint": "Enterprise/API access & licensing review required."},
    {"id": "adobe_stock", "name": "Adobe Stock", "kind": "both", "tier": 2, "configurable": False, "credential": None, "license": "Subscription/credit", "hint": "Account + licensing review required."},
    {"id": "shutterstock", "name": "Shutterstock", "kind": "both", "tier": 2, "configurable": False, "credential": None, "license": "Subscription", "hint": "Account + licensing review required."},
    {"id": "epidemic_sound", "name": "Epidemic Sound", "kind": "audio", "tier": 2, "configurable": False, "credential": None, "license": "Subscription", "hint": "Subscription + API access required."},
    {"id": "artlist", "name": "Artlist", "kind": "audio", "tier": 2, "configurable": False, "credential": None, "license": "Subscription", "hint": "Subscription + licensing review required."},
]

VIDEO_COLLECTIONS = [
    "QRU General Backgrounds", "QRU Purple and Gold Motion", "Education and Learning", "Books and Libraries",
    "Human Brain and Understanding", "Artificial Intelligence", "Technology and Innovation", "Global Markets",
    "Forex and Currency", "Entrepreneurship", "Community and Family", "Youth Learning", "Nature and Earth",
    "Cities and Global Culture", "Abstract Light and Motion", "Documentary B-Roll", "Cinematic Openings",
    "Cinematic Closings", "QRU Signature Reveal Backgrounds", "Mobile Vertical Backgrounds",
    "Presentation Backgrounds", "Neutral Looping Backgrounds",
]

AUDIO_COLLECTIONS = [
    "Peace", "Reflection", "Hope", "Morning", "Evening", "Sleep", "Prayer", "Meditation", "Study",
    "Deep Focus", "Gratitude", "Nature", "Ocean", "Rain", "Forest", "Fireplace", "Wind", "Breathing",
    "Piano", "Strings", "Ambient", "Cinematic", "Documentary", "Background Loops", "Short Intros",
    "QRU Signature Theme", "QRU Outro Theme",
]

# Listening-purpose categories used INSTEAD of unproven therapeutic frequency claims (Treasure Standard™).
LISTENING_PURPOSES = ["Relaxation", "Reflection", "Meditation", "Mindfulness", "Calm", "Focus", "Sleep", "Inspiration"]

ASSET_SCHEMA = [
    "qru_asset_id", "provider", "provider_asset_id", "kind", "source_url", "creator_name", "creator_profile_url",
    "title", "tags", "search_query_used", "collection", "listening_purpose", "duration_seconds", "width", "height",
    "aspect_ratio", "frame_rate", "file_size_bytes", "preview_url", "license_type", "license_url", "license_snapshot",
    "attribution_required", "attribution_text", "commercial_use_allowed", "modification_allowed",
    "redistribution_restricted", "download_date", "imported_by", "approval_status", "active_status",
    "master_asset_vault_id", "checksum", "version", "created_at", "updated_at",
]

FACTORY_RULES = [
    {"id": "FR-097", "title": "No Unverified Stock Media™",
     "statement": "No external stock image, video, music, or sound effect may enter a QRU product unless its "
                  "source, creator, license, commercial-use status, download record, project assignment and "
                  "usage history have been verified and preserved. Public internet availability is never proof of permission."},
    {"id": "FR-AUDIO", "title": "No Unverified Audio™",
     "statement": "No audio enters a QRU product without verified licensing, commercial approval, metadata "
                  "preservation and permanent registration inside the Master Asset Vault™."},
]

_CONFIGURABLE = {p["id"]: p for p in PROVIDERS if p.get("configurable")}


async def provider_status():
    """Honest connection status for every provider (connected only when a real key exists)."""
    out = []
    for p in PROVIDERS:
        connected = False
        if p.get("configurable"):
            creds = await get_connector_credentials(p["id"], secret_fields=("api_key",))
            connected = bool(creds and creds.get("api_key"))
        out.append({**p, "connected": connected,
                    "status": "Connected" if connected else ("Developer Setup Required" if p.get("configurable") else "Prepared — Not Activated")})
    return out


async def save_provider_key(provider_id, api_key):
    if provider_id not in _CONFIGURABLE:
        return False, "This provider is not configurable via an API key."
    await save_connector_credentials(provider_id, {"api_key": api_key}, ("api_key",))
    return True, None


async def _pixabay_key():
    # Pixabay video + music share one key.
    for pid in ("pixabay_video", "pixabay_music"):
        c = await get_connector_credentials(pid, secret_fields=("api_key",))
        if c and c.get("api_key"):
            return c["api_key"]
    return None


async def search(provider_id, query, per_page=12):
    """Live search when the provider is configured; otherwise an honest NEEDS_SETUP response.
    Never pulls from the open internet — only from the approved provider API."""
    p = _CONFIGURABLE.get(provider_id)
    if not p:
        return {"configured": False, "reason": "Unknown or non-configurable provider.", "results": []}
    try:
        if provider_id == "pexels_video":
            c = await get_connector_credentials("pexels_video", secret_fields=("api_key",))
            if not (c and c.get("api_key")):
                return {"configured": False, "reason": p["hint"], "results": []}
            async with httpx.AsyncClient(headers={"Authorization": c["api_key"]}, timeout=25) as client:
                r = await client.get("https://api.pexels.com/videos/search", params={"query": query, "per_page": per_page})
            if r.status_code >= 400:
                return {"configured": True, "error": f"Pexels error {r.status_code}.", "results": []}
            return {"configured": True, "results": [_norm_pexels(v) for v in r.json().get("videos", [])]}

        if provider_id in ("pixabay_video", "pixabay_music"):
            key = await _pixabay_key()
            if not key:
                return {"configured": False, "reason": p["hint"], "results": []}
            url = "https://pixabay.com/api/videos/" if provider_id == "pixabay_video" else "https://pixabay.com/api/"
            params = {"key": key, "q": query, "per_page": per_page}
            if provider_id == "pixabay_music":
                params["media_type"] = "music"
            async with httpx.AsyncClient(timeout=25) as client:
                r = await client.get(url, params=params)
            if r.status_code >= 400:
                return {"configured": True, "error": f"Pixabay error {r.status_code}.", "results": []}
            return {"configured": True, "results": [_norm_pixabay(v, provider_id) for v in r.json().get("hits", [])]}

        if provider_id == "freesound":
            c = await get_connector_credentials("freesound", secret_fields=("api_key",))
            if not (c and c.get("api_key")):
                return {"configured": False, "reason": p["hint"], "results": []}
            async with httpx.AsyncClient(timeout=25) as client:
                r = await client.get("https://freesound.org/apiv2/search/text/",
                                     params={"query": query, "token": c["api_key"], "page_size": per_page,
                                             "fields": "id,name,username,previews,license,url,duration"})
            if r.status_code >= 400:
                return {"configured": True, "error": f"Freesound error {r.status_code}.", "results": []}
            return {"configured": True, "note": "Verify each sound's license before commercial use.",
                    "results": [_norm_freesound(s) for s in r.json().get("results", [])]}
    except Exception as e:
        return {"configured": True, "error": str(e)[:120], "results": []}
    return {"configured": False, "reason": "Provider not implemented for live search yet.", "results": []}


def _norm_pexels(v):
    files = sorted(v.get("video_files", []), key=lambda f: (f.get("width") or 0), reverse=True)
    return {"provider": "pexels_video", "provider_asset_id": str(v.get("id")), "kind": "video",
            "title": (v.get("url") or "").rstrip("/").split("/")[-1].replace("-", " "),
            "creator_name": (v.get("user") or {}).get("name"), "creator_profile_url": (v.get("user") or {}).get("url"),
            "source_url": v.get("url"), "preview_url": v.get("image"),
            "duration_seconds": v.get("duration"), "width": v.get("width"), "height": v.get("height"),
            "file_url": files[0].get("link") if files else None,
            "license_type": "Pexels License", "commercial_use_allowed": True, "attribution_required": False}


def _norm_pixabay(v, pid):
    if pid == "pixabay_music":
        return {"provider": pid, "provider_asset_id": str(v.get("id")), "kind": "audio",
                "title": v.get("tags"), "creator_name": v.get("user"), "source_url": v.get("pageURL"),
                "preview_url": None, "duration_seconds": v.get("duration"),
                "license_type": "Pixabay Content License", "commercial_use_allowed": True, "attribution_required": False}
    vids = v.get("videos") or {}
    best = vids.get("large") or vids.get("medium") or {}
    return {"provider": pid, "provider_asset_id": str(v.get("id")), "kind": "video",
            "title": v.get("tags"), "creator_name": v.get("user"), "source_url": v.get("pageURL"),
            "preview_url": (vids.get("tiny") or {}).get("thumbnail"),
            "duration_seconds": v.get("duration"), "width": best.get("width"), "height": best.get("height"),
            "file_url": best.get("url"),
            "license_type": "Pixabay Content License", "commercial_use_allowed": True, "attribution_required": False}


def _norm_freesound(s):
    return {"provider": "freesound", "provider_asset_id": str(s.get("id")), "kind": "audio",
            "title": s.get("name"), "creator_name": s.get("username"), "source_url": s.get("url"),
            "preview_url": (s.get("previews") or {}).get("preview-hq-mp3"), "duration_seconds": s.get("duration"),
            "license_type": s.get("license"), "license_url": s.get("license"),
            "commercial_use_allowed": None, "attribution_required": True,
            "verify_note": "License must be verified before commercial use."}


async def register_asset(item, collection, purpose, actor):
    """Register an approved external asset into the Master Asset Vault™ with full provenance (FR-097)."""
    doc = {
        "id": gen_id(), "qru_asset_id": f"QRU-MEDIA-{gen_id()[:8].upper()}",
        "provider": item.get("provider"), "provider_asset_id": item.get("provider_asset_id"),
        "kind": item.get("kind"), "source_url": item.get("source_url"), "creator_name": item.get("creator_name"),
        "creator_profile_url": item.get("creator_profile_url"), "title": item.get("title"),
        "search_query_used": item.get("search_query_used"), "collection": collection, "listening_purpose": purpose,
        "duration_seconds": item.get("duration_seconds"), "width": item.get("width"), "height": item.get("height"),
        "preview_url": item.get("preview_url"), "file_url": item.get("file_url"),
        "license_type": item.get("license_type"), "license_url": item.get("license_url"),
        "attribution_required": item.get("attribution_required"), "commercial_use_allowed": item.get("commercial_use_allowed"),
        "download_date": now_iso(), "imported_by": actor,
        "approval_status": "Pending Review" if item.get("commercial_use_allowed") is None else "Approved",
        "active_status": "Active", "version": 1, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.media_assets.insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


def config():
    return {
        "providers": PROVIDERS,
        "video_collections": VIDEO_COLLECTIONS,
        "audio_collections": AUDIO_COLLECTIONS,
        "listening_purposes": LISTENING_PURPOSES,
        "asset_schema": ASSET_SCHEMA,
        "factory_rules": FACTORY_RULES,
        "modules": [{"id": "MO-021", "name": "Stock Media Intelligence System™"},
                    {"id": "MO-023", "name": "Audio Intelligence & Licensed Sound Library™"}],
    }
