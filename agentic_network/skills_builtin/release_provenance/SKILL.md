# Release Provenance

Release hashes, Authenticode, attestations, and clean-machine evidence.

## Actions

- inspect: Inspect hashes, signatures, attestations, and clean-machine evidence.
- verify: Verify release provenance and Authenticode evidence.
- sign: Run the repository's approved Authenticode signing script.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
