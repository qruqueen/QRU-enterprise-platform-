"""QRU Asset Vault™ (MT-027) — reusable manufacturing inventory for Founder-imported
legacy assets and factory-generated assets.

Assets are stored on disk (served via /api/vault/asset/{fname}) with rich classification,
approval status, and full version history. Approved/Protected/Founder-imported assets are
REUSED by default across the factory; nothing approved is ever overwritten — new work is
saved as a new version.
"""
import os
import logging

from database import db
from models import now_iso, gen_id, clean

logger = logging.getLogger("qru.vault")

VAULT_DIR = "/app/backend/asset_vault"
os.makedirs(VAULT_DIR, exist_ok=True)

# Source classification → replacement rule.
SOURCES = ["Protected Master", "Founder Imported", "Approved Production Asset",
           "Factory Draft", "Superseded", "Archived"]
REPLACEMENT_RULES = {
    "Protected Master": "Never recreate, never replace — only reuse.",
    "Founder Imported": "Do not recreate or replace without Founder permission. Preferred source when relevant.",
    "Approved Production Asset": "Reuse by default. Regenerate only when improvement is requested.",
    "Factory Draft": "May be regenerated, revised, or replaced.",
    "Superseded": "Kept for history — do not use by default.",
    "Archived": "Preserved for continuity — not used in production unless reactivated.",
}
APPROVAL_STATUSES = ["Treasure Standard™ Approved", "Founder Approved", "Brand Approved",
                     "Draft", "Needs Review", "Rejected", "Archived"]
ASSET_TYPES = ["Image", "Cover", "Poster", "Icon", "Logo", "QRU Shield™", "Treasure Standard™ Seal",
               "Character Artwork", "Transparent PNG", "Background", "Diagram", "Infographic",
               "PDF", "PowerPoint", "Audio", "Music", "Narration", "Video", "Template",
               "Marketing Graphic", "Social Media Asset", "Other"]

# Sources & statuses that make an asset reusable-by-default in Creative Studio™ lookups.
REUSABLE_SOURCES = ["Protected Master", "Founder Imported", "Approved Production Asset"]
REUSABLE_STATUSES = ["Treasure Standard™ Approved", "Founder Approved", "Brand Approved"]
# Ranking for "best" reusable asset (higher = stronger).
SOURCE_RANK = {"Protected Master": 5, "Founder Imported": 4, "Approved Production Asset": 3,
               "Factory Draft": 1, "Superseded": 0, "Archived": 0}

MEDIA_TYPE = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp",
    "gif": "image/gif", "svg": "image/svg+xml", "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "mp3": "audio/mpeg", "wav": "audio/wav", "mp4": "video/mp4", "webm": "video/webm",
    "html": "text/html",
}
PREVIEWABLE = {"png", "jpg", "jpeg", "webp", "gif", "svg", "pdf"}


def _asset_url(fid):
    return f"/api/vault/asset/{fid}" if fid else None


def save_bytes(data: bytes, ext: str) -> dict:
    ext = (ext or "bin").lower().lstrip(".")
    fid = f"vault-{gen_id()[:10]}.{ext}"
    with open(os.path.join(VAULT_DIR, fid), "wb") as f:
        f.write(data)
    return {"filename": fid, "url": _asset_url(fid), "ext": ext,
            "media_type": MEDIA_TYPE.get(ext, "application/octet-stream"),
            "bytes": len(data), "previewable": ext in PREVIEWABLE}


async def create_asset(name, asset_type, file_info, source="Founder Imported",
                       approval_status="Founder Approved", created_by="Founder",
                       knowledge_record_id=None, product_family=None, character=None,
                       department=None, notes=None):
    count = await db.asset_vault.count_documents({})
    asset = {
        "id": gen_id(), "asset_code": f"AV-{count + 1:05d}",
        "name": name, "asset_type": asset_type, "source": source,
        "protection_level": source, "replacement_rule": REPLACEMENT_RULES.get(source, ""),
        "approval_status": approval_status, "version": 1,
        "knowledge_record_id": knowledge_record_id, "product_family": product_family,
        "character": character, "department": department, "usage_notes": notes,
        "file": file_info, "related_products": [], "parent_id": None,
        "superseded": False, "superseded_by": None, "archived": False,
        "created_by": created_by, "upload_date": now_iso(), "created_at": now_iso(),
        "updated_at": now_iso(),
        "version_history": [{"version": 1, "file": file_info, "created_by": created_by,
                             "created_at": now_iso(), "reason": "Initial upload",
                             "approval_status": approval_status}],
    }
    await db.asset_vault.insert_one(dict(asset))
    try:
        from org_activity import log_org
        await log_org("Creative Studio Director™", "Creative Studio",
                      f"added {asset_type} '{name}' ({source}) to the QRU Asset Vault™",
                      asset["asset_code"], "success")
    except Exception:
        pass
    return clean(asset)


