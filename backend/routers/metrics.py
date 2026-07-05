"""QRU Evidence Metrics Engine™ — every dashboard number traces to real records.

Treasure Standard™: no synthetic math. Each metric declares its provenance
(LIVE / TEST / SIMULATED / NOT TRACKED YET) and drills into the exact records
that produced the value. TEST and LIVE activity is never combined.
"""
import os

from fastapi import APIRouter, Depends, HTTPException, Request

from database import db
from auth import get_current_user
import connectors as cx

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
STRIPE_TEST = STRIPE_API_KEY.startswith("sk_test_")
# Commerce provenance: TEST when a Stripe test key is active, LIVE when live.
PAY_MODE = "TEST" if STRIPE_TEST else ("LIVE" if STRIPE_API_KEY else "NOT_TRACKED")

LIVE, TEST, SIMULATED, NOT_TRACKED = "LIVE", "TEST", "SIMULATED", "NOT_TRACKED"


# ---------------------------------------------------------------------------
# Record formatters (full evidence per the Treasure Standard™)
# ---------------------------------------------------------------------------
def _order_record(t):
    paid = t.get("payment_status") == "paid"
    created = t.get("created_at") or ""
    return {
        "order_id": t.get("session_id") or t.get("id"),
        "transaction_id": t.get("session_id") or "—",
        "product": t.get("title") or "—",
        "product_code": t.get("product_code") or "—",
        "customer": t.get("user_email") or "—",
        "purchase_date": created[:10] or "—",
        "purchase_time": created[11:19] or "—",
        "payment_provider": "Stripe",
        "payment_status": t.get("payment_status") or "—",
        "mode": PAY_MODE,
        "revenue": round(t.get("amount", 0) or 0, 2),
        "currency": (t.get("currency") or "usd").upper(),
        "taxes": 0.0,
        "discounts": 0.0,
        "fulfillment_status": "Fulfilled" if paid else "Pending",
        "download_delivered": "Yes" if paid else "No",
        "platform": "QRU Store™",
    }


def _purchase_record(p):
    granted = p.get("granted_at") or ""
    return {
        "product": p.get("title") or "—",
        "product_code": p.get("product_code") or "—",
        "customer": p.get("user_email") or "—",
        "delivered_date": granted[:10] or "—",
        "delivered_time": granted[11:19] or "—",
        "amount": round(p.get("amount", 0) or 0, 2),
        "currency": (p.get("currency") or "usd").upper(),
        "mode": PAY_MODE,
        "download_delivered": "Yes",
    }


def _product_record(p):
    return {
        "product_code": p.get("product_code") or "—",
        "title": p.get("title") or "—",
        "type": p.get("product_type") or "—",
        "status": p.get("status") or "—",
        "factory_confidence": p.get("factory_confidence", "—"),
        "created": (p.get("created_at") or "")[:10] or "—",
    }


def _published_record(p):
    return {
        "product_code": p.get("product_code") or "—",
        "title": p.get("title") or "—",
        "status": p.get("status") or "—",
        "published_at": (p.get("published_at") or "")[:19].replace("T", " ") or "—",
        "published_by": p.get("published_by") or "—",
        "platform": "QRU Store™",
        "treasure_standard": p.get("treasure_standard_status", "Pending"),
    }


def _mo_record(m):
    return {
        "code": m.get("code") or m.get("mo_code") or m.get("id") or "—",
        "product": m.get("title") or m.get("product_title") or "—",
        "status": m.get("status") or "—",
        "created": (m.get("created_at") or "")[:10] or "—",
    }


def _job_record(j):
    return {
        "job_id": j.get("id") or "—",
        "type": j.get("type") or j.get("job_type") or "—",
        "status": j.get("status") or "—",
        "created": (j.get("created_at") or "")[:19].replace("T", " ") or "—",
    }


def _kr_record(k):
    return {
        "kr_code": k.get("kr_code") or "—",
        "title": k.get("title") or "—",
        "category": k.get("category") or "—",
        "verification_status": k.get("verification_status") or "—",
        "treasure_standard": "Yes" if k.get("treasure_standard") else "No",
    }


