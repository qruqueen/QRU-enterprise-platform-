"""QRU Product Protection & Verification Agent™.

Balanced protection: secure enough to protect QRU's investment, simple enough for
buyers, teachers, families, and organizations.

- AI verification of products before publication (accuracy, sources, confidence).
- Intellectual property: copyright notice, watermark flag, version history, proof of creation.
- License system: Personal / Classroom / School-Org / Commercial with clear rules.
- Access security: account-gated access + expiring secure download links + access tracking.
- Founder escalation only for IP/legal uncertainty, source conflicts, launch approval, or license disputes.
"""
import os
import secrets
import logging
from datetime import datetime, timezone, timedelta

from database import db
from models import gen_id, now_iso
from ai_service import llm_generate, parse_json
from org_activity import log_org

logger = logging.getLogger("qru.protection")

CONFIDENCE_THRESHOLD = int(os.environ.get("VERIFICATION_CONFIDENCE_THRESHOLD", "80"))
COPYRIGHT_HOLDER = "QRU (Quest for Real Understanding)"


def copyright_notice():
    year = datetime.now(timezone.utc).year
    return f"© {year} {COPYRIGHT_HOLDER}. All rights reserved."


# ---------------- License catalog ----------------
LICENSE_TYPES = {
    "Personal Use": {
        "who": "A single individual learner", "max_users": 1,
        "printing": True, "sharing": False, "resale_prohibited": True, "expires": None,
        "summary": "For one person's personal learning. No sharing or resale.",
    },
    "Classroom/Teacher": {
        "who": "One teacher and their class", "max_users": 40,
        "printing": True, "sharing": True, "resale_prohibited": True, "expires": None,
        "summary": "One teacher may use and print for their own classroom of students.",
    },
    "School/Organization": {
        "who": "A school or organization", "max_users": 500,
        "printing": True, "sharing": True, "resale_prohibited": True, "expires": None,
        "summary": "Site-wide use across an institution. No resale or redistribution outside the organization.",
    },
    "Commercial": {
        "who": "A business using QRU products commercially", "max_users": 0,
        "printing": True, "sharing": True, "resale_prohibited": False, "expires": None,
        "summary": "Negotiated commercial use, including approved resale/white-label. Requires agreement.",
    },
}

DEFAULT_LICENSE_TERMS = (
    "This product is licensed, not sold. You may use it within the terms of your license. "
    "You may not redistribute, resell, or claim authorship of QRU content unless your license "
    "explicitly permits it. QRU verified knowledge and branding remain the property of "
    f"{COPYRIGHT_HOLDER}."
)


PRODUCT_VERIFICATION_SYSTEM = """You are the QRU Verification Team™ reviewing a finished educational
PRODUCT before it can be published or sold. Check accuracy, clarity, completeness, and QRU standards,
and whether the content is grounded in verified knowledge.

Return ONLY valid JSON (no markdown fences):
{
  "scores": {"accuracy": 0-100, "clarity": 0-100, "completeness": 0-100, "readability": 0-100},
  "confidence_score": 0-100,
  "decision": "approve" | "request_revision" | "reject",
  "sources_checked": ["source or basis 1", "..."],
  "issues": ["..."],
  "reasons": "concise explanation",
  "ip_or_legal_uncertainty": false,
  "source_conflict": false
}
Approve only if the product is accurate, clear, and meets QRU standards."""


