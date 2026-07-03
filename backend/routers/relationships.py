"""QRU Enterprise Relationship Engine™ endpoints."""
from fastapi import APIRouter, Depends

from auth import get_current_user
import relationship_engine as re

router = APIRouter(prefix="/api/relationships", tags=["relationship-engine"])


@router.get("/graph")
async def graph(user=Depends(get_current_user)):
    return await re.graph_overview()


@router.get("/schema")
async def schema(user=Depends(get_current_user)):
    return {"schema": re.SCHEMA}


@router.get("/object/{otype}/{oid}")
async def obj(otype: str, oid: str, user=Depends(get_current_user)):
    return await re.object_relationships(otype, oid)


@router.get("/suggest/{otype}/{oid}")
async def suggest(otype: str, oid: str, user=Depends(get_current_user)):
    return await re.suggest(otype, oid)
