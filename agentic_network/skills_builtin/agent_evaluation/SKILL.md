# Agent Evaluation

Golden-task scoring, outcome comparison, latency, retry, and agent-quality evidence.

## Actions

- evaluate: Score agent task outcomes against explicit golden expectations and runtime evidence.
- compare: Compare bounded agent or model evaluation result sets without loading a model.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
