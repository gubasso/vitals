"""The command line: flags, exit codes, --once as JSON, the log file, and the one exit boundary."""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from returns.result import Success

from tests.conftest import plain, write_config
from vitals import cli
from vitals.adapters.fake_source import FakeSource
from vitals.collectors.snapshot import collect_snapshot
from vitals.report import snapshot_json
from vitals.sources import fake_sources
lazy from vitals.domain.samples import Snapshot


def vitals(*args: str, fake: bool = True) -> subprocess.CompletedProcess[str]:
    """Run the vitals module in a child process, with the environment of the test."""
    env = dict(os.environ)
    if fake:
        env["VITALS_FAKE_SOURCES"] = "1"
    return subprocess.run(  # noqa: S603 - the interpreter of the test venv
        [sys.executable, "-m", "vitals", *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_help_lists_every_flag_and_view(terminal: str) -> None:
    """--help names each flag and both views, and exits 0, with or without forced color."""
    del terminal
    result = vitals("--help")
    assert result.returncode == 0
    for word in ("--view", "--interval", "--theme", "--once", "--version", "overview", "processes"):
        assert word in plain(result.stdout)


def test_an_unknown_view_exits_64() -> None:
    """--view network lists the known views on stderr and exits 64."""
    result = vitals("--view", "network")
    assert result.returncode == 64
    assert "overview, processes" in result.stderr


def test_an_unknown_option_exits_64() -> None:
    """An option the command does not know is a usage error."""
    result = vitals("--refresh", "3")
    assert result.returncode == 64
    assert "--refresh" in result.stderr


def test_a_malformed_file_exits_78_with_its_path(xdg_home: Path) -> None:
    """A config.toml that is not TOML exits 78, and stderr names its path."""
    path = write_config(xdg_home, "interval = = 3\n")
    result = vitals("--once")
    assert result.returncode == 78
    assert str(path) in result.stderr


def test_no_file_runs_on_the_defaults() -> None:
    """With no configuration folder, --once runs and exits 0."""
    result = vitals("--once")
    assert result.returncode == 0


def test_once_prints_one_snapshot_as_json() -> None:
    """--once prints one JSON object, and the GPU key holds its temperature."""
    result = vitals("--once")
    document = json.loads(result.stdout)
    assert document["gpu"]["temperature"] == 52.0
    assert set(document) == {"host", "cpu", "memory", "disks", "temperatures", "gpu", "processes"}


def test_a_failed_source_is_an_object_with_its_kind() -> None:
    """A failed source prints its kind and detail in place of its sample."""
    snapshot = collect_snapshot(fake_sources(FakeSource(failing=frozenset({"gpu"}))))
    document = json.loads(snapshot_json(snapshot))
    assert document["gpu"] == {
        "error": {"kind": "source-unavailable", "detail": "fake gpu failure"}
    }


def _exit_of_main(monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> int:
    monkeypatch.setattr(sys, "argv", ["vitals", *argv])
    with pytest.raises(SystemExit) as stop:
        cli.main()
    return int(stop.value.code or 0)


def test_no_readable_source_exits_69(monkeypatch: pytest.MonkeyPatch) -> None:
    """--once exits 69 when every source fails."""
    every = frozenset({"host", "cpu", "memory", "disks", "temperatures", "gpu", "processes"})
    monkeypatch.setenv("VITALS_FAKE_SOURCES", "1")
    monkeypatch.setattr(cli, "fake_sources", lambda: fake_sources(FakeSource(failing=every)))
    assert _exit_of_main(monkeypatch, ["--once"]) == 69


def test_an_escaped_exception_exits_70(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Main turns an exception that escapes the run into exit 70 and a message."""

    def broken(_: object) -> Snapshot:
        message = "boom"
        raise RuntimeError(message)

    monkeypatch.setenv("VITALS_FAKE_SOURCES", "1")
    monkeypatch.setattr(cli, "collect_snapshot", broken)
    assert _exit_of_main(monkeypatch, ["--once"]) == 70
    assert "internal error: boom" in capsys.readouterr().err


def test_the_flags_reach_the_dashboard(monkeypatch: pytest.MonkeyPatch) -> None:
    """The view, the interval, and the theme of the flags start the app."""
    started: dict[str, object] = {}

    def fake_run_app(**kwargs: object) -> None:
        started.update(kwargs)

    monkeypatch.setenv("VITALS_FAKE_SOURCES", "1")
    monkeypatch.setattr("vitals.ui.app.run_app", fake_run_app)
    result = cli.run(["--view", "processes", "--interval", "1", "--theme", "nord"])
    assert result == Success(None)
    assert (started["view"], started["interval"], started["theme"]) == ("processes", 1.0, "nord")


def test_the_log_goes_to_the_state_file(
    xdg_home: Path,
    capfd: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A run writes its log under XDG_STATE_HOME, and no log line reaches the terminal."""
    monkeypatch.setenv("VITALS_FAKE_SOURCES", "1")
    monkeypatch.setattr("vitals.ui.app.run_app", lambda **_: None)
    cli.run([])
    log = (xdg_home / "state" / "vitals" / "vitals.log").read_text(encoding="utf-8")
    assert "start: view=overview" in log
    captured = capfd.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_only_main_exits() -> None:
    """No function but cli.main calls sys.exit or raises SystemExit."""
    source = Path(cli.__file__).parent
    exits: list[str] = []
    for path in source.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef):
                continue
            text = ast.unparse(function)
            if "sys.exit" in text or "SystemExit" in text:
                exits.append(f"{path.name}:{function.name}")
    assert exits == ["cli.py:main"]
