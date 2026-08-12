# LMS SaaS Architecture

```mermaid
flowchart LR
  Web[Next.js Web] --> API[FastAPI]
  API --> DB[(PostgreSQL)]
  API --> Auth[Password Hashing and Token Issuing]
```

## Boundaries

- `apps/web`: user interface and CRM dashboard.
- `apps/api`: API, auth, business entities, and persistence.
- `database`: reference SQL schema; runtime schema changes are applied through Alembic.
- `docs`: generated architecture, security, and product notes.
