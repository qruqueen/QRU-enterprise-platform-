"""QRU Governed Product Description Manufacturing™ (STD-MFG-0001) + Governed Back Cover Manufacturing™
(STD-BLB-0001, an application of STD-MFG-0001).

CONSTITUTIONAL RULE:
    The Factory shall NEVER require generative AI to manufacture a customer-facing description when
    sufficient verified enterprise knowledge exists. Generative AI is an OPTIONAL enhancement layer,
    never a manufacturing dependency.

Three manufacturing modes (every product, every marketplace):
    1. Governed Manufacturing™  (DEFAULT, 0 AI credits) — assemble a polished description from verified
       metadata using constitutional templates. Every sentence is traceable to a source field.
    2. AI Enhancement™          (OPTIONAL) — marketplace-optimized variants, grounded in the same
       verified metadata. Turn on/off per product & budget.
    3. Founder Canonical™       (0 AI credits) — the Founder writes/approves the definitive text; the
       Factory stores it as canonical and reuses it wherever appropriate.

Applies to books, workbooks, guides, courses, videos, audiobooks, posters, PDFs, bundles, Knowledge
Records, reports, checklists, templates, business docs — and every storefront channel (Amazon/KDP,
Etsy, Teachers Pay Teachers, QRU Online, and any future marketplace).
"""
import re
from datetime import datetime, timezone

from database import db

STANDARD_ID = "STD-MFG-0001"
BACK_COVER_STANDARD_ID = "STD-BLB-0001"

MODES = [
    {"id": "governed", "name": "Governed Manufacturing™", "ai_credits": 0, "default": True,
     "desc": "Assembled from verified metadata using constitutional templates. Every sentence traceable. $0."},
    {"id": "ai", "name": "AI Enhancement™", "ai_credits": "optional",
     "desc": "Marketplace-optimized variants grounded in the verified metadata. Optional, turn on/off per budget."},
    {"id": "founder", "name": "Founder Canonical™", "ai_credits": 0,
     "desc": "Founder writes/approves the definitive text; stored as canonical and reused everywhere. $0."},
]

# Channel = a storefront/output surface with its own conventions and length budget.
CHANNELS = {
    "back_cover":  {"label": "Back Cover (print)",           "words": (120, 170), "cta": False},
    "amazon":      {"label": "Amazon / KDP",                 "words": (150, 220), "cta": True},
    "etsy":        {"label": "Etsy",                          "words": (90, 150),  "cta": True},
    "tpt":         {"label": "Teachers Pay Teachers",         "words": (110, 180), "cta": True},
    "qru_online":  {"label": "QRU Online Store",              "words": (70, 130),  "cta": True},
    "short":       {"label": "Short summary",                 "words": (20, 45),   "cta": False},
    "generic":     {"label": "General description",           "words": (90, 150),  "cta": False},
}

# AI Enhancement™ marketing styles (optional).
AI_STYLES = ["amazon", "etsy", "tpt", "parent", "professional", "inspirational", "seo"]

_LITERARY_IMPRINT = "E.Q. Rothwell"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _wc(text):
    return len((text or "").split())


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if s.strip()]


def _clean(v):
    return re.sub(r"\s+", " ", str(v or "").strip())


def _kr_text(kr):
    """Extract verified value language from a Knowledge Record (any known field shape). No invention."""
    if not kr:
        return "", ""
    def pick(*keys):
        for k in keys:
            v = kr.get(k)
            if isinstance(v, str) and v.strip():
                return _clean(v)
            if isinstance(v, dict):
                for kk in ("summary", "statement", "text", "value", "content"):
                    if isinstance(v.get(kk), str) and v[kk].strip():
                        return _clean(v[kk])
        return ""
    why = pick("why_it_matters", "why_matters", "significance", "value", "so_what")
    what = pick("verified_truth", "core_knowledge", "synopsis", "summary", "abstract",
                "core_mental_model", "description")
    return what, why


