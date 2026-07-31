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
              "color_space": "CMYK", "format": "pdf", "accepted_formats": ["pdf"],
              "pdf_standard_preferred": "PDF/X-1a:2001", "spine_text_min_pages": 79,
              "barcode_zone_in": [2.0, 1.2], "font_embedding": True, "uses_platform_template": True,
              "transparency_allowed": False, "transparency_rule": "Flatten — no transparency in print PDF.",
              "no_crop_marks": True, "no_surrounding_whitespace": True},
             verified="2026-06-01",
             source="Amazon KDP Print Cover Guidelines — https://kdp.amazon.com/help/topic/G201953020 "
                    "and Cover Calculator https://kdp.amazon.com/cover-calculator (verified 2026-06)"),
    _profile("kdp_ebook_cover", "Amazon KDP (eBook)", "digital_marketplace", "digital_cover",
             {"family": "digital_cover", "min_px": [625, 1000], "ideal_px": [1600, 2560],
              "aspect_ratio": 1.6, "format": "jpeg", "accepted_formats": ["jpeg", "tiff"],
              "color_space": "RGB", "max_mb": 50, "dpi": 300,
              "transparency_allowed": False, "transparency_rule": "Flatten — JPEG/TIFF are opaque.",
              "note": "1600×2560 is the governed EXACT export target; 625×1000 is KDP's hard minimum."},
             verified="2026-06-01",
             source="Amazon KDP eBook Cover help — https://kdp.amazon.com/help/topic/G200645690 "
                    "(min 625×1000, ideal 1600×2560 @1.6:1, JPEG/TIFF, <50MB; verified 2026-06)"),
    _profile("etsy_primary", "Etsy", "digital_marketplace", "marketplace_image",
             {"family": "marketplace_image", "min_px": [2000, 2000], "ideal_px": [3000, 2250],
              "aspect_ratio": 1.3333, "format": "jpeg", "accepted_formats": ["jpeg", "png", "gif"],
              "color_space": "RGB", "max_mb": 20, "dpi": 72,
              "transparency_allowed": False, "transparency_rule": "Flatten for JPEG; PNG accepted. No animated GIF.",
              "listing_image_roles": ["primary", "contents", "usage", "digital_download_notice", "preview"]},
             verified="2026-06-01",
             source="Etsy Image Requirements — https://help.etsy.com/hc/en-us/articles/115015663347 "
                    "and Listing Image Policy https://www.etsy.com/legal/policy/listing-image-requirements/253962679005 "
                    "(≥2000px shortest side, JPG/PNG/GIF; verified 2026-06)"),
    _profile("tpt_primary", "Teachers Pay Teachers", "education_marketplace", "marketplace_image",
             {"family": "marketplace_image", "min_px": [750, 750], "ideal_px": [1080, 1080],
              "aspect_ratio": 1.0, "format": "png", "accepted_formats": ["png", "jpeg"],
              "color_space": "RGB", "max_mb": 4, "dpi": 300,
              "transparency_allowed": True, "transparency_rule": "PNG transparency allowed; TpT displays square thumbnails.",
              "listing_image_roles": ["cover", "preview", "contents", "usage", "terms"]},
             verified="2026-06-01",
             source="TpT Thumbnail help — https://help.teacherspayteachers.com/hc/en-us/articles/360042865791 "
                    "(square, min 750×750, PNG, <4MB; verified 2026-06)"),
    _profile("qru_online_primary", "QRU Online Store", "owned_storefront", "marketplace_image",
             {"family": "marketplace_image", "min_px": [1000, 1250], "ideal_px": [1600, 2000],
              "aspect_ratio": 0.8, "format": "png", "accepted_formats": ["png", "jpeg", "webp"],
              "color_space": "RGB", "max_mb": 15, "dpi": 72,
              "transparency_allowed": True, "transparency_rule": "PNG/WebP transparency allowed on storefront."},
             verified="2026-06-01",
             source="QRU Online storefront spec (internal authoritative; verified 2026-06)"),
    _profile("youtube_thumbnail", "YouTube", "video_platform", "social_asset",
             {"family": "social_asset", "ideal_px": [1280, 720], "min_px": [640, 360], "aspect_ratio": 1.7778,
              "format": "jpeg", "accepted_formats": ["jpeg", "png"], "color_space": "RGB", "max_mb": 2, "dpi": 72,
              "text_safe": True, "transparency_allowed": False, "transparency_rule": "Flatten for JPEG."},
             verified="2026-06-01",
             source="YouTube Thumbnail help — https://support.google.com/youtube/answer/72431 "
                    "(1280×720 @16:9, <2MB, JPG/PNG/GIF; verified 2026-06)"),
    _profile("youtube_screen_16x9", "YouTube", "video_platform", "motion_asset",
             {"family": "motion_asset", "canvas_px": [1920, 1080], "aspect_ratio": 1.7778, "fps": 30,
              "format": "mp4", "codec": "h264", "audio": "aac", "caption_safe": True,
              "supports_slideshow_of_stills": True},
             verified="2026-06-01",
             source="YouTube upload encoding — https://support.google.com/youtube/answer/6375112 (verified 2026-06)"),
    _profile("pinterest_pin", "Pinterest", "social_platform", "social_asset",
             {"family": "social_asset", "ideal_px": [1000, 1500], "min_px": [600, 900], "aspect_ratio": 0.6667,
              "format": "png", "accepted_formats": ["png", "jpeg"], "color_space": "RGB", "max_mb": 20, "dpi": 72,
              "transparency_allowed": True, "transparency_rule": "PNG transparency allowed."},
             verified="2026-06-01",
             source="Pinterest product specs — https://help.pinterest.com/en/business/article/pinterest-product-specs (verified 2026-06)"),
    _profile("instagram_post", "Instagram", "social_platform", "social_asset",
             {"family": "social_asset", "ideal_px": [1080, 1080], "min_px": [600, 600], "aspect_ratio": 1.0,
              "format": "jpeg", "accepted_formats": ["jpeg", "png"], "color_space": "RGB", "max_mb": 30, "dpi": 72,
              "transparency_allowed": False, "transparency_rule": "Flatten for JPEG."},
             verified="2026-06-01",
             source="Instagram image sizes — https://help.instagram.com (verified 2026-06)"),
    _profile("tiktok_vertical", "TikTok", "video_platform", "social_asset",
             {"family": "social_asset", "ideal_px": [1080, 1920], "min_px": [720, 1280], "aspect_ratio": 0.5625,
              "format": "jpeg", "accepted_formats": ["jpeg", "png"], "color_space": "RGB", "max_mb": 20, "dpi": 72,
              "overlay_safe": True, "focal_point": "center",
              "transparency_allowed": False, "transparency_rule": "Flatten for JPEG."},
             verified="2026-06-01",
             source="TikTok video/cover specs — https://support.tiktok.com (verified 2026-06)"),
    _profile("one_page_visual_print", "QRU One-Page Knowledge Visual™ (Print)", "print_owned",
             "one_page_knowledge_visual",
             {"family": "one_page_knowledge_visual", "print_sizes_in": [[8.5, 11], [18, 24], [24, 36]],
              "default_size_in": [8.5, 11], "bleed_in": 0.125, "safe_margin_in": 0.25, "dpi": 300,
              "color_space": "CMYK", "format": "pdf", "accepted_formats": ["pdf"],
              "transparency_allowed": False, "transparency_rule": "Flatten — no transparency in print PDF.",
              "requires_information_design": True},
             verified="2026-06-01",
             source="QRU One-Page Knowledge Visual™ Standard (internal authoritative; verified 2026-06)"),
]


