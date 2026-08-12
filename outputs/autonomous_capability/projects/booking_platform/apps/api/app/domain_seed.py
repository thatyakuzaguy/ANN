"""Idempotent seed definitions for local development."""

from typing import Any

SEED_ROWS: list[dict[str, Any]] = [
    {
        "entity_type": "resource",
        "name": "Demo Resource",
        "status": "active"
    },
    {
        "entity_type": "booking",
        "name": "Demo Booking",
        "status": "active"
    },
    {
        "entity_type": "appointment",
        "name": "Demo Appointment",
        "status": "active"
    },
    {
        "entity_type": "availability",
        "name": "Demo Availability",
        "status": "active"
    },
    {
        "entity_type": "calendar",
        "name": "Demo Calendar",
        "status": "active"
    },
    {
        "entity_type": "customer",
        "name": "Demo Customer",
        "status": "active"
    },
    {
        "entity_type": "staff",
        "name": "Demo Staff",
        "status": "active"
    },
    {
        "entity_type": "payment",
        "name": "Demo Payment",
        "status": "active"
    }
]


def seed_records() -> list[dict[str, Any]]:
    return [dict(item) for item in SEED_ROWS]
