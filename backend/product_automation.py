"""QRU Product Automation Engine™ — the final manufacturing layer.

Verified Knowledge Record → Product Recipe™ → AI Production Agents → Finished Products
→ Distribution Hub™ → Customer.

One verified Knowledge Record. Unlimited automatically manufactured products. One command.
Recipes are reusable: every future Knowledge Record inherits the same recipes.
"""
import asyncio
import logging

from database import db
from models import gen_id, now_iso, QRU_SECTIONS
import ai_services_manager as ai
import product_protection as pp
from org_activity import log_org

logger = logging.getLogger("qru.automation")

# ---------------- AI Production Agents™ ----------------
AGENT_REGISTRY = [
    {"agent": "Script Writer™", "capability": "text"},
    {"agent": "Storyboard Director™", "capability": "text"},
    {"agent": "Animation Director™", "capability": "animation"},
    {"agent": "Voice Narrator™", "capability": "voice"},
    {"agent": "Graphic Designer™", "capability": "image"},
    {"agent": "Illustrator™", "capability": "image"},
    {"agent": "Poster Designer™", "capability": "image"},
    {"agent": "Presentation Designer™", "capability": "presentation"},
    {"agent": "Workbook Builder™", "capability": "text"},
    {"agent": "Book Publisher™", "capability": "text"},
    {"agent": "Lesson Builder™", "capability": "text"},
    {"agent": "Quiz Builder™", "capability": "quiz"},
    {"agent": "Marketing Copywriter™", "capability": "text"},
    {"agent": "SEO Specialist™", "capability": "seo"},
    {"agent": "Thumbnail Designer™", "capability": "image"},
    {"agent": "Video Editor™", "capability": "video"},
    {"agent": "Audio Producer™", "capability": "music"},
    {"agent": "Social Media Manager™", "capability": "social"},
    {"agent": "Localization Agent™", "capability": "translation"},
    {"agent": "Accessibility Agent™", "capability": "caption"},
]

