#!/usr/bin/env python3
"""RI-MFG-0002b — Production Book Data & EPUB Cutover (GOVERNED, IDEMPOTENT).

REVIEW-ONLY package. Runs ONLY where MONGO_URL/DB_NAME point (i.e. executed by Support in the
PRODUCTION container). DRY-RUN by default — pass --apply to write. Preview CANNOT and MUST NOT
run this against production.

Stage 1: create the 4 missing book records (BOOK-0013/0016/0018/0019) from data_stage1_books.json.
Stage 2: apply validated EPUB pointers for the 8 books from data_stage2_pointers.json (rollback-preserving).

Scope guards: acts ONLY on the listed book_codes/ids; never duplicates; never alters manuscripts,
covers, prices, authorization, purchase records, or Knowledge Records; verifies each target asset
exists in durable object storage before touching a pointer; STOPS on any missing prerequisite.

Usage:
  python migrate_production.py --stage all            # dry-run (default, no writes)
  python migrate_production.py --stage 1 --apply      # execute Stage 1
  python migrate_production.py --stage 2 --apply      # execute Stage 2
  python migrate_production.py --rollback-stage2      # restore prior EPUB pointers
"""
import os, sys, json, argparse, datetime
from pathlib import Path

HERE = Path(__file__).parent
MARK = "RI-MFG-0002b"
STAGE1_CODES = ["BOOK-0013", "BOOK-0016", "BOOK-0018", "BOOK-0019"]
STAGE2_CODES = ["BOOK-0001", "BOOK-0004", "BOOK-0009", "BOOK-0011",
                "BOOK-0013", "BOOK-0016", "BOOK-0018", "BOOK-0019"]
COLL = "book_records"


def _db():
    from pymongo import MongoClient
    url = os.environ["MONGO_URL"]; name = os.environ["DB_NAME"]
    print(f"[env] DB_NAME={name}  (host redacted)")
    return MongoClient(url)[name]


def _asset_exists(filename: str) -> bool:
    """True if the asset resolves in durable object storage for THIS environment."""
    if not filename:
        return False
    try:
        sys.path.insert(0, "/app/backend")
        import storage, rendering_engine as re
        dest = os.path.join(re.ASSET_DIR, filename)
        if os.path.exists(dest):
            return True
        return bool(storage.ensure_local(filename, dest))
    except Exception as e:
        print(f"   [warn] asset check unavailable ({type(e).__name__}); treating as MISSING")
        return False


def _load(name):
    return json.loads((HERE / name).read_text())


def stage1(db, apply):
    print("\n===== STAGE 1 — create 4 missing book records =====")
    books = _load("data_stage1_books.json")
    before = db[COLL].count_documents({})
    print(f"[inventory] production book_records BEFORE = {before}")
    created = skipped = blocked = 0
    for b in books:
        code, bid = b.get("book_code"), b.get("id")
        if code not in STAGE1_CODES:
            print(f"  {code}: OUT OF SCOPE — skip"); continue
        if db[COLL].find_one({"id": bid}):
            print(f"  {code} ({bid}): already exists by id -> VERIFY & SKIP (no duplicate)"); skipped += 1; continue
        if db[COLL].find_one({"book_code": code}):
            print(f"  {code}: exists with DIFFERENT id -> CONFLICT, SKIP (founder review)"); skipped += 1; continue
        design = (b.get("artifacts") or {}).get("design") or {}
        epub_f = ((design.get("ebook") or {}).get("epub") or "").rsplit("/", 1)[-1]
        cover_f = ((design.get("selected_cover") or {}).get("url") or "").rsplit("/", 1)[-1]
        ok_epub, ok_cover = _asset_exists(epub_f), _asset_exists(cover_f)
        if not (ok_epub and ok_cover):
            print(f"  {code}: PREREQ MISSING (epub={ok_epub}, cover={ok_cover}) -> STOP, do not create")
            blocked += 1; continue
        doc = dict(b); doc["_migrated_by"] = MARK; doc["_migrated_at"] = datetime.datetime.utcnow().isoformat()
        if apply:
            db[COLL].insert_one(doc); print(f"  {code}: CREATED (assets verified)")
        else:
            print(f"  {code}: WOULD CREATE (assets verified) [dry-run]")
        created += 1
    after = before + (created if apply else 0)
    print(f"[result] created={created} skipped={skipped} blocked={blocked}")
    print(f"[inventory] production book_records AFTER = {after} (expected {before}+4 on a clean apply)")
    return blocked == 0