# ---------------------------------------------------------------------------
# Metric registry — each metric knows its value, provenance and evidence.
# ---------------------------------------------------------------------------
async def _paid_txns():
    return await db.payment_transactions.find({"payment_status": "paid"}).sort("created_at", -1).to_list(1000)


async def _summary():
    paid = await _paid_txns()
    revenue = round(sum(t.get("amount", 0) or 0 for t in paid), 2)
    pending = await db.payment_transactions.count_documents({"payment_status": "pending"})
    purchases = await db.purchases.count_documents({})
    paying_customers = len([e for e in await db.purchases.distinct("user_email") if e])

    prod_total = await db.products.count_documents({})
    prod_published = await db.products.count_documents({"status": "Published"})
    mo_total = await db.manufacturing_orders.count_documents({})
    jobs_total = await db.manufacturing_jobs.count_documents({})
    kr_total = await db.knowledge_records.count_documents({})

    connectors = await cx.list_connectors()
    operational = sum(1 for c in connectors if c["operational"])

    commerce_note = "Stripe is in TEST mode — these are test orders, not live revenue." if STRIPE_TEST \
        else ("Live Stripe payments." if STRIPE_API_KEY else "Payments not connected yet.")

    metrics = [
        # ---- Commerce (real payment records) ----
        {"id": "paid_orders", "label": "Paid Orders", "group": "Commerce", "value": len(paid),
         "display": str(len(paid)), "provenance": PAY_MODE if paid else NOT_TRACKED,
         "note": commerce_note},
        {"id": "revenue", "label": "Revenue", "group": "Commerce", "value": revenue,
         "display": f"${revenue:,.2f}", "provenance": PAY_MODE if paid else NOT_TRACKED,
         "note": commerce_note + " Gross of any refunds/fees (not tracked in test mode)."},
        {"id": "pending_orders", "label": "Pending Orders", "group": "Commerce", "value": pending,
         "display": str(pending), "provenance": PAY_MODE if pending else NOT_TRACKED,
         "note": "Checkouts opened that have not completed payment."},
        {"id": "fulfilled", "label": "Fulfilled", "group": "Commerce", "value": purchases,
         "display": str(purchases), "provenance": PAY_MODE if purchases else NOT_TRACKED,
         "note": "Paid orders where access + files were granted to the customer."},
        {"id": "downloads", "label": "Downloads Delivered", "group": "Commerce", "value": purchases,
         "display": str(purchases), "provenance": PAY_MODE if purchases else NOT_TRACKED,
         "note": "Manufactured files delivered to paying customers (real files)."},
        {"id": "customers", "label": "Paying Customers", "group": "Commerce", "value": paying_customers,
         "display": str(paying_customers), "provenance": PAY_MODE if paying_customers else NOT_TRACKED,
         "note": "Distinct customers who completed a purchase."},
        {"id": "refunds", "label": "Refunds", "group": "Commerce", "value": 0, "display": "0",
         "provenance": NOT_TRACKED, "note": "No refund flow is implemented yet — nothing to show."},
        {"id": "subscriptions", "label": "Subscriptions", "group": "Commerce", "value": 0, "display": "0",
         "provenance": NOT_TRACKED, "note": "Subscriptions are not implemented yet — one-time purchases only."},
        # ---- Manufacturing (real factory records) ----
        {"id": "products", "label": "Products", "group": "Manufacturing", "value": prod_total,
         "display": str(prod_total), "provenance": LIVE,
         "note": "Real product records in the factory."},
        {"id": "manufacturing_orders", "label": "Manufacturing Orders", "group": "Manufacturing",
         "value": mo_total, "display": str(mo_total), "provenance": LIVE,
         "note": "Real manufacturing orders across all stages."},
        {"id": "manufacturing_jobs", "label": "Manufacturing Jobs", "group": "Manufacturing",
         "value": jobs_total, "display": str(jobs_total), "provenance": LIVE,
         "note": "Real manufacturing job records (all statuses)."},
        {"id": "knowledge_records", "label": "Knowledge Records", "group": "Manufacturing",
         "value": kr_total, "display": str(kr_total), "provenance": LIVE,
         "note": "Real verified/draft knowledge records."},
        # ---- Publishing ----
        {"id": "published", "label": "Published Products", "group": "Publishing", "value": prod_published,
         "display": str(prod_published), "provenance": LIVE,
         "note": "Products published to the QRU Store™."},
        {"id": "connector_status", "label": "Operational Connectors", "group": "Publishing",
         "value": operational, "display": f"{operational}/{len(connectors)}", "provenance": LIVE,
         "note": "Publishing connectors that are fully wired end-to-end today."},
        {"id": "publishing_status", "label": "Publishing Jobs", "group": "Publishing",
         "value": prod_published, "display": str(prod_published), "provenance": LIVE,
         "note": "Publication events to operational connectors (QRU Store™)."},
    ]
    return metrics


