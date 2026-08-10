"""QRU Online™ — public storefront surface for non-book products (workbooks, posters,
courses, quizzes, and everything else manufactured outside the Book Manufacturing System).

Mirrors public_site.py's discipline exactly: read-only, public-safe field projection only,
never exposes Factory internals. Sources from db.products — the single canonical listing
every manufacturing engine already converges into via manufacturing_foundation.publish_product()
(confirmed: publication, poster, recipe, and media engines all write here; books deliberately
do not and are not touched by this file — they keep their own proven path in public_site.py).

Visibility gate mirrors the field this collection already uses: status == "Published". No new
field, no new enum — manufacturing_foundation.publish_product(), the ukr-quarantine flow, and
book's own defensive unlist code already read and write these exact values.

Not in scope for this file: checkout/purchase for non-book products. Preserving the existing
checkout/payment/delivery pipeline (Founder requirement) means this file does discovery only —
list, detail, filter. Nothing here fabricates a buy action Stripe isn't actually wired for.
"""
import re

from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from auth import require_super_admin, get_current_user
import product_recipes as recipes
import public_subject as psub
import public_pathway as pp

router = APIRouter(prefix="/api/public", tags=["qru-online-products"])

_PUBLISHED_QUERY = {"status": "Published"}
_SUPER_ADMIN_ROLES = ("Founder & CEO", "Administrator")


async def _optional_super_admin(request: Request) -> dict | None:
    """Best-effort super-admin check for a read endpoint that stays public by default but
    reveals a hidden item to an authenticated Founder — the one carve-out that lets them
    inspect and restore something they just unpublished, without opening this endpoint to
    everyone. Never raises: no/invalid/insufficient auth just means 'treat as a customer'."""
    try:
        user = await get_current_user(request)
    except Exception:
        return None
    return user if user.get("role") in _SUPER_ADMIN_ROLES else None


def _slugify(text: str) -> str:
    """Identical scheme to public_site.py's book slugs — kept as a local, deliberately
    duplicated 2-line pure function rather than a cross-file import, same reasoning as
    public_subject.py's DOMAINS duplication: avoids coupling two otherwise-independent
    public routers over a trivial helper."""
    base = re.sub(r"[^a-z0-9]+", "-", (text or "").lower())
    return re.sub(r"-+", "-", base).strip("-") or "product"


def _slug_map(docs: list[dict]) -> dict:
    out, seen = {}, set()
    for d in sorted(docs, key=lambda x: x.get("id") or ""):
        base = _slugify(d.get("title"))
        slug = base if base not in seen else f"{base}-{(d.get('id') or '')[:6]}"
        seen.add(base)
        out[d.get("id")] = slug
    return out


def _public_product(p: dict, slug: str | None = None, detail: bool = False) -> dict:
    """Project a db.products record down to public-safe fields only. No download_url, no
    internal provenance — matches _public_book()'s discipline in public_site.py."""
    ptype = p.get("product_type")
    recipe = recipes.get_recipe(ptype)
    card = {
        "id": p.get("id"),
        "slug": slug or _slugify(p.get("title")),
        "title": p.get("title"),
        "product_type": ptype,
        "family": recipe.get("category"),
        "format": recipe.get("primary"),
        "topic": p.get("topic"),
        "cover_url": p.get("cover_url") or p.get("thumbnail_url"),
        "price": p.get("price"),
        "currency": "USD",
        "pathways": pp.classify(p, ptype),
        "subject": psub.reconcile_subject(p),
        # Honest state, not a fabricated action — no self-serve checkout exists yet for
        # non-book products. A storefront page can show this plainly rather than a
        # non-working "Buy" button.
        "purchasable": False,
        "published": p.get("status") == "Published",
    }
    if detail:
        card["description"] = p.get("description") or p.get("topic")
    return card


