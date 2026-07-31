"""QRU Governed Render/Export Engine™ (STD-UCAMS-0001) — the technically-compliant final-file maker.

CRITICAL DISTINCTION (Treasure Standard™):
  • Image generation (OpenAI/Gemini/designer) creates the ARTWORK — it is only *source material*.
  • THIS engine renders/exports the governed FINAL file at the EXACT destination profile: exact pixel
    dimensions, format, color mode, DPI metadata, transparency rule, and max file size.

Rules honored:
  • Auto-normalize only SAFE technical differences (RGB conversion, DPI metadata, PNG/JPEG conversion,
    downscaling from a larger source, JPEG quality-reduction to meet max size).
  • NEVER distort, stretch, or crop. Aspect mismatch is corrected by brand-safe PADDING (letterbox),
    never by cropping the artwork.
  • When a change could affect DESIGN QUALITY (upscaling a too-small source, or padding to fix aspect),
    produce the compliant candidate BUT set quality_review_required=True so a human must approve it.
  • Never silently degrade — every action is recorded and returned.
"""
import io

# Tolerance for treating an aspect ratio as "already correct" (no padding needed).
_AR_TOL = 0.01
# Brand-safe letterbox background (QRU-neutral white). Padding is always flagged for human review.
_PAD_BG_RGB = (255, 255, 255)


def _target_px(spec):
    """Governed EXACT export size (width, height) for this destination, if the family has one."""
    return spec.get("target_px") or spec.get("requirements", {}).get("ideal_px")


def _fmt(req):
    return (req.get("format") or "png").lower().replace("jpg", "jpeg")


def governed_export(spec, data, *, mime=""):
    """Render the final governed asset from source artwork.

    Returns: {
      normalized: bool, data: bytes|None, ext: str, mime: str,
      actions: [str], quality_review_required: bool, notes: str, error: str|None
    }
    PDFs are NOT reflowed here (print geometry must be authored exactly) — returned untouched with a note.
    """
    req = spec.get("requirements", {})
    fmt = _fmt(req)
    head = data[:5].lstrip()
    is_pdf = head[:4] == b"%PDF" or "pdf" in (mime or "") or fmt == "pdf"
    if is_pdf:
        return {"normalized": False, "data": data, "ext": "pdf", "mime": "application/pdf",
                "actions": [], "quality_review_required": False,
                "notes": "Print PDFs are authored at exact wrap geometry; the render engine does not "
                         "reflow them. Regenerate at the required geometry if it fails validation.",
                "error": None}

    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception as e:
        return {"normalized": False, "data": None, "ext": None, "mime": None, "actions": [],
                "quality_review_required": False, "notes": "", "error": f"Not a decodable image: {str(e)[:80]}"}

    actions, quality_review = [], False
    want_fmt = fmt if fmt in ("jpeg", "png", "webp") else "png"
    want_cs = (req.get("color_space") or "RGB").upper()
    transparency_allowed = bool(req.get("transparency_allowed", want_fmt == "png"))
    dpi = int(req.get("dpi") or 72)
    max_mb = req.get("max_mb")
    target = _target_px(spec)

    src_w, src_h = im.width, im.height

    # 1) Color mode — safe technical normalization.
    if want_cs == "RGB":
        if im.mode == "P":
            im = im.convert("RGBA"); actions.append("Converted palette (P) → RGBA")
        if not transparency_allowed and im.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", im.size, _PAD_BG_RGB)
            bg.paste(im, mask=im.split()[-1]); im = bg
            actions.append("Flattened transparency onto brand-safe background (destination is opaque)")
        elif im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB"); actions.append(f"Converted color mode → RGB")
    elif want_cs == "CMYK" and im.mode != "CMYK":
        im = im.convert("CMYK")
        actions.append("Converted RGB → CMYK for print (color values shift — verify proof)")
        quality_review = True

    # 2) Aspect + exact-size render (never distort, never crop).
    if target:
        tw, th = int(target[0]), int(target[1])
        # Correct aspect by PADDING (letterbox), never cropping.
        src_ar = im.width / im.height
        tgt_ar = tw / th
        if abs(src_ar - tgt_ar) > _AR_TOL:
            # Fit the whole artwork inside the target aspect, then pad the remainder.
            if src_ar > tgt_ar:
                new_w = im.width; new_h = int(round(im.width / tgt_ar))
            else:
                new_h = im.height; new_w = int(round(im.height * tgt_ar))
            pad_mode = "RGBA" if (im.mode == "RGBA" and transparency_allowed) else "RGB"
            pad_bg = (0, 0, 0, 0) if pad_mode == "RGBA" else _PAD_BG_RGB
            canvas = Image.new(pad_mode, (new_w, new_h), pad_bg)
            if im.mode == "RGBA" and pad_mode == "RGB":
                base = Image.new("RGB", im.size, _PAD_BG_RGB); base.paste(im, mask=im.split()[-1]); im = base
            canvas.paste(im, ((new_w - im.width) // 2, (new_h - im.height) // 2))
            im = canvas
            actions.append(f"Aspect {round(src_ar,3)} ≠ target {round(tgt_ar,3)}: padded (letterbox) to correct "
                           f"aspect without cropping artwork")
            quality_review = True

        # Resize to the EXACT governed dimensions (aspect now matches → no distortion).
        if (im.width, im.height) != (tw, th):
            upscaling = im.width < tw or im.height < th
            im = im.resize((tw, th), Image.LANCZOS)
            if upscaling:
                actions.append(f"Upscaled source {src_w}×{src_h} → exact {tw}×{th} (Lanczos) — verify sharpness")
                quality_review = True
            else:
                actions.append(f"Downscaled source {src_w}×{src_h} → exact {tw}×{th} (Lanczos)")

    # 3) Transparency rule for the final format.
    if want_fmt == "jpeg" and im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, _PAD_BG_RGB)
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1]); im = bg
        actions.append("Flattened to RGB for JPEG (JPEG has no transparency)")

    # 4) Encode to the required format + DPI metadata; JPEG size-fit if a max is set.
    out = io.BytesIO()
    save_kwargs = {"dpi": (dpi, dpi)}
    if want_fmt == "jpeg":
        q = 92
        if im.mode not in ("RGB", "CMYK"):
            im = im.convert("RGB")
        im.save(out, format="JPEG", quality=q, **save_kwargs)
        if max_mb:
            limit = max_mb * 1024 * 1024
            while out.tell() > limit and q > 55:
                q -= 8; out = io.BytesIO(); im.save(out, format="JPEG", quality=q, **save_kwargs)
            if out.tell() <= limit and q < 92:
                actions.append(f"Reduced JPEG quality to {q} to meet the {max_mb}MB limit")
        ext, out_mime = "jpg", "image/jpeg"
    elif want_fmt == "webp":
        im.save(out, format="WEBP", quality=95, **save_kwargs); ext, out_mime = "webp", "image/webp"
    else:
        im.save(out, format="PNG", **save_kwargs); ext, out_mime = "png", "image/png"

    final = out.getvalue()
    wrote_format = want_fmt != (Image.open(io.BytesIO(data)).format or "").lower().replace("jpg", "jpeg")
    if wrote_format:
        actions.append(f"Exported as required format: {want_fmt.upper()}")
    actions.append(f"Embedded {dpi} DPI resolution metadata")

    return {
        "normalized": True, "data": final, "ext": ext, "mime": out_mime,
        "actions": actions, "quality_review_required": quality_review,
        "notes": "Governed final file rendered from source artwork at the exact destination profile.",
        "error": None,
        "final_dimensions": [im.width, im.height], "final_bytes": len(final), "final_format": want_fmt,
    }
