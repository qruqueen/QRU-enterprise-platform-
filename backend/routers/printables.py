"""QRU Governed Printable Product Manufacturing™ (STD-PPB-0001) — router.

Upload artwork → choose a product type → arrange pages → QA (resolution gate) → export a governed,
distributable PDF (Etsy download / QRU Online download / TpT resource). Never auto-publishes.
"""
import base64
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from auth import get_current_user
from database import db
from models import gen_id, now_iso
import pdf_product_builder as ppb
import rendering_engine as re
import design_language as dl

router = APIRouter(prefix="/api/printables", tags=["printables"])
COLL = "printable_products"


async def _resolve_product(engine, record_id):
    coll = {"book": "book_records", "publication": "products", "product": "products"}.get(engine, "products")
    return await db[coll].find_one({"id": record_id}, {"_id": 0}) \
        or await db[coll].find_one({"book_code": record_id}, {"_id": 0}) \
        or await db[coll].find_one({"product_code": record_id}, {"_id": 0})


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return {"standard": ppb.STANDARD_ID,
            "product_types": [{"id": k, **v} for k, v in ppb.PRODUCT_TYPES.items()],
            "page_sizes": [{"id": k, **v} for k, v in ppb.PAGE_SIZES.items()],
            "worksheet_presets": [{"id": k, "label": v} for k, v in ppb.WORKSHEET_PRESETS.items()],
            "destinations": ppb.SUITABLE_DESTINATIONS,
            "gate": {"min_print_dpi": ppb.MIN_PRINT_DPI, "ideal_print_dpi": ppb.IDEAL_PRINT_DPI}}


@router.get("/library")
async def library(user=Depends(get_current_user)):
    """Standalone Printables Library — every printable built (with or without a product), newest first,
    so you can find, download, and reuse them later."""
    rows = await db[COLL].find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"count": len(rows), "printables": rows}


class BuildReq(BaseModel):
    product_type: str
    images_base64: List[str]                 # ordered page images (PNG/JPEG)
    include_cover: Optional[bool] = None
    include_instructions: Optional[bool] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    instructions: Optional[List[str]] = None
    page_size: Optional[str] = "letter"
    activity_layout: Optional[bool] = None
    worksheet_presets: Optional[List[str]] = None


@router.post("/build/{engine}/{record_id}")
async def build(engine: str, record_id: str, req: BuildReq, user=Depends(get_current_user)):
    # record_id "standalone" (or "none") builds a printable without attaching to an existing product.
    standalone = record_id in ("standalone", "none", "")
    product = {} if standalone else await _resolve_product(engine, record_id)
    if not standalone and not product:
        raise HTTPException(404, "Product not found.")
    if not req.images_base64:
        raise HTTPException(400, "Upload at least one page image.")
    try:
        images = [base64.b64decode(b.split(",")[-1]) for b in req.images_base64]
    except Exception:
        raise HTTPException(400, "One or more images_base64 values are invalid.")
    result = ppb.build(product, req.product_type, images, include_cover=req.include_cover,
                       include_instructions=req.include_instructions, title=req.title,
                       subtitle=req.subtitle, instructions=req.instructions,
                       page_size=req.page_size or "letter", activity_layout=req.activity_layout,
                       worksheet_presets=req.worksheet_presets)
    if result.get("error"):
        raise HTTPException(400, result["error"])
    pdf_bytes = result.pop("pdf_bytes")
    fid = re._save("printable", "pdf", pdf_bytes)
    pdf_url = re._asset_url(fid)
    doc_title = req.title or product.get("title") or "QRU Printable"
    record = {"id": gen_id(), "product_id": product.get("id"), "engine": engine, "title": doc_title,
              "product_type": result["product_type"], "page_count": result["page_count"],
              "qa_result": result["qa"]["result"], "quality_review_required": result["quality_review_required"],
              "pdf_url": pdf_url, "bytes": len(pdf_bytes), "created_by": user.get("name", "Founder"),
              "created_at": now_iso(), "standard": ppb.STANDARD_ID}
    await db[COLL].insert_one(dict(record))
    return {**result, "pdf_url": pdf_url, "bytes": len(pdf_bytes), "printable_id": record["id"],
            "product_id": product.get("id")}


class EnhanceReq(BaseModel):
    image_base64: str
    page_size: Optional[str] = "letter"
    activity: Optional[bool] = False


@router.post("/enhance-image")
async def enhance_image(req: EnhanceReq, user=Depends(get_current_user)):
    """Regenerate Larger — Lanczos-upscale one page's source so it meets ~300 DPI in its slot. Returns
    the enhanced image (base64) to replace that page. Honestly flagged as upscaled (adds no new detail)."""
    try:
        data = base64.b64decode(req.image_base64.split(",")[-1])
    except Exception:
        raise HTTPException(400, "Invalid image_base64.")
    try:
        out = ppb.enhance_image_for_print(data, page_size=req.page_size or "letter", activity=bool(req.activity))
    except Exception as e:
        raise HTTPException(400, f"Could not enhance image: {str(e)[:100]}")
    return {"image_base64": "data:image/png;base64," + base64.b64encode(out["data"]).decode(),
            "upscaled": out["upscaled"], "new_px": out["new_px"], "original_px": out["original_px"],
            "target_dpi": out["target_dpi"]}


class BundleReq(BaseModel):
    printable_ids: List[str]
    title: Optional[str] = None


