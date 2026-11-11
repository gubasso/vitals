"""The smoke test: the package imports, and its command answers --help and --version."""

import subprocess
import sys
from importlib.metadata import version

from tests.conftest import plain
from vitals import cli


def run(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a command of the project venv and capture its output."""
    return subprocess.run(args, capture_output=True, text=True, check=False)  # noqa: S603


def test_the_package_imports() -> None:
    """The package exposes its entry point."""
    assert callable(cli.main)


def test_help_exits_zero(terminal: str) -> None:
    """`vitals --help` prints the usage and exits 0, with or without forced color."""
    del terminal
    result = run("vitals", "--help")
    assert result.returncode == 0
    assert "Usage: vitals" in plain(result.stdout)


def test_version_prints_the_package_version() -> None:
    """`vitals --version` prints the installed version and exits 0."""
    result = run("vitals", "--version")
    assert result.returncode == 0
    assert result.stdout.strip() == f"vitals {version('vitals')}"


def test_module_answers_help(terminal: str) -> None:
    """`python -m vitals --help` runs the same entry point, with or without forced color."""
    del terminal
    result = run(sys.executable, "-m", "vitals", "--help")
    assert result.returncode == 0
    assert "Usage: vitals" in plain(result.stdout)