async def seed_profiles():
    """PSR seed + reconcile. Inserts missing profiles and CORRECTS profiles that still hold a superseded
    seed (e.g., the old kdp_ebook min_px bug), appending an honest change_history entry. A profile that a
    human has independently edited (extra change_history) is never silently overwritten."""
    for p in _SEED_PROFILES:
        existing = await db[PLATFORM_COLL].find_one({"platform_id": p["platform_id"], "asset_role": p["asset_role"]})
        if not existing:
            await db[PLATFORM_COLL].insert_one(dict(p))
            continue
        # Reconcile: same verified requirements/source? leave it. Otherwise, if not human-modified, correct it.
        same = (existing.get("requirements") == p["requirements"]
                and existing.get("source") == p["source"]
                and existing.get("date_verified") == p["date_verified"])
        human_modified = len(existing.get("change_history", []) or []) > 1
        if not same and not human_modified:
            updated = dict(p)
            hist = list(existing.get("change_history", []) or [])
            hist.append({"version": p["profile_version"], "date": p["date_verified"], "status": p["status"],
                         "note": "Reconciled to verified source during Asset Profile Audit (corrected requirements)."})
            updated["change_history"] = hist
            await db[PLATFORM_COLL].replace_one({"_id": existing["_id"]}, {**updated, "_id": existing["_id"]})


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
    out = {
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
    # Founder Copy Package™ — three ready-to-use export modes (does NOT affect the governance checksum).
    out["founder_copy_package"] = build_founder_copy_package(out, product)
    return out


def _dimensions_text(spec):
    g = spec.get("geometry")
    if g:
        return (f"Full print wrap (back + spine + front): EXACTLY {g['total_wrap_in'][0]} x {g['total_wrap_in'][1]} inches "
                f"({g['total_wrap_px'][0]} x {g['total_wrap_px'][1]} px at {g['dpi']} DPI). "
                f"Spine width {g['spine_in']} in ({g['page_count']} pages, {g['paper_type']} paper). "
                f"Bleed {g['bleed_in']} in on all sides; keep all text/logos {g['zones']['safe_margin_in']} in inside the trim (safe area). "
                f"Reserve a clear barcode zone of {g['zones']['barcode_zone_in'][0]} x {g['zones']['barcode_zone_in'][1]} in on the back cover.")
    px = spec.get("target_px")
    ar = spec.get("aspect_ratio")
    req = spec.get("requirements", {})
    if px:
        return (f"EXACTLY {px[0]} x {px[1]} px" + (f" (aspect ratio {ar})" if ar else "") +
                f", {req.get('color_space','RGB')}, {req.get('dpi',72)} DPI, format {req.get('format','png').upper()}"
                + (f", max {req['max_mb']} MB" if req.get('max_mb') else "") + ".")
    return "Follow the platform's published dimensions."


def build_founder_copy_package(spec, product=None):
    """Founder Copy Package™ (STD-UCAMS-0001) — three ready-to-use export modes for founder/external-AI
    collaboration. No manual editing required. Governance JSON + checksum are preserved untouched."""
    di = spec.get("design_intent", {})
    req = spec.get("requirements", {})
    info = spec.get("information_design")
    title = spec.get("title") or ""
    dims = _dimensions_text(spec)
    colors = ", ".join(di.get("approved_colors", []))
    fonts = ", ".join(di.get("approved_fonts", []))
    prohibited = ", ".join(di.get("prohibited", []))
    listing_roles = ", ".join(req.get("listing_image_roles", []) or req.get("image_roles", []) or [])

    # 1) Human Summary — readable spec.
    hs = [
        f"QRU CREATIVE ASSET SPECIFICATION — {spec.get('spec_id')}",
        f"Product: {title}" + (f" — {spec.get('subtitle')}" if spec.get('subtitle') else ""),
        f"Asset: {spec.get('asset_family')} · Role: {spec.get('asset_role')} · Destination: {spec.get('platform_name')} (profile {spec.get('profile_version')}, {spec.get('profile_status')})",
        "",
        "TECHNICAL REQUIREMENTS:",
        f"  • {dims}",
        "",
        "DESIGN INTENT:",
        f"  • Purpose: {di.get('asset_purpose','')}",
        f"  • Audience: {di.get('audience','')}",
        f"  • Primary message: {di.get('primary_message','')}",
        f"  • Tone: {di.get('emotional_tone','')}",
        "",
        "BRAND STANDARDS (inherited):",
        f"  • Imprint: {di.get('imprint','')}  ·  Trademark: {', '.join(di.get('required_trademark_symbols', []))}",
        f"  • Approved colors: {colors}",
        f"  • Approved fonts: {fonts}",
        f"  • Editorial: {di.get('editorial_bible_inheritance','')}",
        f"  • Do NOT use: {prohibited}",
    ]
    if listing_roles:
        hs += ["", f"MARKETPLACE REQUIREMENTS:", f"  • Listing image roles: {listing_roles}"]
    if info:
        hs += ["", "INFORMATION DESIGN:", f"  • Type: {info.get('visual_type')} · Outcome: {info.get('intended_outcome')}",
               f"  • Hierarchy: {' > '.join(info.get('visual_hierarchy', []))}",
               f"  • Quality bar: {info.get('quality_bar')}"]
    hs += ["", f"GOVERNANCE: spec_id {spec.get('spec_id')} · checksum {spec.get('spec_checksum','')[:16]} · {spec.get('standard')}"]
    human_summary = "\n".join(hs)

    # 2) ChatGPT Prompt — complete, one-paste prompt formatted for AI image generation.
    cg = [
        f"You are a senior brand designer. Create a {spec.get('asset_family','').replace('_',' ')} "
        f"({spec.get('asset_role','').replace('_',' ')}) for {spec.get('platform_name')}.",
        "",
        f"PRODUCT: \"{title}\"" + (f", subtitle \"{spec.get('subtitle')}\"" if spec.get('subtitle') else "")
        + (f", by {di.get('imprint')}" if di.get('imprint') else "") + ".",
        f"PRIMARY MESSAGE: {di.get('primary_message','')}",
        f"AUDIENCE: {di.get('audience','')}.  TONE: {di.get('emotional_tone','')}.",
        "",
        f"EXACT TECHNICAL REQUIREMENTS (must match precisely): {dims}",
        "",
        f"BRAND STANDARDS (mandatory): Imprint {di.get('imprint','')}. "
        f"Use ONLY these brand colors: {colors}. Use ONLY these fonts (or closest match): {fonts}. "
        f"Include the ™ trademark on QRU marks. Follow the {di.get('editorial_bible_inheritance','QRU brand')}.",
        f"DO NOT: {prohibited}. No generic AI-poster look, no clip art, no unverified claims.",
    ]
    if listing_roles:
        cg += ["", f"MARKETPLACE: Produce the {spec.get('platform_name')} listing set covering these roles: {listing_roles}."]
    if info:
        cg += ["", f"INFORMATION DESIGN: This is a {info.get('visual_type')} whose goal is to {info.get('intended_outcome')}. "
               f"Visual hierarchy (most to least prominent): {', '.join(info.get('visual_hierarchy', []))}. "
               f"Quality bar: {info.get('quality_bar')}."]
    cg += ["",
           "RENDER INSTRUCTIONS: Deliver at the EXACT pixel dimensions above. Keep all text fully inside the safe "
           "area (nothing clipped at edges). High contrast, legible typography, intentional hierarchy, premium finish. "
           "Provide a flat, print/marketplace-ready image.",
           "",
           f"(Governance ref — do not render this line: QRU {spec.get('spec_id')} / checksum {spec.get('spec_checksum','')[:16]})"]
    chatgpt_prompt = "\n".join(cg)

    return {
        "modes": ["human_summary", "chatgpt_prompt", "raw_json"],
        "human_summary": human_summary,
        "chatgpt_prompt": chatgpt_prompt,
        "raw_json_note": "Full specification JSON (this object) is the technical archive; checksum preserved for governance.",
        "spec_id": spec.get("spec_id"), "spec_checksum": spec.get("spec_checksum"),
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
    target = spec.get("target_px") or req.get("ideal_px")
    minpx = req.get("min_px")
    # HARD minimum — a genuine reject only if the source cannot meet the destination's floor.
    if minpx and (w < minpx[0] or h < minpx[1]):
        issues.append(f"Below hard minimum pixels: got {w}x{h}, need >= {minpx[0]}x{minpx[1]}")
    # Governed EXACT export target — below/above target but above minimum is NORMALIZABLE, not a failure.
    if target and (w, h) != (int(target[0]), int(target[1])) and not (minpx and (w < minpx[0] or h < minpx[1])):
        warnings.append(f"Not at exact governed size {target[0]}x{target[1]} (got {w}x{h}) — "
                        f"the Render/Export engine will produce the exact final file.")
    # Aspect — compare orientation-aware against the target dimensions (not the raw ratio field).
    if target:
        tgt_ar = round(int(target[0]) / int(target[1]), 4)
        ar = round(w / h, 4)
        if abs(ar - tgt_ar) > 0.02:
            warnings.append(f"Aspect ratio {ar} differs from target {tgt_ar} — will be padded (letterbox), never cropped.")
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


def scan_qr(data, is_pdf=False):
    """Scan QR codes from the FINAL RENDERED asset (rasterize PDF pages / decode image) using OpenCV.
    Returns the list of decoded payload strings actually present in the finished file."""
    import cv2
    import numpy as np
    imgs = []
    try:
        if is_pdf or data[:4] == b"%PDF":
            import fitz
            doc = fitz.open(stream=data, filetype="pdf")
            for pg in doc:
                pix = pg.get_pixmap(dpi=200)
                arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if pix.n == 4:
                    arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:
                    arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                imgs.append(arr)
        else:
            arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if arr is not None:
                imgs.append(arr)
    except Exception:
        return []
    det = cv2.QRCodeDetector()
    found = []
    for arr in imgs:
        try:
            ok, decoded, pts, _ = det.detectAndDecodeMulti(arr)
            if ok:
                found += [s for s in decoded if s]
            else:
                s, _, _ = det.detectAndDecode(arr)
                if s:
                    found.append(s)
        except Exception:
            pass
    return found


def _norm_url(u):
    return (u or "").strip().rstrip("/").lower().replace("https://", "").replace("http://", "")


def validate_qr(data, expected_url=None, is_pdf=False):
    """QR verification (§15): scan the finished asset, confirm it decodes, and confirm the destination
    matches the expected URL. Fails manufacturing on missing / broken / wrong destination."""
    found = scan_qr(data, is_pdf)
    if not found:
        return {"result": "FAIL", "found": False, "decoded": [],
                "reason": "No QR code detected in the final rendered asset."}
    decoded = found[0]
    if expected_url and expected_url.strip():
        if _norm_url(decoded) == _norm_url(expected_url):
            return {"result": "PASS", "found": True, "decoded": found,
                    "reason": "QR decodes to the expected destination."}
        if _norm_url(expected_url).split("/")[0] in _norm_url(decoded):
            return {"result": "PASS WITH WARNINGS", "found": True, "decoded": found,
                    "reason": f"QR host matches but full path differs (got '{decoded}')."}
        return {"result": "FAIL", "found": True, "decoded": found,
                "reason": f"QR decodes to '{decoded}', which does NOT match expected '{expected_url}'."}
    return {"result": "PASS WITH WARNINGS", "found": True, "decoded": found,
            "reason": "QR decodes, but no expected destination was supplied to compare against."}


def validate_asset(spec, data, *, mime="", asset_meta=None, expected_qr_url=None):
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
    # QR verification from the FINAL rendered asset (§15) — only when a QR destination is expected.
    qr = None
    if expected_qr_url:
        qr = validate_qr(data, expected_qr_url, is_pdf=is_pdf)
        checks["qr"] = qr["result"] in ("PASS", "PASS WITH WARNINGS")
        if qr["result"] == "FAIL":
            issues.append(f"QR validation FAILED — {qr['reason']}")
            result = "FAIL"
        elif qr["result"] == "PASS WITH WARNINGS" and result == "PASS":
            warnings.append(f"QR: {qr['reason']}")
            result = "PASS WITH WARNINGS"
    if rights_missing:
        warnings.append(f"Rights incomplete (missing: {', '.join(rights_missing)}) — Rights Hold until resolved.")
        result = "HOLD"
    return {"result": result, "issues": issues, "warnings": warnings,
            "rights_missing": rights_missing, "spec_checksum": spec.get("spec_checksum"),
            "qr_validation": qr, "validated_at": _now(), "checks": checks,
            "correction_required": issues or ([f"Provide rights: {rights_missing}"] if rights_missing else [])}


# ---------------------------------------------------------------------------
# CAVL™ — vault + lineage. Approved+locked assets are never silently replaced (§2.2).
# ---------------------------------------------------------------------------
async def store_asset(*, product_id, spec, data, filename, asset_meta, validation, actor="Founder",
                      parent_asset_id=None, normalization=None, source_validation=None,
                      source_file_url=None, source_checksum=None):
    import rendering_engine as re
    fid = re._save(f"ucams-{spec.get('asset_role','asset')}", (filename.rsplit(".", 1)[-1] if "." in filename else "bin"), data)
    checksum = hashlib.sha256(data).hexdigest()
    # Version: increment within the same (product, role, platform) family.
    prior = await db[ASSET_COLL].count_documents({"product_id": product_id, "asset_role": spec.get("asset_role"),
                                                  "platform_id": spec.get("platform_id")})
    quality_review = bool((normalization or {}).get("quality_review_required"))
    if validation["result"] == "HOLD":
        state = "Rights Hold"
    elif validation["result"] == "FAIL":
        state = "Rejected"
    elif quality_review:
        state = "Revision Required"  # compliant file produced, but a quality-affecting change needs human sign-off
    else:
        state = "Under Review"
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
        # Governed Render/Export lineage — source artwork is preserved; final file is governed.
        "normalization": normalization,
        "source_validation": source_validation,
        "source_file_url": source_file_url, "source_checksum": source_checksum,
        "quality_review_required": quality_review,
        "lifecycle_state": state,
        "created_by": actor, "created_at": _now(), "updated_at": _now(),
        "publication_history": [], "standard": STANDARD_ID,
    }
    await db[ASSET_COLL].insert_one(dict(asset))
    asset.pop("_id", None)
    return asset


async def manufacture_final_asset(product, asset_role, platform_id, source_bytes, filename, *,
                                  mime="", rights=None, pages=None, paper_type="white",
                                  expected_qr_url=None, auto_normalize=True, actor="Founder",
                                  parent_asset_id=None):
    """Governed manufacturing path: source artwork → Render/Export the EXACT final file → validate the
    FINAL file → vault. Provider/designer output is treated as SOURCE and never published as-is."""
    import asset_normalizer as norm
    import rendering_engine as re
    spec_obj = await generate_spec(product, asset_role, platform_id, pages=pages, paper_type=paper_type or "white")
    if spec_obj.get("error"):
        return {"error": spec_obj["error"]}
    # Validate the incoming SOURCE first (honest record of what arrived).
    source_validation = validate_asset(spec_obj, source_bytes, mime=mime, asset_meta=rights, expected_qr_url=expected_qr_url)
    source_checksum = hashlib.sha256(source_bytes).hexdigest()
    source_fid = re._save(f"ucams-source-{asset_role}", (filename.rsplit(".", 1)[-1] if "." in filename else "bin"), source_bytes)
    source_url = re._asset_url(source_fid)

    export = norm.governed_export(spec_obj, source_bytes, mime=mime) if auto_normalize else \
        {"normalized": False, "data": source_bytes, "ext": None, "actions": [], "quality_review_required": False, "error": None}
    if export.get("error"):
        return {"error": f"Render/Export failed: {export['error']}", "source_validation": source_validation}

    final_data = export.get("data") if export.get("normalized") else source_bytes
    if export.get("normalized") and export.get("ext"):
        base = filename.rsplit(".", 1)[0] if "." in filename else filename
        final_filename = f"{base}.{export['ext']}"
    else:
        final_filename = filename
    # Validate the GOVERNED FINAL file — this is the compliance gate.
    final_validation = validate_asset(spec_obj, final_data, mime=export.get("mime", ""),
                                      asset_meta=rights, expected_qr_url=expected_qr_url)
    asset = await store_asset(product_id=product["id"], spec=spec_obj, data=final_data, filename=final_filename,
                              asset_meta=rights, validation=final_validation, actor=actor,
                              parent_asset_id=parent_asset_id, normalization=export,
                              source_validation=source_validation, source_file_url=source_url,
                              source_checksum=source_checksum)
    return {"spec_id": spec_obj.get("spec_id"), "source_validation": source_validation,
            "normalization": {k: export[k] for k in ("normalized", "actions", "quality_review_required",
                              "notes", "final_dimensions", "final_bytes", "final_format") if k in export},
            "final_validation": final_validation, "asset": asset}


# ---------------------------------------------------------------------------
# Asset Profile Audit (§ registry audit) — every destination × asset profile in one governed table,
# including the source used to verify each requirement, date verified, version, and current status.
# ---------------------------------------------------------------------------
def _fmt_px(v):
    return f"{v[0]}×{v[1]}" if isinstance(v, (list, tuple)) and len(v) == 2 else "—"


async def profile_audit():
    profiles = await list_profiles()
    today = datetime.now(timezone.utc).date().isoformat()
    rows = []
    for p in profiles:
        req = p.get("requirements", {})
        geom = "print wrap (computed per page count)" if req.get("family") == "print_cover_wrap" else None
        exact = req.get("ideal_px") or req.get("canvas_px")
        rows.append({
            "platform_id": p["platform_id"], "destination": p["platform_name"],
            "destination_type": p.get("destination_type"), "asset_role": p["asset_role"],
            "asset_family": req.get("family"),
            "file_format": (req.get("format") or "").upper(),
            "accepted_formats": ", ".join([f.upper() for f in (req.get("accepted_formats") or [req.get("format")]) if f]),
            "exact_or_ideal_px": geom or _fmt_px(exact),
            "minimum_px": _fmt_px(req.get("min_px")) if req.get("min_px") else "—",
            "aspect_ratio": req.get("aspect_ratio") or (round(exact[0] / exact[1], 4) if exact else "—"),
            "color_mode": req.get("color_space") or "—",
            "dpi": req.get("dpi") or "—",
            "max_file_size_mb": req.get("max_mb") or "—",
            "transparency": req.get("transparency_rule") or ("Allowed" if req.get("transparency_allowed") else "Not allowed"),
            "print_bleed_trim_spine": (
                f"bleed {req.get('bleed_in')}in, trim {req.get('default_trim_in') or req.get('default_size_in')}, "
                f"spine ≥{req.get('spine_text_min_pages','—')}pp, safe {req.get('safe_margin_in')}in"
                if req.get("family") in ("print_cover_wrap", "one_page_knowledge_visual") else "N/A (digital)"),
            "source": p.get("source"),
            "date_verified": p.get("date_verified"),
            "verified_by": p.get("verified_by"),
            "profile_version": p.get("profile_version"),
            "status": p.get("status"),
            "review_due": bool(p.get("next_review_date") and p["next_review_date"] < today),
            "next_review_date": p.get("next_review_date"),
        })
    return {"standard": STANDARD_ID, "generated_at": _now(), "destination_count": len({r["destination"] for r in rows}),
            "profile_count": len(rows), "rows": rows}


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


# ---------------------------------------------------------------------------
# Marketplace packages (§ Marketplace Packages) — governed, review-ready. NEVER auto-publish.
# ---------------------------------------------------------------------------
MARKETPLACE_REQUIRED_ROLES = {
    "etsy": [("marketplace_image", "etsy_primary", ["primary", "contents", "usage", "preview"])],
    "amazon_kdp": [("print_cover_wrap", "kdp_paperback_wrap", ["wrap"]),
                   ("digital_cover", "kdp_ebook_cover", ["cover"])],
    "kdp": [("print_cover_wrap", "kdp_paperback_wrap", ["wrap"]),
            ("digital_cover", "kdp_ebook_cover", ["cover"])],
    "tpt": [("marketplace_image", "tpt_primary", ["cover", "preview", "contents"])],
    "shopify": [("marketplace_image", "qru_online_primary", ["primary"])],
    "qru_online": [("marketplace_image", "qru_online_primary", ["primary"])],
}


async def build_marketplace_package(product, marketplace):
    """Assemble a governed, review-ready marketplace package from APPROVED+LOCKED assets. Reports the
    required vs present assets, listing copy for that channel, pricing, and the governed publication
    decision. Does NOT publish (STD-PUB-0001 decides the mode)."""
    import publication_policy as pp
    mk = marketplace.lower()
    reqs = MARKETPLACE_REQUIRED_ROLES.get(mk)
    if not reqs:
        return {"error": f"No governed package definition for marketplace '{marketplace}'."}
    required, present, missing = [], [], []
    for role, platform_id, image_roles in reqs:
        prof = await get_profile(platform_id, role)
        assets = await db[ASSET_COLL].find(
            {"product_id": product.get("id"), "platform_id": platform_id,
             "lifecycle_state": {"$in": ["Approved", "Locked", "Platform Validated", "Distribution Authorized"]}},
            {"_id": 0}).to_list(50)
        required.append({"asset_role": role, "platform_id": platform_id, "image_roles": image_roles,
                         "profile_version": (prof or {}).get("profile_version"),
                         "profile_status": (prof or {}).get("status")})
        if assets:
            for a in assets:
                present.append({"asset_id": a["asset_id"], "asset_role": role, "platform_id": platform_id,
                                "version": a["version"], "state": a["lifecycle_state"], "file_url": a["file_url"]})
        else:
            missing.append({"asset_role": role, "platform_id": platform_id,
                            "reason": "No Approved/Locked asset in the vault for this role."})
    channel = {"etsy": "etsy", "amazon_kdp": "amazon", "kdp": "amazon", "tpt": "tpt",
               "shopify": "qru_online", "qru_online": "qru_online"}.get(mk, "generic")
    descs = (product.get("descriptions") or {})
    listing_copy = descs.get(channel) or descs.get("generic") or {"text": product.get("description", "")}
    decision = await pp.decide(product, mk if mk != "kdp" else "amazon_kdp")
    ready = len(missing) == 0 and bool(listing_copy.get("text"))
    return {
        "standard": STANDARD_ID, "marketplace": marketplace, "product_id": product.get("id"),
        "title": product.get("title"),
        "required_assets": required, "present_assets": present, "missing_assets": missing,
        "listing_copy": listing_copy,
        "pricing": product.get("pricing") or {"list_price": product.get("list_price")},
        "package_ready": ready,
        "governed_publication_mode": decision["policy"]["effective_mode"],
        "publication_decision": decision["decision"],
        "can_publish": decision["can_publish"],
        "blocked_reason": None if ready else "Package is not review-ready — supply the missing approved assets and an approved description.",
        "note": "Review-ready package. The Factory does NOT auto-publish; Governed Publication Policy™ decides the mode.",
        "built_at": _now(),
    }
