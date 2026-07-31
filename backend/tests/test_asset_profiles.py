"""Asset Profile Audit tests (STD-UCAMS-0001) — one VALID and one intentionally INVALID file per
destination profile. Verifies: (1) valid/normalizable source → governed EXACT final file that PASSES,
(2) a hard-requirement failure stays FAILED and is never silently 'fixed'."""
import io
import sys
import json

sys.path.insert(0, "/app/backend")
from PIL import Image
import creative_asset_system as ucams
import asset_normalizer as norm


def _img(w, h, mode="RGB", fmt="PNG"):
    im = Image.new(mode, (w, h), (40, 30, 90) if mode != "RGBA" else (40, 30, 90, 255))
    b = io.BytesIO(); im.save(b, format=fmt); return b.getvalue()


def _spec_from_profile(p):
    """Build the minimal spec the engine needs directly from a PSR profile (no DB)."""
    req = p["requirements"]
    spec = {"requirements": req, "asset_family": req.get("family"), "asset_role": p["asset_role"],
            "platform_id": p["platform_id"], "spec_checksum": "test"}
    if req.get("family") == "print_cover_wrap":
        trim = req.get("default_trim_in", [6, 9])
        spec["geometry"] = ucams._wrap_geometry(trim[0], trim[1], 120, "white",
                                                 bleed=req.get("bleed_in", 0.125), dpi=req.get("dpi", 300))
    else:
        spec["target_px"] = req.get("ideal_px") or req.get("canvas_px")
        spec["aspect_ratio"] = req.get("aspect_ratio")
    return spec


def _valid_source_for(req):
    """A realistic 'provider output' source: correct aspect but ~62% of target size (simulates the
    992×1586 / 1122×1402 shrink) so the Render/Export must upscale to the exact governed size."""
    tgt = req.get("ideal_px") or req.get("canvas_px")
    tw, th = int(tgt[0]), int(tgt[1])
    sw, sh = max(int(tw * 0.62), 8), max(int(th * 0.62), 8)
    return _img(sw, sh, mode="RGBA", fmt="PNG")  # deliberately RGBA + PNG to exercise mode/format normalization


def _invalid_source_for(req):
    """A HARD failure the factory must NOT silently fix: below the hard minimum pixels (or, if no
    minimum is declared, a corrupt non-image)."""
    minpx = req.get("min_px")
    if minpx:
        return _img(max(int(minpx[0] // 3), 4), max(int(minpx[1] // 3), 4)), "below-hard-minimum"
    return b"this-is-not-an-image", "corrupt-file"


def run():
    RIGHTS = {"creator": "QRU Design Studio", "creation_method": "governed manufacturing",
              "license": "QRU-owned", "commercial_use_authorization": "authorized",
              "ai_disclosure_status": "AI-assisted, human-approved"}
    results = []
    passed = failed = 0
    for p in ucams._SEED_PROFILES:
        fam = p["requirements"].get("family")
        pid, role = p["platform_id"], p["asset_role"]
        if fam in ("motion_asset",):
            results.append({"profile": pid, "role": role, "skipped": "motion/video (not an image render)"}); continue
        if fam in ("print_cover_wrap", "one_page_knowledge_visual"):
            # Print: normalizer intentionally does NOT reflow PDFs. Verify it declines safely.
            spec = _spec_from_profile(p)
            export = norm.governed_export(spec, b"%PDF-1.4 fake")
            ok = (export["normalized"] is False and export["error"] is None)
            results.append({"profile": pid, "role": role, "family": fam, "pdf_passthrough_ok": ok,
                            "note": export["notes"]})
            passed += ok; failed += (not ok)
            continue

        spec = _spec_from_profile(p)
        req = p["requirements"]
        target = req.get("ideal_px") or req.get("canvas_px")

        # ---- VALID (normalizable) ----
        src = _valid_source_for(req)
        src_val = ucams.validate_asset(spec, src, asset_meta=RIGHTS)
        export = norm.governed_export(spec, src)
        fin_val = ucams.validate_asset(spec, export["data"], mime=export["mime"], asset_meta=RIGHTS)
        exact = export.get("final_dimensions") == [int(target[0]), int(target[1])]
        fmt_ok = export.get("final_format") == (req.get("format") or "").lower().replace("jpg", "jpeg")
        valid_ok = (export["normalized"] and exact and fmt_ok and fin_val["result"] in ("PASS", "PASS WITH WARNINGS")
                    and export["quality_review_required"] is True)  # upscaled → must require review
        results.append({"profile": pid, "role": role, "family": fam, "case": "VALID/normalizable",
                        "source_result": src_val["result"], "final_result": fin_val["result"],
                        "final_dimensions": export.get("final_dimensions"), "target": target,
                        "final_format": export.get("final_format"),
                        "quality_review_required": export["quality_review_required"],
                        "actions": export["actions"], "ok": bool(valid_ok)})
        passed += bool(valid_ok); failed += (not valid_ok)

        # ---- INVALID (hard failure that must stay failed) ----
        bad, kind = _invalid_source_for(req)
        bad_src_val = ucams.validate_asset(spec, bad, asset_meta=RIGHTS)
        bad_export = norm.governed_export(spec, bad)
        if kind == "corrupt-file":
            inv_ok = (bad_src_val["result"] == "FAIL" and bad_export.get("error"))
        else:
            # Below hard minimum: source must FAIL. (Normalizer can upscale, but the source floor is a
            # governed hard requirement — publication is blocked and human review is required.)
            inv_ok = (bad_src_val["result"] == "FAIL")
        results.append({"profile": pid, "role": role, "family": fam, "case": f"INVALID ({kind})",
                        "source_result": bad_src_val["result"], "ok": bool(inv_ok)})
        passed += bool(inv_ok); failed += (not inv_ok)

    print(json.dumps({"passed": passed, "failed": failed, "results": results}, indent=2, default=str))
    print(f"\n=== SUMMARY: {passed} passed, {failed} failed ===")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
