# Distributed Resilience

Timeout, retry, idempotency, circuit breaker, concurrency, degradation, and fault-plan evidence.

## Actions

- analyze: Inspect timeouts, retries, idempotency, circuit breakers, concurrency, and degradation.
- fault_plan: Create a non-executing fault-injection and recovery verification plan.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
