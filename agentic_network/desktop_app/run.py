"""Entrypoint for the native ANN desktop app."""

from __future__ import annotations

import sys

from agentic_network.desktop_app.bootstrap import (
    bootstrap_local_package_paths as _bootstrap_local_package_paths,
)


_bootstrap_local_package_paths()


def main() -> int:
    """Run the ANN desktop app."""

    from agentic_network.desktop_app.main_window import (
        QApplication,
        PYSIDE6_AVAILABLE,
        PySide6UnavailableError,
        create_main_window,
        dispose_main_window,
    )

    if not PYSIDE6_AVAILABLE or QApplication is None:
        raise PySide6UnavailableError(
            "PySide6 is required for ANN Desktop. Install it with: python -m pip install PySide6"
        )
    app = QApplication(sys.argv)
    window = create_main_window()
    window.show()
    exit_code = int(app.exec())
    dispose_main_window(window, app)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