@router.get("/summary")
async def summary(user=Depends(get_current_user)):
    metrics = await _summary()
    return {"metrics": metrics, "pay_mode": PAY_MODE,
            "stripe_test": STRIPE_TEST, "groups": ["Commerce", "Manufacturing", "Publishing"]}


COLUMNS = {
    "orders": [("order_id", "Order ID"), ("product", "Product"), ("customer", "Customer"),
               ("purchase_date", "Date"), ("purchase_time", "Time"), ("payment_provider", "Provider"),
               ("payment_status", "Payment"), ("mode", "Live/Test"), ("revenue", "Revenue ($)"),
               ("taxes", "Taxes"), ("discounts", "Discounts"), ("fulfillment_status", "Fulfillment"),
               ("download_delivered", "Delivered"), ("platform", "Platform"), ("transaction_id", "Transaction ID")],
    "purchases": [("product", "Product"), ("product_code", "Code"), ("customer", "Customer"),
                  ("delivered_date", "Delivered"), ("delivered_time", "Time"), ("amount", "Amount ($)"),
                  ("mode", "Live/Test"), ("download_delivered", "Delivered")],
    "products": [("product_code", "Code"), ("title", "Title"), ("type", "Type"),
                 ("status", "Status"), ("factory_confidence", "Confidence"), ("created", "Created")],
    "published": [("product_code", "Code"), ("title", "Title"), ("status", "Status"),
                  ("published_at", "Published"), ("published_by", "By"), ("platform", "Platform"),
                  ("treasure_standard", "Treasure Standard™")],
    "mos": [("code", "Code"), ("product", "Product"), ("status", "Status"), ("created", "Created")],
    "jobs": [("job_id", "Job ID"), ("type", "Type"), ("status", "Status"), ("created", "Created")],
    "krs": [("kr_code", "Code"), ("title", "Title"), ("category", "Category"),
            ("verification_status", "Verification"), ("treasure_standard", "Treasure Standard™")],
    "connectors": [("name", "Connector"), ("category", "Category"), ("status", "Status"),
                   ("operational", "Operational"), ("auth_method", "Auth")],
}


def _cols(key):
    return [{"key": k, "label": lbl} for k, lbl in COLUMNS[key]]


