"""QRU Manufacturing Economics™ API (MT-028) — read-only financial transparency + reports."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from auth import get_current_user
import economics

router = APIRouter(prefix="/api/economics", tags=["economics"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await economics.overview()


@router.get("/product/{pid}")
async def product(pid: str, user=Depends(get_current_user)):
    from database import db
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    return await economics.economics_row(p)


@router.get("/export/csv")
async def export_csv(user=Depends(get_current_user)):
    data = await economics.overview()
    return Response(content=economics.to_csv(data), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="QRU_Economics_Report.csv"'})


@router.get("/export/pdf")
async def export_pdf(user=Depends(get_current_user)):
    data = await economics.overview()
    return Response(content=economics.to_pdf(data), media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="QRU_Economics_Report.pdf"'})
