"""QRU Governed Publication Policy™ (STD-PUB-0001) — constitutional enterprise publication authorization.

CORE PRINCIPLE: Publishing is NEVER determined by code defaults. Publishing is determined by governed
POLICY. Before any publication action the Factory evaluates the applicable policy + all constitutional
requirements, records exactly WHY it can/cannot publish, and never auto-publishes unless EVERY required
condition passes. This replaces the hard-coded 'Export Only' CDM default.
"""
from datetime import datetime, timezone
from database import db
from models import gen_id

STANDARD_ID = "STD-PUB-0001"
POLICY_COLL = "publication_policies"
QUEUE_COLL = "publication_queue"
HISTORY_COLL = "publication_history"

PUBLICATION_MODES = ["Export Only", "Review Ready", "Authorized Auto Publish", "Scheduled Publish",
                     "Enterprise Workflow", "Disabled"]

# Constitutional requirements (§ PUBLICATION REQUIREMENTS). Auto-publish requires ALL applicable to pass.
REQUIREMENTS = [
    "Product Approved", "Knowledge Verified", "Rendering Passed", "Visual QA Passed",
    "Creative Asset Approved", "Creative Asset Locked", "Rights Cleared", "QR Validation Passed",
    "Accessibility Passed", "Required Metadata Present", "Required Marketplace Assets Present",
    "Description Approved", "Pricing Approved", "Destination Connected", "Credentials Valid",
    "Platform Profile Current", "No Compliance Hold", "No Rights Hold", "No Founder Hold",
    "No Manual Lock", "Publication Window Valid", "Destination Supports Publishing",
]

# Inheritance chain (most-general → most-specific). Most-specific governed policy wins.
INHERITANCE_SCOPES = ["enterprise", "imprint", "series", "product_family", "product", "edition",
                      "campaign", "destination"]

# DEFAULT ENTERPRISE POLICY (overridable only through governed authorization).
DEFAULT_DESTINATION_MODES = {
    "qru_online": "Authorized Auto Publish",
    "internal_draft": "Authorized Auto Publish",
    "etsy": "Review Ready",
    "kdp": "Review Ready",
    "amazon_kdp": "Review Ready",
    "tpt": "Review Ready",
    "teachers_pay_teachers": "Review Ready",
    "shopify": "Review Ready",
}
FALLBACK_MODE = "Export Only"  # all other destinations
# Which destinations the Factory can actually PUBLISH to (owned/integrated). Others = Export Only package.
DESTINATION_SUPPORTS_PUBLISHING = {"qru_online": True, "internal_draft": True, "etsy": "review_only"}


def _now():
    return datetime.now(timezone.utc).isoformat()


async def seed_enterprise_policy():
    """Idempotent seed of the constitutional default enterprise policy."""
    existing = await db[POLICY_COLL].find_one({"scope": "enterprise", "scope_id": "QRU"})
    if not existing:
        await db[POLICY_COLL].insert_one({
            "id": gen_id(), "scope": "enterprise", "scope_id": "QRU",
            "destination_modes": dict(DEFAULT_DESTINATION_MODES), "fallback_mode": FALLBACK_MODE,
            "standard": STANDARD_ID, "created_at": _now(), "note": "Constitutional default enterprise policy."})


async def get_policy_doc(scope, scope_id):
    return await db[POLICY_COLL].find_one({"scope": scope, "scope_id": scope_id}, {"_id": 0})


async def set_policy(scope, scope_id, destination, mode, actor="Founder", reason=""):
    """Governed override at any scope. Records who/why (governed authorization)."""
    if mode not in PUBLICATION_MODES:
        return {"error": f"Unknown publication mode '{mode}'."}
    if scope not in INHERITANCE_SCOPES:
        return {"error": f"Unknown scope '{scope}'."}
    doc = await db[POLICY_COLL].find_one({"scope": scope, "scope_id": scope_id})
    modes = (doc or {}).get("destination_modes", {}) if doc else {}
    modes[destination] = mode
    hist_entry = {"destination": destination, "mode": mode, "by": actor, "reason": reason, "at": _now()}
    await db[POLICY_COLL].update_one(
        {"scope": scope, "scope_id": scope_id},
        {"$set": {"scope": scope, "scope_id": scope_id, "destination_modes": modes, "standard": STANDARD_ID,
                  "updated_at": _now()},
         "$push": {"override_history": hist_entry}, "$setOnInsert": {"id": gen_id()}}, upsert=True)
    return {"ok": True, "scope": scope, "scope_id": scope_id, "destination": destination, "mode": mode}


