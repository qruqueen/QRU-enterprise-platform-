"""
QRU ENTERPRISE RELATIONSHIP ENGINE™ — every enterprise object understands what it is
connected to. Connects Knowledge Records, Standards, Recipes, Characters, Colleges,
Divisions, AI Directors, Manufacturing Orders, Products, Customers, Media Assets, Brand
Assets, Lessons Learned, Workflows, and Verification Reports into one live graph.
"""
from database import db
import character_registry as wis
import qiks

# Canonical relationship schema (type → what it connects to). The permanent enterprise map.
SCHEMA = [
    {"type": "Knowledge Records", "connects_to": ["Standards", "Verification Reports", "Manufacturing Orders", "Products", "Colleges"]},
    {"type": "Standards", "connects_to": ["Standards", "Products", "Recipes", "AI Directors", "Colleges"]},
    {"type": "Recipes", "connects_to": ["Knowledge Records", "Products", "AI Directors"]},
    {"type": "Characters", "connects_to": ["Divisions", "AI Directors", "Products", "Media Assets", "Brand Assets"]},
    {"type": "Colleges", "connects_to": ["Knowledge Records", "Products", "Divisions"]},
    {"type": "Divisions", "connects_to": ["AI Directors", "Workflows", "Lessons Learned"]},
    {"type": "AI Directors", "connects_to": ["Divisions", "Workflows", "Manufacturing Orders", "Characters"]},
    {"type": "Manufacturing Orders", "connects_to": ["Knowledge Records", "Products", "Workflows", "Lessons Learned"]},
    {"type": "Products", "connects_to": ["Knowledge Records", "Customers", "Media Assets", "Brand Assets", "Standards"]},
    {"type": "Customers", "connects_to": ["Products"]},
    {"type": "Media Assets", "connects_to": ["Products", "Characters"]},
    {"type": "Brand Assets", "connects_to": ["Products", "Characters", "Standards"]},
    {"type": "Lessons Learned", "connects_to": ["Manufacturing Orders", "Divisions", "Standards"]},
    {"type": "Workflows", "connects_to": ["Manufacturing Orders", "AI Directors", "Divisions"]},
    {"type": "Verification Reports", "connects_to": ["Knowledge Records", "Products"]},
]

TYPE_META = {
    "Knowledge Records": ("knowledge_records", None),
    "Products": ("products", None),
    "Customers": ("customers", None),
    "Manufacturing Orders": ("manufacturing_orders", None),
    "Workflows": ("workflow_jobs", None),
    "Media Assets": ("media_assets", None),
    "Colleges": ("colleges", None),
}


async def graph_overview():
    """Live counts per enterprise object type + total connections defined."""
    nodes = []
    for t in SCHEMA:
        col = TYPE_META.get(t["type"], (None, None))[0]
        count = await db[col].count_documents({}) if col else None
        if t["type"] == "Standards":
            count = await qiks.STD_COL.count_documents({})
        elif t["type"] == "Lessons Learned":
            count = await qiks.LESSON_COL.count_documents({})
        elif t["type"] == "Characters" or t["type"] == "AI Directors":
            count = await wis.CHAR_COL.count_documents({})
        elif t["type"] == "Recipes":
            count = 44
        elif t["type"] == "Brand Assets":
            count = await db.brand_library.count_documents({}) or 1
        elif t["type"] == "Divisions":
            count = 6
        elif t["type"] == "Verification Reports":
            count = await db.knowledge_records.count_documents({"verification_status": "Verified"})
        nodes.append({"type": t["type"], "count": count if count is not None else 0, "connects_to": t["connects_to"]})
    edges = sum(len(t["connects_to"]) for t in SCHEMA)
    return {"nodes": nodes, "relationship_types": edges, "object_types": len(SCHEMA)}


async def object_relationships(otype: str, oid: str):
    """What a specific object is connected to (live)."""
    connections = {}
    if otype == "Products":
        p = await db.products.find_one({"id": oid}) or {}
        if p.get("kr_id"):
            kr = await db.knowledge_records.find_one({"id": p["kr_id"]})
            if kr:
                connections["Knowledge Records"] = [{"id": kr["id"], "label": kr.get("title", kr["id"])}]
        buyers = []
        async for pu in db.purchases.find({"product_id": oid}).limit(10):
            buyers.append({"id": pu.get("customer_email", "customer"), "label": pu.get("customer_email", "Customer")})
        if buyers:
            connections["Customers"] = buyers
        media = []
        async for m in db.media_assets.find({"product_id": oid}).limit(10):
            media.append({"id": m.get("id"), "label": m.get("type", "media")})
        if media:
            connections["Media Assets"] = media
    elif otype == "Knowledge Records":
        prods = []
        async for p in db.products.find({"kr_id": oid}).limit(20):
            prods.append({"id": p["id"], "label": p.get("title", p["id"])})
        if prods:
            connections["Products"] = prods
    elif otype == "Standards":
        s = await qiks.get_standard(oid) or {}
        rel = []
        for r in s.get("related_standards", []):
            rs = await qiks.get_standard(r)
            if rs:
                rel.append({"id": r, "label": rs["name"]})
        if rel:
            connections["Standards"] = rel
        if s.get("related_ai_agents"):
            connections["AI Directors"] = [{"id": a, "label": a} for a in s["related_ai_agents"]]
    elif otype == "Characters":
        c = await wis.get_character(oid) or {}
        if c:
            connections["Divisions"] = [{"id": c.get("department"), "label": c.get("department")}]
            connections["AI Directors"] = [{"id": c["id"], "label": r} for r in c.get("roles", [])]
    return {"type": otype, "id": oid, "connections": connections}


async def suggest(otype: str, oid: str):
    """Auto-suggest related knowledge for a new/updated object."""
    suggestions = []
    if otype in ("Products", "Knowledge Records"):
        doc = await (db.products if otype == "Products" else db.knowledge_records).find_one({"id": oid}) or {}
        text = f"{doc.get('title','')} {doc.get('category','')}"
        consult = await qiks.consult(text)
        suggestions = [{"type": "Standards", "id": s["id"], "label": s["name"], "reason": "Applicable institutional standard"} for s in consult["applicable_standards"][:4]]
        # Suggest an aligned character by department/category keyword.
        ch = await wis.get_by_role_or_department(doc.get("category", ""))
        if ch:
            suggestions.append({"type": "Characters", "id": ch["id"], "label": ch["name"], "reason": "Aligned QRU Director for brand identity"})
    return {"type": otype, "id": oid, "suggestions": suggestions}
