"""QRU Store Health™ — read-only, evidence-based integrity view of the live store.

Treasure Standard™: every number is derived from real data in THIS environment's
database (production when run on the deployed site). No fabricated metrics, no
fake "healthy" states. Purely read-only — computes, never writes.
"""
import os
from datetime import datetime, timezone

from database import db
import prod_migrations as pm

_PUBLISHED_QUERY = {"founder_authorization.authorized": True}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _cover_url(book: dict):
    design = (book.get("artifacts") or {}).get("design") or {}
    concepts = design.get("cover_concepts") or []
    selected = design.get("selected_cover") or {}
    sel_no = selected.get("concept")
    if sel_no is not None:
        for c in concepts:
            if c.get("concept") == sel_no and c.get("url"):
                return c["url"]
    for c in concepts:
        if c.get("url"):
            return c["url"]
    return None


async def _storefront():
    docs = await db.book_records.find(_PUBLISHED_QUERY, {"_id": 0}).to_list(1000)
    with_cover, missing = [], []
    for b in docs:
        (with_cover if _cover_url(b) else missing).append(b)
    settings = await db.storefront_settings.find_one({"key": "featured"})
    featured = (settings or {}).get("book_ids") or []
    return {
        "authorized_books": len(docs),
        "live_on_storefront": len(with_cover),          # only cover-bearing books show publicly
        "hidden_missing_cover": len(missing),
        "missing_cover_titles": [b.get("title") for b in missing][:20],
        "featured_selected": len(featured),
        "featured_mode": "founder-curated" if featured else "auto",
    }


async def _hygiene():
    rows = await pm._test_products_classify()
    visible = [r for r in rows if r["classification"] == "TEST_VISIBLE_IN_CATALOG"]
    return {
        "test_products_matched": len(rows),
        "test_products_visible_in_catalog": len(visible),
        "visible_codes": [r["code"] for r in visible][:20],
    }


def _commerce_config():
    key = os.environ.get("STRIPE_API_KEY", "")
    test_override = os.environ.get("STRIPE_TEST")
    if key.startswith("sk_live"):
        mode = "LIVE"
    elif key.startswith("sk_test") or key == "sk_test_emergent" or test_override:
        mode = "TEST"
    else:
        mode = "UNKNOWN"
    return {
        "stripe_mode": mode,
        "accepts_real_money": mode == "LIVE",
        "webhook_secret_set": bool(os.environ.get("STRIPE_WEBHOOK_SECRET")),
        "sender_email_set": bool(os.environ.get("SENDER_EMAIL")),
        "support_email_set": bool(os.environ.get("SUPPORT_EMAIL")),
        "email_provider_key_set": bool(os.environ.get("RESEND_API_KEY")),
    }


async def _orders():
    total = await db.book_purchases.count_documents({})
    paid = await db.book_purchases.count_documents({"payment_status": "paid"})
    pending = await db.book_purchases.count_documents({"payment_status": "pending"})
    # email delivery breakdown for paid orders
    sent = await db.book_purchases.count_documents(
        {"payment_status": "paid", "confirmation_email.status": {"$in": ["sent-to-provider", "sent", "delivered"]}})
    skipped = await db.book_purchases.count_documents(
        {"payment_status": "paid", "confirmation_email.status": "skipped"})
    failed = await db.book_purchases.count_documents(
        {"payment_status": "paid", "confirmation_email.status": "error"})
    subs = await db.newsletter_subscribers.count_documents({})
    return {
        "orders_total": total, "orders_paid": paid, "orders_pending": pending,
        "confirmation_sent": sent, "confirmation_skipped": skipped, "confirmation_failed": failed,
        "newsletter_subscribers": subs,
    }


