# Slo Telemetry Verification

SLO, error-budget, metric, trace, log, redaction, and alert-contract verification.

## Actions

- inspect: Inspect SLOs, error budgets, metrics, traces, logs, redaction, and alert evidence.
- run: Run only approved telemetry-contract tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
