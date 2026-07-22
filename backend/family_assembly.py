"""QRU Product Family Assembly™ — orchestration only (no new manufacturing engine).

One Verified source (a Manufacturing-eligible understanding, which itself traces to a Verified UKR)
→ one Manufacturing Intent™ → a family of products, each manufactured through the EXISTING
create_product_from_decoder bridge → one Family Package.

This is a WRAPPER over existing capabilities: it loops the proven single-product bridge over the
selected families and assembles a package. Book uses the dedicated 7-button line; document families
inherit the Publication Quality Standard™. $0 AI for document families (allow_ai_cover=False); Book
records are created deterministically (cover/design happen later in the Book line).
"""
import io
import json
import zipfile
from datetime import datetime, timezone

import decoder_engine as de
import book_manufacturing as bm
import manufacturing_intents as intents
from database import db
from models import gen_id, now_iso


def _now():
    return datetime.now(timezone.utc).isoformat()


async def preview(did, intent_id):
    """Show what a family assembly WOULD produce (source verification + intent bundle). Read-only."""
    d = await de.get_decoder(did)
    if not d:
        return {"error": "Understanding record not found."}
    intent = intents.get_intent(intent_id)
    if not intent:
        return {"error": f"Unknown Manufacturing Intent '{intent_id}'."}
    gate = await bm.verify_source(d)
    eligible = d.get("review_state") in de.MANUFACTURING_ELIGIBLE_STATES
    return {
        "source": {"decoder_id": d.get("decoder_id"), "title": d.get("title"),
                   "review_state": d.get("review_state"), "eligible": eligible,
                   "source_kr_ids": d.get("source_kr_ids", [])},
        "intent": intent,
        "families": intent["families"],
        "gate": gate,
        "can_manufacture": eligible and gate.get("match", {}).get("level") != "critical",
    }


async def assemble(did, intent_id, families, actor, base_url="", override_source_gate=False):
    """Manufacture a product family from one understanding. Returns per-family results + package."""
    d = await de.get_decoder(did)
    if not d:
        return {"error": "Understanding record not found."}
    intent = intents.get_intent(intent_id)
    if not intent:
        return {"error": f"Unknown Manufacturing Intent '{intent_id}'."}

    if d.get("review_state") not in de.MANUFACTURING_ELIGIBLE_STATES:
        return {"error": f"This understanding is not manufacturing-eligible (state: {d.get('review_state')}). "
                         f"Eligible states: {', '.join(de.MANUFACTURING_ELIGIBLE_STATES)}."}

    gate = await bm.verify_source(d)
    if gate.get("match", {}).get("level") == "critical" and not override_source_gate:
        return {"error": "source_verification_failed", "gate": gate,
                "message": "🔴 Source does not match the intended subject. Assembly stopped. " + gate["match"]["reason"]}

    selected = [f for f in (families or intent["families"]) if f in de.available_product_types()]
    if not selected:
        return {"error": "No valid product families selected."}

    results = []
    for fam in selected:
        try:
            res = await de.create_product_from_decoder(d, fam, actor, base_url)
            if isinstance(res, dict) and res.get("error"):
                results.append({"family": fam, "ok": False, "error": res["error"]})
            else:
                results.append({"family": fam, "ok": True, "engine": res.get("engine"),
                                "id": res.get("id"), "book_id": res.get("book_id"),
                                "code": res.get("product_code") or res.get("book_code"),
                                "title": res.get("title"), "route": res.get("route"),
                                "deliverable_ready": res.get("deliverable_ready", None)})
        except Exception as e:
            results.append({"family": fam, "ok": False, "error": str(e)})

    ok_items = [r for r in results if r.get("ok")]
    family_id = f"FAM-{gen_id()[:8].upper()}"
    record = {
        "id": gen_id(), "family_code": family_id,
        "source_decoder_id": d.get("decoder_id"), "source_kr_ids": d.get("source_kr_ids", []),
        "title": d.get("title"), "intent": intent["id"], "intent_label": intent["label"],
        "audience": intent["audience"], "families_requested": selected,
        "items": results, "manufactured_by": actor, "created_at": now_iso(),
    }
    await db.product_families.insert_one(dict(record))

    package = None
    if ok_items:
        package = await _build_family_package(record, ok_items)
        await db.product_families.update_one({"id": record["id"]}, {"$set": {"package": package}})

    return {"ok": len(ok_items) > 0, "family_code": family_id, "family_id": record["id"],
            "intent": intent["label"], "audience": intent["audience"],
            "items": results, "succeeded": len(ok_items), "requested": len(selected),
            "package": package, "gate": gate}


async def _build_family_package(record, ok_items):
    """Assemble ONE Family Package (manifest of the whole family). Deterministic, $0."""
    import rendering_engine as re_engine
    manifest = {
        "standard": "QRU Product Family Package™",
        "family_code": record["family_code"], "title": record["title"],
        "intent": record["intent_label"], "audience": record["audience"],
        "source": {"decoder_id": record["source_decoder_id"], "source_kr_ids": record["source_kr_ids"]},
        "products": [{"family": r["family"], "code": r.get("code"), "title": r.get("title"),
                      "engine": r.get("engine")} for r in ok_items],
        "assembled_at": _now(),
        "note": "Manufactured once from one Verified source, assembled into a product family.",
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("00_FAMILY_MANIFEST.json", json.dumps(manifest, indent=2, default=str))
        z.writestr("README.txt",
                   f"{record['title']} — {record['intent_label']} family\n"
                   f"Manufactured from {record['source_decoder_id']} for audience: {record['audience']}.\n"
                   f"{len(ok_items)} product(s). See 00_FAMILY_MANIFEST.json.\n")
    fid = re_engine._save(f"family-{record['family_code']}", "zip", buf.getvalue())
    return {"url": re_engine._asset_url(fid), "size_kb": len(buf.getvalue()) // 1024,
            "manifest": manifest}


async def list_families():
    rows = await db.product_families.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return rows
