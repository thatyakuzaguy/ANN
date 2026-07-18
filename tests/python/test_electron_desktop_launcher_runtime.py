from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_web_exposes_desktop_dev_port() -> None:
    package_path = REPO_ROOT / "apps" / "web" / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))

    assert package["scripts"]["dev:desktop"] == "next dev -H 127.0.0.1 -p 3001"
    assert package["scripts"]["start:desktop"] == "next start -H 127.0.0.1 -p 3001"


def test_electron_launcher_has_direct_web_fallback() -> None:
    launcher = (REPO_ROOT / "apps" / "desktop" / "src" / "main.js").read_text(encoding="utf-8")

    assert "DESKTOP_WEB_URL" in launcher
    assert "http://127.0.0.1:3001" in launcher
    assert "startDesktopWeb" in launcher
    assert "desktopWebAlreadyReady = await requestOk(DESKTOP_WEB_URL" in launcher
    assert "reusing existing desktop web" in launcher
    assert '".next", "standalone", "apps", "web", "server.js"' in launcher
    assert "HOSTNAME: \"127.0.0.1\"" in launcher
    assert "PORT: \"3001\"" in launcher
    assert "const command = process.execPath" in launcher
    assert 'ELECTRON_RUN_AS_NODE: "1"' in launcher
    assert "AEN_ROOT: APP_ROOT" in launcher
    assert "AEN_HOST_ROOT: APP_ROOT" in launcher
    assert 'path.join(APP_ROOT, "runtime", "python", "python.exe")' in launcher
    assert "resolveAppRoot" in launcher
    assert "startServices" in launcher
    assert "desktop-launcher.log" in launcher
    assert "Confirm Docker Desktop is running" not in launcher


def test_api_allows_desktop_fallback_origin() -> None:
    api_main = (REPO_ROOT / "apps" / "api" / "app" / "main.py").read_text(encoding="utf-8")

    assert "http://localhost:3001" in api_main
    assert "http://127.0.0.1:3001" in api_main
