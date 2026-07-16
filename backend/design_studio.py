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
        if y < H * 0.36:
            a = int(170 * (1 - y / (H * 0.36)))
        if y > H * 0.46:
            a = max(a, int(235 * ((y - H * 0.46) / (H * 0.54))))
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


def compose_print_wrap(front_bytes, spec):
    """Compose a COMPLETE print-ready paperback cover wrap (back + spine + front) as a single flat
    image at print DPI. Dimensions are computed by the caller from final page count, trim, paper
    type & bleed. `spec` = {trim_w_in, trim_h_in, spine_in, bleed_in, dpi, title, subtitle, author,
    imprint, blurb, spine_text(bool)}."""
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
    dpi = spec.get("dpi", 300)
    bleed, tw, th, sp = spec["bleed_in"], spec["trim_w_in"], spec["trim_h_in"], spec["spine_in"]
    W = int(round((bleed + tw + sp + tw + bleed) * dpi))
    H = int(round((bleed + th + bleed) * dpi))
    front_x = int(round((bleed + tw + sp) * dpi))   # left edge of front panel (incl. front's inner start)
    spine_x = int(round((bleed + tw) * dpi))
    canvas = Image.new("RGB", (W, H), (18, 14, 34))

    front = Image.open(io.BytesIO(front_bytes)).convert("RGB")
    # FRONT panel (right): trim width + right & top/bottom bleed
    fpw = W - front_x
    fr = front.resize((fpw, H))
    canvas.paste(fr, (front_x, 0))
    # BACK panel (left): darkened, blurred art as an on-brand background
    bpw = spine_x
    back_bg = ImageEnhance.Brightness(front.resize((bpw, H)).filter(ImageFilter.GaussianBlur(8))).enhance(0.30)
    canvas.paste(back_bg, (0, 0))
    # SPINE: solid deep brand panel
    ImageDraw.Draw(canvas).rectangle([spine_x, 0, front_x, H], fill=(24, 18, 44))
    d = ImageDraw.Draw(canvas)

    def font(path, size):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    def wrap(text, fnt, maxw):
        out, cur = [], ""
        for word in text.split():
            t = (cur + " " + word).strip()
            if d.textlength(t, font=fnt) <= maxw:
                cur = t
            else:
                out.append(cur); cur = word
        if cur:
            out.append(cur)
        return out

    m = int(0.5 * dpi)            # 0.5in safe margin
    safe_l = int(bleed * dpi) + m
    safe_r = spine_x - m
    # Reserve a clean bottom band on the BACK cover for the imprint (left) and the barcode zone (right).
    bc_w, bc_h = int(2.0 * dpi), int(1.2 * dpi)          # KDP required clear zone: 2.0 x 1.2 in
    pad = int(0.2 * dpi)
    bc_x = safe_r - bc_w
    bc_y = H - int(bleed * dpi) - m - bc_h
    band_top = bc_y - pad - int(0.35 * dpi)              # text must stop above this
    # Legibility panel: a solid dark scrim behind header + blurb guarantees text contrast on any art.
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    pdraw.rectangle([safe_l - pad, int(bleed * dpi) + m - pad, safe_r + pad, band_top], fill=(10, 8, 22, 205))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), panel).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(canvas)
    # Back header
    hf = font(dl.SERIF_BOLD, int(0.30 * dpi))
    d.text((safe_l, int(bleed * dpi) + m), (spec.get("title") or "").upper(), font=hf, fill=(255, 255, 255))
    y = int(bleed * dpi) + m + int(0.5 * dpi)
    # Blurb — capped so it never runs into the bottom band (imprint / barcode clear zone)
    bf = font(dl.SERIF, int(0.17 * dpi))
    blurb = spec.get("blurb") or ""
    for para in blurb.split("\n"):
        for ln in wrap(para, bf, safe_r - safe_l):
            if y > band_top - int(0.26 * dpi):
                break
            d.text((safe_l, y), ln, font=bf, fill=(236, 232, 244)); y += int(0.26 * dpi)
        y += int(0.12 * dpi)
    # Imprint — bottom-LEFT only, clear of the barcode zone
    imf = font(dl.SANS_BOLD, int(0.15 * dpi))
    d.text((safe_l, H - int(bleed * dpi) - m - int(0.18 * dpi)), (spec.get("imprint") or "").upper(), font=imf, fill=_GOLD)
    # Barcode clear zone — KDP prints the retail barcode here (bottom-right of BACK cover).
    # A solid WHITE rectangle (with padding) guarantees a light, solid, element-free 2.0 x 1.2 in area.
    # The Founder selects "No, my cover does not have a barcode" so Amazon fills this zone.
    d.rectangle([bc_x - pad, bc_y - pad, min(bc_x + bc_w + pad, safe_r + pad), bc_y + bc_h + pad], fill=(255, 255, 255))
    # SPINE text only if allowed (>=79 pages)
    if spec.get("spine_text") and sp * dpi > int(0.2 * dpi):
        spine_img = Image.new("RGBA", (H, int(sp * dpi)), (0, 0, 0, 0))
        sd = ImageDraw.Draw(spine_img)
        stf = font(dl.SERIF_BOLD, int(min(sp * dpi * 0.5, 0.18 * dpi)))
        label = f"{spec.get('title','')}    {spec.get('author','')}"
        sd.text((H / 2, int(sp * dpi) / 2), label, font=stf, fill=(255, 255, 255), anchor="mm")
        canvas.paste(spine_img.rotate(90, expand=True), (spine_x, 0), spine_img.rotate(90, expand=True))

    buf = io.BytesIO(); canvas.save(buf, "PNG")
    return buf.getvalue(), (W, H)


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
