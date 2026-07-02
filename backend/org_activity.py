from database import db
from models import gen_id, now_iso


async def log_org(agent: str, department: str, action: str, entity: str = "", level: str = "info"):
    """Append an entry to the live Organizational Activity feed."""
    await db.org_activity.insert_one({
        "id": gen_id(),
        "agent": agent,
        "department": department,
        "action": action,
        "entity": entity,
        "level": level,
        "created_at": now_iso(),
    })
