"""Publishing-lineage engine validation against a scratch DB (no impact on preview data).
Covers: checksum match (SAME_BOOK), 'FINAL' title correction (TITLE_CHANGED/SAME_BOOK, adopt),
and a genuinely different work sharing a per-DB book_code (DIFFERENT_WORK, no adopt)."""
import asyncio, json, os
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from motor.motor_asyncio import AsyncIOMotorClient
import prod_migrations as pm

STAGE1 = json.load(open("/app/backend/migrations_data/data_stage1_books.json"))
B13 = next(b for b in STAGE1 if b["book_code"] == "BOOK-0013")   # Patterns of Intelligence
B16 = next(b for b in STAGE1 if b["book_code"] == "BOOK-0016")   # The brain as a changing network
PTR = {p["book_code"]: p for p in json.load(open("/app/backend/migrations_data/data_stage2_pointers.json"))}
INC13_CK = (B13.get("original") or {}).get("checksum")


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    scratch = client["scratch_conflict_test"]
    await scratch.book_records.delete_many({})
    await scratch.book_purchases.delete_many({})

    # Case A — BOOK-0013 exists under a DIFFERENT id, SAME sealed checksum, title with "FINAL",
    # blank author, source filename "...FINAL.docx" (the real production scenario).
    await scratch.book_records.insert_one({
        "id": "PROD-DIFF-13", "book_code": "BOOK-0013",
        "title": "Patterns of Intelligence FINAL", "author": "",
        "publication_status": "Published",
        "original": {"checksum": INC13_CK},
        "transparent_provenance": {"immutable_original_checksum": INC13_CK,
                                   "source_filename": "Patterns of Intelligence FINAL.docx"},
        "artifacts": {"design": {"ebook": {"epub": "/api/rendering/asset/OLD-13.epub"}}}})
    await scratch.book_purchases.insert_one({"book_id": "PROD-DIFF-13", "payment_status": "paid"})

    # Case B — BOOK-0016 exists as a genuinely DIFFERENT work (different checksum, filename, title, author).
    await scratch.book_records.insert_one({
        "id": "PROD-DIFF-16", "book_code": "BOOK-0016",
        "title": "How to Understand AI", "author": "Someone Else",
        "publication_status": "Published",
        "original": {"checksum": "deadbeef" * 8},
        "transparent_provenance": {"immutable_original_checksum": "deadbeef" * 8,
                                   "source_filename": "How to Understand AI.docx"},
        "artifacts": {"design": {"ebook": {"epub": "/api/rendering/asset/OLD-16.epub"}}}})

    pm.db = scratch  # redirect module db to scratch (no effect on preview data)

    insp = await pm.inspect_book_conflicts()
    by = {b["book_code"]: b for b in insp["books"]}
    for code in ("BOOK-0013", "BOOK-0016", "BOOK-0018"):
        b = by[code]
        print(f"{code}: {b['classification']} (conf {b['confidence']}) adopt_eligible={b['adopt_eligible']}")

    # BOOK-0013: same checksum -> SAME_BOOK, definitive, adopt eligible
    assert by["BOOK-0013"]["classification"] == "SAME_BOOK"
    assert by["BOOK-0013"]["confidence"] == 1.0
    assert by["BOOK-0013"]["adopt_eligible"] is True
    assert by["BOOK-0013"]["existing_by_code"]["purchases"] == 1
    # BOOK-0016: genuinely different -> DIFFERENT_WORK, NOT adopt eligible
    assert by["BOOK-0016"]["classification"] == "DIFFERENT_WORK"
    assert by["BOOK-0016"]["adopt_eligible"] is False
    # BOOK-0018: absent -> create
    assert by["BOOK-0018"]["classification"] == "ABSENT"

    # resolve dry-run: 0013 adopts, 0016 skipped
    dry = await pm.resolve_book_conflicts(apply=False)
    outc = {r["code"]: r["outcome"] for r in dry["rows"]}
    print("resolve dry:", outc)
    assert outc["BOOK-0013"] == "WOULD_ADOPT_AND_REPOINT"
    assert outc["BOOK-0016"] == "SKIP"

    # resolve apply
    app = await pm.resolve_book_conflicts(apply=True)
    outc2 = {r["code"]: r["outcome"] for r in app["rows"]}
    print("resolve apply:", outc2)
    assert outc2["BOOK-0013"] == "ADOPTED_AND_REPOINTED"
    rec = await scratch.book_records.find_one({"id": "PROD-DIFF-13"})
    eb = rec["artifacts"]["design"]["ebook"]
    assert eb["epub"] == PTR["BOOK-0013"]["new_epub_url"]
    assert eb["epub_rollback"] == "/api/rendering/asset/OLD-13.epub"
    rec16 = await scratch.book_records.find_one({"id": "PROD-DIFF-16"})
    assert rec16["artifacts"]["design"]["ebook"]["epub"] == "/api/rendering/asset/OLD-16.epub"  # untouched
    print("collision record untouched: OK")

    # Extra: filename-only correction (no checksum) still classifies as adopt-eligible.
    await scratch.book_records.delete_one({"id": "PROD-DIFF-13"})
    await scratch.book_records.insert_one({
        "id": "PROD-NOCK-13", "book_code": "BOOK-0013",
        "title": "Patterns of Intelligence FINAL", "author": "",
        "publication_status": "Published",
        "transparent_provenance": {"source_filename": "Patterns of Intelligence FINAL.docx"},
        "artifacts": {"design": {"ebook": {"epub": "/api/rendering/asset/OLD-13b.epub"}}}})
    # temporarily strip incoming checksum to force secondary-evidence path
    insp2 = await pm.inspect_book_conflicts()
    b13b = next(b for b in insp2["books"] if b["book_code"] == "BOOK-0013")
    print("filename-correction case:", b13b["classification"], "adopt_eligible=", b13b["adopt_eligible"])
    assert b13b["adopt_eligible"] is True  # checksum match still (incoming has checksum, existing lacks -> falls to source/title)

    # ---- create-under-fresh-code for the DIFFERENT_WORK case (BOOK-0016) ----
    cf_dry = await pm.create_under_fresh_code(apply=False)
    cfd = {r["code"]: r["outcome"] for r in cf_dry["rows"]}
    print("create-fresh dry:", cfd)
    assert cfd["BOOK-0016"] == "WOULD_CREATE_UNDER_NEW_CODE"
    cf = await pm.create_under_fresh_code(apply=True)
    cfa = {r["code"]: r["outcome"] for r in cf["rows"]}
    print("create-fresh apply:", cfa)
    assert cfa["BOOK-0016"] == "CREATED_UNDER_NEW_CODE"
    newrec = await scratch.book_records.find_one({"id": B16["id"]})
    assert newrec and newrec["book_code"] != "BOOK-0016" and newrec["_recoded_from"] == "BOOK-0016"
    print("  new code:", newrec["book_code"], "| canonical id preserved:", newrec["id"])
    # existing collision record untouched
    assert (await scratch.book_records.find_one({"id": "PROD-DIFF-16"}))["title"] == "How to Understand AI"
    # idempotent: re-run inspect -> BOOK-0016 now present by id
    insp3 = await pm.inspect_book_conflicts()
    b16b = next(b for b in insp3["books"] if b["book_code"] == "BOOK-0016")
    assert b16b["classification"] == "PRESENT_BY_ID"
    # rollback removes it (no purchases)
    rb = await pm.create_under_fresh_code_rollback(apply=True)
    assert any(r["outcome"] == "REMOVED" for r in rb["rows"])
    assert await scratch.book_records.find_one({"id": B16["id"]}) is None
    print("create-fresh-code + rollback: OK")

    await client.drop_database("scratch_conflict_test")
    print("\nALL LINEAGE ASSERTIONS PASSED.")


asyncio.run(main())