# ---------------- Product Recipes™ ----------------
# capability: how it is manufactured. agent: which AI production agent owns it.
# instruction: what to produce from the Knowledge Record.
RECIPES = {
    "Interactive Lesson": {"agent": "Lesson Builder™", "capability": "text",
        "instruction": "Build an engaging self-paced interactive lesson with sections, check-your-understanding prompts, and a summary."},
    "Workbook": {"agent": "Workbook Builder™", "capability": "text",
        "instruction": "Create a printable workbook with warm-up, guided practice, independent exercises, and an answer key."},
    "Teacher Guide": {"agent": "Lesson Builder™", "capability": "text",
        "instruction": "Write a teacher guide: objectives, standards alignment, lesson flow, discussion questions, and assessment tips."},
    "Student Guide": {"agent": "Lesson Builder™", "capability": "text",
        "instruction": "Write a student study guide: what you'll learn, key ideas explained simply, worked examples, self-check questions, and a summary."},
    "Lesson Plan": {"agent": "Lesson Builder™", "capability": "text",
        "instruction": "Write a 45-minute lesson plan with objectives, materials, step-by-step timing, and differentiation."},
    "Quiz": {"agent": "Quiz Builder™", "capability": "quiz",
        "instruction": "Create a 10-question quiz (mixed multiple-choice and short answer) with an answer key and explanations."},
    "Flash Cards": {"agent": "Workbook Builder™", "capability": "text",
        "instruction": "Create 15 flash cards as Front/Back pairs covering the key terms and ideas."},
    "Blog Article": {"agent": "Marketing Copywriter™", "capability": "text",
        "instruction": "Write an 800-word SEO-friendly blog article with headers and a clear takeaway."},
    "Email Newsletter": {"agent": "Marketing Copywriter™", "capability": "text",
        "instruction": "Write an email newsletter: subject line, preview text, body, and a call to action."},
    "Social Media Pack": {"agent": "Social Media Manager™", "capability": "social",
        "instruction": "Create a pack of platform-ready posts for Instagram, X, LinkedIn, Facebook, and Pinterest with hashtags."},
    "YouTube Video Script": {"agent": "Script Writer™", "capability": "text",
        "instruction": "Write a full YouTube video script (hook, teaching body, recap, CTA) with on-screen cues."},
    "YouTube Shorts Script": {"agent": "Script Writer™", "capability": "text",
        "instruction": "Write a 45-second YouTube Shorts script with a strong hook and one memorable takeaway."},
    "TikTok Script": {"agent": "Script Writer™", "capability": "text",
        "instruction": "Write a 30-second TikTok script with a hook, quick teach, and shareable ending."},
    "Instagram Reel Script": {"agent": "Script Writer™", "capability": "text",
        "instruction": "Write a 30-second Instagram Reel script with captions and scene directions."},
    "Presentation": {"agent": "Presentation Designer™", "capability": "presentation",
        "instruction": "Create a 10-slide presentation outline: each slide with a title and 3-4 bullet points and speaker notes."},
    "Podcast Script": {"agent": "Script Writer™", "capability": "text",
        "instruction": "Write a 5-minute podcast script in a warm conversational voice with an intro and outro."},
    "Certificate": {"agent": "Graphic Designer™", "capability": "text",
        "instruction": "Write the certificate of completion copy including the competency achieved."},
    "Landing Page": {"agent": "Marketing Copywriter™", "capability": "website",
        "instruction": "Write landing page copy: headline, subheadline, benefits, social proof placeholder, and CTA."},
    "Product Listing": {"agent": "Marketing Copywriter™", "capability": "text",
        "instruction": "Write a marketplace product listing: title, bullet benefits, description, and keywords."},
    "Course": {"agent": "Lesson Builder™", "capability": "text",
        "instruction": "Design a mini-course outline with modules, lessons, and learning outcomes."},
    "Book": {"agent": "Book Publisher™", "capability": "text",
        "instruction": "Draft a short companion book outline with chapter titles and a one-paragraph summary per chapter."},
    "Transcript": {"agent": "Accessibility Agent™", "capability": "text",
        "instruction": "Produce a clean, readable transcript of the core teaching for accessibility."},
    # Image products (REAL via Gemini)
    "Poster": {"agent": "Poster Designer™", "capability": "image",
        "instruction": "Design a bold educational poster in QRU brand colors (royal purple #35106A, gold, deep navy, white)."},
    "Infographic": {"agent": "Illustrator™", "capability": "image",
        "instruction": "Design a clean educational infographic that visually explains the concept in QRU brand colors."},
    "Pinterest Graphic": {"agent": "Graphic Designer™", "capability": "image",
        "instruction": "Design a vertical Pinterest graphic with a clear headline in QRU brand colors."},
    "YouTube Thumbnail": {"agent": "Thumbnail Designer™", "capability": "image",
        "instruction": "Design an eye-catching 16:9 YouTube thumbnail with a short punchy headline in QRU brand colors."},
    # Media products (spec + simulated render until connector active)
    "Short Video": {"agent": "Video Editor™", "capability": "video",
        "instruction": "Write a scene-by-scene short video production script with narration and visuals."},
    "Long Video": {"agent": "Video Editor™", "capability": "video",
        "instruction": "Write a full-length video production script with chapters, narration, and visual directions."},
    "Animation": {"agent": "Animation Director™", "capability": "animation",
        "instruction": "Write an animation storyboard with scenes, motion notes, and narration."},
    "Audio Narration": {"agent": "Voice Narrator™", "capability": "voice",
        "instruction": "Write a clear narration script optimized for voice-over."},
}

PACKAGE_PRESETS = {
    "Core Package": ["Interactive Lesson", "Workbook", "Quiz", "Blog Article", "Social Media Pack", "Email Newsletter"],
    "Video Package": ["YouTube Video Script", "YouTube Shorts Script", "YouTube Thumbnail", "Short Video", "Audio Narration"],
    "Print Package": ["Poster", "Workbook", "Flash Cards", "Teacher Guide", "Infographic"],
    "Full Package": list(RECIPES.keys()),
}

