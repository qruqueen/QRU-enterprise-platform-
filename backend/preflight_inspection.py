"""QRU Automated Pre-Review Inspection™ (STD-INSPECT-0001).

Read-only. Runs EVERY automatable quality check against a manufactured document and returns ONE
consolidated exception list so the Founder reviews only what is flagged — never every word.

CONSTITUTIONAL RULE (Treasure Standard™): this module INSPECTS and REPORTS. It NEVER rewrites,
corrects, or mutates the product. Author voice, teaching effectiveness, reader experience and final
approval remain Founder judgment and are deliberately NOT scored here.

Severity buckets:
  • blocking     — must be resolved before publication (real defects / mismatches)
  • recommended  — should be reviewed; not a hard stop
  • advisory     — informational / stylistic; Founder's call
"""
import re
from datetime import datetime, timezone

import book_structure as bs
import publication_quality as pq
import book_manufacturing as _bm

STANDARD_ID = "STD-INSPECT-0001"
STANDARD_NAME = "QRU Automated Pre-Review Inspection™"

_URL_RE = re.compile(r"https?://[^\s)\]}>\"']+", re.I)
# Domain / brand terms that a general spell checker would falsely flag.
_ALLOWLIST = {
    "qru", "ukr", "pms", "pmf", "treasure", "storefront", "audiobook", "ebook", "epub", "pdf",
    "kdp", "isbn", "colophon", "workbook", "homeschool", "metadata", "dataset", "datasets",
    "chatbot", "chatbots", "generative", "algorithmic", "misinformation", "cybersecurity",
    "biometric", "wellbeing", "decarbonization", "neuroplasticity",
}
_spell = None


def _speller():
    global _spell
    if _spell is None:
        try:
            from spellchecker import SpellChecker
            _spell = SpellChecker(distance=1)
        except Exception:
            _spell = False
    return _spell


def _now():
    return datetime.now(timezone.utc).isoformat()


def _finding(fid, label, severity, detail, examples=None):
    return {"id": fid, "label": label, "severity": severity, "detail": detail,
            "examples": examples or []}


# ---------------------------------------------------------------------------
# Individual inspectors — each returns (passed: bool, finding_or_None).
# ---------------------------------------------------------------------------
def _inspect_placeholders(content):
    hits = pq.detect_placeholders(content)
    if not hits:
        return True, None
    ex = [f"{h['marker']}: “{h['text']}”" for h in hits[:6]]
    return False, _finding("placeholders", "Internal / draft placeholders present", "blocking",
                           f"{len(hits)} internal marker(s) would reach a reader-facing page (working title, TK, TODO, DRAFT, etc.).", ex)


def _inspect_repeated_words(content):
    hits = list(re.finditer(r"\b(\w+)(\s+)\1\b", content, flags=re.IGNORECASE))
    if not hits:
        return True, None
    ex = [f"“…{content[max(0, m.start()-15):m.end()+15].strip()}…”" for m in hits[:6]]
    return False, _finding("repeated_words", "Repeated consecutive words", "recommended",
                           f"{len(hits)} duplicate consecutive word(s) detected (e.g. “the the”).", ex)


def _inspect_spacing(content):
    dbl = content.count("  ")
    if not dbl:
        return True, None
    return False, _finding("double_spaces", "Double spaces", "advisory",
                           f"{dbl} double-space occurrence(s) — collapse for clean typesetting.")


def _inspect_structure(content):
    structure = bs.parse_book(content)
    chapters = structure.get("chapters", [])
    problems = []
    if not chapters:
        try:
            units = bs.content_units(content)
        except Exception:
            units = []
        if not units:
            return False, _finding("structure", "No chapter/section structure detected", "recommended",
                                   "The manuscript has no detectable chapters or parts — verify headings.")
        return True, None
    nums = [c.get("number") for c in chapters]
    if nums and nums != list(range(1, len(nums) + 1)):
        problems.append("chapter numbering is not strictly sequential")
    empty = [c for c in chapters if len((c.get("content") or "").split()) < 15]
    if empty:
        problems.append(f"{len(empty)} chapter(s) look nearly empty (<15 words)")
    if not problems:
        return True, None
    return False, _finding("structure", "Structural issues", "recommended",
                           "; ".join(problems).capitalize() + ".",
                           [f"Chapter {c.get('number')}: {c.get('title','')}" for c in empty[:5]])


def _inspect_frontmatter(content):
    if "copyright" in (content or "").lower():
        return True, None
    return False, _finding("frontmatter", "No copyright line in manuscript", "advisory",
                           "The Publication Quality Standard™ will inherit copyright at publish; confirm the rights holder.")


def _inspect_links(content):
    urls = _URL_RE.findall(content or "")
    if not urls:
        return True, None
    malformed = [u for u in urls if u.count("://") != 1 or " " in u or u.endswith((".", ",")) or len(u) < 12]
    if malformed:
        return False, _finding("links", "Malformed link(s)", "recommended",
                               f"{len(malformed)} link(s) look malformed. (Network reachability is NOT checked here.)",
                               malformed[:6])
    return True, _finding("links", f"{len(urls)} link(s) present", "advisory",
                          "Link formats look valid. Network reachability is not verified automatically.")


