"""Iteration 105 — Backend tests for:
- Universal Page Layout Engine (config/build/preview/settings)
- Creative Assets DELETE gate (removable only Rejected/Rights Hold/Revision Required)
"""
import os, io, base64, uuid, asyncio, requests, pytest
from PIL import Image

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN = {"email": "demo.admin@qru.com", "password": "qru-demo-admin-2026"}


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


def _big_png_b64():
    im = Image.new("RGB", (2119, 3000), (240, 220, 200))
    # add some content so QA passes
    for x in range(0, 2119, 60):
        for y in range(0, 3000, 60):
            im.paste((30, 60, 120), (x, y, min(x + 40, 2119), min(y + 40, 3000)))
    buf = io.BytesIO(); im.save(buf, "PNG"); buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode()


# ---------- Printables config ----------
def test_config_layouts(client):
    r = client.get(f"{BASE_URL}/api/printables/config", timeout=30)
    assert r.status_code == 200
    j = r.json()
    layouts = j.get("layouts") or []
    ids = {l["id"] for l in layouts}
    expected = {"poster", "fill", "original", "custom_scale", "coloring", "bordered",
                "book_illustration", "worksheet", "workbook", "activity", "cut_paste"}
    assert expected.issubset(ids), f"missing layouts: {expected - ids}"
    assert len(layouts) == 11
    assert j.get("default_margin_in") == 0.25


# ---------- Build standalone poster/worksheet/bordered ----------
@pytest.fixture(scope="module")
def png_b64():
    return _big_png_b64()


def test_build_standalone_poster(client, png_b64):
    payload = {"product_type": "one_page_printable", "images_base64": [png_b64],
               "layout": "poster", "margin_in": 0.25, "page_size": "letter"}
    r = client.post(f"{BASE_URL}/api/printables/build/book/standalone", json=payload, timeout=90)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("layout") == "poster"
    assert j.get("margin_in") == 0.25
    assert j["qa"]["result"] in ("PASS", "PASS WITH WARNINGS")
    assert j["pages_meta"][0]["type"] == "layout_poster"


@pytest.mark.parametrize("layout,expected_type_prefix", [("worksheet", "layout_"), ("bordered", "layout_")])
def test_build_standalone_other_layouts(client, png_b64, layout, expected_type_prefix):
    payload = {"product_type": "one_page_printable", "images_base64": [png_b64],
               "layout": layout, "margin_in": 0.25}
    r = client.post(f"{BASE_URL}/api/printables/build/book/standalone", json=payload, timeout=90)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("layout") == layout
    assert j["pages_meta"][0]["type"].startswith(expected_type_prefix)
    assert layout in j["pages_meta"][0]["type"]


# ---------- Preview page ----------
def test_preview_page_poster(client, png_b64):
    r = client.post(f"{BASE_URL}/api/printables/preview-page",
                    json={"image_base64": png_b64, "layout": "poster", "margin_in": 0.25}, timeout=60)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["preview_base64"].startswith("data:image/png;base64,")
    assert "effective_dpi" in j or "status" in j


def test_preview_page_fullbleed(client, png_b64):
    r = client.post(f"{BASE_URL}/api/printables/preview-page",
                    json={"image_base64": png_b64, "layout": "poster", "margin_in": 0.0}, timeout=60)
    assert r.status_code == 200, r.text
    assert r.json()["preview_base64"].startswith("data:image/png;base64,")


# ---------- Settings persistence ----------
def test_settings_save_and_read(client):
    payload = {"layout": "worksheet", "margin_in": 0.5, "custom_scale": 90, "page_size": "letter"}
    r = client.post(f"{BASE_URL}/api/printables/settings", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    r2 = client.get(f"{BASE_URL}/api/printables/settings", timeout=30)
    assert r2.status_code == 200
    j = r2.json()
    assert j["layout"] == "worksheet"
    assert j["margin_in"] == 0.5


def test_build_persists_last_layout(client, png_b64):
    payload = {"product_type": "one_page_printable", "images_base64": [png_b64],
               "layout": "bordered", "margin_in": 0.3}
    r = client.post(f"{BASE_URL}/api/printables/build/book/standalone", json=payload, timeout=90)
    assert r.status_code == 200
    r2 = client.get(f"{BASE_URL}/api/printables/settings", timeout=30)
    j = r2.json()
    assert j["layout"] == "bordered"
    assert abs(float(j["margin_in"]) - 0.3) < 1e-6


# ---------- Creative Assets DELETE gate ----------
# Seed test assets directly via Motor (same DB used by app)
@pytest.fixture(scope="module")
def seeded_assets():
    import motor.motor_asyncio
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    client_m = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    db = client_m[db_name]

    ids = {}
    async def seed():
        for state_key, state in [("rejected", "Rejected"), ("rights_hold", "Rights Hold"),
                                  ("revision", "Revision Required"), ("locked", "Locked"),
                                  ("approved", "Approved")]:
            aid = f"CA-TEST-{uuid.uuid4().hex[:8]}"
            doc = {"id": aid, "asset_id": aid, "product_id": "TEST-PROD",
                   "lifecycle_state": state, "file_url": "/tmp/x.png",
                   "asset_role": "test", "platform_id": "test"}
            await db["ucams_assets"].insert_one(doc)
            ids[state_key] = aid
    asyncio.get_event_loop().run_until_complete(seed())
    yield ids
    async def cleanup():
        await db["ucams_assets"].delete_many({"asset_id": {"$regex": "^CA-TEST-"}})
    asyncio.get_event_loop().run_until_complete(cleanup())


def test_delete_rejected_asset_ok(client, seeded_assets):
    aid = seeded_assets["rejected"]
    r = client.delete(f"{BASE_URL}/api/creative-assets/assets/{aid}", timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["deleted"] is True
    assert j["asset_id"] == aid


def test_delete_rights_hold_ok(client, seeded_assets):
    aid = seeded_assets["rights_hold"]
    r = client.delete(f"{BASE_URL}/api/creative-assets/assets/{aid}", timeout=30)
    assert r.status_code == 200, r.text
    assert r.json()["deleted"] is True


def test_delete_revision_required_ok(client, seeded_assets):
    aid = seeded_assets["revision"]
    r = client.delete(f"{BASE_URL}/api/creative-assets/assets/{aid}", timeout=30)
    assert r.status_code == 200


def test_delete_locked_forbidden(client, seeded_assets):
    aid = seeded_assets["locked"]
    r = client.delete(f"{BASE_URL}/api/creative-assets/assets/{aid}", timeout=30)
    assert r.status_code == 400, r.text


def test_delete_approved_forbidden(client, seeded_assets):
    aid = seeded_assets["approved"]
    r = client.delete(f"{BASE_URL}/api/creative-assets/assets/{aid}", timeout=30)
    assert r.status_code == 400, r.text


def test_delete_unknown_404(client):
    r = client.delete(f"{BASE_URL}/api/creative-assets/assets/CA-DOES-NOT-EXIST-XYZ", timeout=30)
    assert r.status_code == 404
