"""QRU Publish Success Dashboard™ + environment auto-detection.

Answers the Factory's defining question: "Has this product TRULY shipped to customers?"
Every stage is derived from real data — nothing is faked (Treasure Standard™).

Environment auto-detection: each app host that touches THIS database writes a beacon. If more
than one distinct host is seen, preview & production SHARE a database; otherwise we only know of
one environment (production will register itself automatically once it loads)."""
import os
from datetime import datetime, timezone

from database import db

_BEACONS = "system_env_beacons"


async def record_beacon(host: str):
    if not host:
        return
    await db[_BEACONS].update_one(
        {"host": host},
        {"$set": {"host": host, "db_name": os.environ.get("DB_NAME"),
                  "last_seen": datetime.now(timezone.utc).isoformat()}},
        upsert=True)


async def environment_report(current_host: str):
    await record_beacon(current_host)
    beacons = await db[_BEACONS].find({}, {"_id": 0}).sort("last_seen", -1).to_list(50)
    hosts = sorted({b["host"] for b in beacons if b.get("host")})
    shared = len(hosts) > 1
    return {
        "current_host": current_host,
        "db_name": os.environ.get("DB_NAME"),
        "environments_seen": beacons,
        "distinct_hosts": hosts,
        "verdict": "shared_database" if shared else "single_environment_known",
        "explanation": (
            "Multiple distinct app hosts have written to THIS database — your PREVIEW and PRODUCTION "
            "SHARE one database, so an authorized book will appear on qru-online once the app is deployed."
            if shared else
            "Only this environment has registered against this database so far. This means preview and "
            "production are most likely SEPARATE databases — a book authorized in preview must also be "
            "authorized in production. Once production is deployed and loads once, it registers itself here "
            "and this verdict updates automatically."),
    }


def _stage(name, passed, detail=""):
    return {"stage": name, "passed": bool(passed), "detail": detail}


async def _book_stages(b, purchases_by_book):
    bid = b.get("id")
    content = (b.get("editorial_edition") or b.get("working_copy") or {}).get("content")
    artifacts = b.get("artifacts", {}) or {}
    design = artifacts.get("design", {}) or {}
    sanit = artifacts.get("sanitization", {}) or {}
    retail = sanit.get("retail_edition", {}) or {}
    has_deliverable = bool(retail.get("epub") or design.get("selected_cover") or design.get("ebook"))
    authorized = bool((b.get("founder_authorization") or {}).get("authorized"))
    priced = bool((b.get("pricing") or {}).get("approved"))
    on_store = authorized  # public store gate is founder_authorization.authorized
    purchases = purchases_by_book.get(bid, [])
    paid = [p for p in purchases if p.get("payment_status") == "paid"]
    delivered = [p for p in paid if (p.get("download_count") or 0) > 0]

    stages = [
        _stage("Knowledge Record", bool(content), "Source manuscript present" if content else "No source content"),
        _stage("Manufacturing", has_deliverable, "Deliverables rendered" if has_deliverable else "No cover/edition yet"),
        _stage("QA", bool(sanit) or b.get("editorial_locked"), "Sanitized / editorial locked" if (sanit or b.get("editorial_locked")) else "Not sanitized"),
        _stage("Authorized", authorized, "Founder authorized release" if authorized else "Awaiting Founder authorization"),
        _stage("Published", authorized and priced, "Live gate open" if (authorized and priced) else ("Priced but not authorized" if priced else "Not published")),
        _stage("Store Sync", on_store and priced, "Visible in storefront feed" if (on_store and priced) else "Not on storefront"),
        _stage("Purchase Tested", len(paid) > 0, f"{len(paid)} paid order(s)" if paid else "No purchase recorded yet"),
        _stage("Delivery Tested", len(delivered) > 0, f"{len(delivered)} delivered download(s)" if delivered else "No delivery confirmed yet"),
    ]
    shipped = all(s["passed"] for s in stages)
    green = sum(1 for s in stages if s["passed"])
    return {
        "id": bid, "title": b.get("title"), "book_code": b.get("book_code"),
        "stages": stages, "shipped": shipped, "green": green, "total": len(stages),
        "next_action": next((s["stage"] for s in stages if not s["passed"]), None),
    }


async def shipping_status():
    books = await db.book_records.find({}, {"_id": 0}).to_list(1000)
    purchases = await db.book_purchases.find({}, {"_id": 0}).to_list(5000)
    by_book = {}
    for p in purchases:
        by_book.setdefault(p.get("book_id"), []).append(p)
    rows = [await _book_stages(b, by_book) for b in books]
    # Surface manufactured/authorized products first, then by progress.
    rows.sort(key=lambda r: (-r["green"], r["title"] or ""))
    fully = [r for r in rows if r["shipped"]]
    return {
        "total_products": len(rows),
        "fully_shipped": len(fully),
        "in_progress": len(rows) - len(fully),
        "products": rows,
        "stage_names": ["Knowledge Record", "Manufacturing", "QA", "Authorized",
                        "Published", "Store Sync", "Purchase Tested", "Delivery Tested"],
    }
