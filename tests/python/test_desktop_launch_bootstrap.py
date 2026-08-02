from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_desktop_entrypoint_bootstraps_monorepo_packages() -> None:
    environment = {**os.environ, "PYTHONPATH": ""}
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import agentic_network.desktop_app.run; "
                "import agentic_engineering_network; "
                "print(agentic_engineering_network.__name__)"
            ),
        ],
        cwd=ROOT,
        capture_output=True,
        env=environment,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert completed.stdout.strip() == "agentic_engineering_network"


def test_desktop_window_api_bootstraps_monorepo_packages() -> None:
    environment = {**os.environ, "PYTHONPATH": ""}
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import agentic_network.desktop_app.main_window; "
                "import agentic_engineering_network; "
                "print(agentic_engineering_network.__name__)"
            ),
        ],
        cwd=ROOT,
        capture_output=True,
        env=environment,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert completed.stdout.strip() == "agentic_engineering_network"