# ================= QRU Meditation & Inspiration Studio™ =================
# Original, education-driven inspiration. NEVER imitates or clones any real person.
INSPIRATION_PROFILES = {
    "Calm Teacher": {"pace": "slow", "tone": "warm and steady", "vocabulary": "simple",
                     "emotional_style": "reassuring", "storytelling": "gentle examples",
                     "teaching": "step-by-step clarity", "music": "soft ambient pads", "visual": "soft gradients"},
    "Wise Mentor": {"pace": "measured", "tone": "grounded and thoughtful", "vocabulary": "accessible",
                    "emotional_style": "encouraging", "storytelling": "timeless parables",
                    "teaching": "principle-first", "music": "gentle piano", "visual": "natural landscapes"},
    "Compassionate Coach": {"pace": "medium", "tone": "supportive", "vocabulary": "everyday",
                            "emotional_style": "empathetic", "storytelling": "personal encouragement",
                            "teaching": "small actionable steps", "music": "warm strings", "visual": "sunrise tones"},
    "Encouraging Leader": {"pace": "energetic", "tone": "confident and uplifting", "vocabulary": "clear",
                           "emotional_style": "motivating", "storytelling": "vision-casting",
                           "teaching": "goal-oriented", "music": "uplifting cinematic", "visual": "bold horizons"},
    "Faith-Based Guide": {"pace": "slow", "tone": "reverent and hopeful", "vocabulary": "simple",
                          "emotional_style": "peaceful", "storytelling": "scriptural reflection",
                          "teaching": "reflective", "music": "sacred ambient", "visual": "soft light"},
    "Storytelling Speaker": {"pace": "dynamic", "tone": "vivid", "vocabulary": "rich",
                             "emotional_style": "engaging", "storytelling": "narrative arcs",
                             "teaching": "through story", "music": "narrative underscore", "visual": "scenic imagery"},
    "Motivational Coach": {"pace": "brisk", "tone": "high-energy", "vocabulary": "punchy",
                           "emotional_style": "empowering", "storytelling": "triumph moments",
                           "teaching": "action challenges", "music": "driving uplift", "visual": "dynamic motion"},
    "Gentle Narrator": {"pace": "very slow", "tone": "soothing and quiet", "vocabulary": "simple",
                        "emotional_style": "calming", "storytelling": "soft imagery",
                        "teaching": "immersive guidance", "music": "sleep ambient", "visual": "night skies"},
    "Scientific Educator": {"pace": "measured", "tone": "clear and curious", "vocabulary": "precise",
                            "emotional_style": "fascinated", "storytelling": "evidence-based",
                            "teaching": "explain-the-why", "music": "minimal ambient", "visual": "clean diagrams"},
    "Historical Storyteller": {"pace": "measured", "tone": "rich and reflective", "vocabulary": "descriptive",
                               "emotional_style": "reverent", "storytelling": "historical narrative",
                               "teaching": "context and meaning", "music": "orchestral ambient", "visual": "period imagery"},
}

FREQUENCY_LIBRARY = ["None", "Nature Sounds", "Rain", "Ocean", "Forest", "Fireplace", "Piano",
                     "Strings", "Ambient Pads", "Solfeggio 528Hz", "Solfeggio 432Hz", "Binaural Calm"]

