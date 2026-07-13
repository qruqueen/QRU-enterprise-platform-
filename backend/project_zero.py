"""QRU Project Zero™ — closed learning loop.

Real learner/product feedback is ingested and flows back into the originating Knowledge Record so
that improvements become enterprise learning. Deterministic only (Treasure Standard™): no AI, no
fabricated metrics — aggregates are computed strictly from submitted feedback. If no real feedback
exists, the loop is honestly empty.
"""
import re
from collections import Counter
from database import db
from models import gen_id, now_iso

_STOP = {
    "the", "and", "for", "with", "that", "this", "was", "were", "have", "has", "had", "you", "your",
    "but", "not", "are", "were", "would", "could", "should", "more", "less", "very", "just", "some",
    "about", "when", "what", "which", "them", "they", "from", "into", "than", "then", "there", "here",
    "make", "made", "need", "needs", "want", "like", "really", "also", "much", "many", "understand",
}


async def _kr(kr_id):
    for coll in (db.knowledge_engine_records, db.knowledge_records):
        doc = await coll.find_one({"id": kr_id}, {"_id": 0})
        if doc:
            return doc, coll
    return None, None


def _themes(texts, top=5):
    words = []
    for t in texts:
        words += [w for w in re.findall(r"[a-zA-Z]{4,}", (t or "").lower()) if w not in _STOP]
    common = Counter(words).most_common(top)
    return [{"signal": w, "mentions": c} for w, c in common if c > 0]


async def recompute(kr_id):
    fb = [f async for f in db.project_zero_feedback.find({"kr_id": kr_id}, {"_id": 0})]
    ratings = [f["rating"] for f in fb if isinstance(f.get("rating"), (int, float))]
    deltas = [f["understanding_after"] - f["understanding_before"] for f in fb
              if isinstance(f.get("understanding_after"), (int, float))
              and isinstance(f.get("understanding_before"), (int, float))]
    agg = {
        "feedback_count": len(fb),
        "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
        "avg_understanding_gain": round(sum(deltas) / len(deltas), 1) if deltas else None,
        "improvement_signals": _themes([f.get("suggested_improvement") or f.get("comment") or "" for f in fb]),
        "updated_at": now_iso(),
    }
    for coll in (db.knowledge_engine_records, db.knowledge_records):
        await coll.update_one({"id": kr_id}, {"$set": {"project_zero": agg}})
    return agg


async def ingest_feedback(kr_id, payload, actor="Learner"):
    kr, _ = await _kr(kr_id)
    if not kr:
        return None
    rec = {
        "id": gen_id(), "kr_id": kr_id,
        "product_id": payload.get("product_id"),
        "product_type": payload.get("product_type"),
        "source": payload.get("source", "learner"),
        "rating": payload.get("rating"),
        "understanding_before": payload.get("understanding_before"),
        "understanding_after": payload.get("understanding_after"),
        "comment": (payload.get("comment") or "").strip(),
        "suggested_improvement": (payload.get("suggested_improvement") or "").strip(),
        "summary": (payload.get("comment") or payload.get("suggested_improvement") or "Learner feedback").strip()[:180],
        "created_by": actor, "created_at": now_iso(),
    }
    await db.project_zero_feedback.insert_one(dict(rec))
    rec.pop("_id", None)
    agg = await recompute(kr_id)
    return {"feedback": rec, "aggregate": agg}


async def loop(kr_id):
    fb = [f async for f in db.project_zero_feedback.find({"kr_id": kr_id}, {"_id": 0}).sort("created_at", -1).limit(20)]
    kr, _ = await _kr(kr_id)
    agg = (kr or {}).get("project_zero") if kr else None
    if fb and not agg:
        agg = await recompute(kr_id)
    return {"feedback": fb, "aggregate": agg or {"feedback_count": 0}}
