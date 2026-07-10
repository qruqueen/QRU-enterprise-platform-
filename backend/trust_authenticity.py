"""QRU Trust & Authenticity System™ — MO-015 / MO-016 / MO-017 + Factory Rule FR-095.

One cohesive layer on top of the existing Product Protection Agent™:
  • MO-015 Content Protection & Rights Management™ — layered protection + rights + authenticity cert.
  • MO-016 Trust & Authenticity Registry™          — permanent identity/registry + public/internal lookup.
  • MO-017 Platform Capability Awareness™           — apply the highest protection each platform supports.
  • FR-095 Protect Without Punishing™               — protect with layered security while preserving an
                                                      excellent learning experience.

Treasure Standard™: capability status is HONEST — a protection layer is only reported as "enforced" when
it is genuinely enforced in this system today; platform-only capabilities (screen-capture blocking, DRM,
secure streaming) are reported as "platform_provided" or "planned", never faked as active.
"""
import base64
import io

import qrcode
import qrcode.image.svg

from database import db
from models import now_iso

COPYRIGHT_HOLDER = "QRU / Erica Talbert"
QRU_SEAL = "QRU-SEAL™"

# status: enforced | configurable | platform_provided | planned
PROTECTION_LAYERS = {
    "access_control": {
        "label": "Access Control", "status": "enforced",
        "features": ["authentication", "membership_validation", "role_permissions",
                     "purchase_verification", "expiration_rules"],
        "detail": "Account/purchase-gated secure links with expiry & access limits are enforced now."},
    "watermarking": {
        "label": "Watermarking", "status": "enforced",
        "features": ["visible_watermark", "personalized_watermark", "qr_code", "customer_identifier"],
        "detail": "License + customer watermark stamped into delivered content; QR authenticity available."},
    "metadata": {
        "label": "Embedded Metadata", "status": "enforced",
        "features": ["product_id", "version", "copyright", "license", "creation_date", "author", "qruseal"],
        "detail": "Every authenticity certificate embeds the QRU-SEAL™ and provenance metadata."},
    "platform_security": {
        "label": "Platform Security", "status": "platform_provided",
        "features": ["screen_capture_protection", "disable_downloads", "protected_streaming"],
        "detail": "Enforced by the destination platform when supported (see Platform Capability Awareness™). "
                  "QRU requests the highest available; it never claims control it does not have."},
    "audit_logging": {
        "label": "Audit Logging", "status": "enforced",
        "features": ["downloads", "exports", "publications", "revisions", "approvals"],
        "detail": "Access, license grants, publications and verification events are recorded and queryable."},
}

# security_level -> requirement
SECURITY_LEVELS = {
    "open": {"label": "Open", "requirement": "public_access", "detail": "Publicly accessible."},
    "standard": {"label": "Standard", "requirement": "purchase_required", "detail": "Requires a purchase."},
    "premium": {"label": "Premium", "requirement": "authenticated_access", "detail": "Authenticated members only."},
    "enterprise": {"label": "Enterprise", "requirement": "contract_required", "detail": "Requires a contract."},
    "internal": {"label": "Internal", "requirement": "qru_staff_only", "detail": "QRU staff only."},
}

DISTRIBUTION_CHANNELS = ["wordpress", "youtube", "kdp", "teachers_pay_teachers", "shopify",
                         "etsy", "podcast_platforms", "customer_library"]
DISTRIBUTION_PERMISSIONS = ["public", "members", "licensed", "enterprise", "internal_only"]

