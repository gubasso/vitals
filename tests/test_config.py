"""The configuration resolves flags over the environment over the file, and names a bad layer."""

lazy from pathlib import Path

import pydantic
import pytest
from returns.result import Failure, Success

from tests.conftest import write_config
from vitals.config import Settings, load_settings
from vitals.errors import AppErrorKind


def test_defaults_without_a_file() -> None:
    """No file and no variable give the defaults."""
    assert load_settings({}) == Success(Settings())
    assert Settings().interval == 2.0
    assert Settings().theme == "textual-dark"


def test_a_flag_wins_over_the_environment_and_the_file(
    xdg_home: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The interval comes from the flag, then the variable, then the file."""
    write_config(xdg_home, "interval = 5\ntheme = 'nord'\n")
    monkeypatch.setenv("VITALS_INTERVAL", "3")
    match load_settings({"interval": 1.0}):
        case Success(settings):
            assert settings.interval == 1.0
            assert settings.theme == "nord"
        case _:
            raise AssertionError
    match load_settings({}):
        case Success(settings):
            assert settings.interval == 3.0
        case _:
            raise AssertionError
    monkeypatch.delenv("VITALS_INTERVAL")
    match load_settings({}):
        case Success(settings):
            assert settings.interval == 5.0
        case _:
            raise AssertionError


def test_an_unknown_key_in_the_file_names_the_key_and_the_file(xdg_home: Path) -> None:
    """The model forbids a key it does not declare."""
    path = write_config(xdg_home, "refresh = 3\n")
    match load_settings({}):
        case Failure(error):
            assert error.kind is AppErrorKind.CONFIG
            assert str(path) in error.message
            assert "refresh" in error.message
        case _:
            raise AssertionError


def test_malformed_toml_names_the_file(xdg_home: Path) -> None:
    """A file that is not TOML is a configuration error with its path."""
    path = write_config(xdg_home, "interval = = 3\n")
    match load_settings({}):
        case Failure(error):
            assert error.kind is AppErrorKind.CONFIG
            assert str(path) in error.message
        case _:
            raise AssertionError


def test_a_bad_variable_names_the_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """VITALS_INTERVAL=-1 is a configuration error that names the variable."""
    monkeypatch.setenv("VITALS_INTERVAL", "-1")
    match load_settings({}):
        case Failure(error):
            assert error.kind is AppErrorKind.CONFIG
            assert "VITALS_INTERVAL" in error.message
        case _:
            raise AssertionError


def test_a_bad_flag_is_a_usage_error() -> None:
    """An unknown theme from the command line names the flag."""
    match load_settings({"theme": "neon"}):
        case Failure(error):
            assert error.kind is AppErrorKind.USAGE
            assert error.message.startswith("--theme:")
        case _:
            raise AssertionError


def test_the_settings_are_frozen() -> None:
    """A setting cannot change after the load."""
    with pytest.raises(pydantic.ValidationError):
        Settings().interval = 9.0  # type: ignore[misc]
