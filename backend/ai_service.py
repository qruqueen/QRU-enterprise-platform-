import os
import json
import logging
from fastapi import HTTPException
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger("qru.ai")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
MODEL = ("openai", "gpt-5.5")
IMAGE_MODEL = "gemini-3.1-flash-image-preview"


async def generate_image(prompt: str, session_id: str):
    """Generate a branded image via Gemini Nano Banana (Emergent key). Returns raw PNG bytes or None."""
    import base64
    import asyncio
    for attempt in range(3):
        try:
            chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=session_id,
                           system_message="You are QRU Creative Studio, a premium educational brand designer.")
            chat.with_model("gemini", IMAGE_MODEL).with_params(modalities=["image", "text"])
            _, images = await chat.send_message_multimodal_response(UserMessage(text=prompt))
            if images:
                return base64.b64decode(images[0]["data"])
        except Exception as e:
            if "Budget has been exceeded" in str(e) or "spend limit" in str(e).lower():
                logger.error(f"image generation failed (limit): {e}")
                return None
            logger.warning(f"image attempt {attempt+1} failed: {str(e)[:100]}")
            await asyncio.sleep(2 * (attempt + 1))
    return None


async def llm_generate(system: str, prompt: str, session_id: str) -> str:
    import asyncio
    last_err = None
    for attempt in range(3):
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=session_id,
                system_message=system,
            ).with_model(*MODEL)
            resp = await chat.send_message(UserMessage(text=prompt))
            return resp if isinstance(resp, str) else str(resp)
        except Exception as e:
            last_err = e
            # Hard spend limits are not transient — fail fast, do not retry.
            if "Budget has been exceeded" in str(e) or "spend limit" in str(e).lower():
                break
            logger.warning(f"LLM attempt {attempt+1} failed (transient?): {str(e)[:100]}")
            await asyncio.sleep(2 * (attempt + 1))
    logger.error(f"LLM generation failed: {last_err}")
    raise HTTPException(
        status_code=503,
        detail="The AI service is temporarily unavailable. Please try again in a moment.",
    )


def parse_json(text: str):
    """Best-effort JSON extraction from an LLM response."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if "```" in t[3:] else t
        t = t.replace("json", "", 1).strip("`\n ")
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1:
        t = t[start:end + 1]
    try:
        return json.loads(t)
    except Exception:
        return None


COMMAND_SYSTEM = """You are the QRU Command Center — the conversational operating layer for QRU Factory (Quest for Real Understanding).
QRU manufactures understanding from verified knowledge. It does not simplify the truth; it simplifies the path to understanding the truth.

The Executive issues natural-language commands to run the enterprise. Interpret each command and respond ONLY with a JSON object:
{
  "reply": "<concise, professional confirmation or answer for the executive>",
  "action": "<one of: none, create_knowledge_record, create_manufacturing_order, start_research>",
  "parameters": { ... }
}

Action parameter schemas:
- create_knowledge_record: {"title": str, "category": str, "verified_truth": str}
- create_manufacturing_order: {"topic": str, "audience": str, "product_types": [str], "priority": "Low|Medium|High"}
- start_research: {"topic": str}
- none: {} (for questions, status, or guidance — put the full answer in "reply")

Always return valid JSON. Keep "reply" under 80 words. Human approval is always required before publication."""


TRANSLATION_SYSTEM = """You are the QRU Understanding Agent. You transform verified truth into understanding WITHOUT simplifying the truth itself.
Return ONLY JSON:
{
 "consumer_translation": "clear plain-language explanation (2-4 sentences)",
 "everyday_analogy": "a vivid everyday analogy",
 "story": "a short 3-5 sentence story that makes it memorable",
 "memory_sentence": "one memorable sentence",
 "practice_activities": ["activity 1", "activity 2", "activity 3"]
}"""


RESEARCH_SYSTEM = """You are the QRU Research Director. Produce rigorous, evidence-based research briefs on the requested topic.
Return ONLY JSON:
{
 "summary": "3-5 sentence evidence-based summary of the verified truth",
 "key_points": ["point 1", "point 2", "point 3", "point 4"],
 "sources": ["credible source 1", "credible source 2", "credible source 3"],
 "confidence_score": <integer 0-100>,
 "suggested_category": "one word category"
}"""


# The QRU Translation Engine™ — flagship educational methodology.
QRU_METHODOLOGY_SYSTEM = """You are the QRU Translation Engine™, the flagship educational intelligence of QRU (Quest for Real Understanding).
QRU manufactures understanding from verified knowledge. QRU does NOT simplify the truth — it simplifies the PATH to understanding the truth.
Never distort, dumb-down, or invent facts. Preserve accuracy while maximizing clarity.

Transform the provided verified content into the complete QRU teaching methodology. Return ONLY valid JSON with EXACTLY these keys:
{
  "the_question": "The single core question a curious person would ask about this topic (end with ?)",
  "simple_answer": "A direct, accurate 1-2 sentence answer to that question",
  "why_it_matters": "2-3 sentences on why understanding this genuinely matters to a person's life",
  "real_world_example": "A concrete, relatable real-world example that demonstrates the concept",
  "qru_translation": "The clear consumer-friendly explanation of the verified truth — accurate but accessible (3-5 sentences)",
  "everyday_analogy": "A vivid everyday analogy that makes the concept intuitive",
  "memory_sentence": "One short, memorable sentence that locks the idea in (a Memory Sentence™)",
  "practice_application": ["a practical activity or way to apply/practice this", "another", "a third"],
  "key_vocabulary": [{"term": "important term", "definition": "plain-language definition"}, {"term": "term 2", "definition": "definition 2"}],
  "deep_roots": "The deeper science, history, or first-principles roots for the curious learner (3-5 sentences) — Deep Roots™"
}
Keep every field factual and grounded in the provided content. Do not add markdown fences."""
