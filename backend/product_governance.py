"""QRU Product Governance Package™ — one centralized, inherited enterprise standard.

Every manufactured artifact (Decoder Record, Book, Poster, Workbook, Audiobook, Video, Course…)
AUTOMATICALLY inherits the appropriate disclaimers, transparency statements, provenance,
versioning, accessibility, copyright, licensing and category-specific governance language based
on its classification and domain. This is a Factory responsibility — never a manual per-product step.
One Responsibility. One Owner. One source of governance truth.
"""
from datetime import datetime, timezone

BRAND = "QRU Factory™"
COPYRIGHT_HOLDER = "QRU"
STANDARD_ID = "STD-GOV-PKG-0001"

# Domains that require heightened, category-specific governance language.
HIGH_STAKES_DOMAINS = {
    "medical": ("Health & Medical", "This material is educational and is not medical advice, diagnosis, or treatment. "
                "Consult a qualified healthcare professional for personal decisions."),
    "health": ("Health & Medical", "This material is educational and is not medical advice, diagnosis, or treatment. "
               "Consult a qualified healthcare professional for personal decisions."),
    "finance": ("Financial", "This material is educational and is not financial, investment, or trading advice. "
                "Markets carry risk; consult a licensed financial professional before making decisions."),
    "trading": ("Financial", "This material is educational and is not financial, investment, or trading advice. "
                "Trading carries substantial risk of loss; consult a licensed professional."),
    "legal": ("Legal", "This material is educational and is not legal advice. Consult a qualified attorney "
              "for guidance on your specific situation."),
    "safety": ("Safety", "This material is educational. Follow official safety guidance and qualified supervision "
               "for real-world application."),
    "child": ("Children", "Designed for children with a caring adult. Adult guidance is recommended."),
    "children": ("Children", "Designed for children with a caring adult. Adult guidance is recommended."),
}

# Classification → licensing + primary transparency note.
_CLASS_LICENSE = {
    "Decoder Record™": "Internal governed artifact — inherited by downstream products.",
    "Book": "All rights reserved. Single-reader license unless otherwise stated.",
    "Workbook": "All rights reserved. Classroom/family use license as stated at point of sale.",
    "Poster": "All rights reserved. Display license as stated at point of sale.",
    "Audiobook": "All rights reserved. Single-listener license unless otherwise stated.",
    "Video": "All rights reserved. Standard viewing license.",
    "Course": "All rights reserved. Single-enrollment license unless otherwise stated.",
}


def _now_year():
    return datetime.now(timezone.utc).year


def detect_high_stakes(text):
    t = (text or "").lower()
    for key, (label, _msg) in HIGH_STAKES_DOMAINS.items():
        if key in t:
            return label, HIGH_STAKES_DOMAINS[key][1]
    return None, None


def build_package(classification, *, title="", version=1, domain="", audience="",
                  source=None, decoded_by="", high_stakes=False, accessibility_notes=""):
    """Return the governed package inherited by an artifact. Centralized & automatic."""
    domain_label, category_statement = detect_high_stakes(f"{domain} {title}")
    if high_stakes and not category_statement:
        domain_label, category_statement = ("General", "This material is educational.")

    disclaimers = ["This material is educational and reflects governed knowledge at time of manufacture."]
    if category_statement:
        disclaimers.append(category_statement)

    pkg = {
        "standard_id": STANDARD_ID,
        "standard": "QRU Product Governance Package™",
        "owner": "Factory (inherited — never manual per-product)",
        "classification": classification,
        "disclaimers": disclaimers,
        "transparency": (
            "Manufactured by the QRU Factory™ from a Verified Knowledge Record™. "
            "AI assisted drafting and advisory scoring; all governed standards were checked by the Factory. "
            "AI advisory never approves, certifies, or publishes — governance authority is human/constitutional."
        ),
        "provenance": {
            "manufactured_by": BRAND,
            "source": source or {},
            "decoded_by": decoded_by,
            "manufactured_at": datetime.now(timezone.utc).isoformat(),
        },
        "versioning": {"version": version, "policy": "Append-only; canonical records are never overwritten."},
        "accessibility": (accessibility_notes or
                          "Plain-language explanation, defined vocabulary, and alt-text for visuals where applicable."),
        "copyright": f"© {_now_year()} {COPYRIGHT_HOLDER}. All rights reserved.",
        "licensing": _CLASS_LICENSE.get(classification, "All rights reserved."),
        "category_governance": ({"domain": domain_label, "statement": category_statement}
                                if category_statement else None),
        "inherited": True,
    }
    return pkg
