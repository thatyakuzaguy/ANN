# Legal Review Preparation

Status: `PENDING_QUALIFIED_HUMAN_REVIEW`

This document is a review checklist, not legal advice and not legal approval.

## Review scope

- Distribution: source/community release, unsigned Windows artifacts, third-party
  notices, model files excluded from the repository.
- Privacy: local-first processing, telemetry expectations, generated-project data,
  logs, screenshots, and operator responsibility.
- Model licensing: four user-supplied model families, quantized files, optional
  private adapters, attribution and redistribution obligations.
- Terms: warranty disclaimer, user approval boundaries, generated-code ownership,
  acceptable use, export and jurisdiction considerations.

## Current release position

ANN distributes code and configuration but no model weights. Operators must supply
authorized model files and accept the applicable licenses. The trusted Windows
publisher channel remains fail-closed without a real signing identity.

A qualified human must review the exact release snapshot and record a named
decision. Compliance is never guaranteed by this packet.
