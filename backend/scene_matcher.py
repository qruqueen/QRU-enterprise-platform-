"""QRU Scene Asset Matcher™ (MO-021 intelligence layer).

Transforms narration/storyboard into governed, brand-safe media recommendations:
narration → scenes → learning purpose → literal/metaphorical/emotional/environmental search terms
(+ topic exclusion terms) → search APPROVED providers only → top-5 scored candidates per scene with
crop/duration/start/end/speed/transition/text-safe guidance. Human approves/replaces/rejects.

$0 & honest: scoring is deterministic from real asset metadata; nothing is auto-published; every
candidate keeps its license status. Never forces stock footage into every scene.
"""
import re

import media_library as ml

_STOP = set("the a an and or of to in for with on at is are be by from this that your you our we it as "
            "will can may does do how what why when where which who into over under more most less".split())

# Learning-purpose classification by keyword.
_PURPOSE = [
    ("Risk & Caution", ["risk", "loss", "danger", "caution", "warning", "protect", "mistake", "margin", "leverage"]),
    ("Definition / Concept", ["what", "means", "definition", "is a", "understand", "concept", "term", "pair", "currency"]),
    ("Process / How-it-works", ["how", "process", "works", "step", "flow", "move", "exchange", "trade", "session"]),
    ("Motivation / Encouragement", ["begin", "start", "journey", "confidence", "learn", "grow", "continue", "responsibly"]),
    ("Reflection / Calm", ["breath", "calm", "peace", "reflect", "quiet", "still", "renew", "gratitude", "hope"]),
]

# Emotional & metaphorical term expansion.
_EMOTION_TERMS = {
    "Risk & Caution": ["storm clouds", "steady hands", "safety net", "balance"],
    "Definition / Concept": ["clear glass", "building blocks", "open book", "focused study"],
    "Process / How-it-works": ["flowing water", "connected network", "moving gears", "world map connections"],
    "Motivation / Encouragement": ["sunrise", "open road", "climbing steps", "first light"],
    "Reflection / Calm": ["calm ocean", "quiet forest", "soft light", "gentle rain"],
}
_ENV_TERMS = {
    "forex": ["global financial district", "world city skyline", "international business", "trading floor calm"],
    "trading": ["financial data screen", "world map network", "city time lapse"],
    "reflection": ["peaceful forest", "mountain sunrise", "calm sea horizon"],
    "learning": ["library study", "focused learner", "classroom light"],
}

# Topic-aware exclusion terms (Treasure Standard — brand-safe).
_EXCLUSIONS = {
    "forex": ["gambling", "casino", "guaranteed profit", "get rich quick", "piles of money", "luxury cars",
              "cryptocurrency", "misleading charts", "reckless trading", "inaccurate currency symbols"],
    "trading": ["gambling", "casino", "guaranteed profit", "lamborghini", "stacks of cash"],
    "default": ["explicit content", "violence", "misleading claims", "brand conflict"],
}

_TEXT_SAFE = {"landscape": "lower-third band (bottom 25%) or left third", "portrait": "center-lower third",
              "square": "center band"}


def _keywords(text, limit=5):
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower())
    freq = {}
    for w in words:
        if w in _STOP:
            continue
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]


def _classify(sentence):
    low = sentence.lower()
    for label, kws in _PURPOSE:
        if any(k in low for k in kws):
            return label
    return "Definition / Concept"


def split_scenes(narration):
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", narration) if s.strip()]
    # Group into scenes of ~1-2 sentences.
    scenes, buf = [], []
    for p in parts:
        buf.append(p)
        if len(buf) >= 2 or len(p) > 140:
            scenes.append(" ".join(buf)); buf = []
    if buf:
        scenes.append(" ".join(buf))
    return scenes or [narration]


def generate_terms(scene_text, purpose, topic):
    kw = _keywords(scene_text)
    literal = kw[:4]
    emotional = _EMOTION_TERMS.get(purpose, [])[:3]
    env_key = next((k for k in _ENV_TERMS if k in (topic or "").lower() or k in scene_text.lower()), None)
    environmental = _ENV_TERMS.get(env_key, _ENV_TERMS["reflection"])[:3]
    metaphorical = emotional[:2] + environmental[:1]
    return {"literal": literal, "metaphorical": metaphorical, "emotional": emotional, "environmental": environmental}


def exclusions_for(topic, extra=None):
    key = next((k for k in _EXCLUSIONS if k in (topic or "").lower()), "default")
    ex = list(_EXCLUSIONS[key])
    if key != "default":
        ex += _EXCLUSIONS["default"]
    if extra:
        ex += [e.strip() for e in extra if e.strip()]
    return sorted(set(ex))


