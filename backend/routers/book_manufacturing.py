"""QRU Book Manufacturing System™ v1.0 — router. Orchestrates the seven-button workflow."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from auth import get_current_user, require_super_admin
import book_manufacturing as bm
import manufacturing_recipes as recipes

router = APIRouter(prefix="/api/book-mfg", tags=["book-manufacturing"])


class UploadPayload(BaseModel):
    title: str
    content: str
    meta: Optional[Dict[str, Any]] = None


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return {"system_title": recipes.SYSTEM_TITLE, "buttons": bm.SEVEN_BUTTONS,
            "publish_destinations": bm.PUBLISH_DESTINATIONS, "recipes": recipes.list_recipes()}


@router.get("/recipes")
async def recipes_list(user=Depends(get_current_user)):
    return {"system_title": recipes.SYSTEM_TITLE, "recipes": recipes.list_recipes()}


@router.get("/books")
async def books(user=Depends(get_current_user)):
    return {"books": await bm.list_books()}


@router.get("/books/{book_id}")
async def get_book(book_id: str, user=Depends(get_current_user)):
    b = await bm.get_book(book_id)
    if not b:
        raise HTTPException(404, "Book Record not found.")
    return b


@router.get("/books/{book_id}/inspection")
async def book_inspection(book_id: str, user=Depends(get_current_user)):
    """QRU Automated Pre-Review Inspection™ — read-only consolidated exception list. Never rewrites."""
    import preflight_inspection as pi
    res = await pi.inspect_book(book_id)
    if res.get("error"):
        raise HTTPException(404, res["error"])
    return res



@router.post("/upload")
async def upload(payload: UploadPayload, user=Depends(require_super_admin)):
    return await bm.create_book_record(payload.dict(), user.get("name", "Founder"))


class UploadFileReq(BaseModel):
    filename: str
    file_base64: str
    meta: Optional[Dict[str, Any]] = None


@router.post("/upload-file")
async def upload_file(req: UploadFileReq, user=Depends(require_super_admin)):
    r = await bm.upload_manuscript_file(req.filename, req.file_base64, req.meta or {}, user.get("name", "Founder"))
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


@router.post("/books/{book_id}/proof")
async def proof(book_id: str, user=Depends(require_super_admin)):
    r = await bm.proof_polish(book_id, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if r.get("error"):
        raise HTTPException(400, r["error"])
    return r


@router.post("/books/{book_id}/approve-edition")
async def approve_edition(book_id: str, user=Depends(require_super_admin)):
    r = await bm.approve_edition(book_id, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


@router.post("/books/{book_id}/open-revision")
async def open_revision(book_id: str, user=Depends(require_super_admin)):
    r = await bm.open_revision(book_id, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


class ManuscriptReq(BaseModel):
    content: str


@router.post("/books/{book_id}/manuscript")
async def update_manuscript(book_id: str, req: ManuscriptReq, user=Depends(require_super_admin)):
    r = await bm.update_manuscript(book_id, req.content, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


class ResolveFindingReq(BaseModel):
    issue: str
    action: str  # "keep" | "correct"
    span: Optional[list] = None
    suggested_fix: Optional[str] = None
    fix_kind: Optional[str] = None


@router.post("/books/{book_id}/resolve-finding")
async def resolve_finding(book_id: str, req: ResolveFindingReq, user=Depends(require_super_admin)):
    r = await bm.resolve_finding(book_id, req.issue, req.action, user.get("name", "Founder"),
                                 span=req.span, suggested_fix=req.suggested_fix, fix_kind=req.fix_kind)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


class DesignReq(BaseModel):
    base_url: Optional[str] = ""
    cover_mode: Optional[str] = None
    remember_preference: Optional[bool] = False


@router.get("/cover-preference")
async def cover_preference(user=Depends(get_current_user)):
    """Founder-wide default Cover Generation mode + the available modes (STD-COV-0001)."""
    mode = await bm.get_cover_preference()
    return {"mode": mode or "auto", "has_saved_default": bool(mode), "modes": bm.COVER_MODES}


@router.post("/books/{book_id}/design")
async def design(book_id: str, req: DesignReq = DesignReq(), user=Depends(require_super_admin)):
    r = await bm.design(book_id, user.get("name", "Founder"), req.base_url or "",
                        cover_mode=req.cover_mode, remember_preference=bool(req.remember_preference))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


class CoverReq(BaseModel):
    concept: int
    base_url: Optional[str] = ""


@router.post("/books/{book_id}/select-cover")
async def select_cover(book_id: str, req: CoverReq, user=Depends(require_super_admin)):
    r = await bm.select_cover(book_id, req.concept, user.get("name", "Founder"), req.base_url or "")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


class SanitizeReq(BaseModel):
    base_url: Optional[str] = ""


@router.post("/books/{book_id}/sanitize")
async def sanitize(book_id: str, req: SanitizeReq = SanitizeReq(), user=Depends(require_super_admin)):
    r = await bm.sanitization_pass(book_id, user.get("name", "Founder"), req.base_url or "")
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


@router.get("/books/{book_id}/audio")
async def audio(book_id: str, user=Depends(get_current_user)):
    r = await bm.audio_plan(book_id)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


@router.get("/books/{book_id}/video")
async def video(book_id: str, user=Depends(get_current_user)):
    r = await bm.video_plan(book_id)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


@router.get("/books/{book_id}/publish")
async def publish(book_id: str, user=Depends(get_current_user)):
    r = await bm.publish_center(book_id)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


@router.get("/books/{book_id}/monitor")
async def monitor(book_id: str, user=Depends(get_current_user)):
    r = await bm.monitor(book_id)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


class AudioPrototypeReq(BaseModel):
    voice: Optional[str] = None
    speed: Optional[float] = None
    custom_script: Optional[str] = None


@router.post("/books/{book_id}/audio-prototype")
async def audio_prototype(book_id: str, req: Optional[AudioPrototypeReq] = None, user=Depends(require_super_admin)):
    req = req or AudioPrototypeReq()
    r = await bm.render_audio_prototype(book_id, user.get("name", "Founder"),
                                        voice=req.voice, speed=req.speed, custom_script=req.custom_script)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


@router.get("/voices")
async def narration_voices(user=Depends(get_current_user)):
    return {"voices": bm.VALID_VOICES, "default": "sage"}


class FullAudiobookReq(BaseModel):
    voice: Optional[str] = None
    speed: Optional[float] = None


@router.post("/books/{book_id}/audiobook")
async def start_audiobook(book_id: str, req: Optional[FullAudiobookReq] = None, user=Depends(require_super_admin)):
    req = req or FullAudiobookReq()
    r = await bm.start_full_audiobook(book_id, user.get("name", "Founder"), voice=req.voice, speed=req.speed)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


@router.get("/books/{book_id}/audiobook/status")
async def audiobook_status(book_id: str, user=Depends(get_current_user)):
    return await bm.full_audiobook_status(book_id)


@router.get("/books/{book_id}/post-publish")
async def get_post_publish(book_id: str, user=Depends(get_current_user)):
    b = await bm.db[bm.COLL].find_one({"id": book_id})
    if not b:
        raise HTTPException(404, "Book Record not found.")
    return bm.clean(b).get("post_publish") or {"sections": [], "counts": {}, "not_run": True}


@router.post("/books/{book_id}/post-publish/run")
async def run_post_publish(book_id: str, user=Depends(require_super_admin)):
    r = await bm.run_post_publish_recipe(book_id, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


class PricingReq(BaseModel):
    list_price: float
    currency: Optional[str] = "USD"
    ebook_price: Optional[float] = None
    paperback_price: Optional[float] = None


@router.post("/books/{book_id}/pricing")
async def pricing(book_id: str, req: PricingReq, user=Depends(require_super_admin)):
    r = await bm.set_pricing(book_id, req.list_price, req.currency, user.get("name", "Founder"),
                             ebook_price=req.ebook_price, paperback_price=req.paperback_price)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


class AuthorizeReq(BaseModel):
    acknowledge_imprint_mismatch: Optional[bool] = False



@router.post("/books/{book_id}/authorize")
async def authorize(book_id: str, data: AuthorizeReq = AuthorizeReq(), user=Depends(require_super_admin)):
    ack = bool(data.acknowledge_imprint_mismatch) if data else False
    r = await bm.authorize_release(book_id, user.get("name", "Founder"), acknowledge_imprint_mismatch=ack)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


class RemoveFromStoreReq(BaseModel):
    reason: Optional[str] = ""


@router.post("/books/{book_id}/remove-from-store")
async def remove_from_store(book_id: str, data: RemoveFromStoreReq = RemoveFromStoreReq(), user=Depends(require_super_admin)):
    r = await bm.remove_from_store(book_id, user.get("name", "Founder"), (data.reason or "").strip())
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


@router.post("/books/{book_id}/relist-to-store")
async def relist_to_store(book_id: str, user=Depends(require_super_admin)):
    r = await bm.relist_to_store(book_id, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r



class PublicationDetailsReq(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    author_bio: Optional[str] = None
    include_blurb: Optional[bool] = None
    blurb_status: Optional[str] = None
    imprint: Optional[str] = None


@router.post("/books/{book_id}/publication-details")
async def publication_details(book_id: str, req: PublicationDetailsReq, user=Depends(require_super_admin)):
    fields = {k: v for k, v in req.dict().items() if v is not None}
    r = await bm.set_publication_details(book_id, fields, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


@router.post("/books/{book_id}/draft-blurb")
async def draft_blurb(book_id: str, user=Depends(require_super_admin)):
    r = await bm.draft_blurb(book_id, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


class PrintWrapReq(BaseModel):
    paper_type: Optional[str] = "white"


@router.post("/books/{book_id}/print-wrap")
async def print_wrap(book_id: str, req: PrintWrapReq = PrintWrapReq(), user=Depends(require_super_admin)):
    r = await bm.build_print_cover_wrap(book_id, req.paper_type, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


@router.get("/books/{book_id}/pricing-advisor")
async def pricing_advisor(book_id: str, paper_type: str = "white", user=Depends(get_current_user)):
    r = await bm.pricing_advisor(book_id, paper_type=paper_type)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


class PricingScenariosReq(BaseModel):
    prices: list
    paper_type: Optional[str] = "white"


@router.post("/books/{book_id}/pricing-scenarios")
async def pricing_scenarios(book_id: str, req: PricingScenariosReq, user=Depends(get_current_user)):
    r = await bm.pricing_advisor(book_id, scenarios=req.prices, paper_type=req.paper_type)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


class ShareReq(BaseModel):
    hours: Optional[int] = 72
    base_url: Optional[str] = ""


@router.post("/books/{book_id}/share")
async def share(book_id: str, req: ShareReq = ShareReq(), user=Depends(require_super_admin)):
    r = await bm.create_share(book_id, req.hours, user.get("name", "Founder"), req.base_url or "")
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


@router.get("/share/{token}")
async def resolve_share(token: str):
    import os
    from fastapi.responses import FileResponse, JSONResponse
    import rendering_engine as re_engine
    s = await bm.resolve_share(token)
    if s.get("error"):
        return JSONResponse(status_code=410 if "expired" in s["error"] else 404, content=s)
    fid = s["package_url"].rstrip("/").split("/")[-1]
    path = os.path.join(re_engine.ASSET_DIR, fid)
    if not os.path.exists(path):
        import storage
        await storage.aensure_local(fid, path)
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "Package file no longer available."})
    fname = "".join(c for c in s["book_title"] if c.isalnum() or c in " -_").strip().replace(" ", "_")
    return FileResponse(path, media_type="application/zip", filename=f"{fname}_Review_Copy.zip")


@router.post("/books/{book_id}/assemble-package")
async def assemble_package(book_id: str, user=Depends(require_super_admin)):
    r = await bm.assemble_master_package(book_id, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


@router.get("/books/{book_id}/master-package")
async def master_package(book_id: str, user=Depends(get_current_user)):
    r = await bm.master_package(book_id)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


@router.get("/books/{book_id}/kdp-checklist")
async def kdp_checklist(book_id: str, user=Depends(get_current_user)):
    r = await bm.build_kdp_checklist(book_id)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r


@router.get("/books/{book_id}/manifest")
async def get_manifest(book_id: str, user=Depends(get_current_user)):
    b = await bm.db[bm.COLL].find_one({"id": book_id}, {"_id": 0, "product_manifest": 1})
    if b is None:
        raise HTTPException(404, "Book Record not found.")
    return b.get("product_manifest") or {"not_generated": True,
        "note": "Product Manifest™ (PMF™) is generated automatically when the Master Output Package is assembled."}


@router.post("/books/{book_id}/manifest/build")
async def build_manifest(book_id: str, user=Depends(require_super_admin)):
    r = await bm.build_product_manifest(book_id, user.get("name", "Founder"))
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if r.get("error"):
        raise HTTPException(400, r["error"])
    return r

