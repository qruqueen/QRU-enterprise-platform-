"""QRU Online™ — PUBLIC presentation layer API (read-only, no auth).

Single governed source of truth: the Factory manufactures and authorizes; this
surface presents ONLY approved, published assets. It never exposes Factory
internals (no provenance, manifests, working copy, states, or unpublished work).

Published gate for a book = founder_authorization.authorized == True.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from PIL import Image
import rendering_engine as re_engine

from database import db

router = APIRouter(prefix="/api/public", tags=["qru-online"])

# The ONLY gate: a book is public when the Founder has authorized its release.
_PUBLISHED_QUERY = {"founder_authorization.authorized": True}

# Master Asset Principle™ — one canonical cover; the web thumbnail is a
# derivative generated once from that master and cached (never hand-maintained).
_THUMB_WIDTH = 460
_THUMB_PREFIX = "webthumb-"


def _cover_filename(book: dict) -> str | None:
    """The canonical cover asset filename for a book (from the selected concept)."""
    url = _cover_url(book)
    return url.rsplit("/", 1)[-1] if url else None


def _ensure_thumbnail(canonical_fname: str) -> str | None:
    """Derive (once, cached) a web-optimized JPEG thumbnail from the canonical cover.
    Returns the thumbnail filename, or None if the master is unavailable."""
    src = os.path.join(re_engine.ASSET_DIR, canonical_fname)
    if not os.path.exists(src):
        return None
    stem = canonical_fname.rsplit(".", 1)[0]
    thumb_fname = f"{_THUMB_PREFIX}{stem}.jpg"
    thumb_path = os.path.join(re_engine.ASSET_DIR, thumb_fname)
    if not os.path.exists(thumb_path):
        with Image.open(src) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w > _THUMB_WIDTH:
                im = im.resize((_THUMB_WIDTH, int(h * _THUMB_WIDTH / w)), Image.LANCZOS)
            im.save(thumb_path, "JPEG", quality=82, optimize=True)
    return thumb_fname


def _cover_url(book: dict) -> str | None:
    """Resolve the Founder-selected cover art for a book (public-safe URL only)."""
    design = (book.get("artifacts") or {}).get("design") or {}
    concepts = design.get("cover_concepts") or []
    selected = design.get("selected_cover") or {}
    sel_no = selected.get("concept")
    if sel_no is not None:
        for c in concepts:
            if c.get("concept") == sel_no and c.get("url"):
                return c["url"]
    for c in concepts:
        if c.get("url"):
            return c["url"]
    return None


def _public_book(book: dict, detail: bool = False) -> dict:
    """Project a book_record down to public-safe fields only."""
    pricing = book.get("pricing") or {}
    meta = book.get("publication_metadata") or {}
    card = {
        "id": book.get("id"),
        "title": book.get("title"),
        "subtitle": book.get("subtitle") or meta.get("subtitle"),
        "author": book.get("author") or meta.get("author"),
        "genre": book.get("genre"),
        "imprint": book.get("imprint") or meta.get("imprint") or "QRU Press™",
        "audience": book.get("audience"),
        "cover_url": _cover_url(book),
        "thumb_url": f"/api/public/books/{book.get('id')}/cover-thumb",
        "list_price": pricing.get("list_price"),
        "currency": pricing.get("currency", "USD"),
    }
    if not detail:
        blurb = (book.get("description") or "").strip()
        card["excerpt"] = (blurb[:220] + "…") if len(blurb) > 220 else blurb
        return card
    card.update({
        "description": book.get("description"),
        "edition": book.get("edition") or meta.get("edition"),
        "language": book.get("language") or meta.get("language") or "English",
        "series": book.get("series"),
        "publisher": meta.get("publisher"),
        "ebook_price": pricing.get("ebook_price"),
        "paperback_price": pricing.get("paperback_price"),
        "published": True,
    })
    return card


@router.get("/home")
async def home():
    """Public landing content — featured published books + honest catalog counts."""
    books = await db.book_records.find(_PUBLISHED_QUERY, {"_id": 0}).to_list(500)
    public = [_public_book(b) for b in books]
    public = [b for b in public if b.get("cover_url")]
    return {
        "brand": {
            "name": "QRU Online",
            "tagline": "A premium educational publishing house.",
            "promise": "Every title is manufactured and verified to the Treasure Standard™ — "
                       "no fabrication, no shortcuts. Only what has been authorized for release.",
        },
        "featured": public[:6],
        "counts": {"books": len(public)},
    }


@router.get("/books")
async def books():
    """Public catalog — every authorized, published book (public-safe fields only)."""
    docs = await db.book_records.find(_PUBLISHED_QUERY, {"_id": 0}).to_list(1000)
    items = [_public_book(b) for b in docs]
    items = [b for b in items if b.get("cover_url")]
    return {"books": items, "count": len(items)}


@router.get("/books/{book_id}/cover-thumb")
async def cover_thumb(book_id: str):
    """Web-optimized cover thumbnail — a cached derivative of the canonical master cover."""
    book = await db.book_records.find_one({"id": book_id, **_PUBLISHED_QUERY}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="This title is not available.")
    canonical = _cover_filename(book)
    thumb = _ensure_thumbnail(canonical) if canonical else None
    if not thumb:
        raise HTTPException(status_code=404, detail="Cover not available.")
    return FileResponse(
        os.path.join(re_engine.ASSET_DIR, thumb),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.get("/books/{book_id}")
async def book_detail(book_id: str):
    """Public book page — one authorized book. 404 if not published (never leak drafts)."""
    book = await db.book_records.find_one(
        {"id": book_id, **_PUBLISHED_QUERY}, {"_id": 0}
    )
    if not book:
        raise HTTPException(status_code=404, detail="This title is not available.")
    return _public_book(book, detail=True)
