"""Point the XDG folders of every test at its own temporary home."""

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
