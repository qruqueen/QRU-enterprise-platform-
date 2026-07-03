"""QRU Enterprise Intelligence™ — the LLM-narrated Level-5 Autonomy layer.

Adds GPT-narrated recommendations on top of the deterministic autonomy engine:
  • Continuous Improvement narrative (Factory Council™)
  • Product Evolution™ (ratings/engagement → recommend v2/v3)
  • Predictive Manufacturing™ (trends → recommend future Manufacturing Orders™)
  • Innovation Radar™ (safe upgrade recommendations)
  • Narrated daily Executive Brief™

Every function DEGRADES GRACEFULLY: if the LLM is unavailable (e.g. daily spend
limit / budget), it returns the deterministic data plus an `ai_available: false`
note instead of failing — so the enterprise keeps operating.
"""
import logging

from database import db
from models import gen_id, now_iso
from ai_service import llm_generate, parse_json
import autonomy

logger = logging.getLogger("qru.enterprise_intel")


async def _narrate(system: str, prompt: str, session: str):
    """Call the LLM; return (data|None, available, reason)."""
    try:
        raw = await llm_generate(system, prompt, session)
        return parse_json(raw), True, None
    except Exception as e:
        reason = "Daily spend limit reached" if "spend limit" in str(e).lower() else (
                 "Budget exceeded" if "Budget" in str(e) else "AI service temporarily unavailable")
        logger.warning(f"enterprise-intel narration unavailable: {reason}")
        return None, False, reason


# ---------------- Continuous Improvement narrative ----------------
IMPROVE_SYS = """You are the QRU Factory Council™ Chair. Given division reports and factory health,
write a concise Enterprise Improvement Report. Return ONLY JSON:
{"headline": "one-line state of the factory", "top_actions": ["3-5 highest-value, safe improvements"],
 "quality_watch": "one sentence on Treasure Standard risk", "cost_note": "one sentence on cost efficiency"}"""


async def improvement_report():
    council = await autonomy.factory_council()
    health = await autonomy.factory_health()
    scorecard = await autonomy.ai_scorecard()
    prompt = (f"Factory health: {health['overall_score']}% ({health['factory_health']}).\n"
              f"Division reports: {council['division_reports']}\n"
              f"Deterministic top improvements: {council['top_improvements']}\n"
              f"Estimated spend: ${scorecard['total_estimated_cost_usd']}.")
    data, available, reason = await _narrate(IMPROVE_SYS, prompt, "intel-improve")
    return {"deterministic": council, "ai_narrative": data, "ai_available": available, "reason": reason}


# ---------------- Product Evolution™ ----------------
async def rate_product(product_id, user, rating, review=""):
    product = await db.products.find_one({"id": product_id})
    if not product:
        return None, "Product not found"
    await db.product_ratings.insert_one({
        "id": gen_id(), "product_id": product_id, "product_code": product.get("product_code"),
        "user_id": str(user.get("id", "")), "user_email": user.get("email", ""),
        "rating": max(1, min(5, int(rating))), "review": (review or "")[:1000], "created_at": now_iso(),
    })
    return {"ok": True}, None


EVOLVE_SYS = """You are QRU Product Evolution™. Given a product and its customer feedback/engagement,
recommend whether to release a new version and what to improve. Return ONLY JSON:
{"recommend_new_version": true|false, "next_version": "v2|v3|none",
 "improvements": ["specific, evidence-based improvements"], "rationale": "1-2 sentences"}"""


async def _rating_summary(product_id):
    ratings = await db.product_ratings.find({"product_id": product_id}).to_list(500)
    if not ratings:
        return {"count": 0, "avg": None, "reviews": []}
    avg = round(sum(r["rating"] for r in ratings) / len(ratings), 2)
    reviews = [r["review"] for r in ratings if r.get("review")][:8]
    return {"count": len(ratings), "avg": avg, "reviews": reviews}


async def product_evolution(product_id):
    product = await db.products.find_one({"id": product_id})
    if not product:
        return None, "Product not found"
    summary = await _rating_summary(product_id)
    prompt = (f"Product: {product.get('title')} ({product.get('product_type')}).\n"
              f"Ratings: {summary['count']} avg {summary['avg']}.\n"
              f"Reviews: {summary['reviews']}\n"
              f"Version: {product.get('kr_version', 1)}.")
    data, available, reason = await _narrate(EVOLVE_SYS, prompt, f"intel-evolve-{product_id[:8]}")
    if data:
        await db.products.update_one({"id": product_id}, {"$set": {"evolution": data, "evolution_at": now_iso()}})
    return {"product_id": product_id, "ratings": summary, "recommendation": data,
            "ai_available": available, "reason": reason}, None