def _inspect_spelling(content):
    sp = _speller()
    if not sp:
        return True, _finding("spelling", "Spelling inspection unavailable", "advisory",
                              "Spell-checker not installed; skipped.")
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", content or "")
    checked, seen = [], set()
    for w in words[:8000]:
        if w[0].isupper():  # skip likely proper nouns
            continue
        lw = w.lower().strip("'-")
        if lw in _ALLOWLIST or lw in seen or len(lw) < 3:
            continue
        seen.add(lw)
        checked.append(lw)
    unknown = sorted(sp.unknown(checked)) if checked else []
    unknown = [u for u in unknown if u not in _ALLOWLIST][:40]
    if not unknown:
        return True, None
    return False, _finding("spelling", "Possible spelling issues", "advisory",
                           f"{len(unknown)} word(s) were not recognized (may include valid domain terms — Founder confirms).",
                           unknown[:20])


def _inspect_content_integrity(title, subtitle, content):
    ci = _bm.content_integrity_check(title, subtitle, content)
    if ci.get("ok", True):
        return True, None
    return False, _finding("content_integrity", "Content–subject mismatch", "blocking",
                           ci.get("message", "The body does not match the title's subject."),
                           [f"Factory-term density: {ci.get('factory_term_density_per_1000w')}/1000 words"])


# ---------------------------------------------------------------------------
# Public entry — inspect assembled document text.
# ---------------------------------------------------------------------------
def inspect_document(*, title, subtitle, author, content, metadata=None):
    """Run all automatable inspectors on a document. Pure/deterministic, $0, read-only."""
    metadata = metadata or {}
    content = content or ""
    words = len(content.split())

    checks = []

    def run(passed, finding):
        checks.append(finding if finding else {"severity": "pass"})
        return passed, finding

    inspectors = [
        _inspect_content_integrity(title, subtitle, content),
        _inspect_placeholders(content),
        _inspect_repeated_words(content),
        _inspect_spacing(content),
        _inspect_structure(content),
        _inspect_frontmatter(content),
        _inspect_links(content),
        _inspect_spelling(content),
    ]

    findings = [f for (_ok, f) in inspectors if f and f.get("severity") != "pass"]

    # Metadata completeness (publication readiness).
    missing = [k for k in ("title", "author") if not (metadata.get(k) or (title if k == "title" else author))]
    if not (metadata.get("price") or metadata.get("priced")):
        missing.append("price")
    if not metadata.get("cover_selected", True):
        missing.append("cover")
    if missing:
        findings.append(_finding("metadata", "Incomplete publication metadata", "recommended",
                                 f"Missing before publish: {', '.join(missing)}.", missing))

    buckets = {"blocking": 0, "recommended": 0, "advisory": 0}
    for f in findings:
        buckets[f["severity"]] = buckets.get(f["severity"], 0) + 1

    return {
        "standard_id": STANDARD_ID, "standard_name": STANDARD_NAME,
        "generated_at": _now(),
        "read_only": True,
        "never_rewrites": True,
        "words": words,
        "summary": {
            "clean": len(findings) == 0,
            "blocking": buckets["blocking"], "recommended": buckets["recommended"],
            "advisory": buckets["advisory"], "total_exceptions": len(findings),
            "publish_ready": buckets["blocking"] == 0,
        },
        "exceptions": findings,
        "founder_judgment": [
            "Author voice & tone", "Teaching effectiveness", "Reader experience",
            "Cover aesthetic & brand fit", "Pricing decision", "Final authorization",
        ],
        "note": ("Automated inspection reports exceptions only and never rewrites the product. "
                 "Voice, teaching quality and final approval remain your judgment."),
    }


async def inspect_book(book_id):
    """Inspect a Canonical Book Record (read-only). Returns the exception report or {error}."""
    from database import db
    b = await db.book_records.find_one({"id": book_id}, {"_id": 0}) \
        or await db.book_records.find_one({"book_code": book_id}, {"_id": 0})
    if not b:
        return {"error": "Book not found."}
    content = (b.get("editorial_edition") or b.get("working_copy") or {}).get("content") or ""
    design = (b.get("artifacts", {}) or {}).get("design", {}) or {}
    metadata = {
        "title": b.get("title"), "author": b.get("author"),
        "priced": bool((b.get("pricing") or {}).get("approved")),
        "cover_selected": bool(design.get("selected_cover")),
    }
    report = inspect_document(
        title=b.get("title"), subtitle=b.get("subtitle"), author=b.get("author"),
        content=content, metadata=metadata)
    report["product"] = {"id": b.get("id"), "book_code": b.get("book_code"), "title": b.get("title")}
    return report
