"""Backend tests for STD-RFN-0001 QRU Enterprise Refinement Initiative.

Covers:
- /api/refinement/overview shape (engines, foundation, matrix, autonomy, contract)
- /api/refinement/knowledge (POST + GET list) — honest independent verification verdict
- /api/refinement/product (POST + GET list) — Draft (not Gold) when KR is internal
- /api/refinement/benchmark — 5 KRs -> 30 products, gold_standard_products = 0
- /api/refinement/learning — aggregates + recommendations, reuse ratio
- Regression: /api/flow/registry (RFN-0001 present) and /api/architecture/domains (8 domains)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PW = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PW}, timeout=30)
    assert r.status_code == 200, f"Founder login failed: {r.status_code} {r.text[:200]}"
    body = r.json()
    tok = body.get("token") or body.get("access_token")
    assert tok, f"No token returned: {body}"
    return tok


@pytest.fixture(scope="module")
def H(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- Refinement Overview ----------
class TestOverview:
    def test_overview_shape(self, H):
        r = requests.get(f"{BASE_URL}/api/refinement/overview", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["doc_id"] == "STD-RFN-0001"
        assert d["experience_layer"]["name"] == "QRU Factory Concierge™"
        engine_ids = {e["id"] for e in d["engines"]}
        assert engine_ids == {"knowledge", "product", "learning"}
        for e in d["engines"]:
            assert e.get("purpose") and isinstance(e.get("internalizes"), list) and len(e["internalizes"]) >= 1
        assert len(d["foundation"]) == 5
        assert len(d["inheritance_matrix"]) == 4
        for m in d["inheritance_matrix"]:
            assert m["consolidated"] and isinstance(m["absorbs"], list) and m["successor"]
            assert m["governance_preserved"] is True and m["memory_preserved"] is True
        assert len(d["autonomy_levels"]) == 5
        assert {a["level"] for a in d["autonomy_levels"]} == {0, 1, 2, 3, 4}
        umc = d["universal_manufacturing_contract"]
        assert "order" in umc and "invariants" in umc and len(umc["invariants"]) >= 3


# ---------- Knowledge Manufacturing ----------
class TestKnowledge:
    def test_manufacture_knowledge_honest_verification(self, H):
        r = requests.post(f"{BASE_URL}/api/refinement/knowledge",
                          headers=H, json={"topic": "What Is Understanding?"}, timeout=45)
        assert r.status_code == 200, r.text[:200]
        kr = r.json()
        assert kr["id"] and kr["kr_code"].startswith("KMR-")
        # sections required
        for s in ("definition", "explanation", "relationships", "examples",
                  "counterexamples", "common_misunderstandings", "memory_anchors", "assessment_plan"):
            assert s in kr["sections"], f"Missing section: {s}"
        # confidence profile with human_review_requirement
        cp = kr["confidence_profile"]
        assert cp["human_review_requirement"] is True
        # HONESTY: NOT VERIFIED_EXTERNAL for topic without cited sources
        v = kr["verification"]
        assert v["verdict"] == "APPROVED_INTERNAL_PENDING_HUMAN_VERIFICATION"
        assert v["independent"] is True
        assert v["evidence_sufficient_for_external_publication"] is False
        # Treasure passed on structural
        assert kr["treasure"]["verdict"] == "PASSED"
        assert kr["status"] == "Approved (internal)"

    def test_list_knowledge(self, H):
        r = requests.get(f"{BASE_URL}/api/refinement/knowledge", headers=H, timeout=30)
        assert r.status_code == 200
        assert "records" in r.json() and isinstance(r.json()["records"], list)


# ---------- Product Manufacturing ----------
class TestProduct:
    def test_manufacture_product_stays_draft(self, H):
        # First manufacture a KR
        r = requests.post(f"{BASE_URL}/api/refinement/knowledge",
                          headers=H, json={"topic": "What Is Knowledge?"}, timeout=45)
        assert r.status_code == 200
        kr_id = r.json()["id"]

        r = requests.post(f"{BASE_URL}/api/refinement/product",
                          headers=H, json={"kr_id": kr_id, "product_type": "Book"}, timeout=45)
        assert r.status_code == 200, r.text[:200]
        p = r.json()
        assert p["kr_id"] == kr_id
        assert p["product_type"] == "Book"
        # HONESTY: Not Gold Standard
        assert p["gold_standard"] is False
        assert "Draft" in p["status"]
        assert isinstance(p["preflight"].get("verdict"), str) and p["preflight"]["verdict"]
        assert p["preflight"]["blocked"] is False

    def test_product_unknown_kr_returns_404(self, H):
        r = requests.post(f"{BASE_URL}/api/refinement/product",
                          headers=H, json={"kr_id": "does-not-exist", "product_type": "Book"}, timeout=30)
        assert r.status_code == 404

    def test_list_products(self, H):
        r = requests.get(f"{BASE_URL}/api/refinement/products", headers=H, timeout=30)
        assert r.status_code == 200
        assert "products" in r.json()


# ---------- Benchmark run ----------
class TestBenchmark:
    def test_benchmark_full_run(self, H):
        r = requests.post(f"{BASE_URL}/api/refinement/benchmark", headers=H, timeout=180)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d["knowledge_records_manufactured"] == 5
        assert d["kr_treasure_pass"] == 5
        assert d["kr_success_rate"] == 100
        assert d["products_manufactured"] == 30
        assert d["product_success_rate"] == 100
        # CRITICAL HONESTY INVARIANT
        assert d["gold_standard_products"] == 0, "Honesty violation: benchmark should not certify external Gold."
        assert d["founder_decisions_required"] == 0
        assert d.get("honesty_note")
        assert len(d.get("knowledge_records", [])) == 5
        assert len(d.get("products", [])) == 30
        # All products must be Draft
        assert all(p["gold_standard"] is False for p in d["products"])


# ---------- Learning ----------
class TestLearning:
    def test_learning_summary(self, H):
        # Ensure benchmark has run first (side-effect in the same session)
        r = requests.get(f"{BASE_URL}/api/refinement/learning", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("knowledge_records", "products", "gold_standard_products",
                  "draft_products", "knowledge_reuse_ratio", "recommendations", "note"):
            assert k in d
        assert d["gold_standard_products"] == 0
        assert d["knowledge_records"] >= 5
        assert d["products"] >= 30
        assert d["knowledge_reuse_ratio"] >= 1.0
        assert isinstance(d["recommendations"], list) and len(d["recommendations"]) >= 1
        for rec in d["recommendations"]:
            assert rec.get("authority") and rec.get("governed") is True


# ---------- Regression ----------
class TestRegression:
    def test_flow_registry_includes_rfn(self, H):
        r = requests.get(f"{BASE_URL}/api/flow/registry", headers=H, timeout=30)
        assert r.status_code == 200, r.text[:200]
        d = r.json()
        # response can be either dict or list; find standard ids
        text = str(d)
        for sid in ["QRU-CON-0001", "QRU-CON-0002", "STD-MFG-0001", "STD-EIP-0002", "STD-RFN-0001"]:
            assert sid in text, f"Missing standard {sid} in /api/flow/registry"

    def test_architecture_domains_8(self, H):
        r = requests.get(f"{BASE_URL}/api/architecture/domains", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        # accept {domains: [...]} or [...] shape
        domains = d.get("domains") if isinstance(d, dict) else d
        assert isinstance(domains, list) and len(domains) == 8
