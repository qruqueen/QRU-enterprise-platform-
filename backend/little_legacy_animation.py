"""QRU Animation Manufacturing Platform™ — vendor-agnostic character animation.

Built as PLATFORM, not a vendor integration. Three pillars + one new pipeline layer:

  1) Canonical Character Identity System™ — identity stored ONCE per character (appearance, palette,
     facial proportions, expressions, personality, voice, vocabulary, movement style, emotional style)
     and handed IDENTICALLY to every provider. This is what makes consistency scale.
  2) Character Performance Library™ — a reusable, extensible catalog of performance primitives
     (expressions, gestures, walks, emotional transitions, idles, entrances, exits, educational poses).
  3) Animation Provider Layer — any current or FUTURE AI animation model plugs in through ONE interface
     (AnimationProvider). Nothing else in the Factory changes when providers are swapped — no vendor lock-in.

Pipeline (the new Performance Plan layer inserted as requested):
    Knowledge Record™ → Storyboard → Performance Plan → Animation → Assembly

The QRU Character Performance Engine™ turns a data-driven Performance Plan + Identity Packages into a
finished scene through whichever provider is ACTIVE. Default = StoryboardMotion (camera motion — honestly
NOT character motion) so the whole platform is testable with zero vendor lock-in. Connect a real motion
provider later and the SAME plan yields moving characters, with no other Factory code changing.
"""
from database import db
from models import gen_id, now_iso
import little_legacy as ll
import little_legacy_production as llp


# ─────────────────────────── 1. CANONICAL CHARACTER IDENTITY SYSTEM ───────────────────────────
# Identity that lives OUTSIDE any provider. Stored once; every provider receives the same package.
MOVEMENT_STYLE = {
    "nova-sparkle": {"face": "soft round face, large curious brown eyes, warm open smile", "movement": "confident, springy, leads with the heart", "emotion": "hopeful, curious, encouraging"},
    "sunny-bee": {"face": "round cheeks, bright eyes, beaming grin", "movement": "bouncy, buzzy, generous", "emotion": "cheerful, warm, giving"},
    "tilly-turtle": {"face": "gentle eyes behind glasses, calm smile", "movement": "slow, steady, deliberate", "emotion": "patient, calm, reassuring"},
    "bella-butterfly": {"face": "kind eyes, soft smile", "movement": "graceful, floaty, light", "emotion": "expressive, uplifting, kind"},
    "eli-elephant": {"face": "thoughtful eyes, gentle smile", "movement": "grounded, gentle, careful", "emotion": "thoughtful, wise, gentle"},
    "rio-rainbow": {"face": "friendly bright eyes, inclusive smile", "movement": "energetic, welcoming, inclusive", "emotion": "upbeat, friendly, community-minded"},
}
VOCABULARY = {
    "_default": ["let's find out", "I wonder", "great question", "we can do this", "let's be kind", "keep learning"],
    "nova-sparkle": ["Big dreams start small!", "Let's discover together!", "I wonder why…", "You can do it!"],
    "sunny-bee": ["Sharing is caring!", "Let's help!", "Sweet as honey!"],
    "tilly-turtle": ["Slow and steady", "Let's take our time", "Patience, friends"],
    "bella-butterfly": ["You are wonderful!", "Spread your wings!", "Be kind to yourself"],
    "eli-elephant": ["Let's remember", "I never forget a friend", "Think it through"],
    "rio-rainbow": ["Everyone belongs!", "All colors together!", "Let's include everyone"],
}


async def identity_package(char_key):
    """The single, canonical identity package handed IDENTICALLY to every animation provider."""
    c = await db.ll_characters.find_one({"key": char_key}, {"_id": 0})
    if not c:
        return None
    m = await db.ll_character_masters.find_one({"key": char_key}, {"_id": 0}) or {}
    style = MOVEMENT_STYLE.get(char_key, {})
    vp = m.get("voice_profile") or llp.VOICE_PROFILES.get(char_key, {"voice": "fable", "tone": "warm"})
    return {
        "key": char_key, "character": c["name"], "role": c.get("role"),
        "canon_locked": bool(c.get("anchor_locked")),
        "version": c.get("version", "0.1"),
        "canonical_appearance": {"anchor_url": m.get("anchor_url") or m.get("model_sheet_url"),
                                 "expression_sheet_url": m.get("expression_sheet_url"),
                                 "description": c.get("identity"),
                                 "canon_notes": c.get("canon_notes", [])},
        "color_palette": c.get("color_palette") or c.get("palette", []),
        "facial_proportions": style.get("face", "soft rounded, large expressive eyes, gentle smile"),
        "personality": c.get("role"),
        "voice": vp,
        "vocabulary": VOCABULARY.get(char_key, VOCABULARY["_default"]),
        "movement_style": style.get("movement", "warm, purposeful, child-friendly"),
        "emotional_style": style.get("emotion", "optimistic, encouraging"),
        "signature_prop": c.get("signature_prop"),
        "identity_standard": ll.IDENTITY_STANDARD,
    }


