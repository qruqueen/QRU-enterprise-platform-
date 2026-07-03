"""MT-025 — Design Validation + Download Headers backend tests.

Covers:
- GET /api/rendering/asset/{fname}?download=1&name=X → Content-Disposition attachment + correct Content-Type per format
- GET /api/rendering/asset/{fname} (no download) → inline (no attachment disposition)
- POST /api/manufacturing2/{pid}/render-deliverable → customer_deliverable.design_review
  (grade 0-100, approved bool, status string, criteria[] covering cover/branding/interior/hierarchy/
  typography/print/mobile/margins)
- Design gate on release: POST /api/manufacturing2/{pid}/release blocks with 400 + 'design review'
  when design_review_required=true; approved product still publishes (idempotent re-release ok).
"""
import os
import re
import pytest
import requests


def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not set")


BASE_URL = _load_backend_url()

BOOK_PID = "c4530d52-9286-458a-9104-48f4be38c08a"
PRESENTATION_PID = "a3a3326e-0046-4681-a13f-38f06ee8fa3a"
POSTER_PID = "f464e59c-e30c-47c7-9ab3-77a596e2a7bc"

LOGIN_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
LOGIN_PASSWORD = "QruFounder2026!"

# expected content-type per file format
FORMAT_CTYPE = {
    "html": "text/html",
    "pdf": "application/pdf",
    "epub": "application/epub+zip",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "png": "image/png",
}


# --------------------------- fixtures --------------------------- #
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


@pytest.fixture(scope="session")
def book_deliverable(api_client, auth):
    r = api_client.post(f"{BASE_URL}/api/manufacturing2/{BOOK_PID}/render-deliverable",
                        headers=auth, timeout=120)
    assert r.status_code == 200, r.text[:400]
    return r.json()


@pytest.fixture(scope="session")
def presentation_deliverable(api_client, auth):
    r = api_client.post(f"{BASE_URL}/api/manufacturing2/{PRESENTATION_PID}/render-deliverable",
                        headers=auth, timeout=120)
    assert r.status_code == 200, r.text[:400]
    return r.json()


@pytest.fixture(scope="session")
def poster_deliverable(api_client, auth):
    r = api_client.post(f"{BASE_URL}/api/manufacturing2/{POSTER_PID}/render-deliverable",
                        headers=auth, timeout=120)
    assert r.status_code == 200, r.text[:400]
    return r.json()


# ------------------------------------------------------------------
# (A) DESIGN VALIDATION — POST /render-deliverable returns design_review
# ------------------------------------------------------------------
REQUIRED_CRIT_KEYWORDS = [
    "cover", "branding", "interior", "hierarchy",
    "typography", "print", "mobile", "margins",
]


def _assert_design_review_shape(d, expect_approved=True, min_grade=None):
    cd = d
    dz = cd.get("design_review")
    assert dz, f"design_review missing on deliverable: {list(cd.keys())}"
    # grade 0-100
    assert isinstance(dz.get("grade"), int), f"grade not int: {dz.get('grade')!r}"
    assert 0 <= dz["grade"] <= 100
    # approved bool
    assert isinstance(dz.get("approved"), bool)
    # status label
    if dz["approved"]:
        assert dz["status"] == "Treasure Standard™ Approved", dz
    else:
        assert dz["status"] == "Rendered — Design Review Required", dz
    # criteria array
    crits = dz.get("criteria") or []
    assert isinstance(crits, list) and len(crits) >= 8, f"criteria list too short: {crits}"
    for cr in crits:
        assert "name" in cr and "passed" in cr and "weight" in cr, cr
        assert isinstance(cr["passed"], bool)
        assert isinstance(cr["weight"], int) and cr["weight"] > 0
    names_lower = " ".join(cr["name"].lower() for cr in crits)
    for kw in REQUIRED_CRIT_KEYWORDS:
        assert kw in names_lower, f"missing criterion keyword '{kw}' in: {names_lower}"
    # threshold echoed
    assert dz.get("threshold") == 85
    # top-level convenience flags
    assert cd.get("design_approved") == dz["approved"]
    assert cd.get("status_label") == dz["status"]
    # explicit expectation
    if expect_approved:
        assert dz["approved"] is True, f"expected approved but got: {dz}"
    if min_grade is not None:
        assert dz["grade"] >= min_grade, f"grade {dz['grade']} below expected {min_grade}"


