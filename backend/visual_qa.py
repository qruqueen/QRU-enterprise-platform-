"""QRU Visual QA Hard Gate™ — render every page to an image and detect defects that must NEVER ship.

Part of the Treasure Standard™ Final Inspection™. A product cannot reach VISUAL_QA_PASSED (and therefore
cannot satisfy the STD-PUB-0001 'Visual QA Passed' publication requirement) unless every page passes.
Detects: blank pages, sparse pages, text clipped outside the page/margins, split headings (a heading
stranded at the very bottom of a page), duplicate pages, and Unicode replacement characters (�).
Deterministic — no AI, no external services.
"""
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def inspect_pdf(data, *, margin_pt=36):
    """Rasterize + analyze every page. Returns {result, pages, findings, summary}. result ∈ PASS/FAIL."""
    import fitz
    import numpy as np
    findings = []
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        return {"result": "FAIL", "pages": 0, "findings": [{"page": 0, "type": "unreadable_pdf",
                "severity": "FAIL", "detail": f"PDF could not be opened: {str(e)[:80]}"}], "summary": {}}

    hashes = []
    n = doc.page_count
    for i, page in enumerate(doc):
        pno = i + 1
        rect = page.rect
        # Rasterize to grayscale for ink-coverage / blank detection.
        pix = page.get_pixmap(dpi=120, colorspace=fitz.csGRAY)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
        ink = float(np.mean(arr < 200))  # fraction of non-white pixels
        # perceptual hash (16x16 threshold on the mean) — only for content-rich pages (blank/sparse
        # pages naturally look alike and are already reported; excluding them avoids false duplicates).
        small = arr[:: max(1, pix.height // 16), :: max(1, pix.width // 16)][:16, :16]
        bits = (small < small.mean()) if small.size else np.zeros((1,))
        if ink >= 0.02:
            hashes.append((pno, bits.flatten()))

        if ink < 0.0015:
            findings.append({"page": pno, "type": "blank_page", "severity": "FAIL",
                             "detail": f"Page {pno} appears blank (ink coverage {ink:.4f})."})
        elif ink < 0.012 and pno not in (1, n):
            findings.append({"page": pno, "type": "sparse_page", "severity": "WARN",
                             "detail": f"Page {pno} is very sparse (ink coverage {ink:.3f})."})

        # Text analysis via structured dict.
        try:
            d = page.get_text("dict")
        except Exception:
            d = {"blocks": []}
        page_bottom = rect.height
        spans = []
        for b in d.get("blocks", []):
            for line in b.get("lines", []):
                for sp in line.get("spans", []):
                    spans.append(sp)
                    x0, y0, x1, y1 = sp.get("bbox", (0, 0, 0, 0))
                    # Clipping: any glyph outside the physical page (small tolerance).
                    if x0 < -1 or y0 < -1 or x1 > rect.width + 1 or y1 > rect.height + 1:
                        findings.append({"page": pno, "type": "text_clipping", "severity": "FAIL",
                                         "detail": f"Text extends outside the page on page {pno} (bbox {round(x0)},{round(y0)},{round(x1)},{round(y1)} vs page {round(rect.width)}x{round(rect.height)})."})
                    if "\ufffd" in sp.get("text", ""):
                        findings.append({"page": pno, "type": "replacement_char", "severity": "FAIL",
                                         "detail": f"Unicode replacement character (\u25a1/\ufffd) found on page {pno}."})
        # Split heading: a large-font span stranded in the bottom ~12% of the page with (almost) nothing after it.
        big = [sp for sp in spans if sp.get("size", 0) >= 15]
        for sp in big:
            y0 = sp.get("bbox", (0, 0, 0, 0))[1]
            if y0 > page_bottom * 0.88:
                after_ink = float(np.mean(arr[int((y0 / page_bottom) * pix.height):, :] < 200))
                if after_ink < 0.02:
                    findings.append({"page": pno, "type": "split_heading", "severity": "FAIL",
                                     "detail": f"Heading '{sp.get('text','')[:40]}' is stranded at the bottom of page {pno} (should start the next page)."})
                    break

    # Duplicate page detection (near-identical rasters).
    for a in range(len(hashes)):
        for b in range(a + 1, len(hashes)):
            pa, ha = hashes[a]
            pb, hb = hashes[b]
            if len(ha) == len(hb) and len(ha) > 4:
                ham = int((ha != hb).sum())
                if ham <= 2:
                    findings.append({"page": pb, "type": "duplicate_page", "severity": "FAIL",
                                     "detail": f"Page {pb} is a near-duplicate of page {pa}."})

    fails = [f for f in findings if f["severity"] == "FAIL"]
    result = "FAIL" if fails else "PASS"
    summary = {}
    for f in findings:
        summary[f["type"]] = summary.get(f["type"], 0) + 1
    return {"result": result, "pages": n, "findings": findings, "summary": summary,
            "fail_count": len(fails), "inspected_at": _now(),
            "standard": "Visual QA Hard Gate™ / Treasure Standard™ Final Inspection™"}


async def run_visual_qa(product, engine="book"):
    """Render the product's interior PDF and run the hard-gate inspection. Persists the result and the
    VISUAL_QA_PASSED / VISUAL_QA_FAILED status that STD-PUB-0001 reads as a publication requirement."""
    import io
    import qrcode
    import rendering_engine as reng
    from database import db
    # Build a QR for the render (learning products embed one) — $0, deterministic.
    qb = io.BytesIO(); qrcode.make("https://qru-online.com").save(qb, "PNG")
    try:
        pdf_bytes = reng._make_pdf(product, None, None, qb.getvalue())
    except Exception as e:
        report = {"result": "FAIL", "pages": 0, "findings": [{"page": 0, "type": "render_error",
                  "severity": "FAIL", "detail": f"Render failed: {str(e)[:120]}"}], "summary": {}, "fail_count": 1}
        pdf_bytes = None
    else:
        report = inspect_pdf(pdf_bytes)
    status = "VISUAL_QA_PASSED" if report["result"] == "PASS" else "VISUAL_QA_FAILED"
    coll = {"book": "book_records", "publication": "products", "product": "products"}.get(engine, "products")
    await db[coll].update_one({"id": product.get("id")}, {"$set": {
        "visual_qa_status": status, "visual_qa_report": report, "visual_qa_at": _now()}})
    return {"status": status, "report": report}