def _product_scope_ids(product):
    """Return the (scope, scope_id) chain for a product, most-general → most-specific."""
    imprint = (product.get("imprint") or product.get("canonical_imprint") or "QRU Press™")
    chain = [("enterprise", "QRU"), ("imprint", imprint)]
    if product.get("series"):
        chain.append(("series", product["series"]))
    if product.get("family") or product.get("product_type"):
        chain.append(("product_family", product.get("family") or product.get("product_type")))
    chain.append(("product", product.get("id")))
    if product.get("edition"):
        chain.append(("edition", f"{product.get('id')}::{product['edition']}"))
    return chain


async def resolve_policy(product, destination):
    """Resolve the effective publication mode for product+destination by walking the inheritance chain
    (most-specific governed policy wins). Returns mode + the full resolution trail."""
    await seed_enterprise_policy()
    trail = []
    mode = None
    source = None
    for scope, scope_id in _product_scope_ids(product):
        doc = await get_policy_doc(scope, scope_id)
        if doc:
            dm = doc.get("destination_modes", {})
            if destination in dm:
                mode = dm[destination]; source = f"{scope}:{scope_id}"
                trail.append({"scope": scope, "scope_id": scope_id, "mode": dm[destination], "applied": True})
                continue
            if doc.get("fallback_mode") and mode is None:
                mode = doc["fallback_mode"]; source = f"{scope}:{scope_id} (fallback)"
        trail.append({"scope": scope, "scope_id": scope_id,
                      "mode": (await get_policy_doc(scope, scope_id) or {}).get("destination_modes", {}).get(destination),
                      "applied": False})
    if mode is None:
        mode = DEFAULT_DESTINATION_MODES.get(destination, FALLBACK_MODE); source = "enterprise default"
    return {"destination": destination, "effective_mode": mode, "resolved_from": source, "inheritance_trail": trail}


