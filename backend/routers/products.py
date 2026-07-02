from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import db
from auth import get_current_user
from models import gen_id, now_iso, clean
from ai_service import llm_generate

router = APIRouter(prefix="/api/products", tags=["products"])

PRODUCT_TYPES = [
    "Book", "Poster", "Infographic", "Presentation", "Teacher Guide", "Caregiver Guide",
    "Workbook", "Lesson Plan", "Video Script", "Podcast Script", "Short-form Content",
    "Interactive Lesson", "AI Tutor", "Course", "Certificate", "Flash Cards", "Quiz", "Printable PDF",
]


class GenerateInput(BaseModel):
    knowledge_record_id: Optional[str] = None
    topic: Optional[str] = None
    product_type: str
    audience: Optional[str] = "General public"
    learning_level: Optional[str] = "Introductory"


def product_system(ptype: str) -> str:
    return (
        f"You are the QRU Manufacturing Director producing a publication-ready {ptype}. "
        "QRU manufactures understanding from verified knowledge without simplifying the truth. "
        f"Generate complete, well-structured, professional {ptype} content in clean Markdown. "
        "Include a title, clear sections, and where relevant an everyday analogy and a memorable takeaway. "
        "Return ONLY the Markdown content."
    )


@router.get("")
async def list_products(product_type: Optional[str] = None, status: Optional[str] = None,
                        family: Optional[str] = None, user=Depends(get_current_user)):
    query = {}
    if product_type:
        query["product_type"] = product_type
    if status:
        query["status"] = status
    if family:
        query["family"] = family
    products = await db.products.find(query, {"content": 0}).sort("created_at", -1).to_list(500)
    return clean(products)


@router.get("/types")
async def get_types():
    return {"types": PRODUCT_TYPES}


@router.get("/{pid}")
async def get_product(pid: str, user=Depends(get_current_user)):
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Product not found")
    return clean(p)


@router.post("/generate")
async def generate_product(data: GenerateInput, user=Depends(get_current_user)):
    kr = None
    topic = data.topic
    family = "General"
    if data.knowledge_record_id:
        kr = await db.knowledge_records.find_one({"id": data.knowledge_record_id})
        if kr:
            topic = kr["title"]
            family = kr.get("category", "General")
    if not topic:
        raise HTTPException(400, "topic or knowledge_record_id required")

    context = ""
    if kr:
        context = (
            f"Verified Truth: {kr.get('verified_truth','')}\n"
            f"Consumer Translation: {kr.get('consumer_translation','')}\n"
            f"Analogy: {kr.get('everyday_analogy','')}\n"
        )
    prompt = (
        f"Topic: {topic}\nAudience: {data.audience}\nLearning Level: {data.learning_level}\n{context}\n"
        f"Produce the {data.product_type}."
    )
    content = await llm_generate(product_system(data.product_type), prompt, f"product-{gen_id()}")

    count = await db.products.count_documents({})
    product = {
        "id": gen_id(),
        "product_code": f"PRD-{count + 1:05d}",
        "title": f"{topic} — {data.product_type}",
        "product_type": data.product_type,
        "family": family,
        "topic": topic,
        "audience": data.audience,
        "learning_level": data.learning_level,
        "content": content,
        "status": "Draft",
        "knowledge_record_id": data.knowledge_record_id,
        "created_by": user["name"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.products.insert_one(dict(product))
    if kr:
        await db.knowledge_records.update_one(
            {"id": kr["id"]}, {"$inc": {"products_created": 1}})
    return clean(product)


class StatusInput(BaseModel):
    status: str


@router.patch("/{pid}/status")
async def set_status(pid: str, data: StatusInput, user=Depends(get_current_user)):
    if data.status not in ["Draft", "In Review", "Approved", "Published", "Archived"]:
        raise HTTPException(400, "Invalid status")
    p = await db.products.find_one({"id": pid})
    if not p:
        raise HTTPException(404, "Not found")
    await db.products.update_one({"id": pid}, {"$set": {"status": data.status, "updated_at": now_iso()}})
    return clean(await db.products.find_one({"id": pid}))


@router.delete("/{pid}")
async def delete_product(pid: str, user=Depends(get_current_user)):
    await db.products.delete_one({"id": pid})
    return {"message": "deleted"}
