from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean
from ai_service import llm_generate, parse_json, COMMAND_SYSTEM, RESEARCH_SYSTEM

router = APIRouter(prefix="/api/command", tags=["command"])


class CommandInput(BaseModel):
    message: str


async def _create_kr(params, user):
    count = await db.knowledge_records.count_documents({})
    rec = {
        "id": gen_id(),
        "kr_code": f"KR-{count + 1:05d}",
        "title": params.get("title", "Untitled"),
        "subtitle": "",
        "category": params.get("category", "General"),
        "verified_truth": params.get("verified_truth", ""),
        "consumer_translation": "", "everyday_analogy": "", "story": "",
        "memory_sentence": "", "references": [], "sources": [], "practice_activities": [],
        "confidence_score": 0, "verification_status": "Draft", "approval_status": "Pending",
        "reviewer": None, "products_created": 0, "version": 1,
        "created_by": user["name"], "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.knowledge_records.insert_one(dict(rec))
    return {"type": "KnowledgeRecord", "id": rec["id"], "code": rec["kr_code"], "title": rec["title"]}


async def _create_mo(params, user):
    count = await db.manufacturing_orders.count_documents({})
    order = {
        "id": gen_id(),
        "mo_code": f"MO-{count + 1:05d}",
        "topic": params.get("topic", "Untitled"),
        "audience": params.get("audience", "General"),
        "learning_level": "General",
        "product_types": params.get("product_types", []),
        "priority": params.get("priority", "Medium"),
        "due_date": None, "verification_level": "Standard", "assigned_employees": [],
        "knowledge_record_id": None, "status": "Queued", "deliverables": [],
        "approval_history": [{"stage": "Created", "by": user["name"], "at": now_iso()}],
        "created_by": user["name"], "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.manufacturing_orders.insert_one(dict(order))
    return {"type": "ManufacturingOrder", "id": order["id"], "code": order["mo_code"], "title": order["topic"]}


@router.post("")
async def run_command(data: CommandInput, user=Depends(get_current_user)):
    session_id = f"command-{user['id']}"
    raw = await llm_generate(COMMAND_SYSTEM, data.message, session_id)
    parsed = parse_json(raw) or {"reply": raw, "action": "none", "parameters": {}}
    action = parsed.get("action", "none")
    params = parsed.get("parameters", {}) or {}
    reply = parsed.get("reply", "")
    created = None

    if action == "create_knowledge_record":
        created = await _create_kr(params, user)
    elif action == "create_manufacturing_order":
        created = await _create_mo(params, user)
    elif action == "start_research":
        brief = await llm_generate(RESEARCH_SYSTEM, params.get("topic", data.message), f"research-{gen_id()}")
        rdata = parse_json(brief) or {}
        kr = await _create_kr({
            "title": params.get("topic", "Research Topic"),
            "category": rdata.get("suggested_category", "Research"),
            "verified_truth": rdata.get("summary", ""),
        }, user)
        if rdata.get("confidence_score"):
            await db.knowledge_records.update_one(
                {"id": kr["id"]}, {"$set": {"confidence_score": rdata["confidence_score"],
                                            "sources": rdata.get("sources", [])}})
        created = kr

    # persist to history
    await db.command_history.insert_one({
        "id": gen_id(), "user_id": user["id"], "role": "user",
        "message": data.message, "created_at": now_iso(),
    })
    await db.command_history.insert_one({
        "id": gen_id(), "user_id": user["id"], "role": "assistant",
        "message": reply, "action": action, "created": created, "created_at": now_iso(),
    })
    return {"reply": reply, "action": action, "created": created}


@router.get("/history")
async def command_history(user=Depends(get_current_user)):
    msgs = await db.command_history.find({"user_id": user["id"]}).sort("created_at", 1).to_list(200)
    return clean(msgs)
