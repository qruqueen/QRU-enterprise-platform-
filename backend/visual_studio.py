"""QRU Visual Intelligence Studio™ (MO-009) — operating engine.

Configured by the Founder declaration (STD-00032). Phase 1 delivers the DETERMINISTIC core the
charter calls Priority 1 ("correct rendering failures"): the Layout Intelligence analyzer enforces
the layout_rules, and the Gold Standard Experience review runs the quality_checks. $0 AI —
deterministic and honest: checks that genuinely require human/visual judgment are marked
'human_review' rather than faked (Treasure Standard™).
"""
import re

# ---- Operating configuration (from the Founder YAML declaration) ----
CONFIG = {
    "enabled": True, "version": "1.0",
    "mission": "Transform verified knowledge into premium visual learning experiences that improve "
               "understanding, memory, engagement, and product desirability.",
    "governing_standard": "QRU Visual Intelligence Studio",
    "departments": {k: True for k in [
        "cinematic_hero_artwork", "concept_visualization", "memory_illustration_library",
        "character_intelligence", "storyboard_design", "diagram_intelligence", "icon_language",
        "layout_experience_design", "infographic_manufacturing", "memory_maps", "world_building",
        "gold_gallery", "neuro_design_lab"]},
    "quality_checks": {k: True for k in [
        "cover_invitation_test", "first_spread_test", "eye_flow_test", "reading_density_test",
        "visual_balance_test", "continuation_test", "memory_test", "understanding_test",
        "display_test", "share_test", "more_test"]},
    "layout_rules": {k: True for k in [
        "prevent_character_per_line", "prevent_word_stacking", "prevent_blank_pages",
        "prevent_unbalanced_spacing", "prevent_duplicate_titles", "enforce_reading_rhythm",
        "enforce_visual_hierarchy", "enforce_brand_typography", "enforce_page_value_rule"]},
    "outputs": ["hero_image", "concept_art", "diagrams", "infographics", "comparison_graphics",
                "workbook_graphics", "chapter_openers", "memory_maps", "marketing_assets", "social_media_assets"],
    "approval": {"treasure_standard_required": True, "gold_standard_required": True},
}

DEPARTMENT_LABELS = {
    "cinematic_hero_artwork": "Cinematic Hero Artwork™", "concept_visualization": "Concept Visualization™",
    "memory_illustration_library": "Memory Illustration Library™", "character_intelligence": "Character Intelligence System™",
    "storyboard_design": "Storyboard & Learning Journey™", "diagram_intelligence": "Diagram Intelligence™",
    "icon_language": "Icon & Symbol Language™", "layout_experience_design": "Layout Experience Design™",
    "infographic_manufacturing": "Infographic Manufacturing™", "memory_maps": "QRU Memory Maps™",
    "world_building": "World-Building & University Identity™", "gold_gallery": "QRU Gold Gallery™",
    "neuro_design_lab": "NeuroDesign Lab™",
}


def _text(product):
    return product.get("content") or product.get("summary") or ""


