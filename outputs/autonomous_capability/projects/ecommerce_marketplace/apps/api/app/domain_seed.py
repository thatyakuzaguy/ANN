"""Idempotent seed definitions for local development."""

from typing import Any

SEED_ROWS: list[dict[str, Any]] = [
    {
        "entity_type": "product",
        "name": "Demo Product",
        "status": "active"
    },
    {
        "entity_type": "catalog",
        "name": "Demo Catalog",
        "status": "active"
    },
    {
        "entity_type": "cart",
        "name": "Demo Cart",
        "status": "active"
    },
    {
        "entity_type": "seller",
        "name": "Demo Seller",
        "status": "active"
    },
    {
        "entity_type": "vendor",
        "name": "Demo Vendor",
        "status": "active"
    },
    {
        "entity_type": "buyer",
        "name": "Demo Buyer",
        "status": "active"
    },
    {
        "entity_type": "order",
        "name": "Demo Order",
        "status": "active"
    },
    {
        "entity_type": "payment",
        "name": "Demo Payment",
        "status": "active"
    },
    {
        "entity_type": "payout",
        "name": "Demo Payout",
        "status": "active"
    }
]


def seed_records() -> list[dict[str, Any]]:
    return [dict(item) for item in SEED_ROWS]