async def list_assets(q=None, asset_type=None, source=None, approval_status=None,
                      product_family=None, character=None, knowledge_record_id=None,
                      include_archived=False, selectable=False):
    query = {}
    if not include_archived:
        query["archived"] = {"$ne": True}
    if selectable:
        # Manufacturing-selectable = reusable (Founder/Protected/Approved OR approved status), not superseded.
        query["superseded"] = {"$ne": True}
        query["$or"] = [{"source": {"$in": REUSABLE_SOURCES}},
                        {"approval_status": {"$in": REUSABLE_STATUSES}}]
    if asset_type:
        query["asset_type"] = asset_type
    if source:
        query["source"] = source
    if approval_status:
        query["approval_status"] = approval_status
    if product_family:
        query["product_family"] = product_family
    if character:
        query["character"] = character
    if knowledge_record_id:
        query["knowledge_record_id"] = knowledge_record_id
    if q:
        query["$and"] = [{"$or": [{"name": {"$regex": q, "$options": "i"}},
                                  {"asset_code": {"$regex": q, "$options": "i"}},
                                  {"usage_notes": {"$regex": q, "$options": "i"}}]}]
    docs = await db.asset_vault.find(query).sort("created_at", -1).to_list(2000)
    return [clean(d) for d in docs]


async def get_asset(aid):
    d = await db.asset_vault.find_one({"id": aid})
    return clean(d) if d else None


async def update_asset(aid, updates: dict):
    allowed = {"name", "asset_type", "source", "approval_status", "knowledge_record_id",
               "product_family", "character", "department", "usage_notes", "archived"}
    upd = {k: v for k, v in updates.items() if k in allowed}
    if "source" in upd:
        upd["protection_level"] = upd["source"]
        upd["replacement_rule"] = REPLACEMENT_RULES.get(upd["source"], "")
    if upd.get("archived") is True:
        upd["approval_status"] = "Archived"
    upd["updated_at"] = now_iso()
    await db.asset_vault.update_one({"id": aid}, {"$set": upd})
    return await get_asset(aid)


async def link_product(aid, product_id):
    p = await db.products.find_one({"id": product_id})
    if not p:
        return None
    entry = {"id": product_id, "product_code": p.get("product_code"), "title": p.get("title")}
    await db.asset_vault.update_one({"id": aid}, {"$addToSet": {"related_products": entry},
                                                  "$set": {"updated_at": now_iso()}})
    return await get_asset(aid)


async def add_version(aid, file_info, created_by, reason, approval_status="Draft", supersede=True):
    """Save a NEW version — never overwrites the original. Optionally marks the prior state Superseded."""
    a = await db.asset_vault.find_one({"id": aid})
    if not a:
        return None
    new_version = a.get("version", 1) + 1
    history = a.get("version_history", [])
    history.append({"version": new_version, "file": file_info, "created_by": created_by,
                    "created_at": now_iso(), "reason": reason, "approval_status": approval_status,
                    "previous_file": a.get("file")})
    upd = {"file": file_info, "version": new_version, "version_history": history,
           "approval_status": approval_status, "updated_at": now_iso()}
    await db.asset_vault.update_one({"id": aid}, {"$set": upd})
    return await get_asset(aid)


