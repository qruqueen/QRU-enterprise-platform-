"""QRU Integration Hub™ — single source of truth for every external platform.

Connect Once. Manufacture Forever. Distribute Everywhere.

NOTE: Sensitive credentials are encrypted at rest (Fernet) and NEVER returned by the API.
Live external publishing is performed by a connector layer. Until a platform's real
OAuth app / API credentials are wired via the integration expert, distribution to that
platform is SIMULATED (recorded as published with generated metadata) so the full
factory workflow operates end-to-end. Real connectors can be activated per platform
without redesigning the hub.
"""
import os
import logging
from cryptography.fernet import Fernet

from database import db
from models import gen_id, now_iso
from ai_service import llm_generate, parse_json
from org_activity import log_org

logger = logging.getLogger("qru.integrations")

_fernet = Fernet(os.environ["INTEGRATION_ENC_KEY"].encode())


def _encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def _decrypt(token: str) -> str:
    try:
        return _fernet.decrypt(token.encode()).decode()
    except Exception:
        return ""


# ---------------- Platform catalog ----------------
PLATFORM_CATALOG = {
    "Publishing": ["Amazon KDP", "Apple Books", "Google Play Books", "Kobo", "Barnes & Noble Press"],
    "Educational": ["Teachers Pay Teachers", "QRU Academy", "Future LMS"],
    "Commerce": ["Shopify", "Etsy", "Gumroad", "WooCommerce", "QRU Store"],
    "Video": ["YouTube", "Vimeo"],
    "Marketing": ["Facebook", "Instagram", "TikTok", "Pinterest", "LinkedIn", "X"],
    "Storage": ["Google Drive", "Dropbox", "OneDrive"],
    "Communication": ["Mailchimp", "ConvertKit", "Email Provider"],
    "Payment": ["Stripe", "PayPal", "Square"],
    "Analytics": ["Google Analytics", "Search Console"],
    "AI Services": ["Gemini Nano Banana (Image)", "OpenAI Image", "Runway (Video)",
                    "Pika (Video)", "D-ID (Animation)", "ElevenLabs (Voice)",
                    "OpenAI TTS (Voice)", "Suno (Music)", "Gamma (Presentation)",
                    "DeepL (Translation)", "Whisper (Captions)"],
}

# OAuth-preferred platforms (else API key / token).
OAUTH_PLATFORMS = {
    "Amazon KDP", "Apple Books", "Google Play Books", "YouTube", "Vimeo", "Shopify",
    "Etsy", "Facebook", "Instagram", "TikTok", "Pinterest", "LinkedIn", "X",
    "Google Drive", "Dropbox", "OneDrive", "Mailchimp", "ConvertKit", "Stripe",
    "PayPal", "Square", "Google Analytics", "Search Console",
}

# Smart routing: product type -> default target platforms.
ROUTING_DEFAULTS = {
    "Book": ["Amazon KDP", "QRU Store"],
    "Workbook": ["Amazon KDP", "Teachers Pay Teachers", "QRU Store"],
    "Teacher Guide": ["Teachers Pay Teachers", "QRU Store"],
    "Lesson Plan": ["Teachers Pay Teachers", "QRU Academy"],
    "Interactive Lesson": ["QRU Academy", "QRU Store"],
    "Course": ["QRU Academy"],
    "Video Script": ["YouTube"],
    "Poster": ["Etsy", "QRU Store"],
    "Infographic": ["Etsy", "Pinterest", "QRU Store"],
    "Printable PDF": ["Etsy", "Teachers Pay Teachers", "QRU Store"],
    "Short-form Content": ["Instagram", "TikTok", "X"],
    "Quiz": ["QRU Academy"],
    "Flash Cards": ["Teachers Pay Teachers", "QRU Store"],
    "Certificate": ["QRU Academy"],
    "Presentation": ["QRU Store"],
    "Caregiver Guide": ["QRU Store", "Amazon KDP"],
    "Podcast Script": ["QRU Store"],
    "AI Tutor": ["QRU Academy"],
}


