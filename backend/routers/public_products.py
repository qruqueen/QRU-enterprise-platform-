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

Classification against REAL Factory records (corrected from an earlier round that assumed a
book-shaped genre/audience on every product): manufacturing_foundation._resolve_listing() shows
most non-book engines never copy a genre/domain field onto the canonical db.products listing —
only `knowledge_record_id` survives reliably. Subject is recovered from the linked Knowledge
Record's own `category` field via that relationship (public_subject.resolve_genre()/
reconcile_subject_for()), batched once per request (_kr_category_lookup) — never per item, so
list/pathway/collection endpoints stay O(1) queries regardless of catalog size. audience is used
exactly as stored (present for decoder-bridge-manufactured products, absent for most others);
public_pathway.classify() already degrades gracefully when it's missing.

layout_family vs family/collection: product_recipes.RECIPES[type].category (e.g. "guide",
"workbook", "poster") is the product's LAYOUT family — useful, but not the customer-facing
"other formats of the same work" concept. That concept is served by public_family.py, which reads
the Factory's own Product Family Assembly™ records (db.product_families) — see that module's
docstring for the full resolution story. The two are exposed as separate fields (layout_family vs
family) so they are never conflated in the API or the UI.
"""
import re

from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from auth import require_super_admin, get_current_user
import product_recipes as recipes
import public_subject as psub
import public_pathway as pp
import public_family as pf
import distribution_architecture as da

router = APIRouter(prefix="/api/public", tags=["qru-online-products"])

_PUBLISHED_QUERY = {"status": "Published"}
# Public storefront discovery query: Published, and never demo/seed inventory (is_demo True).
# Read-side exclusion only — demo records are preserved untouched in the database (Round 1 D).
_STOREFRONT_QUERY = {"status": "Published", "is_demo": {"$ne": True}}
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


async def _kr_category_lookup(product_docs: list[dict]) -> dict:
    """One batched query resolving every distinct knowledge_record_id among the given products to
    that Knowledge Record's `category` field — the nearest existing subject signal for a product
    whose own doc never got a genre/domain copied onto it (see module docstring). Called exactly
    once per request by every caller below; never inside a per-item loop."""
    ids = sorted({p.get("knowledge_record_id") for p in product_docs if p.get("knowledge_record_id")})
    if not ids:
        return {}
    docs = await db.knowledge_records.find({"id": {"$in": ids}}, {"_id": 0, "id": 1, "category": 1}).to_list(len(ids))
    return {d["id"]: d.get("category") for d in docs}


def _public_product(p: dict, kr_category_by_id: dict, family_index: dict, slug: str | None = None,
                    detail: bool = False) -> dict:
    """Project a db.products record down to public-safe fields only. No download_url, no
    internal provenance — matches _public_book()'s discipline in public_site.py."""
    ptype = p.get("product_type")
    recipe = recipes.get_recipe(ptype)
    kr_category = kr_category_by_id.get(p.get("knowledge_record_id"))
    # Same merged-genre view feeds both classify() and reconcile_subject() so the Adult-family
    # subject check inside public_pathway.classify() sees the identical resolved signal.
    classification_record = {**p, "genre": psub.resolve_genre(p, kr_category)}
    card = {
        "id": p.get("id"),
        "slug": slug or _slugify(p.get("title")),
        "title": p.get("title"),
        "product_type": ptype,
        "layout_family": recipe.get("category"),
        "format": recipe.get("primary"),
        "topic": p.get("topic"),
        "cover_url": p.get("cover_url") or p.get("thumbnail_url"),
        "price": p.get("price"),
        "currency": "USD",
        "pathways": pp.classify(classification_record, ptype),
        "subject": psub.reconcile_subject(classification_record),
        "family": pf.family_for_product(family_index, p.get("id")),
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
                        layout_family: str | None = None, format: str | None = None,
                        family_id: str | None = None):
    """Public catalog of non-book products. Optional filters compose with AND semantics.
    pathway/subject are computed at read time (see public_pathway.py / public_subject.py),
    not stored — so a filter always reflects the current deterministic rule, never a stale
    cached label. family_id filters to a single Product Family Assembly™ collection (see
    public_family.py) — distinct from layout_family, which is the product's own layout type."""
    docs = await db.products.find(_STOREFRONT_QUERY, {"_id": 0}).to_list(2000)
    docs = [p for p in docs if da.in_storefront(p)]
    slugs = _slug_map(docs)
    kr_category_by_id = await _kr_category_lookup(docs)
    family_index = await pf.load_index()
    items = [_public_product(p, kr_category_by_id, family_index, slug=slugs.get(p.get("id"))) for p in docs]
    if layout_family:
        items = [i for i in items if i["layout_family"] == layout_family]
    if format:
        items = [i for i in items if i["format"] == format]
    if subject:
        items = [i for i in items if i["subject"] == subject]
    if pathway:
        items = [i for i in items if pathway in i["pathways"]]
    if family_id:
        items = [i for i in items if i["family"] and i["family"]["id"] == family_id]
    return {"products": items, "count": len(items)}


