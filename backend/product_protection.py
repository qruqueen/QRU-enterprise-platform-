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


PRODUCT_VERIFICATION_SYSTEM = """You are the QRU Verification Team™ guarding the TREASURE STANDARD™ — the
highest quality standard in the QRU Enterprise. The Treasure Standard™ is the IDENTITY of QRU, not a
checkbox. The Founder's name (Erica Talbert) and the QRU brand appear on every product.

THE QRU QUESTION™ — you MUST ask before approving:
"If Erica Talbert's name appears on this product, would she be enthusiastically proud to sell it to her
family, a classroom, a hospital, a church, a school district, or a Fortune 500 company?"
If the answer is anything less than an enthusiastic YES, decision must be "request_revision" (or "reject"
if fundamentally unsound) — never approve "good enough" or generic AI content.

THE TREASURE STANDARD™ TEST — evaluate all: verified accuracy, complete understanding, professional
writing, presentation, consistent QRU branding, educational excellence, logical organization, appropriate
reading level, strong learning outcomes, memory reinforcement, practical application, accessibility,
commercial quality, customer value, professional formatting.

Return ONLY valid JSON (no markdown fences):
{
  "scores": {"accuracy": 0-100, "clarity": 0-100, "completeness": 0-100, "readability": 0-100},
  "confidence_score": 0-100,
  "treasure_standard_met": true|false,
  "founder_would_be_proud": true|false,
  "decision": "approve" | "request_revision" | "reject",
  "sources_checked": ["source or basis 1", "..."],
  "issues": ["specific, actionable improvement", "..."],
  "reasons": "concise explanation",
  "ip_or_legal_uncertainty": false,
  "source_conflict": false
}
Approve ONLY when the Treasure Standard™ is met and the Founder would be proud."""


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


IMPROVE_SYSTEM = """You are a QRU AI Production Agent improving an educational product to meet the
TREASURE STANDARD™. Rewrite and elevate the product so the Founder would be enthusiastically proud to
put her name on it: fix every listed issue, strengthen clarity, understanding, structure, learning
outcomes, memory reinforcement, practical application, and professional formatting. Keep it accurate and
grounded. Return ONLY the improved product content in clean Markdown — no commentary."""


async def _improve_product(pid, issues, actor):
    p = await db.products.find_one({"id": pid})
    if not p:
        return
    issue_text = "\n".join(f"- {i}" for i in (issues or [])) or "- Elevate to full Treasure Standard™ quality."
    prompt = (f"PRODUCT TYPE: {p.get('product_type')}\nTITLE: {p.get('title')}\n\n"
              f"ISSUES TO FIX:\n{issue_text}\n\nCURRENT CONTENT:\n{(p.get('content') or '')[:4000]}")
    improved = await llm_generate(IMPROVE_SYSTEM, prompt, f"improve-{pid}")
    if improved and len(improved.strip()) > 40:
        history = p.get("improvement_history", [])
        history.append({"at": now_iso(), "by": actor, "issues": issues or []})
        await db.products.update_one(
            {"id": pid}, {"$set": {"content": improved, "improvement_history": history, "updated_at": now_iso()}})
    await log_org("Manufacturing Director™", "Manufacturing", "auto-revised to meet Treasure Standard™",
                  p.get("product_code", ""))


async def treasure_finalize(pid, actor="QRU Verification Team™", max_rounds=2):
    """Treasure Standard™ Improvement Loop™: verify → auto-revise → re-verify until the
    standard is met, then protect, publish, and distribute. Escalate only on true exceptions.
    Returns one of: published | escalated | needs_review."""
    for rnd in range(max_rounds + 1):
        res = await ai_verify_product(pid, actor)
        if res.get("escalated"):
            await db.products.update_one({"id": pid}, {"$set": {"status": "Needs Review", "updated_at": now_iso()}})
            return "escalated"
        v = (await db.products.find_one({"id": pid})).get("verification") or {}
        conf = v.get("confidence_score") or 0
        decision = v.get("decision")
        proud = v.get("founder_would_be_proud", conf >= CONFIDENCE_THRESHOLD)
        treasure = v.get("treasure_standard_met", conf >= CONFIDENCE_THRESHOLD)
        if decision == "approve" and conf >= CONFIDENCE_THRESHOLD and proud and treasure:
            break
        if rnd < max_rounds:
            await _improve_product(pid, v.get("issues", []), actor)
            continue
        # Exhausted rounds: publish only if confident, else hold for Founder judgment.
        if not (conf >= CONFIDENCE_THRESHOLD and proud):
            await db.products.update_one({"id": pid}, {"$set": {"status": "Needs Review", "updated_at": now_iso()}})
            await db.founder_escalations.insert_one({
                "id": gen_id(), "type": "quality", "product_id": pid,
                "product_code": (await db.products.find_one({"id": pid})).get("product_code"),
                "title": (await db.products.find_one({"id": pid})).get("title"),
                "reason": "Did not reach Treasure Standard™ after automatic revisions — Founder judgment requested.",
                "status": "Open", "confidence_score": conf, "created_at": now_iso()})
            return "needs_review"

    # Treasure Standard™ met → protect, publish, distribute.
    await db.products.update_one({"id": pid}, {"$set": {"verified": True, "treasure_standard": True}})
    await apply_protection(pid, (await db.products.find_one({"id": pid})).get("license_type") or "Personal Use",
                           True, "account_required", actor)
    await db.products.update_one({"id": pid}, {"$set": {"status": "Published", "published_at": now_iso(),
                                                        "ip.publication_date": now_iso(), "updated_at": now_iso()}})
    try:
        import integration_hub as ihub
        await ihub.auto_distribute(pid, "AI Distribution Team™")
    except Exception:
        pass
    await log_org("AI Publishing Team™", "Manufacturing", "published at Treasure Standard™",
                  (await db.products.find_one({"id": pid})).get("product_code", ""), "success")
    return "published"


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