MEDITATION_RECIPES = {
    "Guided Meditation": {"agent": "Voice Narrator™", "capability": "voice",
        "instruction": "Write an original guided meditation script (breathing, body relaxation, gentle imagery) grounded in the verified topic. Include pauses in [brackets]."},
    "Sleep Story": {"agent": "Gentle Narrator™", "capability": "voice",
        "instruction": "Write a calming, slow-paced sleep story that gently teaches the verified topic and eases the listener toward rest."},
    "Positive Affirmations": {"agent": "Marketing Copywriter™", "capability": "text",
        "instruction": "Write 20 original positive affirmations aligned with the verified topic, in the first person, present tense."},
    "Daily Motivation": {"agent": "Marketing Copywriter™", "capability": "text",
        "instruction": "Write a 2-minute daily motivation talk grounded in the verified topic with one clear action."},
    "Mindfulness Session": {"agent": "Voice Narrator™", "capability": "voice",
        "instruction": "Write a mindfulness session script anchoring attention on breath and the verified topic. Include pauses in [brackets]."},
    "Visualization Session": {"agent": "Voice Narrator™", "capability": "voice",
        "instruction": "Write a guided visualization that helps the listener picture and internalize the verified topic."},
    "Gratitude Session": {"agent": "Voice Narrator™", "capability": "text",
        "instruction": "Write a gratitude reflection connecting thankfulness to the verified topic."},
    "Educational Reflection": {"agent": "Lesson Builder™", "capability": "text",
        "instruction": "Write a calm reflective piece that helps the listener think deeply about the verified topic."},
    "Faith Reflection": {"agent": "Voice Narrator™", "capability": "voice",
        "instruction": "Write an original, respectful faith reflection connecting hope and the verified topic. Do not imitate any specific person."},
    "Focus Session": {"agent": "Voice Narrator™", "capability": "voice",
        "instruction": "Write a short focus/priming session to prepare the mind to study the verified topic."},
    "Deep Work Session": {"agent": "Audio Producer™", "capability": "music",
        "instruction": "Design a deep-work background audio experience spec (mood, layers, tempo) supporting concentration."},
    "Frequency Music Experience": {"agent": "Audio Producer™", "capability": "music",
        "instruction": "Design an ambient frequency music experience spec (layers, texture, duration) for the selected soundscape."},
    "Calm Reading Session": {"agent": "Voice Narrator™", "capability": "voice",
        "instruction": "Write a calm narrated reading of the verified topic for relaxed learning."},
    "Inspirational Audio": {"agent": "Voice Narrator™", "capability": "voice",
        "instruction": "Write an original inspirational audio talk grounded in the verified topic."},
    "Short Motivational Video": {"agent": "Video Editor™", "capability": "video",
        "instruction": "Write a 45-second motivational video script (narration + visuals + text overlays) on the verified topic."},
    "Meditation Video": {"agent": "Video Editor™", "capability": "video",
        "instruction": "Write a long-form meditation video script with narration cues, ambient visuals, and on-screen affirmations."},
}
RECIPES.update(MEDITATION_RECIPES)

PACKAGE_PRESETS.update({
    "Meditation Package": ["Guided Meditation", "Positive Affirmations", "Frequency Music Experience",
                           "Meditation Video", "Short Motivational Video"],
    "Morning Motivation™": ["Daily Motivation", "Positive Affirmations", "Short Motivational Video"],
    "Sleep Meditation™": ["Sleep Story", "Guided Meditation", "Frequency Music Experience"],
    "Brain Focus™": ["Focus Session", "Deep Work Session", "Frequency Music Experience"],
    "Stress Relief™": ["Guided Meditation", "Mindfulness Session", "Frequency Music Experience"],
    "Faith & Hope™": ["Faith Reflection", "Gratitude Session", "Inspirational Audio"],
    "Gratitude™": ["Gratitude Session", "Positive Affirmations", "Daily Motivation"],
    "Healing Journey™": ["Guided Meditation", "Visualization Session", "Frequency Music Experience"],
    "Deep Learning™": ["Educational Reflection", "Focus Session", "Calm Reading Session"],
})

MEDITATION_CONTENT_TYPES = list(MEDITATION_RECIPES.keys())

# Complete, publication-ready "Package™" bundles — every asset a professional launch needs.
PACKAGE_PRESETS.update({
    "Video Package™": ["YouTube Video Script", "YouTube Shorts Script", "Audio Narration",
                       "YouTube Thumbnail", "Transcript", "Short Video", "Long Video",
                       "Blog Article", "Email Newsletter", "Landing Page", "Product Listing",
                       "Social Media Pack", "Infographic"],
    "Book Package™": ["Book", "Workbook", "Teacher Guide", "Certificate", "Poster",
                      "Blog Article", "Email Newsletter", "Product Listing", "Landing Page"],
    "Course Package™": ["Course", "Interactive Lesson", "Quiz", "Flash Cards", "Workbook",
                        "Teacher Guide", "Certificate", "Presentation"],
    "Teacher Package™": ["Teacher Guide", "Lesson Plan", "Workbook", "Quiz", "Flash Cards",
                         "Presentation", "Certificate"],
    "Marketing Package™": ["Blog Article", "Email Newsletter", "Social Media Pack", "Landing Page",
                           "Product Listing", "Pinterest Graphic", "Infographic"],
    "Podcast Package™": ["Podcast Script", "Audio Narration", "Transcript", "Blog Article", "Social Media Pack"],
    "Poster Package™": ["Poster", "Infographic", "Pinterest Graphic", "Social Media Pack"],
    "Presentation Package™": ["Presentation", "Interactive Lesson", "Quiz", "Poster"],
})