async def _cover_integrity():
    """Live durable check of every published book's ACTIVE cover master. Flags books whose
    active cover is missing from durable storage (the root cause of broken cover thumbnails)
    and whether a Founder-generated alternate concept is available to fall back to."""
    docs = await db.book_records.find(_PUBLISHED_QUERY, {"_id": 0}).to_list(1000)
    broken, repairable, unrepairable, checked = [], 0, 0, 0
    for b in docs:
        design = (b.get("artifacts") or {}).get("design") or {}
        concepts = design.get("cover_concepts") or []
        selected = design.get("selected_cover") or {}
        url = selected.get("url") or _cover_url(b)
        if not url:
            continue  # missing-cover books are reported under storefront
        checked += 1
        fname = url.rsplit("/", 1)[-1]
        if await pm._asset_ok(fname):
            continue
        alt = None
        for c in concepts:
            cu = c.get("url")
            if not cu or cu.rsplit("/", 1)[-1] == fname or c.get("status") == "failed":
                continue
            if await pm._asset_ok(cu.rsplit("/", 1)[-1]):
                alt = c.get("concept")
                break
        rep = alt is not None
        repairable += 1 if rep else 0
        unrepairable += 0 if rep else 1
        broken.append({"code": b.get("book_code"), "title": b.get("title"),
                       "active_cover": fname, "repairable": rep, "fallback_concept": alt})
    return {"checked": checked, "broken": len(broken), "repairable": repairable,
            "unrepairable": unrepairable, "books": broken[:50]}


def _overall(storefront, hygiene, commerce, orders, cover=None):
    """Deterministic health rollup — honest signals, not a vanity score."""
    checks = []
    checks.append({"key": "storefront_has_books", "ok": storefront["live_on_storefront"] > 0,
                   "label": "At least one book is live on the storefront",
                   "detail": f"{storefront['live_on_storefront']} live"})
    checks.append({"key": "no_hidden_covers", "ok": storefront["hidden_missing_cover"] == 0,
                   "label": "No authorized book is hidden by a missing cover",
                   "detail": f"{storefront['hidden_missing_cover']} hidden"})
    checks.append({"key": "no_visible_test_products", "ok": hygiene["test_products_visible_in_catalog"] == 0,
                   "label": "No internal test products visible in the learner catalog",
                   "detail": f"{hygiene['test_products_visible_in_catalog']} visible"})
    checks.append({"key": "checkout_configured", "ok": commerce["stripe_mode"] != "UNKNOWN",
                   "label": "Stripe checkout is configured",
                   "detail": f"{commerce['stripe_mode']} mode"})
    checks.append({"key": "webhook_secret", "ok": commerce["webhook_secret_set"],
                   "label": "Stripe webhook secret is set (secure fulfillment)",
                   "detail": "set" if commerce["webhook_secret_set"] else "missing"})
    checks.append({"key": "email_delivery", "ok": commerce["email_provider_key_set"],
                   "label": "Confirmation email provider is connected",
                   "detail": "connected" if commerce["email_provider_key_set"] else "not connected"})
    checks.append({"key": "no_failed_confirmations", "ok": orders["confirmation_failed"] == 0,
                   "label": "No failed purchase-confirmation emails",
                   "detail": f"{orders['confirmation_failed']} failed"})
    if cover is not None:
        checks.append({"key": "covers_durable", "ok": cover["broken"] == 0,
                       "label": "Every live book's active cover is retrievable from durable storage",
                       "detail": "all durable" if cover["broken"] == 0 else f"{cover['broken']} broken ({cover['repairable']} repairable)"})
    passed = sum(1 for c in checks if c["ok"])
    critical = {"storefront_has_books", "no_visible_test_products", "checkout_configured"}
    critical_fail = [c["key"] for c in checks if not c["ok"] and c["key"] in critical]
    if critical_fail:
        status = "attention"
    elif passed == len(checks):
        status = "healthy"
    else:
        status = "warnings"
    return {"status": status, "passed": passed, "total": len(checks), "checks": checks}


async def report():
    storefront = await _storefront()
    hygiene = await _hygiene()
    commerce = _commerce_config()
    orders = await _orders()
    cover = await _cover_integrity()
    overall = _overall(storefront, hygiene, commerce, orders, cover)
    return {
        "at": _now(),
        "overall": overall,
        "storefront": storefront,
        "hygiene": hygiene,
        "commerce": commerce,
        "orders": orders,
        "cover_integrity": cover,
    }