@router.post("/bundle/{engine}/{record_id}")
async def bundle(engine: str, record_id: str, req: BundleReq, user=Depends(get_current_user)):
    """Bundle Builder — combine several finished printables into one activity-pack PDF with a
    branded Table of Contents. Preserves each source printable (never deletes)."""
    import fitz
    import os
    product = await _resolve_product(engine, record_id)
    if not product:
        raise HTTPException(404, "Product not found.")
    if len(req.printable_ids) < 2:
        raise HTTPException(400, "Select at least two printables to bundle.")
    rows = await db[COLL].find({"id": {"$in": req.printable_ids}, "product_id": product["id"]}, {"_id": 0}).to_list(50)
    order = {pid: i for i, pid in enumerate(req.printable_ids)}
    rows.sort(key=lambda r: order.get(r["id"], 999))
    if len(rows) < 2:
        raise HTTPException(400, "Could not find the selected printables for this product.")

    palette = dl.resolve_palette(product.get("family", ""), product.get("department", product.get("college", "")),
                                 product.get("topic", ""), product.get("title", ""))
    title = req.title or f"{product.get('title', 'QRU')} — Activity Pack"

    # Compute TOC entries: TOC is page 1, content starts at page 2.
    entries, start = [], 2
    for r in rows:
        entries.append({"title": r.get("title") or r.get("product_type"), "start_page": start,
                        "pages": r.get("page_count", 0)})
        start += r.get("page_count", 0)

    toc_pdf = ppb.render_toc_pdf(title, entries, "letter", palette)
    merged = fitz.open()
    merged.insert_pdf(fitz.open(stream=toc_pdf, filetype="pdf"))
    missing = []
    for r in rows:
        fid = (r.get("pdf_url") or "").split("/")[-1]
        path = os.path.join(re.ASSET_DIR, fid)
        if not fid or not os.path.exists(path):
            missing.append(r.get("title") or r["id"]); continue
        with open(path, "rb") as f:
            merged.insert_pdf(fitz.open(stream=f.read(), filetype="pdf"))
    if missing:
        raise HTTPException(400, f"Missing source PDF file(s): {', '.join(missing)}. Rebuild them and try again.")
    out = merged.tobytes()
    fid = re._save("printable-bundle", "pdf", out)
    pdf_url = re._asset_url(fid)
    record = {"id": gen_id(), "product_id": product["id"], "engine": engine, "title": title,
              "product_type": "activity_pack_bundle", "page_count": merged.page_count,
              "qa_result": "PASS", "quality_review_required": False, "bundled_from": req.printable_ids,
              "pdf_url": pdf_url, "bytes": len(out), "created_by": user.get("name", "Founder"),
              "created_at": now_iso(), "standard": ppb.STANDARD_ID}
    await db[COLL].insert_one(dict(record))
    return {"bundle_id": record["id"], "title": title, "page_count": merged.page_count,
            "pdf_url": pdf_url, "bytes": len(out), "table_of_contents": entries,
            "suitable_destinations": ppb.SUITABLE_DESTINATIONS}


_DEST_TO_POLICY = {"etsy_download": "etsy", "qru_online_download": "qru_online", "tpt_resource": "tpt"}


class AttachReq(BaseModel):
    printable_id: str
    destination: str          # etsy_download | qru_online_download | tpt_resource


@router.post("/attach/{engine}/{record_id}")
async def attach(engine: str, record_id: str, req: AttachReq, user=Depends(get_current_user)):
    """Attach To Listing — register a finished PDF as the product's download file for a destination and
    return the Governed Publication Policy™ decision. Never auto-publishes; records the deliverable and
    whether policy authorizes it."""
    import publication_policy as pp
    product = await _resolve_product(engine, record_id)
    if not product:
        raise HTTPException(404, "Product not found.")
    pr = await db[COLL].find_one({"id": req.printable_id, "product_id": product["id"]}, {"_id": 0})
    if not pr:
        raise HTTPException(404, "Printable not found for this product.")
    policy_dest = _DEST_TO_POLICY.get(req.destination)
    if not policy_dest:
        raise HTTPException(400, f"Unknown destination '{req.destination}'.")
    decision = await pp.decide(product, policy_dest)
    attachment = {"printable_id": pr["id"], "pdf_url": pr["pdf_url"], "title": pr.get("title"),
                  "page_count": pr.get("page_count"), "qa_result": pr.get("qa_result"),
                  "destination": req.destination, "attached_by": user.get("name", "Founder"),
                  "attached_at": now_iso(),
                  "publication_decision": decision["decision"], "can_publish": decision["can_publish"],
                  "policy_mode": decision["policy"]["effective_mode"]}
    coll = {"book": "book_records", "publication": "products", "product": "products"}.get(engine, "products")
    await db[coll].update_one({"id": product["id"]}, {"$set": {f"download_files.{req.destination}": attachment}})
    return {"attached": True, "destination": req.destination, "attachment": attachment,
            "decision": decision,
            "note": "Deliverable attached to the product. Governed Publication Policy™ decides the mode — "
                    "the Factory does not auto-publish. Use the destination's publish flow to go live."}


@router.get("/history/{engine}/{record_id}")
async def history(engine: str, record_id: str, user=Depends(get_current_user)):
    product = await _resolve_product(engine, record_id)
    if not product:
        raise HTTPException(404, "Product not found.")
    rows = await db[COLL].find({"product_id": product["id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"product_id": product["id"], "printables": rows}