@router.get("/products")
async def list_products(pathway: str | None = None, subject: str | None = None,
                        family: str | None = None, format: str | None = None):
    """Public catalog of non-book products. Optional filters compose with AND semantics.
    pathway/subject are computed at read time (see public_pathway.py / public_subject.py),
    not stored — so a filter always reflects the current deterministic rule, never a stale
    cached label."""
    docs = await db.products.find(_PUBLISHED_QUERY, {"_id": 0}).to_list(2000)
    slugs = _slug_map(docs)
    items = [_public_product(p, slug=slugs.get(p.get("id"))) for p in docs]
    if family:
        items = [i for i in items if i["family"] == family]
    if format:
        items = [i for i in items if i["format"] == format]
    if subject:
        items = [i for i in items if i["subject"] == subject]
    if pathway:
        items = [i for i in items if pathway in i["pathways"]]
    return {"products": items, "count": len(items)}


@router.get("/products/{key}")
async def product_detail(key: str, request: Request):
    """Resolves by id OR slug. 404 if not published for an ordinary visitor — never leaks
    an unpublished product's existence, matching public_site.py's book_detail() behavior
    exactly. The one carve-out: an authenticated Founder/Administrator can still reach a
    hidden product's page (read-only otherwise) so they can inspect and restore it from the
    same storefront experience they just unpublished it from."""
    founder = await _optional_super_admin(request)
    query = {"id": key} if founder else {"id": key, **_PUBLISHED_QUERY}
    p = await db.products.find_one(query, {"_id": 0})
    all_docs = await db.products.find({} if founder else _PUBLISHED_QUERY, {"_id": 0}).to_list(2000)
    if not p:
        slugs = _slug_map(all_docs)
        match = next((d for d in all_docs if slugs.get(d.get("id")) == key), None)
        if not match:
            raise HTTPException(status_code=404, detail="This product is not available.")
        p, slug = match, key
    else:
        slug = _slug_map(all_docs).get(p.get("id"))
    return _public_product(p, slug=slug, detail=True)


@router.get("/pathways")
async def list_pathways():
    """Metadata for the 5 pathway landing pages + counts. Explore All is intentionally not
    included as a row here — it's the inclusive default surface, never a stored/exclusive
    classification (Founder decision)."""
    book_docs = await db.book_records.find(
        {"founder_authorization.authorized": True}, {"_id": 0, "audience": 1, "genre": 1}
    ).to_list(2000)
    product_docs = await db.products.find(_PUBLISHED_QUERY, {"_id": 0, "audience": 1, "genre": 1, "product_type": 1}).to_list(2000)
    counts = {p: 0 for p in pp.PATHWAYS}
    for b in book_docs:
        for path in pp.classify(b, "Book"):
            counts[path] += 1
    for p in product_docs:
        for path in pp.classify(p, p.get("product_type")):
            counts[path] += 1
    return {"pathways": [{"id": p, "name": p, "count": counts[p]} for p in pp.PATHWAYS]}


@router.get("/collections")
async def list_collections():
    """Subject list with counts, for /collections/:subject. Same non-exclusive discovery
    principle — a product's subject is always exactly one value, but nothing here prevents
    it from also matching multiple pathways."""
    book_docs = await db.book_records.find(
        {"founder_authorization.authorized": True}, {"_id": 0, "genre": 1}
    ).to_list(2000)
    product_docs = await db.products.find(_PUBLISHED_QUERY, {"_id": 0, "genre": 1}).to_list(2000)
    counts = {}
    for rec in book_docs + product_docs:
        s = psub.reconcile_subject(rec)
        counts[s] = counts.get(s, 0) + 1
    return {"collections": [{"id": s, "name": s, "count": n} for s, n in sorted(counts.items())]}


@router.post("/products/{pid}/publish")
async def publish_product_storefront(pid: str, user=Depends(require_super_admin)):
    """Founder-only. Non-destructive — flips status back to Published. Mirrors
    routers/bundles.py's existing publish/unpublish pattern exactly."""
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(status_code=404, detail="Product not found.")
    await db.products.update_one({"id": pid}, {"$set": {"status": "Published"}})
    return {"ok": True, "status": "Published"}


@router.post("/products/{pid}/unpublish")
async def unpublish_product_storefront(pid: str, user=Depends(require_super_admin)):
    """Founder-only. Non-destructive — removes it from public visibility only. Does not
    delete the product, its manufacturing assets, source material, or history."""
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(status_code=404, detail="Product not found.")
    await db.products.update_one({"id": pid}, {"$set": {"status": "Unpublished"}})
    return {"ok": True, "status": "Unpublished"}
