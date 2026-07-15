"""QRU Product Manufacturing System™ — Manufacturing Recipe Registry (7-button workflow).

The seven-button workflow (Upload · Proof & Polish · Design · Audio · Video · Publish · Monitor) is a
UNIVERSAL manufacturing interface. Each product type registers a MANUFACTURING RECIPE that specializes
only the product-specific stages (intake profile, design brief, distribution set), while the shared
orchestration — governance, release gates, Publication Sanitization Pass™, Master Output Package and
Factory Library™ — remains an INHERITED standard, never duplicated per product.

    Interface remains constant. Recipes specialize.

Product-type labels are reused from the existing product catalog (`product_recipes`) so there is one
owner for that vocabulary (inherited standards instead of duplicated workflows).
"""
import product_recipes as catalog

SYSTEM_TITLE = "QRU Product Manufacturing System™"
_DEFAULT = "Book"
_REGISTRY = {}


def register(recipe):
    """Register a manufacturing recipe for a product type. Product types plug in here without
    touching the shared engine or the Founder's seven-button interface."""
    _REGISTRY[recipe["product_type"]] = recipe
    return recipe


def get(product_type):
    return _REGISTRY.get(product_type) or _REGISTRY.get(_DEFAULT)


def list_recipes():
    return [{"product_type": r["product_type"], "label": r["label"], "description": r["description"],
             "intake": r.get("intake", {})} for r in _REGISTRY.values()]


def label_for(product_type):
    return catalog.get_recipe(product_type).get("label", "QRU Product Recipe™")
