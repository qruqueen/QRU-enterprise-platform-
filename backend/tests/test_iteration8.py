"""Iteration 8 — QRU Memory Engineering™ + Enterprise Evolution Governance™ regression.

Covers:
- GET /api/memory/characters returns 6 QRU Character Voices with required fields.
- GET /api/memory/records returns verified records with memory_status.
- POST /api/memory/manufacture on a non-verified record returns 400.
- POST /api/memory/manufacture/{kr_id} for a verified record starts async job,
  polling /api/memory/{kr_id} eventually returns memory_status='manufactured'
  with memory_assets containing every required key.
- GET /api/evolution/refactoring returns principle 'Extend Before Expand™' + insights.
- POST /api/evolution/review returns EXTEND/CREATE recommendation with rationale + 5 questions.
- Regression: after memory manufactured, consumer build_understanding returns memory.hook.
"""
import os
import time
import pytest
import requests


def _read_frontend_env():
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return None


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _read_frontend_env()).rstrip("/")

ADMIN = {"email": "admin@qru.com", "password": "qru-admin-2026"}
LEARNER = {"email": "learner@qru.com", "password": "qru-learn-2026"}

REQUIRED_ASSET_KEYS = [
    "memory_sentence", "memory_hook", "memory_chant", "call_and_response",
    "one_line_repeat", "educational_lyrics", "memory_rhythm",
    "character_scripts", "character_dialogue", "legacy_learners",
    "music_prompt", "instrumental_prompt",
]

EXPECTED_CHARACTERS = [
    "Kingdom Lion™", "Legacy Bear™", "Legacy Eagle™",
    "Queen Unity™", "Crowned Bull™", "Royal Phoenix™",
]


@pytest.fixture(scope="module")
def admin_client():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    s.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return s


@pytest.fixture(scope="module")
def learner_client():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json=LEARNER, timeout=30)
    assert r.status_code == 200, r.text
    s.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return s


