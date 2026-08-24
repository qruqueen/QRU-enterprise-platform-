# routers package

# QRU Online digital-product commerce is kept in its own module so the proven ebook router stays
# untouched. public_products is already registered by server.py; attaching these fully-qualified
# routes here makes the new commerce surface travel with that public storefront router without
# changing Factory startup wiring.
from . import public_products as _public_products
from . import public_product_commerce as _public_product_commerce
from . import public_storefront_webhook as _public_storefront_webhook

_public_products.router.routes.extend(_public_product_commerce.router.routes)

# Register the hardened unified webhook on public_products, which server.py includes before the
# legacy ebook public_commerce router. Starlette resolves the first matching route, so this safely
# supersedes the older ebook-only /api/public/webhook without modifying the proven ebook module.
_public_products.router.routes.extend(_public_storefront_webhook.router.routes)
