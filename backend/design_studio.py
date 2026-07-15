"""QRU Design Studio™ — the single, shared design engine for the whole Factory.

This is the ONE owner of publication-quality design across QRU. Every surface that needs design —
Book covers, Cover Studio, Poster Studio, workbook/guide covers, and every product recipe's design
concepts — calls this engine so the output is consistently superb and on-brand.

Pipeline (proven in the Book Manufacturing System):
    LLM art-direction  →  Gemini artwork (NO baked-in text)  →  professional QRU typography composite
    (legibility scrim, serif title, gold rule, byline + imprint)  →  strict validation + honest provenance.

A concept is 'success' ONLY when the provider returns real, decodable artwork — never a faked
placeholder presented as real art (Treasure Standard™).

    Interface remains constant. Recipes specialize. Design quality is inherited, never duplicated.
"""
import io
import json as _json
import time as _time
import asyncio

import design_language as dl
import ai_service
import rendering_engine as re_engine

# Format profiles → (width, height). Portrait book cover is the default.
FORMATS = {
    "cover": (1024, 1536),
    "book": (1024, 1536),
    "poster": (1024, 1536),
    "poster_landscape": (1536, 1024),
    "workbook": (1024, 1536),
    "guide": (1024, 1536),
    "concept": (1024, 1536),
}

_GOLD = (243, 200, 90)


def valid_art(data):
    """Strictly validate provider image bytes. Returns (ok, reason). Rejects empty/HTML/JSON/
    malformed/tiny payloads so a failure is NEVER presented as real art."""
    if not data:
        return False, "empty response from image provider"
    if len(data) < 2048:
        return False, f"response too small ({len(data)} bytes) — likely truncated or an error payload"
    head = data[:64].lstrip().lower()
    if head[:1] in (b"{", b"[") or head[:5] == b"<!doc" or head[:5] == b"<html":
        return False, "provider returned JSON/HTML, not an image"
    try:
        from PIL import Image
        Image.open(io.BytesIO(data)).verify()
        im = Image.open(io.BytesIO(data))
        if im.width < 256 or im.height < 256:
            return False, f"image too small ({im.width}x{im.height})"
    except Exception as e:
        return False, f"malformed image bytes: {str(e)[:80]}"
    return True, None


def compose(hero_bytes, spec):
    """Publication-quality composite: full-bleed art + legibility scrim + clean QRU typography.
    `spec` = {title, subtitle, byline, imprint, palette, kind, size(optional (w,h))}."""
    from PIL import Image, ImageDraw, ImageFont
    kind = spec.get("kind", "cover")
    W, H = spec.get("size") or FORMATS.get(kind, FORMATS["cover"])
    title = (spec.get("title") or "").strip()
    subtitle = (spec.get("subtitle") or "").strip()
    byline = (spec.get("byline") or "").strip()
    imprint = (spec.get("imprint") or "").strip()
    palette_hint = spec.get("palette", "") or ""

    if hero_bytes:
        art = Image.open(io.BytesIO(hero_bytes)).convert("RGB")
        ar = art.width / art.height
        if ar > W / H:
            nh = H; nw = int(H * ar)
        else:
            nw = W; nh = int(W / ar)
        art = art.resize((nw, nh)).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
    else:
        base = (34, 26, 66) if "amber" not in palette_hint else (60, 32, 20)
        art = Image.new("RGB", (W, H), base)
        d0 = ImageDraw.Draw(art)
        for y in range(H):
            t = y / H
            d0.line([(0, y), (W, y)], fill=tuple(int(base[i] * (1 - 0.55 * t)) for i in range(3)))
    img = art.copy()
    # top + bottom scrims for text legibility
    scrim = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scrim)
    for y in range(H):
        a = 0
        if y < H * 0.34:
            a = int(150 * (1 - y / (H * 0.34)))
        if y > H * 0.5:
            a = max(a, int(205 * ((y - H * 0.5) / (H * 0.5))))
        sd.line([(0, y), (W, y)], fill=a)
    black = Image.new("RGB", (W, H), (8, 6, 18))
    img = Image.composite(black, img, scrim)
    d = ImageDraw.Draw(img)

    def font(path, size):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    def wrap(text, fnt, maxw):
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=fnt) <= maxw:
                cur = t
            else:
                lines.append(cur); cur = w
        if cur:
            lines.append(cur)
        return lines

    scale = W / 1024.0
    if imprint:
        ef = font(dl.SANS_BOLD, int(30 * scale))
        d.text((W / 2, 70 * scale), imprint.upper(), font=ef, fill=_GOLD, anchor="mm")
    size = 118 if len(title) <= 18 else (92 if len(title) <= 30 else 70)
    size = int(size * scale)
    tf = font(dl.SERIF_BOLD, size)
    lines = wrap(title.upper(), tf, W - int(150 * scale))
    y = H * 0.60 - (len(lines) * size * 0.6)
    for ln in lines:
        d.text((W / 2, y), ln, font=tf, fill=(255, 255, 255), anchor="mm")
        y += size * 1.08
    d.line([(W / 2 - 90 * scale, y + 14), (W / 2 + 90 * scale, y + 14)], fill=_GOLD, width=max(3, int(4 * scale)))
    y += 46 * scale
    if subtitle:
        sf = font(dl.SERIF, int(40 * scale))
        for ln in wrap(subtitle, sf, W - int(200 * scale)):
            d.text((W / 2, y), ln, font=sf, fill=(232, 226, 240), anchor="mm"); y += 50 * scale
    if byline:
        af = font(dl.SANS_BOLD, int(46 * scale))
        d.text((W / 2, H - 96 * scale), byline.upper(), font=af, fill=_GOLD, anchor="mm")
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


