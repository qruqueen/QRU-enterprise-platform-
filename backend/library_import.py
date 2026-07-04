"""QRU Bulk Library Import™ — folder → Knowledge Records with dedupe (deterministic, $0 AI).

Knowledge-First rule preserved: content comes ONLY from the imported Founder documents.
No AI generation or hallucination — the extracted text is stored verbatim. Imported records
land as "Imported — Needs Completion" so the Founder structures them via the Promotion
Pipeline™ (Guided Understanding System™) before manufacturing.

Deduplication: normalized content hash + normalized title against existing Knowledge Records
so re-importing the same folder never creates duplicates.
"""
import hashlib
import io
import re

from database import db
from models import gen_id, now_iso, QRU_SECTIONS
import knowledge_extraction as ke

OWNER_ID = "1fac7f6d-8dab-4ae8-bf37-a2ff30fe3c8f"
SUPPORTED = (".txt", ".md", ".markdown", ".docx", ".pdf")


def _ext(name):
    name = (name or "").lower()
    for e in SUPPORTED:
        if name.endswith(e):
            return e
    return None


def extract_text(filename, data):
    """Deterministic text extraction. Returns (text, error)."""
    ext = _ext(filename)
    try:
        if ext in (".txt", ".md", ".markdown"):
            return data.decode("utf-8", errors="ignore"), None
        if ext == ".docx":
            import docx
            doc = docx.Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip()), None
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            return "\n".join((pg.extract_text() or "") for pg in reader.pages), None
        return "", f"Unsupported file type ({filename})."
    except Exception as e:
        return "", f"Could not read {filename}: {str(e)[:120]}"


def _normalize(text):
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _hash(text):
    return hashlib.sha256(_normalize(text).encode("utf-8")).hexdigest()


def _title_from(filename, text):
    for line in (text or "").splitlines():
        s = line.strip().lstrip("# ").strip()
        if 3 <= len(s) <= 120:
            return s
    base = re.sub(r"\.[^.]+$", "", filename or "Untitled")
    return re.sub(r"[_\-]+", " ", base).strip().title() or "Untitled Import"


async def analyze(files):
    """files: list of (filename, bytes). Returns a per-file report (no writes)."""
    report, seen_hashes = [], {}
    for filename, data in files:
        if not _ext(filename):
            report.append({"filename": filename, "status": "unsupported",
                           "reason": "Type not supported (use txt, md, docx, pdf)."})
            continue
        text, err = extract_text(filename, data)
        if err or len(text.strip()) < 40:
            report.append({"filename": filename, "status": "empty",
                           "reason": err or "Too little readable text to import."})
            continue
        h = _hash(text)
        title = _title_from(filename, text)
        # Duplicate within this batch.
        if h in seen_hashes:
            report.append({"filename": filename, "title": title, "status": "duplicate",
                           "chars": len(text), "reason": f"Same content as {seen_hashes[h]} in this batch."})
            continue
        # Duplicate against the existing library.
        dup = await db.knowledge_records.find_one({"$or": [{"import_hash": h}, {"title": title}]})
        if dup:
            report.append({"filename": filename, "title": title, "status": "duplicate",
                           "chars": len(text),
                           "reason": f"Matches existing {dup.get('kr_code') or dup.get('title')}."})
            continue
        seen_hashes[h] = filename
        report.append({"filename": filename, "title": title, "status": "new",
                       "chars": len(text), "hash": h,
                       "preview": text.strip()[:280]})
    return report


async def _next_code():
    n = await db.knowledge_records.count_documents({"kr_code": {"$regex": "^KR-IMP-"}})
    return f"KR-IMP-{n + 1:04d}"


async def commit(files, actor, only_filenames=None):
    """Create Knowledge Records for NEW files (skips duplicates/unsupported). Returns report."""
    report = await analyze(files)
    file_map = {fn: data for fn, data in files}
    created = []
    for item in report:
        if item["status"] != "new":
            continue
        if only_filenames is not None and item["filename"] not in only_filenames:
            item["status"] = "skipped"
            item["reason"] = "Not selected for import."
            continue
        text, _ = extract_text(item["filename"], file_map[item["filename"]])
        excerpt = text.strip()[:600]
        code = await _next_code()
        # MO-043 — Automatic Knowledge Extraction™ (deterministic, structures the source's own text).
        ex = ke.extract_fields(text, item["title"])
        f = ex["fields"] if ex["sufficient"] else {}
        if ex["sufficient"] and ex["required_complete"]:
            rec_class = "Extracted — Founder Review"
            v_status = "Extracted — Needs Founder Review"
            readiness = f"Auto-extracted {ex['extracted_count']} field(s) — review in Promotion Pipeline™"
        elif ex["sufficient"]:
            rec_class = "Extracted — Needs Completion"
            v_status = "Extracted — Needs Completion"
            readiness = f"Auto-extracted {ex['extracted_count']} field(s); complete required fields in Promotion Pipeline™"
        else:
            rec_class = "Imported — Needs Completion"
            v_status = "Needs Completion"
            readiness = "Needs Completion — Structure in Promotion Pipeline™"
        kr = {
            "id": gen_id(), "kr_code": code, "title": item["title"], "subtitle": "",
            "category": "Imported", "division": "Imported Library",
            "verified_truth": f.get("verified_truth", excerpt), "consumer_translation": "", "everyday_analogy": f.get("everyday_analogy", ""),
            "story": "", "memory_sentence": f.get("memory_sentence", ""), "the_question": f.get("the_question", ""), "simple_answer": f.get("simple_answer", excerpt),
            "why_it_matters": f.get("why_it_matters", ""), "real_world_example": f.get("real_world_example", ""),
            "qru_translation": f.get("qru_translation", ""), "deep_roots": f.get("deep_roots", ""),
            "references": [], "sources": [], "practice_activities": [], "key_vocabulary": f.get("key_vocabulary", []),
            "practice_application": [], "tags": f.get("tags", []),
            "audience": "General Public", "level": "Introductory", "product_types": [],
            "imported_text": text.strip(), "import_hash": item["hash"],
            "import_source_file": item["filename"],
            "extraction": {"sufficient": ex["sufficient"], "extracted_count": ex.get("extracted_count", 0),
                           "required_complete": ex.get("required_complete", False), "reason": ex.get("reason")},
            "source_label": "Founder Bulk Import", "record_class": rec_class,
            "readiness": readiness,
            "confidence_score": 0, "verification_status": v_status,
            "approval_status": "Founder Imported", "reviewer": actor,
            "is_master_file": False, "treasure_standard": False, "treasure_standard_status": "Pending",
            "understanding_status": "Not Manufactured", "promotion_ready": True,
            "owner_id": OWNER_ID, "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
            "products_created": 0, "version": 1, "verification": None, "customer_facing": True,
        }
        kr["section_status"] = {s: ("Draft" if kr.get(s) else "Empty") for s in QRU_SECTIONS}
        await db.knowledge_records.insert_one(dict(kr))
        item["status"] = "imported"
        item["kr_code"] = code
        item["extracted_count"] = ex.get("extracted_count", 0)
        created.append({"kr_code": code, "title": item["title"], "id": kr["id"],
                        "extracted_count": ex.get("extracted_count", 0)})
    return {"report": report, "created": created,
            "created_count": len(created),
            "duplicate_count": sum(1 for r in report if r["status"] == "duplicate"),
            "skipped_count": sum(1 for r in report if r["status"] in ("skipped", "empty", "unsupported"))}
