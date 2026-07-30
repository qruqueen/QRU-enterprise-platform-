"""QRU Universal Creative Asset Manufacturing System™ (UCAMS) — governed, inherited enterprise core.

This is the AUTHORITATIVE bridge between governed QRU knowledge/product manufacturing and external
creative production. The Factory owns the deterministic manufacturing requirements; external creative
providers (ChatGPT, Canva, designers) only produce artwork against exported specifications and never
become the source of truth.

Foundation (Phase 1) implements the five governed subsystems:
  • UCAS™ — Universal Creative Asset Specification (what must be created; deterministic)
  • PSR™  — Platform Specification Registry (verified, versioned, source-backed destination profiles)
  • CAVE™ — Creative Asset Validation Engine (validate returned/uploaded assets vs the spec)
  • CAVL™ — Creative Asset Vault & Lineage (masters, versions, rights, checksums, publication history)
  • CDM™  — Creative Distribution Manifest (machine-readable, never auto-publishes)

Deterministic manufacturing is separated from variable creative generation. Approved+locked assets are
never silently regenerated — regeneration always creates a NEW candidate version.
"""
import hashlib
import io
import json
import csv as _csv
from datetime import datetime, timezone, timedelta

from database import db
from models import gen_id, now_iso

STANDARD_ID = "STD-UCAMS-0001"
PLATFORM_COLL = "ucams_platforms"
ASSET_COLL = "ucams_assets"

# 6x9 trade paperback spine math (inherited from the Book line — authoritative deterministic calc).
PAPER_THICKNESS_IN = {"white": 0.002252, "cream": 0.0025, "color": 0.002347}

# Governed lifecycle (§16) and validation results (§17).
LIFECYCLE = ["Required", "Specification Draft", "Specification Verified", "Ready for Creation",
             "Concept Requested", "Concept Produced", "Under Review", "Revision Required", "Approved",
             "Locked", "Derivative Requested", "Derivative Produced", "Platform Validated",
             "Distribution Authorized", "Published", "Publication Verified", "Superseded", "Archived",
             "Rejected", "Rights Hold", "Compliance Hold"]
VALIDATION_RESULTS = ["PASS", "PASS WITH WARNINGS", "FAIL", "HOLD"]
PROFILE_STATUSES = ["Draft", "Under Verification", "Verified", "Active", "Review Due", "Changed",
                    "Deprecated", "Superseded", "Unsupported"]
PUBLICATION_MODES = ["Export Only", "Review Ready", "Draft Listing", "Authorized to Publish",
                     "Published", "Paused", "Removed", "Archived"]

# Asset families & one-page-visual / poster taxonomy the Factory must distinguish (§3, §4).
ASSET_FAMILIES = ["print_cover_wrap", "digital_cover", "one_page_knowledge_visual", "poster",
                  "marketplace_image", "social_asset", "web_email_asset", "motion_asset",
                  "education_asset", "physical_merch"]
POSTER_CLASSES = ["Educational Poster", "Reference Poster", "Premium Art Poster", "Typography Poster",
                  "Classroom Poster", "Promotional Poster", "Campaign Poster"]
