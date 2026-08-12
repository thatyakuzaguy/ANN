"""Idempotent seed definitions for local development."""

from typing import Any

SEED_ROWS: list[dict[str, Any]] = [
    {
        "entity_type": "chat",
        "name": "Demo Chat",
        "status": "active"
    },
    {
        "entity_type": "conversation",
        "name": "Demo Conversation",
        "status": "active"
    },
    {
        "entity_type": "message",
        "name": "Demo Message",
        "status": "active"
    },
    {
        "entity_type": "model",
        "name": "Demo Model",
        "status": "active"
    },
    {
        "entity_type": "provider",
        "name": "Demo Provider",
        "status": "active"
    },
    {
        "entity_type": "knowledge_base",
        "name": "Demo Knowledge Base",
        "status": "active"
    },
    {
        "entity_type": "usage_event",
        "name": "Demo Usage Event",
        "status": "active"
    }
]


def seed_records() -> list[dict[str, Any]]:
    return [dict(item) for item in SEED_ROWS]