async def gather_meta(engine, record_id):
    """Pull structured, governed enterprise metadata for a record from any engine. Returns a dict; the
    governed assembler uses only fields that are actually present (no invented facts)."""
    coll_map = {"book": "book_records", "publication": "products", "product": "products",
                "poster": "poster_assets", "recipe": "inherited_products", "media": "media_products",
                "kr": "knowledge_records", "bundle": "bundles"}
    coll = coll_map.get(engine, "products")
    d = await db[coll].find_one({"id": record_id}, {"_id": 0}) \
        or await db[coll].find_one({"book_code": record_id}, {"_id": 0}) \
        or await db[coll].find_one({"product_code": record_id}, {"_id": 0}) \
        or await db[coll].find_one({"kr_code": record_id}, {"_id": 0})
    if not d:
        return None
    # Knowledge Record synopsis (verified value language) — the source of truth for benefits.
    kr = None
    krid = d.get("knowledge_record_id") or d.get("kr_id") or (d.get("id") if engine == "kr" else None)
    if krid:
        for c in ("knowledge_records", "ukr_records"):
            kr = await db[c].find_one({"id": krid}, {"_id": 0}) or await db[c].find_one({"kr_code": krid}, {"_id": 0})
            if kr:
                break
    kr_what, kr_why = _kr_text(kr if engine != "kr" else d)
    content = (d.get("editorial_edition") or d.get("working_copy") or {}).get("content", "") or d.get("content", "")
    # Grounded body paragraphs (verified, Founder-authored) — substantive prose only, no headings/markdown.
    body_paras = []
    for p in re.split(r"\n+", content or ""):
        p = _clean(p)
        if len(p) >= 60 and not p.startswith(("#", "-", "*", "|", ">")) and "." in p:
            body_paras.append(p)
        if len(body_paras) >= 12:
            break
    ptype = d.get("product_type") or ("Book" if engine == "book" else d.get("family") or "Publication")
    imprint = d.get("imprint") or d.get("canonical_imprint") or "QRU Press™"
    return {
        "engine": engine, "id": d.get("id"),
        "title": _clean(d.get("published_title") or d.get("title")),
        "subtitle": _clean(d.get("subtitle")),
        "author": _clean(d.get("author") or d.get("byline")),
        "product_type": _clean(ptype),
        "genre": _clean(d.get("genre") or d.get("family")),
        "audience": _clean(d.get("audience")),
        "reading_level": _clean(d.get("reading_level")),
        "imprint": _clean(imprint),
        "learning_objectives": [x for x in (d.get("learning_objectives") or []) if isinstance(x, str)],
        "benefits": [x for x in (d.get("benefits") or []) if isinstance(x, str)],
        "skills": [x for x in (d.get("skills_gained") or d.get("skills") or []) if isinstance(x, str)],
        "keywords": [x for x in (d.get("keywords") or []) if isinstance(x, str)],
        "series": _clean(d.get("series")),
        "kr_what": kr_what, "kr_why": kr_why,
        "kr_code": (kr or {}).get("kr_code") or krid,
        "content_excerpt": " ".join((content or "").split()[:400]),
        "body_paragraphs": body_paras,
        "existing_description": _clean(d.get("description")),
        "descriptions": d.get("descriptions") or {},
    }


def _is_literary(meta):
    return (_LITERARY_IMPRINT.lower() in (meta.get("imprint", "").lower())) \
        or (meta.get("genre", "").lower() in ("literary fiction", "fiction", "literary"))


def _type_phrase(meta):
    pt = (meta.get("product_type") or "publication").lower()
    m = {"book": "book", "workbook": "hands-on workbook", "teacher guide": "teacher's guide",
         "course": "self-paced course", "audiobook": "audiobook", "video": "video lesson",
         "poster": "classroom poster", "quick card": "quick-reference card", "flash cards": "flash-card set",
         "presentation": "presentation deck", "bundle": "curated bundle"}
    return m.get(pt, pt)


