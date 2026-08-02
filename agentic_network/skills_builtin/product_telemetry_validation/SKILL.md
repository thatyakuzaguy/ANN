# Product Telemetry Validation

Event taxonomy, identity, consent, PII, funnel, experiment, and telemetry-quality verification.

## Actions

- analyze: Inspect event taxonomy, identity, consent, PII, funnels, experiments, and telemetry quality.
- run: Run only approved product telemetry contract tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
