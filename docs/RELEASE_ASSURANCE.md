# ANN Release Assurance

ANN separates **technical release readiness** from **production assurance**.
Passing unit tests, building the installer, signing binaries, and validating a
clean Windows machine are necessary, but they do not prove long-running
reliability, legal clearance, independent security review, or the quality of
generated products.

The public final-release CLI therefore requires six external evidence records.
It never creates passing records on its own.

## Required Evidence

| Record | Minimum acceptance |
|---|---|
| `hardware_matrix.json` | Two clean Windows 11 machines, two distinct GPU profiles, install/uninstall, inference, and project smoke passed |
| `soak_validation.json` | At least 8 hours, 20 runs, 3 project archetypes, <=2% failures, sequential model and rollback invariants preserved |
| `independent_security_review.json` | Named independent reviewer, approved decision, no open critical or high findings |
| `legal_review.json` | Named qualified human review covering distribution, privacy, model licensing, and terms |
| `model_license_review.json` | A decision for every supported model; no model weights committed to the public repository |
| `generated_software_acceptance.json` | Human acceptance of at least three green projects from three archetypes |

Each JSON record references a report stored beside it through `report_path`
and binds that report with `report_sha256`. Absolute paths and traversal are
rejected. Evidence older than 180 days is rejected by default.

## Initialize Pending Templates

From the repository root:

```powershell
$env:PYTHONPATH="."
python scripts/runtime/verify_release_assurance.py --init-evidence
```

This creates deliberately incomplete records under
`outputs/release_assurance/external`. Existing evidence is never overwritten.
The generated records use `PENDING` decisions and cannot pass verification.

For every record:

1. Perform the real validation described by the policy.
2. Preserve the full report in the same evidence directory.
3. Compute its digest with `Get-FileHash -Algorithm SHA256`.
4. Fill the JSON with the actual UTC collection time, relative report path,
   digest, reviewer identity, results, and decision.
5. Do not convert an unresolved limitation into an approved decision.

## Verify Assurance

```powershell
$env:PYTHONPATH="."
python scripts/runtime/verify_release_assurance.py --json
```

Artifacts are written to `outputs/release_assurance/verification`:

- `374_release_assurance_verification.json`
- `375_release_assurance_verification.md`

The final release verifier runs the same gate automatically:

```powershell
$env:PYTHONPATH="."
python scripts/runtime/verify_final_release.py `
  --install-root D:\ANN `
  --installer-root installer `
  --bundle-root outputs\release_candidates\ANN_RC_HANDOFF `
  --clean-machine-marker D:\ANN\clean_machine_external_validation.json `
  --signing-evidence installer\release_signing_evidence.json `
  --certificate-thumbprint "<REAL_40_CHARACTER_SHA1_THUMBPRINT>" `
  --assurance-evidence-root outputs\release_assurance\external `
  --output-dir outputs\runtime_finalization
```

`FINAL_RELEASE_READY` is impossible from this command while any production
assurance item is missing, stale, malformed, tampered with, or below policy.

## Collection Protocol

### Hardware and clean machines

Use isolated Windows 11 machines or VMs that have not previously installed
ANN. Preserve OS build, GPU, driver, RAM, installer hashes, install result,
first-run result, local inference result, generated-project smoke, uninstall,
and residue checks. At least one machine should match the documented 8 GB VRAM
baseline; another must use a distinct GPU profile.

### Prolonged project validation

Run real, approval-gated ANN workflows rather than static fixture checks. The
minimum set must cover three product archetypes and preserve run IDs, prompts,
approvals, patches, build/test output, retries, model lifecycle, peak VRAM,
rollback state, and final human outcome. A run only counts as successful when
its generated project builds and its required tests pass in the sandbox.

### Independent security and legal review

The project owner cannot mark their own work as independent. Preserve the
reviewer's name or organization, scope, date, tool/manual methodology,
findings, accepted risks, and final decision. Legal review is mandatory but
does not create a guarantee of regulatory compliance.

### Model distribution

The public repository does not redistribute model weights. Record the exact
upstream license source and the qualified review decision for each model.
Models that are not cleared for redistribution must remain `user_supplied`.

### Generated-software acceptance

Qualified humans must inspect behavior, security, maintainability, UX, and
deployment evidence for each benchmark project. Green automated tests alone do
not constitute acceptance.

## Trust Boundary

The verifier provides integrity, schema, freshness, and policy checks. It
cannot prove that a named reviewer is qualified or that an external report is
truthful. For a trusted publisher channel, preserve signed assessor reports or
equivalent organizational evidence outside source control and archive their
hashes with the release.

ANN does not guarantee legal compliance, security, sellability, or perfect
generated software.