# ─────────────────────────── 2. CHARACTER PERFORMANCE LIBRARY ───────────────────────────
# A reusable, extensible catalog. `target` is the roadmap capacity per category; `seed` is the
# canonical starter set shipped today (honestly a starter, designed to grow to target).
PERFORMANCE_LIBRARY = {
    "facial_expressions": {"target": 300, "seed": ["neutral", "happy", "curious", "proud", "kind", "surprised",
        "thoughtful", "excited", "gentle", "delighted", "concerned", "hopeful", "playful", "focused", "reassured"]},
    "hand_gestures": {"target": 120, "seed": ["wave", "point-left", "point-right", "point-up", "thumbs-up",
        "open-arms", "present", "count-fingers", "clap", "hand-on-heart", "beckon", "shrug"]},
    "walk_cycles": {"target": 40, "seed": ["idle-stand", "confident-walk", "gentle-walk", "excited-skip",
        "slow-steady", "float", "bouncy"]},
    "emotional_transitions": {"target": 80, "seed": ["neutral→excited", "curious→understanding", "worried→reassured",
        "surprised→delighted", "thinking→confident", "calm→joyful"]},
    "idle_animations": {"target": 60, "seed": ["breathe", "blink", "look-around", "sway", "hold-prop", "tilt-head"]},
    "entrances": {"target": 40, "seed": ["walk-in-left", "walk-in-right", "pop-up", "float-down", "spin-in"]},
    "exits": {"target": 40, "seed": ["wave-goodbye", "walk-off-right", "float-up", "skip-away"]},
    "educational_poses": {"target": 100, "seed": ["explain", "point-to-board", "hold-up-object", "count-together",
        "read-book", "raise-hand", "big-reveal", "invite-to-think"]},
}


def performance_library():
    cats = []
    for cat, d in PERFORMANCE_LIBRARY.items():
        cats.append({"category": cat, "label": cat.replace("_", " ").title(),
                     "target_capacity": d["target"], "shipped": len(d["seed"]), "primitives": d["seed"]})
    return {"categories": cats,
            "total_shipped": sum(len(d["seed"]) for d in PERFORMANCE_LIBRARY.values()),
            "total_target": sum(d["target"] for d in PERFORMANCE_LIBRARY.values()),
            "note": "Canonical starter library. Every character inherits this shared taxonomy and performs it "
                    "in their own identity style. Designed to grow to target capacity — no per-clip reinvention."}


# ─────────────────────────── 3. PLUGGABLE ANIMATION PROVIDER LAYER ───────────────────────────
class AnimationProvider:
    """One interface every animation model implements. The Factory depends on THIS, not on any vendor."""
    id = "base"
    name = "Base Provider"
    kind = "abstract"
    produces_character_motion = False

    def available(self):
        return (False, "Not implemented.")

    async def render_beat(self, identity, beat, keyframe_png=None):
        raise NotImplementedError


class StoryboardMotionProvider(AnimationProvider):
    """Default, always-available. Cinematic CAMERA motion on approved key-art (Ken Burns) — honestly NOT
    character motion. Guarantees the platform is fully testable with zero vendor lock-in."""
    id = "storyboard-motion"
    name = "QRU Storyboard Motion (built-in)"
    kind = "builtin"
    produces_character_motion = False

    def available(self):
        return (True, None)

    async def render_beat(self, identity, beat, keyframe_png=None):
        return {"status": "rendered", "technique": "camera-motion",
                "note": "Cinematic pan/zoom on the approved identity anchor. The camera moves; the character does not."}


class ExternalMotionProvider(AnimationProvider):
    """A slot representing any pluggable AI character-motion model. Reports UNavailable until a real provider
    is registered/connected — this is the vendor-agnostic seam. Connecting one changes nothing else."""
    id = "character-motion"
    name = "QRU Character Motion (provider slot)"
    kind = "external"
    produces_character_motion = True

    def available(self):
        return (False, "No character-motion provider is connected yet. Any AI animation model can be plugged "
                       "into this slot through the Animation Provider Layer without changing the rest of the Factory.")

    async def render_beat(self, identity, beat, keyframe_png=None):
        return {"status": "pending", "technique": "character-motion",
                "note": "Awaiting a connected character-motion provider."}


_REGISTRY = {p.id: p for p in [StoryboardMotionProvider(), ExternalMotionProvider()]}


def register_provider(provider):
    """Future models plug in here. The rest of the Factory is unaffected."""
    _REGISTRY[provider.id] = provider


async def _active_id():
    cfg = await db.ll_animation_config.find_one({"key": "config"}) or {}
    return cfg.get("active_provider", "storyboard-motion")


async def list_providers():
    active = await _active_id()
    out = []
    for pid, p in _REGISTRY.items():
        ok, reason = p.available()
        out.append({"id": pid, "name": p.name, "kind": p.kind,
                    "produces_character_motion": p.produces_character_motion,
                    "available": ok, "reason": reason, "active": pid == active})
    return {"providers": out, "active": active}