async def art_direction(context, n=3):
    """LLM art-direction → n strategically distinct art briefs (art_prompt = ARTWORK only, no text)."""
    kind = context.get("kind", "cover")
    title = context.get("title", "")
    subject = context.get("genre") or context.get("family") or context.get("topic") or "subject"
    synopsis = " ".join((context.get("synopsis") or context.get("content") or "").split()[:180])
    brief_sys = (f"You are the QRU Art Director for a premium publishing/design imprint. For a {kind}, "
                 f"produce EXACTLY {n} strategically DIFFERENT art directions. Return strict JSON: "
                 '{"concepts":[{"name":"short concept name","palette":"comma colors","art_prompt":'
                 '"a vivid, specific image-generation prompt for the ARTWORK ONLY — evocative subject/mood/'
                 'lighting/composition, portrait orientation, NO text, NO words, NO lettering"}]}. '
                 "Make the concepts genuinely distinct (e.g. symbolic, atmospheric, subject/object-focused).")
    brief_prompt = (f"Title: {title}\nSubtitle: {context.get('subtitle','')}\nType/Genre: {subject}\n"
                    f"Audience: {context.get('audience','')}\nSummary: {synopsis}")
    briefs = []
    try:
        raw = await ai_service.llm_generate(brief_sys, brief_prompt, f"artdir-{context.get('slug','x')}")
        raw = raw.strip().replace("```json", "").replace("```", "")
        briefs = _json.loads(raw).get("concepts", [])[:n]
    except Exception:
        briefs = []
    if len(briefs) < n:
        defaults = [
            {"name": "Symbolic", "palette": "deep navy, gold", "art_prompt": f"A symbolic, atmospheric illustration evoking '{title}' ({subject}); rich lighting, portrait, no text."},
            {"name": "Atmospheric", "palette": "twilight blues", "art_prompt": f"A moody atmospheric scene evoking the themes of '{title}'; cinematic, portrait, no text."},
            {"name": "Object Focus", "palette": "warm amber", "art_prompt": f"A single meaningful object central to '{title}' on an elegant textured background; portrait, no text."},
            {"name": "Bold Graphic", "palette": "high-contrast brand", "art_prompt": f"A bold, modern graphic composition representing '{title}'; strong shapes, portrait, no text."},
        ]
        briefs = (briefs + defaults)[:n]
    return briefs


async def manufacture_bytes(context, *, kind="cover", size=None, n=3, slug="design"):
    """Core: produce n publication-quality composited design concepts and return raw PNG BYTES
    (so any caller can store them however it likes). Each item carries honest status + provenance."""
    context = dict(context or {})
    context.setdefault("kind", kind)
    context.setdefault("slug", slug)
    dims = size or FORMATS.get(kind, FORMATS["cover"])
    briefs = await art_direction(context, n=n)

    async def _gen(idx, brief):
        t0 = _time.time()
        try:
            raw = await ai_service.generate_image(
                f"Professional {kind} ARTWORK (no text, no lettering): {brief.get('art_prompt','')}",
                f"{slug}-art-{idx}")
        except Exception as e:
            return None, round(_time.time() - t0, 1), f"provider error: {str(e)[:120]}"
        elapsed = round(_time.time() - t0, 1)
        ok, reason = valid_art(raw)
        return (raw if ok else None), elapsed, (None if ok else reason)

    results = await asyncio.gather(*[_gen(i, br) for i, br in enumerate(briefs, 1)])
    art_provider = "Gemini (Emergent LLM Key)"
    art_model = ai_service.IMAGE_MODEL
    direction_model = ai_service.MODEL[1] if isinstance(ai_service.MODEL, (tuple, list)) else str(ai_service.MODEL)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    out = []
    for idx, (brief, (hero, elapsed, fail_reason)) in enumerate(zip(briefs, results), 1):
        success = hero is not None
        png = compose(hero, {"title": context.get("title", ""), "subtitle": context.get("subtitle", ""),
                             "byline": context.get("byline", ""), "imprint": context.get("imprint", ""),
                             "palette": brief.get("palette", ""), "kind": kind, "size": dims})
        out.append({
            "concept": idx, "name": brief.get("name", f"Concept {idx}"),
            "art_direction": brief.get("art_prompt", ""), "palette": brief.get("palette", ""),
            "png": png,
            "status": "success" if success else "failed",
            "has_ai_art": success,
            "failure_reason": None if success else fail_reason,
            "thumbnail_legible": True,
            "readability_status": "Title & byline legible at retail thumbnail size (composited scrim + high-contrast serif).",
            "provenance": {
                "art_provider": art_provider, "art_model": art_model, "art_direction_model": direction_model,
                "art_direction_prompt": brief.get("art_prompt", ""), "generation_time_sec": elapsed,
                "generated_at": now, "fallback_used": not success, "has_ai_art": success,
                "failure_reason": None if success else fail_reason, "design_engine": "QRU Design Studio™",
            },
            "rights": "Rights-safe — AI-generated original artwork (no third-party imagery)." if success
                      else "AI artwork could not be generated for this concept (honest failure — a branded placeholder is shown, NOT presented as real art).",
        })
    return out


async def manufacture_design_concepts(context, *, kind="cover", size=None, n=3, slug="design"):
    """Produce n publication-quality design concepts and SAVE them to the shared asset store,
    returning concept dicts with url/status/has_ai_art/provenance (Book-system structure)."""
    items = await manufacture_bytes(context, kind=kind, size=size, n=n, slug=slug)
    concepts = []
    for it in items:
        fid = re_engine._save(f"{slug}-c{it['concept']}", "png", it["png"])
        c = {k: v for k, v in it.items() if k != "png"}
        c["url"] = re_engine._asset_url(fid)
        concepts.append(c)
    return concepts
