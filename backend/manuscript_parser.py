"""QRU Manuscript Structure Detector™ — deterministic (no AI).

Turns an uploaded DOCX / text-based PDF / TXT / MD into governed markdown where:
  `# `   → book title
  `## `  → chapter (Heading 1 / Chapter N / Prologue / Part / Epilogue / page-break unit)
  `### ` → section (Heading 2 / title-case sub-heading)

It also produces a read-only structure-confidence report for the Upload panel. Original files are
never modified — this only reads bytes and emits a working markdown string.
"""
import io
import re

# ---- shared heading heuristics -------------------------------------------------
_CHAPTER_KW = r"(chapter|part|prologue|epilogue|book|section|act|volume|interlude|appendix|foreword|preface|introduction|conclusion|afterword)"
_CHAPTER_RE = re.compile(rf"^\s*{_CHAPTER_KW}\b", re.IGNORECASE)
_NUMBERED_RE = re.compile(r"^\s*(\d{1,3})[\.\):]?\s+\S")            # "1. Title" / "12) Title"
_ROMAN_RE = re.compile(r"^\s*(part\s+)?[ivxlcdm]{1,7}\b[\.\):—-]?\s*", re.IGNORECASE)
_BARE_NUM_RE = re.compile(r"^\s*\d{1,4}\s*$")                       # standalone page number
_SENT_END = tuple(".?!:;,")


def _looks_like_chapter(text):
    t = (text or "").strip()
    if not t or len(t) > 90:
        return False
    if _CHAPTER_RE.match(t):
        return True
    if _NUMBERED_RE.match(t) and len(t) <= 80:
        return True
    return False


def _looks_like_section(text, next_text=""):
    """Conservative title-case sub-heading detector for un-styled manuscripts."""
    t = (text or "").strip()
    if not t or len(t) > 72 or t.endswith(_SENT_END):
        return False
    words = [w for w in re.split(r"\s+", t) if w]
    if len(words) < 2 or len(words) > 12:
        return False
    # Title Case: most significant words start uppercase
    signif = [w for w in words if len(w) > 3]
    if signif and sum(1 for w in signif if w[0].isupper()) / len(signif) < 0.6:
        return False
    # a real heading is usually followed by a longer body line
    if next_text and len(next_text.strip()) < 25:
        return False
    return True


def _title_case(text):
    return re.sub(r"\s+", " ", (text or "").strip())


# ---- DOCX ----------------------------------------------------------------------
def _para_has_page_break(p):
    try:
        xml = p._element.xml
        return ('w:type="page"' in xml) or ("lastRenderedPageBreak" in xml)
    except Exception:
        return False


def docx_to_markdown(raw_bytes):
    from docx import Document
    doc = Document(io.BytesIO(raw_bytes))
    paras = [{"text": (p.text or "").strip(),
              "style": ((p.style.name or "").lower() if p.style is not None else ""),
              "pb": _para_has_page_break(p)} for p in doc.paragraphs]
    nonempty = [p for p in paras if p["text"]]

    out, method_bits = [], set()
    title_set = False
    core_title = ""
    try:
        core_title = (doc.core_properties.title or "").strip()
    except Exception:
        core_title = ""
    if core_title:
        out.append(f"# {_title_case(core_title)}")
        title_set = True
        method_bits.add("core-properties title")

    # Title block: leading un-styled short lines before the first real heading/chapter.
    first_heading_idx = None
    for i, p in enumerate(nonempty):
        if ("heading" in p["style"] or "title" in p["style"]) or _looks_like_chapter(p["text"]):
            first_heading_idx = i
            break
    lead = nonempty[:first_heading_idx] if first_heading_idx is not None else []

    consumed_title_line = False
    for idx, p in enumerate(paras):
        t, style, pb = p["text"], p["style"], p["pb"]
        if not t:
            out.append("")
            continue
        nxt = ""
        for q in paras[idx + 1:]:
            if q["text"]:
                nxt = q["text"]; break

        # --- title (only the very first qualifying leading line) ---
        if not title_set and not consumed_title_line and p in lead:
            if "title" in style or (idx == next((j for j, x in enumerate(paras) if x["text"]), 0)):
                out.append(f"# {_title_case(t)}")
                title_set = True; consumed_title_line = True
                method_bits.add("title-style" if "title" in style else "leading title line")
                continue

        # --- styled headings (most reliable) ---
        if re.search(r"heading\s*1", style) or style == "heading":
            out.append(f"## {t}"); method_bits.add("Word Heading styles"); continue
        if re.search(r"heading\s*[2-9]", style):
            out.append(f"### {t}"); method_bits.add("Word Heading styles"); continue

        # --- pattern chapters (Chapter/Part/Prologue/Epilogue/numbered) ---
        if _looks_like_chapter(t):
            out.append(f"## {t}"); method_bits.add("chapter keyword/number patterns"); continue

        # --- page-break unit: short line right after a page break ---
        if pb and len(t) <= 80 and not t.endswith(_SENT_END) and len(t.split()) <= 12:
            out.append(f"## {t}"); method_bits.add("page-break structure"); continue

        # --- title-case sub-heading → section ---
        if _looks_like_section(t, nxt):
            out.append(f"### {t}"); method_bits.add("title-case section detection"); continue

        out.append(t)

    return "\n\n".join(out), {"method": ", ".join(sorted(method_bits)) or "plain text",
                              "source": "docx"}


