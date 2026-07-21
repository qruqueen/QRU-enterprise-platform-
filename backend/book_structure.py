"""QRU Reading Experience Standard™ (STD-READ-0001) — the Product Recipe owns the reading experience.

One governed book structure, inherited by every book automatically:
  Front Matter  →  Introduction  →  Chapters  →  Sections  →  Back Matter

Navigation (Table of Contents) is manufactured as a learning journey — never a bulleted list of headings.
Instructional content and navigation structure are kept strictly separate. Strengthen the Recipe,
never the individual book.
"""
import re

STANDARD_ID = "STD-READ-0001"

# Headings that belong to FRONT matter (orientation, not instruction).
_FRONT = ["table of contents", "contents", "copyright", "disclaimer", "dedication",
          "foreword", "preface", "acknowledg", "how to use this book", "colophon"]
# Headings that belong to BACK matter (reference, not instruction).
_BACK = ["references", "bibliography", "glossary", "appendix", "index",
         "about the author", "about qru", "further reading", "answer key", "resources"]
_INTRO = ["introduction", "welcome"]


def _clean(s):
    return re.sub(r"\s+", " ", (s or "").lstrip("#").strip())


def classify_heading(title):
    t = _clean(title).lower()
    if any(k in t for k in _INTRO):
        return "introduction"
    if any(k in t for k in _FRONT):
        return "front"
    if any(k in t for k in _BACK):
        return "back"
    return "chapter"


def strip_navigation(content):
    """Remove any content-embedded Table of Contents (recipe owns navigation, not the body)."""
    lines = (content or "").split("\n")
    out, skipping = [], False
    for line in lines:
        st = line.strip()
        is_heading = st.startswith("#")
        if is_heading:
            title = _clean(st).lower()
            if "table of contents" in title or title == "contents":
                skipping = True
                continue
            skipping = False
            out.append(line)
            continue
        if skipping:
            continue
        out.append(line)
    return "\n".join(out)


def parse_book(content):
    """Return the governed reading structure derived from the instructional content.
    `## ` → Chapter, `### ` → Section (numbered N.M). Front/back headings are set aside."""
    lines = strip_navigation(content).split("\n")
    introduction = None
    chapters, back_matter = [], []
    current = None
    chap_num = 0
    for line in lines:
        st = line.strip()
        if st.startswith("### "):
            title = _clean(st)
            if current is not None:
                n = len(current["sections"]) + 1
                current["sections"].append({"number": f"{current['number']}.{n}", "title": title})
        elif st.startswith("## "):
            title = _clean(st)
            kind = classify_heading(title)
            if kind == "chapter":
                chap_num += 1
                current = {"number": chap_num, "title": title, "sections": []}
                chapters.append(current)
            else:
                current = None
                if kind == "introduction" and not introduction:
                    introduction = title
                elif kind == "back":
                    back_matter.append(title)
    # Fallback: books structured with `# Part …` (or level-1 divisions) previously parsed as
    # 0 chapters. Recover them as governed units so audio/timing/TOC all work.
    if not chapters:
        for u in content_units(content):
            chapters.append({"number": u["number"], "title": u["title"], "sections": [],
                             "unit_word": u["unit_word"]})
    return {"introduction": introduction, "chapters": chapters, "back_matter": back_matter}


_UNIT_KEYWORDS = ("part", "chapter", "book", "section", "act", "volume",
                  "movement", "unit", "module", "lesson", "phase", "stage", "chapters")


def _unit_word(title):
    """The structural noun a division is titled with, e.g. 'Part', 'Chapter', else None."""
    t = _clean(title).lower()
    for k in _UNIT_KEYWORDS:
        if t == k or t.startswith(k + " ") or t.startswith(k + ":"):
            return k.capitalize()
    return None


def content_units(content):
    """Robustly detect the book's primary structural divisions and their body text.
    Handles books built with `## Chapter` (default) AND books built with `# Part …` or
    `## Part …` (which previously parsed as 0 chapters). Returns
    [{number, title, unit_word, body}] where unit_word is 'Chapter'/'Part'/… .
    - Prefer `## ` content headings (classified as chapter). If none exist, fall back to
      `# ` level-1 divisions (dropping a lone leading book-title heading)."""
    lines = strip_navigation(content or "").split("\n")

    def collect(prefix):
        units, cur = [], None
        for line in lines:
            st = line.strip()
            if st.startswith(prefix + " ") and not st.startswith(prefix + "# "):
                title = _clean(st)
                if classify_heading(title) != "chapter":
                    cur = None
                    continue
                cur = {"title": title, "body": []}
                units.append(cur)
            elif cur is not None and st and st != "---":
                cur["body"].append(st.lstrip("#").strip() if st.startswith("#") else st)
        return units

    units = collect("##")
    if not units:
        u1 = collect("#")
        unit_titled = [u for u in u1 if _unit_word(u["title"])]
        if unit_titled:
            # Explicit Part/Chapter/… divisions exist → use only those (drops the book-title heading).
            u1 = unit_titled
        elif u1:
            # No explicit unit words → the first `# ` is the book title; the rest are divisions.
            u1 = u1[1:]
        units = u1

    out = []
    for i, u in enumerate(units, 1):
        out.append({"number": i, "title": u["title"], "unit_word": _unit_word(u["title"]) or "Chapter",
                    "body": " ".join(u["body"]).strip()})
    return out


def toc_entries(structure, front_matter_items):
    """Flat, ordered, reader-facing TOC as a learning journey (grouped, never a raw heading dump)."""
    groups = []
    if front_matter_items:
        groups.append(("Front Matter", [{"label": x} for x in front_matter_items]))
    lead = []
    if structure.get("introduction"):
        lead.append({"label": "Introduction"})
    if lead:
        groups.append(("", lead))
    chap_rows = []
    for c in structure["chapters"]:
        chap_rows.append({"label": f"Chapter {c['number']}", "title": c["title"],
                          "sections": [{"num": s["number"], "title": s["title"]} for s in c["sections"]]})
    if chap_rows:
        groups.append(("Chapters", chap_rows))
    if structure["back_matter"]:
        groups.append(("Back Matter", [{"label": x} for x in structure["back_matter"]]))
    return groups
