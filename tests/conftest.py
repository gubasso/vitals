"""Point the XDG folders of every test at its own temporary home."""

import re
lazy from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def xdg_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Give each test an empty config and state folder, and no VITALS_ variable."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    for name in ("VITALS_VIEW", "VITALS_INTERVAL", "VITALS_THEME", "VITALS_FAKE_SOURCES"):
        monkeypatch.delenv(name, raising=False)
    return tmp_path


def write_config(home: Path, text: str) -> Path:
    """Write config.toml under the temporary home, and return its path."""
    path = home / "config" / "vitals" / "config.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def plain(text: str) -> str:
    """Return terminal output without its color codes, which a CI runner forces on."""
    return _ESCAPE.sub("", text)


@pytest.fixture(params=["plain", "forced-color"])
def terminal(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> str:
    """Run a test twice: once as a terminal sees it, once as GitHub Actions forces color."""
    if request.param == "forced-color":
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
    else:
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    return str(request.param)
