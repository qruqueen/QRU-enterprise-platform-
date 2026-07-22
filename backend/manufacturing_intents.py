"""QRU Manufacturing Intent™ — lightweight presets that map a Founder's intent to a product-family
bundle + audience + publishing profile. Configuration, not code: each Intent simply pre-selects the
families to assemble from one Verified source. The Founder always confirms before manufacturing.
"""

# family names must exist in decoder_engine.available_product_types()
INTENTS = {
    "consumer": {
        "id": "consumer", "label": "Consumer", "audience": "General reader",
        "description": "A trade edition for the general public.",
        "families": ["Book"],
        "publishing_profile": "book",
    },
    "classroom": {
        "id": "classroom", "label": "Classroom", "audience": "Teachers & students",
        "description": "A teaching bundle for a school classroom.",
        "families": ["Book", "Workbook", "Teacher Guide"],
        "publishing_profile": "publication",
    },
    "homeschool": {
        "id": "homeschool", "label": "Homeschool", "audience": "Parents & learners at home",
        "description": "A parent-led learning bundle for the home.",
        "families": ["Book", "Workbook", "Family Guide"],
        "publishing_profile": "publication",
    },
    "professional": {
        "id": "professional", "label": "Professional", "audience": "Working professionals",
        "description": "A practical reference + workbook for self-directed professionals.",
        "families": ["Book", "Workbook"],
        "publishing_profile": "publication",
    },
    "corporate": {
        "id": "corporate", "label": "Corporate / Training", "audience": "Corporate learners",
        "description": "A training bundle for organizational learning & development.",
        "families": ["Book", "Workbook", "Teacher Guide", "Quick Card"],
        "publishing_profile": "publication",
    },
    "exam_prep": {
        "id": "exam_prep", "label": "Exam Prep", "audience": "Test candidates",
        "description": "A study bundle focused on assessment readiness.",
        "families": ["Book", "Workbook", "Quiz", "Flash Cards"],
        "publishing_profile": "publication",
    },
}


def list_intents():
    return list(INTENTS.values())


def get_intent(intent_id):
    return INTENTS.get((intent_id or "").lower())
