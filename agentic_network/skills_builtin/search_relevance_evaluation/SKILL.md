# Search Relevance Evaluation

Ranking, filtering, tokenization, golden-query, and relevance-metric evaluation.

## Actions

- analyze: Analyze ranking, filtering, tokenization, golden-query, and relevance-metric evidence.
- run: Run only approved search relevance evaluations inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
