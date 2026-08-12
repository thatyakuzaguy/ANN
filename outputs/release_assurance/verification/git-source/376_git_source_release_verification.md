# ANN Git/Source Release Verification

- Status: `GIT_SOURCE_RELEASE_READY`
- Release Channel: `GIT_SOURCE`
- Trusted Windows Installer: `NOT_CLAIMED`
- Unsigned Installer: `USER_APPROVAL_REQUIRED`
- Final Signed Installer Channel: `FINAL_RELEASE_BLOCKED_UNTIL_AUTHENTICODE`
- Runtime Materialization: `READY`
- Wheelhouse Integrity: `HASH_VERIFIED`
- Embedded Package Audit: `PACKAGE_AUDIT_READY`
- Installer RC: `RC_READY`
- Autonomous Complex Capability: `AUTONOMOUS_COMPLEX_CAPABILITY_PASSED`
- Release Candidate Handoff: `HANDOFF_VERIFIED`
- Release Command Contract: `PASS`
- Next Step: Publish the Git/source release with unsigned-installer user-approval notes.

## Checks

- `source_tree_present`: PASS (D:\AgenticEngineeringNetwork\releases\github-public\ANN)
- `source_path:README.md`: PASS (D:\AgenticEngineeringNetwork\releases\github-public\ANN\README.md)
- `source_path:pyproject.toml`: PASS (D:\AgenticEngineeringNetwork\releases\github-public\ANN\pyproject.toml)
- `source_path:agentic_network`: PASS (D:\AgenticEngineeringNetwork\releases\github-public\ANN\agentic_network)
- `source_path:scripts/runtime`: PASS (D:\AgenticEngineeringNetwork\releases\github-public\ANN\scripts\runtime)
- `source_path:tests/python`: PASS (D:\AgenticEngineeringNetwork\releases\github-public\ANN\tests\python)
- `source_path:installer`: PASS (D:\AgenticEngineeringNetwork\releases\github-public\ANN\installer)
- `runtime_materialization`: PASS (READY)
- `wheelhouse_integrity`: PASS (HASH_VERIFIED)
- `embedded_package_audit`: PASS (PACKAGE_AUDIT_READY)
- `installer_rc`: PASS (RC_READY:local_runtime_evidence)
- `autonomous_complex_capability`: PASS (AUTONOMOUS_COMPLEX_CAPABILITY_PASSED:local_runtime_evidence)
- `release_candidate_handoff`: PASS (HANDOFF_VERIFIED)
- `release_command_contract`: PASS (contract_ready)
- `unsigned_installer_allowed`: PASS (git_source_channel_requires_user_approval)
- `authenticode_not_required`: PASS (trusted_installer_channel_separate)
