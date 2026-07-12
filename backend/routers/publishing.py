"""QRU Publishing Standard™ + Cover Studio™ API (QRU-CON-0002).

Exposes the governed standard, machine-readable design tokens, the governed CSS, the professional TOC
engine, the Treasure Standard™ Pre-Ship Gate, the pilot regeneration, and the Cover Studio (governed
AI-assisted cover production with provenance, human-approval states, and a manual/spec fallback so a
provider outage never breaks publishing). AI images are a governed TOOL — never the final authority.
"""
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional, List

from auth import get_current_user
from database import db
from models import gen_id, now_iso
import publishing_standard as ps

router = APIRouter(prefix="/api/publishing", tags=["publishing"])

COVER_DIR = Path(os.environ.get("QRU_COVER_DIR", "/app/backend/generated_covers"))
COVER_DIR.mkdir(parents=True, exist_ok=True)
COVER_STATES = ps.COVER_STANDARD["cover_states"]


@router.get("/standard")
async def get_standard(user=Depends(get_current_user)):
    return ps.standard_view()


@router.get("/tokens")
async def get_tokens(user=Depends(get_current_user)):
    return ps.design_tokens()


@router.get("/tokens.css")
async def get_tokens_css():
    return PlainTextResponse(ps.render_css(), media_type="text/css")


@router.get("/bindings")
async def get_bindings(user=Depends(get_current_user)):
    return await ps.bindings_view()


@router.get("/reference-covers")
async def reference_covers(user=Depends(get_current_user)):
    return {"note": "Reference assets — evidence of visual DIRECTION, NOT auto-approved Gold Standard.",
            "covers": ps.REFERENCE_COVERS}


class TocInput(BaseModel):
    raw: str


@router.post("/toc/clean")
async def toc_clean(data: TocInput, user=Depends(get_current_user)):
    entries = ps.clean_toc_markdown(data.raw)
    return {"entries": entries, "typeset_lines": ps.render_toc_lines(entries),
            "governed_by": [f"{ps.DOC_ID} §Table of Contents Standard"]}


class PreflightInput(BaseModel):
    artifact: dict
    product_id: Optional[str] = None


@router.post("/preflight")
async def preflight(data: PreflightInput, user=Depends(get_current_user)):
    report = ps.preflight_validate(data.artifact)
    record = {"id": gen_id(), "product_id": data.product_id, "title": (data.artifact or {}).get("title"),
              "verdict": report["verdict"], "blocked": report["blocked"], "counts": report["counts"],
              "results": report["results"], "by": user.get("name", "Founder"), "created_at": now_iso()}
    await db.preflight_runs.insert_one(dict(record))
    report["audit_id"] = record["id"]
    return report


@router.get("/preflight/runs")
async def preflight_runs(user=Depends(get_current_user)):
    runs = [r async for r in db.preflight_runs.find({}, {"_id": 0, "results": 0}).sort("created_at", -1).limit(25)]
    return {"runs": runs}


@router.get("/pilot")
async def pilot(user=Depends(get_current_user)):
    reg = ps.regenerate_pilot()
    before = ps.preflight_validate(ps.get_pilot_artifact(clean=False))
    after = ps.preflight_validate(ps.get_pilot_artifact(clean=True))
    return {"pilot": reg, "preflight_before": before, "preflight_after": after,
            "css_url": "/api/publishing/tokens.css", "pdf_url": "/api/publishing/pilot.pdf"}


@router.get("/pilot.pdf")
async def pilot_pdf(user=Depends(get_current_user)):
    pdf = ps.build_pilot_pdf()
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": "inline; filename=science-of-understanding-governed.pdf"})


# ------------------------------------------------------------------ COVER STUDIO
class CoverGenInput(BaseModel):
    title: str
    subtitle: Optional[str] = ""
    series: Optional[str] = ""
    edition: Optional[str] = ""
    trim: Optional[str] = "kdp_ebook"       # key in COVER_STANDARD.trim_presets
    concept_notes: Optional[str] = ""        # minimal visual brief only (no manuscript)
    concepts: Optional[int] = 2
    mode: Optional[str] = "ai"               # "ai" | "spec_only"


