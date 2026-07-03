"""Iteration 14 tests: Stripe checkout, OpenAI TTS voice, slideshow video, Workflow Engine, FAT."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://understanding-os.preview.emergentagent.com").rstrip("/")

FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="session")
def auth_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=60)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="session")
def client(auth_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"})
    return s


# ---------- AUTH ----------
class TestAuth:
    def test_login_returns_access_token(self, auth_token):
        assert isinstance(auth_token, str) and len(auth_token) > 20


# ---------- COMMERCE ----------
class TestCommerce:
    def test_storefront_returns_products_with_price(self, client):
        r = client.get(f"{BASE_URL}/api/commerce/storefront", timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        # payload could be list or object; capture flexibly
        products = data if isinstance(data, list) else data.get("products", [])
        assert len(products) > 0, f"No products in storefront: {data}"
        for p in products:
            assert "price" in p, f"Product missing price: {p}"
            assert isinstance(p["price"], (int, float)), f"price not numeric: {p['price']}"
        # save for other tests
        pytest._storefront_products = products

    def test_revenue_summary_connected_stripe(self, client):
        r = client.get(f"{BASE_URL}/api/commerce/revenue", timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("connected") is True, f"expected connected=true, got {data}"
        assert data.get("provider") == "Stripe", f"expected provider=Stripe, got {data}"

    def test_checkout_creates_real_stripe_session(self, client):
        products = getattr(pytest, "_storefront_products", None)
        if not products:
            r = client.get(f"{BASE_URL}/api/commerce/storefront", timeout=60)
            products = r.json() if isinstance(r.json(), list) else r.json().get("products", [])
        pid = products[0].get("id") or products[0].get("_id") or products[0].get("product_id")
        assert pid, f"No product id: {products[0]}"

        r = client.post(f"{BASE_URL}/api/commerce/checkout",
                        json={"product_id": pid, "origin_url": "https://understanding-os.preview.emergentagent.com"},
                        timeout=45)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "url" in data and data["url"].startswith("https://checkout.stripe.com"), f"Bad url: {data}"
        assert "session_id" in data and data["session_id"], f"missing session_id: {data}"
        pytest._checkout_session_id = data["session_id"]

    def test_transaction_recorded(self, client):
        sid = getattr(pytest, "_checkout_session_id", None)
        assert sid, "No checkout session id from prev test"
        # small delay to allow write
        time.sleep(1)
        r = client.get(f"{BASE_URL}/api/commerce/transactions", timeout=60)
        assert r.status_code == 200, r.text
        txns = r.json()
        assert isinstance(txns, list)
        match = [t for t in txns if t.get("session_id") == sid]
        assert match, f"session_id {sid} not found in transactions"
        t = match[0]
        assert t.get("payment_status") == "pending", f"expected pending, got {t.get('payment_status')}"

    def test_checkout_rejects_client_amount(self, client):
        """Verify amount is not accepted from client (only product_id + origin_url)."""
        products = getattr(pytest, "_storefront_products", None) or []
        if not products:
            r = client.get(f"{BASE_URL}/api/commerce/storefront", timeout=60)
            products = r.json() if isinstance(r.json(), list) else r.json().get("products", [])
        pid = products[0].get("id") or products[0].get("_id") or products[0].get("product_id")
        # Send inflated amount hoping it gets ignored — server should use server-side price
        r = client.post(f"{BASE_URL}/api/commerce/checkout",
                        json={"product_id": pid, "origin_url": "https://x.com", "amount": 999999.99},
                        timeout=45)
        # Either 200 (ignored) or 422 (rejected) is acceptable; the key is that we don't
        # end up with a 999999.99 pending transaction.
        assert r.status_code in (200, 422, 400), r.text
        if r.status_code == 200:
            sid = r.json().get("session_id")
            time.sleep(1)
            r2 = client.get(f"{BASE_URL}/api/commerce/transactions", timeout=60)
            match = [t for t in r2.json() if t.get("session_id") == sid]
            assert match, "txn not recorded"
            amt = float(match[0].get("amount", 0))
            assert amt < 10000, f"Client amount was honored! amount={amt}"


# ---------- WORKFLOW ----------
class TestWorkflowTemplates:
    def test_templates_and_stages(self, client):
        r = client.get(f"{BASE_URL}/api/workflow/templates", timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "templates" in data and "stages" in data
        assert len(data["templates"]) == 8, f"Expected 8 templates, got {len(data['templates'])}"
        assert len(data["stages"]) == 10, f"Expected 10 stages, got {len(data['stages'])}"


class TestWorkflowRun:
    def test_run_translation_workflow(self, client):
        r = client.post(f"{BASE_URL}/api/workflow/run",
                        json={"template": "Translation Workflow™", "topic": "Why hydration matters"},
                        timeout=60)
        assert r.status_code == 200, r.text
        job = r.json()
        assert "job_number" in job and job["job_number"].startswith("WF-"), f"bad job_number: {job}"
        assert job.get("status") in ("queued", "running"), f"bad status: {job.get('status')}"
        pytest._wf_job_id = job["id"]
        pytest._wf_job_number = job["job_number"]

    def test_poll_workflow_progress(self, client):
        job_id = getattr(pytest, "_wf_job_id", None)
        assert job_id, "No workflow job id"
        deadline = time.time() + 240  # 4 minutes
        last = None
        stage_names_seen = set()
        while time.time() < deadline:
            r = client.get(f"{BASE_URL}/api/workflow/jobs/{job_id}", timeout=60)
            assert r.status_code == 200, r.text
            j = r.json()
            last = j
            # structure asserts
            for k in ("job_number", "stage", "progress", "completed_tasks", "warnings",
                      "errors", "products", "retry_count", "est_cost_usd", "logs"):
                assert k in j, f"missing key {k} in job detail"
            for t in j.get("completed_tasks", []):
                stage_names_seen.add(t)
            if j.get("status") in ("completed", "completed_with_errors", "failed"):
                break
            time.sleep(6)
        assert last is not None
        # Not requiring completion but at least progress > 0 or some stages
        assert last.get("progress", 0) > 0 or len(stage_names_seen) > 0, \
            f"No progress observed: {last.get('progress')} tasks={stage_names_seen}"
        # log structure
        if last.get("logs"):
            l0 = last["logs"][0]
            for k in ("stage", "division", "message"):
                assert k in l0, f"log missing {k}: {l0}"
        pytest._wf_final = last
        print(f"Final status: {last.get('status')} progress: {last.get('progress')} products: {len(last.get('products', []))}")


class TestMonitor:
    def test_factory_monitor_structure(self, client):
        r = client.get(f"{BASE_URL}/api/workflow/monitor", timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("jobs", "health", "estimated_production_cost_usd", "cost_label",
                  "revenue", "ai_usage", "division_activity"):
            assert k in d, f"monitor missing {k}"
        assert d["cost_label"] == "Estimated"
        for k in ("running", "waiting", "completed", "escalated", "total"):
            assert k in d["jobs"], f"jobs missing {k}"
        for k in ("factory_health", "automation_success_pct", "founder_intervention_pct",
                  "treasure_compliance_pct", "knowledge_health"):
            assert k in d["health"], f"health missing {k}"


# ---------- ENTERPRISE FAT ----------
class TestFAT:
    def test_enterprise_fat_score(self, client):
        r = client.get(f"{BASE_URL}/api/enterprise/factory-acceptance-test", timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("enterprise_quality_score") == 100, f"EQS={d.get('enterprise_quality_score')}"
        modules = d.get("modules", [])
        analytics = next((m for m in modules if "Analytics" in (m.get("name") or m.get("module", ""))), None)
        assert analytics is not None, f"analytics module not found: {[m.get('name') or m.get('module') for m in modules]}"
        assert analytics.get("score") == 100, f"analytics score={analytics.get('score')}"

    def test_fat_workflow_launch(self, client):
        r = client.post(f"{BASE_URL}/api/workflow/factory-acceptance-test", timeout=60)
        assert r.status_code == 200, r.text
        job = r.json()
        assert "job_number" in job
        # is_fat may be set immediately or after run starts — verify via GET
        pytest._fat_job_id = job["id"]
        time.sleep(2)
        r2 = client.get(f"{BASE_URL}/api/workflow/factory-acceptance-test/{job['id']}", timeout=60)
        assert r2.status_code == 200, r2.text
        eval_ = r2.json()
        for k in ("score", "checks", "acceptance", "defects"):
            assert k in eval_, f"FAT eval missing {k}"
        assert eval_["acceptance"] in ("PASS", "IN PROGRESS / REVIEW", "IN PROGRESS", "REVIEW"), \
            f"unexpected acceptance: {eval_['acceptance']}"

    def test_fat_job_detail_is_fat(self, client):
        job_id = getattr(pytest, "_fat_job_id", None)
        assert job_id
        r = client.get(f"{BASE_URL}/api/workflow/jobs/{job_id}", timeout=60)
        assert r.status_code == 200
        j = r.json()
        assert j.get("is_fat") is True, f"expected is_fat=True, got {j.get('is_fat')}"


# ---------- MEDIA ASSET SERVING ----------
class TestMediaAssets:
    def test_asset_served_if_present(self, client):
        # Look at recent workflow_jobs for any product with asset_url matching rendering/asset/
        r = client.get(f"{BASE_URL}/api/workflow/jobs?limit=30", timeout=60)
        assert r.status_code == 200
        jobs = r.json()
        found = None
        for j in jobs:
            for p in j.get("products", []) or []:
                url = p.get("asset_url") or ""
                if "/api/rendering/asset/" in url and (url.endswith(".mp3") or url.endswith(".mp4")):
                    found = url
                    break
            if found:
                break
        if not found:
            pytest.skip("No media asset with /api/rendering/asset/*.mp3|.mp4 found yet — real media generation not observed in recent jobs")
        # Fetch — url may be relative
        full_url = found if found.startswith("http") else f"{BASE_URL}{found}"
        r2 = requests.get(full_url, timeout=60, headers={"Authorization": client.headers.get("Authorization", "")})
        assert r2.status_code == 200, f"asset fetch failed: {r2.status_code} {full_url}"
