"""QRU Manufacturing Foundation™, Product Manufacturing Standards™ (PMS™) and Product Manifests™ (PMF™).

CONSTITUTIONAL OWNERSHIP:
    UKR™ = TRUTH        (what is true, valuable, worth teaching)          — see ukr_standard.py
    PMS™ = INSTRUCTIONS (how a product family is ALWAYS manufactured)      — this module
    PMF™ = EVIDENCE     (exactly what happened during one manufacture)     — this module

Nothing overlaps. Knowledge is governed once; products inherit; production is auditable.

Manufacturing Foundation™ (STD-MFG-FOUNDATION-0001) owns the SHARED manufacturing behavior every product
family inherits so the families never drift apart:
    intake · state management · verification · provenance · Founder navigation ·
    packaging · approval logic · monitoring
Each Product Manufacturing Standard™ inherits the Foundation and adds ONLY its product-specific
instructions (the 6 categories). CONSTITUTIONAL RULE: no product may manufacture without an approved PMS™.
"""
from datetime import datetime, timezone

import product_recipes as catalog

FOUNDATION_ID = "STD-MFG-FOUNDATION-0001"
PMS_STANDARD_ID = "STD-MFG-PRD-0001"
PMF_STANDARD_ID = "STD-MFG-PMF-0001"

# The shared behavior every PMS inherits (owned once, improved once, inherited everywhere).
FOUNDATION = {
    "standard_id": FOUNDATION_ID,
    "name": "QRU Manufacturing Foundation™",
    "purpose": "Own the shared manufacturing behavior every product family inherits, so families never drift apart.",
    "constitutional_ownership": "PMS™ = INSTRUCTIONS. Each PMS inherits this Foundation and adds only product-specific instructions.",
    "shared_capabilities": [
        "Intake (Upload / Decoder bridge / import)",
        "State management (governed lifecycle)",
        "Verification (Knowledge-First gate)",
        "Provenance (Transparent Provenance™)",
        "Founder navigation (the same 7-button interface)",
        "Packaging (Master Output Package + Factory Library™)",
        "Approval logic (Founder Release Review™ + release gate)",
        "Monitoring (honest post-publish + evidence)",
    ],
    "improvement_rule": "Improve the Foundation once → every product family inherits the improvement.",
}

# The constitutional standards every product records as having governed its production (per Founder).
INHERITED_STANDARDS_BASE = [
    {"id": "STD-UKR-0001", "name": "QRU Universal Knowledge Record™ (UKR™)", "owns": "Truth"},
    {"id": PMS_STANDARD_ID, "name": "QRU Product Manufacturing Standard™ (PMS™)", "owns": "Instructions"},
    {"id": "STD-PUB-0001", "name": "QRU Publishing Standard™", "owns": "Publication conventions"},
    {"id": "STD-DES-0001", "name": "QRU Design Standard™", "owns": "On-brand design & typography"},
    {"id": "STD-TREASURE-0001", "name": "Treasure Standard™", "owns": "Absolute honesty — no fake states"},
    {"id": "STD-VER-0001", "name": "Verification Standard™", "owns": "Evidence before publication"},
    {"id": "STD-EVID-0001", "name": "Evidence Standard™", "owns": "Auditable manufacturing record"},
]

_PMS_REGISTRY = {}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _pms(product_family, product_type, *, version="v1.0", ukr_sections, specs, metadata,
         brand, quality_gates, deliverables, approved=True):
    """Compose a Product Manufacturing Standard™ that INHERITS the Manufacturing Foundation™."""
    return {
        "standard_id": PMS_STANDARD_ID, "name": f"{product_family} Manufacturing Standard™",
        "product_family": product_family, "product_type": product_type, "version": version,
        "owner": f"{product_family} Manufacturing Engine™",
        "inherits_foundation": FOUNDATION_ID,
        "constitutional_ownership": "PMS™ = INSTRUCTIONS (only product-specific).",
        "approved": approved, "approved_at": _now() if approved else None,
        # 1. Product Identity (2. Applicable UKR sections)
        "product_identity": {"product_family": product_family, "product_type": product_type,
                             "version": version, "owner": f"{product_family} Manufacturing Engine™",
                             "applicable_ukr_sections": ukr_sections},
        # 2. Manufacturing Specifications
        "manufacturing_specifications": specs,
        # 3. Product Metadata
        "product_metadata": metadata,
        # 4. Brand Standards
        "brand_standards": brand,
        # 5. Quality Gates
        "quality_gates": quality_gates,
        # 6. Deliverables
        "deliverables": deliverables,
    }