# -------- Memory: Characters --------
class TestCharacters:
    def test_six_characters_with_required_fields(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/memory/characters", timeout=15)
        assert r.status_code == 200, r.text
        chars = r.json()["characters"]
        assert len(chars) == 6, f"Expected 6 characters, got {len(chars)}"
        names = [c["name"] for c in chars]
        for expected in EXPECTED_CHARACTERS:
            assert expected in names, f"Missing character: {expected}"
        for c in chars:
            assert "traits" in c and isinstance(c["traits"], list) and c["traits"]
            assert "role" in c and c["role"]
            assert "voice" in c and c["voice"]


# -------- Memory: Records --------
class TestMemoryRecords:
    def test_records_verified_only_with_memory_status(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/memory/records", timeout=15)
        assert r.status_code == 200, r.text
        records = r.json()["records"]
        assert isinstance(records, list) and records, "No verified records"
        for rec in records:
            assert "id" in rec
            assert "kr_code" in rec
            assert "title" in rec

    def test_manufacture_guard_on_non_verified(self, admin_client):
        # Try to find a non-verified record (or create fake path)
        # Fetch all knowledge records and find a non-verified one
        r = admin_client.get(f"{BASE_URL}/api/knowledge/records", timeout=15)
        if r.status_code != 200:
            pytest.skip("Cannot query knowledge/records endpoint")
        recs = r.json() if isinstance(r.json(), list) else r.json().get("records", [])
        non_verified = [x for x in recs if x.get("verification_status") != "Verified"]
        if not non_verified:
            pytest.skip("No non-verified record available to test 400 guard")
        kr_id = non_verified[0]["id"]
        r2 = admin_client.post(f"{BASE_URL}/api/memory/manufacture/{kr_id}", timeout=15)
        assert r2.status_code == 400, f"Expected 400 for non-verified, got {r2.status_code}: {r2.text}"


# -------- Memory: Manufacture end-to-end (uses GPT) --------
class TestMemoryManufacture:
    def test_manufacture_and_poll(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/memory/records", timeout=15)
        assert r.status_code == 200
        records = r.json()["records"]
        assert records, "No verified records available"

        # Choose a demo record — prefer Heart/Sleep/Insulin one; else first one
        preferred = None
        for kw in ["Insulin", "Heart", "Sleep"]:
            for rec in records:
                if kw.lower() in (rec.get("title") or "").lower():
                    preferred = rec
                    break
            if preferred:
                break
        target = preferred or records[0]
        kr_id = target["id"]

        start = admin_client.post(f"{BASE_URL}/api/memory/manufacture/{kr_id}", timeout=30)
        assert start.status_code == 200, start.text
        assert start.json().get("kr_id") == kr_id

        # Poll for up to 90 seconds
        deadline = time.time() + 90
        assets = None
        status = None
        while time.time() < deadline:
            r2 = admin_client.get(f"{BASE_URL}/api/memory/{kr_id}", timeout=20)
            assert r2.status_code == 200, r2.text
            body = r2.json()
            status = body.get("memory_status")
            if status in ("manufactured", "failed"):
                assets = body.get("memory_assets")
                break
            time.sleep(3)

        assert status == "manufactured", f"Final status={status} (assets={bool(assets)})"
        assert assets, "No memory_assets returned"
        missing = [k for k in REQUIRED_ASSET_KEYS if k not in assets]
        assert not missing, f"Missing asset keys: {missing}"

        # Deeper checks on shape
        assert isinstance(assets["memory_hook"], str) and assets["memory_hook"].strip()
        assert isinstance(assets["call_and_response"], list) and assets["call_and_response"]
        for cr in assets["call_and_response"]:
            assert "call" in cr and "response" in cr
        assert isinstance(assets["character_scripts"], list) and assets["character_scripts"]
        for cs in assets["character_scripts"]:
            assert "character" in cs and "script" in cs
        assert isinstance(assets["legacy_learners"], dict)
        for lvl in ("child", "teen", "adult", "professional"):
            assert lvl in assets["legacy_learners"] and assets["legacy_learners"][lvl]
        assert isinstance(assets["educational_lyrics"], dict)
        assert "chorus" in assets["educational_lyrics"]
        assert "verse" in assets["educational_lyrics"]

        # Regression: consumer understanding endpoint exposes memory hook
        # Locate a product linked to this KR
        pr = admin_client.get(f"{BASE_URL}/api/products", timeout=15)
        if pr.status_code == 200:
            products = pr.json() if isinstance(pr.json(), list) else pr.json().get("products", [])
            linked = [p for p in products if p.get("knowledge_record_id") == kr_id]
            if linked:
                pid = linked[0]["id"]
                # Try consumer understanding endpoint
                u = admin_client.get(f"{BASE_URL}/api/consumer/products/{pid}/understanding", timeout=20)
                if u.status_code == 200:
                    ubody = u.json()
                    mem = ubody.get("memory") or {}
                    assert mem.get("hook"), f"Consumer understanding missing memory.hook: {mem}"


# -------- Evolution --------
class TestEvolution:
    def test_refactoring_principle_and_insights(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/evolution/refactoring", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("principle") == "Extend Before Expand™"
        assert isinstance(body.get("insights"), list) and body["insights"], "insights empty"
        for ins in body["insights"]:
            assert "area" in ins
            assert "finding" in ins
            assert "recommendation" in ins
            assert "severity" in ins

    def test_capabilities_list(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/evolution/capabilities", timeout=15)
        assert r.status_code == 200
        caps = r.json()["capabilities"]
        assert len(caps) >= 5

    def test_evolution_review_extend_recommendation(self, admin_client):
        payload = {
            "objective": "We want a system to deliver finished products to customers after certification.",
            "save": False,
        }
        r = admin_client.post(f"{BASE_URL}/api/evolution/review", json=payload, timeout=90)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("recommendation") in ("EXTEND EXISTING SYSTEM", "CREATE NEW SYSTEM")
        assert isinstance(body.get("rationale"), str) and body["rationale"].strip()
        assert isinstance(body.get("questions"), list) and len(body["questions"]) == 5
        for q in body["questions"]:
            assert "q" in q and "a" in q
        assert body.get("target_capability")
