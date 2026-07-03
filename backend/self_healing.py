"""QRU Self-Healing Factory™ — failures become intelligent, self-recovering workflows.

Classifies every failure, chooses a recovery posture, produces a transparent human-readable
status, and records the outcome in the Factory Learning Database so recovery improves over time.

Treasure Standard™ principle: "Failures are not endpoints. They are opportunities for the
factory to become smarter."
"""
from database import db
from models import gen_id, now_iso

# category -> (transparent status, factory response, recommended action, founder_required, confidence)
CLASSIFICATION = {
    "ai_capacity": ("Waiting for AI Capacity", "Retrying automatically; will resume when AI capacity returns.",
                    "No action needed — auto-resumes. Add balance / raise the daily cap to accelerate.", False, 0.9),
    "rate_limit": ("Retrying Automatically", "Backing off and retrying with exponential delay.",
                   "No action needed — automatic recovery in progress.", False, 0.92),
    "provider_switch": ("Switched to Backup Provider", "Primary AI provider unavailable — using an alternate approved provider.",
                        "No action needed — manufacturing continues.", False, 0.85),
    "authentication": ("Blocked — Credentials", "Provider authentication failed.",
                       "Founder: verify the integration credentials in the Integration Hub.", True, 0.95),
    "missing_kr": ("Blocked by Missing Knowledge Record", "No verified Knowledge Record available for this topic.",
                   "Manufacture or verify a Knowledge Record for this topic first.", False, 0.9),
    "missing_data": ("Blocked — Missing Data", "Required input data was missing.",
                     "Founder: review the source topic/order inputs.", True, 0.8),
    "media_render": ("Retrying Media Render", "Media rendering failed; retrying and will fall back to a branded still.",
                     "No action needed — automatic recovery in progress.", False, 0.8),
    "distribution": ("Distribution Pending", "Publishing succeeded; distribution routing is pending/retrying.",
                     "No action needed — distribution retries automatically.", False, 0.85),
    "workflow_logic": ("Ready for Review", "A workflow logic issue was detected.",
                       "Founder: review this job's logs.", True, 0.6),
    "human_approval": ("Awaiting Founder Decision", "Human judgment is genuinely required (policy/quality/legal).",
                       "Founder: review and decide.", True, 0.99),
    "unknown": ("Retrying Automatically", "Unclassified issue; retrying automatically.",
                "Monitoring — will escalate if it recurs.", False, 0.5),
}


def classify_failure(err: str) -> dict:
    e = (err or "").lower()
    if "budget" in e or "spend limit" in e:
        cat = "ai_capacity"
    elif "rate" in e and "limit" in e:
        cat = "rate_limit"
    elif "503" in e or "temporarily unavailable" in e or "overload" in e:
        cat = "ai_capacity"
    elif "auth" in e or "api key" in e or "401" in e or "unauthorized" in e:
        cat = "authentication"
    elif "knowledge record" in e or "no verified" in e:
        cat = "missing_kr"
    elif "no recipe" in e or "missing" in e:
        cat = "missing_data"
    elif "ffmpeg" in e or "render" in e or "image" in e or "slideshow" in e or "audio" in e:
        cat = "media_render"
    elif "distribut" in e:
        cat = "distribution"
    else:
        cat = "unknown"
    status, response, action, founder, conf = CLASSIFICATION[cat]
    return {"category": cat, "human_status": status, "factory_response": response,
            "recommended_action": action, "founder_required": founder, "confidence": conf}


async def record_event(job_id, stage, err, classification, recovered: bool, attempts: int):
    await db.factory_healing_log.insert_one({
        "id": gen_id(), "job_id": job_id, "stage": stage, "error": (err or "")[:300],
        "category": classification["category"], "human_status": classification["human_status"],
        "recovered": recovered, "attempts": attempts, "founder_required": classification["founder_required"],
        "at": now_iso(),
    })


async def learning_summary():
    logs = await db.factory_healing_log.find().sort("at", -1).to_list(1000)
    by_cat = {}
    for l in logs:
        c = by_cat.setdefault(l["category"], {"count": 0, "recovered": 0})
        c["count"] += 1
        c["recovered"] += 1 if l.get("recovered") else 0
    strategies = [{"category": k, "occurrences": v["count"],
                   "auto_recovered": v["recovered"],
                   "recovery_rate": round(v["recovered"] / v["count"] * 100) if v["count"] else 0}
                  for k, v in sorted(by_cat.items(), key=lambda x: -x[1]["count"])]
    return {"total_events": len(logs), "strategies": strategies,
            "recent": [{"category": l["category"], "human_status": l["human_status"],
                        "recovered": l.get("recovered"), "at": l["at"]} for l in logs[:15]]}