def platform_auth_type(platform: str) -> str:
    return "oauth" if platform in OAUTH_PLATFORMS else "api_key"


def mask(conn: dict) -> dict:
    """Public-safe view — never expose secrets."""
    return {
        "id": conn["id"], "platform": conn["platform"], "category": conn.get("category"),
        "auth_type": conn.get("auth_type"), "account_name": conn.get("account_name"),
        "display_name": conn.get("display_name"), "channel_name": conn.get("channel_name"),
        "store_name": conn.get("store_name"), "publisher_name": conn.get("publisher_name"),
        "default_pricing": conn.get("default_pricing"), "license_rules": conn.get("license_rules"),
        "default_categories": conn.get("default_categories", []), "tags": conn.get("tags", []),
        "branding": conn.get("branding"), "publishing_rules": conn.get("publishing_rules"),
        "status": conn.get("status", "Disconnected"), "connection_health": conn.get("connection_health", "unknown"),
        "last_sync": conn.get("last_sync"), "has_credentials": bool(conn.get("secret_enc")),
        "created_at": conn.get("created_at"), "updated_at": conn.get("updated_at"),
    }


async def upsert_connection(data: dict, owner_id: str) -> dict:
    platform = data["platform"]
    category = next((c for c, ps in PLATFORM_CATALOG.items() if platform in ps), data.get("category", "Other"))
    existing = await db.integrations.find_one({"platform": platform})
    doc = existing or {"id": gen_id(), "platform": platform, "created_at": now_iso(), "owner_id": owner_id}
    doc.update({
        "category": category, "auth_type": platform_auth_type(platform),
        "account_name": data.get("account_name", ""), "display_name": data.get("display_name", ""),
        "channel_name": data.get("channel_name", ""), "store_name": data.get("store_name", ""),
        "publisher_name": data.get("publisher_name", ""),
        "default_pricing": data.get("default_pricing", ""), "license_rules": data.get("license_rules", "Personal Use"),
        "default_categories": data.get("default_categories", []), "tags": data.get("tags", []),
        "branding": data.get("branding", "QRU"), "publishing_rules": data.get("publishing_rules", ""),
        "updated_at": now_iso(),
    })
    secret = data.get("credential")
    if secret:
        doc["secret_enc"] = _encrypt(secret)
        doc["status"] = "Connected"
        doc["connection_health"] = "healthy"
        doc["last_sync"] = now_iso()
    else:
        doc.setdefault("status", "Configured")
        doc.setdefault("connection_health", "unknown")
    if existing:
        await db.integrations.update_one({"id": doc["id"]}, {"$set": doc})
    else:
        await db.integrations.insert_one(dict(doc))
    await log_org("Brand Director™", "Brand", f"configured integration: {platform}", platform, "success")
    return mask(doc)


async def test_connection(cid: str) -> dict:
    conn = await db.integrations.find_one({"id": cid})
    if not conn:
        return None
    # Real connectors would ping the platform API here. Without live credentials we
    # report health based on whether credentials are stored (SIMULATED check).
    if conn.get("secret_enc"):
        health, status = "healthy", "Connected"
    else:
        health, status = "needs_auth", "Configured"
    await db.integrations.update_one(
        {"id": cid}, {"$set": {"connection_health": health, "status": status, "last_sync": now_iso()}})
    conn = await db.integrations.find_one({"id": cid})
    return mask(conn)


async def get_routing():
    doc = await db.integration_routing.find_one({"id": "routing"})
    if not doc:
        doc = {"id": "routing", "rules": ROUTING_DEFAULTS}
        await db.integration_routing.insert_one(dict(doc))
    return doc.get("rules", ROUTING_DEFAULTS)


async def route_targets(product_type: str):
    rules = await get_routing()
    return rules.get(product_type, ["QRU Store"])


