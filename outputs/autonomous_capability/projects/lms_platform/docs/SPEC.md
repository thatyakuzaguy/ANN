# LMS SaaS Specification

Original idea: Build an LMS with courses, lessons, quizzes, progress tracking, roles, certificates, and analytics.

## Core Workflows

- Register and log in.
- Manage accounts and contacts.
- Track deals through qualified, proposal, negotiation, and won stages.
- View dashboard metrics for accounts, contacts, open deals, and pipeline value.
- Run locally through Docker Compose.

## Acceptance Criteria

- API exposes health, auth, dashboard, accounts, contacts, and deals endpoints.
- Frontend renders a CRM workspace without external services.
- Database schema supports users, accounts, contacts, and deals.
- Secrets are provided through `.env`.
- Unit and E2E test scaffolds are present.