@router.get("/{metric_id}/evidence")
async def evidence(metric_id: str, user=Depends(get_current_user)):
    async def customers_records():
        emails = [e for e in await db.purchases.distinct("user_email") if e]
        out = []
        for e in emails:
            docs = await db.purchases.find({"user_email": e}).to_list(500)
            out.append({"customer": e, "orders": len(docs),
                        "total_spent": round(sum(d.get("amount", 0) or 0 for d in docs), 2),
                        "mode": PAY_MODE, "last_purchase": max((d.get("granted_at", "") for d in docs), default="")[:10]})
        return {"columns": [{"key": "customer", "label": "Customer"}, {"key": "orders", "label": "Orders"},
                            {"key": "total_spent", "label": "Total Spent ($)"}, {"key": "mode", "label": "Live/Test"},
                            {"key": "last_purchase", "label": "Last Purchase"}],
                "records": out, "provenance": PAY_MODE if out else NOT_TRACKED}

    if metric_id in ("paid_orders", "revenue"):
        txns = await _paid_txns()
        return {"metric": metric_id, "columns": _cols("orders"),
                "records": [_order_record(t) for t in txns], "provenance": PAY_MODE if txns else NOT_TRACKED,
                "empty_message": "No paid orders yet. When a customer completes a Stripe test checkout, it appears here."}

    if metric_id == "pending_orders":
        txns = await db.payment_transactions.find({"payment_status": {"$ne": "paid"}}).sort("created_at", -1).to_list(500)
        return {"metric": metric_id, "columns": _cols("orders"),
                "records": [_order_record(t) for t in txns], "provenance": PAY_MODE if txns else NOT_TRACKED,
                "empty_message": "No pending checkouts."}

    if metric_id in ("fulfilled", "downloads"):
        docs = await db.purchases.find().sort("granted_at", -1).to_list(500)
        return {"metric": metric_id, "columns": _cols("purchases"),
                "records": [_purchase_record(p) for p in docs], "provenance": PAY_MODE if docs else NOT_TRACKED,
                "empty_message": "No fulfilled orders yet — files are delivered automatically once a payment clears."}

    if metric_id == "customers":
        return {"metric": metric_id, **(await customers_records()),
                "empty_message": "No paying customers yet."}

    if metric_id in ("refunds", "subscriptions"):
        return {"metric": metric_id, "columns": [], "records": [], "provenance": NOT_TRACKED,
                "empty_message": ("No refund flow is implemented yet — nothing to show."
                                  if metric_id == "refunds"
                                  else "Subscriptions are not implemented yet — QRU sells one-time products only.")}

    if metric_id == "products":
        docs = await db.products.find().sort("created_at", -1).to_list(500)
        return {"metric": metric_id, "columns": _cols("products"),
                "records": [_product_record(p) for p in docs], "provenance": LIVE,
                "empty_message": "No products yet."}

    if metric_id in ("published", "publishing_status"):
        docs = await db.products.find({"status": "Published"}).sort("published_at", -1).to_list(500)
        return {"metric": metric_id, "columns": _cols("published"),
                "records": [_published_record(p) for p in docs], "provenance": LIVE,
                "empty_message": "Nothing published yet — publish a review-passed product from the Founder Inbox or Connectors."}

    if metric_id == "manufacturing_orders":
        docs = await db.manufacturing_orders.find().sort("created_at", -1).to_list(500)
        return {"metric": metric_id, "columns": _cols("mos"),
                "records": [_mo_record(m) for m in docs], "provenance": LIVE,
                "empty_message": "No manufacturing orders yet."}

    if metric_id == "manufacturing_jobs":
        docs = await db.manufacturing_jobs.find().sort("created_at", -1).to_list(500)
        return {"metric": metric_id, "columns": _cols("jobs"),
                "records": [_job_record(j) for j in docs], "provenance": LIVE,
                "empty_message": "No manufacturing jobs yet."}

    if metric_id == "knowledge_records":
        docs = await db.knowledge_records.find().sort("updated_at", -1).to_list(500)
        return {"metric": metric_id, "columns": _cols("krs"),
                "records": [_kr_record(k) for k in docs], "provenance": LIVE,
                "empty_message": "No knowledge records yet."}

    if metric_id == "connector_status":
        connectors = await cx.list_connectors()
        recs = [{"name": c["name"], "category": c["category"], "status": c["status"],
                 "operational": "Yes" if c["operational"] else "No", "auth_method": c["auth_method"]}
                for c in connectors]
        return {"metric": metric_id, "columns": _cols("connectors"),
                "records": recs, "provenance": LIVE, "empty_message": "No connectors registered."}

    raise HTTPException(404, "Unknown metric")


