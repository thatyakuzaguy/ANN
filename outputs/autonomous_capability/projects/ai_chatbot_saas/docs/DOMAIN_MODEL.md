# AI Chatbot SaaS Domain Model

## Core Domains

- Identity: users, refresh tokens, memberships.
- Tenancy: tenant records and tenant-scoped business data.
- CRM: accounts, contacts, deals, activities.
- Billing: plans, subscriptions, invoices.
- Automation: workflow definitions and future workflow runs.
- Integrations: external provider connections and webhook boundaries.
- Audit: append-only security and business event history.

## Permission Model

Recommended roles:

- `owner`: full tenant administration.
- `admin`: user, billing, integration, and workflow management.
- `manager`: CRM pipeline and reporting management.
- `contributor`: create and update assigned CRM records.
- `viewer`: read-only access.

Every endpoint that reads or mutates tenant data should require tenant context and role checks.
