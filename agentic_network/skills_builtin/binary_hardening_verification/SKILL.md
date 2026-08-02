# Binary Hardening Verification

Binary integrity, signing, SBOM, mitigation, update, and rollback evidence verification.

## Actions

- inspect: Inspect signing, hashes, SBOM, mitigations, update, and binary release evidence.
- verify: Verify attested external binary-lab evidence without launching host binaries.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