@router.get("/products/{key}")
async def product_detail(key: str, request: Request):
    """Resolves by id OR slug. 404 if not published for an ordinary visitor — never leaks
    an unpublished product's existence, matching public_site.py's book_detail() behavior
    exactly. The one carve-out: an authenticated Founder/Administrator can still reach a
    hidden product's page (read-only otherwise) so they can inspect and restore it from the
    same storefront experience they just unpublished it from."""
    founder = await _optional_super_admin(request)
    query = {"id": key} if founder else {"id": key, **_STOREFRONT_QUERY}
    p = await db.products.find_one(query, {"_id": 0})
    all_docs = await db.products.find({} if founder else _STOREFRONT_QUERY, {"_id": 0}).to_list(2000)
    if not p:
        slugs = _slug_map(all_docs)
        match = next((d for d in all_docs if slugs.get(d.get("id")) == key), None)
        if not match:
            raise HTTPException(status_code=404, detail="This product is not available.")
        p, slug = match, key
    else:
        slug = _slug_map(all_docs).get(p.get("id"))
    kr_category_by_id = await _kr_category_lookup([p])
    family_index = await pf.load_index()
    return _public_product(p, kr_category_by_id, family_index, slug=slug, detail=True)


@router.get("/pathways")
async def list_pathways():
    """Metadata for the 5 pathway landing pages + counts. Explore All is intentionally not
    included as a row here — it's the inclusive default surface, never a stored/exclusive
    classification (Founder decision)."""
    book_docs = await db.book_records.find(
        {"founder_authorization.authorized": True}, {"_id": 0, "audience": 1, "genre": 1}
    ).to_list(2000)
    product_docs = await db.products.find(
        _STOREFRONT_QUERY, {"_id": 0, "audience": 1, "genre": 1, "product_type": 1,
                            "knowledge_record_id": 1, "distribution": 1}
    ).to_list(2000)
    product_docs = [p for p in product_docs if da.in_storefront(p)]
    kr_category_by_id = await _kr_category_lookup(product_docs)
    counts = {p: 0 for p in pp.PATHWAYS}
    for b in book_docs:
        for path in pp.classify(b, "Book"):
            counts[path] += 1
    for p in product_docs:
        kr_category = kr_category_by_id.get(p.get("knowledge_record_id"))
        classification_record = {**p, "genre": psub.resolve_genre(p, kr_category)}
        for path in pp.classify(classification_record, p.get("product_type")):
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
    product_docs = await db.products.find(
        _STOREFRONT_QUERY, {"_id": 0, "genre": 1, "knowledge_record_id": 1,
                            "product_type": 1, "distribution": 1}
    ).to_list(2000)
    product_docs = [p for p in product_docs if da.in_storefront(p)]
    kr_category_by_id = await _kr_category_lookup(product_docs)
    counts = {}
    for b in book_docs:
        s = psub.reconcile_subject(b)
        counts[s] = counts.get(s, 0) + 1
    for p in product_docs:
        s = psub.reconcile_subject_for(p, kr_category_by_id.get(p.get("knowledge_record_id")))
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
