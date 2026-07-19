"""QRU Publication Quality Standard™ (STD-PUB-0001) — the SHARED publication foundation.

Master Design Standard™ Phase 2. ONE owner of publication-grade output for every DOCUMENT-based
product. Build it once here; every document family inherits it (books, workbooks, guides, courses,
cards…). Families EXTEND this foundation with their own specialized features — they never re-implement
it. Posters/audio/video stay on their own media pipelines (this module is not applied to them).

The foundation guarantees, for any document product:
  • Publication Sanitization Pass™ (internal markers / draft placeholders / embedded front-matter block
    removed from reader-facing pages)
  • a professional Title page, Copyright page, and Colophon (publishing convention)
  • consistent typography hierarchy + spacing + QRU branding standards (rendered by `rendering_engine`)
  • accessibility + governance/disclaimer front matter where applicable (educational profile)

Two governed profiles inherit the same builder:
  • "book"        — Founder-authored trade edition (fiction clause, no governance dump, no learning QR)
  • "publication" — educational documents (educational disclaimer + inherited Product Governance
                    Package™ front matter + continue-learning QR)
  • "card"        — lightweight documents (title + copyright, no colophon)
"""
import re
from datetime import datetime, timezone

STANDARD = {
    "standard_id": "STD-PUB-0001",
    "name": "QRU Publication Quality Standard™",
    "phase": "Master Design Standard™ — Phase 2 (interior/publication parity)",
    "owns": ["Publication Sanitization Pass™", "Title page", "Copyright page", "Colophon",
             "Typography hierarchy", "Spacing & layout", "QRU branding standards",
             "Accessibility & governance front matter (educational)"],
    "typography": {
        "display_serif": "Times (bold) — titles & chapter/section headings",
        "body_serif": "Times — long-form reading body (12pt / 6.5mm leading)",
        "eyebrow_sans": "Helvetica (bold) — CHAPTER eyebrows, labels, running feet",
        "hierarchy": ["Title 30/26pt", "H1 20pt", "H2/chapter 17pt", "H3/section 12pt", "Body 12pt",
                      "Caption/foot 8–9.5pt"],
    },
    "spacing": {"trim": "6x9in trade (152.4 x 228.6mm)", "margins_mm": 18, "auto_page_break_mm": 16},
    "branding": {"palette": "QRU navy / royal / metallic gold", "rule": "gold underline rules on headings",
                 "imprint": "QRU Press™"},
    "accessibility": "Governed disclaimers + accessibility statement inherited from Product Governance"
                     " Package™ (educational profile).",
}

# --- Internal markers that must NEVER reach a reader-facing (retail) page. ---
PLACEHOLDER_PATTERNS = [
    (r"\(?\s*working title\s*\)?", "working-title placeholder"),
    (r"\[[^\]]*?\b(TK|TBD|TODO|PLACEHOLDER|DRAFT|FIXME|XXX)\b[^\]]*?\]", "bracketed editorial marker"),
    (r"\bTKTK\b|\bTK\b(?=\s|$)", "TK marker"),
    (r"\[\s*insert[^\]]*?\]", "insert-note marker"),
    (r"\(draft\)|\bDRAFT ONLY\b|\bDO NOT DISTRIBUTE\b|\bCONFIDENTIAL\b|\bINTERNAL USE ONLY\b", "internal-status marker"),
    (r"\b(TODO|FIXME|XXX|TBD)\b\s*:?[^\n]*", "editorial note"),
    (r"\bfull manuscript\b", "full-manuscript label"),
    (r"ISBN:?\s*assignment pending", "placeholder ISBN"),
]

FICTION_CLAUSE = ("This is a work of fiction. Names, characters, places, and incidents are the product "
                  "of the author's imagination or are used fictitiously. Any resemblance to actual "
                  "persons, living or dead, events, or locales is entirely coincidental.")
EDUCATIONAL_CLAUSE = ("This work is provided for general educational purposes. It has been prepared with "
                      "care and reviewed for accuracy; where a subject carries real-world consequences, "
                      "consult a qualified professional. See the governance and disclaimer notes that follow.")
REPRODUCTION_CLAUSE = ("No part of this book may be reproduced in any form or by any electronic or "
                       "mechanical means, including information storage and retrieval systems, without "
                       "written permission from the publisher, except by a reviewer who may quote brief "
                       "passages in a review.")

# --- Governed profiles. Families inherit ONE of these; they never re-implement the builder. ---
PROFILES = {
    "book": {"subtitle_default": "A Novel", "clause": FICTION_CLAUSE, "include_colophon": True,
             "include_governance": False, "include_learning_qr": False},
    "publication": {"subtitle_default": "", "clause": EDUCATIONAL_CLAUSE, "include_colophon": True,
                    "include_governance": True, "include_learning_qr": True},
    "card": {"subtitle_default": "", "clause": EDUCATIONAL_CLAUSE, "include_colophon": False,
             "include_governance": False, "include_learning_qr": True},
}