def governed_description(meta, channel="generic"):
    """Mode 1 — Governed Manufacturing™ ($0). Assemble a channel-appropriate description from ONLY the
    verified metadata that exists. Returns text + word count + per-sentence source trace."""
    cfg = CHANNELS.get(channel, CHANNELS["generic"])
    lo, hi = cfg["words"]
    literary = _is_literary(meta)
    title = meta.get("title") or "This title"
    author = meta.get("author")
    blocks = []  # (sentence, source)

    def add(sentence, source):
        s = _clean(sentence)
        if s and not s.endswith((".", "!", "?", "”", '"')):
            s += "."
        if s:
            blocks.append((s, source))

    if literary:
        # Literary voice (E.Q. Rothwell™) — evocative, no invented plot facts.
        sub = meta.get("subtitle")
        if sub:
            add(f"{title} — {sub}", "title+subtitle")
        else:
            add(f"{title}", "title")
        if meta.get("kr_what"):
            first = _sentences(meta["kr_what"])[:2]
            for s in first:
                add(s, "knowledge_record.core")
        elif meta.get("content_excerpt"):
            add(_sentences(meta["content_excerpt"])[0] if _sentences(meta["content_excerpt"]) else title,
                "manuscript.opening")
        if meta.get("kr_why"):
            add(_sentences(meta["kr_why"])[0], "knowledge_record.why_it_matters")
        if author:
            add(f"A {meta.get('genre') or 'literary'} work by {author}", "author+genre")
        add(f"Published by {meta.get('imprint')}", "imprint")
    else:
        # Educational / product voice (QRU Press™) — benefit-led, grounded in verified knowledge.
        tp = _type_phrase(meta)
        aud = (meta.get("audience") or "").strip()
        generic_aud = aud.lower() in ("", "general", "general reader", "general learner",
                                      "general audience", "all", "everyone", "all levels")
        opener = f"{title} is a {tp}"
        if not generic_aud:
            opener += f" for {aud}"
        add(opener, "title+type+audience")
        if meta.get("subtitle"):
            add(meta["subtitle"], "subtitle")
        if meta.get("kr_what"):
            add(_sentences(meta["kr_what"])[0], "knowledge_record.core")
        if meta.get("kr_why"):
            add(_sentences(meta["kr_why"])[0], "knowledge_record.why_it_matters")
        objs = meta.get("learning_objectives") or meta.get("skills") or []
        if objs:
            top = ", ".join(x.strip().rstrip(".").lower() for x in objs[:3])
            add(f"You'll learn to {top}", "learning_objectives")
        bens = meta.get("benefits") or []
        if bens:
            add(bens[0], "benefits")
        if meta.get("reading_level"):
            add(f"Reading level: {meta['reading_level']}", "reading_level")

    # Fill toward the channel's lower word bound using ONLY grounded, verified manuscript/KR prose
    # (never invented). Educational voice only — literary blurbs stay intentionally evocative/short.
    if not literary and _wc(" ".join(s for s, _ in blocks)) < lo:
        used = {re.sub(r'[^a-z0-9]', '', s.lower())[:60] for s, _ in blocks}
        grounded_pool = []
        for para in (meta.get("body_paragraphs") or []):
            grounded_pool.extend(_sentences(para))
        for src_field in ("kr_what", "kr_why"):
            if meta.get(src_field):
                grounded_pool.extend(_sentences(meta[src_field]))
        for s in grounded_pool:
            if _wc(" ".join(x for x, _ in blocks)) >= lo:
                break
            key = re.sub(r'[^a-z0-9]', '', s.lower())[:60]
            if key in used or _wc(s) < 4:
                continue
            used.add(key)
            add(s, "manuscript.body")

    if not literary:
        add(f"From {meta.get('imprint')} — grounded in verified knowledge, reviewed and approved", "imprint")

    # Channel CTA (store channels only) — factual, no fake urgency.
    if cfg.get("cta"):
        cta = {"amazon": "Available now in paperback and eBook.",
               "etsy": "Instant digital download — yours to keep.",
               "tpt": "Ready to print and use in your classroom.",
               "qru_online": "Available now at QRU Online."}.get(channel, "")
        if cta:
            add(cta, "channel.cta")

    text = " ".join(s for s, _ in blocks)
    # Trim toward the channel's upper word bound at sentence boundaries (never mid-sentence).
    if _wc(text) > hi:
        kept, count = [], 0
        for s, src in blocks:
            if count + _wc(s) > hi and kept:
                break
            kept.append((s, src)); count += _wc(s)
        blocks = kept
        text = " ".join(s for s, _ in blocks)
    return {
        "channel": channel, "mode": "governed", "ai_used": False,
        "text": text, "word_count": _wc(text),
        "within_target": lo <= _wc(text) <= hi,
        "target_words": [lo, hi],
        "sources": [{"sentence": s, "source": src} for s, src in blocks],
        "traceable": True, "standard": STANDARD_ID,
        "generated_at": _now(),
    }


