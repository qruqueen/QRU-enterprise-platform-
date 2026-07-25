CONTINUE PILOT-MFG-0001 · WORKSTREAM A ONLY
# RI-MFG-0002b — Production Book Data & EPUB Cutover — REVIEW PACKAGE
Status: PREPARED FOR REVIEW. NOT EXECUTED. Preview has NO production write authority.
Execution path: authorized production-data path (Emergent Support / Option C).

## Package files
- `migrate_production.py` — idempotent, dry-run-by-default migration (Stage 1 + Stage 2 + rollback).
- `data_stage1_books.json` — the 4 missing book records (full approved documents exported from preview).
- `data_stage2_pointers.json` — validated EPUB pointer map for the 8 books (book_code, id, new_epub_url/file).
- `MANIFEST.md` — this document.

## Scope (hard allow-list; script refuses anything else)
- Stage 1 CREATE: BOOK-0013, BOOK-0016, BOOK-0018, BOOK-0019.
- Stage 2 POINTERS: BOOK-0001, BOOK-0004, BOOK-0009, BOOK-0011, BOOK-0013, BOOK-0016, BOOK-0018, BOOK-0019.

## Exact production collections & fields affected
- Collection: `book_records` (ONLY).
- Stage 1: inserts whole approved documents (canonical `id` preserved) + adds `_migrated_by`, `_migrated_at` tags.
- Stage 2: sets `artifacts.design.ebook.epub` (new pointer); writes `artifacts.design.ebook.epub_rollback`
  (prior pointer, once); appends `artifacts.design.rerender_provenance[]`. NOTHING else is touched.
- NOT touched anywhere: manuscripts, covers, `pricing`, `founder_authorization`, `editorial_locked`,
  Knowledge Records, `book_purchases`.

## Idempotency behavior
- Stage 1: if a record with the same `id` exists → VERIFY & SKIP (no duplicate). Same `book_code`, different
  `id` → CONFLICT, SKIP (founder review). Missing EPUB/cover in object storage → STOP, do not create.
- Stage 2: if current pointer already == new pointer → SKIP. Record missing → STOP (run Stage 1 first).
  Target EPUB file missing in object storage → STOP. Re-running after success = all SKIP.

## Dry-run evidence (executed against PREVIEW + a scratch empty DB; NO writes)
Idempotent re-run (preview, records already present):
  STAGE 1: created=0 skipped=4 blocked=0   (all "already exists by id -> VERIFY & SKIP")
  STAGE 2: updated=0 already_applied=8 blocked=0  (all "pointer already = new -> SKIP")
Fresh/empty DB (create path + asset verification):
  STAGE 1: BOOK-0013/0016/0018/0019 -> "WOULD CREATE (assets verified)"  (created=4 blocked=0)

## Rollback procedure
- Stage 2: `python migrate_production.py --rollback-stage2 --apply` → restores each `epub` from the saved
  `epub_rollback`. Prior production files were never overwritten (new files use fresh names), so rollback is
  a pure pointer restore.
- Stage 1: remove only migration-tagged inserts: `db.book_records.delete_many({"_migrated_by": "RI-MFG-0002b"})`
  (documented for Support; not automated to avoid accidental deletion). No pre-existing record is affected.

## Post-migration validation checklist (run in production)
1. `GET /api/public/books` → `count == 8`; all 8 book_codes present.
2. `GET /api/public/books/{id}` → 200 for each of the 4 newly created IDs.
3. For each of the 8: `GET /api/public/checkout/status` path unaffected; EPUB pointer resolves; a live
   download succeeds (EPUB opens).
4. Spot-check pricing, authorization, cover, and title unchanged vs `data_stage1_books.json`.
5. Existing `book_purchases` still resolve (download uses the current pointer → refreshed EPUB).
6. Confirm `epub_rollback` present on the 4 previously-live books (BOOK-0001/0004/0009/0011).

## Expected record counts (public/authorized books)
- BEFORE: 4 public books (BOOK-0001/0004/0009/0011).
- AFTER Stage 1: 8 public books (the 4 above + 4 created).
- AFTER Stage 2: 8 public books, all pointing at validated re-rendered EPUBs.

## PREREQUISITE / OPEN DEPENDENCY — object storage
Stage 1 (new books) and Stage 2 (pointers) require the re-rendered EPUB + cover files to exist in the
PRODUCTION durable object storage. The script verifies each file and STOPS if any is missing. If production
object storage is separate from preview and the files are absent, the ASSET files must be migrated first
(flag to Support). Files referenced are listed in `data_stage2_pointers.json` (`new_epub_file`) and inside
the Stage 1 documents (`artifacts.design.ebook.epub`, `artifacts.design.selected_cover.url`).

## Support execution instructions (Option C — authorized production-data path)
1. Place this folder in the PRODUCTION backend container (where MONGO_URL/DB_NAME point to production).
2. Dry-run: `python migrate_production.py --stage all`  → review output; confirm no unexpected CREATE/UPDATE.
3. Apply Stage 1: `python migrate_production.py --stage 1 --apply`  → verify AFTER count = BEFORE + 4.
4. Apply Stage 2: `python migrate_production.py --stage 2 --apply`  → verify updated + already == 8.
5. Run the validation checklist above.
6. If anything is wrong: `python migrate_production.py --rollback-stage2 --apply`.
RI-MFG-0002b is COMPLETE only after step 5 (production validation) passes.