# Recipe category → publication profile (document families only). None = not a publication document
# (poster/deck/quiz/lesson/script/certificate/audio/video stay on their own pipelines).
CATEGORY_PROFILE = {
    "book": "publication",       # KR-derived Books & Courses (educational) on the product path
    "guide": "publication",
    "workbook": "publication",
    "card": "card",
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def detect_placeholders(text):
    findings = []
    for pat, label in PLACEHOLDER_PATTERNS:
        for m in re.finditer(pat, text or "", re.I):
            s = max(0, m.start() - 30)
            findings.append({"marker": label, "text": m.group(0).strip(),
                             "context": " ".join((text or "")[s:m.end() + 30].split())})
    return findings


def split_front_matter(content):
    """Separate a manuscript-embedded front-matter block (title/byline/publisher) from the reader body.
    The reader body begins at the first chapter heading; the embedded block is regenerated cleanly as a
    Title Page, so it is dropped from the body."""
    lines = (content or "").split("\n")
    for i, ln in enumerate(lines):
        st = ln.strip()
        if st.startswith("## ") or re.match(r"^#{1,6}\s*chapter\b", st, re.I):
            return "\n".join(lines[:i]), "\n".join(lines[i:])
    return "", content or ""


def sanitize(content):
    """Publication Sanitization Pass™ (content-level): returns (clean_body, findings, front_removed)."""
    findings = detect_placeholders(content)
    front_block, body = split_front_matter(content)
    body_clean = body
    for pat, _ in PLACEHOLDER_PATTERNS:
        body_clean = re.sub(pat, "", body_clean, flags=re.I)
    body_clean = re.sub(r"\(\s*\)", "", body_clean)
    body_clean = re.sub(r"\n{3,}", "\n\n", body_clean).strip()
    return body_clean, findings, bool(front_block.strip())


def build_publication(meta, profile):
    """The ONE shared Title/Copyright/Colophon builder. `profile` selects the clause + inclusions."""
    year = datetime.now(timezone.utc).year
    title = meta.get("title") or "Untitled"
    author = meta.get("author") or "QRU Press™"
    publisher = meta.get("publisher") or meta.get("imprint") or "QRU Press"
    imprint = meta.get("imprint") or publisher
    edition = meta.get("edition") or "First Edition"
    lang = meta.get("language") or "English"
    isbn = meta.get("isbn") or "ISBN: __________________________  (assigned at publication)"
    genre = meta.get("genre") or ""
    ai_disc = meta.get("ai_content_disclosure") or "AI-assisted manufacturing; human-reviewed and human-approved."
    subtitle = meta.get("subtitle") or profile.get("subtitle_default") or ""

    pub_meta = {
        "title": title, "subtitle": meta.get("subtitle") or "", "author": author, "imprint": imprint,
        "publisher": publisher, "edition": edition, "language": lang, "isbn": isbn,
        "copyright_year": year, "copyright_holder": publisher, "rights_statement": "All rights reserved.",
        "publication_date": None, "genre": genre, "ai_content_disclosure": ai_disc,
    }
    title_page = {"title": title, "subtitle": subtitle, "author": author, "imprint": imprint}
    copyright_page = [
        title,
        f"Copyright © {year} {publisher}",
        "All rights reserved.",
        REPRODUCTION_CLAUSE,
        profile["clause"],
        edition,
        isbn,
        f"Published by {imprint}.",
        f"AI content disclosure: {ai_disc}",
    ]
    colophon = []
    if profile.get("include_colophon"):
        colophon = [
            "Colophon",
            (f"{title} was set in a classic serif text face chosen for comfortable long-form reading, "
             "with display typography in a complementary sans-serif."),
            f"Interior design and typesetting by {imprint} — QRU Publication Quality Standard™.",
        ]
    return pub_meta, title_page, copyright_page, colophon


def _governance_front(product):
    """Inherited Product Governance Package™ front matter (educational profile)."""
    try:
        import product_governance as pg
        gp = product.get("governance_package") or pg.build_package(
            product.get("product_type") or "Document",
            title=product.get("title", ""), version=product.get("kr_version", 1),
            domain=product.get("family", ""), audience=product.get("audience", ""),
            high_stakes=bool(product.get("high_stakes")))
        return {
            "copyright": gp.get("copyright", ""), "licensing": gp.get("licensing", ""),
            "disclaimers": gp.get("disclaimers", []), "category_governance": gp.get("category_governance"),
            "transparency": gp.get("transparency", ""), "accessibility": gp.get("accessibility", ""),
        }
    except Exception:
        return None


def profile_for(category, product_type=""):
    return CATEGORY_PROFILE.get(category)


def prepare(product, category=None):
    """Inherit the Publication Quality Standard™ for a DOCUMENT product. Returns None for non-document
    families (they stay on their own pipeline). Otherwise returns the sanitized body + a
    `retail_publication` block ready for `rendering_engine._make_pdf` / EPUB."""
    ptype = product.get("product_type", "")
    if category is None:
        try:
            import product_recipes as pr
            category = pr.get_recipe(ptype).get("category")
        except Exception:
            category = None
    profile_id = profile_for(category, ptype)
    if not profile_id:
        return None
    profile = PROFILES[profile_id]

    clean_body, findings, front_removed = sanitize(product.get("content") or "")
    meta = {
        "title": product.get("title"), "subtitle": product.get("subtitle"),
        "author": product.get("author") or product.get("byline") or "QRU Press™",
        "imprint": product.get("imprint") or "QRU Press", "genre": product.get("family") or "",
        "audience": product.get("audience", ""), "isbn": product.get("isbn"),
    }
    pub_meta, title_page, copyright_page, colophon = build_publication(meta, profile)
    rp = {
        "metadata": pub_meta, "title_page": title_page, "copyright_page": copyright_page,
        "colophon": colophon, "include_governance": profile["include_governance"],
        "include_learning_qr": profile["include_learning_qr"], "profile": profile_id,
        "standard_id": STANDARD["standard_id"],
    }
    if profile["include_governance"]:
        gf = _governance_front(product)
        if gf:
            rp["governance_front"] = gf
    return {"clean_content": clean_body, "retail_publication": rp, "findings": findings,
            "front_matter_removed": front_removed, "profile": profile_id, "applied": True}
