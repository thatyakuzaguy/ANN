---
name: release_packaging
description: SBOM, hashes, installer evidence, package verification, and rollback.
---

# Release Packaging

Use this skill to prepare, verify, then run installer smoke only after Approval Center.

Supply a local `project_root`. Never pass raw shell commands. Review generated artifacts and errors. Operations marked as mutating require the existing ANN Approval Center; no skill permission bypasses patch, terminal, or release gates.
