import asyncio, os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    import rendering_engine as re_engine
    b = await db["book_records"].find_one({"book_code": "BOOK-0001"})
    pp = b.get("post_publish") or {}
    url = pp.get("assets_zip")
    if not url:
        print("no assets_zip"); return
    fid = url.rstrip("/").split("/")[-1]
    p = os.path.join(re_engine.ASSET_DIR, fid)
    size_kb = os.path.getsize(p) // 1024
    now = datetime.now(timezone.utc).isoformat()
    by = pp.get("by", "Founder")
    deliverable = {"type": "Publication Assets Package", "label": "Publication Assets Package",
                   "url": url, "filename": fid, "size_kb": size_kb, "assembled_at": now, "by": by}
    existing = b.get("deliverables", []) or []
    deliverables = [d for d in existing if d.get("type") != "Publication Assets Package"] + [deliverable]
    await db["book_records"].update_one({"id": b["id"]}, {"$set": {"deliverables": deliverables}})
    print("Registered. Deliverables now:")
    for d in deliverables:
        print("  -", d["type"], d["size_kb"], "KB", d["url"])

asyncio.run(main())
