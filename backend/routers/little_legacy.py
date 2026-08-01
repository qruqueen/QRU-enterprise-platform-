"""Little Legacy Learners™ Animation Studio API — a governed capability of the QRU Factory™.

Phase 1 (Foundation): exposes the version-controlled data layer — the Universe Bible, the six
canonical Character Bibles, world locations, the Five Responsibilities, the Knowledge Flow, governance
gates and Knowledge-First Episode Blueprints. Nothing here generates animation, voice or video; those
are later governed phases. Every write respects canon protection and the Knowledge-First rule.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from auth import get_current_user
import little_legacy as ll
import little_legacy_production as llp
import little_legacy_animation as lla

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


# ─────────── PHASE 2 — Character Mastering ───────────
@router.post("/characters/{char_key}/master")
async def master_character(char_key: str, user=Depends(get_current_user)):
    res = await llp.master_character(char_key, actor=user.get("email", "Founder"))
    if res is None:
        raise HTTPException(404, "Character not found.")
    return res


@router.get("/characters/{char_key}/master")
async def master_character_status(char_key: str, user=Depends(get_current_user)):
    return await llp.master_status(char_key)


@router.get("/masters")
async def masters(user=Depends(get_current_user)):
    return {"masters": await llp.list_masters()}


class MasterApproval(BaseModel):
    consistency_confirmed: bool = False


@router.post("/masters/{char_key}/approve")
async def approve_master(char_key: str, body: MasterApproval = MasterApproval(), user=Depends(get_current_user)):
    res = await llp.approve_master(char_key, actor=user.get("email", "Founder"), consistency_confirmed=body.consistency_confirmed)
    if res is None:
        raise HTTPException(404, "Master not found.")
    return res


@router.get("/masters/{char_key}/{kind}.png")
async def master_file(char_key: str, kind: str):
    if kind not in ("model_sheet", "expression_sheet"):
        raise HTTPException(404, "Unknown sheet.")
    p = llp.master_file_path(char_key, kind)
    if not p.exists():
        raise HTTPException(404, "Not rendered yet.")
    return FileResponse(str(p), media_type="image/png")


# ─────────── PHASE 3 — Pilot Episode Manufacturing ───────────
class PilotReq(BaseModel):
    teaser: Optional[bool] = False


@router.post("/episodes/{episode_id}/pilot")
async def manufacture_pilot(episode_id: str, body: PilotReq = PilotReq(), user=Depends(get_current_user)):
    res = await llp.manufacture_pilot(episode_id, actor=user.get("email", "Founder"), teaser=bool(body.teaser))
    if res is None:
        raise HTTPException(404, "Episode not found.")
    return res


@router.get("/episodes/{episode_id}/pilot")
async def pilot_status(episode_id: str, user=Depends(get_current_user)):
    return await llp.pilot_status(episode_id)


@router.get("/pilots")
async def pilots(user=Depends(get_current_user)):
    return {"pilots": await llp.list_pilots()}


@router.post("/pilots/{episode_id}/approve")
async def approve_pilot(episode_id: str, user=Depends(get_current_user)):
    res = await llp.approve_pilot(episode_id, actor=user.get("email", "Founder"))
    if res is None:
        raise HTTPException(404, "Pilot not found.")
    return res


class PublishYouTubeReq(BaseModel):
    privacy: Optional[str] = "private"


@router.post("/pilots/{episode_id}/publish-youtube")
async def publish_pilot_youtube(episode_id: str, body: PublishYouTubeReq = PublishYouTubeReq(), user=Depends(get_current_user)):
    res = await llp.publish_pilot_youtube(episode_id, actor=user.get("email", "Founder"), privacy=body.privacy or "private")
    if res is None:
        raise HTTPException(404, "Pilot not found.")
    return res


@router.get("/pilots/{episode_id}.mp4")
async def pilot_file(episode_id: str):
    p = llp.pilot_file_path(episode_id)
    if not p.exists():
        raise HTTPException(404, "Pilot not rendered yet.")
    return FileResponse(str(p), media_type="video/mp4")


@router.get("/pilots/{episode_id}.srt")
async def pilot_captions(episode_id: str):
    p = llp.captions_file_path(episode_id)
    if not p.exists():
        raise HTTPException(404, "Captions not available yet.")
    return FileResponse(str(p), media_type="text/plain")


# ─────────── PHASE 4 — Product Kit (kid-format inheriting recipes) ───────────
@router.post("/episodes/{episode_id}/kit")
async def manufacture_kit(episode_id: str, user=Depends(get_current_user)):
    res = await llp.manufacture_kit(episode_id, actor=user.get("email", "Founder"))
    if res is None:
        raise HTTPException(404, "Episode not found.")
    return res


@router.get("/episodes/{episode_id}/kit")
async def kit_status(episode_id: str, user=Depends(get_current_user)):
    return await llp.kit_status(episode_id)


@router.get("/kits")
async def kits(user=Depends(get_current_user)):
    return {"kits": await llp.list_kits()}


@router.post("/kits/{episode_id}/approve")
async def approve_kit(episode_id: str, user=Depends(get_current_user)):
    res = await llp.approve_kit(episode_id, actor=user.get("email", "Founder"))
    if res is None:
        raise HTTPException(404, "Kit not found.")
    return res


@router.post("/episodes/{episode_id}/family")
async def manufacture_family(episode_id: str, user=Depends(get_current_user)):
    res = await llp.manufacture_family(episode_id, actor=user.get("email", "Founder"))
    if res is None:
        raise HTTPException(404, "Episode not found.")
    return res


@router.get("/episodes/{episode_id}/family")
async def family_status(episode_id: str, user=Depends(get_current_user)):
    return await llp.family_status(episode_id)


@router.get("/kits/{episode_id}/{kind}.png")
async def kit_file(episode_id: str, kind: str):
    p = llp.kit_file_path(episode_id, kind)
    if not p.exists():
        raise HTTPException(404, "Not rendered yet.")
    return FileResponse(str(p), media_type="image/png")


# ─────────── PHASE 4 — Little Legacy Project Zero™ feedback ───────────
class FeedbackInput(BaseModel):
    episode_id: str
    role: Optional[str] = "parent"
    rating: Optional[int] = None
    understanding_before: Optional[int] = None
    understanding_after: Optional[int] = None
    comment: Optional[str] = None
    suggested_improvement: Optional[str] = None


@router.post("/feedback")
async def submit_feedback(body: FeedbackInput, user=Depends(get_current_user)):
    return await llp.submit_feedback(body.episode_id, body.dict(), actor=user.get("email", "Founder"))


@router.get("/feedback")
async def feedback_loop(episode_id: str, user=Depends(get_current_user)):
    return await llp.feedback_loop(episode_id)


# ─────────── QRU Animation Manufacturing Platform™ ───────────
@router.get("/animation/status")
async def animation_status(episode_id: Optional[str] = None, user=Depends(get_current_user)):
    return await lla.engine_status(episode_id)


@router.get("/animation/providers")
async def animation_providers(user=Depends(get_current_user)):
    return await lla.list_providers()


@router.post("/animation/providers/{provider_id}/activate")
async def activate_provider(provider_id: str, user=Depends(get_current_user)):
    return await lla.set_active_provider(provider_id)


@router.get("/animation/performance-library")
async def performance_library(user=Depends(get_current_user)):
    return lla.performance_library()


@router.get("/animation/identity/{char_key}")
async def identity_package(char_key: str, user=Depends(get_current_user)):
    idp = await lla.identity_package(char_key)
    if not idp:
        raise HTTPException(404, "Character not found.")
    return idp


@router.get("/animation/identities")
async def identities(user=Depends(get_current_user)):
    out = []
    for c in ll.CHARACTERS:
        idp = await lla.identity_package(c["key"])
        if idp:
            out.append(idp)
    return {"identities": out}


@router.post("/animation/performance-plan/{episode_id}")
async def build_plan(episode_id: str, user=Depends(get_current_user)):
    plan = await lla.build_performance_plan(episode_id, actor=user.get("email", "Founder"))
    if plan is None:
        raise HTTPException(404, "Episode not found.")
    return plan


@router.get("/animation/performance-plan/{episode_id}")
async def get_plan(episode_id: str, user=Depends(get_current_user)):
    return await lla.get_performance_plan(episode_id) or {"beats": []}
