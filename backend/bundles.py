"""QRU Bundles™ — first-class bundle products.

A Bundle is a real, governed product: it is created, priced as one, published to the
Bundles experience, and delivered as a single purchase that grants access to every
included item. Phase 1 items are authorized books (fully deliverable); the data model
accepts any product type so other experiences can be added later without a rewrite.
"""
import re
from datetime import datetime, timezone

from database import db
from models import gen_id, now_iso

BUNDLES_COLL = "bundles"
_PUBLISHED_BOOK = {"founder_authorization.authorized": True}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (text or "").lower())
    return re.sub(r"-+", "-", base).strip("-") or "bundle"


def _cover_url(book: dict):
    design = (book.get("artifacts") or {}).get("design") or {}
    concepts = design.get("cover_concepts") or []
    sel = (design.get("selected_cover") or {}).get("concept")
    if sel is not None:
        for c in concepts:
            if c.get("concept") == sel and c.get("url"):
                return c["url"]
    for c in concepts:
        if c.get("url"):
            return c["url"]
    return None


def _epub_url(book: dict):
    return ((book.get("artifacts") or {}).get("design") or {}).get("ebook", {}).get("epub")


def _book_price(book: dict) -> float:
    pr = book.get("pricing") or {}
    return float(pr.get("ebook_price") or pr.get("list_price") or 0)


async def eligible_items():
    """Books that can go in a bundle today: authorized, with a real EPUB + a price."""
    out = []
    async for b in db.book_records.find(_PUBLISHED_BOOK, {"_id": 0}):
        if _epub_url(b) and _book_price(b) > 0:
            out.append({"id": b["id"], "title": b.get("title"), "author": b.get("author"),
                        "imprint": b.get("imprint") or "QRU Press™", "price": _book_price(b),
                        "type": "Book", "cover_thumb": f"/api/public/books/{b['id']}/cover-thumb"})
    out.sort(key=lambda x: (x["title"] or ""))
    return out


async def _resolve_items(item_ids: list):
    books = {b["id"]: b async for b in db.book_records.find({"id": {"$in": item_ids or []}}, {"_id": 0})}
    items, total = [], 0.0
    for iid in item_ids or []:
        b = books.get(iid)
        if not b:
            continue
        price = _book_price(b)
        total += price
        items.append({"id": iid, "type": "Book", "title": b.get("title"), "author": b.get("author"),
                      "imprint": b.get("imprint") or "QRU Press™", "price": price,
                      "deliverable": bool(_epub_url(b)),
                      "cover_thumb": f"/api/public/books/{iid}/cover-thumb"})
    return items, round(total, 2)


def _public_bundle(bundle: dict, items: list, sum_price: float) -> dict:
    price = float(bundle.get("price") or 0)
    return {
        "id": bundle["id"], "slug": bundle.get("slug") or _slugify(bundle.get("title")),
        "code": bundle.get("code"), "title": bundle.get("title"),
        "subtitle": bundle.get("subtitle"), "description": bundle.get("description"),
        "imprint": bundle.get("imprint"), "cover_url": bundle.get("cover_url") or (items[0]["cover_thumb"] if items else None),
        "price": price, "currency": bundle.get("currency", "USD"),
        "item_count": len(items), "items": items,
        "sum_price": sum_price, "savings": round(max(0.0, sum_price - price), 2),
    }


# ── Founder CRUD ──────────────────────────────────────────────────────────
async def create(data: dict, actor: str):
    if not data.get("title"):
        return {"error": "A bundle needs a title."}
    bid = gen_id()
    doc = {
        "id": bid, "code": f"BUNDLE-{bid[:8].upper()}",
        "title": data["title"], "subtitle": data.get("subtitle", ""),
        "description": data.get("description", ""), "imprint": data.get("imprint") or "QRU Press™",
        "cover_url": data.get("cover_url"), "price": float(data.get("price") or 0),
        "currency": data.get("currency", "USD"), "item_ids": data.get("item_ids") or [],
        "status": "Draft", "distribution": {"experiences": ["bundles"]},
        "slug": _slugify(data["title"]),
        "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db[BUNDLES_COLL].insert_one(dict(doc))
    doc.pop("_id", None)
    return {"ok": True, "bundle": doc}


async def update(bundle_id: str, data: dict):
    allowed = {k: v for k, v in data.items()
               if k in ("title", "subtitle", "description", "imprint", "cover_url", "price", "currency", "item_ids")}
    if "price" in allowed:
        allowed["price"] = float(allowed["price"] or 0)
    if "title" in allowed:
        allowed["slug"] = _slugify(allowed["title"])
    allowed["updated_at"] = now_iso()
    r = await db[BUNDLES_COLL].update_one({"id": bundle_id}, {"$set": allowed})
    if not r.matched_count:
        return {"error": "Bundle not found."}
    return {"ok": True}


async def publish(bundle_id: str, actor: str):
    b = await db[BUNDLES_COLL].find_one({"id": bundle_id}, {"_id": 0})
    if not b:
        return {"error": "Bundle not found."}
    items, _ = await _resolve_items(b.get("item_ids"))
    if len(items) < 2:
        return {"error": "A bundle needs at least 2 items."}
    if float(b.get("price") or 0) <= 0:
        return {"error": "Set a bundle price before publishing."}
    if not all(i["deliverable"] for i in items):
        return {"error": "Every item must be deliverable before this bundle can be published."}
    await db[BUNDLES_COLL].update_one({"id": bundle_id}, {"$set": {
        "status": "Published", "published_by": actor, "published_at": now_iso(), "updated_at": now_iso()}})
    return {"ok": True}


async def unpublish(bundle_id: str):
    await db[BUNDLES_COLL].update_one({"id": bundle_id}, {"$set": {"status": "Draft", "updated_at": now_iso()}})
    return {"ok": True}


async def delete(bundle_id: str):
    await db[BUNDLES_COLL].delete_one({"id": bundle_id})
    return {"ok": True}


async def list_all():
    out = []
    async for b in db[BUNDLES_COLL].find({}, {"_id": 0}).sort("created_at", -1):
        items, total = await _resolve_items(b.get("item_ids"))
        out.append({**b, "item_detail": items, "sum_price": total,
                    "savings": round(max(0.0, total - float(b.get("price") or 0)), 2)})
    return out


async def get_admin(bundle_id: str):
    b = await db[BUNDLES_COLL].find_one({"id": bundle_id}, {"_id": 0})
    if not b:
        return None
    items, total = await _resolve_items(b.get("item_ids"))
    return {**b, "item_detail": items, "sum_price": total}


# ── Public projections ────────────────────────────────────────────────────
async def public_list():
    out = []
    async for b in db[BUNDLES_COLL].find({"status": "Published"}, {"_id": 0}).sort("published_at", -1):
        items, total = await _resolve_items(b.get("item_ids"))
        out.append(_public_bundle(b, items, total))
    return out


async def public_get(key: str):
    b = await db[BUNDLES_COLL].find_one({"id": key, "status": "Published"}, {"_id": 0})
    if not b:
        async for d in db[BUNDLES_COLL].find({"status": "Published"}, {"_id": 0}):
            if (d.get("slug") or _slugify(d.get("title"))) == key:
                b = d
                break
    if not b:
        return None
    items, total = await _resolve_items(b.get("item_ids"))
    return _public_bundle(b, items, total)