def _governed_prompt(d: CoverGenInput):
    return (
        "Design an ORIGINAL premium educational book cover in the QRU Press visual family. "
        "Do NOT copy any existing cover or imitate any living artist. "
        "Style DNA (from approved QRU references): deep navy ground (#0B1B3F), QRU Gold accents (#F5B21A), "
        "occasional Royal Purple (#35106A); a QRU shield/crest mark; a Treasure Standard gold seal; "
        "bold stacked serif title with clean sans subtitle; strong single focal concept artwork; "
        "generous negative space; luxury simplicity; excellent thumbnail readability. "
        f"TITLE: '{d.title}'. SUBTITLE: '{d.subtitle}'. "
        + (f"SERIES: '{d.series}'. " if d.series else "")
        + (f"EDITION: '{d.edition}'. " if d.edition else "")
        + (f"CONCEPT: {d.concept_notes}. " if d.concept_notes else "")
        + "Portrait book-cover composition, print-quality, no lorem text, no watermark."
    )


def _size_for(trim):
    return {"kdp_ebook": "1024x1536", "reel_9x16": "1024x1536", "us_trade_6x9": "1024x1536",
            "square_1x1": "1024x1024", "video_16x9": "1536x1024"}.get(trim, "1024x1536")


@router.post("/cover/generate")
async def cover_generate(data: CoverGenInput, user=Depends(get_current_user)):
    prompt = _governed_prompt(data)
    base = {"title": data.title, "subtitle": data.subtitle, "series": data.series, "edition": data.edition,
            "trim": data.trim, "provenance": {"prompt": prompt, "generator": "human_brief"}}
    if data.mode == "spec_only":
        rec = {**base, "id": gen_id(), "state": "DRAFT_CONCEPT", "spec_only": True, "file": None,
               "provenance": {**base["provenance"], "provider": "manual/spec", "model": None, "generated_at": now_iso()},
               "by": user.get("name", "Founder"), "created_at": now_iso(), "history": [{"state": "DRAFT_CONCEPT", "at": now_iso()}]}
        await db.cover_assets.insert_one(dict(rec))
        rec.pop("_id", None)
        return {"ok": True, "mode": "spec_only", "concepts": [rec],
                "note": "Spec-only concept recorded. Attach a manually produced or licensed asset to proceed."}

    # AI mode — governed tool; provider failure must not break the workflow.
    import ai_service as ai
    concepts, errors = [], []
    n = max(1, min(3, data.concepts or 2))
    for i in range(n):
        try:
            png = await ai.generate_image(prompt, session_id=f"cover-{gen_id()[:8]}")
        except Exception as e:
            png = None
            errors.append(str(e)[:120])
        if not png:
            errors.append("generation returned no image (provider unavailable or spend cap)")
            continue
        cid = gen_id()
        fpath = COVER_DIR / f"{cid}.png"
        fpath.write_bytes(png)
        rec = {**base, "id": cid, "state": "DRAFT_CONCEPT", "spec_only": False,
               "file": str(fpath), "size": len(png),
               "provenance": {**base["provenance"], "provider": "Emergent/Gemini", "model": ai.IMAGE_MODEL,
                              "generated_at": now_iso(), "version": ps.VERSION, "governing_standard": ps.DOC_ID},
               "by": user.get("name", "Founder"), "created_at": now_iso(),
               "history": [{"state": "DRAFT_CONCEPT", "at": now_iso(), "by": user.get("name", "Founder")}]}
        await db.cover_assets.insert_one(dict(rec))
        rec.pop("_id", None)
        rec["file_url"] = f"/api/publishing/cover/{cid}/file"
        concepts.append(rec)
    if not concepts:
        return {"ok": False, "mode": "ai", "concepts": [], "errors": errors,
                "fallback": "spec_only", "note": "Cover generation unavailable — use spec-only or upload a manual asset. Publishing is not blocked."}
    return {"ok": True, "mode": "ai", "concepts": concepts, "errors": errors,
            "note": "DRAFT CONCEPTS only — human approval required before any becomes an Approved Design or Gold Master."}


@router.get("/covers")
async def list_covers(user=Depends(get_current_user)):
    docs = [d async for d in db.cover_assets.find({}, {"_id": 0}).sort("created_at", -1).limit(60)]
    for d in docs:
        if d.get("file"):
            d["file_url"] = f"/api/publishing/cover/{d['id']}/file"
    return {"covers": docs, "states": COVER_STATES}


