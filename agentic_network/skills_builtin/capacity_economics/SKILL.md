# Capacity Economics

Throughput, latency, memory, concurrency, and non-binding capacity planning from approved benchmarks.

## Actions

- analyze: Analyze supplied throughput, latency, memory, concurrency, and non-binding capacity evidence.
- benchmark: Run only an approved capacity benchmark inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