async def ai_enhanced(meta, channel="amazon", styles=None):
    """Mode 2 — AI Enhancement™ (OPTIONAL). Marketplace-optimized variants grounded in the verified
    metadata. Never invents facts beyond the supplied metadata."""
    import ai_service
    styles = [s for s in (styles or ["amazon", "professional", "inspirational"]) if s in AI_STYLES]
    cfg = CHANNELS.get(channel, CHANNELS["generic"])
    grounded = "\n".join(f"- {k}: {v}" for k, v in {
        "Title": meta.get("title"), "Subtitle": meta.get("subtitle"), "Author": meta.get("author"),
        "Type": meta.get("product_type"), "Audience": meta.get("audience"),
        "Verified knowledge": meta.get("kr_what"), "Why it matters": meta.get("kr_why"),
        "Benefits": "; ".join(meta.get("benefits") or []),
        "Learning objectives": "; ".join(meta.get("learning_objectives") or []),
        "Imprint": meta.get("imprint"),
    }.items() if v)
    sys_p = ("You are a QRU marketing copywriter. Using ONLY the verified metadata provided, write a "
             f"{cfg['label']} product description of {cfg['words'][0]}-{cfg['words'][1]} words for EACH "
             "requested style. Do NOT invent facts, quotes, reviews, or statistics beyond the metadata. "
             "Return STRICT JSON: {\"variants\":[{\"style\":\"..\",\"text\":\"..\"}]}. No markdown.")
    prompt = f"Requested styles: {', '.join(styles)}\n\nVerified metadata:\n{grounded}"
    variants = []
    try:
        raw = await ai_service.llm_generate(sys_p, prompt, f"desc-{meta.get('id')}")
        import json as _json
        s = raw[raw.find("{"): raw.rfind("}") + 1]
        variants = _json.loads(s).get("variants", [])
    except Exception as e:
        return {"error": f"AI Enhancement™ is unavailable right now ({str(e)[:80]}). "
                         "Governed Manufacturing™ ($0) always works as the default.", "mode": "ai"}
    out = [{"style": v.get("style", ""), "text": _clean(v.get("text", "")), "word_count": _wc(v.get("text", ""))}
           for v in variants if v.get("text")]
    return {"channel": channel, "mode": "ai", "ai_used": True, "variants": out,
            "grounded_in": "verified metadata only", "standard": STANDARD_ID, "generated_at": _now()}


async def save_description(engine, record_id, channel, text, *, mode, ai_used, canonical=False,
                           sources=None, actor="Founder"):
    """Persist a manufactured description on the record under `descriptions[channel]`. Founder Canonical™
    marks it canonical so it is reused wherever appropriate. Back-cover mirrors to `description` for the
    print cover wrap (STD-BLB-0001)."""
    coll_map = {"book": "book_records", "publication": "products", "product": "products",
                "poster": "poster_assets", "recipe": "inherited_products", "media": "media_products",
                "kr": "knowledge_records", "bundle": "bundles"}
    coll = coll_map.get(engine, "products")
    entry = {"text": _clean(text), "mode": mode, "ai_used": bool(ai_used), "canonical": bool(canonical),
             "sources": sources or [], "channel": channel, "by": actor, "updated_at": _now(),
             "standard": STANDARD_ID}
    upd = {f"descriptions.{channel}": entry, "updated_at": _now()}
    if channel == "back_cover" and engine == "book":
        upd["description"] = entry["text"]
        upd["include_blurb"] = True
        upd["blurb_status"] = "Founder canonical" if canonical else f"{mode} — Founder to approve"
    await db[coll].update_one({"id": record_id}, {"$set": upd})
    return entry


async def manufacture(engine, record_id, *, mode="governed", channel="generic", text=None,
                      styles=None, save=True, actor="Founder"):
    """Orchestrate a description manufacture. Governed & Founder modes are $0; AI is optional."""
    meta = await gather_meta(engine, record_id)
    if not meta:
        return {"error": "Record not found."}
    if mode == "founder":
        if not (text or "").strip():
            return {"error": "Founder Canonical™ requires the Founder's text."}
        entry = None
        if save:
            entry = await save_description(engine, record_id, channel, text, mode="founder",
                                           ai_used=False, canonical=True, actor=actor)
        return {"mode": "founder", "channel": channel, "ai_used": False, "canonical": True,
                "text": _clean(text), "word_count": _wc(text), "standard": STANDARD_ID, "saved": bool(save)}
    if mode == "ai":
        res = await ai_enhanced(meta, channel, styles)
        return res  # not auto-saved; Founder selects a variant then saves via founder/governed save
    # Default: Governed Manufacturing™ ($0)
    res = governed_description(meta, channel)
    if save:
        await save_description(engine, record_id, channel, res["text"], mode="governed",
                               ai_used=False, canonical=False, sources=res["sources"], actor=actor)
        res["saved"] = True
    return res
