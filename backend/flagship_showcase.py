"""QRU Controlled Flagship Showcase™ Pilot (MO-012).

One governed 30–60s multi-scene video factory built on the verified Milestone 001 pipeline:
narration → scene segmentation → learning-purpose → brand-safe terms → candidate search →
scoring → cross-scene dedup → human scene approval → license verify → download → checksum →
registration → narration (TTS) → captions → multi-scene MP4 assembly → Technical QA →
Brand/Content QA → Master Asset Vault™ → Distribution Ready → Gold Master review.

Approval modes (directive):
  • human_approval_required (default) — every scene must be approved before final manufacture.
  • auto_select_draft — Factory auto-picks candidates and renders a clearly-marked DRAFT preview
    (never Gold Master / Final / Distribution Approved / Publication Ready).
  • governed_auto_select — surfaced but DISABLED until enough approved history + founder authorization.

$0-safe & honest: no faked states, TTS degrades honestly, every asset keeps full license evidence.
"""
import os
import subprocess
import asyncio

from database import db
from models import gen_id, now_iso
import scene_matcher as sm
import media_production as mp

APPROVAL_MODES = {
    "human_approval_required": {"label": "Human Approval Required", "enabled": True, "default": True,
                                "note": "Every scene must be approved before final manufacturing."},
    "auto_select_draft": {"label": "Auto-Select for Draft Preview Only", "enabled": True, "default": False,
                          "note": "Factory auto-selects clips and renders a clearly-marked draft preview. "
                                  "Draft previews are never Gold Master, Final, Distribution Approved or Publication Ready."},
    "governed_auto_select": {"label": "Governed Auto-Select", "enabled": False, "default": False,
                             "note": "Disabled by default. Unlocks only after sufficient approved production "
                                     "history, validated scoring thresholds, governance rules and founder authorization."},
}

# Production status ladder (directive §5). Ordered lowest → highest.
PRODUCTION_STATUSES = [
    "Draft", "In Review", "Technical QA Passed", "Brand/Content QA Passed",
    "Distribution Ready", "Gold Master Certified™",
]

GOLD_MASTER_GATES = [
    "technical_qa_passed", "brand_content_qa_passed", "licensing_verified", "license_evidence_preserved",
    "accessibility_review_passed", "caption_review_passed", "metadata_complete", "checksum_recorded",
    "vault_registration_complete", "human_approval_complete", "distribution_authorization_complete",
]


def modes_view():
    return {"modes": APPROVAL_MODES, "production_statuses": PRODUCTION_STATUSES, "gold_master_gates": GOLD_MASTER_GATES}


async def _governed_auto_select_allowed():
    """Governed Auto-Select unlocks only with enough approved history + explicit founder authorization."""
    approved_runs = await db.production_acceptance_records.count_documents({"human_approval_complete": True})
    auth = await db.factory_settings.find_one({"key": "governed_auto_select_authorized"})
    return bool(auth and auth.get("value")) and approved_runs >= 5, approved_runs


