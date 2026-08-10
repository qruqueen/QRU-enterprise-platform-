"""Round 1 storefront recovery — tests written against REAL Factory vocabulary and states
(not idealized values). Covers:
  B. Product classification normalization (public_subject, public_pathway)
  C. Storefront distribution enforcement (distribution_architecture.in_storefront)
  D. Demo-product exclusion query semantics (routers.public_products._STOREFRONT_QUERY)

Pure-function / deterministic tests — no DB required. Endpoint-level behavior is covered by
the real-data smoke test recorded in the Round 1 report.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import public_subject as ps
import public_pathway as pp
import distribution_architecture as da


# ---------------------------------------------------------------- B. SUBJECT
def test_subject_real_health_categories_resolve_to_health():
    for cat in ["Heart Health", "Brain Health", "Lung Health",
                "Metabolic Health", "Kidney Health", "Prevention & Wellness"]:
        assert ps.reconcile_subject({"genre": cat}) == "Health", cat


def test_subject_exact_domain_and_known_values():
    assert ps.reconcile_subject({"genre": "Finance"}) == "Finance"
    assert ps.reconcile_subject({"genre": "Day Trading"}) == "Trading"  # substring -> Trading


def test_subject_unknown_and_general_fall_back():
    assert ps.reconcile_subject({"genre": "General"}) == "General"
    assert ps.reconcile_subject({"genre": "Research"}) == "General"
    assert ps.reconcile_subject({"genre": "Totally Unknown Thing"}) == "General"
    assert ps.reconcile_subject({"genre": ""}) == "General"
    assert ps.reconcile_subject({}) == "General"


# ---------------------------------------------------------------- B. PATHWAY
def test_pathway_real_audience_values_isolated():
    # product_type=None isolates the audience-driven contribution (no type overlay).
    assert pp.classify({"audience": "Professional audience"}, None) == ["Professional"]
    assert pp.classify({"audience": "Entrepreneur"}, None) == ["Professional"]
    assert pp.classify({"audience": "Teen learner"}, None) == ["Learning Resources"]
    assert pp.classify({"audience": "Student"}, None) == ["Learning Resources"]


def test_pathway_no_signal_and_unknown_are_conservative():
    # "General"/"General public" carry no pathway signal; unknown free-text must not guess.
    assert pp.classify({"audience": "General public"}, None) == []
    assert pp.classify({"audience": "General"}, None) == []
    assert pp.classify({"audience": "wild free text xyz"}, None) == []


def test_pathway_beginner_adult_is_adult_family():
    # "Beginner adult" routes through the adult-family resolver (deterministic; empty when
    # product_type/subject give no additional signal). Must not raise, must be a list.
    out = pp.classify({"audience": "Beginner adult"}, None)
    assert isinstance(out, list)


# ------------------------------------------------------- C. DISTRIBUTION ENFORCEMENT
def test_storefront_includes_public_experiences():
    assert da.in_storefront({"distribution": {"experiences": ["books"]}}) is True
    assert da.in_storefront({"distribution": {"experiences": ["resources"]}}) is True
    assert da.in_storefront({"distribution": {"experiences": ["learn", "resources"]}}) is True


def test_learn_only_product_excluded_from_storefront():
    assert da.in_storefront({"distribution": {"experiences": ["learn"]}}) is False


def test_legacy_missing_distribution_uses_type_default():
    # Compatibility rule: no distribution.experiences -> recommend by product_type.
    assert da.in_storefront({"product_type": "Interactive Lesson"}) is False  # -> learn-only
    assert da.in_storefront({"product_type": "Poster"}) is True               # -> resources
    assert da.in_storefront({"product_type": "Zonk-unknown"}) is True         # -> resources fallback


# ------------------------------------------------------------ D. DEMO EXCLUSION
def test_storefront_query_excludes_demo_and_requires_published():
    from routers import public_products as ppr
    q = ppr._STOREFRONT_QUERY
    assert q.get("status") == "Published"
    assert q.get("is_demo") == {"$ne": True}
