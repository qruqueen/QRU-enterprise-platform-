import asyncio, os
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")


async def m():
    from emergentintegrations.llm.openai import OpenAITextToSpeech
    k = os.getenv("EMERGENT_LLM_KEY")
    print("key prefix:", (k or "")[:14])
    tts = OpenAITextToSpeech(api_key=k)
    out = await tts.generate_speech(text="Hello, this is a test of the QRU audiobook narration voice. One two three four five.", model="tts-1", voice="sage")
    print("type:", type(out), "len:", len(out) if hasattr(out, "__len__") else "?")
    print("first 8 bytes:", bytes(out[:8]))
    with open("/tmp/tts_test.mp3", "wb") as f:
        f.write(out)


asyncio.run(m())