# MO-017 — honest per-platform protection capability matrix.
# supported = protections the platform can actually enforce; best_available = QRU's applied fallback.
PLATFORM_CAPABILITIES = {
    "customer_library": {"label": "QRU Customer Library™", "supported": ["disable_downloads", "protected_streaming", "watermarking", "access_control"],
                         "best_available": "Full QRU-native protection: gated streaming, expiring access, personalized watermark."},
    "youtube": {"label": "YouTube", "supported": ["protected_streaming"],
                "best_available": "Unlisted/members-only + on-screen brand watermark; downloads controlled by YouTube."},
    "wordpress": {"label": "WordPress / Blog", "supported": ["access_control"],
                  "best_available": "Membership gating + visible watermark & copyright metadata."},
    "shopify": {"label": "Shopify", "supported": ["access_control", "download_controls"],
                "best_available": "Purchase-gated digital delivery with expiring links & watermark."},
    "etsy": {"label": "Etsy", "supported": [],
             "best_available": "Watermark + copyright metadata only (Etsy provides no DRM)."},
    "kdp": {"label": "Amazon KDP", "supported": ["drm"],
            "best_available": "Amazon DRM (when enabled at publish) + embedded copyright metadata."},
    "teachers_pay_teachers": {"label": "Teachers Pay Teachers", "supported": ["download_controls"],
                              "best_available": "TpT download controls + personalized teacher-license watermark."},
    "podcast_platforms": {"label": "Podcast Platforms", "supported": [],
                          "best_available": "Audio brand intro/outro + episode copyright metadata (no DRM available)."},
}
ALL_PROTECTIONS = ["screen_capture_protection", "protected_video", "watermarking", "download_controls", "drm", "secure_streaming"]

FACTORY_RULE = {
    "id": "FR-095", "title": "Protect Without Punishing™",
    "statement": "QRU products are protected using layered security, authenticity verification, licensing, "
                 "watermarking, and platform-aware controls while preserving an excellent customer learning "
                 "experience. Protection must never unnecessarily interfere with legitimate learning.",
}


def qr_svg_data_url(text):
    img = qrcode.make(text, image_factory=qrcode.image.svg.SvgImage, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf)
    return "data:image/svg+xml;base64," + base64.b64encode(buf.getvalue()).decode()


def _version(p):
    return str(p.get("qbos_version") or p.get("qeds_version") or "1.0")


def _release_date(p):
    return p.get("listed_at") or p.get("created_at")


async def _manufacturing_record(p):
    mo = None
    if p.get("knowledge_record_id"):
        mo = await db.manufacturing_orders.find_one({"knowledge_record_id": p["knowledge_record_id"]}, {"mo_code": 1, "status": 1, "topic": 1})
    return {
        "knowledge_record_id": p.get("knowledge_record_id"),
        "mo_code": (mo or {}).get("mo_code"),
        "manufacturing_status": (mo or {}).get("status"),
        "created_at": p.get("created_at"),
        "product_family": p.get("family") or p.get("product_type"),
    }


def _approval_history(p):
    history = []
    v = p.get("verification") or {}
    if v:
        history.append({"stage": "Verification", "decision": v.get("decision") or ("Verified" if p.get("verified") else "Pending"),
                        "authority": v.get("reviewer") or "QRU Verification Team™",
                        "confidence": v.get("confidence_score"), "at": v.get("verified_at") or p.get("updated_at")})
    if p.get("design_gate"):
        dg = p.get("design_gate")
        if isinstance(dg, dict):
            dg = dg.get("status") or dg.get("decision") or ("Passed" if dg.get("passed") else "Reviewed")
        history.append({"stage": "Design Gate", "decision": str(dg), "authority": "Design Director™", "at": p.get("updated_at")})
    if p.get("status") in ("Published", "Listed"):
        history.append({"stage": "Publication", "decision": p.get("status"), "authority": "Distribution Framework™", "at": p.get("listed_at") or p.get("updated_at")})
    return history


def treasure_status(p):
    return "Met" if p.get("verified") else "Pending"


def gold_status(p):
    dg = p.get("design_gate")
    if isinstance(dg, dict):
        dg = dg.get("status") or dg.get("decision") or dg.get("result") or ""
    dg = str(dg or "").lower()
    if dg in ("passed", "cleared", "approved", "pass"):
        return "Met"
    return "Pending Human Review"


async def authenticity_certificate(p, verify_base_url=""):
    """MO-015 authenticity certificate + QRU-SEAL™ + QR verification code."""
    code = p.get("product_code")
    verify_url = f"{verify_base_url}/api/trust/verify/{code}" if verify_base_url else f"/api/trust/verify/{code}"
    cert_id = f"QRU-CERT-{code}"
    return {
        "qru_product_id": code,
        "authenticity_certificate": cert_id,
        "title": p.get("title"),
        "author": COPYRIGHT_HOLDER,
        "copyright": f"© {(_release_date(p) or now_iso())[:4]} {COPYRIGHT_HOLDER}. All rights reserved.",
        "qruseal": QRU_SEAL,
        "treasure_standard_status": treasure_status(p),
        "gold_standard_status": gold_status(p),
        "version": _version(p),
        "release_date": _release_date(p),
        "manufacturing_record": await _manufacturing_record(p),
        "approval_history": _approval_history(p),
        "license_type": p.get("license_type"),
        "verify_url": verify_url,
        "qr_code": qr_svg_data_url(verify_url),
        "authentic": bool(p.get("verified")),
    }


