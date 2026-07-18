from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[2]
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
URI_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def _tracked_markdown_files() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "*.md"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def _target_path(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = re.split(r"\s+[\"']", target, maxsplit=1)[0]
    if not target or target.startswith("#") or URI_SCHEME.match(target):
        return None
    return unquote(target.split("#", 1)[0].split("?", 1)[0])


def find_broken_links() -> list[str]:
    failures: list[str] = []
    for document in _tracked_markdown_files():
        text = document.read_text(encoding="utf-8", errors="replace")
        in_fence = False
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for match in LINK_PATTERN.finditer(line):
                target = _target_path(match.group(1))
                if target is None:
                    continue
                if re.match(r"^[a-zA-Z]:[\\/]", target) or target.startswith(("/", "\\")):
                    failures.append(
                        f"{document.relative_to(ROOT)}:{line_number}: absolute local link {target}"
                    )
                    continue
                candidate = (document.parent / target).resolve()
                if not candidate.exists():
                    failures.append(
                        f"{document.relative_to(ROOT)}:{line_number}: missing {target}"
                    )
    return failures


def main() -> int:
    failures = find_broken_links()
    if failures:
        print("Broken local Markdown links:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("All tracked local Markdown links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
