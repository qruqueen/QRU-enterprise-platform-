"""QRU Inheriting Product Recipes™ — KR-driven PDF products (Knowledge-First inheritance).

Workbook, Student Workbook, Instructor Guide and Assessment Pack are manufactured directly from the
verified Knowledge Record via kr_inheritance. Course, Audiobook, Marketing Assets and Product Bundle
are declared but not yet built — surfaced honestly as COMING_SOON (never faked).
"""
import os
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from database import db
from models import gen_id, now_iso
import kr_inheritance as kri
import publishing_standard as ps

INHERITED_DIR = Path(os.environ.get("QRU_INHERITED_DIR", "/app/backend/generated_inherited"))
INHERITED_DIR.mkdir(parents=True, exist_ok=True)

# recipes with a completed builder → manufacturable now
RECIPES = {
    "workbook": {"label": "Workbook", "edition": "Learner Edition", "teacher_notes": False, "answers": False},
    "student_workbook": {"label": "Student Workbook", "edition": "Student Edition", "teacher_notes": False, "answers": False},
    "instructor_guide": {"label": "Instructor Guide", "edition": "Instructor Edition", "teacher_notes": True, "answers": True},
    "assessment_pack": {"label": "Assessment Pack", "edition": "Assessment Edition", "assessment_only": True},
}
# declared future recipes (no builder yet) → honest "Coming Soon"
COMING_SOON = ["course", "audiobook", "marketing", "bundle"]

NAVY = (11, 16, 48)
GOLD = (231, 181, 60)
INK = (42, 37, 64)


def _s(t):
    return str(t or "").encode("latin-1", "replace").decode("latin-1")


class _Doc(FPDF):
    title_line = ""

    def mc(self, *a, **k):
        self.set_x(self.l_margin)
        k.setdefault("new_x", XPos.LMARGIN)
        k.setdefault("new_y", YPos.NEXT)
        return self.multi_cell(*a, **k)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, _s(f"QRU PRESS(TM) - {self.title_line} - Page {self.page_no()}"), align="C")


def _heading(pdf, text, color=NAVY):
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*color)
    pdf.mc(0, 8, _s(text))
    pdf.set_draw_color(*GOLD); pdf.set_line_width(0.5)
    y = pdf.get_y() + 1
    pdf.line(pdf.l_margin, y, pdf.l_margin + 40, y)
    pdf.ln(3)


def _body(pdf, text, size=11):
    pdf.set_font("Helvetica", "", size)
    pdf.set_text_color(*INK)
    pdf.mc(0, 6, _s(text))
    pdf.ln(1)


def _bullets(pdf, items, numbered=False):
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*INK)
    for i, it in enumerate(items, 1):
        prefix = f"{i}.  " if numbered else "-  "
        pdf.mc(0, 6, _s(prefix + str(it)))
    pdf.ln(1)


def _build_pdf(inh, recipe):
    pdf = _Doc()
    pdf.title_line = f"{inh['term'].title()} {recipe['label']}"
    pdf.set_auto_page_break(True, margin=18)
    pdf.set_margins(20, 20, 20)

    # Cover
    pdf.add_page()
    pdf.set_fill_color(*NAVY); pdf.rect(0, 0, 210, 297, "F")
    pdf.set_y(90); pdf.set_font("Helvetica", "B", 34); pdf.set_text_color(255, 255, 255)
    pdf.mc(0, 14, _s(inh["term"].title()), align="C")
    pdf.set_font("Helvetica", "B", 18); pdf.set_text_color(*GOLD)
    pdf.mc(0, 12, _s(recipe["label"].upper()), align="C")
    pdf.set_font("Helvetica", "", 12); pdf.set_text_color(230, 230, 230)
    pdf.mc(0, 8, _s(f"{recipe['edition']}  -  QRU PRESS(TM)"), align="C")
    pdf.set_y(250); pdf.set_font("Helvetica", "", 10); pdf.set_text_color(200, 200, 200)
    pdf.mc(0, 6, _s(f"Manufactured from verified Knowledge Record {inh['kr_code']} v{inh['version']}. Treasure Standard(TM). Quest for Real Understanding(TM)."), align="C")

    pdf.add_page()
    assessment_only = recipe.get("assessment_only")

    if not assessment_only:
        _heading(pdf, "Learning Objectives")
        objs = [f"Understand {inh['term'].lower()} and explain it in your own words."] + \
               [f"Recognise {kp[:80]}" for kp in inh["key_points"][:3]]
        _bullets(pdf, objs)

        _heading(pdf, "Vocabulary")
        _body(pdf, f"{inh['term']}: {inh['definition_plain']}", 11)

        _heading(pdf, "Lesson")
        _body(pdf, inh["definition_professional"])
        if inh["key_points"]:
            _body(pdf, "Key points:")
            _bullets(pdf, inh["key_points"][:5])

        _heading(pdf, "Real-World Examples")
        _bullets(pdf, inh["examples"][:5] or ["See the concept applied in practice."])

        _heading(pdf, "Activities & Exercises")
        _bullets(pdf, [f"Explain: {q}" for q in inh["challenge_questions"][:4]], numbered=True)

        _heading(pdf, "Reflection")
        _bullets(pdf, [f"What did you understand about {inh['term'].lower()} that you didn't before?",
                       "Where could you apply this in real life?",
                       "What question do you still have?"])

    _heading(pdf, "Assessment")
    _bullets(pdf, inh["challenge_questions"][:6], numbered=True)
    if recipe.get("answers"):
        _heading(pdf, "Answer & Facilitation Guidance", GOLD)
        _body(pdf, f"Model understanding centres on: {inh['definition_professional']}")
        if inh.get("misconceptions"):
            _body(pdf, "Watch for these misconceptions:")
            _bullets(pdf, inh["misconceptions"][:4])

    if recipe.get("teacher_notes"):
        _heading(pdf, "Teacher Notes", GOLD)
        _bullets(pdf, [f"Open by connecting {inh['term'].lower()} to a familiar experience.",
                       "Use the real-world examples to build from concrete to abstract.",
                       "Close with the memory sentence below and a reflection prompt."])
        _body(pdf, f"Memory sentence: {inh['memory_sentence']}")

    if not assessment_only:
        _heading(pdf, "Memory Sentence")
        pdf.set_font("Helvetica", "BI", 13); pdf.set_text_color(*NAVY)
        pdf.mc(0, 8, _s(inh["memory_sentence"]), align="C")

    _heading(pdf, "Sources")
    _bullets(pdf, inh["citations"] or [inh["kr_code"]])
    return bytes(pdf.output())


