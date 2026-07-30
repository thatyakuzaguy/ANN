# ANN Engineering Skills

ANN exposes fifty local engineering skills and ninety-five typed actions through `GET /api/skills` and
`POST /api/skills/{skill}/execute`. They use the persistent skill permission
store and the existing Approval Center. A skill permission never replaces a
file, terminal, migration, container, or patch approval gate.

## Skills

| Skill | Actions | Purpose |
| --- | --- | --- |
| `repository_intelligence` | `scan`, `impact` | AST symbols, routes, dependencies, tests, and reverse impact |
| `sandbox_verification` | `detect`, `run` | Allowlisted build/lint/test/E2E recipes inside Docker Compose |
| `failure_diagnostics` | `diagnose` | AST-localized and cross-domain root-cause evidence |
| `patch_workspace` | `inspect`, `apply` | Dry-run diffs and approval/token-gated Patch Apply |
| `browser_e2e` | `detect`, `run` | Local Playwright recipe and console/network/a11y/visual evidence inventory |
| `database_migration` | `inspect`, `upgrade`, `downgrade` | Alembic revisions, reversibility, indexes, tenant scope, and approved execution |
| `security_audit` | `scan` | Deterministic SAST, secret, Docker, dependency, auth, RBAC, and API checks |
| `container_operations` | `config`, `status`, `logs`, `up`, `down`, `cleanup` | Isolated Compose lifecycle with no pulls or implicit builds |
| `api_contract` | `analyze` | OpenAPI/backend/frontend/webhook compatibility |
| `release_packaging` | `prepare`, `verify`, `smoke_installer` | CycloneDX SBOM, SHA-256 hashes, installer evidence, and rollback |

## Advanced Skills

