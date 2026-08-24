# routers package

# QRU Online digital-product commerce is kept in its own module so the proven ebook router stays
# untouched. public_products is already registered by server.py; attaching these fully-qualified
# routes here makes the new commerce surface travel with that public storefront router without
# changing Factory startup wiring.
from . import public_products as _public_products
from . import public_product_commerce as _public_product_commerce

_public_products.router.routes.extend(_public_product_commerce.router.routes)
