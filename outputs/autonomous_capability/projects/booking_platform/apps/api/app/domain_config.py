"""Generated, deterministic product-domain contract."""

DOMAIN_ID = "booking"
DOMAIN_NAME = "Booking SaaS"
DOMAIN_DESCRIPTION = "Availability, calendars, appointments, staff, reminders, and payments."
ENTITIES = [
    "resource",
    "booking",
    "appointment",
    "availability",
    "calendar",
    "customer",
    "staff",
    "payment"
]
WORKFLOWS = [
    "availability sync",
    "timezone scheduling",
    "reminder",
    "cancellation",
    "no-show followup"
]
INTEGRATIONS = [
    "calendar",
    "Stripe",
    "SMS",
    "email"
]
ENTITY_TYPES = frozenset(ENTITIES)
