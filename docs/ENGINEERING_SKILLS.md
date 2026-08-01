# ANN Engineering Skills

ANN exposes one hundred four local engineering skills and two hundred one typed actions through `GET /api/skills` and
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
| `dependency_provisioning` | `inspect`, `run` | Offline hash-locked dependency materialization inside an ephemeral Compose container |
| `semantic_code_transformation` | `analyze`, `prepare` | Token-aware Python symbol changes emitted as approval-required unified diffs |
| `test_generation` | `analyze`, `generate` | Bounded deterministic pytest contracts written only to the skill workspace |
| `mutation_testing` | `inspect`, `run` | Mutation readiness and approved Python or web mutation recipes |
| `visual_regression` | `inspect`, `run` | Playwright visual-regression evidence through an approved web recipe |
| `service_virtualization` | `inspect`, `generate` | Credential-free deterministic external-service mock contracts |
| `consumer_contract_testing` | `analyze`, `run` | Producer/consumer compatibility evidence and approved contract tests |
| `architecture_refactor_execution` | `analyze`, `prepare` | Architecture evidence plus dry-run validation through the existing Patch Workspace gate |
| `infrastructure_plan_execution` | `inspect`, `run` | Offline Terraform plan execution in a pre-existing Compose service |
| `schema_drift_data_evolution` | `inspect`, `run` | Schema-evolution evidence and approved Alembic drift checks |
| `chaos_verification` | `inspect`, `run` | Resilience evidence and approved deterministic chaos-test recipes |
| `release_rollback` | `inspect`, `run` | Rollback evidence and approved release-rollback verification |
| `semantic_repository_search` | `query` | Bounded deterministic repository search without model loading or raw-source artifacts |
| `queue_broker_verification` | `inspect`, `run` | Queue contract evidence and approved broker-focused tests |
| `data_quality_execution` | `inspect`, `run` | Data-quality evidence and approved invariant tests |
| `secrets_lifecycle` | `inspect`, `plan` | Secret ownership, rotation, revocation, and incident planning without reading secret values |
| `cross_platform_matrix` | `inspect`, `run` | Compatibility evidence and approved platform-tagged tests |
| `documentation_drift` | `analyze`, `run` | Documentation/source drift evidence and approved documentation tests |

## Delivery Assurance Skills

| Skill | Actions | Purpose |
| --- | --- | --- |
| `requirements_traceability` | `analyze`, `verify` | Requirement-to-architecture, implementation, test, and release trace graph |
| `git_history_intelligence` | `analyze` | Pseudonymized bounded churn, ownership, co-change, and regression hotspots |
| `database_query_performance` | `inspect`, `run` | Query plans, indexes, N+1, locks, budgets, and approved database tests |
| `stateful_workflow_verification` | `analyze`, `run` | States, transitions, invariants, idempotency, and recovery tests |
| `concurrency_correctness` | `inspect`, `run` | Races, deadlocks, atomicity, cancellation, and deterministic stress tests |
| `reproducible_build_verification` | `inspect`, `run` | Locked inputs, deterministic artifacts, hashes, SBOM, and repeat builds |
| `configuration_parity` | `analyze` | Environment-key parity without reading configuration secret values |
| `slo_telemetry_verification` | `inspect`, `run` | SLO, metric, trace, log, redaction, alert, and telemetry-contract evidence |
| `user_journey_synthesis` | `analyze`, `generate` | Reviewable user journeys and workspace-only E2E specifications |
| `upgrade_compatibility` | `inspect`, `run` | Runtime, framework, database, deprecation, migration, and upgrade tests |
| `disaster_recovery_drill` | `inspect`, `run` | RPO/RTO, backup, restore, integrity, and isolated recovery tests |
| `release_channel_management` | `inspect`, `verify` | Alpha/beta/RC/stable promotion, compatibility, hashes, and rollback evidence |
| `clean_machine_certification` | `inspect`, `verify` | Evidence gate for isolated install, first run, uninstall, and residue scans |
| `signed_vulnerability_intelligence` | `inspect`, `verify` | Freshness and provenance gate for externally verified signed local feeds |
| `policy_as_code` | `inspect`, `run` | OPA/Rego/Conftest evidence and approved offline policy tests |
| `formal_model_checking` | `inspect`, `run` | TLA+/PlusCal/Alloy evidence and approved bounded model-check recipes |
| `coverage_guided_test_synthesis` | `analyze`, `generate` | Ranked coverage/mutation gaps and workspace-only test plans |
| `architectural_debt_ledger` | `snapshot`, `compare` | Architecture debt metrics, markers, trend, and repayment evidence |

## Supreme Engineering Skills

