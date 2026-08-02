# Cryptographic Protocol Verification

TLS, JWT, key rotation, password hashing, randomness, and unsafe cryptographic-use verification.

## Actions

- inspect: Inspect TLS, JWT, rotation, hashing, randomness, and unsafe cryptographic usage evidence.
- run: Run only approved cryptographic protocol tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
