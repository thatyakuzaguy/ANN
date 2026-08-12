# Independent Security Review Preparation

Status: `PENDING_INDEPENDENT_REVIEW`

This packet prepares evidence for an independent security reviewer. It is not an
independent assessment and does not claim approval.

## Available automated evidence

- Python and frontend dependency audits are part of the release gate.
- Secret, repository-boundary, command allowlist, installer, Docker, auth, RBAC,
  API, and generated-project security checks are covered by repository tests and
  security scripts.
- The official soak completed 20 of 20 runs with zero counted failures and clean
  sequential-model rollback.
- Seven autonomous project archetypes preserved portable lifecycle, security,
  build, test, E2E, and visual evidence where applicable.
- Model weights, private adapters, datasets, credentials, and local absolute model
  files are excluded from the public repository.

## Reviewer work still required

An independent reviewer must inspect the exact release commit, reproduce the
security gates, assess trust boundaries and threat assumptions, record findings,
and sign an `APPROVED` or `APPROVED_WITH_LIMITATIONS` decision. Until then,
`independent=false` and the production assurance gate remains blocked.