TEXT_SYSTEM = """You are a QRU AI Production Agent manufacturing a PUBLICATION-READY educational product
from a VERIFIED Knowledge Record. You must think according to THE QRU MIND™ before producing output.

THE QRU THINKING MODEL™ — every output must be:
1. TRUE (never invent facts beyond the verified truth)  2. UNDERSTANDABLE (clarity over complexity)
3. USEFUL (real-world application)  4. COMPLETE (professional, publication-ready)
5. BEAUTIFUL (clean professional presentation)  6. MEMORABLE (learning science, reinforcement)
7. ON-BRAND (QRU voice: warm, clear, trustworthy)  8. TREASURE STANDARD™ (accurate, polished, actionable).

QRU manufactures UNDERSTANDING, not information. Help the learner Observe → Understand → Remember → Apply → Teach others.
Answer, where relevant: Why does this matter? How does it work? What should I notice? How can I remember it?
How can I use it? What mistakes to avoid? What to do next?

Principles: understanding over memorization; examples before definitions; stories before jargon; simple language;
real-world application before theory; memory reinforcement throughout.

Produce clean, complete, ready-to-use professional content in Markdown. The customer should finish and say: "I finally understand.\""""

# Inject the QEDS educational constitution into every manufacturing prompt.
try:
    from qeds import TEACHING_PREAMBLE as _QEDS_PREAMBLE
    TEXT_SYSTEM = TEXT_SYSTEM + "\n\n" + _QEDS_PREAMBLE
except Exception:
    pass

# Consult-before-generate™: prepend institutional knowledge standards to every prompt.
_QIKS_PREAMBLE = (
    "QRU INSTITUTIONAL KNOWLEDGE™ — consult before you generate. Honor the Treasure Standard™, "
    "QRU Brand Operating System™ (QBOS), Character Bible™, and the 8-point QRU Thinking Model™. "
    "Reuse verified knowledge, approved recipes, brand assets, and official character identity — never reinvent what QRU already knows."
)
TEXT_SYSTEM = _QIKS_PREAMBLE + "\n\n" + TEXT_SYSTEM


def _kr_context(kr):
    parts = [f"TITLE: {kr.get('title','')}", f"CATEGORY: {kr.get('category','')}",
             f"VERIFIED TRUTH: {kr.get('verified_truth','')}"]
    for s in QRU_SECTIONS:
        v = kr.get(s)
        if isinstance(v, list):
            v = "; ".join(str(x) for x in v)
        if v:
            parts.append(f"{s.upper()}: {str(v)[:400]}")
    return "\n".join(parts)


