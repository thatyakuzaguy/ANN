"""Advanced production domain blueprint for Marketplace SaaS.

This file documents domain modules that are intentionally separated from
transport code so future agents can implement them incrementally.
"""

DOMAIN_CAPABILITIES = {
    "multi_tenancy": [
        "tenant isolation on every business row",
        "membership-based tenant access",
        "tenant-aware audit log",
    ],
    "rbac": [
        "roles: owner, admin, manager, contributor, viewer",
        "permission checks per endpoint",
        "least-privilege service accounts",
    ],
    "billing": [
        "plans",
        "subscriptions",
        "invoices",
        "payment provider adapter boundary",
    ],
    "workflows": [
        "pipeline automations",
        "activity reminders",
        "webhook triggers",
        "workflow run history",
    ],
    "integrations": [
        "email provider adapter",
        "calendar provider adapter",
        "webhook signing",
        "CRM import/export",
    ],
    "hardening": [
        "refresh token rotation",
        "rate limiting",
        "CSP and security headers",
        "secret manager adapter",
        "dependency scanning",
    ],
}
