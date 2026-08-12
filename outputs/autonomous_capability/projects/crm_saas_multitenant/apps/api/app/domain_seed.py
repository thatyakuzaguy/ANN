"""Idempotent seed definitions for local development."""

from typing import Any

SEED_ROWS: list[dict[str, Any]] = [
    {
        "entity_type": "tenant",
        "name": "Demo Tenant",
        "status": "active"
    },
    {
        "entity_type": "account",
        "name": "Demo Account",
        "status": "active"
    },
    {
        "entity_type": "contact",
        "name": "Demo Contact",
        "status": "active"
    },
    {
        "entity_type": "deal",
        "name": "Demo Deal",
        "status": "active"
    },
    {
        "entity_type": "activity",
        "name": "Demo Activity",
        "status": "active"
    }
]


def seed_records() -> list[dict[str, Any]]:
    return [dict(item) for item in SEED_ROWS]