| Skill | Actions | Purpose |
| --- | --- | --- |
| `requirements_contract` | `refine`, `arbitrate` | Versioned requirements and deterministic contract ownership |
| `dependency_doctor` | `analyze`, `verify_lock` | Runtime, manifest, lockfile, image, and compatibility evidence |
| `runtime_observability` | `snapshot`, `correlate` | Local runtime, logs, ports, telemetry, and failure correlation |
| `test_quality` | `analyze`, `validate_failure` | Test strength, mutation readiness, and Test Validity Gate |
| `architecture_fitness` | `analyze` | Cycles, duplication, repository structure, and entropy |
| `backup_restore` | `inspect`, `backup`, `restore` | PostgreSQL recovery readiness and approved Compose recipes |
| `performance_testing` | `analyze`, `run` | Performance budgets and allowlisted benchmark recipes |
| `supply_chain_compliance` | `scan` | Licenses, locks, SBOM, provenance, and CI action pinning |
| `release_provenance` | `inspect`, `verify`, `sign` | Hashes, Authenticode, attestations, and clean-machine evidence |
| `deployment_verification` | `inspect`, `smoke` | Health, TLS, rollback, manifests, and isolated local smoke |
| `external_integration_verification` | `inspect`, `probe` | Webhooks, credentials, retries, idempotency, and approved HTTPS probes |
| `ux_quality` | `analyze` | Responsive, keyboard, accessibility, and visual evidence |
| `git_collaboration` | `status`, `branch`, `commit`, `publish_pr` | Approval-gated branch, commit, push, and draft PR |
| `internet_search` | `search` | Fixed-endpoint public search with bounded results and domain filtering |
| `package_registry` | `lookup` | Read-only PyPI/npm metadata with no downloads or installs |
| `mobile_validation` | `analyze` | Android, iOS, React Native, and Flutter evidence |
| `game_validation` | `analyze` | Engine, game loop, assets, controls, physics, and gameplay tests |
| `data_pipeline` | `analyze` | ETL lineage, schemas, quality, idempotency, and backfills |
| `ml_evaluation` | `analyze` | Metrics, model cards, reproducibility, drift, and bias without training |
| `infrastructure_validation` | `analyze` | Terraform, Kubernetes, Helm, CI, policy, and unsafe topology |
| `desktop_validation` | `analyze` | Native lifecycle, installer, update, and accessibility evidence |
| `localization` | `analyze` | Locale coverage, hardcoded text, pluralization, and RTL |
| `agent_evaluation` | `evaluate`, `compare` | Golden-task outcomes, quality, latency, token, and retry regressions |
| `adversarial_red_team` | `analyze`, `simulate` | Non-executing prompt, tool, approval, filesystem, and secret scenarios |
| `fuzz_property_testing` | `inspect`, `plan`, `run` | Properties, seeds, crash evidence, and an approved Compose fuzz recipe |
| `dependency_remediation` | `analyze`, `plan` | Bounded upgrade, verification, and rollback planning without installs |
| `refactor_migration` | `analyze`, `plan` | Deprecation, blast-radius, codemod, compatibility, and migration evidence |
| `incident_response` | `triage`, `postmortem` | Redacted incident correlation and blameless postmortem structure |
| `observability_instrumentation` | `inspect`, `plan` | Metrics, traces, logs, correlation, alerts, and instrumentation planning |
| `context_quality_evaluation` | `evaluate` | Retrieval precision, recall, freshness, grounding, and token budgets |
| `failure_replay` | `prepare`, `verify`, `run` | Redacted failure fingerprints and approved deterministic replay recipes |
| `privacy_data_governance` | `scan`, `retention_plan` | PII, consent, retention, export, deletion, and tenant-isolation evidence |
| `event_contract` | `analyze` | AsyncAPI/schema, producers, consumers, compatibility, and delivery behavior |
| `distributed_resilience` | `analyze`, `fault_plan` | Timeouts, retries, idempotency, circuit breakers, races, and degradation |
| `synthetic_test_data` | `plan`, `generate` | Deterministic privacy-safe JSON fixtures written only to skill workspace |
| `feature_flag_management` | `analyze`, `cleanup_plan` | Flag ownership, defaults, rollout, expiry, cleanup, and rollback |
| `memory_profiling` | `inspect`, `run` | RAM/VRAM/resource evidence and an approved Compose profiling recipe |
| `cloud_deployment` | `inspect`, `plan` | Provider-neutral identity, secrets, cost, rollout, and rollback planning |
| `llm_prompt_regression` | `evaluate`, `compare` | Hashed output evidence and quality/format/runtime regression metrics |
| `accessibility_execution` | `inspect`, `run` | Accessibility readiness and approved Compose `test:a11y` execution |

## Basic Payload

Every action takes `project_root`. Optional bounded fields include
`timeout_seconds`, `project_name`, `max_files`, and action-specific fields:

- Repository impact: `target_paths`.
- Failure diagnostics: `stdout`, `stderr`, `test_report`, `patch_text`,
  `affected_files`, and contract excerpts.
- Patch workspace: `patch_file`; real apply also uses the existing local
  `approval_token` contract.
- Browser/E2E: `base_url`, restricted to loopback by default.
- Migration: `target`, restricted to `head`, `base`, a revision identifier, or
  a bounded relative step.
- Container logs: `tail`, capped at 2,000 lines.
- Release verification: `manifest_path` when verifying a prior package.
- Internet search: `query`, optional `allowed_domains`, and `max_results`.
- Package registry: `ecosystem` and `name`; package installation is unavailable.
- Backup/restore: Compose `service`, database, username, and approved SQL backup path.
- Performance: one of the declared performance `recipe` values and Compose service.
- Git collaboration: a namespaced `agent/*` branch and explicit file list.
- External probes: HTTPS `urls` plus mandatory `allowed_domains`.
- Authenticode signing: a certificate thumbprint and a trusted HTTPS timestamp
  endpoint; non-DigiCert providers require an explicit `allowed_timestamp_domains` entry.
