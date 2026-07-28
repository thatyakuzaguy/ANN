---
name: patch_workspace
description: Diff validation and approval-gated patch application.
---

# Patch Workspace

Use this skill to inspect before apply; apply requires Approval Center and patch token.

Supply a local `project_root`. Never pass raw shell commands. Review generated artifacts and errors. Operations marked as mutating require the existing ANN Approval Center; no skill permission bypasses patch, terminal, or release gates.
