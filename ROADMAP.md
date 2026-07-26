# Roadmap

ANN 1.0 is a stable local-first engineering workbench, not a claim of perfect
or universal autonomous software generation. The following work is deliberately
outside the 1.0 acceptance boundary.

## 1.x Reliability

- Add stage-level checkpoints before proposal generation so even pre-proposal
  interruptions can be resumed without replay ambiguity.
- Extend live event streaming beyond Agent Office and retain bounded event
  history for long-running pipelines.
- Add migration tooling for persisted run and conversation schema changes.
- Add fault-injection coverage for power loss, disk exhaustion, Docker daemon
  loss, corrupt model files, and interrupted release packaging.

## 1.x Capability

- Expand artifact families and deterministic analyzers for additional game
  engines, mobile applications, native applications, data systems, and
  infrastructure repositories.
- Add deeper TypeScript/JavaScript AST slicing and language-server evidence to
  the Failure Context Compiler.
- Publish reproducible, model-provenance-aware capability benchmarks across
  fresh prompts and existing repositories.

## Distribution

- Produce a trusted-publisher Windows channel after obtaining a real
  Authenticode certificate and timestamping service.
- Transfer installer evidence from an independent clean Windows 11 machine.
- Add a signed update manifest and rollback channel. Until then, updates are
  manual and hash-verified.

## Ongoing Human Work

- Security assessment, accessibility testing, legal/compliance review, model
  license review, product discovery, and production operations remain human
  responsibilities. ANN can produce evidence and checklists but cannot certify
  those outcomes.
