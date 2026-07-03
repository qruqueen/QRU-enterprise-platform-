"""MT-024 — Customer-Ready Deliverable Renderer backend tests.

Covers:
- POST /api/manufacturing2/{pid}/render-deliverable for Book/Presentation/Poster products
- GET /api/rendering/asset/{fname} — content-type + magic-byte validation
- GET /api/manufacturing2/{pid}/pipeline exposes customer_deliverable/deliverable_ready/cover_url/thumbnail_url
- POST /api/manufacturing2/{pid}/release publishes with published_deliverable snapshot; blocks on unmet gates
- Idempotency of render-deliverable
- 404 handling for unknown pid
"""
import os
import pytest
import requests


def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    env_path = "/app/frontend/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not set")


BASE_URL = _load_backend_url()

# Product IDs per the review request
BOOK_PID = "c4530d52-9286-458a-9104-48f4be38c08a"
PRESENTATION_PID = "a3a3326e-0046-4681-a13f-38f06ee8fa3a"
POSTER_PID = "f464e59c-e30c-47c7-9ab3-77a596e2a7bc"

LOGIN_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
LOGIN_PASSWORD = "QruFounder2026!"


# --------------------------------------------------------------------------- #
# Auth fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def auth_token(api_client):
    r = api_client.post(f"{BASE_URL}/api/auth/login",
                        json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Login failed ({r.status_code}): {r.text[:200]}")
    tok = r.json().get("token") or r.json().get("access_token")
    if not tok:
        pytest.skip("No token in login response")
    return tok


@pytest.fixture(scope="session")
def auth(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _assert_file_entry(fentry):
    assert "format" in fentry
    assert "label" in fentry
    assert "url" in fentry
    assert "media_type" in fentry
    assert "filename" in fentry
    assert "bytes" in fentry
    assert isinstance(fentry["bytes"], int)
    assert fentry["bytes"] >= 800, f"file too small: {fentry}"


def _fetch_asset(url, auth_headers, expected_media):
    # asset URL may be relative like /api/rendering/asset/... — normalize
    if url.startswith("http"):
        full = url
    else:
        full = f"{BASE_URL}{url}"
    # asset endpoint has no auth requirement, but pass token anyway - harmless
    r = requests.get(full, headers=auth_headers, timeout=30)
    assert r.status_code == 200, f"GET {full} failed: {r.status_code}"
    ctype = r.headers.get("content-type", "").split(";")[0].strip()
    assert ctype == expected_media, f"content-type mismatch for {full}: got {ctype} expected {expected_media}"
    assert len(r.content) >= 800, f"body too small for {full}: {len(r.content)} bytes"
    return r


# --------------------------------------------------------------------------- #
# render-deliverable across product types
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("pid,primary,expected_formats", [
    (BOOK_PID, "epub", {"html", "epub", "pdf"}),
    (PRESENTATION_PID, "pptx", {"html", "pptx", "pdf"}),
    (POSTER_PID, "png", {"html", "png"}),
])
def test_render_deliverable(api_client, auth, pid, primary, expected_formats):
    r = api_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/render-deliverable",
                        headers=auth, timeout=120)
    assert r.status_code == 200, f"render failed: {r.status_code} {r.text[:400]}"
    d = r.json()
    assert d.get("ready") is True, f"ready not true: {d.get('validation')}"
    assert d.get("primary_format") == primary, f"primary_format mismatch: {d.get('primary_format')}"
    assert d.get("preview_url"), "preview_url missing"
    assert d.get("preview_url").endswith(".html") or ".html" in d.get("preview_url", ""), \
        f"preview_url not html: {d.get('preview_url')}"
    assert d.get("download_url"), "download_url missing"
    files = d.get("files") or []
    assert files, "no files returned"
    formats_present = {f["format"] for f in files}
    assert expected_formats.issubset(formats_present), \
        f"missing formats for {pid}: have {formats_present}, expected {expected_formats}"
    for f in files:
        _assert_file_entry(f)
    validation = d.get("validation") or {}
    checks = validation.get("checks") or []
    assert checks, "no validation checks"
    for c in checks:
        assert c.get("passed") is True, f"validation check failed: {c}"


# --------------------------------------------------------------------------- #
# asset serving media-type + magic bytes
# --------------------------------------------------------------------------- #
FORMAT_EXPECTED_CTYPE = {
    "html": "text/html",
    "pdf": "application/pdf",
    "epub": "application/epub+zip",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "png": "image/png",
}


@pytest.mark.parametrize("pid", [BOOK_PID, PRESENTATION_PID, POSTER_PID])
def test_asset_serving_and_magic_bytes(api_client, auth, pid):
    r = api_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/render-deliverable",
                        headers=auth, timeout=120)
    assert r.status_code == 200, r.text[:400]
    d = r.json()

    # preview_url
    pv = d.get("preview_url")
    assert pv, "no preview url"
    resp = _fetch_asset(pv, auth, "text/html")
    assert b"<html" in resp.content.lower() or b"<!doctype" in resp.content.lower(), \
        "html preview body doesn't look like html"

    # each file
    for f in d["files"]:
        fmt = f["format"]
        expected = FORMAT_EXPECTED_CTYPE.get(fmt)
        assert expected, f"unexpected format {fmt}"
        assert f["media_type"] == expected, f"file entry media_type mismatch for {fmt}: {f['media_type']}"
        resp = _fetch_asset(f["url"], auth, expected)
        body = resp.content
        if fmt == "pdf":
            assert body[:4] == b"%PDF", f"pdf magic missing for {f['url']}"
        elif fmt in ("epub", "pptx"):
            assert body[:2] == b"PK", f"zip magic missing for {fmt} {f['url']}"
        elif fmt == "png":
            assert body[:8] == b"\x89PNG\r\n\x1a\n", f"png magic missing for {f['url']}"
        elif fmt == "html":
            assert b"<html" in body.lower() or b"<!doctype" in body.lower()


