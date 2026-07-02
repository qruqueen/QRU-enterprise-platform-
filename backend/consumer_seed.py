"""Demo seed for the QRU Consumer Learning Platform.

Populates a few verified Knowledge Master Records™ with the full QRU educational
structure and publishes matching Finished QRU Products™ so Consumer Mode has a
real, browsable experience. All records/products are stamped is_demo=True.
"""
from database import db
from models import gen_id, now_iso

DEMO = [
    {
        "title": "How the Human Heart Pumps Blood",
        "category": "Heart Health",
        "verified_truth": "The heart is a muscular pump that circulates ~2,000 gallons of blood daily through a closed vascular system, powered by coordinated electrical signals.",
        "the_question": "How does the heart keep blood moving through my entire body every second of my life?",
        "simple_answer": "Your heart is a muscular pump that squeezes about 100,000 times a day to push blood — carrying oxygen and nutrients — to every cell in your body.",
        "why_it_matters": "Understanding your heart helps you protect it. Small daily habits — movement, sleep, and good food — directly change how well this pump serves you for decades.",
        "qru_translation": "Think of your heart as a two-story house with four rooms. The top rooms collect blood; the bottom rooms forcefully pump it out. Valves act like one-way doors so blood never flows backward. An electrical spark keeps the rhythm steady.",
        "step_by_step": [
            "Blood returning from the body enters the right atrium.",
            "It drops into the right ventricle, which pumps it to the lungs to pick up oxygen.",
            "Oxygen-rich blood returns to the left atrium.",
            "The powerful left ventricle pushes it out to the whole body.",
        ],
        "professional_version": "The myocardium contracts in response to depolarization initiated at the sinoatrial node, propagating through the AV node and His-Purkinje system. Stroke volume and heart rate determine cardiac output (CO = SV × HR), regulated by preload, afterload, and contractility.",
        "real_world_example": "When you climb stairs and feel your heart speed up, that's your heart increasing output to deliver more oxygen to your working leg muscles — exactly as designed.",
        "deep_roots": "The heart's four-chambered design evolved to separate oxygen-poor and oxygen-rich blood, dramatically increasing the efficiency of oxygen delivery. This separation is what allows warm-blooded, high-energy life.",
        "memory_sentence": "My heart is a lifelong pump — I protect it with movement, rest, and good fuel.",
        "everyday_analogy": "Your heart is like a dependable water pump in a house, quietly sending fresh water to every faucet, day and night.",
        "children_version": "Your heart is a strong little muscle in your chest. It squeezes like a fist — squeeze, rest, squeeze, rest — to send blood all around your body so you can run and play!",
        "student_version": "The heart has four chambers and four valves. The right side sends blood to the lungs for oxygen; the left side pumps oxygen-rich blood to the body. Its steady beat is set by natural electrical pacemaker cells.",
        "story_version": "Every second, a quiet drummer keeps time inside your chest. It never asks for applause. From your first day to your last, it beats — carrying life to every corner of you.",
        "vocabulary_decoder": [
            {"term": "Atrium", "definition": "An upper chamber of the heart that receives blood."},
            {"term": "Ventricle", "definition": "A lower chamber that pumps blood out of the heart."},
            {"term": "Cardiac output", "definition": "The amount of blood the heart pumps each minute."},
        ],
        "common_misconceptions": [
            "The heart is on the far left — it's actually near the center, tilted slightly left.",
            "A fast heartbeat always means something is wrong — it's often a healthy response to activity.",
        ],
        "practice_application": [
            "Take a 10-minute brisk walk and notice your heart rate rise and recover.",
            "Check your resting pulse for 15 seconds, then multiply by 4.",
        ],
        "conversation_starter": "If your heart beats 100,000 times a day without you thinking about it, what else in your body is quietly working for you right now?",
        "cheat_sheet": "- 4 chambers: 2 atria (collect), 2 ventricles (pump)\n- Right side → lungs; Left side → body\n- Valves prevent backflow\n- Pacemaker cells set the rhythm",
        "call_to_action": "Next, explore how your blood carries oxygen — visit the Lung Health pathway.",
        "references": ["American Heart Association — How the Heart Works", "Guyton and Hall Textbook of Medical Physiology"],
        "sources": ["AHA", "NIH National Heart, Lung, and Blood Institute"],
        "confidence": 96,
    },
    {
        "title": "Why Sleep Strengthens Memory",
        "category": "Brain Health",
        "verified_truth": "During deep and REM sleep, the brain replays and consolidates newly formed memories, strengthening the synaptic connections essential for learning.",
        "the_question": "Why do I remember things better after a good night's sleep?",
        "simple_answer": "While you sleep, your brain replays what you learned and moves it into long-term storage — sleep is when learning gets locked in.",
        "why_it_matters": "If you want to remember what you study, learn, or practice, sleep isn't optional — it's part of the learning itself. Protecting sleep protects your mind.",
        "qru_translation": "Imagine your day fills a messy desk with notes. During sleep, a diligent librarian files the important notes into the right drawers and clears the clutter — so tomorrow you can find what matters.",
        "step_by_step": [
            "During the day, new experiences form fragile memory traces.",
            "In deep sleep, the brain replays these traces.",
            "Replaying strengthens the connections between neurons.",
            "Memories move from temporary to durable storage.",
        ],
        "professional_version": "Hippocampal-neocortical dialogue during slow-wave sleep drives systems consolidation. Sharp-wave ripples coordinate with thalamocortical spindles and slow oscillations to transfer memory representations to neocortical stores.",
        "real_world_example": "Students who sleep after studying recall more than those who pull an all-nighter — even when total study time is equal.",
        "deep_roots": "Memory consolidation during sleep is conserved across many species, suggesting it is a fundamental feature of how nervous systems learn efficiently without needing to experience everything repeatedly while awake.",
        "memory_sentence": "Sleep is not lost time — it's when learning becomes permanent.",
        "everyday_analogy": "Sleep is like saving a document. Learn all day, but if you never save, tomorrow it may be gone.",
        "children_version": "When you sleep, your brain is like a tidy helper putting away everything you learned that day so you remember it tomorrow. That's why sleep makes you smarter!",
        "student_version": "Deep (slow-wave) sleep consolidates facts, while REM sleep supports skills and emotional memory. Sleeping soon after studying improves recall more than cramming without rest.",
        "story_version": "Each night, while the world goes quiet, a patient keeper walks the halls of your mind, gathering the day's discoveries and setting them safely in place for morning.",
        "vocabulary_decoder": [
            {"term": "Consolidation", "definition": "The process of making a memory stable and long-lasting."},
            {"term": "REM sleep", "definition": "A sleep stage with vivid dreams, important for skills and emotion."},
        ],
        "common_misconceptions": [
            "You can 'catch up' fully on lost sleep — some learning benefits can't be recovered.",
            "More study always beats sleep — sleep is part of effective study.",
        ],
        "practice_application": [
            "Review key material right before sleep, then sleep a full night.",
            "Protect a consistent bedtime for one week and notice recall.",
        ],
        "conversation_starter": "If your brain does its best filing while you sleep, how might a rushed, sleepless week be quietly costing you?",
        "cheat_sheet": "- Deep sleep → facts\n- REM sleep → skills & emotion\n- Sleep soon after learning\n- Consistency beats cramming",
        "call_to_action": "Next, discover how daily habits shape long-term brain health.",
        "references": ["Walker, M. — Why We Sleep", "Diekelmann & Born (2010), Nature Reviews Neuroscience"],
        "sources": ["NIH", "Nature Reviews Neuroscience"],
        "confidence": 94,
    },
    {
        "title": "How Insulin Controls Blood Sugar",
        "category": "Metabolic Health",
        "verified_truth": "Insulin, produced by pancreatic beta cells, enables cells to absorb glucose from the bloodstream, maintaining stable blood sugar levels.",
        "the_question": "How does my body keep blood sugar steady after I eat?",
        "simple_answer": "After you eat, your pancreas releases insulin — a key that unlocks your cells so they can take in sugar for energy, keeping blood sugar balanced.",
        "why_it_matters": "Understanding insulin helps you understand energy, cravings, and conditions like diabetes — and why balanced meals and movement keep this system working smoothly.",
        "qru_translation": "Picture glucose as delivery trucks of energy in your blood. Insulin is the doorman who opens the loading docks on each cell so the energy can be unloaded and used — instead of piling up in the street.",
        "step_by_step": [
            "You eat, and glucose enters the bloodstream.",
            "Rising glucose signals the pancreas to release insulin.",
            "Insulin binds to cells and opens glucose channels.",
            "Cells absorb glucose; blood sugar returns to normal.",
        ],
        "professional_version": "Insulin binds the insulin receptor tyrosine kinase, triggering GLUT4 translocation in muscle and adipose tissue. It promotes glycogenesis and lipogenesis while suppressing hepatic gluconeogenesis, maintaining euglycemia.",
        "real_world_example": "After a large meal, a healthy body's blood sugar rises then settles within a couple of hours — that smooth curve is insulin doing its job.",
        "deep_roots": "Insulin is an ancient hormone found across the animal kingdom, reflecting how central stable energy management is to complex life. Its dysregulation underlies much of modern metabolic disease.",
        "memory_sentence": "Insulin is the key that lets my cells use the energy from my food.",
        "everyday_analogy": "Insulin is like a doorman opening cell doors so sugar 'guests' can come inside and be put to work.",
        "children_version": "When you eat, sugar goes into your blood. Insulin is a helper that opens tiny doors so your body can use the sugar for energy to run and jump!",
        "student_version": "Beta cells in the pancreas release insulin when blood glucose rises. Insulin enables glucose uptake (especially in muscle and fat via GLUT4) and storage as glycogen, lowering blood sugar.",
        "story_version": "Every meal sends a wave of energy into your blood. A quiet gatekeeper answers, opening doors across your body so the energy finds its purpose instead of wandering.",
        "vocabulary_decoder": [
            {"term": "Glucose", "definition": "A simple sugar your body uses for energy."},
            {"term": "Pancreas", "definition": "An organ that makes insulin and digestive enzymes."},
            {"term": "Insulin resistance", "definition": "When cells respond poorly to insulin, raising blood sugar."},
        ],
        "common_misconceptions": [
            "Only sugar raises blood glucose — refined carbs do too.",
            "Insulin is only relevant to people with diabetes — everyone relies on it constantly.",
        ],
        "practice_application": [
            "Pair carbohydrates with protein or fiber to steady your energy.",
            "Take a short walk after a meal and notice steadier energy.",
        ],
        "conversation_starter": "If insulin quietly balances your energy after every meal, how might your food choices make its job easier or harder?",
        "cheat_sheet": "- Eat → glucose rises\n- Pancreas releases insulin\n- Cells absorb glucose\n- Blood sugar stabilizes",
        "call_to_action": "Next, explore how movement improves insulin sensitivity.",
        "references": ["ADA — Insulin Basics", "Guyton and Hall Textbook of Medical Physiology"],
        "sources": ["American Diabetes Association", "NIH"],
        "confidence": 95,
    },
]