| Skill | Actions | Purpose |
| --- | --- | --- |
| `project_archetype_synthesis` | `analyze`, `synthesize` | Classify API, SaaS, game, desktop, CLI, data, infrastructure, and library products and emit a bounded blueprint |
| `behavioral_acceptance_oracle` | `analyze`, `run` | Trace requirements to observable behavior and approved acceptance tests |
| `dynamic_authorization_verification` | `inspect`, `run` | Map endpoint, role, tenant, and access-control boundaries and run approved authorization tests |
| `long_horizon_checkpoint_integrity` | `inspect`, `run` | Verify checkpoint, idempotency, replay, approval, atomicity, and recovery controls |
| `agent_trajectory_forensics` | `analyze`, `compare` | Redacted decision, evidence, tool-call, retry, and terminal-outcome analysis |
| `delegation_optimizer` | `analyze`, `plan` | Detect duplicate work, missing ownership, load imbalance, and weak acceptance criteria |
| `cross_language_semantic_graph` | `scan`, `impact` | Index symbols/imports and rank impact across Python, TS/JS, Go, Rust, Java, and C# |
| `flaky_test_investigator` | `analyze`, `run` | Analyze outcome/timing variance and run an approved repeated-test recipe |
| `online_migration_rehearsal` | `inspect`, `run` | Verify expand-contract, backfill, lock, compatibility, tenancy, and rollback evidence |
| `local_resource_guardian` | `snapshot`, `plan`, `cleanup` | Measure bounded project storage and clean only the isolated Compose project after approval |
| `secure_update_delivery` | `inspect`, `verify` | Verify offline signed metadata, hashes, expiry, monotonic versions, and rollback protection |
| `installer_vm_lab` | `inspect`, `run` | Gate clean-VM install, first-launch, upgrade, uninstall, rollback, and residue evidence |
| `model_runtime_certification` | `inspect`, `benchmark` | Gate backend/device/load-run-unload/rollback evidence through approved certification tests |
| `api_abuse_simulation` | `inspect`, `run` | Derive and execute approved non-destructive authz, rate, replay, input, and resource scenarios |
| `performance_regression_bisect` | `analyze`, `run` | Identify the first evidenced benchmark regression without mutating Git history |
| `asset_provenance` | `scan`, `verify` | Hash assets and require source, license, attribution, and legal-review evidence |
| `domain_invariant_mining` | `analyze`, `generate` | Mine candidate business invariants and generate a reviewable workspace-only catalog |
| `ai_governance_evidence` | `assess`, `compare` | Assess AI inventory, risk, evaluation, oversight, privacy/security, and incident evidence without compliance claims |

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
  `web_memory`, `web_accessibility`, dependency-lock, mutation, visual,
  contract, Terraform-plan, schema-drift, chaos, rollback, queue,
  data-quality, compatibility, documentation, or replay recipes only.
- Delivery-assurance execution: fixed database-performance, stateful-workflow,
  concurrency, reproducible-build, telemetry, upgrade, disaster-recovery,
  policy, and formal-model markers/scripts only.
- Supreme execution: fixed behavioral-oracle, authorization, checkpoint,
  flaky-test, online-migration, installer-lab, model-runtime, API-abuse, and
  performance-history markers plus isolated Compose cleanup only.

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
  container startup; Docker socket mounts and host PID/IPC namespaces also
  block every executable recipe. All Compose projects receive an isolated
  project name.
- Public host-port bindings are blocked. Loopback-only bindings require an
  explicit `allow_host_ports: true` acknowledgement inside the approved payload.
- Host package installation, cloud access, arbitrary terminal commands, and
  `shell=True` are unavailable. Dependency Provisioning can only consume a
  SHA-256-hashed `requirements.lock` with `pip --no-index --require-hashes`
  into `/tmp/ann-dependencies` inside an approved ephemeral container.
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
- Semantic transformations and generated tests are proposals only. They write
  to the isolated skill workspace and require Patch Workspace plus Approval
  Center before any project file can change.
- Semantic Repository Search is deterministic term expansion, not embedding or
  model-based semantic retrieval. It stores paths and match metadata, not raw
  source excerpts.
- Service Virtualization emits synthetic contracts; it does not start a mock
  server, copy credentials, or contact a real provider.
- Requirements Traceability relies on explicit stable requirement identifiers;
  prose without IDs remains review evidence rather than a guaranteed trace.
- Git History Intelligence hashes author identities and does not store commit
  messages. Its bounded history window is not a complete ownership record.
- Clean Machine Certification validates evidence produced by an isolated VM;
  it deliberately does not execute an installer directly on the ANN host.
- Signed Vulnerability Intelligence gates prior cryptographic verification
  evidence. It neither downloads a feed nor implements a certificate authority.
- Formal, concurrency, recovery, SLO, and reproducible-build results are only as
  strong as the project-supplied sandbox tests and their declared invariants.
- Archetype synthesis and invariant mining produce evidence-based proposals,
  not proof that a generated architecture or business rule is correct.
- Installer VM Lab validates supplied VM evidence and a project-provided
  sandbox recipe; it does not execute an installer directly on the host.
- Model Runtime Certification does not modify, train, or download models. A
  `SUCCESS` result requires explicit load, inference, unload, device, and
  rollback evidence from the approved recipe.
- Asset Provenance never claims copyright or license clearance. Legal review
  remains required before public distribution.
- AI Governance Evidence is an engineering checklist and comparison tool. It
  does not guarantee EU AI Act, NIST AI RMF, ISO, or other compliance.
