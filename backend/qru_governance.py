"""QRU Character-First Architecture™ & Executive Board™ — permanent governance data.

Persists the QRU Executive Board™, Character Constitution™, Growth System™, Visual DNA™,
Trend Intelligence Division™ structure, and the governance standards as foundational,
idempotently-seeded records in the QRU operating system. Read-only reference data.
"""
from database import db

GROWTH_STAGES = [
    {"stage": 1, "name": "Explorer™", "purpose": "Ignite curiosity."},
    {"stage": 2, "name": "Learner™", "purpose": "Build understanding."},
    {"stage": 3, "name": "Professional™", "purpose": "Apply knowledge."},
    {"stage": 4, "name": "Legacy™", "purpose": "Teach others and build future generations."},
]

EXECUTIVE_BOARD = [
    {
        "id": "kingdom-lion", "name": "Kingdom Lion™", "glyph": "🦁",
        "title": "Chief Verification Officer™", "department": "Verification & Evidence",
        "mission": "Protect truth through evidence and verification.",
        "catchphrase": "Let's check before we believe.",
        "personality": ["Principled", "Protective", "Rigorous", "Fair"],
        "teaching_style": "Socratic — asks for evidence before conclusions.",
        "decision_authority": "Final authority on verification and truth standards.",
        "signature_colors": ["#F5B21A", "#35106A"], "signature_symbols": ["Crown", "Shield", "Mane crest"],
        "attire": "Regal verification robes with the QRU shield.",
        "visual_dna": "Bold golden mane silhouette, steady confident posture, shield emblem.",
        "communication_style": "Measured, authoritative, reassuring.",
        "broadcast_role": "Leads the Verification Review segment.",
    },
    {
        "id": "legacy-eagle", "name": "Legacy Eagle™", "glyph": "🦅",
        "title": "Chief Strategic Intelligence Officer™", "department": "Strategy & Enterprise Planning",
        "mission": "Long-term vision, strategy, and enterprise planning.",
        "catchphrase": "Look higher. Look wider.",
        "personality": ["Visionary", "Far-sighted", "Decisive", "Calm"],
        "teaching_style": "Big-picture framing then zoom to specifics.",
        "decision_authority": "Sets long-term strategic direction.",
        "signature_colors": ["#221A42", "#5BA3D0"], "signature_symbols": ["Spread wings", "Compass", "Horizon"],
        "attire": "Executive strategist attire with a compass emblem.",
        "visual_dna": "Sharp wing silhouette, keen focused eyes, elevated stance.",
        "communication_style": "Concise, forward-looking, strategic.",
        "broadcast_role": "Delivers Strategic Outlook.",
    },
    {
        "id": "legacy-bear", "name": "Legacy Bear™", "glyph": "🐻",
        "title": "Chief Learning Officer™", "department": "Learning & Understanding",
        "mission": "Translate complexity into understanding.",
        "catchphrase": "Understanding beats memorizing.",
        "personality": ["Warm", "Patient", "Wise", "Encouraging"],
        "teaching_style": "Conversation-first — teach before defining.",
        "decision_authority": "Owns educational clarity and the Guided Understanding System™.",
        "signature_colors": ["#8B5A2B", "#F5B21A"], "signature_symbols": ["Open book", "Warm paw", "Lantern"],
        "attire": "Professorial cardigan with a book emblem.",
        "visual_dna": "Rounded friendly silhouette, kind eyes, gentle posture.",
        "communication_style": "Warm, plain-language, analogy-rich.",
        "broadcast_role": "Hosts Educational Opportunity Analysis.",
    },
    {
        "id": "queen-unity", "name": "Queen Unity™", "glyph": "👑",
        "title": "Chief Community Officer™", "department": "Community & Belonging",
        "mission": "Represent multiple perspectives, unity, empathy, collaboration, and belonging.",
        "catchphrase": "Every voice matters. Together we grow.",
        "personality": ["Empathetic", "Inclusive", "Diplomatic", "Uplifting"],
        "teaching_style": "Perspective-taking and collaborative dialogue.",
        "decision_authority": "Represents community, empathy, and belonging standards.",
        "signature_colors": ["#7A3FB0", "#E86A9A"], "signature_symbols": ["Crown", "Signature glasses", "Joined hands"],
        "attire": "Regal community attire with evolving signature glasses.",
        "visual_dna": "Crowned silhouette with signature glasses that evolve by stage.",
        "communication_style": "Warm, inclusive, empowering.",
        "broadcast_role": "Leads Mission Alignment & community voice.",
        "glasses_evolution": [
            {"stage": "Explorer™", "glasses": "Round Glasses", "meaning": "I am learning to see the world and everyone in it."},
            {"stage": "Learner™", "glasses": "Sparkle Cat-Eye Glasses", "meaning": "I am learning to see others with kindness, empathy, and confidence."},
            {"stage": "Professional™", "glasses": "Winged Glasses", "meaning": "I lead with vision, understanding, and the ability to connect perspectives."},
            {"stage": "Legacy™", "glasses": "Royal Winged Glasses", "meaning": "My vision now inspires future generations. I help others see farther than I ever could alone."},
        ],
    },
    {
        "id": "royal-phoenix", "name": "Royal Phoenix™", "glyph": "🔥",
        "title": "Chief Innovation Officer™", "department": "Innovation & Continuous Improvement",
        "mission": "Growth, innovation, adaptation, and continuous improvement.",
        "catchphrase": "Rise, adapt, and become better than before.",
        "personality": ["Bold", "Adaptive", "Resilient", "Inspiring"],
        "teaching_style": "Iterate, learn from failure, improve continuously.",
        "decision_authority": "Drives innovation and continuous improvement.",
        "signature_colors": ["#E8531A", "#F5B21A"], "signature_symbols": ["Flame crest", "Rising wings", "Ember"],
        "attire": "Innovator's regalia with a flame crest.",
        "visual_dna": "Dynamic rising silhouette, radiant plumage, upward motion.",
        "communication_style": "Energizing, optimistic, momentum-building.",
        "broadcast_role": "Presents Innovation & Continuous Improvement.",
    },
    {
        "id": "trend-fox", "name": "Trend Fox™", "glyph": "🦊",
        "title": "Chief Trend Intelligence Officer™", "department": "Trend Intelligence Division",
        "mission": "Discover emerging trends, identify educational opportunities, monitor public curiosity, and present QRU Trend Intelligence Reports in a professional news-anchor style.",
        "catchphrase": "Something is changing… let's find it before everyone else does.",
        "personality": ["Curious", "Observant", "Investigative", "Adaptable", "Energetic"],
        "teaching_style": "Investigative journalism — evidence-led discovery.",
        "decision_authority": "Executive leader and primary news anchor of Trend Intelligence.",
        "signature_colors": ["#E8531A", "#1F8A8A"], "signature_symbols": ["News mic", "Magnifier", "Radar"],
        "attire": "News-anchor blazer with a QRU press badge.",
        "visual_dna": "Alert fox silhouette, bright investigative eyes, mic in hand.",
        "communication_style": "Broadcast news-anchor cadence.",
        "broadcast_role": "Anchors the QRU Trend Intelligence Report™.",
    },
    {
        "id": "master-beaver", "name": "Master Beaver™", "glyph": "🦫",
        "title": "Chief Manufacturing Officer™", "department": "Manufacturing",
        "mission": "Transform approved intelligence into finished educational products through disciplined manufacturing.",
        "catchphrase": "Ideas become legacy only when they're built.",
        "personality": ["Organized", "Methodical", "Dependable", "Craftsmanship-focused"],
        "teaching_style": "Show the craft, step by step, to a finished product.",
        "decision_authority": "Owns manufacturing recipes, quality, and production.",
        "signature_colors": ["#6B4A2B", "#3E7A4E"], "signature_symbols": ["Hard hat", "Blueprint", "Toolbelt"],
        "attire": "Master craftsman's workwear with a blueprint emblem.",
        "visual_dna": "Sturdy grounded silhouette, focused eyes, tools ready.",
        "communication_style": "Practical, precise, dependable.",
        "broadcast_role": "Issues and tracks Manufacturing Orders.",
    },
]

