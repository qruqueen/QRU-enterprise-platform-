"""QRU Factory Readiness Score™ API (MT-026) — read-only decision-support."""
from fastapi import APIRouter, Depends

from auth import get_current_user
import readiness

router = APIRouter(prefix="/api/readiness", tags=["readiness"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await readiness.compute_readiness()