def analyze_layout(product):
    """Deterministic Layout Intelligence™ analysis — detects rendering failures against layout_rules."""
    text = _text(product)
    lines = text.split("\n")
    nonempty = [ln for ln in lines if ln.strip()]
    words = text.split()
    violations = []

    def viol(rule, severity, message):
        violations.append({"rule": rule, "severity": severity, "message": message})

    # prevent_character_per_line — lines that are a single character
    single_char = [ln for ln in nonempty if len(ln.strip()) == 1]
    if len(single_char) >= 3:
        viol("prevent_character_per_line", "high", f"{len(single_char)} lines contain a single character — likely character-per-line rendering failure.")

    # prevent_word_stacking — many consecutive single-word lines
    single_word_runs, run = 0, 0
    for ln in lines:
        if len(ln.split()) == 1 and ln.strip():
            run += 1
            single_word_runs = max(single_word_runs, run)
        else:
            run = 0
    if single_word_runs >= 5:
        viol("prevent_word_stacking", "high", f"A run of {single_word_runs} single-word lines suggests vertical word stacking / broken wrapping.")

    # prevent_blank_pages / page_value — content too thin
    if len(words) < 60:
        viol("enforce_page_value_rule", "high", f"Only {len(words)} words of content — insufficient learning value; risks blank/near-empty pages.")

    # prevent_unbalanced_spacing — excessive consecutive blank lines
    blank_run, max_blank = 0, 0
    for ln in lines:
        blank_run = blank_run + 1 if not ln.strip() else 0
        max_blank = max(max_blank, blank_run)
    if max_blank >= 5:
        viol("prevent_unbalanced_spacing", "medium", f"{max_blank} consecutive blank lines — unbalanced spacing / accidental white space.")

    # prevent_duplicate_titles — repeated identical heading-like lines
    headings = [ln.strip() for ln in nonempty if len(ln.strip()) < 80 and (ln.strip().isupper() or ln.strip().startswith("#"))]
    dupes = {h for h in headings if headings.count(h) > 1}
    if dupes:
        viol("prevent_duplicate_titles", "medium", f"Duplicate title/heading detected: {', '.join(list(dupes)[:2])}.")

    # enforce_visual_hierarchy — presence of headings/structure
    if not headings and len(words) > 150:
        viol("enforce_visual_hierarchy", "medium", "No headings detected — content lacks visual hierarchy for scanning.")

    # enforce_reading_rhythm — overly long paragraphs
    paras = [p for p in text.split("\n\n") if p.strip()]
    long_paras = [p for p in paras if len(p.split()) > 180]
    if long_paras:
        viol("enforce_reading_rhythm", "low", f"{len(long_paras)} very long paragraph(s) (>180 words) — break up for reading rhythm.")

    high = sum(1 for v in violations if v["severity"] == "high")
    score = max(0, 100 - high * 30 - sum(1 for v in violations if v["severity"] == "medium") * 12 - sum(1 for v in violations if v["severity"] == "low") * 4)
    return {
        "product_id": product.get("id"), "product_code": product.get("product_code"), "title": product.get("title"),
        "word_count": len(words), "line_count": len(lines),
        "violations": violations, "layout_score": score,
        "passed": high == 0 and score >= 70,
        "note": "enforce_brand_typography is governed at render time (fonts/spacing tokens) — advisory here.",
    }


# Which Gold Standard tests can be auto-evaluated deterministically vs require human/visual review.
def gold_standard_review(product):
    """Runs the 11 Gold Standard Experience™ quality_checks. Honest: visual/subjective checks that
    require rendered artwork or human judgment are returned as 'human_review', never auto-passed."""
    text = _text(product)
    words = text.split()
    has_headings = bool([ln for ln in text.split("\n") if ln.strip().isupper() or ln.strip().startswith("#")])
    memory = bool(re.search(r"memory|remember|in short|key takeaway", text, re.I))
    layout = analyze_layout(product)

    checks = []
    def add(name, status, detail):
        checks.append({"check": name, "status": status, "detail": detail})

    add("reading_density_test", "pass" if 80 <= len(words) <= 4000 else ("fail" if len(words) < 80 else "warn"),
        f"{len(words)} words.")
    add("understanding_test", "pass" if has_headings else "warn", "Structured with headings." if has_headings else "Add headings/structure to aid understanding.")
    add("memory_test", "pass" if memory else "warn", "Memory anchor detected." if memory else "No explicit memory anchor found — add a memory sentence.")
    add("visual_balance_test", "pass" if layout["passed"] else "fail", f"Layout score {layout['layout_score']}.")
    add("eye_flow_test", "pass" if layout["layout_score"] >= 70 else "warn", "Based on layout hierarchy & spacing.")
    add("continuation_test", "pass" if layout["passed"] and len(words) >= 120 else "warn", "Enough substance to keep the reader going." )
    # Subjective / visual — require human or rendered artwork
    for h in ("cover_invitation_test", "first_spread_test", "display_test", "share_test", "more_test"):
        add(h, "human_review", "Requires rendered artwork / human visual judgment (Gold Standard Reviewer™).")

    auto = [c for c in checks if c["status"] != "human_review"]
    passed = sum(1 for c in auto if c["status"] == "pass")
    treasure_ok = layout["passed"] and len(words) >= 80
    return {
        "product_id": product.get("id"), "product_code": product.get("product_code"), "title": product.get("title"),
        "checks": checks,
        "auto_score": round(passed / len(auto) * 100) if auto else 0,
        "auto_passed": passed, "auto_total": len(auto),
        "human_review_pending": sum(1 for c in checks if c["status"] == "human_review"),
        "treasure_standard": "Met" if treasure_ok else "Not Met",
        "gold_standard": "Pending Human Review" if treasure_ok else "Blocked — fix layout/value first",
        "layout": layout,
    }