async def find_reusable(asset_type=None, product_family=None, character=None,
                        knowledge_record_id=None, department=None):
    """Creative Studio™ lookup — return the STRONGEST reusable asset matching the context,
    or None. Reuse-by-default rule: prefer Protected Master > Founder Imported > Approved."""
    query = {"archived": {"$ne": True}, "superseded": {"$ne": True},
             "$and": [{"$or": [{"source": {"$in": REUSABLE_SOURCES}},
                               {"approval_status": {"$in": REUSABLE_STATUSES}}]}]}
    if asset_type:
        query["asset_type"] = asset_type
    ctx = []
    if character:
        ctx.append({"character": character})
    if knowledge_record_id:
        ctx.append({"knowledge_record_id": knowledge_record_id})
    if product_family:
        ctx.append({"product_family": product_family})
    if department:
        ctx.append({"department": department})
    if ctx:
        query["$and"].append({"$or": ctx})
    docs = await db.asset_vault.find(query).to_list(200)
    if not docs:
        return None
    docs.sort(key=lambda d: (SOURCE_RANK.get(d.get("source"), 0), d.get("version", 1)), reverse=True)
    return clean(docs[0])


def meta():
    return {"sources": SOURCES, "approval_statuses": APPROVAL_STATUSES, "asset_types": ASSET_TYPES,
            "replacement_rules": REPLACEMENT_RULES, "reusable_sources": REUSABLE_SOURCES,
            "reusable_statuses": REUSABLE_STATUSES}


async def recommend_assets(product_family=None, topic=None, asset_type=None, limit=6):
    """MT-029 — intelligent recommendations: reusable assets that match the product's
    family or topic, strongest first. Founder can always override."""
    base = {"archived": {"$ne": True}, "superseded": {"$ne": True},
            "$and": [{"$or": [{"source": {"$in": REUSABLE_SOURCES}},
                              {"approval_status": {"$in": REUSABLE_STATUSES}}]}]}
    if asset_type:
        base["asset_type"] = asset_type
    ors = []
    if product_family:
        ors.append({"product_family": product_family})
    if topic:
        ors.append({"name": {"$regex": topic[:40], "$options": "i"}})
    if ors:
        base["$and"].append({"$or": ors})
    docs = await db.asset_vault.find(base).to_list(200)
    docs.sort(key=lambda d: (SOURCE_RANK.get(d.get("source"), 0), d.get("version", 1)), reverse=True)
    return [clean(d) for d in docs[:limit]]


async def apply_to_product(pid, asset_id, actor="Founder"):
    """MT-029 — manufacture a product USING a selected imported asset. Records the permanent
    Product→Asset relationship and, for image assets, sets the product cover directly from the
    imported asset (preserving original quality — never regenerated/overwritten)."""
    a = await db.asset_vault.find_one({"id": asset_id})
    p = await db.products.find_one({"id": pid})
    if not a or not p:
        return None
    rel = {"asset_vault_id": a["id"], "asset_code": a.get("asset_code"), "asset_version": a.get("version"),
           "asset_source": a.get("source"), "asset_name": a.get("name"), "asset_type": a.get("asset_type"),
           "approval_status": a.get("approval_status")}
    updates = {"manufacturing_asset": rel, "asset_mode": "use_imported", "updated_at": now_iso()}
    # If the imported asset is an image, use it exactly as the product cover (no regeneration).
    if a.get("file", {}).get("previewable") and a["file"].get("ext") in ("png", "jpg", "jpeg", "webp"):
        import rendering_engine as re_engine
        import design_language as dl
        vpath = os.path.join(VAULT_DIR, a["file"]["filename"])
        if os.path.exists(vpath):
            with open(vpath, "rb") as f:
                cover = f.read()
            updates["cover_url"] = re_engine._asset_url(re_engine._save("cover", "png", cover))
            updates["thumbnail_url"] = re_engine._asset_url(re_engine._save("thumb", "png", dl.premium_thumbnail(cover)))
            updates["store_graphic_url"] = re_engine._asset_url(re_engine._save("store", "png", dl.premium_store_graphic(p, cover)))
            updates["cover_has_hero_art"] = False
            updates["cover_source"] = "asset_vault_selected"
            updates["design_language_applied"] = True
    await db.products.update_one({"id": pid}, {"$set": updates})
    await link_product(asset_id, pid)
    try:
        from org_activity import log_org
        await log_org("Manufacturing Director™", "Manufacturing",
                      f"manufactured using imported Asset Vault™ {a.get('asset_code')} ({a.get('source')}) for",
                      p.get("product_code", ""), "success")
    except Exception:
        pass
    return rel
