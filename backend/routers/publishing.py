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
import shipping_status as ship
from fastapi import Request

router = APIRouter(prefix="/api/publishing", tags=["publishing"])

COVER_DIR = Path(os.environ.get("QRU_COVER_DIR", "/app/backend/generated_covers"))
COVER_DIR.mkdir(parents=True, exist_ok=True)
COVER_STATES = ps.COVER_STANDARD["cover_states"]


@router.get("/shipping-status")
async def get_shipping_status(user=Depends(get_current_user)):
    """Publish Success Dashboard™ — the definitive 8-stage shipping status for every product."""
    return await ship.shipping_status()


@router.get("/environment")
async def get_environment(request: Request, user=Depends(get_current_user)):
    """Auto-detect whether preview & production share a database (the Factory determines this itself)."""
    host = request.headers.get("x-forwarded-host") or (request.url.hostname or "")
    return await ship.environment_report(host)


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


@router.get("/cover/kr-brief/{kr_id}")
async def cover_kr_brief(kr_id: str, user=Depends(get_current_user)):
    """Founder Experience Principle™ — a book cover brief auto-derived from a Knowledge Record so the
    founder never re-describes what the Factory already knows."""
    import kr_inheritance as kri
    kr = await kri.load_kr(db, kr_id)
    if not kr:
        raise HTTPException(404, "Knowledge Record not found.")
    inh = kri.build_inheritance(kr)
    concept = (f"A refined, premium QRU editorial book cover expressing the idea: {inh['subtitle']}. "
               f"Symbolic and conceptual (not literal), navy/gold/cream QRU palette, generous negative space, "
               f"no text or lettering baked into the artwork.")
    return {"title": (inh["term"] or inh["topic"] or "").title(), "subtitle": inh["subtitle"],
            "series": "QRU Foundations", "concept_notes": concept, "topic": inh["topic"],
            "verified_external": inh["verified_external"]}



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

    # AI mode — now powered by the shared QRU Design Studio™ engine (art-direction → Gemini artwork →
    # QRU typography composite). Same superb, on-brand quality as the Book system. Provider failure
    # must not break the workflow (Treasure Standard™).
    import ai_service as ai
    import design_studio
    wh = _size_for(data.trim)
    size = tuple(int(x) for x in wh.split("x"))
    kind = "poster_landscape" if wh == "1536x1024" else "cover"
    n = max(1, min(3, data.concepts or 2))
    context = {"title": data.title, "subtitle": data.subtitle or "",
               "byline": data.series or data.edition or "", "imprint": "QRU Press™",
               "genre": data.series or "QRU Editorial", "synopsis": data.concept_notes or "",
               "slug": f"cover-{gen_id()[:8]}"}
    concepts, errors = [], []
    try:
        items = await design_studio.manufacture_bytes(context, kind=kind, size=size, n=n, slug=context["slug"])
    except Exception as e:
        items = []
        errors.append(str(e)[:140])
    for it in items:
        if it["status"] != "success":
            errors.append(f"{it['name']}: {it.get('failure_reason')}")
            continue
        cid = gen_id()
        fpath = COVER_DIR / f"{cid}.png"
        fpath.write_bytes(it["png"])
        rec = {**base, "id": cid, "state": "DRAFT_CONCEPT", "spec_only": False,
               "file": str(fpath), "size": len(it["png"]), "concept_name": it["name"],
               "provenance": {**base["provenance"], "provider": "Emergent/Gemini", "model": ai.IMAGE_MODEL,
                              "design_engine": "QRU Design Studio™", "art_direction": it["art_direction"],
                              "palette": it["palette"], "generated_at": now_iso(),
                              "version": ps.VERSION, "governing_standard": ps.DOC_ID},
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
            "note": "DRAFT CONCEPTS only (QRU Design Studio™) — human approval required before any becomes an Approved Design or Gold Master."}


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


# ── Product Publishing™ — the honest last mile from a rendered book ──────────
import product_publishing as ppub