def _quality_gate(inh, recipe):
    checks = []

    def chk(n, ok, d=""):
        checks.append({"check": n, "passed": bool(ok), "detail": d, "severity": "PASSED" if ok else "BLOCKING_FAILURE"})

    chk("Knowledge fidelity (inherits verified KR)", bool(inh.get("kr_id")))
    chk("Definition present", bool(inh["definition_professional"] or inh["definition_plain"]))
    chk("Assessment present", len(inh["challenge_questions"]) > 0)
    chk("No placeholders", not any(t in (inh["definition_professional"] + inh["definition_plain"]).lower() for t in ("lorem", "todo", "{{")))
    chk("Knowledge-First: verified source KR", inh.get("verified_external"), "unverified KR stays INTERNAL_DRAFT")
    blocked = any(c["severity"] == "BLOCKING_FAILURE" for c in checks)
    return {"verdict": "RETURN_TO_PRODUCTION" if blocked else "TREASURE_STANDARD_PASSED", "blocked": blocked,
            "checks": checks, "counts": {"passed": sum(1 for c in checks if c["passed"]), "total": len(checks),
                                         "blocking": sum(1 for c in checks if not c["passed"])}}


async def manufacture(kr_id, recipe_type, actor="Founder", force=False):
    recipe = RECIPES.get(recipe_type)
    if not recipe:
        return {"error": f"Recipe '{recipe_type}' has no completed builder (Coming Soon)." if recipe_type in COMING_SOON else f"Unknown recipe '{recipe_type}'."}
    kr = await kri.load_kr(db, kr_id)
    if not kr:
        return None
    if not force:
        existing = await db.inherited_products.find_one({"kr_id": kr_id, "type": recipe_type}, {"_id": 0})
        if existing:
            return existing
    inh = kri.build_inheritance(kr)
    pdf_bytes = _build_pdf(inh, recipe)
    pid = gen_id()
    (INHERITED_DIR / f"{pid}.pdf").write_bytes(pdf_bytes)
    gate = _quality_gate(inh, recipe)
    status = "VERIFICATION_REQUIRED" if not inh["verified_external"] else ("REVISION_REQUIRED" if gate["blocked"] else "DRAFT")
    rec = {"id": pid, "kr_id": kr_id, "kr_code": inh["kr_code"], "kr_version": inh["version"],
           "type": recipe_type, "label": recipe["label"], "topic": inh["term"].title(),
           "files": [{"format": "pdf", "bytes": len(pdf_bytes), "url": f"/api/media-studio/inherited/{pid}/file"}],
           "verification_status": "VERIFIED_EXTERNAL" if inh["verified_external"] else "PENDING_HUMAN_VERIFICATION",
           "treasure_status": gate["verdict"], "quality_gate": gate, "status": status,
           "provenance": {"source_kr": kr_id, "source_kr_version": inh["version"], "governing_standard": ps.DOC_ID,
                          "by": actor, "at": now_iso()},
           "created_by": actor, "created_at": now_iso(), "updated_at": now_iso()}
    await db.inherited_products.insert_one(dict(rec))
    rec.pop("_id", None)
    return rec


def file_path(pid):
    return INHERITED_DIR / f"{pid}.pdf"


async def manufacture_all(kr_id, actor="Founder"):
    """Manufacture every AVAILABLE recipe for a KR in one pass. Recipes already built for this KR are
    skipped (idempotent). Declared-but-unbuilt archetypes are surfaced honestly as coming_soon."""
    kr = await kri.load_kr(db, kr_id)
    if not kr:
        return None
    existing = set()
    async for i in db.inherited_products.find({"kr_id": kr_id}, {"_id": 0, "type": 1}):
        existing.add(i.get("type"))

    manufactured, skipped = [], []
    for recipe_type in RECIPES:
        if recipe_type in existing:
            skipped.append({"type": recipe_type, "reason": "Already manufactured for this Knowledge Record."})
            continue
        rec = await manufacture(kr_id, recipe_type, actor)
        if isinstance(rec, dict) and rec.get("error"):
            skipped.append({"type": recipe_type, "reason": rec["error"]})
        else:
            manufactured.append({"type": recipe_type, "id": rec["id"], "label": rec["label"],
                                 "status": rec["status"], "treasure_status": rec["treasure_status"]})

    coming_soon = [{"type": t, "reason": "Declared archetype — inheriting recipe not built yet (Coming Soon)."}
                   for t in COMING_SOON]
    return {"kr_id": kr_id, "manufactured": manufactured, "skipped": skipped, "coming_soon": coming_soon,
            "manufactured_count": len(manufactured),
            "philosophy": "Understand Once. Manufacture Forever."}
