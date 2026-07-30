# Dependency Provisioning

Hash-locked offline dependency inputs and approved ephemeral Compose provisioning.

## Actions

- inspect: Inspect lockfiles, hashes, offline caches, and deterministic dependency inputs.
- run: Provision only hash-locked dependencies into an ephemeral Compose container target.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