def _score(item, scene_kw, exclusions):
    """0-100 deterministic score from real metadata (MO-021 §12 weights, condensed)."""
    title = str(item.get("title") or "").lower()
    # subject relevance (35): keyword overlap.
    hits = sum(1 for k in scene_kw if k in title)
    relevance = min(35, 12 + hits * 8)
    # technical (20): resolution.
    w = item.get("width") or 0
    technical = 20 if w >= 3840 else 16 if w >= 1920 else 10 if w >= 1280 else 4
    # composition/text-safe (15): duration in a usable range.
    d = item.get("duration_seconds") or 0
    composition = 15 if 6 <= d <= 40 else 9 if d else 6
    # brand fit (15): calm/nature/abstract/clean words present.
    brand_words = ("nature", "calm", "forest", "ocean", "light", "abstract", "city", "world", "business", "finance", "study")
    brand = 8 + min(7, sum(2 for b in brand_words if b in title))
    # licensing (10) + representation (5).
    licensing = 10 if item.get("commercial_use_allowed") else 5
    representation = 5
    excluded = any(x in title for x in exclusions)
    total = 0 if excluded else min(100, relevance + technical + composition + brand + licensing + representation)
    return {"total": total, "relevance": relevance, "technical": technical, "composition": composition,
            "brand_fit": brand, "licensing": licensing, "representation": representation, "excluded": excluded}


def _recommendation(item, aspect):
    d = item.get("duration_seconds") or 10
    start = 1 if d > 8 else 0
    return {
        "suggested_crop": {"landscape": "16:9 center", "portrait": "9:16 center", "square": "1:1 center"}.get(aspect, "16:9 center"),
        "suggested_start": start, "suggested_end": min(d, start + 8), "suggested_duration": min(8, max(4, d - start)),
        "suggested_speed": "0.75x (calm)" if (item.get("duration_seconds") or 0) < 6 else "1.0x",
        "suggested_transition": "cross-dissolve (0.5s)",
        "text_safe_zone": _TEXT_SAFE.get(aspect, _TEXT_SAFE["landscape"]),
        "brand_overlay": "QRU gold lower-third + logo",
    }


def _reason(score, scene_kw, item):
    if score["excluded"]:
        return "Rejected — contains an excluded/brand-unsafe subject."
    bits = []
    if score["relevance"] >= 20:
        bits.append("strong subject match")
    if score["technical"] >= 16:
        bits.append("high resolution")
    if score["brand_fit"] >= 13:
        bits.append("on-brand mood")
    if score["licensing"] >= 10:
        bits.append("clear commercial license")
    return "Recommended — " + ", ".join(bits) + "." if bits else "Usable baseline match."


async def match(narration, topic="", aspect="landscape", extra_exclusions=None, provider="pixabay_video"):
    scenes_txt = split_scenes(narration)
    exclusions = exclusions_for(topic, extra_exclusions)
    out = []
    for idx, scene in enumerate(scenes_txt):
        purpose = _classify(scene)
        terms = generate_terms(scene, purpose, topic)
        kw = _keywords(scene)
        # Prefer a curated environmental/metaphorical term (meaningful + brand-safe) over raw keywords.
        query = (terms["environmental"][0] if terms["environmental"] else None) or " ".join(terms["literal"][:2]) or (topic or "learning")
        res = await ml.search(provider, query, 8)
        candidates = []
        if res.get("configured") and res.get("results"):
            scored = []
            for it in res["results"]:
                sc = _score(it, kw, exclusions)
                if sc["excluded"]:
                    continue
                scored.append((sc, it))
            scored.sort(key=lambda x: x[0]["total"], reverse=True)
            for sc, it in scored[:5]:
                candidates.append({
                    "provider": it.get("provider"), "provider_asset_id": it.get("provider_asset_id"),
                    "title": it.get("title"), "creator_name": it.get("creator_name"),
                    "preview_url": it.get("preview_url"), "file_url": it.get("file_url"),
                    "source_url": it.get("source_url"), "width": it.get("width"), "height": it.get("height"),
                    "duration_seconds": it.get("duration_seconds"), "license_type": it.get("license_type"),
                    "commercial_use_allowed": it.get("commercial_use_allowed"),
                    "score": sc, "match_score": sc["total"], "reason": _reason(sc, kw, it),
                    "recommendation": _recommendation(it, aspect),
                    "tier": "Gold Gallery" if sc["total"] >= 90 else "Approved" if sc["total"] >= 80 else "Shortlist" if sc["total"] >= 70 else "Below threshold",
                })
        out.append({
            "scene_index": idx, "scene_text": scene, "learning_purpose": purpose,
            "search_terms": terms, "primary_query": query, "keywords": kw,
            "candidates": candidates, "candidate_count": len(candidates),
            "note": None if candidates else (res.get("reason") or res.get("error") or "No brand-safe candidates found — consider a QRU illustration or diagram instead."),
        })
    return {"scenes": out, "scene_count": len(out), "exclusions": exclusions, "aspect_ratio": aspect,
            "provider": provider, "topic": topic}