TREND_DIVISION_ROLES = [
    "Trend Discovery Director™", "Search Intelligence Analyst™", "Social Listening Analyst™",
    "Consumer Needs Analyst™", "Marketplace Intelligence Analyst™", "Education Gap Analyst™",
    "Competitive Intelligence Analyst™", "Timing & Momentum Analyst™", "Mission Alignment Director™",
    "Verification & Evidence Director™", "Opportunity Prioritization Director™",
]

TREND_REPORT_STRUCTURE = [
    "Opening Broadcast", "Top Trend Stories", "Verification Review", "Educational Opportunity Analysis",
    "Mission Alignment", "Executive Recommendation", "Manufacturing Orders", "Closing Remarks",
]

GOVERNANCE_STANDARDS = [
    {"n": 1, "title": "QRU Character-First Architecture™",
     "summary": "QRU is an educational enterprise whose departments are represented by consistent executive characters — educational guides, not mascots. All character knowledge remains subject to QRU Verification & Evidence Standards™."},
    {"n": 2, "title": "QRU Executive Board™",
     "summary": "Seven permanent executives lead the enterprise: Kingdom Lion™, Legacy Eagle™, Legacy Bear™, Queen Unity™, Royal Phoenix™, Trend Fox™, and Master Beaver™."},
    {"n": 3, "title": "QRU Character Constitution™",
     "summary": "Every character carries permanent attributes: mission, department, title, personality, catchphrase, teaching style, decision authority, signature colors & symbols, attire, visual DNA, growth stages, communication style, and broadcast role."},
    {"n": 4, "title": "QRU Character Growth System™",
     "summary": "Understanding is a journey, not just a grade level. Every core character exists in four stages: Explorer™ → Learner™ → Professional™ → Legacy™, preserving identity while maturing."},
    {"n": 5, "title": "QRU Character Continuity Standard™",
     "summary": "Across life stages, preserve identity, personality, values, signature colors, crest, catchphrase, department, and symbolism. Evolve only age, attire, communication depth, leadership, complexity, and accessories."},
    {"n": 6, "title": "QRU Visual DNA™",
     "summary": "Each character has proprietary, instantly recognizable design language (silhouette, facial proportions, eyes, emblem, accessories, wardrobe, posture, palette) — recognizable without a name."},
    {"n": 7, "title": "Queen Unity™ Visual Evolution Standard™",
     "summary": "Queen Unity's glasses are permanent storytelling devices symbolizing expanding perspective: Round → Sparkle Cat-Eye → Winged → Royal Winged glasses across the four stages."},
    {"n": 8, "title": "QRU Character Selection Standard™",
     "summary": "Characters are never random. Each must naturally represent its department through symbolism, personality, communication, and visual identity — creating enduring intellectual property."},
    {"n": 9, "title": "QRU Trend Intelligence Division™",
     "summary": "A permanent division led by Trend Fox™ with 11 analyst/director roles, delivering professional Trend Intelligence Reports."},
    {"n": 10, "title": "QRU Trend Intelligence Report™",
     "summary": "Every report follows a fixed 8-part broadcast structure and always ends with Manufacturing Orders authorizing production."},
    {"n": 11, "title": "QRU Manufacturing Standard™",
     "summary": "No intelligence report ends without action. Every approved opportunity generates a Manufacturing Order with assigned executive, departments, deliverables, verification status, production status, and QC requirements."},
    {"n": 12, "title": "QRU Brand Philosophy™",
     "summary": "QRU builds a recognizable educational universe of trusted characters guiding learners through every stage — world-class IP consistent across books, courses, software, games, videos, AI, merchandise, and licensing. Understanding is a journey, not just a grade level."},
]


async def seed_governance():
    for c in EXECUTIVE_BOARD:
        doc = {**c, "growth_stages": GROWTH_STAGES}
        await db.qru_characters.update_one({"id": c["id"]}, {"$set": doc}, upsert=True)
    await db.qru_governance.update_one({"id": "master"}, {"$set": {
        "id": "master", "standards": GOVERNANCE_STANDARDS,
        "growth_stages": GROWTH_STAGES,
        "trend_division_roles": TREND_DIVISION_ROLES,
        "trend_report_structure": TREND_REPORT_STRUCTURE,
        "principle": "Understanding is a journey, not just a grade level.",
    }}, upsert=True)


async def get_board():
    docs = await db.qru_characters.find({}).to_list(50)
    for d in docs:
        d.pop("_id", None)
    order = {c["id"]: i for i, c in enumerate(EXECUTIVE_BOARD)}
    docs.sort(key=lambda d: order.get(d["id"], 99))
    return docs


async def get_governance():
    doc = await db.qru_governance.find_one({"id": "master"})
    if doc:
        doc.pop("_id", None)
    return doc or {}
