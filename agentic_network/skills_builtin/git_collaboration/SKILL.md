# Git Collaboration

Approval-gated branch, commit, push, and draft pull-request collaboration.

## Actions

- status: Read branch, worktree, and remote collaboration state.
- branch: Create an approved namespaced Git branch.
- commit: Create an approved commit from an explicit bounded file list.
- publish_pr: Push an approved branch and open a draft pull request.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
