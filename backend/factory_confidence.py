"""QRU Factory Confidence™ & Data Health™ (MO-038) — deterministic ($0 AI).

Two pre-publication safety instruments used across the Founder Review Command Center™,
the Founder Inbox™, and the Autonomous Manufacturing Engine™:

  • Data Health™ — a single traffic-light status describing whether a product has every
    dependency it needs (Knowledge, Assets, Metadata, rendered deliverable) or is Blocked.
  • Factory Confidence™ — a composite 0-100 score blending Design, Treasure Standard™,
    Data Health™, Marketplace Readiness and Recipe compliance.

Both are computed purely from existing product data — no LLM budget is ever spent.
Governance preserved: these instruments only SCORE and CLASSIFY. They never publish.
"""

MIN_CONTENT_CHARS = 180

# Data Health™ traffic lights (fix-effort ascending → severity ascending).
HEALTH = {
    "ready":          {"emoji": "🟢", "label": "Ready",          "color": "emerald"},
    "needs_metadata": {"emoji": "🟡", "label": "Needs Metadata", "color": "amber"},
    "needs_assets":   {"emoji": "🟠", "label": "Needs Assets",   "color": "orange"},
    "needs_knowledge":{"emoji": "🔵", "label": "Needs Knowledge", "color": "blue"},
    "blocked":        {"emoji": "🔴", "label": "Blocked",         "color": "red"},
}


def _design_score(p):
    gate = p.get("design_gate") or {}
    sc = p.get("design_scorecard") or {}
    if gate.get("score") is not None:
        return gate["score"]
    return sc.get("overall")


def _design_passed(p, threshold=91):
    gate = p.get("design_gate") or {}
    if gate.get("passed") is not None:
        return bool(gate["passed"])
    sc = p.get("design_scorecard") or {}
    if sc.get("overall") is not None:
        return sc["overall"] >= threshold
    return False


def _marketplace_readiness(p):
    sc = p.get("design_scorecard") or {}
    for l in sc.get("categories", []):
        if l.get("category") == "Marketplace Readiness":
            return l.get("score", 0) * 10
    # deterministic fallback from marketplace assets present
    have = sum(bool(p.get(k)) for k in ("thumbnail_url", "store_graphic_url", "marketing_kit_ready"))
    return round(have / 3 * 100)


def _recipe_score(p):
    sc = p.get("design_scorecard") or {}
    comp = sc.get("product_type_compliance") or {}
    if comp.get("score") is not None:
        return comp["score"] * 10
    return 100 if p.get("deliverable_ready") else 40


def _has_knowledge(p):
    content = p.get("content") or ""
    return len(content) >= MIN_CONTENT_CHARS or bool(p.get("knowledge_record_id")) or bool(p.get("assembled"))


def _needs_asset(p):
    # Founder-selected asset mode requires an actual chosen asset before manufacturing.
    if p.get("asset_mode") in ("founder_selected", "founder") and not p.get("cover_vault_asset"):
        return True
    return not bool(p.get("cover_url"))


def data_health(p):
    """Deterministic Data Health™ evaluation for a single product document."""
    content = p.get("content") or ""
    has_content = len(content) >= MIN_CONTENT_CHARS
    has_kr = bool(p.get("knowledge_record_id")) or bool(p.get("assembled"))
    metadata_ok = bool(p.get("family")) and bool(p.get("title")) and bool(p.get("product_type")) \
        and bool(p.get("creative_brief")) and p.get("creative_status") == "Reviewed" \
        and bool(p.get("preview_url") or p.get("marketing_kit_ready"))
    assets_ok = not _needs_asset(p)
    deliverable_ok = bool(p.get("deliverable_ready"))

    checklist = {
        "knowledge": bool(has_content or has_kr),
        "assets": assets_ok,
        "metadata": metadata_ok,
        "deliverable": deliverable_ok,
        "verified": bool(p.get("verified")),
    }
    reasons = []
    # Blocked = cannot proceed without new source material (missing content AND no KR).
    if not has_content and not has_kr:
        status = "blocked"
        reasons.append("No Knowledge Record and no content — needs source material.")
    elif not has_content and has_kr:
        # KR present but content not assembled/generated — needs AI or manual completion.
        status = "blocked"
        reasons.append("Knowledge Record present but content not yet manufactured.")
    elif not (has_content or has_kr):
        status = "needs_knowledge"
        reasons.append("Attach a Knowledge Record.")
    elif not assets_ok:
        status = "needs_assets"
        reasons.append("Needs a branded cover / Founder asset.")
    elif not deliverable_ok:
        status = "needs_assets"
        reasons.append("Deliverable not yet rendered.")
    elif not metadata_ok:
        status = "needs_metadata"
        if not (p.get("creative_brief") and p.get("creative_status") == "Reviewed"):
            reasons.append("Needs Creative Studio™ brief.")
        if not (p.get("preview_url") or p.get("marketing_kit_ready")):
            reasons.append("Needs a preview / marketing kit.")
        if not p.get("family"):
            reasons.append("Needs a product family.")
    else:
        status = "ready"

    meta = HEALTH[status]
    return {
        "status": status, "label": meta["label"], "emoji": meta["emoji"], "color": meta["color"],
        "checklist": checklist, "reasons": reasons,
        "ready": status == "ready", "blocked": status == "blocked",
    }


def factory_confidence(p, threshold=91):
    """Composite Factory Confidence™ score (0-100), deterministic."""
    dh = data_health(p)
    ds = _design_score(p)
    design_component = ds if isinstance(ds, (int, float)) else 40
    if p.get("treasure_standard"):
        treasure_component = 100
    elif p.get("deliverable_ready"):
        treasure_component = 60
    else:
        treasure_component = 20
    dh_map = {"ready": 100, "needs_metadata": 75, "needs_assets": 55, "needs_knowledge": 30, "blocked": 0}
    dh_component = dh_map[dh["status"]]
    market_component = _marketplace_readiness(p)
    recipe_component = _recipe_score(p)

    components = [
        {"name": "Design Director™", "score": round(design_component), "weight": 30},
        {"name": "Treasure Standard™", "score": treasure_component, "weight": 20},
        {"name": "Data Health™", "score": dh_component, "weight": 20},
        {"name": "Marketplace Readiness", "score": round(market_component), "weight": 15},
        {"name": "Recipe Compliance", "score": round(recipe_component), "weight": 15},
    ]
    score = round(sum(c["score"] * c["weight"] for c in components) / 100)
    band = "High" if score >= 90 else ("Medium" if score >= 70 else "Low")
    return {
        "score": score, "band": band, "components": components,
        "data_health": dh,
        "design_passed": _design_passed(p, threshold),
    }


def publish_gate(p, threshold=91):
    """Un-bypassable publication gate. Returns (publishable, blockers[])."""
    dh = data_health(p)
    blockers = []
    if not dh["ready"]:
        blockers.append(f"Data Health™: {dh['label']}" + (f" — {dh['reasons'][0]}" if dh["reasons"] else ""))
    if not _design_passed(p, threshold):
        ds = _design_score(p)
        blockers.append(f"Design Director™ score {ds if ds is not None else '—'} below {threshold}")
    if not p.get("verified"):
        blockers.append("Product Protection™ verification")
    if not (p.get("creative_brief") and p.get("creative_status") == "Reviewed"):
        blockers.append("Creative Studio™ review")
    if not p.get("deliverable_ready"):
        blockers.append("Customer deliverable not rendered")
    return (len(blockers) == 0, blockers)
