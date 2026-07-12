"""QRU Enterprise Architecture Foundation API (STD-EIP-0002)."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from auth import get_current_user
import enterprise_architecture as ea

router = APIRouter(prefix="/api/architecture", tags=["enterprise-architecture"])


@router.get("/domains")
async def domains(user=Depends(get_current_user)):
    return ea.domains_view()


@router.get("/layers")
async def layers(user=Depends(get_current_user)):
    return ea.layers_view()


@router.get("/modules")
async def modules(user=Depends(get_current_user)):
    return {"modules": ea.MODULES, "count": len(ea.MODULES)}


@router.get("/intentions")
async def intentions(view: str = "ent", user=Depends(get_current_user)):
    return ea.intentions_view(view)


@router.get("/why")
async def why(route: str, user=Depends(get_current_user)):
    return ea.why_am_i_here(route)


@router.get("/explorer")
async def explorer(route: str, user=Depends(get_current_user)):
    d = ea.explorer(route)
    if not d:
        raise HTTPException(404, "Module not found in the Architecture Explorer.")
    return d
