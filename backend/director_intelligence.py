"""QRU Director Intelligence™ (MO-027) — part of Design Intelligence™, governed by the Treasure Standard™
and Constitution §6 (Art Direction). Turns automatic assembly into governed cinematic direction.

Produces a Direction Plan: emotional arc, scene pacing, visual variety, camera-movement suggestions,
transition selection, text/music timing, learning reinforcement, closing CTA, thumbnail concept, and
viewer-retention notes. HONEST: each directive is labeled 'applied' (the render engine executes it now)
or 'suggested' (needs the font/music engine — not faked as rendered).
"""

# Emotional arc roles assigned by position in the narration.
_ARC = ["Hook", "Context", "Insight", "Reinforcement", "Closing CTA"]

# xfade transition names the bundled ffmpeg supports — chosen for meaning, cycled for variety.
_TRANSITIONS = ["fade", "fadeblack", "dissolve", "slideleft", "smoothright", "wipeleft"]

# Target seconds per arc role (clamped 3–8 in the render).
_ROLE_DURATION = {"Hook": 4.0, "Context": 5.5, "Insight": 6.5, "Reinforcement": 5.0, "Closing CTA": 4.5}
_ROLE_ENERGY = {"Hook": 92, "Context": 68, "Insight": 85, "Reinforcement": 60, "Closing CTA": 74}
_ROLE_CAMERA = {
    "Hook": "Slow push-in (Ken Burns zoom-in) to draw the viewer in.",
    "Context": "Gentle pan to establish the setting.",
    "Insight": "Hold steady, then subtle zoom to emphasize the key idea.",
    "Reinforcement": "Slow pull-back (zoom-out) to give reflective space.",
    "Closing CTA": "Static, centered — let the call to action land.",
}


def _role_for(i, n):
    if n == 1:
        return "Insight"
    if i == 0:
        return "Hook"
    if i == n - 1:
        return "Closing CTA"
    if i == n - 2:
        return "Reinforcement"
    return "Insight" if i % 2 else "Context"


def build_plan(scenes, topic="", aspect="landscape"):
    """scenes: list of {scene_index, scene_text, learning_purpose}. Returns a governed Direction Plan."""
    n = len(scenes)
    scene_plans = []
    for i, s in enumerate(scenes):
        role = _role_for(i, n)
        dur = max(3.0, min(8.0, _ROLE_DURATION[role]))
        transition = _TRANSITIONS[i % len(_TRANSITIONS)] if i < n - 1 else None
        scene_plans.append({
            "scene_index": s.get("scene_index", i),
            "arc_role": role,
            "energy": _ROLE_ENERGY[role],
            "duration_seconds": dur,
            "camera_move": _ROLE_CAMERA[role],
            "transition_out": transition,
            "transition_label": (transition or "final hold").replace("fadeblack", "dip to black").replace("smoothright", "smooth right").title(),
            "text_timing": "Caption in after 0.4s, out 0.4s before the cut." if role != "Closing CTA" else "Hold the CTA caption for the full scene.",
            "pacing_note": {"Hook": "Keep it tight — earn the first 3 seconds.",
                            "Context": "Let it breathe to orient the viewer.",
                            "Insight": "Give the key idea room to land.",
                            "Reinforcement": "Slow down for retention.",
                            "Closing CTA": "Calm, clear, decisive."}[role],
        })
    total = sum(sp["duration_seconds"] for sp in scene_plans)
    closing_cta = f"Learn more about {topic} with QRU — verified, governed understanding." if topic else \
        "Explore more governed knowledge with QRU."
    hero_idx = max(range(n), key=lambda i: scene_plans[i]["energy"]) if n else 0
    return {
        "engine": "Director Intelligence™ (MO-027)",
        "governed_by": ["QRU-CON-0001 §6 Art-Direction Standard", "Treasure Standard™"],
        "scene_count": n,
        "target_runtime_seconds": round(total, 1),
        "emotional_flow": [{"scene": sp["scene_index"], "role": sp["arc_role"], "energy": sp["energy"]} for sp in scene_plans],
        "scenes": scene_plans,
        "music_cues": [
            {"at": "0s", "cue": "Soft ambient enters under the Hook — low volume beneath narration."},
            {"at": "mid", "cue": "Lift subtly at the first Insight to signal importance."},
            {"at": "close", "cue": "Resolve gently under the Closing CTA."},
        ],
        "learning_reinforcement": "Restate the single most important idea during the Reinforcement scene, "
                                  "then anchor it in the Closing CTA.",
        "closing_cta": closing_cta,
        "thumbnail_concept": {
            "hero_scene_index": hero_idx,
            "overlay_text_suggestion": (topic.title() if topic else "QRU"),
            "note": "Use the highest-energy scene's mid-frame as the hero; add a short 2–4 word overlay.",
        },
        "retention_optimization": [
            "Open on the strongest visual within 3 seconds (the Hook).",
            "Change the visual at every scene to avoid monotony (visual variety enforced by the Scene Asset Matcher™).",
            "Use a pattern interrupt (transition) between scenes to reset attention.",
            "End with a clear, single call to action.",
        ],
        # HONEST capability split (Treasure Standard™): what the render engine executes now vs. suggestions.
        "applied_by_engine": [
            "Scene pacing (arc-based durations)",
            "Transition selection (cinematic crossfades between scenes)",
            "Visual variety (deduplicated footage per scene)",
            "Soft caption timing (embedded captions)",
        ],
        "suggested_for_review": [
            "Camera movement (Ken Burns) — planned; awaiting the motion-render upgrade.",
            "On-screen text & CTA overlays — planned; the bundled renderer lacks font support (drawtext).",
            "Music bed & timing — planned; awaiting the Licensed Sound Library™ (MO-023).",
            "Thumbnail overlay text — planned; hero frame is auto-selected today.",
        ],
    }
