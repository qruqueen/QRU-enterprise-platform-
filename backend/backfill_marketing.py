"""One-off backfill — manufacture the Preview & Marketing Kit™ for every Published
product that doesn't have one yet, so the QRU Store™ shows Read Sample / Preview PDF."""
import asyncio
import os

from database import db
import marketing_engine as me

BASE = os.environ.get("REACT_APP_BACKEND_URL", "")


async def run():
    prods = await db.products.find(
        {"status": "Published", "marketing_kit_ready": {"$ne": True}}, {"id": 1, "product_code": 1}
    ).to_list(500)
    print(f"Backfilling {len(prods)} published product(s)…")
    ok = 0
    for p in prods:
        try:
            await me.build_family(p["id"], "Marketing Backfill™", BASE)
            ok += 1
            print(f"  ✓ {p.get('product_code')}")
        except Exception as e:
            print(f"  ✗ {p.get('product_code')}: {e}")
    print(f"Backfill complete — {ok}/{len(prods)} kits built")


if __name__ == "__main__":
    asyncio.run(run())
