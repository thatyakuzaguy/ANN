"""Generated, deterministic product-domain contract."""

DOMAIN_ID = "crm"
DOMAIN_NAME = "SaaS CRM"
DOMAIN_DESCRIPTION = "Tenant-scoped accounts, contacts, deals, activities, billing, and dashboards."
ENTITIES = [
    "tenant",
    "account",
    "contact",
    "deal",
    "activity"
]
WORKFLOWS = [
    "lead qualification",
    "deal escalation",
    "renewal reminder"
]
INTEGRATIONS = [
    "Stripe",
    "email",
    "calendar",
    "Slack"
]
ENTITY_TYPES = frozenset(ENTITIES)
