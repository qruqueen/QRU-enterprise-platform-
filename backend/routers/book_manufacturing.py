"""QRU Book Manufacturing System™ v1.0 — router. Orchestrates the seven-button workflow."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from auth import get_current_user, require_super_admin
import book_manufacturing as bm

router = APIRouter(prefix="/api/book-mfg", tags=["book-manufacturing"])


class UploadPayload(BaseModel):
    title: str
    content: str
    meta: Optional[Dict[str, Any]] = None


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return {"buttons": bm.SEVEN_BUTTONS, "publish_destinations": bm.PUBLISH_DESTINATIONS}


@router.get("/books")
async def books(user=Depends(get_current_user)):
    return {"books": await bm.list_books()}


@router.get("/books/{book_id}")
async def get_book(book_id: str, user=Depends(get_current_user)):
    b = await bm.get_book(book_id)
    if not b:
        raise HTTPException(404, "Book Record not found.")
    return b


@router.post("/upload")
async def upload(payload: UploadPayload, user=Depends(require_super_admin)):
    return await bm.create_book_record(payload.dict(), user.get("name", "Founder"))


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


class DesignReq(BaseModel):
    base_url: Optional[str] = ""


@router.post("/books/{book_id}/design")
async def design(book_id: str, req: DesignReq = DesignReq(), user=Depends(require_super_admin)):
    r = await bm.design(book_id, user.get("name", "Founder"), req.base_url or "")
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    if isinstance(r, dict) and r.get("error"):
        raise HTTPException(400, r["error"])
    return r


class CoverReq(BaseModel):
    concept: int


@router.post("/books/{book_id}/select-cover")
async def select_cover(book_id: str, req: CoverReq, user=Depends(require_super_admin)):
    r = await bm.select_cover(book_id, req.concept, user.get("name", "Founder"))
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


@router.get("/books/{book_id}/master-package")
async def master_package(book_id: str, user=Depends(get_current_user)):
    r = await bm.master_package(book_id)
    if r is None:
        raise HTTPException(404, "Book Record not found.")
    return r
