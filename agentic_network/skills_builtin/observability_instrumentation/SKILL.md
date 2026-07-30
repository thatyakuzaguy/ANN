# Observability Instrumentation

Metrics, traces, logs, correlation IDs, dashboards, alerts, and instrumentation planning.

## Actions

- inspect: Inspect metrics, traces, logs, correlation IDs, dashboards, and alert coverage.
- plan: Prepare an OpenTelemetry-compatible instrumentation plan without modifying the project.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
