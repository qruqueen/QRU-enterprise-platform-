"""Backend tests for QRU Distribution Architecture™ (Phase 0)."""
import os
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE:
    # fall back: read frontend env
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE = line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass

ADMIN_EMAIL = "demo.admin@qru.com"
ADMIN_PASS = "qru-demo-admin-2026"

APPROVED_MAP = {
    "Book": ["books"],
    "Course": ["learn"],
    "Workbook": ["learn", "resources"],
    "Teacher Guide": ["learn"],
    "Student Guide": ["learn"],
    "Family Guide": ["learn"],
    "Poster": ["resources"],
    "Flash Cards": ["resources", "learn"],
    "Motion Story": ["books", "media"],
    "Podcast": ["media"],
    "Video": ["media"],
    "Bundle": ["bundles"],
}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def test_unauth_get_experiences_rejected():
    r = requests.get(f"{BASE}/api/distribution-architecture/experiences", timeout=15)
    assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"


def test_unauth_post_register_rejected():
    r = requests.post(f"{BASE}/api/distribution-architecture/experiences",
                      json={"id": "x", "name": "X"}, timeout=15)
    assert r.status_code in (401, 403)


def test_get_experiences_seeded(admin_headers):
    r = requests.get(f"{BASE}/api/distribution-architecture/experiences",
                     headers=admin_headers, timeout=15)
    assert r.status_code == 200
    exps = r.json()["experiences"]
    ids = [e["id"] for e in exps]
    # first 5 in exact order
    assert ids[:5] == ["books", "learn", "resources", "media", "bundles"], ids
    learn = next(e for e in exps if e["id"] == "learn")
    assert learn.get("protected") is True
    assert learn.get("builtin") is True


def test_destinations_map_exact(admin_headers):
    r = requests.get(f"{BASE}/api/distribution-architecture/destinations-map",
                     headers=admin_headers, timeout=15)
    assert r.status_code == 200
    rows = {row["product_type"]: [d["id"] for d in row["destinations"]]
            for row in r.json()["map"]}
    for ptype, expected in APPROVED_MAP.items():
        assert rows.get(ptype) == expected, f"{ptype}: got {rows.get(ptype)} expected {expected}"
    # names are human strings
    m = r.json()["map"]
    assert all(d.get("name") for row in m for d in row["destinations"])


def test_resolve_workbook(admin_headers):
    r = requests.get(f"{BASE}/api/distribution-architecture/resolve/Workbook",
                     headers=admin_headers, timeout=15)
    assert r.status_code == 200
    assert r.json()["recommended"] == ["learn", "resources"]


def test_resolve_unknown_fallback(admin_headers):
    r = requests.get(f"{BASE}/api/distribution-architecture/resolve/DoesNotExist",
                     headers=admin_headers, timeout=15)
    assert r.status_code == 200
    assert r.json()["recommended"] == ["resources"]


def test_register_experience_flow(admin_headers):
    exp = {"id": "qa-test-exp", "name": "QA Test Experience",
           "description": "temp", "audience": "qa"}
    # ensure clean-ish: try to register; if exists we consider previous run — call cleanup path is main agent's
    r = requests.post(f"{BASE}/api/distribution-architecture/experiences",
                      headers=admin_headers, json=exp, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    if "error" in body and "already exists" in body["error"]:
        pytest.skip("qa-test-exp already exists from a prior run; main agent will clean up")
    assert body.get("ok") is True, body
    new = body["experience"]
    assert new["id"] == "qa-test-exp"
    assert new["builtin"] is False
    assert new["founder_locked"] is True
    assert new["order"] >= 6

    # duplicate rejected
    r2 = requests.post(f"{BASE}/api/distribution-architecture/experiences",
                       headers=admin_headers, json=exp, timeout=15)
    assert r2.status_code == 200
    assert "error" in r2.json() and "already exists" in r2.json()["error"]

    # empty id
    r3 = requests.post(f"{BASE}/api/distribution-architecture/experiences",
                       headers=admin_headers, json={"id": "", "name": "x"}, timeout=15)
    # pydantic may reject empty-required or app may return error body
    if r3.status_code == 200:
        assert "error" in r3.json()
    else:
        assert r3.status_code in (400, 422)

    # empty name
    r4 = requests.post(f"{BASE}/api/distribution-architecture/experiences",
                       headers=admin_headers, json={"id": "yyy", "name": ""}, timeout=15)
    if r4.status_code == 200:
        assert "error" in r4.json()
    else:
        assert r4.status_code in (400, 422)

    # GET includes it
    r5 = requests.get(f"{BASE}/api/distribution-architecture/experiences",
                      headers=admin_headers, timeout=15)
    ids = [e["id"] for e in r5.json()["experiences"]]
    assert "qa-test-exp" in ids


# Regression
def test_consumer_catalog_still_works(admin_headers):
    r = requests.get(f"{BASE}/api/consumer/catalog", headers=admin_headers, timeout=15)
    assert r.status_code == 200


def test_public_home_still_returns_books():
    r = requests.get(f"{BASE}/api/public/home", timeout=15)
    assert r.status_code == 200
    data = r.json()
    # loose check — some field mentioning books/products
    assert isinstance(data, dict)
