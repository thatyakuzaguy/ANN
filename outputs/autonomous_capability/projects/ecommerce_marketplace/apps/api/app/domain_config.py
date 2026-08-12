"""Generated, deterministic product-domain contract."""

DOMAIN_ID = "marketplace"
DOMAIN_NAME = "Marketplace SaaS"
DOMAIN_DESCRIPTION = "Product catalog, carts, sellers, vendors, buyers, orders, payments, and moderation."
ENTITIES = [
    "product",
    "catalog",
    "cart",
    "seller",
    "vendor",
    "buyer",
    "order",
    "payment",
    "payout"
]
WORKFLOWS = [
    "seller onboarding",
    "checkout",
    "dispute",
    "payout review"
]
INTEGRATIONS = [
    "Stripe Connect",
    "storage",
    "email",
    "analytics"
]
ENTITY_TYPES = frozenset(ENTITIES)
