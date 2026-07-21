from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SaasTemplate:
    id: str
    name: str
    description: str
    core_entities: list[str]
    workflows: list[str]
    integrations: list[str]


def get_saas_templates() -> list[dict[str, object]]:
    return [asdict(template) for template in _templates()]


def resolve_saas_template(idea: str) -> SaasTemplate:
    """Select a deterministic domain contract from a project request."""

    lowered = idea.lower()
    selectors = (
        ("ai_chatbot", ("chatbot", "ai chat", "assistant saas")),
        ("marketplace", ("marketplace", "multi-vendor", "multivendor")),
        ("ecommerce", ("ecommerce", "e-commerce", "online store", "shop")),
        ("booking", ("booking", "appointment", "reservation")),
        ("lms", ("lms", "learning management", "course platform")),
        ("internal_admin", ("internal admin", "admin dashboard", "backoffice")),
        ("crm", ("crm", "customer relationship", "sales pipeline")),
    )
    selected = next(
        (template_id for template_id, keywords in selectors if any(item in lowered for item in keywords)),
        "crm",
    )
    return next(template for template in _templates() if template.id == selected)


def _templates() -> tuple[SaasTemplate, ...]:
    return (
        SaasTemplate(
            "crm",
            "SaaS CRM",
            "Tenant-scoped accounts, contacts, deals, activities, billing, and dashboards.",
            ["tenant", "account", "contact", "deal", "activity"],
            ["lead qualification", "deal escalation", "renewal reminder"],
            ["Stripe", "email", "calendar", "Slack"],
        ),
        SaasTemplate(
            "ecommerce",
            "Ecommerce SaaS",
            "Catalog, cart, checkout, orders, inventory, fulfillment, and customer support.",
            ["product", "catalog", "cart", "order", "customer", "inventory", "refund"],
            ["checkout", "abandoned cart", "low stock", "refund approval"],
            ["Stripe", "shipping", "email", "analytics"],
        ),
        SaasTemplate(
            "booking",
            "Booking SaaS",
            "Availability, calendars, appointments, staff, reminders, and payments.",
            ["resource", "booking", "appointment", "availability", "calendar", "customer", "staff", "payment"],
            ["availability sync", "timezone scheduling", "reminder", "cancellation", "no-show followup"],
            ["calendar", "Stripe", "SMS", "email"],
        ),
        SaasTemplate(
            "lms",
            "LMS SaaS",
            "Courses, lessons, modules, enrollments, student progress, certificates, and billing.",
            ["course", "lesson", "module", "enrollment", "student", "progress", "certificate"],
            ["course completion", "drip schedule", "assessment review", "certificate issue"],
            ["video", "email", "analytics", "payments"],
        ),
        SaasTemplate(
            "marketplace",
            "Marketplace SaaS",
            "Product catalog, carts, sellers, vendors, buyers, orders, payments, and moderation.",
            ["product", "catalog", "cart", "seller", "vendor", "buyer", "order", "payment", "payout"],
            ["seller onboarding", "checkout", "dispute", "payout review"],
            ["Stripe Connect", "storage", "email", "analytics"],
        ),
        SaasTemplate(
            "internal_admin",
            "Internal Admin Dashboard",
            "Operational admin for users, roles, approvals, audit events, tickets, and reporting.",
            ["user", "role", "permission", "audit_event", "ticket", "report"],
            ["approval routing", "incident triage", "access review"],
            ["SSO", "Slack", "warehouse", "error tracking"],
        ),
        SaasTemplate(
            "ai_chatbot",
            "AI Chatbot SaaS",
            "Tenant chat, conversations, messages, model providers, usage limits, and support handoff.",
            ["chat", "conversation", "message", "model", "provider", "knowledge_base", "usage_event"],
            ["stream response", "support handoff", "quality review", "usage alert"],
            ["local model", "Stripe", "vector store", "helpdesk"],
        ),
    )
