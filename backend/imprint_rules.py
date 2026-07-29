"""QRU Imprint Governance™ — the single source of truth for imprint + genre classification.

Two imprints, one rule each (Treasure Standard™, deterministic, $0):
  • E.Q. Rothwell™ — the LITERARY imprint. Author: E.Q. Rothwell.
  • QRU Press™     — the EDUCATIONAL / INSTITUTIONAL imprint. Author: QRU Editorial (or explicitly assigned).

Used by (a) the Authorization QA gate (blocks publishing an Imprint Mismatch until the Founder
corrects it or explicitly overrides) and (b) the Imprint Canonicalization production operation.
"""
import re

EQ_ROTHWELL = "E.Q. Rothwell™"
QRU_PRESS = "QRU Press™"
EQ_AUTHOR = "E.Q. Rothwell"
DEFAULT_EDU_AUTHOR = "QRU Editorial"

# Canonical literary titles (normalized-prefix match) → default to E.Q. Rothwell™.
LITERARY_TITLES = ["the understanding tree", "ordinary tuesdays", "patterns of intelligence"]

# Cosmetic / file-name tokens stripped before matching a title.
_STRIP = re.compile(
    r"\b(full manuscript|final publishing master|publishing master|final|master|largeprint|"
    r"large print|draft|working title|v\d+)\b", re.I)
_DATE = re.compile(r"\b\d{1,4}[.\-/]\d{1,2}[.\-/]\d{1,4}\b")


def normalize_title(title: str) -> str:
    t = (title or "").lower()
    t = _DATE.sub(" ", t)
    t = _STRIP.sub(" ", t)
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_literary(title: str) -> bool:
    n = normalize_title(title)
    return any(n == lit or n.startswith(lit + " ") or n.startswith(lit) for lit in LITERARY_TITLES)


def expected_imprint(title: str) -> str:
    return EQ_ROTHWELL if is_literary(title) else QRU_PRESS


def expected_author(book: dict) -> str:
    """Literary titles are authored by E.Q. Rothwell; educational titles keep an explicitly
    assigned author, otherwise default to QRU Editorial. Author is never inferred FROM the imprint."""
    if is_literary(book.get("title")):
        return EQ_AUTHOR
    cur = (book.get("author") or "").strip()
    return cur or DEFAULT_EDU_AUTHOR


def canonical_genre(book: dict) -> str:
    """Permanent genre category: Literary Fiction / Educational / Science / Legal / Finance."""
    if is_literary(book.get("title")):
        return "Literary Fiction"
    blob = f"{book.get('title','')} {book.get('genre','')} {book.get('subtitle','')}".lower()
    if any(k in blob for k in ["law", "legal", "contractor", "compliance", "statute", "regulation"]):
        return "Legal"
    if any(k in blob for k in ["trading", "finance", "financial", "budget", "money", "invest",
                               "market", "day trading", "economic"]):
        return "Finance"
    if any(k in blob for k in ["brain", "heart", "sleep", "biolog", "science", "scientific",
                               "health", "memory", "network", "nervous", "circulation", "neuro"]):
        return "Science"
    return "Educational"


def imprint_compliance(book: dict) -> dict:
    """Return the imprint-governance verdict for a book_record.
    `mismatch` = the assigned imprint contradicts the rule (the QA gate blocks on this)."""
    title = book.get("title") or ""
    exp = expected_imprint(title)
    actual = (book.get("canonical_imprint") or book.get("imprint") or "").strip()
    return {
        "ok": actual == exp,
        "expected": exp,
        "actual": actual or None,
        "mismatch": bool(actual) and actual != exp,
        "is_literary": is_literary(title),
        "rule": ("Literary titles publish under E.Q. Rothwell™."
                 if is_literary(title) else
                 "Educational / institutional titles publish under QRU Press™."),
    }
