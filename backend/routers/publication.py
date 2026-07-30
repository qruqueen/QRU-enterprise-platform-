"""Governed Publication Policy™ (STD-PUB-0001) — router."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user, require_super_admin
from database import db
import publication_policy as pp

router = APIRouter(prefix="/api/publication", tags=["publication"])


async def _resolve(engine, record_id):
    coll = {"book": "book_records", "publication": "products", "product": "products"}.get(engine, "products")
    return await db[coll].find_one({"id": record_id}, {"_id": 0}) \
        or await db[coll].find_one({"book_code": record_id}, {"_id": 0}) \
        or await db[coll].find_one({"product_code": record_id}, {"_id": 0})


@router.get("/config")
async def config(user=Depends(get_current_user)):
    await pp.seed_enterprise_policy()
    return {"standard": pp.STANDARD_ID, "modes": pp.PUBLICATION_MODES, "requirements": pp.REQUIREMENTS,
            "inheritance_scopes": pp.INHERITANCE_SCOPES,
            "default_destination_modes": pp.DEFAULT_DESTINATION_MODES, "fallback_mode": pp.FALLBACK_MODE}


@router.get("/policies")
async def policies(user=Depends(get_current_user)):
    await pp.seed_enterprise_policy()
    return {"policies": await db[pp.POLICY_COLL].find({}, {"_id": 0}).to_list(500)}


class PolicyReq(BaseModel):
    scope: str
    scope_id: str
    destination: str
    mode: str
    reason: Optional[str] = ""


@router.post("/policy")
async def set_policy(req: PolicyReq, user=Depends(require_super_admin)):
    r = await pp.set_policy(req.scope, req.scope_id, req.destination, req.mode,
                            actor=user.get("name", "Founder"), reason=req.reason or "")
    if r.get("error"):
        raise HTTPException(400, r["error"])
    return r


@router.get("/decide/{engine}/{record_id}")
async def decide(engine: str, record_id: str, destination: str, user=Depends(get_current_user)):
    p = await _resolve(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    return await pp.decide(p, destination)


@router.get("/resolve/{engine}/{record_id}")
async def resolve(engine: str, record_id: str, destination: str, user=Depends(get_current_user)):
    p = await _resolve(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    return await pp.resolve_policy(p, destination)


class PublishReq(BaseModel):
    destination: str


@router.post("/publish/{engine}/{record_id}")
async def publish(engine: str, record_id: str, req: PublishReq, user=Depends(require_super_admin)):
    p = await _resolve(engine, record_id)
    if not p:
        raise HTTPException(404, "Product not found.")
    return await pp.publish(p, req.destination, actor=user.get("name", "Founder"))


@router.get("/history")
async def history(product_id: Optional[str] = None, user=Depends(get_current_user)):
    return {"history": await pp.publication_history(product_id)}
