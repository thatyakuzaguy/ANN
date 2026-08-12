# Constraint-Aware Route Optimizer

Generated from:

```text
Build a service implementing a complex algorithm with correctness tests, benchmarks, and edge cases.
```

This FastAPI service implements deterministic K-shortest loopless paths using
Yen's algorithm over a validated weighted directed graph. It includes
correctness tests, integration tests, edge-case validation, and a reproducible
benchmark.

## Run

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Verify

```powershell
python -m pytest tests -q
python benchmark.py
```
