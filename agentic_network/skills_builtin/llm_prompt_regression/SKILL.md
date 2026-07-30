# Llm Prompt Regression

Golden prompt cases, output quality, format, latency, token, and regression comparison evidence.

## Actions

- evaluate: Evaluate bounded prompt cases against explicit expected output evidence without model loading.
- compare: Compare prompt-suite result sets for quality, format, latency, and token regressions.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