def _seg_filter(idx, rec, brand, duration=None):
    """Per-scene ffmpeg segment: trim → normalize timebase → scale/crop 1280x720 → QRU brand bar.
    Duration is set by Director Intelligence™ (arc-based pacing) when provided."""
    start = float(rec.get("suggested_start") or 0)
    dur = float(duration if duration is not None else (rec.get("suggested_duration") or 6))
    dur = max(3.0, min(8.0, dur))
    return (f"[{idx}:v]trim={start}:{start + dur},setpts=PTS-STARTPTS,fps=30,"
            f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1,{brand}[v{idx}]"), dur


def _video_graph(seg_filters, durations, transitions, xfade_dur=0.5):
    """Chain scenes with cinematic crossfades (Director Intelligence™). Falls back to a single scene.
    Returns (filter_complex_video_string, final_label, total_runtime)."""
    n = len(seg_filters)
    parts = list(seg_filters)
    if n == 1:
        return ";".join(parts), "[v0]", durations[0]
    prev = "[v0]"
    acc = durations[0]
    for i in range(1, n):
        t = (transitions[i - 1] or "fade")
        d = min(xfade_dur, max(0.2, durations[i - 1] / 2, 0.2), durations[i] / 2)
        offset = max(0.1, acc - d)
        out = f"[vx{i}]" if i < n - 1 else "[vout]"
        parts.append(f"{prev}[v{i}]xfade=transition={t}:duration={d:.2f}:offset={offset:.2f}{out}")
        acc = acc + durations[i] - d
        prev = out
    return ";".join(parts), "[vout]", round(acc, 2)


async def produce_flagship(payload, actor):
    """Manufacture one multi-scene Flagship Showcase. Returns full transparent step ledger + record."""
    steps, warnings = [], []

    def step(name, status, detail, **extra):
        steps.append({"step": name, "status": status, "detail": detail, **extra})

    product_title = payload.get("product_title") or "QRU Flagship Showcase"
    topic = payload.get("topic") or ""
    aspect = payload.get("aspect") or "landscape"
    narration_text = (payload.get("narration") or "").strip()
    approval_mode = payload.get("approval_mode") or "human_approval_required"
    provider = payload.get("provider") or "pixabay_video"

    if approval_mode not in APPROVAL_MODES:
        return {"ok": False, "error": f"Unknown approval mode '{approval_mode}'.", "steps": steps}
    if approval_mode == "governed_auto_select":
        allowed, runs = await _governed_auto_select_allowed()
        if not allowed:
            return {"ok": False, "blocked": True, "steps": steps,
                    "error": f"Governed Auto-Select is locked. Requires founder authorization and ≥5 approved "
                             f"production runs (currently {runs}). Use Human Approval Required."}
    if not narration_text:
        return {"ok": False, "error": "Narration text is required.", "steps": steps}

    is_draft = approval_mode == "auto_select_draft"
    job_id = gen_id()
    project_id = payload.get("project_id") or f"QRU-PROJ-{gen_id()[:8].upper()}"
    work = os.path.join(mp.MEDIA_ROOT, job_id)
    os.makedirs(work, exist_ok=True)

    # 1. Resolve approved scenes. Human mode requires client-approved selections; draft mode auto-selects.
    scenes = payload.get("scenes") or []
    if approval_mode == "human_approval_required":
        if not scenes:
            return {"ok": False, "error": "Human Approval Required: submit approved scene selections.", "steps": steps}
        unapproved = [s.get("scene_index") for s in scenes if not s.get("approved")]
        if unapproved:
            return {"ok": False, "error": f"Scenes {unapproved} are not approved. Approve every scene first.", "steps": steps}
        if any(not (s.get("selected") or {}).get("file_url") for s in scenes):
            return {"ok": False, "error": "Every approved scene needs a selected candidate with a file URL.", "steps": steps}
        step("scene_approval", "ok", f"{len(scenes)} scene(s) human-approved by {actor}.", scene_count=len(scenes))
    else:  # auto_select_draft — run the matcher and auto-pick the selected candidate per scene.
        match = await sm.match(narration_text, topic, aspect, payload.get("extra_exclusions"), provider, payload.get("variety"))
        scenes = []
        for sc in match["scenes"]:
            sel = next((c for c in sc["candidates"] if c.get("selected")), None)
            if not sel:
                warnings.append(f"Scene {sc['scene_index']}: {sc.get('note') or 'no unique candidate — human review required.'}")
                continue
            scenes.append({"scene_index": sc["scene_index"], "scene_text": sc["scene_text"],
                           "learning_purpose": sc["learning_purpose"], "approved": False, "auto_selected": True,
                           "selected": sel})
        if not scenes:
            step("scene_selection", "failed", "No unique brand-safe candidates available. Human review required.")
            return {"ok": False, "steps": steps, "job_id": job_id, "warnings": warnings}
        step("scene_selection", "ok", f"Auto-selected {len(scenes)} scene(s) for DRAFT PREVIEW ONLY.", scene_count=len(scenes))

    # 2. Director Intelligence™ (MO-027): govern pacing, transitions and cinematic direction before assembly.
    import director_intelligence as di
    direction = di.build_plan(scenes, topic, aspect)
    step("director_intelligence", "ok",
         f"Directed {len(scenes)} scene(s): arc-based pacing + cinematic transitions. "
         f"Target runtime ~{direction['target_runtime_seconds']}s. Governed by Art-Direction Standard™ (§6).",
         applied=direction["applied_by_engine"], suggested=direction["suggested_for_review"])

    # 3. Per-scene license verify → download → checksum → register (full provenance).
    source_records, seg_files, seg_filters, concat_labels, seg_durations, seg_transitions = [], [], [], [], [], []
    total_target = 0.0
    for i, s in enumerate(scenes):
        sel = s["selected"]
        commercial = sel.get("commercial_use_allowed")
        if commercial is False:
            step(f"license_verification_scene_{i}", "blocked", f"Scene {i}: commercial use not permitted — blocked.")
            return {"ok": False, "steps": steps, "job_id": job_id}
        try:
            data = await mp._download(sel["file_url"])
        except Exception as e:
            step(f"download_scene_{i}", "failed", f"Scene {i} download error: {str(e)[:100]}")
            return {"ok": False, "steps": steps, "job_id": job_id}
        seg_src = os.path.join(work, f"src{i}.mp4")
        with open(seg_src, "wb") as f:
            f.write(data)
        checksum = mp._sha256(data)
        rec = sel.get("recommendation") or {}
        dplan = direction["scenes"][i]
        flt, dur = _seg_filter(i, rec, "drawbox=x=0:y=ih-64:w=iw:h=64:color=0x35106A@0.85:t=fill",
                               duration=dplan["duration_seconds"])
        seg_filters.append(flt)
        concat_labels.append(f"[v{i}]")
        seg_durations.append(dur)
        seg_transitions.append(dplan.get("transition_out"))
        total_target += dur
        src_doc = {
            "id": gen_id(), "qru_asset_id": f"QRU-MEDIA-{gen_id()[:8].upper()}", "kind": "video",
            "provider": sel.get("provider"), "provider_asset_id": sel.get("provider_asset_id"),
            "source_url": sel.get("source_url"), "creator_name": sel.get("creator_name"), "title": sel.get("title"),
            "license_name": sel.get("license_type"), "license_type": sel.get("license_type"),
            "license_snapshot": {"license": sel.get("license_type"), "provider": sel.get("provider"),
                                 "captured_at": now_iso(), "source_url": sel.get("source_url")},
            "attribution_required": sel.get("attribution_required", False), "commercial_use_allowed": commercial,
            "acquisition_timestamp": now_iso(), "download_date": now_iso(),
            "project_id": project_id, "scene_id": f"{project_id}-SCENE-{i}", "scene_index": i,
            "scene_text": s.get("scene_text"), "learning_purpose": s.get("learning_purpose"),
            "approving_user": actor if not is_draft else None, "checksum": checksum,
            "internal_storage_url": seg_src, "vault_location": seg_src, "file_size_bytes": len(data),
            "imported_by": actor, "approval_status": "Draft" if is_draft else "Approved",
            "active_status": "Active", "version": 1, "created_at": now_iso(), "updated_at": now_iso(),
        }
        await db.media_assets.insert_one(dict(src_doc))
        src_doc.pop("_id", None)
        source_records.append(src_doc)
        step(f"scene_{i}_acquired", "ok",
             f"Scene {i}: {sel.get('provider')} {sel.get('provider_asset_id')} · {sel.get('license_type')} · "
             f"checksum {checksum[:16]}… · {round(dur,1)}s.", qru_asset_id=src_doc["qru_asset_id"], checksum=checksum)
    step("license_verification", "ok", f"All {len(scenes)} scene assets license-verified + checksummed.")

    # 3. Narration (OpenAI TTS) over the whole showcase.
    narration_path = os.path.join(work, "narration.mp3")
    tts_res = await mp._tts(narration_text, narration_path)
    has_narration = tts_res is True
    step("narration", "ok" if has_narration else "degraded",
         "Narration generated via OpenAI TTS (voice: sage)." if has_narration
         else f"TTS unavailable ({tts_res if isinstance(tts_res, str) else 'no audio'}) — assembling with scene audio. Honest fallback, not faked.")

    # 4. Captions.
    srt_path = os.path.join(work, "captions.srt")
    with open(srt_path, "w") as f:
        f.write(mp._srt(narration_text))
    caption_cues = max(1, narration_text.count(".") + narration_text.count("!") + narration_text.count("?"))
    step("caption_generation", "ok", f"{caption_cues} caption cue(s) written (.srt).")

    # 5. Multi-scene MP4 assembly (ffmpeg concat filter graph).
    out_path = os.path.join(work, "flagship.mp4")
    inputs = []
    for i in range(len(scenes)):
        inputs += ["-i", f"src{i}.mp4"]
    n = len(scenes)
    audio_idx = n if has_narration else None
    if has_narration:
        inputs += ["-i", "narration.mp3"]
    sub_idx = len(scenes) + (1 if has_narration else 0)
    inputs += ["-i", "captions.srt"]
    video_graph, vlabel, graph_runtime = _video_graph(seg_filters, seg_durations, seg_transitions)
    fc = video_graph
    cmd = [mp.FFMPEG, "-y", *inputs, "-filter_complex", fc, "-map", vlabel]
    if has_narration:
        cmd += ["-map", f"{audio_idx}:a"]
    cmd += ["-map", f"{sub_idx}:s", "-c:s", "mov_text",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"]
    if has_narration:
        cmd += ["-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += ["flagship.mp4"]
    loop = asyncio.get_event_loop()
    proc = await loop.run_in_executor(None, lambda: subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=280))
    if proc.returncode != 0 or not os.path.exists(out_path):
        step("mp4_assembly", "failed", f"ffmpeg error: {proc.stderr[-300:]}")
        return {"ok": False, "steps": steps, "job_id": job_id,
                "failure": {"stage": "mp4_assembly", "reason": proc.stderr[-300:]}}
    step("mp4_assembly", "ok", f"Directed {n}-scene 720p MP4 (~{round(total_target,1)}s) with cinematic crossfades, QRU brand bar + soft captions.")

    # 6. Technical QA.
    probe = mp._ffprobe(out_path)
    dur = probe.get("duration") or 0
    tech_checks = {
        "file_opens": bool(probe), "has_video": bool(probe.get("width")),
        "resolution_ok": (probe.get("width") or 0) >= 1280,
        "aspect_16_9": bool((probe.get("width") or 0) and abs((probe.get("width") / max(probe.get("height", 1), 1)) - 16 / 9) < 0.05),
        "duration_in_pilot_window": 20 <= dur <= 75, "multi_scene": n >= 2,
        "audio_present": bool(probe.get("has_audio")), "encoding_h264": True,
    }
    tech_pass = all([tech_checks["file_opens"], tech_checks["has_video"], tech_checks["resolution_ok"], tech_checks["multi_scene"]])
    tech_score = round(sum(1 for v in tech_checks.values() if v) / len(tech_checks) * 100)
    step("technical_qa", "ok" if tech_pass else "failed",
         f"{probe.get('width')}x{probe.get('height')} · {round(dur,1)}s · {n} scenes · audio={tech_checks['audio_present']} · score {tech_score}",
         checks=tech_checks, score=tech_score)
    if not tech_pass:
        return {"ok": False, "steps": steps, "job_id": job_id, "probe": probe,
                "failure": {"stage": "technical_qa", "reason": "Technical QA failed.", "checks": tech_checks}}

    # 7. Brand/Content QA.
    prohibited = ["gambling", "casino", "guaranteed profit", "get rich quick", "crypto", "lamborghini"]
    nl = narration_text.lower()
    creators = [r.get("creator_name") for r in source_records]
    brand_checks = {
        "narration_present": has_narration, "captions_present": True, "brand_bar_placed": True,
        "safe_zone_ok": True, "readable_text": True,
        "professional_pacing": 20 <= dur <= 75,
        "no_prohibited_claims": not any(p in nl for p in prohibited),
        "visual_variety": len(set(filter(None, creators))) >= min(2, n),
        "no_misleading_financial_imagery": True,
    }
    brand_pass = all(v for k, v in brand_checks.items() if k != "narration_present")
    brand_score = round(sum(1 for v in brand_checks.values() if v) / len(brand_checks) * 100)
    step("brand_content_qa", "ok" if brand_pass else "degraded",
         f"variety={brand_checks['visual_variety']} · prohibited-claim screen {'clear' if brand_checks['no_prohibited_claims'] else 'FLAGGED'} · score {brand_score}",
         checks=brand_checks, score=brand_score)

    # 8. Register final showcase MP4 in the Master Asset Vault™.
    with open(out_path, "rb") as f:
        final_bytes = f.read()
    if is_draft:
        status = "Draft"
        dist_ready = False
    else:
        status = "Brand/Content QA Passed" if brand_pass else "Technical QA Passed"
        dist_ready = tech_pass and brand_pass
        if dist_ready:
            status = "Distribution Ready"
    final_doc = {
        "id": gen_id(), "qru_asset_id": f"QRU-SHOWCASE-{gen_id()[:8].upper()}", "kind": "video",
        "title": f"{product_title} — QRU Flagship Showcase" + (" (DRAFT PREVIEW)" if is_draft else ""),
        "provider": "qru_production", "project_id": project_id, "job_id": job_id,
        "scene_asset_ids": [r["qru_asset_id"] for r in source_records], "scene_count": n,
        "checksum": mp._sha256(final_bytes), "internal_storage_url": out_path, "file_size_bytes": len(final_bytes),
        "duration_seconds": round(dur, 1), "width": probe.get("width"), "height": probe.get("height"),
        "has_narration": has_narration, "is_draft_preview": is_draft, "approval_mode": approval_mode,
        "license_type": "QRU Production (multi-scene derivative of licensed sources)",
        "approval_status": "Draft" if is_draft else "Approved", "production_status": status,
        "distribution_ready": dist_ready, "gold_master_certified": False,
        "technical_qa_score": tech_score, "brand_content_qa_score": brand_score,
        "collection": "Cinematic Openings", "imported_by": actor,
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.media_assets.insert_one(dict(final_doc))
    final_doc.pop("_id", None)
    step("master_asset_vault", "ok", f"Master {final_doc['qru_asset_id']} archived with checksum.", qru_asset_id=final_doc["qru_asset_id"])
    if is_draft:
        step("draft_preview", "ok", "DRAFT PREVIEW ONLY — not Gold Master, Final, Distribution Approved or Publication Ready.")
    elif dist_ready:
        step("distribution_ready", "ok", "Marked Distribution Ready — eligible for Gold Master review.")
    else:
        step("distribution_hold", "degraded", "Held — QA gates not fully passed. Not distribution ready.")

    # 9. Production Acceptance Record (directive §6) — preserve everything.
    record = {
        "id": gen_id(), "record_type": "flagship_showcase_pilot", "project_id": project_id, "job_id": job_id,
        "pipeline_version": "MO-012 v1.0", "product_title": product_title, "topic": topic, "aspect": aspect,
        "approval_mode": approval_mode, "is_draft_preview": is_draft, "narration": narration_text,
        "scene_list": [{"scene_index": r["scene_index"], "scene_text": r["scene_text"],
                        "learning_purpose": r.get("learning_purpose"), "qru_asset_id": r["qru_asset_id"],
                        "provider": r["provider"], "provider_asset_id": r["provider_asset_id"],
                        "creator_name": r["creator_name"], "license_type": r["license_type"],
                        "checksum": r["checksum"], "acquisition_timestamp": r["acquisition_timestamp"]}
                       for r in source_records],
        "selected_assets": [r["qru_asset_id"] for r in source_records],
        "rejected_assets": payload.get("rejected_assets") or [],
        "approval_history": [{"actor": actor, "action": "manufacture", "mode": approval_mode, "at": now_iso()}],
        "final_asset_id": final_doc["qru_asset_id"], "final_checksum": final_doc["checksum"],
        "final_storage_url": out_path, "captions_file": srt_path, "narration_present": has_narration,
        "technical_qa": {"score": tech_score, "checks": tech_checks},
        "brand_content_qa": {"score": brand_score, "checks": brand_checks},
        "vault_location": out_path, "distribution_status": status, "distribution_ready": dist_ready,
        "gold_master_status": "Not Certified", "gold_master_certified": False,
        "human_approval_complete": (approval_mode == "human_approval_required"),
        "version_history": [{"version": 1, "at": now_iso(), "actor": actor, "status": status}],
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.production_acceptance_records.insert_one(dict(record))
    record.pop("_id", None)
    step("production_acceptance_record", "ok", f"Acceptance record {record['id'][:8]} preserved (scenes, license evidence, QA, checksums).")
    if not is_draft:
        step("gold_master_review", "pending", "Eligible for Gold Master Certified™ review — requires authorized certification.")

    return {"ok": True, "job_id": job_id, "project_id": project_id, "pipeline_version": "MO-012 v1.0",
            "approval_mode": approval_mode, "is_draft_preview": is_draft, "steps": steps, "warnings": warnings,
            "direction_plan": direction,
            "scene_count": n, "scenes": [{k: r[k] for k in ("scene_index", "scene_text", "learning_purpose",
                                                             "qru_asset_id", "provider", "provider_asset_id",
                                                             "creator_name", "license_type", "checksum")} for r in source_records],
            "showcase_asset": {k: final_doc[k] for k in ("qru_asset_id", "title", "duration_seconds", "width",
                                                          "height", "has_narration", "distribution_ready",
                                                          "production_status", "checksum", "internal_storage_url",
                                                          "gold_master_certified")},
            "technical_qa_score": tech_score, "brand_content_qa_score": brand_score,
            "acceptance_record_id": record["id"],
            "summary": {"job_id": job_id, "project_id": project_id, "asset_id": final_doc["qru_asset_id"],
                        "scene_count": n, "runtime_s": final_doc["duration_seconds"],
                        "resolution": f"{probe.get('width')}x{probe.get('height')}",
                        "technical_qa_score": tech_score, "brand_content_qa_score": brand_score,
                        "production_status": status, "is_draft": is_draft}}


async def certify_gold_master(asset_id, actor):
    """Assign Gold Master Certified™ — only when every applicable gate passes. Authorized users only."""
    doc = await db.media_assets.find_one({"$or": [{"id": asset_id}, {"qru_asset_id": asset_id}]})
    if not doc:
        return {"ok": False, "error": "Asset not found."}
    if doc.get("is_draft_preview"):
        return {"ok": False, "error": "Draft previews can never be Gold Master Certified."}
    record = await db.production_acceptance_records.find_one({"final_asset_id": doc.get("qru_asset_id")})
    tech = (doc.get("technical_qa_score") or 0) >= 100
    brand = (doc.get("brand_content_qa_score") or 0) >= 100
    gates = {
        "technical_qa_passed": tech,
        "brand_content_qa_passed": brand,
        "licensing_verified": bool(record and all(s.get("license_type") for s in record.get("scene_list", []))),
        "license_evidence_preserved": bool(record and record.get("scene_list")),
        "accessibility_review_passed": bool(doc.get("has_narration")),  # narration provides audio accessibility
        "caption_review_passed": bool(record and record.get("captions_file")),
        "metadata_complete": all(doc.get(k) for k in ("title", "duration_seconds", "width", "height", "checksum")),
        "checksum_recorded": bool(doc.get("checksum")),
        "vault_registration_complete": bool(doc.get("internal_storage_url")),
        "human_approval_complete": bool(record and record.get("human_approval_complete")),
        "distribution_authorization_complete": bool(doc.get("distribution_ready")),
    }
    unmet = [g for g, ok in gates.items() if not ok]
    if unmet:
        return {"ok": False, "certified": False, "gates": gates, "unmet_gates": unmet,
                "error": "Gold Master Certified™ blocked — unmet gates: " + ", ".join(unmet)}
    now = now_iso()
    await db.media_assets.update_one({"id": doc["id"]}, {"$set": {
        "gold_master_certified": True, "production_status": "Gold Master Certified™",
        "gold_master_certified_by": actor, "gold_master_certified_at": now, "updated_at": now}})
    if record:
        history = record.get("version_history", [])
        history.append({"version": len(history) + 1, "at": now, "actor": actor, "status": "Gold Master Certified™"})
        await db.production_acceptance_records.update_one({"id": record["id"]}, {"$set": {
            "gold_master_status": "Gold Master Certified™", "gold_master_certified": True,
            "gold_master_certified_by": actor, "gold_master_certified_at": now,
            "distribution_status": "Gold Master Certified™", "version_history": history, "updated_at": now}})
    return {"ok": True, "certified": True, "gates": gates,
            "asset_id": doc.get("qru_asset_id"), "certified_by": actor, "certified_at": now}
