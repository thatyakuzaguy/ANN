"""Generated, deterministic product-domain contract."""

DOMAIN_ID = "lms"
DOMAIN_NAME = "LMS SaaS"
DOMAIN_DESCRIPTION = "Courses, lessons, modules, enrollments, student progress, certificates, and billing."
ENTITIES = [
    "course",
    "lesson",
    "module",
    "enrollment",
    "student",
    "progress",
    "certificate"
]
WORKFLOWS = [
    "course completion",
    "drip schedule",
    "assessment review",
    "certificate issue"
]
INTEGRATIONS = [
    "video",
    "email",
    "analytics",
    "payments"
]
ENTITY_TYPES = frozenset(ENTITIES)