def test_book_design_review_approved_grade_100(book_deliverable):
    _assert_design_review_shape(book_deliverable, expect_approved=True, min_grade=100)


def test_presentation_design_review_approved(presentation_deliverable):
    _assert_design_review_shape(presentation_deliverable, expect_approved=True, min_grade=85)


def test_poster_design_review_approved(poster_deliverable):
    _assert_design_review_shape(poster_deliverable, expect_approved=True, min_grade=85)


# ------------------------------------------------------------------
# (B) DOWNLOAD HEADERS — /api/rendering/asset/{fname}
# ------------------------------------------------------------------
def _pick(files, fmt):
    for f in files:
        if f["format"] == fmt:
            return f
    return None


def _asset_get(url, params=None):
    if url.startswith("http"):
        full = url
    else:
        full = f"{BASE_URL}{url}"
    # No auth needed for public asset endpoint
    return requests.get(full, params=params, timeout=30, allow_redirects=True)


@pytest.mark.parametrize("pid_fixture,fmt", [
    ("book_deliverable", "html"),
    ("book_deliverable", "epub"),
    ("book_deliverable", "pdf"),
    ("presentation_deliverable", "pptx"),
    ("presentation_deliverable", "pdf"),
    ("poster_deliverable", "png"),
    ("poster_deliverable", "html"),
])
def test_download_flag_sets_attachment_and_correct_ctype(request, pid_fixture, fmt):
    d = request.getfixturevalue(pid_fixture)
    f = _pick(d["files"], fmt)
    assert f, f"no {fmt} file in deliverable of {pid_fixture}"
    r = _asset_get(f["url"], params={"download": 1, "name": "My Test Copy"})
    assert r.status_code == 200, f"asset GET failed: {r.status_code}"
    disp = r.headers.get("content-disposition", "")
    assert disp.lower().startswith("attachment"), \
        f"expected attachment disposition, got: {disp!r}"
    # filename ends with correct extension
    m = re.search(r'filename="([^"]+)"', disp)
    assert m, f"no filename in disposition: {disp}"
    assert m.group(1).lower().endswith(f".{fmt}"), \
        f"filename ext mismatch: {m.group(1)} vs .{fmt}"
    # content-type
    ctype = r.headers.get("content-type", "").split(";")[0].strip()
    assert ctype == FORMAT_CTYPE[fmt], f"ctype {ctype} != {FORMAT_CTYPE[fmt]}"
    # body sanity
    assert len(r.content) >= 800


def test_no_download_flag_is_inline(book_deliverable):
    """Reader/preview must stay inline — no attachment disposition."""
    f = _pick(book_deliverable["files"], "html")
    assert f
    r = _asset_get(f["url"])
    assert r.status_code == 200
    disp = r.headers.get("content-disposition", "") or ""
    assert "attachment" not in disp.lower(), f"unexpected attachment on inline: {disp!r}"
    ctype = r.headers.get("content-type", "").split(";")[0].strip()
    assert ctype == "text/html"
    body_lower = r.content.lower()
    assert b"<html" in body_lower or b"<!doctype" in body_lower


def test_preview_url_is_inline_html(book_deliverable):
    """preview_url is what pd-open-reader hits — must be inline HTML."""
    pv = book_deliverable.get("preview_url")
    assert pv
    r = _asset_get(pv)
    assert r.status_code == 200
    disp = r.headers.get("content-disposition", "") or ""
    assert "attachment" not in disp.lower(), f"preview should be inline: {disp!r}"
    ctype = r.headers.get("content-type", "").split(";")[0].strip()
    assert ctype == "text/html"
    # branded reader signals
    body = r.content.decode("utf-8", errors="ignore")
    assert "QRU PRESS" in body, "reader missing 'QRU PRESS' masthead"
    assert "TREASURE STANDARD" in body.upper(), "reader missing Treasure Standard seal"