def register(pms):
    _PMS_REGISTRY[pms["product_type"]] = pms
    return pms


def get_pms(product_type):
    return _PMS_REGISTRY.get(product_type)


def list_pms():
    return [{"product_family": p["product_family"], "product_type": p["product_type"],
             "version": p["version"], "approved": p["approved"], "owner": p["owner"],
             "inherits_foundation": p["inherits_foundation"]} for p in _PMS_REGISTRY.values()]


def require_pms(product_type):
    """CONSTITUTIONAL GATE: no product may manufacture without an approved PMS™.
    Returns (ok, pms_or_error)."""
    pms = get_pms(product_type)
    if not pms:
        return False, {"error": f"No Product Manufacturing Standard™ exists for '{product_type}'. "
                                "Constitutional rule: every product family must define an approved PMS™ before manufacturing begins."}
    if not pms.get("approved"):
        return False, {"error": f"The {pms['name']} exists but is not approved. Manufacturing is blocked until it is approved."}
    return True, pms


def inherited_standards(product_type, ukr_version=None, pms_version=None):
    """The exact constitutional standards that governed this product's production (per Founder)."""
    pms = get_pms(product_type)
    out = []
    for s in INHERITED_STANDARDS_BASE:
        row = dict(s)
        if s["id"] == "STD-UKR-0001" and ukr_version:
            row["version_used"] = ukr_version
        if s["id"] == PMS_STANDARD_ID:
            row["name"] = (pms["name"] if pms else row["name"])
            row["version_used"] = pms_version or (pms["version"] if pms else None)
        out.append(row)
    return out


def build_manifest(*, product, source_ukr, quality, distribution, governance, assets, production, actor):
    """Generate the Product Manifest™ (PMF™) — EVIDENCE of one manufacture.

    The PMF is sacred because it answers ONE question: "exactly what happened during manufacturing?"
    It REFERENCES the UKR (never duplicates its knowledge) and records the inherited standards used.
    """
    product_type = product.get("product_type", "Book")
    pms = get_pms(product_type)
    ukr_version = (source_ukr or {}).get("version")
    manifest_id = f"PMF-{product.get('book_code') or product.get('id','')}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    return {
        "standard_id": PMF_STANDARD_ID, "name": f"{product.get('product_family', product_type)} Manifest™",
        "manifest_id": manifest_id, "manufacturing_date": _now(), "manufactured_by": actor,
        "constitutional_ownership": "PMF™ = EVIDENCE (exactly what happened during manufacturing).",
        "question_answered": "Exactly what happened during manufacturing?",
        # 1. Product Identity
        "product_identity": {
            "product_name": product.get("published_title") or product.get("title"),
            "product_family": product.get("product_family", product_type), "product_type": product_type,
            "product_version": product.get("edition", "First Edition"), "manifest_id": manifest_id,
        },
        # 2. Source Intelligence (REFERENCE to the UKR — never duplicates its knowledge)
        "source_intelligence": {
            "ukr_id": (source_ukr or {}).get("kr_code") or (source_ukr or {}).get("id"),
            "knowledge_title": (source_ukr or {}).get("knowledge_title"),
            "published_title": product.get("published_title") or product.get("title"),
            "ukr_version": ukr_version,
            "manufacturing_standard_version": pms["version"] if pms else None,
            "note": "Knowledge is referenced, never duplicated — the UKR remains the single source of truth.",
        },
        # INHERITED STANDARDS (Founder-required) — exactly which constitutional standards governed production
        "inherited_standards": inherited_standards(product_type, ukr_version, pms["version"] if pms else None),
        # 3. Assets Used
        "assets_used": assets,
        # 4. Production Results
        "production_results": production,
        # 5. Quality Results
        "quality_results": quality,
        # 6. Distribution
        "distribution": distribution,
        # 7. Governance
        "governance": {**(governance or {}), "manufacturing_engine": pms["owner"] if pms else product_type,
                       "responsible_standard": pms["name"] if pms else None},
        # 8. Enterprise Memory™ links
        "enterprise_memory": {
            "source_record": (source_ukr or {}).get("kr_code") or (source_ukr or {}).get("id"),
            "related_products": product.get("related_products", []),
            "dependencies": product.get("dependencies", []),
        },
    }


