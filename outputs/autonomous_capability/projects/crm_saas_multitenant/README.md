# SaaS CRM

Generated from:

```text
Build a production CRM SaaS with auth, tenancy, billing, workflows, RBAC, tests, and deployment.
```

## Stack

- Next.js, React, TypeScript
- FastAPI, Python, SQLAlchemy
- PostgreSQL
- Docker Compose
- pytest and Playwright

## Run

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

- Web: http://localhost:3000
- API: http://localhost:8000/docs

## Features

- Email/password login scaffold with JWT-compatible token shape
- Accounts, contacts, deals, activities, and pipeline overview
- PostgreSQL schema and SQLAlchemy models
- Alembic migrations
- API health endpoint and CRUD-style CRM endpoints
- Responsive CRM dashboard
- Desktop wrapper scaffold for Windows `.exe` packaging
- Advanced domain blueprint for multi-tenancy, RBAC, billing, integrations, workflows, audit, and dashboard customization
- Docker deployment
- Unit and E2E test scaffolding

## Security

- Secrets are loaded from environment variables.
- Passwords are hashed with PBKDF2.
- CORS is restricted through environment configuration.
- Database credentials are not committed.
