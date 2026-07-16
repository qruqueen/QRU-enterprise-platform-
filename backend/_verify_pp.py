import asyncio, os, json, zipfile
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    import rendering_engine as re_engine
    b = await db["book_records"].find_one({"book_code": "BOOK-0001"})
    if not b:
        print("BOOK-0001 not found"); return
    print("TITLE:", b.get("title"), "| id:", b.get("id"))
    print("AUTHORIZED:", (b.get("founder_authorization") or {}).get("authorized"))
    pp = b.get("post_publish")
    if not pp:
        print("NO post_publish data"); return
    print("PP generated_at:", pp.get("generated_at"), "counts:", pp.get("counts"))
    all_items = [(s["name"], i["name"], i["status"]) for s in pp["sections"] for i in s["items"]]
    print("TOTAL items:", len(all_items))
    for s,n,st in all_items:
        print(f"  [{st:16}] {s} :: {n}")
    # verify zip exists on disk
    zurl = pp.get("assets_zip")
    print("\nASSETS ZIP url:", zurl)
    if zurl:
        fn = zurl.rstrip("/").split("/")[-1]
        p = os.path.join(re_engine.ASSET_DIR, fn)
        print("zip on disk:", os.path.exists(p), "path:", p)
        if os.path.exists(p):
            print("zip size:", os.path.getsize(p))
            with zipfile.ZipFile(p) as z:
                for nm in z.namelist():
                    print("   zip>", nm, z.getinfo(nm).file_size)
    # deliverables (master package library)
    print("\nDELIVERABLES:")
    for d in (b.get("deliverables") or []):
        u = d.get("url","")
        fn = u.rstrip("/").split("/")[-1] if u else ""
        p = os.path.join(re_engine.ASSET_DIR, fn) if fn else ""
        exists = os.path.exists(p) if p else False
        print(f"  type={d.get('type')} name={d.get('name')} url_exists={exists} url={u}")

asyncio.run(main())