# ---- PDF -----------------------------------------------------------------------
def _dominant_size(pages_lines):
    from collections import Counter
    c = Counter()
    for lines in pages_lines:
        for ln in lines:
            c[ln["size"]] += len(ln["text"])
    return (c.most_common(1)[0][0] if c else 12.0)


def pdf_to_markdown(raw_bytes):
    warnings = []
    try:
        import pdfplumber
    except Exception:
        return _pdf_fallback(raw_bytes) + (["pdfplumber unavailable — used basic text extraction"],)

    pages_lines = []
    total_chars = 0
    with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
        n_pages = len(pdf.pages)
        for pg in pdf.pages:
            lines = []
            try:
                raw_lines = pg.extract_text_lines(extra_attrs=["size"]) or []
            except Exception:
                raw_lines = []
            for ln in raw_lines:
                txt = re.sub(r"\s+", " ", (ln.get("text") or "").strip())
                if not txt:
                    continue
                szs = [c.get("size", 0) for c in ln.get("chars", [])]
                lines.append({"text": txt, "size": round(max(szs), 1) if szs else 0,
                              "top": ln.get("top", 0)})
                total_chars += len(txt)
            pages_lines.append(lines)

    if total_chars < 40 * max(1, n_pages) and total_chars < 400:
        return ("", {"method": "none", "source": "pdf", "scanned": True},
                [f"This looks like a SCANNED PDF (only {total_chars} characters of embedded text "
                 f"across {n_pages} pages). OCR is required — automatic OCR is not performed."])

    body = _dominant_size(pages_lines)
    # detect repeating running headers/footers + page numbers
    from collections import Counter
    edge = Counter()
    for lines in pages_lines:
        if not lines:
            continue
        edge[lines[0]["text"].lower()] += 1
        edge[lines[-1]["text"].lower()] += 1
    repeating = {t for t, n in edge.items() if n >= max(3, int(0.3 * n_pages))}

    heading_sizes = sorted({ln["size"] for lines in pages_lines for ln in lines if ln["size"] >= body * 1.25}, reverse=True)
    title_size = heading_sizes[0] if heading_sizes else None

    out, method_bits, dropped = [], set(), 0
    title_set = False
    for lines in pages_lines:
        for pos, ln in enumerate(lines):
            t, sz = ln["text"], ln["size"]
            low = t.lower()
            if _BARE_NUM_RE.match(t) or re.match(r"^\s*page\s+\d+", low):
                dropped += 1; method_bits.add("stripped page numbers"); continue
            if low in repeating and (pos == 0 or pos == len(lines) - 1):
                dropped += 1; method_bits.add("stripped running headers/footers"); continue
            if title_size and sz >= title_size and not title_set and len(t) <= 90:
                out.append(f"# {_title_case(t)}"); title_set = True
                method_bits.add("font-size title"); continue
            if sz >= body * 1.25 and len(t) <= 90:
                out.append(f"## {t}"); method_bits.add("font-size chapter detection"); continue
            if _looks_like_chapter(t) and sz >= body:
                out.append(f"## {t}"); method_bits.add("chapter keyword/number patterns"); continue
            out.append(t)
        out.append("")

    md = _reflow(out)
    if dropped:
        warnings.append(f"Removed {dropped} running header/footer/page-number line(s).")
    return md, {"method": ", ".join(sorted(method_bits)) or "font-size analysis", "source": "pdf"}, warnings