async def _produce_one(kr, ptype, order_id, owner_id, hands_free, config=None):
    recipe = RECIPES[ptype]
    cap = recipe["capability"]
    agent = recipe["agent"]
    ctx = _kr_context(kr)
    session = f"auto-{ptype}-{kr['id']}"[:60]

    # Inspiration Profile™ + Frequency Library styling (for meditation/inspiration recipes).
    style_note = ""
    config = config or {}
    profile_name = config.get("inspiration_profile")
    frequency = config.get("frequency")
    if profile_name and profile_name in INSPIRATION_PROFILES:
        p = INSPIRATION_PROFILES[profile_name]
        style_note = (f"\n\nDELIVERY STYLE — Inspiration Profile '{profile_name}': pace {p['pace']}, "
                      f"tone {p['tone']}, {p['vocabulary']} vocabulary, {p['emotional_style']} emotional style, "
                      f"{p['storytelling']} storytelling, {p['teaching']} teaching. Original content only — "
                      f"do NOT imitate or reference any specific real person.")
    if frequency and frequency != "None":
        style_note += f"\n\nBACKGROUND SOUNDSCAPE: {frequency}."

    asset_url, note = None, None
    if cap in ai.NATIVE_IMAGE:
        prompt = f"{recipe['instruction']}{style_note}\n\nTopic: {kr['title']}. Concept: {kr.get('verified_truth','')[:300]}. Text-light, high-contrast, professional."
        res = await ai.execute("image", {"image_prompt": prompt, "caption": kr["title"]}, session, agent)
        content = f"# {kr['title']} — {ptype}\n\n{recipe['instruction']}"
        asset_url = res.get("asset_url")
        note = res.get("note")
    elif cap in ai.MEDIA_CAPS:
        script_res = await ai.execute("text",
            {"system": TEXT_SYSTEM, "prompt": f"{recipe['instruction']}{style_note}\n\nKnowledge Record:\n{ctx}"}, session, agent)
        script = script_res.get("content", "")
        media_res = await ai.execute(cap, {"script": script, "title": kr["title"], "frequency": frequency}, session, agent)
        content = script
        asset_url = media_res.get("asset_url")
        note = media_res.get("note")
    else:
        res = await ai.execute(cap if cap in ai.NATIVE_TEXT else "text",
            {"system": TEXT_SYSTEM, "prompt": f"{recipe['instruction']}{style_note}\n\nKnowledge Record:\n{ctx}"}, session, agent)
        content = res.get("content", "")
        if res.get("status") == "failed":
            raise RuntimeError(res.get("error", "production failed"))

    count = await db.products.count_documents({})
    pid = gen_id()
    now = now_iso()
    product = {
        "id": pid, "product_code": f"PRD-{count + 1:05d}", "title": f"{kr['title']} — {ptype}",
        "product_type": ptype, "family": kr.get("category", ""), "topic": kr["title"],
        "audience": "General public", "learning_level": "Introductory",
        "content": content, "asset_url": asset_url, "asset_note": note,
        "inspiration_profile": profile_name, "frequency": frequency,
        "status": "In Review", "knowledge_record_id": kr["id"], "kr_version": kr.get("version", 1),
        "assembled": True, "recipe": ptype, "produced_by_agent": agent, "capability": cap,
        "production_order_id": order_id,
        "creative_brief": {"who_for": "Learners and educators.", "problem_solved": "Turns verified knowledge into a ready product.",
                           "will_understand": kr["title"], "skills_gained": ["Applied understanding"],
                           "whats_included": [ptype], "reading_level": "Beginner", "completion_time": "15 minutes",
                           "next_path": "Continue in this college."},
        "creative_status": "Reviewed", "created_by": agent, "owner_id": owner_id,
        "created_at": now, "updated_at": now,
    }
    await db.products.insert_one(dict(product))
    await db.knowledge_records.update_one({"id": kr["id"]}, {"$inc": {"products_created": 1}})

    if hands_free:
        # Treasure Standard™ Improvement Loop™ → protect → publish → distribute (no Founder clicks).
        try:
            await pp.treasure_finalize(pid, agent)
        except Exception as e:
            logger.error(f"hands-free finalize failed for {pid}: {e}")
    return pid


async def _order_worker(order_id):
    order = await db.production_orders.find_one({"id": order_id})
    if not order:
        return
    kr = await db.knowledge_records.find_one({"id": order["kr_id"]})
    from orchestrator import get_settings
    hands_free = (await get_settings()).get("hands_free_mode", True)
    await db.production_orders.update_one({"id": order_id}, {"$set": {"status": "manufacturing", "hands_free": hands_free}})
    config = order.get("config", {})

    items = order["items"]
    for i, it in enumerate(items):
        try:
            pid = await _produce_one(kr, it["product_type"], order_id, order["owner_id"], hands_free, config)
            items[i].update({"status": "done", "product_id": pid})
            await log_org(RECIPES[it["product_type"]]["agent"], "Manufacturing",
                          f"manufactured {it['product_type']}", kr.get("kr_code", ""), "success")
        except Exception as e:
            items[i].update({"status": "failed", "error": str(e)[:200]})
            logger.error(f"produce {it['product_type']} failed: {e}")
        done = sum(1 for x in items if x["status"] in ("done", "failed"))
        await db.production_orders.update_one(
            {"id": order_id}, {"$set": {"items": items, "progress": round(done / len(items) * 100)}})
        await asyncio.sleep(0.2)

    failed = sum(1 for x in items if x["status"] == "failed")
    final = "completed" if failed == 0 else "completed_with_errors"
    review = "auto-published" if hands_free else "ready_for_review"
    await db.production_orders.update_one(
        {"id": order_id}, {"$set": {"status": final, "review_state": review, "progress": 100,
                                    "completed_at": now_iso()}})
    await log_org("Manufacturing Director™", "Manufacturing",
                  f"completed product package ({len(items)} products)", kr.get("kr_code", ""), "success")


