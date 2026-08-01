# Agent Trajectory Forensics

Redacted agent decision, evidence, tool, retry, and terminal-outcome forensics.

## Actions

- analyze: Analyze bounded agent decisions, evidence, tool calls, retries, and terminal outcomes.
- compare: Compare two redacted trajectory summaries without exposing prompts or secrets.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