@router.get("/attachable-products")
async def attachable_products(user=Depends(get_current_user)):
    """Products (db.products) eligible to receive a governed cover for deliverable rendering."""
    rows = [p async for p in db.products.find(
        {}, {"_id": 0, "id": 1, "title": 1, "product_type": 1, "status": 1, "product_code": 1, "cover_asset_id": 1}
    ).sort("created_at", -1).limit(120)]
    return {"products": rows}


class CoverAttachInput(BaseModel):
    product_id: str


@router.post("/cover/{cid}/attach")
async def cover_attach(cid: str, data: CoverAttachInput, user=Depends(get_current_user)):
    """Bind an APPROVED/GOLD cover to a product and auto re-render the deliverable with the real cover.
    Treasure Standard™: a DRAFT_CONCEPT or spec-only cover can never ship on a real deliverable; the
    binding is recorded in the product's cover lineage — no silent swaps."""
    cover = await db.cover_assets.find_one({"id": cid}, {"_id": 0})
    if not cover:
        raise HTTPException(404, "Cover not found.")
    if cover.get("state") not in ("APPROVED_DESIGN", "GOLD_MASTER"):
        raise HTTPException(400, "Only an APPROVED_DESIGN or GOLD_MASTER cover can be attached to a product (Treasure Standard™).")
    if not cover.get("file") or not os.path.exists(cover["file"]):
        raise HTTPException(400, "This cover has no rendered image file to attach (spec-only concept).")
    product = await db.products.find_one({"id": data.product_id})
    if not product:
        raise HTTPException(404, "Product not found.")
    binding = {"cover_asset_id": cid, "cover_state": cover["state"],
               "attached_by": user.get("name", "Founder"), "at": now_iso()}
    await db.products.update_one({"id": data.product_id}, {
        "$set": {"cover_asset_id": cid, "cover_binding": binding, "updated_at": now_iso()},
        "$push": {"cover_lineage": binding}})
    import deliverable_renderer as dr
    rendered = await dr.ensure_deliverable(data.product_id, actor=user.get("name", "Founder"))
    files = (rendered or {}).get("files", []) if isinstance(rendered, dict) else []
    return {"ok": True, "cover_id": cid, "cover_state": cover["state"],
            "product_id": data.product_id, "product_title": product.get("title"),
            "rendered": bool(rendered),
            "download_url": (rendered or {}).get("download_url"),
            "preview_url": (rendered or {}).get("preview_url"),
            "files": files,
            "note": f"Cover attached and deliverable re-rendered with the real cover ({cover['state']})."}


@router.get("/cover/{cid}/file")
async def cover_file(cid: str):
    doc = await db.cover_assets.find_one({"id": cid}, {"_id": 0})
    if not doc or not doc.get("file") or not os.path.exists(doc["file"]):
        raise HTTPException(404, "Cover image not found.")
    return FileResponse(doc["file"], media_type="image/png")


class CoverStateInput(BaseModel):
    state: str
    note: Optional[str] = ""


@router.post("/cover/{cid}/state")
async def cover_state(cid: str, data: CoverStateInput, user=Depends(get_current_user)):
    if data.state not in COVER_STATES:
        raise HTTPException(400, f"Invalid state. Allowed: {COVER_STATES}")
    doc = await db.cover_assets.find_one({"id": cid})
    if not doc:
        raise HTTPException(404, "Cover not found.")
    # GOLD_MASTER requires an approved cover-checklist sign-off (never auto).
    if data.state == "GOLD_MASTER" and doc.get("state") != "APPROVED_DESIGN":
        raise HTTPException(400, "A cover must be APPROVED_DESIGN before it can become GOLD_MASTER.")
    entry = {"state": data.state, "at": now_iso(), "by": user.get("name", "Founder"), "note": data.note}
    await db.cover_assets.update_one({"id": cid}, {"$set": {"state": data.state, "updated_at": now_iso()},
                                                   "$push": {"history": entry}})
    doc = await db.cover_assets.find_one({"id": cid}, {"_id": 0})
    if doc.get("file"):
        doc["file_url"] = f"/api/publishing/cover/{cid}/file"
    return doc