# ------------------------------------------------------------------
# (C) DESIGN GATE ON RELEASE
# ------------------------------------------------------------------
RELEASE_GATES = ["Verification", "Education Review", "Creative Studio", "Brand Review",
                 "Accessibility", "Experience Review", "Quality Control", "Treasure Standard"]


def _list_products(api_client, auth):
    r = api_client.get(f"{BASE_URL}/api/products", headers=auth, timeout=30)
    assert r.status_code == 200
    data = r.json()
    return data.get("products") if isinstance(data, dict) else data


def _find_releasable_certified(api_client, auth):
    """Find a certified product whose gates are ALL passed (Ready for Release or Published)."""
    products = _list_products(api_client, auth) or []
    for p in products:
        if not p.get("treasure_standard"):
            continue
        if p.get("status") not in ("Ready for Release", "Published"):
            continue
        gates = p.get("gates") or {}
        unmet = [g for g in RELEASE_GATES if gates.get(g, {}).get("status") != "passed"]
        if not unmet:
            return p
    return None


def _load_env_from_file():
    """Load MONGO_URL & DB_NAME from backend/.env if not in environ."""
    out = {}
    try:
        with open("/app/backend/.env") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def test_release_of_approved_product_publishes(api_client, auth):
    """A design-approved certified product should release/publish (idempotent re-release ok)."""
    target = _find_releasable_certified(api_client, auth)
    if not target:
        pytest.skip("No certified releasable product with all gates passed")
    pid = target["id"]
    # Ensure deliverable is rendered so design_review is populated
    r0 = api_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/render-deliverable",
                         headers=auth, timeout=120)
    assert r0.status_code == 200
    d0 = r0.json()
    # only run this on a design-approved product
    if not d0.get("design_approved", True):
        pytest.skip(f"Target {pid} is not design-approved; cannot test successful release path")

    r = api_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/release",
                        headers=auth, timeout=120)
    assert r.status_code == 200, f"release failed: {r.status_code} {r.text[:400]}"
    prod = r.json()
    assert prod.get("status") == "Published", f"status={prod.get('status')}"
    pd = prod.get("published_deliverable")
    assert pd, "published_deliverable missing"
    assert pd.get("files")


def test_release_blocked_when_design_review_required(api_client, auth):
    """Flip design_review_required=true on a fully-gated certified product; expect 400 + 'design review'."""
    target = _find_releasable_certified(api_client, auth)
    if not target:
        pytest.skip("No certified releasable product with all gates passed available for gate test")
    pid = target["id"]

    # Load MONGO creds from backend/.env if not in env
    env_extra = _load_env_from_file()
    mongo_url = os.environ.get("MONGO_URL") or env_extra.get("MONGO_URL")
    dbname = os.environ.get("DB_NAME") or env_extra.get("DB_NAME")
    if not mongo_url or not dbname:
        pytest.skip("MONGO_URL/DB_NAME not accessible for direct DB flip")

    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient

    async def _set(val):
        cli = AsyncIOMotorClient(mongo_url)
        try:
            await cli[dbname].products.update_one({"id": pid}, {"$set": {"design_review_required": val}})
        finally:
            cli.close()

    # Snapshot original value to restore later
    orig = target.get("design_review_required", False)
    try:
        asyncio.run(_set(True))
        r = api_client.post(f"{BASE_URL}/api/manufacturing2/{pid}/release",
                            headers=auth, timeout=60)
        assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text[:200]}"
        assert "design review" in r.text.lower(), f"error missing 'design review': {r.text[:200]}"
    finally:
        # Restore to original state
        asyncio.run(_set(bool(orig)))