# --------------------------------------------------------------------------- #
# pipeline endpoint exposes deliverable
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("pid", [BOOK_PID, PRESENTATION_PID, POSTER_PID])
def test_pipeline_exposes_deliverable(api_client, auth, pid):
    r = api_client.get(f"{BASE_URL}/api/manufacturing2/{pid}/pipeline",
                       headers=auth, timeout=30)
    assert r.status_code == 200, r.text[:400]
    p = r.json()
    assert "customer_deliverable" in p
    assert "deliverable_ready" in p
    assert "cover_url" in p
    assert "thumbnail_url" in p
    assert p["deliverable_ready"] is True
    cd = p["customer_deliverable"]
    assert cd and cd.get("files"), "customer_deliverable missing files"
    assert cd.get("primary_format"), "primary_format missing"


# --------------------------------------------------------------------------- #
# Idempotency
# --------------------------------------------------------------------------- #
def test_render_idempotency(api_client, auth):
    pid = BOOK_PID
    r1 = api_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/render-deliverable",
                         headers=auth, timeout=120)
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["ready"] is True
    r2 = api_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/render-deliverable",
                         headers=auth, timeout=120)
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["ready"] is True
    # file counts should match (re-render replaces prior files)
    assert len(d1["files"]) == len(d2["files"])
    assert {f["format"] for f in d1["files"]} == {f["format"] for f in d2["files"]}


# --------------------------------------------------------------------------- #
# 404 handling
# --------------------------------------------------------------------------- #
def test_render_unknown_pid_404(api_client, auth):
    r = api_client.post(f"{BASE_URL}/api/manufacturing2/DOES_NOT_EXIST_xyz/render-deliverable",
                        headers=auth, timeout=30)
    assert r.status_code == 404, f"expected 404 got {r.status_code}: {r.text[:200]}"


def test_pipeline_unknown_pid_404(api_client, auth):
    r = api_client.get(f"{BASE_URL}/api/manufacturing2/DOES_NOT_EXIST_xyz/pipeline",
                       headers=auth, timeout=30)
    assert r.status_code == 404, f"expected 404 got {r.status_code}: {r.text[:200]}"


# --------------------------------------------------------------------------- #
# Release gating
# --------------------------------------------------------------------------- #
def _find_products(api_client, auth, status=None, treasure_standard=None):
    r = api_client.get(f"{BASE_URL}/api/products", headers=auth, timeout=30)
    assert r.status_code == 200, r.text[:200]
    data = r.json()
    if isinstance(data, dict):
        products = data.get("products") or data.get("items") or []
    else:
        products = data
    out = []
    for p in products:
        if status is not None and p.get("status") != status:
            continue
        if treasure_standard is not None and p.get("treasure_standard") != treasure_standard:
            continue
        out.append(p)
    return out


def test_release_idempotent_or_ready(api_client, auth):
    """Prefer a 'Ready for Release' certified product; otherwise re-release a Published certified product."""
    candidates = _find_products(api_client, auth, status="Ready for Release", treasure_standard=True)
    if not candidates:
        # Fall back to an already-Published certified product (idempotent release)
        candidates = _find_products(api_client, auth, status="Published", treasure_standard=True)
    if not candidates:
        pytest.skip("No certified 'Ready for Release' or 'Published' product available to exercise release path")

    pid = candidates[0]["id"]
    r = api_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/release", headers=auth, timeout=120)
    assert r.status_code == 200, f"release failed: {r.status_code} {r.text[:400]}"
    prod = r.json()
    assert prod.get("status") == "Published", f"status after release not Published: {prod.get('status')}"
    pd = prod.get("published_deliverable")
    assert pd, "published_deliverable missing after release"
    assert pd.get("primary_format"), "published_deliverable.primary_format missing"
    assert pd.get("files"), "published_deliverable.files missing"
    # sanity: at least one html file
    formats = {f["format"] for f in pd["files"]}
    assert "html" in formats


def test_release_locked_when_gates_unmet(api_client, auth):
    """Find any product with an unmet release gate and confirm 400 'Release locked. Pending gates'."""
    r = api_client.get(f"{BASE_URL}/api/products", headers=auth, timeout=30)
    if r.status_code != 200:
        pytest.skip("Cannot list products")
    data = r.json()
    products = data.get("products") if isinstance(data, dict) else data
    products = products or []

    target = None
    for p in products:
        gates = p.get("gates") or {}
        if not gates:
            continue
        unmet = [g for g, v in gates.items() if isinstance(v, dict) and v.get("status") != "passed"]
        if unmet and p.get("status") not in ("Published",):
            target = p
            break
    if not target:
        pytest.skip("No product with unmet gates available to test release-lock behaviour")

    pid = target["id"]
    prev_status = target.get("status")
    r = api_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/release", headers=auth, timeout=60)
    assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text[:200]}"
    body = r.text.lower()
    assert "release locked" in body and "pending gates" in body, f"unexpected error body: {r.text[:200]}"

    # ensure it did NOT publish
    r2 = api_client.get(f"{BASE_URL}/api/manufacturing2/{pid}/pipeline", headers=auth, timeout=30)
    assert r2.status_code == 200
    assert r2.json().get("status") == prev_status, "status changed despite release lock"