async def ai_verify_product(pid: str, actor: str = "QRU Verification Team™") -> dict:
    p = await db.products.find_one({"id": pid})
    if not p:
        return {"error": "not found"}
    prompt = (f"Product: {p['title']}\nType: {p['product_type']}\nAudience: {p.get('audience','')}\n"
              f"Content:\n{(p.get('content') or '')[:2500]}")
    raw = await llm_generate(PRODUCT_VERIFICATION_SYSTEM, prompt, f"prod-verify-{pid}")
    review = parse_json(raw) or {"decision": "request_revision", "confidence_score": 0,
                                 "reasons": "Verifier response could not be parsed."}
    conf = review.get("confidence_score") or 0
    history = p.get("verification", {}).get("revision_history", []) if p.get("verification") else []
    history.append({"at": now_iso(), "decision": review.get("decision"),
                    "confidence_score": conf, "reasons": review.get("reasons", "")})
    verification = {
        "reviewer": "QRU Verification Team™", "decision": review.get("decision"),
        "confidence_score": conf, "scores": review.get("scores", {}),
        "sources_checked": review.get("sources_checked", []), "issues": review.get("issues", []),
        "reasons": review.get("reasons", ""), "approved_at": now_iso() if review.get("decision") == "approve" else None,
        "revision_history": history, "autonomous": True,
    }
    verified = review.get("decision") == "approve" and conf >= CONFIDENCE_THRESHOLD
    await db.products.update_one(
        {"id": pid},
        {"$set": {"verification": verification, "verified": verified, "updated_at": now_iso()}})

    escalate = review.get("ip_or_legal_uncertainty") or review.get("source_conflict")
    if escalate:
        reason = "IP/legal uncertainty" if review.get("ip_or_legal_uncertainty") else "Source conflict affecting verification"
        await db.founder_escalations.insert_one({
            "id": gen_id(), "type": "product", "product_id": pid, "product_code": p.get("product_code"),
            "title": p.get("title"), "reason": reason, "review": review, "status": "Open",
            "confidence_score": conf, "created_at": now_iso(),
        })
        await db.notifications.insert_one({
            "id": gen_id(), "level": "warning", "read": False, "created_at": now_iso(),
            "message": f"Founder review needed — product {p.get('product_code')}: {reason}",
        })
    await log_org("Kingdom Lion™", "Verification",
                  f"product {'verified' if verified else 'flagged'} ({conf}%)", p.get("product_code", ""),
                  "success" if verified else "warning")
    return {"verified": verified, "escalated": bool(escalate), "verification": verification}


async def apply_protection(pid: str, license_type: str, watermark: bool, access_control: str, actor: str):
    p = await db.products.find_one({"id": pid})
    if not p:
        return None
    lt = license_type if license_type in LICENSE_TYPES else "Personal Use"
    version = (p.get("ip", {}) or {}).get("version", 0) + 1
    protection = {
        "copyright_notice": copyright_notice(),
        "copyright_applied": True,
        "watermark": bool(watermark),
        "watermark_applied": bool(watermark),
        "access_control": access_control if access_control in ("account_required", "open") else "account_required",
        "secure_download": True,
    }
    ip = {
        "version": version,
        "created_date": p.get("created_at"),
        "proof_of_creation": p.get("created_at"),
        "source_record_id": p.get("knowledge_record_id"),
        "publication_date": p.get("ip", {}).get("publication_date") if p.get("ip") else None,
        "history": (p.get("ip", {}).get("history", []) if p.get("ip") else []) + [
            {"version": version, "action": "protection applied", "by": actor, "at": now_iso()}],
    }
    await db.products.update_one(
        {"id": pid},
        {"$set": {"license_type": lt, "license": LICENSE_TYPES[lt], "license_terms": DEFAULT_LICENSE_TERMS,
                  "protection": protection, "ip": ip, "protected": True, "updated_at": now_iso()}})
    await log_org("Brand Director™", "Brand", f"applied {lt} protection to", p.get("product_code", ""), "success")
    return await db.products.find_one({"id": pid})


async def create_secure_link(pid: str, customer_id: str, minutes: int, actor: str):
    p = await db.products.find_one({"id": pid})
    if not p:
        return None, "Product not found"
    if not p.get("verified"):
        return None, "Product must pass AI verification before secure download links can be issued."
    token = secrets.token_urlsafe(24)
    expires = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
    await db.product_access_links.insert_one({
        "id": gen_id(), "token": token, "product_id": pid, "customer_id": customer_id,
        "expires_at": expires, "max_access": 5, "access_count": 0, "revoked": False,
        "created_by": actor, "created_at": now_iso(),
    })
    return {"token": token, "expires_at": expires, "path": f"/api/protection/download/{token}"}, None


def dashboard_row(p):
    v = p.get("verification") or {}
    prot = p.get("protection") or {}
    risks = []
    if not p.get("verified"):
        risks.append("Unverified")
    if not prot.get("copyright_applied"):
        risks.append("No copyright notice")
    if p.get("status") == "Published" and not p.get("protected"):
        risks.append("Published without protection")
    return {
        "id": p["id"], "product_code": p.get("product_code"), "title": p.get("title"),
        "product_type": p.get("product_type"),
        "verification_status": v.get("decision") or ("Verified" if p.get("verified") else "Unverified"),
        "verified": bool(p.get("verified")), "confidence_score": v.get("confidence_score"),
        "license_type": p.get("license_type") or "None",
        "protected": bool(p.get("protected")),
        "copyright_applied": bool(prot.get("copyright_applied")),
        "watermark_applied": bool(prot.get("watermark_applied")),
        "access_control": prot.get("access_control", "open"),
        "publication_status": p.get("status"),
        "risk_flags": risks,
    }