def standards_overview():
    return {
        "foundation": FOUNDATION,
        "constitutional_flow": [
            {"artifact": "UKR™", "owns": "Truth", "standard": "STD-UKR-0001"},
            {"artifact": "PMS™", "owns": "Instructions", "standard": PMS_STANDARD_ID},
            {"artifact": "PMF™", "owns": "Evidence", "standard": PMF_STANDARD_ID},
        ],
        "rule": "No product may manufacture without an approved Product Manufacturing Standard™.",
        "product_manufacturing_standards": list_pms(),
        "inherited_standards": INHERITED_STANDARDS_BASE,
    }


# ---------------------------------------------------------------------------
# Registered Product Manufacturing Standards™ (each inherits the Foundation).
# ---------------------------------------------------------------------------
register(_pms(
    "Book", "Book",
    ukr_sections=["Knowledge Title", "Published Title", "Verified Truth", "Why It Matters",
                  "How It Works", "Core Mental Model", "Applications", "References"],
    specs={
        "required_inputs": ["Approved editorial edition (locked)", "Selected cover", "Approved pricing"],
        "required_assets": ["Front cover art", "Print cover wrap", "eBook cover (JPEG 1600×2560)"],
        "manufacturing_steps": ["Upload", "Proof & Polish", "Design", "Audio (optional)", "Video (optional)",
                                "Publish (sanitize + release gate)", "Monitor"],
        "output_formats": ["Paperback interior PDF (6×9, 300 DPI)", "EPUB", "Print cover wrap PDF"],
        "export_targets": ["Amazon KDP (manual upload)", "QRU Store™"],
    },
    metadata={"audience": "General reader", "reading_level": "Adult trade", "accessibility": "Alt-text, clear type hierarchy",
              "localization": "English (v1)", "distribution_channels": ["Amazon KDP", "QRU Store™"],
              "licensing": "All rights reserved; single-reader license"},
    brand={"qru_branding": "QRU Press™ imprint", "typography": "Serif title/subtitle, sans eyebrow",
           "colors": "Navy / Gold / Royal", "visual_standards": "Full-bleed cover art + legibility scrim"},
    quality_gates={"acceptance_criteria": ["6×9 trim exact", "eBook cover JPEG ratio 1.600",
                   "Barcode clear zone 2.0×1.2in solid white", "Retail interior sanitized (no placeholders)"],
                   "validation_checks": ["Final Release Gate all items true"],
                   "required_approvals": ["Founder Release Review™ (5 checks)"],
                   "treasure_standard_score": "Honest states only — no fake publishing"},
    deliverables={"final_files": ["paperback_interior.pdf", "book.epub", "paperback_cover_wrap.pdf", "ebook_cover.jpg"],
                  "source_files": ["immutable_original", "approved_editorial_master"],
                  "metadata_package": ["Ready_for_KDP", "publication_metadata", "product_manifest"]},
))

# Common families registered so every product line has a PMS inheriting the Foundation (constitutional rule).
for fam, ptype in [("Workbook", "Workbook"), ("Poster", "Poster"), ("Knowledge Card", "Flash Cards"),
                   ("Quick Card", "Quick Card"), ("Teacher Guide", "Teacher Guide"),
                   ("Presentation", "Presentation"), ("Course", "Course"), ("Audiobook", "Audiobook"),
                   ("Video", "Video")]:
    r = catalog.RECIPES.get(ptype, {})
    register(_pms(
        fam, ptype,
        ukr_sections=["Knowledge Title", "Published Title", "Verified Truth", "Why It Matters"],
        specs={"required_inputs": ["Verified UKR™"], "required_assets": ["On-brand design"],
               "manufacturing_steps": ["Intake", "Design", "Publish", "Monitor"],
               "output_formats": [r.get("primary", "pdf").upper()], "export_targets": ["QRU Store™"]},
        metadata={"audience": "General", "accessibility": "Alt-text where applicable",
                  "distribution_channels": ["QRU Store™"], "licensing": "All rights reserved"},
        brand={"qru_branding": "QRU", "colors": "Navy / Gold / Royal"},
        quality_gates={"acceptance_criteria": ["On-brand", "Honest states only"],
                       "required_approvals": ["Founder approval"], "treasure_standard_score": "Honest states only"},
        deliverables={"final_files": [f"{fam.lower().replace(' ','_')}.{r.get('primary','pdf')}"],
                      "metadata_package": ["product_manifest"]},
        approved=True,
    ))
