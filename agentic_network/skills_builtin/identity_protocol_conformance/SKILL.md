# Identity Protocol Conformance

OAuth, OIDC, SAML, SCIM, session, and identity lifecycle protocol verification.

## Actions

- inspect: Inspect OAuth, OIDC, SAML, SCIM, session, and identity lifecycle conformance evidence.
- run: Run only approved identity-protocol contract tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