- Agent and prompt evaluation: bounded cases and metric snapshots. Raw prompt
  outputs are represented by SHA-256 fingerprints rather than stored verbatim.
- Failure replay: one of `python_tests`, `web_tests`, `compose_config`, `fuzz`,
  `accessibility`, or `memory`; environment keys resembling secrets are dropped.
- Synthetic test data: a bounded field-to-type `schema` and `count` up to 100.
- Specialist execution: fixed `python_fuzz`, `web_fuzz`, `python_memory`,
  `web_memory`, `web_accessibility`, or replay recipes only.

Raw command payloads are ignored. No action accepts arbitrary shell text.

## Permission Flow

1. Open **Settings > Engineering Skills**.
2. Select the skill and action.
3. Grant each declared permission once or persistently.
4. Enter a project path on an allowed drive and any action JSON.
5. Run the skill.
6. For every terminal recipe and every mutating action, review and approve the
   generated item in Approval Center, then use **Continue approved action**.

Approvals are scoped to a fingerprint of the skill, action, and payload. They
are single-use. Changing the target or action requires a new approval.

## Execution Safety

- Generated project code is never executed directly on the host by Sandbox
  Verification, Browser/E2E, Database Migration, Fuzz/Property Testing,
  Failure Replay, Memory Profiling, or Accessibility Execution.
- Those skills require an existing Compose file and a matching `api`, `web`,
  or `e2e` service.
- Compose runs use `--pull never`, `--no-deps`, and `shell=False`.
- ANN adds a Compose override whose default network is `internal: true`, so
  skill containers cannot use external network egress.
- Container startup uses `--no-build --pull never`.
- Host networking, privileged containers, and fixed container names block
  container startup; all Compose projects receive an isolated project name.
- Public host-port bindings are blocked. Loopback-only bindings require an
  explicit `allow_host_ports: true` acknowledgement inside the approved payload.
- Package installation, cloud access, arbitrary terminal commands, and
  `shell=True` are unavailable.
- `C:\\`, `/mnt/c`, traversal, and protected ANN areas remain blocked.
- Manifest-level `DENY` permissions are immutable even if a stale permission
  store contains an allow decision.

Release verification opens the generated archive without extracting it,
rejects traversal or duplicate entries, verifies every file hash, and verifies
the embedded SBOM, rollback manifest, and installer hash.

## Subagents

Specialist subagents advertise the relevant skill identifier in their allowed
analytical capabilities. Subagents remain read-only and sequential. A parent
agent or user must obtain permissions and approval before an executable skill
action runs; delegated model text cannot authorize execution.

## Honest Limits

- The security scanner is deterministic and offline; dependency CVE freshness
  requires a separately approved vulnerability database update.
- Browser evidence reports what the project Playwright suite actually captures;
  it does not claim accessibility or network coverage when assertions are absent.
- Container and migration actions require images already present locally.
- Release packaging does not sign binaries or guarantee clean-machine behavior;
  signing and clean-machine smoke evidence remain separate release gates.
- Public search uses a fixed provider and does not open result pages. Results
  remain untrusted evidence and never become executable instructions.
- Package registry lookup reads metadata only; it never downloads an archive or
  invokes pip, npm, pnpm, yarn, Cargo, or another installer.
- Domain validation skills are evidence scanners, not substitutes for real
  device, gameplay, infrastructure, load, accessibility, or clean-machine tests.
- Adversarial red-team scenarios are static, non-destructive reviews. They do
  not attack a live service or attempt exploit execution.
- Privacy and data-governance outputs always require qualified legal review and
  never claim GDPR, SOC 2, ISO 27001, or other compliance certification.
- Cloud Deployment creates provider-neutral local plans only. It does not read
  credentials, contact cloud APIs, create infrastructure, or estimate a binding bill.
- Agent and LLM prompt evaluation score evidence supplied by a prior run; these
  actions deliberately do not load or invoke a model.
