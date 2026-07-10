"""Iteration 37 — MO-015/016/017 Trust & Authenticity + MO-018 QICS Companion System.

Tests cover:
  • Trust config, certificate, register, registry, verify (public), platform-plan, audit
  • QICS config, activate (immutable identity), portal (public), event, destination, analytics
  • FR-095 / FR-096 factory rules
"""
import os
import pytest
import requests

_url = os.environ.get("REACT_APP_BACKEND_URL")
if not _url:
    # Fallback: read from frontend/.env (test env has envs in different location)
    try:
        with open("/app/frontend/.env") as _f:
            for _line in _f:
                if _line.startswith("REACT_APP_BACKEND_URL="):
                    _url = _line.split("=", 1)[1].strip()
                    break
    except Exception:
        pass
BASE_URL = (_url or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL missing"
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="session")
def founder_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def headers(founder_token):
    return {"Authorization": f"Bearer {founder_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def sample_product(headers):
    r = requests.get(f"{BASE_URL}/api/founder-inbox", headers=headers, timeout=30)
    assert r.status_code == 200
    products = r.json().get("products", [])
    assert products, "No products in founder-inbox"
    # Prefer PRD-00078 if present
    for p in products:
        if p.get("product_code") == "PRD-00078":
            return p
    return products[0]


# -------- Trust config --------
class TestTrustConfig:
    def test_trust_config(self, headers):
        r = requests.get(f"{BASE_URL}/api/trust/config", headers=headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert set(data["protection_layers"].keys()) >= {
            "access_control", "watermarking", "metadata", "platform_security", "audit_logging"}
        assert len(data["protection_layers"]) == 5
        # Honest statuses: enforced or platform_provided
        statuses = {v["status"] for v in data["protection_layers"].values()}
        assert statuses <= {"enforced", "configurable", "platform_provided", "planned"}
        assert data["protection_layers"]["platform_security"]["status"] == "platform_provided"
        assert len(data["security_levels"]) == 5
        assert len(data["distribution_channels"]) == 8
        assert len(data["distribution_permissions"]) == 5
        assert len(data["platform_capabilities"]) == 8
        assert data["factory_rule"]["id"] == "FR-095"


# -------- Trust certificate + register + registry + verify --------
class TestTrustCertificate:
    def test_certificate_returns_all_fields(self, headers, sample_product):
        pid = sample_product["id"]
        r = requests.get(f"{BASE_URL}/api/trust/certificate/{pid}", headers=headers, timeout=30)
        assert r.status_code == 200, r.text
        c = r.json()
        assert c["qru_product_id"] == sample_product["product_code"]
        assert c["authenticity_certificate"].startswith("QRU-CERT-")
        assert c["qruseal"] == "QRU-SEAL™"
        assert c["treasure_standard_status"] in ("Met", "Pending")
        assert c["gold_standard_status"] in ("Met", "Pending Human Review")
        assert c["version"]
        assert c["qr_code"].startswith("data:image/svg+xml;base64,")
        assert "/api/trust/verify/" in c["verify_url"]
        # approval_history: every field must be a string (not raw dict)
        for h in c["approval_history"]:
            assert isinstance(h["stage"], str)
            assert isinstance(h["decision"], str)
            assert isinstance(h["authority"], str)

    def test_register_upserts_record(self, headers, sample_product):
        pid = sample_product["id"]
        r = requests.post(f"{BASE_URL}/api/trust/register/{pid}", headers=headers, timeout=30)
        assert r.status_code == 200, r.text
        rec = r.json()
        assert rec["product_id"] == pid
        assert rec["product_code"] == sample_product["product_code"]
        assert rec["certificate_id"].startswith("QRU-CERT-")
        # idempotent
        r2 = requests.post(f"{BASE_URL}/api/trust/register/{pid}", headers=headers, timeout=30)
        assert r2.status_code == 200

    def test_registry_lists(self, headers, sample_product):
        r = requests.get(f"{BASE_URL}/api/trust/registry", headers=headers, timeout=30)
        assert r.status_code == 200
        records = r.json()["records"]
        assert isinstance(records, list) and len(records) >= 1
        assert any(rec["product_code"] == sample_product["product_code"] for rec in records)

    def test_verify_public_real_code(self, sample_product):
        # No auth headers — endpoint must be PUBLIC
        code = sample_product["product_code"]
        r = requests.get(f"{BASE_URL}/api/trust/verify/{code}", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["found"] is True
        assert d["qru_product_id"] == code
        assert d["qruseal"] == "QRU-SEAL™"

    def test_verify_public_fake_code(self):
        r = requests.get(f"{BASE_URL}/api/trust/verify/PRD-00000-FAKE", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["found"] is False


# -------- Trust platform-plan + audit --------
class TestTrustPlatformPlan:
    @pytest.mark.parametrize("platform,expected_in_supported", [
        ("youtube", "protected_streaming"),
        ("etsy", None),  # etsy has no supported protections
        ("kdp", "drm"),
    ])
    def test_platform_plan(self, headers, platform, expected_in_supported):
        r = requests.get(f"{BASE_URL}/api/trust/platform-plan/{platform}", headers=headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["platform"] == platform
        assert d["known"] is True
        assert "applied" in d and "unsupported" in d and "best_available" in d
        # watermarking + metadata are always applied everywhere
        assert "watermarking" in d["applied"]
        assert "metadata" in d["applied"]
        if expected_in_supported:
            assert expected_in_supported in d["platform_supported"]

    def test_audit_returns_events_list(self, headers, sample_product):
        pid = sample_product["id"]
        r = requests.get(f"{BASE_URL}/api/trust/audit/{pid}", headers=headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["product_code"] == sample_product["product_code"]
        assert isinstance(d["events"], list)
        assert d["total"] == len(d["events"])


# -------- QICS config --------
class TestQICSConfig:
    def test_qics_config(self, headers):
        r = requests.get(f"{BASE_URL}/api/qics/config", headers=headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert len(d["identity_formats"]) == 8
        prefixes = {v.split("-")[0] + "-" + v.split("-")[1] for v in d["identity_formats"].values()}
        assert {"QRU-BK", "QRU-KR", "QRU-WB", "QRU-CR", "QRU-AU", "QRU-VD", "QRU-PT", "QRU-AS"} <= prefixes
        assert len(d["resource_catalog"]) == 18
        assert d["factory_rule"]["id"] == "FR-096"
        assert d["dynamic_qr"]["expiration"] == "never"
        assert isinstance(d["analytics_metrics"], list) and d["analytics_metrics"]
        assert isinstance(d["future_support"], list) and d["future_support"]


# -------- QICS activate (immutability + portal + qr) --------
class TestQICSActivate:
    def test_activate_and_immutability(self, headers, sample_product):
        pid = sample_product["id"]
        r1 = requests.post(f"{BASE_URL}/api/qics/activate/{pid}", headers=headers, timeout=60)
        assert r1.status_code == 200, r1.text
        d1 = r1.json()
        ident1 = d1["qics_identity"]
        assert ident1.startswith("QRU-")
        # correct prefix based on family/product_type (book/pdf/printable → QRU-BK, kr → QRU-KR ...)
        assert d1["qr_code"].startswith("data:image/svg+xml;base64,")
        # Portal must have 15 sections
        assert d1["portal"]["section_total"] == 15
        assert len(d1["portal"]["sections"]) == 15
        # Re-activate — must return SAME identity (immutability)
        r2 = requests.post(f"{BASE_URL}/api/qics/activate/{pid}", headers=headers, timeout=60)
        assert r2.status_code == 200
        assert r2.json()["qics_identity"] == ident1, "Identity mutated on re-activation"


# -------- QICS portal (public) + event + destination + analytics --------
class TestQICSPortal:
    @pytest.fixture(scope="class")
    def portal_data(self, headers, sample_product):
        r = requests.post(f"{BASE_URL}/api/qics/activate/{sample_product['id']}", headers=headers, timeout=60)
        assert r.status_code == 200
        return r.json()

    def test_public_portal(self, portal_data):
        ident = portal_data["qics_identity"]
        # No auth — must be public
        r = requests.get(f"{BASE_URL}/api/qics/portal/{ident}", timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["qics_identity"] == ident
        assert d["landing"]["title"] == "Welcome to Your QRU Learning Portal™"
        assert d["portal"]["section_total"] == 15
        assert "authenticity" in d
        assert isinstance(d["continuation"], list)

    def test_public_event(self, portal_data):
        ident = portal_data["qics_identity"]
        r = requests.post(f"{BASE_URL}/api/qics/portal/{ident}/event",
                          json={"type": "resource_download"}, timeout=30)
        assert r.status_code == 200
        assert r.json()["recorded"] is True

    def test_event_rejects_unknown(self, portal_data):
        ident = portal_data["qics_identity"]
        r = requests.post(f"{BASE_URL}/api/qics/portal/{ident}/event",
                          json={"type": "nope_unknown"}, timeout=30)
        assert r.status_code == 400

    def test_update_destination(self, headers, portal_data):
        ident = portal_data["qics_identity"]
        new_dest = f"{BASE_URL}/companion?override=test"
        r = requests.put(f"{BASE_URL}/api/qics/portal/{ident}/destination",
                         headers=headers, json={"destination_url": new_dest}, timeout=30)
        assert r.status_code == 200
        assert r.json()["destination_url"] == new_dest

    def test_analytics_after_events(self, headers, sample_product, portal_data):
        # Trigger a scan by hitting public portal
        requests.get(f"{BASE_URL}/api/qics/portal/{portal_data['qics_identity']}", timeout=30)
        r = requests.get(f"{BASE_URL}/api/qics/analytics/{sample_product['id']}",
                         headers=headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["product_id"] == sample_product["id"]
        assert d["scan_count"] >= 1
        assert d["total_events"] >= 1
        assert d["resource_downloads"] >= 1  # from earlier event test
        assert "by_type" in d


# -------- Governance binding & regression --------
class TestRegression:
    def test_governance_binding_trust(self, headers):
        r = requests.get(f"{BASE_URL}/api/governance-binding/strip/trust", headers=headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["governed_by"], list) and len(d["governed_by"]) >= 1

    def test_distribution_still_works(self, headers):
        r = requests.get(f"{BASE_URL}/api/distribution/connectors", headers=headers, timeout=30)
        assert r.status_code == 200

    def test_media_starter_kit_still_works(self, headers):
        r = requests.get(f"{BASE_URL}/api/media-starter-kit/config", headers=headers, timeout=30)
        assert r.status_code == 200
