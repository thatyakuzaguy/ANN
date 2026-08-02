# Sdk Contract Conformance

OpenAPI, generated SDK, versioning, error mapping, and approved client-contract verification.

## Actions

- analyze: Compare OpenAPI evidence, generated SDK surfaces, versioning, errors, and contract tests.
- run: Run only approved SDK contract-conformance tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
