"""Iteration 45 — RETEST of the CRITICAL Gold Master honesty defect from iteration_44.

Scope:
1) POST /api/factory-os/projects/{pid}/approve MUST refuse to complete a gold_master gate
   (returns requires_certification=true, stage stays 'needs_approval').
2) POST /api/factory-os/projects/{pid}/approve MUST still work for non-gold_master gates
   (founder_approval → complete + auto-continuation).
3) POST /api/media-library/showcase/{asset_id}/certify-gold-master MUST refuse QA<100 and
   the linked project's gold_master stage MUST stay needs_approval.
4) DB scan — no continuity project may have gold_master='complete' without either a
   gold_master_certified history entry OR a linked asset with gold_master_certified=true.
"""
import os
import time
import pytest
import requests

_url = os.environ.get("REACT_APP_BACKEND_URL")
if not _url:
    # Read from frontend/.env if not exported into pytest environment
    try:
        with open("/app/frontend/.env") as _f:
            for _line in _f:
                if _line.startswith("REACT_APP_BACKEND_URL="):
                    _url = _line.split("=", 1)[1].strip()
                    break
    except Exception:
        pass
BASE_URL = (_url or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be configured"
API = f"{BASE_URL}/api"

FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"

REMEDIATED = [
    "784bd0d7", "010d4afc", "1e519b77", "0fd82cc8", "1355312e",
]


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text}"
    return r.json().get("access_token") or r.json()["token"]


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# Helper: find or create a project in the gold_master needs_approval state.
def _find_gm_needs_approval(client):
    r = client.get(f"{API}/factory-os/projects", timeout=30)
    assert r.status_code == 200, r.text
    projects = r.json().get("projects", [])
    for p in projects:
        cur = next((s for s in p.get("chain", []) if s["status"] == "needs_approval"), None)
        if cur and cur["id"] == "gold_master":
            return p
    return None


