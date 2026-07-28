"""Iteration 50 — QRU Publishing & Presentation Standard (QRU-CON-0002) + Cover Studio tests.

Covers: standard, tokens (json+css), bindings, TOC clean/typeset, preflight (clean + defective + runs),
pilot (before/after), Cover Studio governance (spec_only generate, list, file for existing AI cover,
state workflow with GOLD_MASTER guard).
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://enterprise-os-17.preview.emergentagent.com").rstrip("/")
FOUNDER_EMAIL = "22j2rsdzb8@privaterelay.appleid.com"
FOUNDER_PASSWORD = "QruFounder2026!"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": FOUNDER_EMAIL, "password": FOUNDER_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------- Standard & Tokens
class TestStandardAndTokens:
    def test_standard(self, auth):
        r = requests.get(f"{BASE_URL}/api/publishing/standard", headers=auth, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["doc_id"] == "QRU-CON-0002"
        assert d["version"] == "1.0"
        assert len(d["typography"]) == 13
        assert len(d["colors"]) == 6
        assert len(d["callouts"]) == 10
        assert len(d["reference_covers"]) == 4
        assert len(d["cover_standard"]["cover_states"]) == 6
        assert set(d["pre_ship_gate"]["severities"]) >= {
            "BLOCKING_FAILURE", "WARNING", "ADVISORY", "PASSED", "NOT_APPLICABLE"}

    def test_tokens_json(self, auth):
        r = requests.get(f"{BASE_URL}/api/publishing/tokens", headers=auth, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["version"] == "1.0"
        assert d["governing_standard"] == "QRU-CON-0002"
        assert len(d["typography"]) == 13 and len(d["colors"]) == 6 and len(d["callouts"]) == 10

    def test_tokens_css_public(self):
        r = requests.get(f"{BASE_URL}/api/publishing/tokens.css", timeout=30)
        assert r.status_code == 200
        assert "text/css" in r.headers.get("content-type", "")
        body = r.text
        assert ":root" in body
        assert "--color-ink-navy" in body
        assert ".type-body" in body
        assert ".qru-callout-key_insight" in body


# ---------------------------------------------------------------- Bindings
class TestBindings:
    def test_bindings(self, auth):
        r = requests.get(f"{BASE_URL}/api/publishing/bindings", headers=auth, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["standard"] == "QRU-CON-0002"
        systems = {b["system"] for b in d["bindings"]}
        for req in ["Deliverable Renderer", "Cover Studio", "Design Intelligence",
                    "Treasure Standard Pre-Ship Gate", "Factory OS / Concierge",
                    "Distribution Center", "Media Production"]:
            assert req in systems, f"missing binding: {req}"


# ---------------------------------------------------------------- TOC cleaner
class TestTOC:
    def test_toc_clean(self, auth):
        raw = (
            "## Table of Contents\n"
            "- [Introduction](#intro) .......... 1\n"
            "- **Chapter 1 — What Understanding Is Not** [see also](https://qru.world/ch1) .... 7\n"
            "  - *1.1 Recognition Is Not Comprehension* ...... 9\n"
            "- Chapter 3 — Manufacturing Understanding (#ch3) ... 34\n"
        )
        r = requests.post(f"{BASE_URL}/api/publishing/toc/clean",
                          headers=auth, json={"raw": raw}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert len(d["entries"]) >= 3
        for e in d["entries"]:
            t = e["title"]
            assert "#" not in t and "http" not in t and "[" not in t and "]" not in t
            assert "*" not in t and "`" not in t
        # first entry should be introduction w/ page 1
        titles = [e["title"] for e in d["entries"]]
        assert any("Introduction" in t for t in titles)
        # typeset lines aligned with dot leaders + page numbers
        lines = d["typeset_lines"]
        assert len(lines) == len(d["entries"])
        assert any(l.rstrip().endswith("1") for l in lines)
        assert all("." in l for l in lines)


# ---------------------------------------------------------------- Preflight
CLEAN_ARTIFACT = {
    "title": "Clean Book", "product_type": "book",
    "body_text": "Clean prose, no markdown, no urls, no placeholders.",
    "toc_entries": [{"level": 1, "title": "Introduction", "page": 1},
                    {"level": 1, "title": "Chapter 1", "page": 7}],
    "heading_levels": [1, 2, 2, 1],
    "fonts_used": ["Playfair Display", "Manrope"], "min_font_pt": 11,
    "contrast_pairs": [{"fg": "#1A2233", "bg": "#FFFFFF", "ratio": 15}],
    "margins_in": {"top": 0.75, "bottom": 0.75, "outer": 0.6, "gutter": 0.85},
    "images": [{"alt": "Diagram", "dpi": 300, "width": 1600}],
    "metadata": {"title": "Clean Book", "author": "QRU", "isbn": "979-8-9921234-2-5"},
    "approvals": [{"by": "Founder", "at": "2026-01-01"}],
    "ai_assets": [], "tokens_version": "1.0",
    "cover": {"thumbnail_readable": True},
}

DEFECTIVE_ARTIFACT = {
    "title": "Bad Book", "product_type": "book",
    "body_text": "## Chapter 1\nSee https://qru.world/foo . TODO write more. Lorem ipsum.",
    "toc_entries": [{"level": 1, "title": "Intro [see](https://x) #intro", "page": None}],
    "heading_levels": [1, 3],
    "fonts_used": ["Arial", "Manrope"], "min_font_pt": 7,
    "contrast_pairs": [{"fg": "#AAAAAA", "bg": "#FFFFFF", "ratio": 2.0}],
    "margins_in": {"top": 0.3, "outer": 0.35, "gutter": 0.4},
    "images": [{"alt": "", "dpi": 96, "width": 300}],
    "metadata": {"title": "Bad Book"}, "approvals": [],
    "ai_assets": [{"id": "c1", "approval_status": "DRAFT_CONCEPT"}],
    "tokens_version": "0.9",
    "cover": {"thumbnail_readable": False},
}


class TestPreflight:
    def test_clean_passes(self, auth):
        r = requests.post(f"{BASE_URL}/api/publishing/preflight",
                          headers=auth, json={"artifact": CLEAN_ARTIFACT}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["verdict"] == "TREASURE_STANDARD_PASSED"
        assert d["blocked"] is False
        assert d["counts"]["BLOCKING_FAILURE"] == 0
        assert "audit_id" in d

    def test_defective_blocks(self, auth):
        r = requests.post(f"{BASE_URL}/api/publishing/preflight",
                          headers=auth, json={"artifact": DEFECTIVE_ARTIFACT}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["verdict"] == "RETURN_TO_PRODUCTION"
        assert d["blocked"] is True
        assert d["counts"]["BLOCKING_FAILURE"] >= 5
        for r_ in d["results"]:
            assert "rule_id" in r_ and "name" in r_ and "why" in r_ \
                and "responsible_module" in r_ and "correction" in r_
        assert "audit_id" in d

    def test_preflight_runs_persisted(self, auth):
        r = requests.get(f"{BASE_URL}/api/publishing/preflight/runs", headers=auth, timeout=30)
        assert r.status_code == 200
        runs = r.json()["runs"]
        assert isinstance(runs, list) and len(runs) >= 1
        assert all("id" in x and "verdict" in x and "blocked" in x for x in runs)


# ---------------------------------------------------------------- Pilot
class TestPilot:
    def test_pilot(self, auth):
        r = requests.get(f"{BASE_URL}/api/publishing/pilot", headers=auth, timeout=30)
        assert r.status_code == 200
        d = r.json()
        pilot = d["pilot"]
        assert "toc_before_raw" in pilot and "##" in pilot["toc_before_raw"]
        assert len(pilot["toc_after_entries"]) >= 4
        # Cleaned titles carry no md/urls/anchors
        for e in pilot["toc_after_entries"]:
            t = e["title"]
            assert "#" not in t and "http" not in t and "[" not in t
        assert d["preflight_before"]["blocked"] is True
        assert d["preflight_before"]["verdict"] == "RETURN_TO_PRODUCTION"
        assert d["preflight_before"]["counts"]["BLOCKING_FAILURE"] >= 5
        assert d["preflight_after"]["blocked"] is False
        assert d["preflight_after"]["verdict"] == "TREASURE_STANDARD_PASSED"


# ---------------------------------------------------------------- Cover Studio
class TestCoverStudio:
    def test_spec_only_generate(self, auth):
        payload = {"title": "TEST Spec-Only Cover", "subtitle": "Iteration 50",
                   "trim": "kdp_ebook", "concept_notes": "test brief", "mode": "spec_only", "concepts": 1}
        r = requests.post(f"{BASE_URL}/api/publishing/cover/generate",
                          headers=auth, json=payload, timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["mode"] == "spec_only"
        assert len(d["concepts"]) == 1
        c = d["concepts"][0]
        assert c["state"] == "DRAFT_CONCEPT"
        assert c["spec_only"] is True
        assert c["file"] is None
        assert c["provenance"]["provider"] == "manual/spec"
        assert "prompt" in c["provenance"]

    def test_list_covers(self, auth):
        r = requests.get(f"{BASE_URL}/api/publishing/covers", headers=auth, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "covers" in d and isinstance(d["covers"], list)
        assert "states" in d and len(d["states"]) == 6

    def test_ai_cover_file_and_states(self, auth):
        # Find an existing AI-generated cover (spec_only False and file present).
        r = requests.get(f"{BASE_URL}/api/publishing/covers", headers=auth, timeout=30)
        assert r.status_code == 200
        covers = r.json()["covers"]
        ai_covers = [c for c in covers if c.get("file") and not c.get("spec_only")]
        if not ai_covers:
            pytest.skip("No AI-generated cover present to test /file endpoint")
        cid = ai_covers[0]["id"]
        # File endpoint returns PNG
        rf = requests.get(f"{BASE_URL}/api/publishing/cover/{cid}/file", timeout=60)
        assert rf.status_code == 200
        assert rf.headers.get("content-type", "").startswith("image/png")
        assert len(rf.content) > 1000

    def test_state_workflow(self, auth):
        # Create a fresh spec-only cover, then walk through states.
        payload = {"title": "TEST State Workflow", "subtitle": "walk", "mode": "spec_only", "concepts": 1}
        r = requests.post(f"{BASE_URL}/api/publishing/cover/generate",
                          headers=auth, json=payload, timeout=30)
        assert r.status_code == 200
        cid = r.json()["concepts"][0]["id"]

        # Illegal state
        r_bad = requests.post(f"{BASE_URL}/api/publishing/cover/{cid}/state",
                              headers=auth, json={"state": "NOT_A_STATE"}, timeout=30)
        assert r_bad.status_code == 400

        # Attempt GOLD_MASTER while DRAFT_CONCEPT → must fail 400
        r_gm = requests.post(f"{BASE_URL}/api/publishing/cover/{cid}/state",
                             headers=auth, json={"state": "GOLD_MASTER"}, timeout=30)
        assert r_gm.status_code == 400

        # DRAFT_CONCEPT → UNDER_REVIEW
        r_ur = requests.post(f"{BASE_URL}/api/publishing/cover/{cid}/state",
                             headers=auth, json={"state": "UNDER_REVIEW"}, timeout=30)
        assert r_ur.status_code == 200
        assert r_ur.json()["state"] == "UNDER_REVIEW"

        # → APPROVED_DESIGN
        r_ap = requests.post(f"{BASE_URL}/api/publishing/cover/{cid}/state",
                             headers=auth, json={"state": "APPROVED_DESIGN"}, timeout=30)
        assert r_ap.status_code == 200
        doc = r_ap.json()
        assert doc["state"] == "APPROVED_DESIGN"
        # History logged
        assert len(doc["history"]) >= 3

        # After APPROVED_DESIGN, GOLD_MASTER should be allowed
        r_gm2 = requests.post(f"{BASE_URL}/api/publishing/cover/{cid}/state",
                              headers=auth, json={"state": "GOLD_MASTER"}, timeout=30)
        assert r_gm2.status_code == 200
        assert r_gm2.json()["state"] == "GOLD_MASTER"
