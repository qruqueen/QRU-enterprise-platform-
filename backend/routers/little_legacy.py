"""Little Legacy Learners™ Animation Studio API — a governed capability of the QRU Factory™.

Phase 1 (Foundation): exposes the version-controlled data layer — the Universe Bible, the six
canonical Character Bibles, world locations, the Five Responsibilities, the Knowledge Flow, governance
gates and Knowledge-First Episode Blueprints. Nothing here generates animation, voice or video; those
are later governed phases. Every write respects canon protection and the Knowledge-First rule.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from auth import get_current_user
import little_legacy as ll

router = APIRouter(prefix="/api/little-legacy", tags=["little-legacy"])


@router.post("/seed")
async def seed(force: bool = False, user=Depends(get_current_user)):
    return await ll.seed(force=force)


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    return await ll.overview()


@router.get("/universe-bible")
async def universe_bible(user=Depends(get_current_user)):
    ub = await ll.get_universe_bible()
    if not ub:
        raise HTTPException(404, "Universe Bible not seeded yet.")
    return ub


@router.post("/universe-bible/approve")
async def approve_universe_bible(user=Depends(get_current_user)):
    res = await ll.approve_universe_bible(actor=user.get("email", "Founder"))
    if res is None:
        raise HTTPException(404, "Universe Bible not seeded yet.")
    return res


@router.get("/characters")
async def characters(user=Depends(get_current_user)):
    return {"characters": await ll.list_characters()}


@router.get("/characters/{char_id}")
async def character(char_id: str, user=Depends(get_current_user)):
    c = await ll.get_character(char_id)
    if not c:
        raise HTTPException(404, "Character not found.")
    return c


class CharacterUpdate(BaseModel):
    changes: Dict[str, Any]
    founder_approved: bool = False


@router.put("/characters/{char_id}")
async def update_character(char_id: str, body: CharacterUpdate, user=Depends(get_current_user)):
    res = await ll.update_character(char_id, body.changes, founder_approved=body.founder_approved)
    if res is None:
        raise HTTPException(404, "Character not found.")
    return res


@router.post("/characters/{char_id}/approve")
async def approve_character(char_id: str, user=Depends(get_current_user)):
    res = await ll.approve_character(char_id, actor=user.get("email", "Founder"))
    if res is None:
        raise HTTPException(404, "Character not found.")
    return res


@router.get("/locations")
async def locations(user=Depends(get_current_user)):
    return {"locations": await ll.list_locations()}


@router.get("/episodes")
async def episodes(user=Depends(get_current_user)):
    return {"episodes": await ll.list_episodes()}


@router.get("/memory")
async def memory(user=Depends(get_current_user)):
    return {"events": await ll.memory_ledger()}


class EpisodeInput(BaseModel):
    kr_id: Optional[str] = None
    title: Optional[str] = None
    age_band: Optional[str] = None
    featured_character_key: Optional[str] = None


@router.post("/episodes")
async def create_episode(body: EpisodeInput, user=Depends(get_current_user)):
    return await ll.create_episode_blueprint(
        body.kr_id, body.title, body.age_band, body.featured_character_key,
        actor=user.get("email", "Founder"))


@router.post("/episodes/{episode_id}/approve")
async def approve_episode(episode_id: str, user=Depends(get_current_user)):
    res = await ll.approve_episode(episode_id, actor=user.get("email", "Founder"))
    if res is None:
        raise HTTPException(404, "Episode not found.")
    return res