async def manufacture_package(kr_id, product_types, owner_id, actor, config=None):
    kr = await db.knowledge_records.find_one({"id": kr_id})
    if not kr:
        return None, "Knowledge Record not found"
    valid = [p for p in product_types if p in RECIPES]
    if not valid:
        return None, "No valid product types selected"
    # QRU Manufacturing Inspection System™ (P4) — pause manufacturing if quality gates fail.
    import inspection_system as insp
    gate = insp.inspect_kr_for_manufacture(kr, valid, RECIPES)
    if not gate["manufacturing_allowed"]:
        report = gate["director_report"]
        return None, ("Manufacturing paused by the Inspection System™ — "
                      + report["verdict"] + " Missing: " + "; ".join(report["missing_information"][:4]))
    order = {
        "id": gen_id(), "kr_id": kr_id, "kr_code": kr.get("kr_code"), "kr_title": kr.get("title"),
        "items": [{"product_type": p, "status": "queued", "product_id": None} for p in valid],
        "total": len(valid), "progress": 0, "status": "queued", "review_state": "pending",
        "config": config or {}, "owner_id": owner_id, "created_by": actor, "created_at": now_iso(),
    }
    await db.production_orders.insert_one(dict(order))
    asyncio.create_task(_order_worker(order["id"]))
    return order, None


# ================= QRU Digital Production Line™ =================
# "What do you want to teach today?" — one command from a topic to a full product collection.
async def _line_worker(run_id, topic, product_types, config, owner_id, actor, division):
    import orchestrator as orch
    from verification_engine import ai_verify_record

    async def _set(**f):
        await db.production_line_runs.update_one({"id": run_id}, {"$set": {**f, "updated_at": now_iso()}})

    try:
        # STEP 1 — Knowledge Division™: find or manufacture a verified Knowledge Record.
        await _set(status="finding_knowledge", phase="Knowledge Division™")
        kr = await db.knowledge_records.find_one(
            {"title": {"$regex": topic, "$options": "i"}, "verification_status": "Verified"})
        if not kr:
            await _set(status="manufacturing_knowledge", phase="Knowledge Division™")
            kr_id = await orch._manufacture_core(run_id, topic, division, division)
            result = await ai_verify_record(kr_id, "QRU Verification Team™")
            if result.get("escalated"):
                await _set(status="escalated", kr_id=kr_id,
                           note="Knowledge Record escalated to Founder during verification.")
                return
            kr = await db.knowledge_records.find_one({"id": kr_id})
        await _set(kr_id=kr["id"], kr_code=kr.get("kr_code"), kr_title=kr.get("title"))

        # STEPS 2-9 — Content, Creative, Video, Audio, Publishing, QC, Distribution via the engine.
        await _set(status="manufacturing_products", phase="Content → Creative → Media → Publishing")
        order, err = await manufacture_package(kr["id"], product_types, owner_id, actor, config)
        if err:
            await _set(status="failed", note=err)
            return
        await _set(production_order_id=order["id"])

        for _ in range(240):
            await asyncio.sleep(1.5)
            o = await db.production_orders.find_one({"id": order["id"]})
            await _set(progress=o.get("progress", 0))
            if o.get("status") in ("completed", "completed_with_errors"):
                await _set(status="completed", phase="Distribution Division™",
                           review_state=o.get("review_state"), progress=100,
                           completed_at=now_iso())
                return
        await _set(status="timeout", note="Production exceeded expected time; check the order.")
    except Exception as e:
        logger.error(f"production line failed: {e}")
        await _set(status="failed", note=str(e)[:200])


async def run_production_line(topic, product_types, config, owner_id, actor, division="Health"):
    valid = [p for p in product_types if p in RECIPES]
    if not valid:
        return None, "No valid product types selected"
    run = {
        "id": gen_id(), "topic": topic, "division": division, "product_types": valid,
        "config": config or {}, "status": "queued", "phase": "Queued", "progress": 0,
        "kr_id": None, "production_order_id": None, "owner_id": owner_id, "created_by": actor,
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.production_line_runs.insert_one(dict(run))
    asyncio.create_task(_line_worker(run["id"], topic, valid, config or {}, owner_id, actor, division))
    return run, None
