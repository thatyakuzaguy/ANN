# ANN Specialist Skills

ANN's specialist wave extends the existing skill registry rather than adding a
second runtime. Every action is typed, permission-scoped, audited, and available
through the same API, desktop skill views, Approval Center, and evidence store.

## Capability Groups

| Group | Skills |
| --- | --- |
| Quality and evaluation | Agent Evaluation, Context Quality Evaluation, LLM Prompt Regression |
| Failure prevention and recovery | Fuzz & Property Testing, Failure Replay, Incident Response, Memory Profiling |
| Architecture and operations | Refactor & Code Migration, Observability Instrumentation, Event Contract, Distributed Resilience, Feature Flag Management |
| Security and governance | Adversarial Red Team, Dependency Remediation, Privacy & Data Governance |
| Delivery | Synthetic Test Data, Cloud Deployment, Accessibility Execution |

## Execution Boundary

Most actions are deterministic read-only analyzers. Four skills expose a `run`
action: fuzz/property testing, failure replay, memory profiling, and
accessibility execution. Those actions require persistent permission plus a
single-use Approval Center decision. They accept a recipe identifier, never raw
shell text, and run an existing local image with Docker Compose using
`shell=False`, `--pull never`, `--no-deps`, and an internal-only network.

ANN rejects unknown recipes, missing Compose services, unsafe package scripts,
path traversal, protected paths, command metacharacters, and attempts to use an
unapproved action. Package installation is not an available specialist action.

## Evidence Handling

- Agent and prompt evaluations consume explicit prior-run outcomes and do not
  invoke or load an LLM.
- Prompt outputs, incident events, and replay logs are stored as SHA-256
  fingerprints and aggregate metrics instead of raw potentially sensitive text.
- Failure Replay retains only bounded, allowlisted environment keys and drops
  credential-like names.
- Synthetic Test Data is deterministic, capped at 100 records, uses reserved
  `example.invalid` email addresses, and writes only inside the skill workspace.
- Cloud Deployment is offline planning only and never accesses provider accounts.
- Privacy findings explicitly require qualified human and legal review.

## Subagent Use

Existing principal agents may delegate analysis to their controlled read-only
subagents. A delegated tool name is capability metadata, not authority: a model
cannot grant a permission, approve a command, mutate a project, or apply a diff.
Executable actions still return through the central skill runtime and Approval
Center.

## Limits

Static evidence cannot prove the absence of vulnerabilities, memory leaks,
accessibility defects, production incidents, or compliance gaps. A successful
recipe proves only that the selected local command passed in the tested sandbox
and revision. Production deployment, legal compliance, destructive fault
injection, cloud credentials, and live red-team activity remain human-owned.
