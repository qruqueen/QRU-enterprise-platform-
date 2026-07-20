"""Iteration 84 — verify PDFs/DB of the 2 UI-created products, then CLEANUP.
Reads /app/test_reports/.i84_created.json for the ids and asserts:
 - DB: verified=true, knowledge_record_id=decoder KR, source_decoder.decoder_id, product_type,
   customer_deliverable has a pdf, source KR is Verified/Approved/Treasure.
 - PDF: Copyright, Colophon, Title page, no factory chrome, no sanitization leftovers,
   body derives from decoder decoded understanding.
 - Zero-LLM: create-product call completed in <60s (already asserted at UI runtime).
 - Cleanup: products removed, decoder pull, KR counter decremented; confirms removal.
"""
import asyncio
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pypdf import PdfReader

load_dotenv("/app/backend/.env")
ASSET_DIR = "/app/backend/rendered_assets"

DISALLOWED = [
    "Manufactured by QRU Factory",
    "working title", "TODO", "TKTK", "[PLACEHOLDER]", "DRAFT ONLY",
]


def _pdf_text(path):
    reader = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in reader.pages)


async def _verify_and_cleanup():
    with open("/app/test_reports/.i84_created.json") as f:
        ids = json.load(f)["ids"]
    assert ids, "no created ids to verify"

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    results = {"products": [], "cleanup_confirmations": {}}

    kr_id_hits = {}
    decoder_id_hits = {}

    for pid in ids:
        p = await db.products.find_one({"id": pid}, {"_id": 0})
        assert p, f"product {pid} not in DB"
        assert p.get("verified") is True, f"[{pid}] verified must be true, got {p.get('verified')}"
        kr = p.get("knowledge_record_id")
        assert kr, f"[{pid}] no knowledge_record_id"
        kr_id_hits[kr] = kr_id_hits.get(kr, 0) + 1
        src = p.get("source_decoder") or {}
        assert src.get("decoder_id"), f"[{pid}] no source_decoder.decoder_id"
        decoder_id_hits[src["decoder_id"]] = decoder_id_hits.get(src["decoder_id"], 0) + 1
        ptype = p.get("product_type")
        assert ptype in ("Workbook", "Teacher Guide"), f"[{pid}] unexpected product_type {ptype}"
        files = ((p.get("customer_deliverable") or {}).get("files") or [])
        pdfs = [f for f in files if (f.get("format") or "").lower() == "pdf"]
        assert pdfs, f"[{pid}] no pdf in customer_deliverable.files"

        # Verify decoder → KR chain
        dec = await db.decoder_records.find_one({"decoder_id": src["decoder_id"]}, {"_id": 0, "source_kr_ids": 1, "definition": 1, "why_it_matters": 1, "analogy": 1, "title": 1})
        assert dec, "decoder not found"
        expected_kr = (dec.get("source_kr_ids") or [{}])[0].get("kr_id")
        assert expected_kr == kr, f"KR mismatch: product.knowledge_record_id={kr} decoder.source_kr_ids[0].kr_id={expected_kr}"

        # KR verification status
        kr_doc = await db.knowledge_records.find_one({"id": kr}, {"_id": 0})
        assert kr_doc, "KR not found"
        assert (
            kr_doc.get("verification_status") == "Verified"
            or kr_doc.get("approval_status") == "Approved"
            or kr_doc.get("treasure_standard") is True
        ), f"KR not Verified/Approved/Treasure: {kr_doc.get('verification_status'), kr_doc.get('approval_status'), kr_doc.get('treasure_standard')}"

        # PDF on disk
        pdf_name = pdfs[0].get("filename") or pdfs[0].get("url", "").split("/")[-1]
        pdf_path = os.path.join(ASSET_DIR, pdf_name)
        assert os.path.exists(pdf_path), f"PDF missing at {pdf_path}"

        text = _pdf_text(pdf_path)
        assert re.search(r"copyright", text, re.I), f"[{pid}] PDF missing Copyright"
        assert re.search(r"colophon", text, re.I), f"[{pid}] PDF missing Colophon"
        head = text[:2500]
        title_seed = (dec.get("title") or "").split(" — ")[0].strip()
        assert title_seed.lower() in head.lower(), f"[{pid}] title '{title_seed}' not in PDF head"
        for bad in DISALLOWED:
            assert bad.lower() not in text.lower(), f"[{pid}] disallowed marker '{bad}' present"

        # content-derives-from-decoder spot check
        seeds = [dec.get("definition"), dec.get("why_it_matters"), dec.get("analogy")]
        seeds = [s for s in seeds if isinstance(s, str) and len(s) > 30]
        hits = 0
        for s in seeds:
            snippet = " ".join(s.split()[:6]).lower()
            if snippet and snippet in text.lower():
                hits += 1
        assert hits >= 1, f"[{pid}] PDF body doesn't spot-check against decoder decoded understanding"

        # Zero factory chrome: also ensure the "internal" chrome string 'QRU Factory OS' / 'Factory Ops' is absent
        for chrome in ("QRU Factory OS", "Factory Operator", "Manufacturing Dashboard"):
            assert chrome not in text, f"[{pid}] internal factory chrome '{chrome}' leaked in PDF"

        results["products"].append({
            "id": pid, "product_type": ptype, "title": p.get("title"),
            "kr": kr, "decoder_id": src["decoder_id"], "pdf": pdf_path,
            "pdf_pages": len(PdfReader(pdf_path).pages),
        })
        print(f"OK [{ptype}] id={pid} pdf={pdf_name} pages={results['products'][-1]['pdf_pages']}")

    # STEP 10 CLEANUP
    del_res = await db.products.delete_many({"id": {"$in": ids}})
    assert del_res.deleted_count == len(ids), f"deleted={del_res.deleted_count} expected={len(ids)}"

    remaining = await db.products.count_documents({"id": {"$in": ids}})
    assert remaining == 0, f"remaining={remaining}"
    results["cleanup_confirmations"]["products_deleted"] = del_res.deleted_count
    results["cleanup_confirmations"]["products_remaining"] = remaining

    # pull from decoders' manufactured_products
    for did, _n in decoder_id_hits.items():
        await db.decoder_records.update_one({"decoder_id": did}, {"$pull": {"manufactured_products": {"product_id": {"$in": ids}}}})
        dec = await db.decoder_records.find_one({"decoder_id": did}, {"_id": 0, "manufactured_products": 1}) or {}
        lingering = [m for m in (dec.get("manufactured_products") or []) if m.get("product_id") in ids]
        assert not lingering, f"decoder {did} still references: {lingering}"
        results["cleanup_confirmations"][f"decoder_{did}_lingering"] = len(lingering)

    # decrement KR counter by N (floor 0)
    for kr, n in kr_id_hits.items():
        krd = await db.knowledge_records.find_one({"id": kr}, {"_id": 0, "products_created": 1}) or {}
        cur = int(krd.get("products_created") or 0)
        new_val = max(0, cur - n)
        await db.knowledge_records.update_one({"id": kr}, {"$set": {"products_created": new_val}})
        after = (await db.knowledge_records.find_one({"id": kr}, {"_id": 0, "products_created": 1}) or {}).get("products_created")
        assert after == new_val
        results["cleanup_confirmations"][f"kr_{kr}_products_created_before"] = cur
        results["cleanup_confirmations"][f"kr_{kr}_products_created_after"] = after

    print("CLEANUP OK — products removed, decoders un-linked, KR counters decremented")
    print(json.dumps(results, indent=2, default=str))

    with open("/app/test_reports/.i84_verify_report.json", "w") as f:
        json.dump(results, f, indent=2, default=str)


if __name__ == "__main__":
    asyncio.run(_verify_and_cleanup())
