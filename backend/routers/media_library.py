"""QRU Media Acquisition Foundation™ — API surface (MO-021 Stock Video + MO-023 Audio)."""
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import db
from auth import get_current_user, require_super_admin
import media_library as ml

router = APIRouter(prefix="/api/media-library", tags=["media-library"])


def _clean(doc):
    doc.pop("_id", None)
    return doc


@router.get("/config")
async def config(user=Depends(get_current_user)):
    return ml.config()


@router.get("/providers")
async def providers(user=Depends(get_current_user)):
    return {"providers": await ml.provider_status()}


class KeyInput(BaseModel):
    api_key: str


@router.post("/providers/{provider_id}/config")
async def configure(provider_id: str, data: KeyInput, user=Depends(require_super_admin)):
    ok, err, code = await ml.save_provider_key(provider_id, data.api_key, user["name"])
    if not ok:
        # err is a TEST_CODE (INVALID_KEY/RATE_LIMITED/...) or a message — surface it, never the key.
        raise HTTPException(400, f"Connection not validated: {err}. The key was NOT saved.")
    return {"configured": True, "provider_id": provider_id, "status": "ACTIVE", "test_code": code}


@router.post("/providers/{provider_id}/test")
async def test(provider_id: str, user=Depends(require_super_admin)):
    return {"provider_id": provider_id, "test_code": await ml.retest_provider(provider_id, user["name"])}


@router.delete("/providers/{provider_id}/config")
async def revoke(provider_id: str, user=Depends(require_super_admin)):
    await ml.revoke_provider_key(provider_id, user["name"])
    return {"revoked": True, "provider_id": provider_id}


@router.get("/providers/{provider_id}/logs")
async def logs(provider_id: str, user=Depends(require_super_admin)):
    rows = await db.credential_logs.find({"provider_id": provider_id}, {"_id": 0}).sort("at", -1).to_list(100)
    return {"logs": rows}


class SearchInput(BaseModel):
    provider_id: str
    query: str
    per_page: Optional[int] = 12


@router.post("/search")
async def search(data: SearchInput, user=Depends(get_current_user)):
    return await ml.search(data.provider_id, data.query, min(int(data.per_page or 12), 30))


class RegisterInput(BaseModel):
    item: dict
    collection: Optional[str] = None
    listening_purpose: Optional[str] = None


@router.post("/register")
async def register(data: RegisterInput, user=Depends(require_super_admin)):
    return await ml.register_asset(data.item, data.collection, data.listening_purpose, user["name"])


@router.get("/assets")
async def assets(kind: Optional[str] = None, user=Depends(get_current_user)):
    q = {"kind": kind} if kind else {}
    rows = await db.media_assets.find(q).sort("created_at", -1).to_list(500)
    return {"assets": [_clean(r) for r in rows], "count": len(rows)}


@router.get("/collections")
async def collections(user=Depends(get_current_user)):
    return {"video_collections": ml.VIDEO_COLLECTIONS, "audio_collections": ml.AUDIO_COLLECTIONS}


class ProofInput(BaseModel):
    provider_id: Optional[str] = "pixabay_video"
    query: Optional[str] = "peaceful forest sunrise"
    product_title: Optional[str] = "Forex Foundations"


@router.post("/produce-proof")
async def produce_proof(data: ProofInput, user=Depends(require_super_admin)):
    import media_production as mp
    res = await ml.search(data.provider_id, data.query, 5)
    if not res.get("results"):
        return {"ok": False, "job_id": None, "steps": [
            {"step": "live_provider_search", "status": "failed",
             "detail": res.get("reason") or res.get("error") or "No results to produce from."}]}
    item = dict(res["results"][0])
    item["search_query_used"] = data.query
    return await mp.produce_showcase(item, data.product_title, user["name"],
                                     milestone={"code": "QRU-MILESTONE-001", "title": "First Live Licensed Media Acquisition"},
                                     project_id="QRU-PROJ-FOREX-FOUNDATIONS")


@router.get("/milestones")
async def milestones(user=Depends(get_current_user)):
    rows = await db.factory_milestones.find({}, {"_id": 0}).sort("achieved_at", -1).to_list(50)
    return {"milestones": rows}


class SceneMatchInput(BaseModel):
    narration: str
    topic: Optional[str] = ""
    aspect: Optional[str] = "landscape"
    extra_exclusions: Optional[list] = None
    provider: Optional[str] = "pixabay_video"
    variety: Optional[dict] = None


@router.post("/scene-match")
async def scene_match(data: SceneMatchInput, user=Depends(get_current_user)):
    import scene_matcher as sm
    if not data.narration.strip():
        raise HTTPException(400, "Narration text is required.")
    return await sm.match(data.narration, data.topic or "", data.aspect or "landscape",
                          data.extra_exclusions, data.provider or "pixabay_video", data.variety)


# --- MO-012 Controlled Flagship Showcase™ Pilot ---
@router.get("/showcase/modes")
async def showcase_modes(user=Depends(get_current_user)):
    import flagship_showcase as fs
    view = fs.modes_view()
    allowed, runs = await fs._governed_auto_select_allowed()
    view["governed_auto_select_unlocked"] = allowed
    view["approved_run_count"] = runs
    return view


class FlagshipInput(BaseModel):
    product_title: Optional[str] = "QRU Flagship Showcase"
    topic: Optional[str] = ""
    aspect: Optional[str] = "landscape"
    narration: str
    approval_mode: Optional[str] = "human_approval_required"
    provider: Optional[str] = "pixabay_video"
    scenes: Optional[list] = None
    extra_exclusions: Optional[list] = None
    variety: Optional[dict] = None
    project_id: Optional[str] = None
    rejected_assets: Optional[list] = None


@router.post("/showcase/produce")
async def showcase_produce(data: FlagshipInput, user=Depends(require_super_admin)):
    import flagship_showcase as fs
    return await fs.produce_flagship(data.model_dump(), user["name"])


@router.get("/showcase/records")
async def showcase_records(user=Depends(get_current_user)):
    rows = await db.production_acceptance_records.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"records": rows, "count": len(rows)}


@router.get("/showcase/records/{record_id}")
async def showcase_record(record_id: str, user=Depends(get_current_user)):
    doc = await db.production_acceptance_records.find_one(
        {"$or": [{"id": record_id}, {"job_id": record_id}, {"project_id": record_id}]}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Acceptance record not found.")
    return doc


@router.post("/showcase/{asset_id}/certify-gold-master")
async def certify_gold_master(asset_id: str, user=Depends(require_super_admin)):
    import flagship_showcase as fs
    res = await fs.certify_gold_master(asset_id, user["name"])
    if not res.get("ok"):
        raise HTTPException(400, res.get("error") or "Certification failed.")
    return res


@router.get("/asset/{asset_id}/file")
async def asset_file(asset_id: str):
    from fastapi.responses import FileResponse
    import media_production as mp
    doc = await db.media_assets.find_one({"$or": [{"id": asset_id}, {"qru_asset_id": asset_id}]})
    if not doc or not doc.get("internal_storage_url"):
        raise HTTPException(404, "Asset file not found.")
    path = os.path.abspath(doc["internal_storage_url"])
    if not path.startswith(os.path.abspath(mp.MEDIA_ROOT)) or not os.path.exists(path):
        raise HTTPException(404, "File not available.")
    return FileResponse(path, media_type="video/mp4")
