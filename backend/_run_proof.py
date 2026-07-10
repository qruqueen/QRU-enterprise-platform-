import asyncio, json
import media_library as ml
import media_production as mp


async def main():
    res = await ml.search("pixabay_video", "peaceful forest sunrise", 5)
    if not res.get("results"):
        print("NO_RESULTS", res)
        return
    item = res["results"][0]
    item["search_query_used"] = "peaceful forest sunrise"
    out = await mp.produce_showcase(
        item, "Forex Foundations", "Erica Talbert",
        milestone={"code": "QRU-MILESTONE-001", "title": "First Live Licensed Media Acquisition"})
    print("PIPELINE_RESULT:")
    print(json.dumps(out, indent=1, default=str))


asyncio.run(main())
