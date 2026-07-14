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
    return {"introduction": introduction, "chapters": chapters, "back_matter": back_matter}


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