METHOD_FIELDS = [
    "the_question", "simple_answer", "why_it_matters", "qru_translation", "step_by_step",
    "professional_version", "real_world_example", "deep_roots", "memory_sentence",
    "everyday_analogy", "children_version", "student_version", "story_version",
    "vocabulary_decoder", "common_misconceptions", "practice_application",
    "conversation_starter", "cheat_sheet", "call_to_action",
]


async def seed_consumer_demo():
    if await db.products.count_documents({"is_demo": True}) > 0:
        return
    kr_count = await db.knowledge_records.count_documents({})
    prod_count = await db.products.count_documents({})
    for i, d in enumerate(DEMO):
        kr_id = gen_id()
        section_status = {f: "Verified" for f in METHOD_FIELDS}
        kr = {
            "id": kr_id, "kr_code": f"KR-DEMO-{i + 1:03d}", "title": d["title"], "subtitle": "",
            "category": d["category"], "division": "Health", "verified_truth": d["verified_truth"],
            "confidence_score": d["confidence"], "verification_status": "Verified",
            "approval_status": "Approved", "reviewer": "Kingdom Lion™",
            "verification": {"reviewer": "Kingdom Lion™", "reviewed_at": now_iso(),
                             "evidence": "Reviewed against authoritative medical and scientific sources.",
                             "confidence_score": d["confidence"], "decision": "approve"},
            "section_status": section_status, "understanding_status": "Verified",
            "is_master_file": True, "treasure_standard": True, "products_created": 1,
            "version": 1, "created_by": "QRU Administrator", "is_demo": True,
            "created_at": now_iso(), "updated_at": now_iso(),
        }
        for f in METHOD_FIELDS:
            kr[f] = d.get(f)
        kr["references"] = d.get("references", [])
        kr["sources"] = d.get("sources", [])
        kr["key_vocabulary"] = d.get("vocabulary_decoder", [])
        await db.knowledge_records.insert_one(dict(kr))

        prod = {
            "id": gen_id(), "product_code": f"PRD-DEMO-{prod_count + i + 1:03d}",
            "title": d["title"], "product_type": "Interactive Lesson",
            "family": d["category"], "topic": d["title"], "audience": "General public",
            "learning_level": "Introductory",
            "content": f"# {d['title']}\n\n{d['qru_translation']}",
            "status": "Published", "knowledge_record_id": kr_id, "kr_version": 1,
            "assembled": True, "is_demo": True, "treasure_standard": True,
            "creative_status": "Reviewed",
            "creative_brief": {
                "who_for": "Anyone curious to truly understand this topic.",
                "problem_solved": "Replaces confusing jargon with clear, verified understanding.",
                "will_understand": f"You will understand {d['title'].lower()} and why it matters to your life.",
                "skills_gained": ["Clear mental model", "Everyday application", "Confident conversation"],
                "whats_included": ["Layered understanding", "Everyday analogy", "Quick action steps", "Cheat sheet"],
                "reading_level": "Beginner", "completion_time": "15 minutes",
                "next_path": d.get("call_to_action", ""),
            },
            "created_by": "QRU Administrator", "created_at": now_iso(), "updated_at": now_iso(),
        }
        await db.products.insert_one(dict(prod))