METADATA_SYSTEM = """You are the QRU Distribution Metadata Engine. Given an educational product,
produce marketplace-ready metadata. Return ONLY JSON:
{"seo_title": "<=60 chars", "description": "compelling 2-3 sentence sales description",
 "keywords": ["k1","k2","k3","k4","k5"], "categories": ["cat1","cat2"]}"""


async def _generate_metadata(product):
    prompt = f"Title: {product.get('title')}\nType: {product.get('product_type')}\nTopic: {product.get('topic','')}\nAudience: {product.get('audience','')}"
    raw = await llm_generate(METADATA_SYSTEM, prompt, f"meta-{product['id']}")
    return parse_json(raw) or {}


async def auto_distribute(product_id: str, actor: str = "AI Distribution Team™") -> dict:
    """Route a published product to all connected target platforms. SIMULATED delivery
    where live connectors are not yet wired; records full publication history and
    escalates only on failure."""
    product = await db.products.find_one({"id": product_id})
    if not product:
        return {"error": "not found"}
    targets = await route_targets(product.get("product_type", "Interactive Lesson"))
    metadata = await _generate_metadata(product)

    results, failures = [], 0
    for platform in targets:
        conn = await db.integrations.find_one({"platform": platform})
        if not conn or conn.get("status") not in ("Connected",):
            results.append({"platform": platform, "status": "skipped", "reason": "not connected"})
            continue
        if conn.get("connection_health") in ("error", "expired"):
            results.append({"platform": platform, "status": "failed", "reason": "connection unhealthy"})
            failures += 1
            continue
        # SIMULATED publish (real connector would call the platform API here).
        rec = {
            "id": gen_id(), "product_id": product_id, "product_code": product.get("product_code"),
            "title": product.get("title"), "platform": platform, "status": "published",
            "mode": "simulated", "metadata": metadata, "license": product.get("license_type"),
            "external_url": f"https://qru.example/{platform.lower().replace(' ', '-')}/{product.get('product_code')}",
            "published_at": now_iso(), "by": actor,
        }
        await db.distributions.insert_one(dict(rec))
        results.append({"platform": platform, "status": "published", "mode": "simulated"})

    published = [r for r in results if r["status"] == "published"]
    await db.products.update_one(
        {"id": product_id},
        {"$set": {"distribution": {"targets": targets, "results": results, "metadata": metadata,
                                   "distributed_at": now_iso()}, "updated_at": now_iso()}})
    await log_org("AI Distribution Team™", "Manufacturing",
                  f"distributed to {len(published)} platform(s)", product.get("product_code", ""),
                  "success" if failures == 0 else "warning")

    if failures:
        await db.founder_escalations.insert_one({
            "id": gen_id(), "type": "distribution", "product_id": product_id,
            "product_code": product.get("product_code"), "title": product.get("title"),
            "reason": f"{failures} platform distribution(s) failed and need attention", "status": "Open",
            "created_at": now_iso(),
        })
        await db.notifications.insert_one({
            "id": gen_id(), "level": "warning", "read": False, "created_at": now_iso(),
            "message": f"Distribution issue — {product.get('product_code')}: {failures} platform(s) failed."})
    return {"targets": targets, "results": results, "failures": failures}


async def monitor_summary():
    conns = await db.integrations.find().to_list(200)
    connected = [c for c in conns if c.get("status") == "Connected"]
    unhealthy = [mask(c) for c in conns if c.get("connection_health") in ("error", "expired")]
    dist_total = await db.distributions.count_documents({})
    dist_failed = await db.distributions.count_documents({"status": "failed"})
    open_dist_esc = await db.founder_escalations.count_documents({"type": "distribution", "status": "Open"})
    return {
        "platforms_configured": len(conns), "platforms_connected": len(connected),
        "unhealthy": unhealthy, "distributions_total": dist_total, "distributions_failed": dist_failed,
        "open_distribution_escalations": open_dist_esc,
        "categories": {c: len(ps) for c, ps in PLATFORM_CATALOG.items()},
    }