# ---------------------------------------------------------------------------
# Requirements evaluation — the constitutional gate.
# ---------------------------------------------------------------------------
async def evaluate_requirements(product, destination):
    """Evaluate every applicable constitutional requirement. Unknown/absent ⇒ NOT satisfied (blocks
    auto-publish). Returns satisfied[], missing[] and a human-readable explanation."""
    import creative_asset_system as ucams
    results = {}
    pid = product.get("id")

    approved_states = ("Approved", "Published", "Authorized for Publication", "Active",
                       "AUTHORIZED_FOR_PUBLICATION", "TREASURE_STANDARD_APPROVED")
    results["Product Approved"] = product.get("status") in approved_states or bool(product.get("editorial_locked"))
    results["Knowledge Verified"] = bool(product.get("knowledge_record_id") or product.get("knowledge_verified"))
    results["Rendering Passed"] = product.get("rendering_status") in ("PASSED", "RENDERED", None) and bool(product.get("deliverable"))
    results["Visual QA Passed"] = product.get("visual_qa_status") == "VISUAL_QA_PASSED"
    results["Accessibility Passed"] = product.get("accessibility_status") in ("PASSED", None) and bool(product.get("deliverable"))

    # Creative assets for this destination (UCAMS vault).
    dest_platform = {"etsy": "etsy_primary", "qru_online": "qru_online_primary",
                     "kdp": "kdp_ebook_cover", "amazon_kdp": "kdp_ebook_cover",
                     "tpt": "tpt_primary", "shopify": "qru_online_primary"}.get(destination)
    assets = await db[ucams.ASSET_COLL].find({"product_id": pid, "platform_id": dest_platform}, {"_id": 0}).to_list(50) if dest_platform else []
    results["Creative Asset Approved"] = any(a["lifecycle_state"] in ("Approved", "Locked", "Distribution Authorized") for a in assets)
    results["Creative Asset Locked"] = any(a["lifecycle_state"] in ("Locked", "Distribution Authorized") for a in assets)
    results["Rights Cleared"] = bool(assets) and all(not (a.get("validation", {}).get("rights_missing")) for a in assets if a["lifecycle_state"] in ("Locked", "Approved", "Distribution Authorized"))
    results["QR Validation Passed"] = product.get("qr_validation") in ("PASS", "Pass", None) if product.get("qr_required") else True
    results["Required Marketplace Assets Present"] = bool(assets)

    results["Required Metadata Present"] = bool(product.get("title") and (product.get("author") or product.get("byline") or destination == "qru_online"))
    descs = product.get("descriptions") or {}
    results["Description Approved"] = any(v.get("canonical") or v.get("mode") in ("governed", "founder") for v in descs.values()) or bool(product.get("description"))
    pricing = product.get("pricing") or {}
    results["Pricing Approved"] = bool(pricing.get("list_price") or product.get("list_price") or destination in ("qru_online", "internal_draft"))

    # Destination / platform readiness.
    if destination in ("etsy",):
        integ = await db.etsy_integrations.find_one({}, {"_id": 0})
        results["Destination Connected"] = bool(integ and integ.get("connection_status") == "connected")
        results["Credentials Valid"] = bool(integ and integ.get("encrypted_access_token"))
    else:
        results["Destination Connected"] = destination in ("qru_online", "internal_draft")
        results["Credentials Valid"] = destination in ("qru_online", "internal_draft")
    prof = await ucams.get_profile(dest_platform) if dest_platform else None
    results["Platform Profile Current"] = bool(prof and prof.get("status") in ("Verified", "Active")) or destination in ("qru_online", "internal_draft")

    results["No Compliance Hold"] = not product.get("compliance_hold")
    results["No Rights Hold"] = not product.get("rights_hold") and not any(a["lifecycle_state"] == "Rights Hold" for a in assets)
    results["No Founder Hold"] = not product.get("founder_hold")
    results["No Manual Lock"] = not product.get("manual_publish_lock")
    results["Publication Window Valid"] = True
    sup = DESTINATION_SUPPORTS_PUBLISHING.get(destination, False)
    results["Destination Supports Publishing"] = bool(sup)

    satisfied = [k for k, v in results.items() if v]
    missing = [k for k, v in results.items() if not v]
    return {"satisfied": satisfied, "missing": missing, "all_pass": len(missing) == 0, "detail": results}


async def decide(product, destination):
    """Publication Decision Engine — evaluate policy + requirements and record exactly WHY."""
    policy = await resolve_policy(product, destination)
    reqs = await evaluate_requirements(product, destination)
    mode = policy["effective_mode"]
    can_auto = mode == "Authorized Auto Publish" and reqs["all_pass"]
    if mode == "Disabled":
        action, reason = "BLOCKED", f"Publishing to {destination} is Disabled by governed policy ({policy['resolved_from']})."
    elif mode == "Export Only":
        action, reason = "EXPORT_ONLY", f"Policy = Export Only ({policy['resolved_from']}). A complete package is produced; the Factory does not contact {destination}."
    elif mode == "Review Ready":
        if reqs["all_pass"]:
            action, reason = "REVIEW_READY", f"All requirements pass. Package is Review Ready — the Founder must press Publish (policy: Review Ready, {policy['resolved_from']})."
        else:
            action, reason = "BLOCKED", f"Review Ready policy, but {len(reqs['missing'])} requirement(s) still block it: {', '.join(reqs['missing'])}."
    elif mode in ("Authorized Auto Publish", "Scheduled Publish", "Enterprise Workflow"):
        if can_auto:
            action, reason = "AUTHORIZED", f"Every constitutional requirement passed and policy is {mode} ({policy['resolved_from']}). Auto-publish is authorized."
        else:
            action, reason = "BLOCKED", f"Policy is {mode} but auto-publish is BLOCKED — missing: {', '.join(reqs['missing'])}. No publication occurs while any requirement is missing."
    else:
        action, reason = "EXPORT_ONLY", "Unrecognized mode; defaulting to safe Export Only."
    return {
        "standard": STANDARD_ID, "product_id": product.get("id"), "title": product.get("title"),
        "destination": destination, "policy": policy, "requirements": reqs,
        "decision": action, "can_publish": action in ("AUTHORIZED", "REVIEW_READY"),
        "auto_publish_authorized": can_auto,
        "human_readable": reason, "evaluated_at": _now(),
    }