async def evolution_overview():
    """Products with the most feedback + any stored evolution recommendations."""
    pipeline = [{"$group": {"_id": "$product_id", "count": {"$sum": 1}, "avg": {"$avg": "$rating"}}},
                {"$sort": {"count": -1}}, {"$limit": 20}]
    agg = await db.product_ratings.aggregate(pipeline).to_list(20)
    out = []
    for a in agg:
        p = await db.products.find_one({"id": a["_id"]})
        if p:
            out.append({"product_id": a["_id"], "product_code": p.get("product_code"),
                        "title": p.get("title"), "ratings": a["count"], "avg": round(a["avg"], 2),
                        "evolution": p.get("evolution")})
    return {"rated_products": out, "total_ratings": await db.product_ratings.count_documents({})}


# ---------------- Predictive Manufacturing™ ----------------
PREDICT_SYS = """You are QRU Predictive Manufacturing™. Given the current catalog, pending topics,
and thin subject areas, recommend the next Manufacturing Orders™ to create BEFORE demand peaks.
Return ONLY JSON:
{"recommended_orders": [{"topic": "...", "division": "Health|Faith|...", "why_now": "...", "priority": "High|Medium|Low"}],
 "seasonal_note": "one sentence on timing/seasonality"}"""


async def predictive_manufacturing():
    gaps = await autonomy.knowledge_gaps()
    published = await db.products.count_documents({"status": "Published"})
    prompt = (f"Published catalog size: {published}.\n"
              f"Pending high-priority topics: {[g['topic'] for g in gaps['pending_topics'][:12]]}\n"
              f"Thin catalogs (few products): {gaps['thin_catalogs']}\n"
              f"Current month: June 2026.")
    data, available, reason = await _narrate(PREDICT_SYS, prompt, "intel-predict")
    return {"gaps": gaps, "forecast": data, "ai_available": available, "reason": reason}


# ---------------- Innovation Radar™ ----------------
RADAR_SYS = """You are QRU Innovation Radar™. Recommend SAFE, high-value upgrades that would strengthen a
knowledge-manufacturing factory (AI, publishing, accessibility, automation, video/voice/image, learning science).
Be specific and pragmatic. Return ONLY JSON:
{"opportunities": [{"area": "...", "recommendation": "...", "impact": "High|Medium|Low", "effort": "High|Medium|Low"}]}"""


async def innovation_radar():
    scorecard = await autonomy.ai_scorecard()
    prompt = (f"Current providers/capabilities in use: {[c['name'] for c in scorecard['by_capability']]}.\n"
              f"Known constraints: music generation is spec-only; video is local slideshow; marketplace distribution is simulated.\n"
              f"Recommend safe upgrades that raise quality or reach without locking to one provider.")
    data, available, reason = await _narrate(RADAR_SYS, prompt, "intel-radar")
    return {"radar": data, "ai_available": available, "reason": reason}


# ---------------- Narrated daily Executive Brief™ ----------------
BRIEF_SYS = """You are the QRU Executive Advisor™ briefing Founder & CEO Erica Talbert. Turn the factory
metrics into a warm, concise executive brief. Return ONLY JSON:
{"greeting": "one warm line", "summary": "2-3 sentence state of the enterprise",
 "focus_today": ["3 prioritized actions"], "encouragement": "one mission-aligned closing line"}"""


async def narrated_brief(store=False):
    base = await autonomy.executive_brief()
    prompt = (f"Yesterday: {base['yesterday']}. Health: {base['factory_performance']}. "
              f"Revenue: {base['revenue']}. Risks: {base['risks']}. "
              f"Deterministic priorities: {base['focus_today']}.")
    data, available, reason = await _narrate(BRIEF_SYS, prompt, "intel-brief")
    result = {"date": now_iso(), "metrics": base, "narrative": data,
              "ai_available": available, "reason": reason}
    if store and data:
        await db.executive_briefs.insert_one({"id": gen_id(), **result})
    return result


async def latest_brief():
    docs = await db.executive_briefs.find().sort("date", -1).to_list(1)
    if docs:
        from models import clean
        return clean(docs[0])
    return await narrated_brief(store=False)
