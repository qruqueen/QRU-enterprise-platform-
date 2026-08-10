"""QRU Public Family/Collection™ — storefront-facing cross-format product grouping.

Surfaces the Factory's own Product Family Assembly™ records (db.product_families, written by
family_assembly.assemble() via routers/family.py) as the storefront's "same underlying work, many
formats" concept — e.g. "The Understanding Tree Collection" = the Book + Workbook + Teacher Guide
the Founder manufactured together, in one action, from one Verified source (see manufacturing_intents.py:
the "classroom" intent literally produces ["Book", "Workbook", "Teacher Guide"]).

This is deliberately NOT a new taxonomy: it reads the existing, explicit grouping the Factory
already records at manufacture time. No new field on book_records/db.products, no schema change.

Distinct from subject (public_subject.py): subject is "what domain is this about" (many unrelated
products can share a subject); family is "what else was manufactured from the exact same source in
the exact same Founder action" (usually a small, deliberate set). Both are supported side by side.

Resolution keys (traced from family_assembly.py / decoder_engine.create_product_from_decoder):
  - A Book family member's assemble() result carries book_id -> resolves via db.book_records.id.
  - Every other family member goes through the decoder bridge's "publication" engine, which inserts
    directly into db.products with id == the assemble() result's own "id" -> resolves via
    db.products.id directly (no source_engine/source_id indirection for this path).
A family of exactly one successfully-manufactured item isn't a customer-facing collection, so
single-item families are excluded here.

No module-level `database` import, on purpose — same discipline as public_subject.py/
public_pathway.py: everything except the one query in load_index() is a pure function, directly
unit-testable with hand-built db.product_families-shaped rows and no live Mongo connection.
"""


def _build_index(rows: list[dict]) -> dict:
    """Pure. Turns raw db.product_families rows into the lookup shape family_for_book()/
    family_for_product() read. Split out from load_index() so it's testable without a DB."""
    by_book, by_product, summaries = {}, {}, {}
    for rec in rows:
        ok_items = [it for it in (rec.get("items") or []) if it.get("ok")]
        if len(ok_items) < 2:
            continue
        fam_id = rec.get("id")
        if not fam_id:
            continue
        summaries[fam_id] = {"id": fam_id, "code": rec.get("family_code"), "title": rec.get("title")}
        for it in ok_items:
            if it.get("book_id"):
                by_book[it["book_id"]] = fam_id
            elif it.get("id"):
                by_product[it["id"]] = fam_id
    return {"by_book": by_book, "by_product": by_product, "summaries": summaries}


async def load_index() -> dict:
    """One batched query for the whole request — never call this per item. Returns
    {"by_book": {book_id: family_id}, "by_product": {product_id: family_id},
     "summaries": {family_id: {"id", "code", "title"}}}."""
    from database import db
    rows = await db.product_families.find({}, {"_id": 0}).to_list(500)
    return _build_index(rows)


def family_for_book(index: dict, book_id: str) -> dict | None:
    fam_id = index["by_book"].get(book_id) if book_id else None
    return index["summaries"].get(fam_id) if fam_id else None


def family_for_product(index: dict, product_id: str) -> dict | None:
    fam_id = index["by_product"].get(product_id) if product_id else None
    return index["summaries"].get(fam_id) if fam_id else None


EMPTY_INDEX = {"by_book": {}, "by_product": {}, "summaries": {}}