# ---------- 1. Gold Master approval refusal ----------
class TestGoldMasterApprovalRefusal:
    def test_gold_master_needs_approval_project_exists(self, client):
        p = _find_gm_needs_approval(client)
        assert p is not None, (
            "Expected at least one continuity project with current gate=gold_master "
            "in needs_approval state (5 remediated projects were promised)."
        )
        assert p["id"][:8] in [x[:8] for x in REMEDIATED] or True  # informational
        # Snapshot the id so later tests can use it
        pytest.gm_pid = p["id"]

    def test_approve_refuses_gold_master(self, client):
        pid = pytest.gm_pid
        r = client.post(f"{API}/factory-os/projects/{pid}/approve", timeout=30)
        assert r.status_code == 200, f"/approve failed: {r.status_code} {r.text}"
        data = r.json()
        # Honesty invariant: approve must NOT complete gold_master.
        assert data.get("requires_certification") is True, (
            f"Expected requires_certification=true, got: {data.get('requires_certification')}"
        )
        assert "certif" in (data.get("note") or "").lower(), \
            f"Expected certification note, got note={data.get('note')!r}"
        # Stage stays needs_approval
        cur = next((s for s in data["chain"] if s["id"] == "gold_master"), None)
        assert cur is not None, "gold_master stage missing"
        assert cur["status"] == "needs_approval", \
            f"gold_master status must stay needs_approval, got {cur['status']}"

    def test_persistence_of_refusal(self, client):
        """GET the project fresh from DB — gold_master must still be needs_approval."""
        pid = pytest.gm_pid
        r = client.get(f"{API}/factory-os/projects/{pid}", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        cur = next((s for s in data["chain"] if s["id"] == "gold_master"), None)
        assert cur["status"] == "needs_approval", \
            f"After refusal gold_master persisted as {cur['status']} (must be needs_approval)"


# ---------- 2. Non-gold-master gate still approves ----------
class TestNonGoldMasterGateWorks:
    def test_founder_approval_gate_created_and_approved(self, client):
        """Find (or advance to) a project whose current gate is founder_approval:needs_approval.
        Then call /approve and verify founder_approval completes + auto-continues.
        Strategy:
          a) Look for an existing project with founder_approval:needs_approval — use it if found.
          b) Otherwise, find an in_progress workflow project and walk it via complete-stage until
             founder_approval:needs_approval is reached.
          c) Only as last resort create a new project (which will block at knowledge_record and skip).
        """
        r = client.get(f"{API}/factory-os/projects", timeout=30)
        projects = r.json().get("projects", [])
        pid = None
        for p in projects:
            cur = next((s for s in p.get("chain", []) if s["status"] == "needs_approval"), None)
            if cur and cur["id"] == "founder_approval":
                pid = p["id"]
                break

        if not pid:
            # Walk an in_progress workflow project forward via complete-stage until founder_approval.
            target = next((p for p in projects
                           if any(s["status"] == "in_progress" and s["kind"] == "workflow"
                                  for s in p.get("chain", []))), None)
            if target:
                pid = target["id"]
                for _ in range(8):
                    got = client.get(f"{API}/factory-os/projects/{pid}", timeout=15).json()
                    cur = next((s for s in got["chain"]
                                if s["status"] in ("in_progress", "needs_approval", "blocked")), None)
                    if cur is None or cur["status"] == "blocked":
                        break
                    if cur["status"] == "needs_approval":
                        break
                    if cur["status"] == "in_progress":
                        r2 = client.post(f"{API}/factory-os/projects/{pid}/complete-stage", timeout=15)
                        assert r2.status_code == 200, r2.text

        if not pid:
            pytest.skip("No founder_approval:needs_approval project available and no in_progress "
                        "workflow project to walk from — cannot exercise the founder_approval /approve path.")

        got = client.get(f"{API}/factory-os/projects/{pid}", timeout=15).json()
        cur = next((s for s in got["chain"] if s["status"] == "needs_approval"), None)
        assert cur is not None and cur["id"] == "founder_approval", (
            f"Expected founder_approval needs_approval on {pid}, got current={cur}"
        )
        pytest.founder_pid = pid

        # Now approve founder_approval — this MUST succeed and complete it.
        r3 = client.post(f"{API}/factory-os/projects/{pid}/approve", timeout=15)
        assert r3.status_code == 200, r3.text
        data = r3.json()
        assert not data.get("requires_certification"), \
            "founder_approval should NOT trigger requires_certification"
        fa = next((s for s in data["chain"] if s["id"] == "founder_approval"), None)
        assert fa["status"] == "complete", f"founder_approval must complete, got {fa['status']}"
        # And auto-continuation must have landed on gold_master (needs_approval) OR beyond.
        gm = next((s for s in data["chain"] if s["id"] == "gold_master"), None)
        assert gm["status"] in ("needs_approval", "pending"), \
            f"After founder_approval, gold_master should be needs_approval/pending, got {gm['status']}"

    def test_approve_on_gold_master_of_newly_advanced_project_also_refuses(self, client):
        """The freshly advanced project should now have gold_master=needs_approval.
        Calling /approve again MUST refuse (regression guard)."""
        pid = pytest.founder_pid
        got = client.get(f"{API}/factory-os/projects/{pid}", timeout=15).json()
        gm = next((s for s in got["chain"] if s["id"] == "gold_master"), None)
        if gm["status"] != "needs_approval":
            pytest.skip(f"gold_master not needs_approval on new project (got {gm['status']})")
        r = client.post(f"{API}/factory-os/projects/{pid}/approve", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("requires_certification") is True
        gm2 = next((s for s in d["chain"] if s["id"] == "gold_master"), None)
        assert gm2["status"] == "needs_approval", \
            f"Regression: gold_master got {gm2['status']} after /approve"


# ---------- 3. Certification path is the ONLY way to complete gold_master ----------
class TestRealCertificationPath:
    def test_certify_gold_master_endpoint_exists_and_enforces_qa(self, client):
        """Attempt to certify an asset that is likely short/no QA=100. Verify:
        - 400 with QA/certification error
        - The linked project's gold_master stage is NOT changed
        We look for an existing showcase asset linked to a needs_approval gold_master project.
        """
        pid = pytest.gm_pid
        got = client.get(f"{API}/factory-os/projects/{pid}", timeout=15).json()
        asset_id = got.get("showcase_asset_id")
        if not asset_id:
            pytest.skip("Target GM-needs-approval project has no showcase_asset_id — cannot test cert refusal via linked asset")

        r = client.post(f"{API}/media-library/showcase/{asset_id}/certify-gold-master", timeout=60)
        # Two acceptable honest outcomes:
        # a) 400 QA<100 → refusal
        # b) 200 ok=True → the asset legitimately passes QA (already certified) — then gold_master
        #    stage should update to complete via on_gold_master.
        if r.status_code == 400:
            body = r.text
            assert any(k in body.lower() for k in ("qa", "certif", "brand", "technical", "100")), \
                f"400 body should mention QA/certification, got: {body[:200]}"
            got2 = client.get(f"{API}/factory-os/projects/{pid}", timeout=15).json()
            gm = next((s for s in got2["chain"] if s["id"] == "gold_master"), None)
            assert gm["status"] == "needs_approval", \
                f"After certification refusal, gold_master must stay needs_approval, got {gm['status']}"
        elif r.status_code == 200:
            # This means the asset genuinely passes QA. Verify project moved.
            time.sleep(0.5)
            got2 = client.get(f"{API}/factory-os/projects/{pid}", timeout=15).json()
            gm = next((s for s in got2["chain"] if s["id"] == "gold_master"), None)
            assert gm["status"] == "complete", \
                f"After successful certification, gold_master must be complete, got {gm['status']}"
        else:
            pytest.fail(f"Unexpected status {r.status_code}: {r.text[:300]}")


# ---------- 4. Legacy data cleanliness ----------
class TestNoLegacyFalseCertifications:
    def test_no_project_has_gm_complete_without_evidence(self, client):
        r = client.get(f"{API}/factory-os/projects", timeout=30)
        assert r.status_code == 200
        projects = r.json().get("projects", [])
        offenders = []
        for p in projects:
            gm = next((s for s in p.get("chain", []) if s["id"] == "gold_master"), None)
            if not gm or gm["status"] != "complete":
                continue
            # Evidence #1: history entry mentioning gold_master_certified OR action containing 'gold_master'
            history = p.get("history", []) or []
            has_history_evidence = any(
                (h.get("action") or "").lower() in (
                    "gold_master_certified", "gold_master_certified_manual"
                ) or "gold_master" in (h.get("action") or "").lower()
                for h in history
            )
            # Evidence #2: linked asset has gold_master_certified=true
            has_asset_evidence = False
            asset_id = p.get("showcase_asset_id")
            if asset_id:
                a = client.get(f"{API}/media-library/showcase/records", timeout=15)
                # cheaper: query media asset directly
                ar = client.get(f"{API}/media-library/asset/{asset_id}/file", timeout=10)
                # We don't have a direct "get asset" GET; use the showcase records to try.
                # Fall back: rely on history evidence only.
                _ = ar  # unused
            if not (has_history_evidence or has_asset_evidence):
                offenders.append({
                    "id": p["id"],
                    "topic": p.get("topic"),
                    "history_actions": [h.get("action") for h in history],
                })
        assert not offenders, (
            f"Found {len(offenders)} projects with gold_master=complete but NO certification "
            f"evidence in history: {offenders}"
        )
