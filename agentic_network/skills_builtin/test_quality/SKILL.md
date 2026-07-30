# Test Quality

Test strength, mutation readiness, and deterministic failed-test validity review.

## Actions

- analyze: Measure test quality, weak assertions, skips, and mutation readiness.
- validate_failure: Challenge a failed test through the existing Test Validity Gate.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
