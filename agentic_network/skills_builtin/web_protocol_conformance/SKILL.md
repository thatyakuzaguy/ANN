# Web Protocol Conformance

HTTP caching, CORS, compression, streaming, retry, and web protocol verification.

## Actions

- inspect: Inspect HTTP caching, CORS, streaming, compression, retry, and protocol-boundary evidence.
- run: Run only approved web-protocol conformance tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
