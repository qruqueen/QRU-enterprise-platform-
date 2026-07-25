"""Controlled simulation of the production conflict branches against a scratch DB.
Verifies: ID_MISMATCH_SAME_BOOK -> adopt & repoint; CODE_COLLISION -> founder decision (skip)."""
import asyncio, json, os
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from motor.motor_asyncio import AsyncIOMotorClient
import prod_migrations as pm

STAGE1 = json.load(open("/app/backend/migrations_data/data_stage1_books.json"))
B13 = next(b for b in STAGE1 if b["book_code"] == "BOOK-0013")
B16 = next(b for b in STAGE1 if b["book_code"] == "BOOK-0016")
PTR = {p["book_code"]: p for p in json.load(open("/app/backend/migrations_data/data_stage2_pointers.json"))}


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    scratch = client["scratch_conflict_test"]
    await scratch.book_records.delete_many({})
    await scratch.book_purchases.delete_many({})
    # BOOK-0013 exists under a DIFFERENT id, SAME title+author (production-created) -> adopt
    await scratch.book_records.insert_one({
        "id": "PROD-DIFF-13", "book_code": "BOOK-0013", "title": B13["title"], "author": B13["author"],
        "publication_status": "Published",
        "artifacts": {"design": {"ebook": {"epub": "/api/rendering/asset/OLD-13.epub"}}}})
    await scratch.book_purchases.insert_one({"book_id": "PROD-DIFF-13", "payment_status": "paid"})
    # BOOK-0016 exists under a different id with a DIFFERENT title -> code collision
    await scratch.book_records.insert_one({
        "id": "PROD-DIFF-16", "book_code": "BOOK-0016", "title": "A COMPLETELY DIFFERENT BOOK", "author": "Someone Else",
        "publication_status": "Published",
        "artifacts": {"design": {"ebook": {"epub": "/api/rendering/asset/OLD-16.epub"}}}})

    pm.db = scratch  # redirect module db to scratch (no effect on preview data)

    insp = await pm.inspect_book_conflicts()
    by_code = {b["book_code"]: b for b in insp["books"]}
    print("BOOK-0013 classification:", by_code["BOOK-0013"]["classification"])
    print("BOOK-0016 classification:", by_code["BOOK-0016"]["classification"])
    print("BOOK-0018 classification:", by_code["BOOK-0018"]["classification"], "(absent -> create)")

    assert by_code["BOOK-0013"]["classification"] == "ID_MISMATCH_SAME_BOOK"
    assert by_code["BOOK-0016"]["classification"] == "CODE_COLLISION_DIFFERENT_CONTENT"
    assert by_code["BOOK-0018"]["classification"] == "ABSENT"
    assert by_code["BOOK-0013"]["existing_by_code"]["purchases"] == 1

    dry = await pm.resolve_book_conflicts(apply=False)
    outc = {r["code"]: r["outcome"] for r in dry["rows"]}
    print("resolve dry:", outc)
    assert outc["BOOK-0013"] == "WOULD_ADOPT_AND_REPOINT"
    assert outc["BOOK-0016"] == "SKIP"  # collision left untouched

    app = await pm.resolve_book_conflicts(apply=True)
    outc2 = {r["code"]: r["outcome"] for r in app["rows"]}
    print("resolve apply:", outc2)
    assert outc2["BOOK-0013"] == "ADOPTED_AND_REPOINTED"

    rec = await scratch.book_records.find_one({"id": "PROD-DIFF-13"})
    eb = rec["artifacts"]["design"]["ebook"]
    print("new epub:", eb["epub"], "| rollback:", eb["epub_rollback"])
    assert eb["epub"] == PTR["BOOK-0013"]["new_epub_url"]
    assert eb["epub_rollback"] == "/api/rendering/asset/OLD-13.epub"
    # collision record untouched
    rec16 = await scratch.book_records.find_one({"id": "PROD-DIFF-16"})
    assert rec16["artifacts"]["design"]["ebook"]["epub"] == "/api/rendering/asset/OLD-16.epub"
    print("collision record untouched: OK")

    await client.drop_database("scratch_conflict_test")
    print("\nALL ASSERTIONS PASSED — conflict branches behave correctly.")


asyncio.run(main())
