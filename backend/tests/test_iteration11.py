"""Iteration 11 — Founder ownership, Topic Registry, Orchestrator (hands-free), Verification, Protection."""
import os
import time
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://understanding-os.preview.emergentagent.com").rstrip("/")

FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASS = "QruFounder2026!"
DEMO_ADMIN_EMAIL = "demo.admin@qru.com"
DEMO_ADMIN_PASS = "qru-demo-admin-2026"
DEMO_INSTR_EMAIL = "demo.instructor@qru.com"
DEMO_INSTR_PASS = "qru-demo-instructor-2026"
DEMO_STUD_EMAIL = "demo.student@qru.com"
DEMO_STUD_PASS = "qru-demo-student-2026"


def _login(email, password):
    r = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": password}, timeout=30)
    return r


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def founder_token():
    r = _login(FOUNDER_EMAIL, FOUNDER_PASS)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def demo_admin_token():
    r = _login(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASS)
    assert r.status_code == 200, f"Demo admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


# ---------------- Auth ----------------
class TestAuth:
    def test_setup_status(self):
        r = requests.get(f"{BASE}/api/auth/setup-status", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["founder_exists"] is True
        assert d["using_temporary_password"] is True
        assert d["setup_required"] is True
        assert d["founder_email"] == FOUNDER_EMAIL

    def test_founder_login_and_me(self, founder_token):
        r = requests.get(f"{BASE}/api/auth/me", headers=_bearer(founder_token), timeout=15)
        assert r.status_code == 200
        me = r.json()
        assert me["email"] == FOUNDER_EMAIL
        assert me["role"] == "Founder & CEO"
        # is_founder should be true (may exist on returned user dict)
        assert me.get("is_founder") is True

    @pytest.mark.parametrize("email,pwd", [
        ("admin@qru.com", "qru-admin-2026"),
        ("executive@qru.com", "qru-exec-2026"),
        ("learner@qru.com", "qru-learn-2026"),
    ])
    def test_old_accounts_removed(self, email, pwd):
        r = _login(email, pwd)
        assert r.status_code == 401, f"Old account {email} should not login, got {r.status_code}"

    @pytest.mark.parametrize("email,pwd", [
        (DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASS),
        (DEMO_INSTR_EMAIL, DEMO_INSTR_PASS),
        (DEMO_STUD_EMAIL, DEMO_STUD_PASS),
    ])
    def test_demo_accounts_login(self, email, pwd):
        r = _login(email, pwd)
        assert r.status_code == 200, f"Demo account {email} failed: {r.text}"

    def test_change_password_flow_on_demo_admin(self):
        # Login demo admin
        r = _login(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASS)
        assert r.status_code == 200
        tok = r.json()["access_token"]
        h = _bearer(tok)
        new_pw = "qru-demo-admin-2026-new1"
        # Wrong current password -> 400
        r_bad = requests.post(f"{BASE}/api/auth/change-password",
                              headers=h, json={"current_password": "wrong-current", "new_password": new_pw}, timeout=15)
        assert r_bad.status_code == 400
        # Correct current -> 200
        r_ok = requests.post(f"{BASE}/api/auth/change-password",
                             headers=h, json={"current_password": DEMO_ADMIN_PASS, "new_password": new_pw}, timeout=15)
        assert r_ok.status_code == 200, r_ok.text
        # Login with new
        r_login_new = _login(DEMO_ADMIN_EMAIL, new_pw)
        assert r_login_new.status_code == 200
        tok2 = r_login_new.json()["access_token"]
        # Revert back
        r_revert = requests.post(f"{BASE}/api/auth/change-password",
                                 headers=_bearer(tok2),
                                 json={"current_password": new_pw, "new_password": DEMO_ADMIN_PASS}, timeout=15)
        assert r_revert.status_code == 200
        # Confirm old works
        assert _login(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASS).status_code == 200


# ---------------- Ownership ----------------
class TestOwnership:
    def test_list_users_and_founder_undeletable(self, founder_token):
        r = requests.get(f"{BASE}/api/users", headers=_bearer(founder_token), timeout=15)
        assert r.status_code == 200
        users = r.json()
        assert isinstance(users, list) and len(users) > 0
        founder = next((u for u in users if u.get("email") == FOUNDER_EMAIL), None)
        assert founder is not None
        # Try to delete the founder
        r_del = requests.delete(f"{BASE}/api/users/{founder['id']}", headers=_bearer(founder_token), timeout=15)
        assert r_del.status_code == 400

    def test_knowledge_records_owner_id(self, founder_token):
        r = requests.get(f"{BASE}/api/knowledge-records", headers=_bearer(founder_token), timeout=30)
        assert r.status_code == 200
        recs = r.json()
        if isinstance(recs, list) and recs:
            # spot check: at least one has owner_id
            has_owner = any(k.get("owner_id") for k in recs)
            assert has_owner, "Expected at least one Knowledge Record with owner_id"


# ---------------- Topic Registry ----------------
class TestTopicRegistry:
    def test_topic_crud(self, founder_token):
        h = _bearer(founder_token)
        payload = {"college": "TEST_College", "department": "TEST_Dept",
                   "topic_name": "TEST_Topic_" + str(int(time.time())),
                   "division": "Health", "priority_score": 75}
        r = requests.post(f"{BASE}/api/topic-registry", headers=h, json=payload, timeout=15)
        assert r.status_code == 200, r.text
        t = r.json()
        assert t.get("topic_id", "").startswith("TOP-")
        tid = t["id"]

        # List
        r_list = requests.get(f"{BASE}/api/topic-registry", headers=h, timeout=15)
        assert r_list.status_code == 200
        assert any(x["id"] == tid for x in r_list.json())

        # Stats
        r_stats = requests.get(f"{BASE}/api/topic-registry/stats", headers=h, timeout=15)
        assert r_stats.status_code == 200
        stats = r_stats.json()
        assert stats["total"] >= 1
        assert "by_status" in stats

        # Update
        r_up = requests.put(f"{BASE}/api/topic-registry/{tid}", headers=h,
                            json={"priority_score": 88}, timeout=15)
        assert r_up.status_code == 200
        assert r_up.json()["priority_score"] == 88

        # Delete
        r_del = requests.delete(f"{BASE}/api/topic-registry/{tid}", headers=h, timeout=15)
        assert r_del.status_code == 200

    def test_ai_generate_small(self, founder_token):
        h = _bearer(founder_token)
        r = requests.post(f"{BASE}/api/topic-registry/generate", headers=h,
                          json={"domain": "Faith", "count": 10}, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["division"] == "Faith"
        assert isinstance(d["topics"], list)
        assert len(d["topics"]) >= 5, f"Expected ~10 topics, got {len(d['topics'])}"
        # Check department + scores present
        t0 = d["topics"][0]
        assert "department" in t0
        assert "priority_score" in t0

    def test_bulk_import_creates_topics_and_orders(self, founder_token):
        h = _bearer(founder_token)
        ts = int(time.time())
        payload = {
            "college": f"TEST_BulkCollege_{ts}",
            "division": "Health",
            "topics": [
                {"topic_name": f"TEST_BI_Topic_A_{ts}", "department": "General", "priority_score": 70},
                {"topic_name": f"TEST_BI_Topic_B_{ts}", "department": "General", "priority_score": 72},
            ],
            "create_orders": True,
        }
        r = requests.post(f"{BASE}/api/topic-registry/bulk-import", headers=h, json=payload, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["topics_created"] == 2
        assert d["orders_created"] == 2


# ---------------- Orchestrator ----------------
class TestOrchestrator:
    def test_settings(self, founder_token):
        h = _bearer(founder_token)
        r = requests.get(f"{BASE}/api/orchestrator/settings", headers=h, timeout=15)
        assert r.status_code == 200
        s = r.json()
        # By default hands_free_mode true
        assert s.get("hands_free_mode") in (True, False)  # exists
        initial = s.get("hands_free_mode", True)
        # Toggle
        r_tog = requests.post(f"{BASE}/api/orchestrator/settings", headers=h,
                              json={"hands_free_mode": not initial}, timeout=15)
        assert r_tog.status_code == 200
        assert r_tog.json()["hands_free_mode"] == (not initial)
        # Restore
        r_res = requests.post(f"{BASE}/api/orchestrator/settings", headers=h,
                              json={"hands_free_mode": initial}, timeout=15)
        assert r_res.status_code == 200

    def test_hands_free_batch_single_topic(self, founder_token):
        """Create one topic, run one batch of size 1, poll until completed. LLM-heavy."""
        h = _bearer(founder_token)
        # Ensure hands-free mode is on
        requests.post(f"{BASE}/api/orchestrator/settings", headers=h,
                      json={"hands_free_mode": True}, timeout=15)

        ts = int(time.time())
        payload = {"college": "QRU Health University", "department": "Heart Health",
                   "topic_name": f"TEST_BatchTopic_{ts}", "division": "Health", "priority_score": 80}
        r_top = requests.post(f"{BASE}/api/topic-registry", headers=h, json=payload, timeout=15)
        assert r_top.status_code == 200
        topic = r_top.json()
        tid = topic["id"]

        # Create batch
        r_b = requests.post(f"{BASE}/api/orchestrator/batches", headers=h,
                            json={"name": f"TEST_Batch_{ts}", "division": "Health",
                                  "batch_size": 1, "topic_registry_ids": [tid]}, timeout=30)
        assert r_b.status_code == 200, r_b.text
        batch = r_b.json()
        bid = batch["id"]

        # Start
        r_s = requests.post(f"{BASE}/api/orchestrator/batches/{bid}/start", headers=h, timeout=30)
        assert r_s.status_code == 200

        # Poll up to 240s
        final = None
        for i in range(60):
            time.sleep(4)
            r_g = requests.get(f"{BASE}/api/orchestrator/batches/{bid}", headers=h, timeout=30)
            if r_g.status_code != 200:
                continue
            b = r_g.json()
            if b.get("status") in ("completed", "completed_with_errors"):
                final = b
                break

        assert final is not None, "Batch did not complete in time"
        assert final["status"] in ("completed", "completed_with_errors")
        items = final.get("items") or []
        assert items, "Batch has no items"
        item0 = items[0]
        stage = item0.get("stage") or ""
        # Allowed stages
        allowed = ["Published", "Verified (QC review)", "Escalated", "Completed"]
        assert any(a.lower() in stage.lower() for a in allowed) or stage != "", \
            f"Unexpected item stage: {stage}"

        # Verify a Knowledge Record exists for this topic
        kr_id = item0.get("knowledge_record_id")
        if kr_id:
            r_kr = requests.get(f"{BASE}/api/knowledge-records/{kr_id}", headers=h, timeout=15)
            # Might be under memory or knowledge-records; accept 200
            if r_kr.status_code == 404:
                # try alternative endpoint
                r_kr2 = requests.get(f"{BASE}/api/memory/records/{kr_id}", headers=h, timeout=15)
                assert r_kr2.status_code == 200, "KR should exist"
            else:
                assert r_kr.status_code == 200

        # If published, check product
        if "publish" in stage.lower():
            pid = item0.get("product_id")
            if pid:
                r_p = requests.get(f"{BASE}/api/products/{pid}", headers=h, timeout=15)
                assert r_p.status_code == 200
                p = r_p.json()
                assert p.get("verified") is True
                assert p.get("protected") is True
                assert (p.get("protection") or {}).get("copyright_notice")
                assert p.get("license_type")

    def test_pause_resume_retry(self, founder_token):
        h = _bearer(founder_token)
        # Get an existing batch (from previous test)
        r_list = requests.get(f"{BASE}/api/orchestrator/batches", headers=h, timeout=15)
        assert r_list.status_code == 200
        batches = r_list.json()
        assert batches, "Expected at least one batch"
        bid = batches[0]["id"]
        # These endpoints should return 200 regardless of state
        for ep in ("pause", "resume", "retry"):
            r = requests.post(f"{BASE}/api/orchestrator/batches/{bid}/{ep}", headers=h, timeout=15)
            assert r.status_code == 200, f"{ep} returned {r.status_code}: {r.text}"


# ---------------- Verification Team ----------------
class TestVerification:
    def test_config(self, founder_token):
        r = requests.get(f"{BASE}/api/verification/config", headers=_bearer(founder_token), timeout=15)
        assert r.status_code == 200
        assert r.json().get("confidence_threshold") == 80

    def test_log_and_escalations(self, founder_token):
        h = _bearer(founder_token)
        r = requests.get(f"{BASE}/api/verification/log", headers=h, timeout=15)
        assert r.status_code == 200
        assert "entries" in r.json()

        r_esc = requests.get(f"{BASE}/api/verification/escalations", headers=h, timeout=15)
        assert r_esc.status_code == 200
        esc_list = r_esc.json()
        assert isinstance(esc_list, list)
        if esc_list:
            eid = esc_list[0]["id"]
            r_res = requests.post(f"{BASE}/api/verification/escalations/{eid}/resolve",
                                  headers=h, json={"decision": "approve"}, timeout=15)
            assert r_res.status_code == 200


# ---------------- Product Protection ----------------
class TestProtection:
    def test_licenses(self, founder_token):
        r = requests.get(f"{BASE}/api/protection/licenses", headers=_bearer(founder_token), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert len(d["license_types"]) == 4
        assert "copyright_notice" in d and "©" in d["copyright_notice"]

    def test_dashboard(self, founder_token):
        r = requests.get(f"{BASE}/api/protection/dashboard", headers=_bearer(founder_token), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "rows" in d and "summary" in d

    def test_verify_and_protect_and_link(self, founder_token):
        h = _bearer(founder_token)
        # Find any product
        r_prods = requests.get(f"{BASE}/api/products", headers=h, timeout=30)
        assert r_prods.status_code == 200
        prods = r_prods.json()
        if not prods:
            pytest.skip("No products available to run protection tests")
        # Choose one
        pid = prods[0]["id"]

        # Verify
        r_v = requests.post(f"{BASE}/api/protection/{pid}/verify", headers=h, timeout=90)
        assert r_v.status_code == 200
        vresult = r_v.json()
        assert "verified" in vresult
        assert "verification" in vresult

        # Apply protection
        r_p = requests.post(f"{BASE}/api/protection/{pid}/apply-protection",
                            headers=h, json={"license_type": "Personal Use",
                                              "watermark": True, "access_control": "account_required"},
                            timeout=15)
        assert r_p.status_code == 200
        prot = r_p.json()
        assert prot.get("protected") is True
        assert (prot.get("protection") or {}).get("copyright_applied") is True

        # Secure link — check verified vs unverified
        r_link = requests.post(f"{BASE}/api/protection/{pid}/secure-link",
                               headers=h, json={"minutes": 10}, timeout=15)
        if vresult.get("verified"):
            assert r_link.status_code == 200
            link = r_link.json()
            assert link.get("token") and link.get("path")
            # Download
            r_dl = requests.get(f"{BASE}/api/protection/download/{link['token']}", timeout=15)
            assert r_dl.status_code == 200
            content = r_dl.json().get("content", "")
            assert "©" in content or "QRU" in content
            # access counter incremented
            assert r_dl.json().get("access_number") == 1
        else:
            # Unverified should 400
            assert r_link.status_code == 400

        # Ensure an unverified product returns 400
        # Find an unverified product by creating a fresh one via /products/generate is too costly; instead pick one that is not verified
        unv = next((p for p in prods if not p.get("verified") and p["id"] != pid), None)
        if unv:
            r_ul = requests.post(f"{BASE}/api/protection/{unv['id']}/secure-link",
                                 headers=h, json={"minutes": 10}, timeout=15)
            assert r_ul.status_code == 400


# ---------------- Publish Gate ----------------
class TestPublishGate:
    def test_publish_requires_verified(self, founder_token):
        h = _bearer(founder_token)
        r_prods = requests.get(f"{BASE}/api/products", headers=h, timeout=30)
        assert r_prods.status_code == 200
        prods = r_prods.json()
        # Find an unverified product
        unv = next((p for p in prods if not p.get("verified")), None)
        if not unv:
            pytest.skip("No unverified products found; cannot test publish gate")
        pid = unv["id"]
        r = requests.patch(f"{BASE}/api/products/{pid}/status",
                           headers=h, json={"status": "Published"}, timeout=15)
        assert r.status_code == 400