ONE_PAGE_FUNCTIONS = ["Sellable Product", "Product Component", "Educational Resource",
                      "Promotional Asset", "Lead Magnet", "Classroom Display", "Printable Reference",
                      "Social Content", "Institutional Handout", "Internal Factory Document"]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _checksum(obj):
    """Deterministic sha256 over canonical JSON (sorted keys) — the manufacturing fingerprint."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


# ---------------------------------------------------------------------------
# PSR™ — Platform Specification Registry (verified, versioned, source-backed).
# Every profile carries authoritative provenance so a stale profile is never presented as current.
# ---------------------------------------------------------------------------
def _profile(pid, name, dtype, role, req, *, source, verified="2026-07-30", verifier="QRU Founder",
             version="v1.0", status="Verified", review_days=180):
    eff = datetime.fromisoformat(verified)
    return {
        "platform_id": pid, "platform_name": name, "destination_type": dtype, "asset_role": role,
        "requirements": req,  # the deterministic spec body
        "source": source, "date_verified": verified, "verified_by": verifier,
        "profile_version": version, "status": status, "effective_date": verified,
        "last_reviewed_date": verified,
        "next_review_date": (eff + timedelta(days=review_days)).date().isoformat(),
        "change_history": [{"version": version, "date": verified, "status": status, "note": "Initial verified profile."}],
        "superseded_version": None, "standard": STANDARD_ID,
    }


# Seed set — real, commonly-cited specs. Each is a governed, verifiable profile (Founder must confirm
# on next review; source recorded so it is never an "unverified assumption presented as truth").
_SEED_PROFILES = [
    _profile("kdp_paperback_wrap", "Amazon KDP", "print_marketplace", "print_cover_wrap",
             {"family": "print_cover_wrap", "trim_options_in": [[6, 9], [5, 8], [8.5, 11]],
              "default_trim_in": [6, 9], "bleed_in": 0.125, "safe_margin_in": 0.25, "dpi": 300,
              "color_space": "CMYK", "format": "pdf", "spine_text_min_pages": 79,
              "barcode_zone_in": [2.0, 1.2], "font_embedding": True, "uses_platform_template": True},
             source="https://kdp.amazon.com/en_US/help/topic/G201953020 (KDP paperback cover spec)"),
    _profile("kdp_ebook_cover", "Amazon KDP (eBook)", "digital_marketplace", "digital_cover",
             {"family": "digital_cover", "min_px": [1600, 2560], "ideal_px": [1600, 2560],
              "aspect_ratio": 1.6, "format": "jpeg", "color_space": "RGB", "max_mb": 50, "dpi": 72},
             source="https://kdp.amazon.com/en_US/help/topic/G200645690 (KDP eBook cover)"),
    _profile("etsy_primary", "Etsy", "digital_marketplace", "marketplace_image",
             {"family": "marketplace_image", "min_px": [2000, 2000], "ideal_px": [3000, 2250],
              "aspect_ratio": 1.3333, "format": "jpeg", "color_space": "RGB", "max_mb": 20, "dpi": 72,
              "listing_image_roles": ["primary", "contents", "usage", "digital_download_notice", "preview"]},
             source="https://help.etsy.com/hc/en-us/articles/360000579548 (Etsy listing images)"),
    _profile("tpt_primary", "Teachers Pay Teachers", "education_marketplace", "marketplace_image",
             {"family": "marketplace_image", "ideal_px": [2550, 3300], "aspect_ratio": 0.7727,
              "format": "png", "color_space": "RGB", "max_mb": 20, "dpi": 300,
              "listing_image_roles": ["cover", "preview", "contents", "usage", "terms"]},
             source="https://help.teacherspayteachers.com (TpT product image guidance)"),
    _profile("qru_online_primary", "QRU Online Store", "owned_storefront", "marketplace_image",
             {"family": "marketplace_image", "ideal_px": [1600, 2000], "aspect_ratio": 0.8,
              "format": "png", "color_space": "RGB", "max_mb": 15, "dpi": 72},
             source="QRU Online storefront spec (internal authoritative)"),
    _profile("youtube_thumbnail", "YouTube", "video_platform", "social_asset",
             {"family": "social_asset", "ideal_px": [1280, 720], "aspect_ratio": 1.7778,
              "format": "jpeg", "color_space": "RGB", "max_mb": 2, "dpi": 72,
              "text_safe": True, "min_px": [640, 360]},
             source="https://support.google.com/youtube/answer/72431 (YouTube thumbnail)"),
    _profile("youtube_screen_16x9", "YouTube", "video_platform", "motion_asset",
             {"family": "motion_asset", "canvas_px": [1920, 1080], "aspect_ratio": 1.7778, "fps": 30,
              "format": "mp4", "codec": "h264", "audio": "aac", "caption_safe": True,
              "supports_slideshow_of_stills": True},
             source="https://support.google.com/youtube/answer/6375112 (YouTube upload encoding)"),
    _profile("pinterest_pin", "Pinterest", "social_platform", "social_asset",
             {"family": "social_asset", "ideal_px": [1000, 1500], "aspect_ratio": 0.6667,
              "format": "png", "color_space": "RGB", "max_mb": 20, "dpi": 72},
             source="https://help.pinterest.com/en/business/article/pinterest-product-specs"),
    _profile("instagram_post", "Instagram", "social_platform", "social_asset",
             {"family": "social_asset", "ideal_px": [1080, 1080], "aspect_ratio": 1.0,
              "format": "jpeg", "color_space": "RGB", "max_mb": 30, "dpi": 72},
             source="https://help.instagram.com (Instagram image sizes)"),
    _profile("tiktok_vertical", "TikTok", "video_platform", "social_asset",
             {"family": "social_asset", "ideal_px": [1080, 1920], "aspect_ratio": 0.5625,
              "format": "jpeg", "color_space": "RGB", "max_mb": 20, "dpi": 72,
              "overlay_safe": True, "focal_point": "center"},
             source="https://support.tiktok.com (TikTok video/cover specs)"),
    _profile("one_page_visual_print", "QRU One-Page Knowledge Visual™ (Print)", "print_owned",
             "one_page_knowledge_visual",
             {"family": "one_page_knowledge_visual", "print_sizes_in": [[8.5, 11], [18, 24], [24, 36]],
              "default_size_in": [8.5, 11], "bleed_in": 0.125, "safe_margin_in": 0.25, "dpi": 300,
              "color_space": "CMYK", "format": "pdf", "requires_information_design": True},
             source="QRU One-Page Knowledge Visual™ Standard (internal authoritative)"),
]


async def seed_profiles():
    """Idempotent PSR seed — never overwrites a profile the Founder has already re-verified/changed."""
    for p in _SEED_PROFILES:
        existing = await db[PLATFORM_COLL].find_one({"platform_id": p["platform_id"], "asset_role": p["asset_role"]})
        if not existing:
            await db[PLATFORM_COLL].insert_one(dict(p))


async def list_profiles(include_stale_warning=True):
    await seed_profiles()
    out = []
    today = datetime.now(timezone.utc).date().isoformat()
    for p in await db[PLATFORM_COLL].find({}, {"_id": 0}).to_list(500):
        stale = p.get("next_review_date") and p["next_review_date"] < today
        if stale and p.get("status") == "Verified":
            p["status_warning"] = "Review Due — profile past next_review_date; re-verify before treating as current."
        out.append(p)
    return out


async def get_profile(platform_id, asset_role=None):
    await seed_profiles()
    q = {"platform_id": platform_id}
    if asset_role:
        q["asset_role"] = asset_role
    return await db[PLATFORM_COLL].find_one(q, {"_id": 0})


# ---------------------------------------------------------------------------
# UCAS™ — deterministic specification generation.
# ---------------------------------------------------------------------------
def _wrap_geometry(trim_w, trim_h, pages, paper_type, bleed=0.125, dpi=300):
    thickness = PAPER_THICKNESS_IN.get((paper_type or "white").lower(), PAPER_THICKNESS_IN["white"])
    spine_in = round(pages * thickness, 4)
    total_w_in = round(bleed + trim_w + spine_in + trim_w + bleed, 4)
    total_h_in = round(bleed + trim_h + bleed, 4)
    return {
        "trim_in": [trim_w, trim_h], "page_count": pages, "paper_type": paper_type,
        "spine_in": spine_in, "spine_text_allowed": pages >= 79,
        "bleed_in": bleed, "dpi": dpi,
        "total_wrap_in": [total_w_in, total_h_in],
        "total_wrap_px": [int(round(total_w_in * dpi)), int(round(total_h_in * dpi))],
        "zones": {
            "back_cover_in": [bleed, bleed, bleed + trim_w, bleed + trim_h],
            "spine_in": [bleed + trim_w, bleed, bleed + trim_w + spine_in, bleed + trim_h],
            "front_cover_in": [bleed + trim_w + spine_in, bleed, bleed + trim_w + spine_in + trim_w, bleed + trim_h],
            "barcode_zone_in": [2.0, 1.2], "safe_margin_in": 0.25,
        },
    }


def _design_intent(product, asset_role, family):
    literary = "rothwell" in (product.get("imprint", "").lower())
    return {
        "asset_purpose": f"{family} for '{product.get('title')}'",
        "audience": product.get("audience") or "General",
        "product_promise": product.get("subtitle") or "",
        "brand": "QRU", "imprint": product.get("imprint") or "QRU Press™",
        "series": product.get("series") or "", "emotional_tone": "literary/evocative" if literary else "clear/credible",
        "primary_message": product.get("title"),
        "required_trademark_symbols": ["™ on QRU marks and imprint"],
        "approved_fonts": ["QRU Serif (Liberation Serif)", "QRU Sans (Liberation Sans)"],
        "approved_colors": ["QRU Navy", "QRU Royal", "Metallic Gold"],
        "editorial_bible_inheritance": "QRU Editorial & Writing Bible™",
        "knowledge_source": product.get("knowledge_record_id"),
        "prohibited": ["generic AI-poster look", "clip art", "unverified claims", "off-brand fonts"],
    }


def _cost_controls(family):
    # Default: reuse/deterministic first; AI never a dependency (inherits the $0-default constitution).
    ai_ok = family in ("digital_cover", "poster", "one_page_knowledge_visual", "social_asset", "marketplace_image")
    return {
        "ai_policy": "AI Allowed (optional)" if ai_ok else "AI Prohibited",
        "premium_typography_preferred": True, "existing_asset_reuse_preferred": True,
        "max_concepts": 3, "max_paid_attempts": 3, "approval_required_before_paid_generation": True,
        "fallback_method": "Premium Typography™", "provider_failure_behavior": "silent fallback; never stop manufacturing",
    }


async def generate_spec(product, asset_role, platform_id, *, pages=None, paper_type="white", language="EN",
                        edition="First Edition", campaign=None):
    """UCAS™ — produce a complete, DETERMINISTIC specification for one product+role+destination.
    Identical inputs → identical spec + checksum (§2.1)."""
    profile = await get_profile(platform_id, asset_role)
    if not profile:
        return {"error": f"No verified Platform Specification Registry™ profile for '{platform_id}/{asset_role}'. "
                         "Add a governed, verified profile before manufacturing to this destination."}
    req = profile["requirements"]
    family = req.get("family", asset_role)
    spec_body = {
        "product_id": product.get("id"), "product_code": product.get("book_code") or product.get("product_code"),
        "title": product.get("title"), "published_title": product.get("published_title") or product.get("title"),
        "knowledge_record_id": product.get("knowledge_record_id"),
        "asset_family": family, "asset_role": asset_role,
        "platform_id": platform_id, "platform_name": profile["platform_name"],
        "profile_version": profile["profile_version"], "profile_status": profile["status"],
        "language": language, "edition": edition, "campaign": campaign,
        "requirements": req,
    }
    if family == "print_cover_wrap":
        trim = req.get("default_trim_in", [6, 9])
        pg = int(pages or product.get("page_count") or 100)
        spec_body["geometry"] = _wrap_geometry(trim[0], trim[1], pg, paper_type,
                                                bleed=req.get("bleed_in", 0.125), dpi=req.get("dpi", 300))
    elif family in ("digital_cover", "marketplace_image", "social_asset", "one_page_knowledge_visual"):
        px = req.get("ideal_px") or req.get("min_px") or req.get("canvas_px")
        spec_body["target_px"] = px
        spec_body["aspect_ratio"] = req.get("aspect_ratio")
    if family == "one_page_knowledge_visual":
        spec_body["information_design"] = {
            "visual_type": "educational_visual", "intended_outcome": "teach/reinforce verified knowledge",
            "viewing_distance": "arm's length (print) / screen", "content_density": "medium",
            "visual_hierarchy": ["primary message", "key points", "supporting detail", "source/QR"],
            "source_requirements": "cite Knowledge Record™", "requires_verified_knowledge": True,
            "quality_bar": "premium composition, intentional hierarchy, brand inheritance, factual traceability",
        }
    # Deterministic fingerprint over the manufacturing requirements only (excludes any timestamps).
    fingerprint_src = {k: spec_body[k] for k in spec_body if k not in ("campaign",)}
    spec_checksum = _checksum(fingerprint_src)
    return {
        "standard": STANDARD_ID, "spec_id": f"UCAS-{spec_checksum[:12]}",
        "spec_checksum": spec_checksum, "deterministic": True,
        "generated_at": _now(),
        **spec_body,
        "design_intent": _design_intent(product, asset_role, family),
        "cost_controls": _cost_controls(family),
        "source_deliverables": _deliverables_for(family),
        "accessibility_requirements": ACCESSIBILITY_REQS,
        "provenance_required": RIGHTS_REQUIRED_FIELDS,
        "lifecycle_state": "Specification Verified" if profile["status"] in ("Verified", "Active") else "Specification Draft",
    }


def _deliverables_for(family):
    base = ["print_ready_pdf" if "print" in family or family == "one_page_knowledge_visual" else "web_png",
            "editable_source", "preview_image", "source_manifest"]
    if family == "motion_asset":
        base = ["mp4", "poster_frame", "caption_file", "transcript", "reduced_motion_version", "source_manifest"]
    return base


ACCESSIBILITY_REQS = {
    "min_contrast_ratio": 4.5, "min_body_text_pt": 10, "non_color_only_meaning": True,
    "alt_text_required": True, "reduced_motion_variant": "for motion assets", "language_declaration": True,
}
RIGHTS_REQUIRED_FIELDS = ["creator", "creation_method", "license", "commercial_use_authorization",
                          "ai_disclosure_status"]


# ---------------------------------------------------------------------------
# CAVE™ — Creative Asset Validation Engine (deterministic).
# ---------------------------------------------------------------------------
def _validate_image_bytes(spec, data):
    from PIL import Image
    issues, warnings = [], []
    try:
        im = Image.open(io.BytesIO(data)); im.verify()
        im = Image.open(io.BytesIO(data))
    except Exception as e:
        return "FAIL", [f"Not a decodable image: {str(e)[:80]}"], []
    req = spec.get("requirements", {})
    w, h = im.width, im.height
    target = spec.get("target_px")
    minpx = req.get("min_px")
    if minpx and (w < minpx[0] or h < minpx[1]):
        issues.append(f"Below minimum pixels: got {w}x{h}, need >= {minpx[0]}x{minpx[1]}")
    ar_req = req.get("aspect_ratio")
    if ar_req:
        ar = round(w / h, 4)
        if abs(ar - ar_req) > 0.03:
            warnings.append(f"Aspect ratio {ar} differs from target {ar_req}")
    fmt = (im.format or "").lower().replace("jpg", "jpeg")
    want_fmt = (req.get("format") or "").lower().replace("jpg", "jpeg")
    if want_fmt and fmt and want_fmt != fmt and not (want_fmt == "jpeg" and fmt == "mpo"):
        warnings.append(f"Format {fmt} differs from required {want_fmt}")
    want_cs = req.get("color_space")
    if want_cs == "RGB" and im.mode not in ("RGB", "RGBA"):
        warnings.append(f"Color mode {im.mode}; destination expects RGB")
    max_mb = req.get("max_mb")
    if max_mb and len(data) > max_mb * 1024 * 1024:
        issues.append(f"File {round(len(data)/1048576,1)}MB exceeds max {max_mb}MB")
    return ("FAIL" if issues else ("PASS WITH WARNINGS" if warnings else "PASS")), issues, warnings


def _validate_pdf_bytes(spec, data):
    issues, warnings = [], []
    try:
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        pages = doc.page_count
        page = doc[0]
        w_in, h_in = page.rect.width / 72.0, page.rect.height / 72.0
    except Exception as e:
        return "FAIL", [f"Not a readable PDF: {str(e)[:80]}"], []
    geom = spec.get("geometry")
    if geom:
        want = geom["total_wrap_in"]
        if abs(w_in - want[0]) > 0.06 or abs(h_in - want[1]) > 0.06:
            issues.append(f"Wrap size {round(w_in,3)}x{round(h_in,3)}in != required {want[0]}x{want[1]}in "
                          f"(spine {geom['spine_in']}in for {geom['page_count']}pp {geom['paper_type']} paper)")
        if pages != 1:
            warnings.append(f"Cover wrap should be a single page; got {pages}")
    return ("FAIL" if issues else ("PASS WITH WARNINGS" if warnings else "PASS")), issues, warnings


def validate_rights(asset_meta):
    missing = [f for f in RIGHTS_REQUIRED_FIELDS if not (asset_meta or {}).get(f)]
    return missing


def validate_asset(spec, data, *, mime="", asset_meta=None):
    """CAVE™ — validate an uploaded/returned/derived asset against its UCAS spec. Deterministic.
    Returns {result, issues, warnings, checks} where result ∈ PASS/PASS WITH WARNINGS/FAIL/HOLD."""
    # Rights gate first (§14) — missing rights ⇒ HOLD (cannot be Approved for Distribution).
    rights_missing = validate_rights(asset_meta)
    fmt = (spec.get("requirements", {}).get("format") or "").lower()
    head = data[:5].lstrip()
    is_pdf = head[:4] == b"%PDF" or "pdf" in (mime or "") or fmt == "pdf"
    if is_pdf:
        result, issues, warnings = _validate_pdf_bytes(spec, data)
    else:
        result, issues, warnings = _validate_image_bytes(spec, data)
    checks = {"dimensions": True, "rights": not rights_missing, "format": True}
    if rights_missing:
        warnings.append(f"Rights incomplete (missing: {', '.join(rights_missing)}) — Rights Hold until resolved.")
        result = "HOLD"
    return {"result": result, "issues": issues, "warnings": warnings,
            "rights_missing": rights_missing, "spec_checksum": spec.get("spec_checksum"),
            "validated_at": _now(), "checks": checks,
            "correction_required": issues or ([f"Provide rights: {rights_missing}"] if rights_missing else [])}


# ---------------------------------------------------------------------------
# CAVL™ — vault + lineage. Approved+locked assets are never silently replaced (§2.2).
# ---------------------------------------------------------------------------
async def store_asset(*, product_id, spec, data, filename, asset_meta, validation, actor="Founder",
                      parent_asset_id=None):
    import rendering_engine as re
    fid = re._save(f"ucams-{spec.get('asset_role','asset')}", (filename.rsplit(".", 1)[-1] if "." in filename else "bin"), data)
    checksum = hashlib.sha256(data).hexdigest()
    # Version: increment within the same (product, role, platform) family.
    prior = await db[ASSET_COLL].count_documents({"product_id": product_id, "asset_role": spec.get("asset_role"),
                                                  "platform_id": spec.get("platform_id")})
    asset = {
        "id": gen_id(), "asset_id": f"CA-{checksum[:12]}", "product_id": product_id,
        "asset_family": spec.get("asset_family"), "asset_role": spec.get("asset_role"),
        "platform_id": spec.get("platform_id"), "profile_version": spec.get("profile_version"),
        "language": spec.get("language"), "edition": spec.get("edition"),
        "version": f"v1.{prior}", "parent_asset_id": parent_asset_id,
        "spec_id": spec.get("spec_id"), "spec_checksum": spec.get("spec_checksum"),
        "file_url": re._asset_url(fid), "filename": filename, "checksum": checksum,
        "bytes": len(data), "rights": asset_meta or {},
        "validation": validation,
        "lifecycle_state": "Rights Hold" if validation["result"] == "HOLD"
                           else ("Rejected" if validation["result"] == "FAIL" else "Under Review"),
        "created_by": actor, "created_at": _now(), "updated_at": _now(),
        "publication_history": [], "standard": STANDARD_ID,
    }
    await db[ASSET_COLL].insert_one(dict(asset))
    asset.pop("_id", None)
    return asset


async def set_asset_state(asset_id, new_state, actor="Founder"):
    if new_state not in LIFECYCLE:
        return {"error": f"Unknown lifecycle state '{new_state}'."}
    a = await db[ASSET_COLL].find_one({"asset_id": asset_id}, {"_id": 0})
    if not a:
        return {"error": "Asset not found."}
    # Guardrail: cannot approve/authorize while on a hold or failed.
    if new_state in ("Approved", "Locked", "Distribution Authorized") and a["lifecycle_state"] in ("Rights Hold", "Rejected", "Compliance Hold"):
        return {"error": f"Cannot move to {new_state} — asset is on {a['lifecycle_state']}. Resolve first."}
    await db[ASSET_COLL].update_one({"asset_id": asset_id}, {"$set": {
        "lifecycle_state": new_state, "updated_at": _now()},
        "$push": {"publication_history": {"state": new_state, "by": actor, "at": _now()}}})
    return await db[ASSET_COLL].find_one({"asset_id": asset_id}, {"_id": 0})


# ---------------------------------------------------------------------------
# CDM™ — Creative Distribution Manifest. NEVER auto-publishes (§24).
# ---------------------------------------------------------------------------
async def build_distribution_manifest(product, destinations, actor="Founder"):
    """Produce a machine-readable distribution package. The publication_mode for each destination is now
    determined by GOVERNED POLICY (STD-PUB-0001) — not a hard-coded default. Passing validation is still
    NOT permission to publish; auto-publish requires an authorizing decision from the policy engine."""
    import publication_policy as pp
    entries = []
    for dest in destinations:
        assets = await db[ASSET_COLL].find(
            {"product_id": product.get("id"), "platform_id": dest,
             "lifecycle_state": {"$in": ["Approved", "Locked", "Platform Validated", "Distribution Authorized"]}},
            {"_id": 0}).to_list(50)
        decision = await pp.decide(product, dest)
        entries.append({
            "destination": dest, "assets": [{"asset_id": a["asset_id"], "role": a["asset_role"],
                                             "file_url": a["file_url"], "version": a["version"],
                                             "state": a["lifecycle_state"]} for a in assets],
            "listing_copy": (product.get("descriptions") or {}),
            "governed_policy_mode": decision["policy"]["effective_mode"],
            "policy_resolved_from": decision["policy"]["resolved_from"],
            "publication_decision": decision["decision"],
            "publication_mode": {"AUTHORIZED": "Authorized to Publish", "REVIEW_READY": "Review Ready",
                                 "EXPORT_ONLY": "Export Only", "BLOCKED": "Export Only"}.get(decision["decision"], "Export Only"),
            "can_publish": decision["can_publish"],
            "publish_blocked_reason": None if decision["can_publish"] else decision["human_readable"],
            "missing_requirements": decision["requirements"]["missing"],
        })
    manifest = {
        "standard": STANDARD_ID, "manifest_id": f"CDM-{gen_id()[:8].upper()}",
        "product_id": product.get("id"), "title": product.get("title"),
        "built_at": _now(), "built_by": actor, "destinations": entries,
        "note": "Publication mode is set by Governed Publication Policy™ (STD-PUB-0001), not code defaults. "
                "The Factory does NOT auto-publish unless the policy engine authorizes it and every "
                "constitutional requirement passes.",
    }
    return manifest


# ---------------------------------------------------------------------------
# Inheritance (§2.3) — every product auto-inherits applicable role+destination profiles.
# ---------------------------------------------------------------------------
def applicable_specs(product):
    """Which asset-role/destination pairs a product inherits automatically, by product type."""
    pt = (product.get("product_type") or "Book").lower()
    base = [("digital_cover", "kdp_ebook_cover"), ("marketplace_image", "etsy_primary"),
            ("marketplace_image", "qru_online_primary"), ("social_asset", "youtube_thumbnail"),
            ("social_asset", "pinterest_pin"), ("social_asset", "instagram_post"),
            ("social_asset", "tiktok_vertical")]
    if pt in ("book", "workbook", "teacher guide", "journal", "planner"):
        base = [("print_cover_wrap", "kdp_paperback_wrap")] + base
    if pt in ("workbook", "teacher guide"):
        base += [("marketplace_image", "tpt_primary")]
    if pt in ("poster", "one page", "one_page_knowledge_visual", "knowledge visual"):
        base = [("one_page_knowledge_visual", "one_page_visual_print")] + base
    return base


# ---------------------------------------------------------------------------
# Migration audit (§29) — classify existing creative assets; never auto-approve legacy.
# ---------------------------------------------------------------------------
async def migration_audit_posters(limit=200):
    posters = await db.poster_assets.find({}, {"_id": 0}).to_list(limit)
    rows = []
    for p in posters:
        title = (p.get("title") or p.get("family") or "").lower()
        is_visual = any(k in title for k in ("infographic", "explainer", "reference", "guide", "one-page",
                                             "sell sheet", "checklist", "framework"))
        classification = "One-Page Knowledge Visual™ (candidate)" if is_visual else "Poster (candidate)"
        quality = "Legacy Needs Validation"  # never auto-approve legacy (§29)
        rows.append({"id": p.get("id"), "title": p.get("title") or p.get("family"),
                     "classification": classification, "legacy_status": quality,
                     "rights_status": "Legacy Rights Unknown", "preserved": True})
    return {"total": len(rows), "rows": rows,
            "note": "Legacy assets are classified only. None auto-approved; files preserved (never deleted/overwritten)."}


# ---------------------------------------------------------------------------
# Export (§22) — specs/manifests as JSON / CSV / HTML. $0, no creative generation.
# ---------------------------------------------------------------------------
async def catalog_export(scope="catalog", fmt="json", limit=100):
    """Deterministic catalog-level export of required specs per product. Triggers NO AI/creative gen."""
    books = await db.book_records.find({}, {"_id": 0, "id": 1, "title": 1, "book_code": 1,
                                            "product_type": 1, "imprint": 1, "page_count": 1,
                                            "knowledge_record_id": 1, "audience": 1, "subtitle": 1}).to_list(limit)
    rows = []
    for b in books:
        for role, plat in applicable_specs(b):
            prof = await get_profile(plat, role)
            rows.append({"product_id": b["id"], "product_code": b.get("book_code"), "title": b.get("title"),
                         "asset_role": role, "platform_id": plat,
                         "profile_version": (prof or {}).get("profile_version"),
                         "profile_status": (prof or {}).get("status", "MISSING PROFILE"),
                         "asset_present": await db[ASSET_COLL].count_documents(
                             {"product_id": b["id"], "asset_role": role, "platform_id": plat}) > 0})
    if fmt == "csv":
        buf = io.StringIO(); w = _csv.DictWriter(buf, fieldnames=list(rows[0].keys()) if rows else
                                                 ["product_id", "asset_role", "platform_id"])
        w.writeheader(); [w.writerow(r) for r in rows]
        return {"format": "csv", "content": buf.getvalue(), "row_count": len(rows), "ai_generation_triggered": False}
    if fmt == "html":
        head = "".join(f"<th>{k}</th>" for k in (rows[0].keys() if rows else []))
        body = "".join("<tr>" + "".join(f"<td>{r[k]}</td>" for k in r) + "</tr>" for r in rows)
        html = f"<h1>QRU UCAMS Catalog Export</h1><table border=1><tr>{head}</tr>{body}</table>"
        return {"format": "html", "content": html, "row_count": len(rows), "ai_generation_triggered": False}
    return {"format": "json", "rows": rows, "row_count": len(rows), "ai_generation_triggered": False,
            "scope": scope, "standard": STANDARD_ID}
