"""QRU Store Health™ — founder-only read-only store integrity endpoint."""
from fastapi import APIRouter, Depends

from auth import require_super_admin
import store_health as sh

router = APIRouter(prefix="/api/store", tags=["store-health"])


@router.get("/health")
async def store_health(user=Depends(require_super_admin)):
    return await sh.report()
