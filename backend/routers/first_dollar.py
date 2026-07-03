"""QRU First Dollar Mode™ endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
import first_dollar as fd

router = APIRouter(prefix="/api/first-dollar", tags=["first-dollar-mode"])


@router.get("/status")
async def status(user=Depends(get_current_user)):
    return await fd.status()


@router.post("/check-milestone")
async def check_milestone(user=Depends(get_current_user)):
    return await fd.check_and_record_milestone()


class ModeInput(BaseModel):
    mode: str


@router.post("/mode")
async def set_mode(data: ModeInput, user=Depends(get_current_user)):
    return {"mode": await fd.set_mode(data.mode)}
