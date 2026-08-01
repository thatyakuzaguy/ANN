# Asset Provenance

Hashed asset inventory, source, license, attribution, and legal-review evidence.

## Actions

- scan: Inventory bounded visual, audio, font, and binary assets with hashes and attribution evidence.
- verify: Gate supplied asset provenance without claiming legal clearance.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