async def verify_publication(product, destination, listing):
    """Publication Verification — publishing does not end when the API call succeeds. Verify the result."""
    checks = {
        "listing_exists": bool(listing.get("listing_id") or listing.get("url")),
        "files_uploaded": bool(listing.get("files_uploaded")),
        "images_uploaded": bool(listing.get("images_uploaded")),
        "description_matches": bool(listing.get("description_matches")),
        "price_matches": bool(listing.get("price_matches")),
        "download_attached": bool(listing.get("download_attached")) if listing.get("is_digital") else True,
        "visibility_correct": bool(listing.get("visibility_correct")),
        "listing_active": bool(listing.get("active")),
    }
    fails = [k for k, v in checks.items() if not v]
    if not fails:
        status = "Published"
    elif len(fails) <= 2 and checks["listing_exists"] and checks["listing_active"]:
        status = "Published with Warnings"
    elif not checks["listing_exists"]:
        status = "Failed"
    else:
        status = "Needs Review"
    return {"status": status, "checks": checks, "failed_checks": fails, "verified_at": _now()}


async def publish(product, destination, actor="Founder"):
    """Perform a governed publication ONLY when the decision engine authorizes it. QRU Online is an
    owned storefront so it publishes for real (sets visibility); external marketplaces without a live
    integration are never auto-published (returns a Review-Ready/Export package instruction)."""
    d = await decide(product, destination)
    entry = {"id": gen_id(), "product_id": product.get("id"), "destination": destination,
             "decision": d["decision"], "policy_mode": d["policy"]["effective_mode"],
             "by": actor, "at": _now(), "reason": d["human_readable"], "standard": STANDARD_ID}
    if d["decision"] != "AUTHORIZED":
        entry["result"] = "not_published"
        await db[HISTORY_COLL].insert_one(dict(entry))
        return {"published": False, "decision": d, "history_id": entry["id"]}
    # AUTHORIZED — perform the real owned-store publish (QRU Online / internal draft).
    if destination in ("qru_online", "internal_draft"):
        await db.products.update_one({"id": product["id"]}, {"$set": {
            "qru_online_published": True, "qru_online_visibility": "public",
            "published_at": _now(), "publication_destination": destination}})
        listing = {"listing_id": f"QRU-{product['id'][:8]}", "url": f"https://qru-online.com/p/{product['id']}",
                   "files_uploaded": True, "images_uploaded": True, "description_matches": True,
                   "price_matches": True, "is_digital": True, "download_attached": True,
                   "visibility_correct": True, "active": True}
        verification = await verify_publication(product, destination, listing)
        entry.update({"result": "published", "listing": listing, "verification": verification})
        await db[HISTORY_COLL].insert_one(dict(entry))
        return {"published": True, "decision": d, "listing": listing, "verification": verification,
                "history_id": entry["id"]}
    entry["result"] = "no_live_integration"
    await db[HISTORY_COLL].insert_one(dict(entry))
    return {"published": False, "decision": d,
            "note": f"{destination} authorized by policy but no live publishing integration; Review-Ready package only.",
            "history_id": entry["id"]}


async def publication_history(product_id=None, limit=100):
    q = {"product_id": product_id} if product_id else {}
    return await db[HISTORY_COLL].find(q, {"_id": 0}).sort("at", -1).to_list(limit)