def _pdf_fallback(raw_bytes):
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
    text = "\n\n".join((pg.extract_text() or "") for pg in reader.pages).strip()
    return text, {"method": "basic text extraction", "source": "pdf"}


def _reflow(lines):
    """Merge consecutive body lines into paragraphs; keep heading lines standalone."""
    md, buf = [], []

    def flush():
        if buf:
            md.append(" ".join(buf).strip()); buf.clear()

    for ln in lines:
        s = ln.strip()
        if s.startswith(("#", "##", "###")) or s == "":
            flush()
            md.append(s)
        else:
            buf.append(s)
    flush()
    # collapse multiple blank lines
    res = []
    for s in md:
        if s == "" and res and res[-1] == "":
            continue
        res.append(s)
    return "\n\n".join(x for x in res if x != "") if False else "\n".join(res)


# ---- unified entry + confidence report ----------------------------------------
def extract_markdown(filename, raw):
    name = (filename or "").lower()
    warnings = []
    if name.endswith(".docx"):
        md, meta = docx_to_markdown(raw)
    elif name.endswith(".pdf"):
        md, meta, warnings = pdf_to_markdown(raw)
    elif name.endswith((".txt", ".md", ".markdown", ".text")):
        md, meta = raw.decode("utf-8", errors="replace"), {"method": "manual markdown (## / ###)", "source": "text"}
    else:
        md, meta = raw.decode("utf-8", errors="replace"), {"method": "plain text", "source": "text"}
    meta["warnings"] = warnings
    return md, meta


def analyze_structure(markdown, meta=None):
    """Deterministic confidence report for the Upload panel."""
    meta = meta or {}
    lines = (markdown or "").split("\n")
    title, chapters, sections, warnings = "", [], 0, list(meta.get("warnings") or [])
    for ln in lines:
        s = ln.strip()
        if s.startswith("### "):
            sections += 1
        elif s.startswith("## "):
            chapters.append(s[3:].strip())
        elif s.startswith("# ") and not title:
            title = s[2:].strip()
    if meta.get("scanned"):
        return {"title": title, "chapter_count": 0, "section_count": 0,
                "method": "none — scanned PDF", "preview": [], "warnings": warnings,
                "confidence": "none",
                "confidence_note": "Scanned image PDF — OCR required before manufacturing (not performed automatically)."}

    word_count = len(re.findall(r"\S+", re.sub(r"^#+\s.*$", "", markdown, flags=re.M)))
    if not chapters:
        confidence = "low"
        warnings.append("No chapters detected. Add '## ' before each chapter heading, or re-export with heading styles.")
    elif len(chapters) == 1 and word_count > 3000:
        confidence = "medium"
        warnings.append("Only one chapter detected in a long manuscript — verify chapter breaks.")
    else:
        confidence = "high"
    return {
        "title": title or "(no title detected)",
        "chapter_count": len(chapters),
        "section_count": sections,
        "method": meta.get("method", "n/a"),
        "preview": chapters[:12],
        "warnings": warnings,
        "confidence": confidence,
        "confidence_note": {
            "high": "Structure detected with high confidence.",
            "medium": "Structure detected — please spot-check the chapter breaks.",
            "low": "Weak structure — review before proofing (manual '## ' headings always work).",
        }[confidence],
    }
