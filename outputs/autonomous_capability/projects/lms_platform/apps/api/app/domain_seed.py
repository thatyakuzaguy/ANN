"""Idempotent seed definitions for local development."""

from typing import Any

SEED_ROWS: list[dict[str, Any]] = [
    {
        "entity_type": "course",
        "name": "Demo Course",
        "status": "active"
    },
    {
        "entity_type": "lesson",
        "name": "Demo Lesson",
        "status": "active"
    },
    {
        "entity_type": "module",
        "name": "Demo Module",
        "status": "active"
    },
    {
        "entity_type": "enrollment",
        "name": "Demo Enrollment",
        "status": "active"
    },
    {
        "entity_type": "student",
        "name": "Demo Student",
        "status": "active"
    },
    {
        "entity_type": "progress",
        "name": "Demo Progress",
        "status": "active"
    },
    {
        "entity_type": "certificate",
        "name": "Demo Certificate",
        "status": "active"
    }
]


def seed_records() -> list[dict[str, Any]]:
    return [dict(item) for item in SEED_ROWS]
