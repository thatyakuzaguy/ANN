# Secure Update Delivery

Offline update metadata, signature, hash, expiry, freeze, and rollback verification.

## Actions

- inspect: Inspect offline update metadata, version monotonicity, expiry, hashes, signatures, and rollback policy.
- verify: Verify supplied update evidence without downloading, installing, or publishing anything.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