@router.post("/product/{pid}/publish-store")
async def publish_to_store(pid: str, user=Depends(get_current_user)):
    # Delegate to the shared Manufacturing Foundation™ (single publish owner — no duplicate logic).
    import manufacturing_foundation as mf
    res = await mf.publish_product("publication", pid, user.get("name", "Founder"))
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.post("/product/{pid}/kdp-package")
async def kdp_package(pid: str, user=Depends(get_current_user)):
    res = await ppub.kdp_package(pid, user.get("name", "Founder"))
    if res is None:
        raise HTTPException(404, "Product not found.")
    return res


@router.get("/product/{pid}/kdp-file")
async def kdp_file(pid: str):
    path = ppub.kdp_file_path(pid)
    if not os.path.exists(path):
        raise HTTPException(404, "KDP package not found — build it first.")
    return FileResponse(str(path), media_type="application/zip", filename=f"{pid}-KDP-Ready.zip")


class AudiobookInput(BaseModel):
    voice: str = "onyx"


@router.post("/product/{pid}/audiobook")
async def make_audiobook(pid: str, data: AudiobookInput = AudiobookInput(), user=Depends(get_current_user)):
    res = await ppub.make_audiobook(pid, data.voice, actor=user.get("name", "Founder"))
    if res is None:
        raise HTTPException(404, "Product not found.")
    return res


@router.get("/product/{pid}/audiobook-status")
async def audiobook_status(pid: str, user=Depends(get_current_user)):
    res = await ppub.audiobook_status(pid)
    if res is None:
        raise HTTPException(404, "Product not found.")
    return res


@router.get("/product/{pid}/audiobook-file")
async def audiobook_file(pid: str):
    path = ppub.audiobook_file_path(pid)
    if not os.path.exists(path):
        import storage
        await storage.aensure_local(f"audiobook-{pid}.mp3", str(path))
    if not os.path.exists(path):
        raise HTTPException(404, "Audiobook not found — create it first.")
    return FileResponse(str(path), media_type="audio/mpeg", filename=f"{pid}-audiobook.mp3")


# ── QRU Poster Studio™ (governed template-driven posters) ───────────────────
import poster_studio as pstudio


@router.get("/poster/templates")
async def poster_templates(user=Depends(get_current_user)):
    return pstudio.overview()


@router.get("/posters")
async def list_posters(user=Depends(get_current_user)):
    return {"posters": await pstudio.list_posters(), "status_model": pstudio.STATUS_MODEL}


class PosterStep(BaseModel):
    heading: str
    body: str
    outcome: str


class PosterGenInput(BaseModel):
    template_id: str = "process-formula-v1"
    kr_id: Optional[str] = None
    is_factual: bool = False
    eyebrow: Optional[str] = None
    title: Optional[str] = None
    trademark: Optional[bool] = None
    tagline: Optional[str] = None
    subtitle: Optional[str] = None
    steps: Optional[List[PosterStep]] = None
    mid_line: Optional[str] = None
    footer: Optional[str] = None


@router.post("/poster/generate")
async def poster_generate(data: PosterGenInput, user=Depends(get_current_user)):
    content = {k: v for k, v in data.dict().items()
               if k not in ("template_id", "kr_id", "is_factual") and v is not None}
    if data.steps:
        content["steps"] = [s.dict() for s in data.steps]
    res = await pstudio.generate_poster(data.template_id, content or None, data.kr_id,
                                        bool(data.is_factual), user.get("name", "Founder"))
    if res.get("error"):
        raise HTTPException(400, res["error"])
    return res


@router.get("/poster/{pid}/file")
async def poster_file(pid: str, format: str = "png"):
    rec = await db.poster_assets.find_one({"id": pid}, {"_id": 0})
    if not rec:
        raise HTTPException(404, "Poster not found.")
    path = pstudio.poster_file_path(rec, format)
    if not os.path.exists(path):
        raise HTTPException(404, "Poster file not found.")
    media = "application/pdf" if format == "pdf" else "image/png"
    return FileResponse(str(path), media_type=media)


class PosterStatusInput(BaseModel):
    status: str
    note: Optional[str] = ""


@router.post("/poster/{pid}/status")
async def poster_status(pid: str, data: PosterStatusInput, user=Depends(get_current_user)):
    res = await pstudio.set_poster_status(pid, data.status, user.get("name", "Founder"), data.note or "")
    if res is None:
        raise HTTPException(404, "Poster not found.")
    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(400, res["error"])
    return res


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
