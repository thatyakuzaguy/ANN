# Supply Chain Compliance

License, lockfile, SBOM, provenance, and dependency policy evidence.

## Actions

- scan: Audit licenses, lockfiles, provenance, SBOM, and dependency policy.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
