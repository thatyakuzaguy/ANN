---
name: sandbox_verification
description: Allowlisted build, lint, test, and E2E verification recipes.
---

# Sandbox Verification

Use this skill to detect recipes first, then run after explicit permissions.

Supply a local `project_root`. Never pass raw shell commands. Review generated artifacts and errors. Operations marked as mutating require the existing ANN Approval Center; no skill permission bypasses patch, terminal, or release gates.