async def registry_record(p):
    """MO-016 permanent identity/registry record."""
    return {
        "product_id": p.get("product_code"),
        "internal_id": p.get("id"),
        "knowledge_record": p.get("knowledge_record_id"),
        "product_family": p.get("family") or p.get("product_type"),
        "manufacturing_date": p.get("created_at"),
        "version": _version(p),
        "approvals": _approval_history(p),
        "revisions": p.get("qbos_version") and [{"version": _version(p), "at": p.get("updated_at")}] or [],
        "ownership": COPYRIGHT_HOLDER,
        "copyright": f"© {(_release_date(p) or now_iso())[:4]} {COPYRIGHT_HOLDER}.",
        "publication_history": [{"status": p.get("status"), "at": p.get("listed_at") or p.get("updated_at")}] if p.get("status") else [],
        "active_status": "Active" if p.get("status") in ("Published", "Listed") else (p.get("status") or "In Manufacturing"),
        "treasure_standard_status": treasure_status(p),
        "gold_standard_status": gold_status(p),
    }


def platform_protection_plan(platform, security_level="standard"):
    """MO-017 — the highest protection each platform supports, plus QRU's best-available fallback."""
    cap = PLATFORM_CAPABILITIES.get(platform)
    if not cap:
        return {"platform": platform, "known": False,
                "applied": ["watermarking", "metadata", "access_control"],
                "note": "Unknown platform — QRU applies its best-available baseline (watermark + metadata + access control)."}
    supported = cap["supported"]
    always = ["watermarking", "metadata"]  # QRU-native, applied everywhere
    applied = sorted(set(supported) | set(always))
    unsupported = [p for p in ALL_PROTECTIONS if p not in supported and p not in always]
    return {
        "platform": platform, "label": cap["label"], "known": True,
        "security_level": security_level,
        "platform_supported": supported,
        "applied": applied,
        "unsupported": unsupported,
        "best_available": cap["best_available"],
        "factory_rule": FACTORY_RULE["id"],
    }


async def audit_log(product_id, product_code):
    """FR-095 / MO-015 audit trail assembled from real collections."""
    events = []
    for l in await db.product_access_links.find({"product_id": product_id}).sort("created_at", -1).to_list(200):
        events.append({"type": "download_access", "at": l.get("last_access") or l.get("created_at"),
                       "detail": f"Secure link · {l.get('access_count', 0)}/{l.get('max_access', 0)} accesses", "actor": l.get("created_by")})
    for lic in await db.product_licenses.find({"product_id": product_id}).sort("created_at", -1).to_list(200):
        events.append({"type": "license_grant", "at": lic.get("created_at"),
                       "detail": f"{lic.get('license_type')} → {lic.get('customer_id')}", "actor": lic.get("granted_by")})
    for j in await db.distribution_jobs.find({"product_id": product_id}).sort("created_at", -1).to_list(200):
        events.append({"type": "publication", "at": j.get("updated_at") or j.get("created_at"),
                       "detail": f"{j.get('connector_name')} · {j.get('status')}", "actor": j.get("created_by")})
    events.sort(key=lambda e: e.get("at") or "", reverse=True)
    return {"product_code": product_code, "events": events, "total": len(events)}


def config():
    return {
        "protection_layers": PROTECTION_LAYERS,
        "security_levels": SECURITY_LEVELS,
        "distribution_channels": DISTRIBUTION_CHANNELS,
        "distribution_permissions": DISTRIBUTION_PERMISSIONS,
        "platform_capabilities": PLATFORM_CAPABILITIES,
        "all_protections": ALL_PROTECTIONS,
        "factory_rule": FACTORY_RULE,
        "modules": [
            {"id": "MO-015", "name": "Content Protection & Rights Management™"},
            {"id": "MO-016", "name": "Trust & Authenticity Registry™"},
            {"id": "MO-017", "name": "Platform Capability Awareness™"},
        ],
    }
