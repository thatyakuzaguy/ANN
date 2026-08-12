# Security

- Pydantic bounds graph size, K, identifiers, and edge weights.
- The algorithm does not execute user code or shell commands.
- The container is read-only and uses `no-new-privileges`.
- Production deployments should add authentication, tenant quotas, and request
  rate limiting at the API gateway.
