"""Validate external ANN release assurance evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentic_network.runtime_engine.release_assurance import (  # noqa: E402
    build_release_assurance_report,
    write_release_assurance_artifacts,
    write_release_assurance_templates,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify ANN production assurance evidence.")
    parser.add_argument("--evidence-root", default="outputs/release_assurance/external")
    parser.add_argument("--policy", default="config/release-assurance-policy.json")
    parser.add_argument("--output-dir", default="outputs/release_assurance/verification")
    parser.add_argument("--init-evidence", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.init_evidence:
        paths = write_release_assurance_templates(args.evidence_root)
        print("\n".join(paths))
        return 0
    report = build_release_assurance_report(args.evidence_root, policy_path=args.policy)
    write_release_assurance_artifacts(report, args.output_dir)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"ANN Release Assurance: {report['status']}")
        print(f"Evidence: {report['evidence_files_found']}/{report['evidence_files_required']}")
        print(f"Next step: {report['next_step']}")
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