def stage2(db, apply):
    print("\n===== STAGE 2 — apply validated EPUB pointers (rollback-preserving) =====")
    ptrs = _load("data_stage2_pointers.json")
    updated = already = blocked = 0
    for p in ptrs:
        code, bid = p["book_code"], p["id"]
        if code not in STAGE2_CODES:
            print(f"  {code}: OUT OF SCOPE — skip"); continue
        rec = db[COLL].find_one({"id": bid})
        if not rec:
            print(f"  {code}: RECORD MISSING in production -> STOP (run Stage 1 first)"); blocked += 1; continue
        if not _asset_exists(p["new_epub_file"]):
            print(f"  {code}: target EPUB {p['new_epub_file']} NOT in object storage -> STOP"); blocked += 1; continue
        cur = (((rec.get("artifacts") or {}).get("design") or {}).get("ebook") or {}).get("epub")
        if cur == p["new_epub_url"]:
            print(f"  {code}: pointer already = new -> SKIP (idempotent)"); already += 1; continue
        if apply:
            design = (rec.get("artifacts") or {}).get("design") or {}
            ebook = dict(design.get("ebook") or {})
            ebook.setdefault("epub_rollback", cur)          # preserve prior pointer ONCE
            ebook["epub"] = p["new_epub_url"]
            prov = design.get("rerender_provenance") or []
            prov.append({"ri": MARK, "at": datetime.datetime.utcnow().isoformat(),
                         "old_epub": cur, "new_epub": p["new_epub_url"], "standard": "Publication Quality Standard\u2122"})
            db[COLL].update_one({"id": bid}, {"$set": {
                "artifacts.design.ebook": ebook, "artifacts.design.rerender_provenance": prov}})
            print(f"  {code}: POINTER UPDATED  {cur}  ->  {p['new_epub_file']}  (rollback saved)")
        else:
            print(f"  {code}: WOULD UPDATE  {cur}  ->  {p['new_epub_file']}  (rollback would be saved) [dry-run]")
        updated += 1
    print(f"[result] updated={updated} already_applied={already} blocked={blocked}")
    return blocked == 0


def rollback_stage2(db, apply):
    print("\n===== ROLLBACK STAGE 2 — restore prior EPUB pointers =====")
    for p in _load("data_stage2_pointers.json"):
        rec = db[COLL].find_one({"id": p["id"]})
        if not rec:
            continue
        eb = (((rec.get("artifacts") or {}).get("design") or {}).get("ebook") or {})
        prior = eb.get("epub_rollback")
        if not prior:
            print(f"  {p['book_code']}: no rollback pointer stored -> skip"); continue
        if apply:
            db[COLL].update_one({"id": p["id"]}, {"$set": {"artifacts.design.ebook.epub": prior}})
            print(f"  {p['book_code']}: RESTORED -> {prior.rsplit('/',1)[-1]}")
        else:
            print(f"  {p['book_code']}: WOULD RESTORE -> {prior.rsplit('/',1)[-1]} [dry-run]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["1", "2", "all"], default="all")
    ap.add_argument("--apply", action="store_true", help="perform writes (default: dry-run)")
    ap.add_argument("--rollback-stage2", action="store_true")
    a = ap.parse_args()
    mode = "APPLY (WRITING)" if a.apply else "DRY-RUN (no writes)"
    print(f"RI-MFG-0002b migration | mode={mode}")
    db = _db()
    if a.rollback_stage2:
        rollback_stage2(db, a.apply); return
    ok = True
    if a.stage in ("1", "all"):
        ok = stage1(db, a.apply)
    if a.stage in ("2", "all"):
        if not ok:
            print("\n[HALT] Stage 1 prerequisites failed — NOT proceeding to Stage 2."); sys.exit(2)
        stage2(db, a.apply)
    print("\nDone.")


if __name__ == "__main__":
    main()
