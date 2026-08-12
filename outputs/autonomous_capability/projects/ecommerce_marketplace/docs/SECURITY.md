# Security

- Do not commit `.env`.
- Replace `JWT_SECRET` before sharing the app.
- Passwords are stored with PBKDF2 hashes.
- CORS is environment-controlled.
- Database credentials live in environment variables.
- Stripe, webhook, and provider secrets live in environment variables or vault-backed runtime secrets.
- Add gateway rate limiting and refresh-token rotation before internet deployment.
