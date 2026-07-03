"""QRU College Activation System™ — every College is a live manufacturing division
powered by the ONE shared QRU Factory™. Colleges supply defaults, topics, recipes and
branding; the Factory does the manufacturing.
"""
from database import db

VIDEO_TYPES = ["Short Video", "Long Video", "YouTube Video Script", "Video Script"]
BOOK_TYPES = ["Book", "Companion Book"]
COURSE_TYPES = ["Course"]

# Recipes offered when a College opens the Factory (mapped to real product recipes).
COLLEGE_RECIPES = ["Book", "Workbook", "Short Video", "Presentation", "Poster", "Podcast Script",
                   "Quiz", "Teacher Guide", "Student Guide", "Interactive Lesson", "Social Media Pack",
                   "Blog Article", "Email Newsletter", "Course", "Animation"]

SUGGESTED_TOPICS = {
    "Heart Health": ["Blood pressure basics", "Cholesterol explained", "Heart-healthy eating", "Exercise for the heart", "Recognizing warning signs"],
    "Brain Health": ["How memory works", "Protecting focus", "Sleep and the brain", "Stress and the mind", "Lifelong learning"],
    "Lung Health": ["How breathing works", "Protecting your lungs", "Air quality basics", "Breathing exercises"],
    "Finance": ["Saving", "Investing", "Budgeting", "Credit", "Taxes", "Debt", "Retirement", "Insurance"],
    "Faith": ["Gratitude", "Hope", "Patience", "Forgiveness", "Generosity"],
    "Programming": ["What is code", "Variables and logic", "Thinking like a developer", "Debugging basics"],
    "Business": ["Starting small", "Serving customers", "Simple marketing", "Cash flow basics"],
    "Nutrition": ["Hydration", "Fiber and gut health", "Reading labels", "Balanced plates"],
    "Mental Health": ["Managing stress", "Deep breathing", "Healthy routines", "Talking about feelings"],
}

DIVISION_TOPICS = {
    "Health": ["Prevention basics", "Healthy habits", "Understanding the body", "When to seek care"],
    "Faith": ["Foundations", "Character", "Community", "Daily practice"],
    "Finance": ["Money basics", "Saving and investing", "Avoiding debt", "Planning ahead"],
}


def _status_from(metrics, running):
    if metrics["published"] >= 5:
        return "Growing"
    if metrics["published"] >= 1:
        return "Live"
    if running > 0:
        return "Manufacturing"
    if metrics["verified"] > 0:
        return "Verification"
    if metrics["records"] > 0:
        return "Planning"
    return "Not Started"


async def college_metrics(college):
    name = college["name"]
    fam = {"family": name}
    records = await db.knowledge_records.count_documents({"category": name})
    verified = await db.knowledge_records.count_documents({"category": name, "verification_status": "Verified"})
    products = await db.products.count_documents(fam)
    published = await db.products.count_documents({**fam, "status": "Published"})
    treasure = await db.products.count_documents({**fam, "treasure_standard": True})
    videos = await db.products.count_documents({**fam, "product_type": {"$in": VIDEO_TYPES}})
    books = await db.products.count_documents({**fam, "product_type": {"$in": BOOK_TYPES}})
    courses = await db.products.count_documents({**fam, "product_type": {"$in": COURSE_TYPES}})
    orders = await db.manufacturing_orders.count_documents({"topic": {"$regex": name.split()[0], "$options": "i"}})
    running = await db.workflow_jobs.count_documents({"division": college.get("division"), "status": {"$in": ["running", "queued"]}})

    # revenue + students from purchases of this college's products
    prod_ids = [p["id"] async for p in db.products.find(fam, {"id": 1})]
    revenue_cents = 0
    students = 0
    if prod_ids:
        for pr in await db.purchases.find({"product_id": {"$in": prod_ids}}).to_list(5000):
            revenue_cents += int(round((pr.get("amount", 0)) * 100))
        students = await db.consumer_enrollments.count_documents({"product_id": {"$in": prod_ids}}) if \
            "consumer_enrollments" in await db.list_collection_names() else 0
        students = students or await db.purchases.count_documents({"product_id": {"$in": prod_ids}})
        ratings = await db.product_ratings.find({"product_id": {"$in": prod_ids}}).to_list(5000)
        avg_rating = round(sum(r["rating"] for r in ratings) / len(ratings), 2) if ratings else None
    else:
        avg_rating = None

    # avg treasure score
    scores = [p.get("verification", {}).get("confidence_score") async for p in
              db.products.find({**fam, "treasure_standard": True}, {"verification": 1})]
    scores = [s for s in scores if isinstance(s, (int, float))]
    avg_treasure = round(sum(scores) / len(scores)) if scores else (95 if treasure else None)

    understanding_impact = published * 100 + students * 10 + verified * 5

    m = {"records": records, "verified": verified, "products": products, "published": published,
         "treasure": treasure, "videos": videos, "books": books, "courses": courses, "orders": orders,
         "students": students, "revenue_usd": round(revenue_cents / 100, 2), "queue": running,
         "avg_treasure": avg_treasure, "avg_rating": avg_rating,
         "understanding_impact": understanding_impact}
    status = _status_from(m, running)
    if m["treasure"] > 0 and (avg_treasure or 0) >= 90 and published >= 1:
        status_badge = "Treasure Standard™"
    else:
        status_badge = status
    activated = verified > 0 or orders > 0 or published > 0
    # health: blend of published ratio, verification, treasure compliance
    health = 0
    if products:
        health += min(50, round(published / max(products, 1) * 50))
        health += min(30, round(treasure / max(products, 1) * 30))
    if verified:
        health += 20
    if not products and activated:
        health = 40
    m.update({"status": status, "status_badge": status_badge, "activated": activated,
              "health": min(100, health) if (products or activated) else 0})
    return m


def factory_defaults(college):
    name = college["name"]
    topics = SUGGESTED_TOPICS.get(name) or DIVISION_TOPICS.get(college.get("division"), ["Foundational understanding"])
    return {"category": name, "division": college.get("division"), "audience": "General Public",
            "suggested_topics": topics, "recipes": COLLEGE_RECIPES,
            "workflow_template": "Full Treasure Package™"}


async def colleges_overview(division=None):
    q = {"division": division} if division else {}
    colleges = await db.colleges.find(q).sort("name", 1).to_list(100)
    out = []
    for c in colleges:
        m = await college_metrics(c)
        out.append({"id": c["id"], "name": c["name"], "division": c.get("division"),
                    "description": c.get("description"), "color": c.get("color"),
                    "metrics": m, "status": m["status"], "status_badge": m["status_badge"],
                    "activated": m["activated"], "health": m["health"]})
    return out
