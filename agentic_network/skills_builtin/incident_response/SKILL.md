# Incident Response

Bounded incident triage, timeline correlation, impact assessment, and blameless postmortem evidence.

## Actions

- triage: Correlate bounded logs, events, releases, and health evidence into an incident assessment.
- postmortem: Generate a blameless postmortem draft with evidence, impact, and prevention actions.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