async def set_active_provider(pid):
    p = _REGISTRY.get(pid)
    if not p:
        return {"ok": False, "message": "Unknown provider."}
    ok, reason = p.available()
    if not ok:
        return {"ok": False, "message": f"Cannot activate — {reason}"}
    await db.ll_animation_config.update_one({"key": "config"}, {"$set": {"key": "config", "active_provider": pid, "updated_at": now_iso()}}, upsert=True)
    await ll.remember("animation_provider_activated", f"Active animation provider set to {p.name}.", "Founder", pid)
    return {"ok": True, "active": pid, "message": f"Active animation provider: {p.name}."}


# ─────────────────────────── 4. PERFORMANCE PLAN (new pipeline layer) ───────────────────────────
# Data-driven direction per storyboard beat. Animation becomes DATA, not hand-built clips.
_BEAT_DIRECTION = {
    "Title": {"expression": "happy", "gesture": "wave", "walk": "confident-walk", "emotion": "excited", "camera": "wide-establishing", "pose": "big-reveal"},
    "Curiosity": {"expression": "curious", "gesture": "point-up", "walk": "idle-stand", "emotion": "curious→understanding", "camera": "medium", "pose": "invite-to-think"},
    "Understand": {"expression": "proud", "gesture": "present", "walk": "gentle-walk", "emotion": "thinking→confident", "camera": "medium", "pose": "explain"},
    "Real life": {"expression": "happy", "gesture": "point-left", "walk": "gentle-walk", "emotion": "neutral→excited", "camera": "wide", "pose": "point-to-board"},
    "Your turn": {"expression": "kind", "gesture": "open-arms", "walk": "idle-stand", "emotion": "calm→joyful", "camera": "close", "pose": "raise-hand"},
    "Treasure Takeaway™": {"expression": "delighted", "gesture": "clap", "walk": "excited-skip", "emotion": "surprised→delighted", "camera": "wide", "pose": "celebrate"},
}


async def build_performance_plan(episode_id, actor="Founder"):
    ep = await db.ll_episodes.find_one({"id": episode_id})
    if not ep:
        return None
    import kr_inheritance as kri
    kr = await kri.load_kr(db, ep.get("primary_kr")) if ep.get("primary_kr") else None
    inh = kri.build_inheritance(kr) if kr else {}
    char = next((x for x in ll.CHARACTERS if x["key"] == ep.get("featured_character")), None)
    _, scenes = llp._build_scenes(ep, inh, char)
    idp = await identity_package(char["key"]) if char else None
    voice = (idp or {}).get("voice", {}).get("voice", "fable")

    beats = []
    for i, sc in enumerate(scenes, 1):
        d = _BEAT_DIRECTION.get(sc["label"], _BEAT_DIRECTION["Understand"])
        beats.append({
            "beat": i, "scene": sc["label"], "line": sc["narration"], "caption": sc["caption"],
            "character": (char or {}).get("name", "Ensemble"), "character_key": ep.get("featured_character"),
            "expression": d["expression"], "gesture": d["gesture"], "walk": d["walk"],
            "emotion": d["emotion"], "voice": voice, "camera": d["camera"], "educational_pose": d["pose"],
        })
    plan = {
        "id": gen_id(), "episode_id": episode_id, "title": ep.get("title"),
        "featured_character": ep.get("featured_character"), "beats": beats,
        "identity_package_ref": (char or {}).get("key"),
        "created_by": actor, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.ll_performance_plans.update_one({"episode_id": episode_id}, {"$set": plan}, upsert=True)
    await ll.remember("performance_plan_built", f"Performance Plan built for '{ep.get('title')}' ({len(beats)} beats).", actor, episode_id)
    return plan


async def get_performance_plan(episode_id):
    return await db.ll_performance_plans.find_one({"episode_id": episode_id}, {"_id": 0})


# ─────────────────────────── QRU CHARACTER PERFORMANCE ENGINE™ ───────────────────────────
async def engine_status(episode_id=None):
    providers = await list_providers()
    active = _REGISTRY[providers["active"]]
    ok, reason = active.available()
    plan = await get_performance_plan(episode_id) if episode_id else None
    return {
        "engine": "QRU Character Performance Engine™",
        "pipeline": ["Knowledge Record™", "Storyboard", "Performance Plan", "Animation", "Assembly"],
        "active_provider": {"id": active.id, "name": active.name,
                            "produces_character_motion": active.produces_character_motion,
                            "available": ok, "reason": reason},
        "provider_layer": providers["providers"],
        "identity_system": "Canonical Character Identity System™ — one identity package per character, handed identically to every provider.",
        "performance_plan_ready": bool(plan),
        "render_note": ("Active provider produces true character motion." if active.produces_character_motion and ok
                        else "Active provider produces cinematic camera motion (Animated Storybook). Connect a character-motion provider to the Provider Layer to make characters move — the same Performance Plan will drive it."),
    }