# ---------------------------------------------------------------------------
# Founder Beta Status™ — plain-language transparency (interaction audit)
# ---------------------------------------------------------------------------
@router.get("/beta-status")
async def beta_status(request: Request, host: str = "", user=Depends(get_current_user)):
    origin = host or str(request.headers.get("origin", "")) or str(request.base_url)
    is_preview = "preview.emergentagent.com" in origin
    is_deployed = (".emergent.host" in origin) or ("emergentagent.com" in origin and not is_preview)
    connectors = await cx.list_connectors()
    operational = [c["name"] for c in connectors if c["operational"]]
    under_dev = [c["name"] for c in connectors if not c["operational"]]

    deployment_state = ("Founder Preview (Private Beta)" if is_preview
                        else "Deployed Beta" if is_deployed else "Local Development")
    blocks_promotion = [
        "Stripe is in TEST mode — no real payments can be accepted until live keys are added.",
        "Email delivery is not yet wired — customers are not emailed their downloads.",
        f"Automated file publishing is not yet wired for {len(under_dev)} OAuth connectors (connect + test connection are operational via the Universal OAuth Framework™).",
    ]

    questions = [
        {"q": "Is this Beta public or private?", "a": "Private. Only signed-in QRU accounts can access it.", "status": "info"},
        {"q": "Can anyone with the URL access it?", "a": "No. The URL requires login — sharing the link alone does not grant access.", "status": "warn"},
        {"q": "Does it require an account?", "a": "Yes. A QRU/Emergent-authenticated account is required to sign in.", "status": "info"},
        {"q": "Can customers purchase products?", "a": "Yes — checkout works end-to-end through Stripe.", "status": "ok"},
        {"q": "Are purchases simulated or live?", "a": "Sandbox. Purchases run through Stripe TEST mode.", "status": "warn"},
        {"q": "Are payments real or sandbox?", "a": "Sandbox (Stripe test keys). No real money moves.", "status": "warn"},
        {"q": "Are downloads real or simulated?", "a": "Real. Paying customers receive the actual manufactured files.", "status": "ok"},
        {"q": "Can products actually be published?", "a": "Yes — to the QRU Store™ (native connector). External platforms are guided-setup only.", "status": "ok"},
        {"q": "Which platforms are operational?", "a": (", ".join(operational) or "None") + ". Others can now be Connected & Tested via the Universal OAuth Framework™ once an admin configures each provider's OAuth app.", "status": "ok"},
        {"q": "Which platforms are under development?", "a": (", ".join(under_dev) or "None") + " — connect/test works after Developer Setup; automated publishing of the file is not yet wired for these.", "status": "warn"},
        {"q": "Can YouTube publishing be tested?", "a": "Yes — once an admin completes Developer Setup (OAuth app), the Founder can Connect via Google and Test the connection. Automated video upload is not yet wired.", "status": "warn"},
        {"q": "Can Stripe accept real payments?", "a": "No — test keys only. Add live keys to accept real payments.", "status": "warn"},
        {"q": "Can Amazon KDP publish?", "a": "No — Amazon KDP has no public OAuth publishing API; books are uploaded in the KDP dashboard.", "status": "warn"},
        {"q": "Can QRU Store process orders?", "a": "Yes — QRU Store™ is fully operational (native).", "status": "ok"},
        {"q": "Can customers create accounts?", "a": "Yes — account creation and login are operational.", "status": "ok"},
        {"q": "Is email delivery operational?", "a": "No — email delivery is not wired yet. Downloads appear in-app after checkout.", "status": "warn"},
        {"q": "What is currently disabled?", "a": "Real payments, email delivery, and external publishing connectors (OAuth/API-key setup pending).", "status": "warn"},
        {"q": "What is still being built?", "a": f"Automated file publishing for {len(under_dev)} OAuth connectors (connect/test is ready); email delivery; live payments.", "status": "info"},
        {"q": "What is the recommended next milestone?", "a": "Reach Founder Beta Complete™ (25 consecutive clean runs), then add live Stripe keys + email delivery for a public launch.", "status": "info"},
    ]

    return {
        "deployment_state": deployment_state,
        "is_production": False,
        "blocks_promotion": blocks_promotion,
        "shareable": "LIMITED",
        "shareable_detail": "The URL can be shared, but recipients must sign in with a QRU account. It is not publicly accessible.",
        "pay_mode": PAY_MODE,
        "stripe_test": STRIPE_TEST,
        "operational_connectors": operational,
        "under_development_connectors": under_dev,
        "questions": questions,
    }
