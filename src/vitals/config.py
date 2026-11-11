"""The configuration: flags over the VITALS_ environment over config.toml over the defaults."""

import os
import tomllib
from typing import ClassVar, override
lazy from pathlib import Path

from platformdirs import user_config_path
from pydantic import Field, PositiveFloat, ValidationError, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)
from returns.result import Failure, Result, Success
from textual.theme import BUILTIN_THEMES

from vitals.errors import AppError, AppErrorKind

ENV_PREFIX = "VITALS_"


def config_path() -> Path:
    """Return `${XDG_CONFIG_HOME:-$HOME/.config}/vitals/config.toml`."""
    return user_config_path("vitals") / "config.toml"


def _view_names() -> tuple[str, ...]:
    # The registry lives in the UI. A function keeps the import out of the module load.
    from vitals.ui.app import view_names  # noqa: PLC0415

    return view_names()


class Settings(BaseSettings):
    """Every setting of a run. A flag wins over the environment, which wins over the file."""

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        frozen=True,
        extra="forbid",
    )

    view: str = Field(default="overview", description="The view that opens first.")
    interval: PositiveFloat = Field(default=2.0, description="The sampling interval, in seconds.")
    theme: str = Field(default="textual-dark", description="The Textual theme.")
    fake_sources: bool = Field(
        default=False,
        description="Read the fixed fake sources instead of the machine, for tests.",
    )

    @field_validator("view")
    @classmethod
    def _known_view(cls, view: str) -> str:
        names = _view_names()
        if view not in names:
            msg = f"unknown view {view!r}; the views are {', '.join(names)}"
            raise ValueError(msg)
        return view

    @field_validator("theme")
    @classmethod
    def _known_theme(cls, theme: str) -> str:
        if theme not in BUILTIN_THEMES:
            msg = f"unknown theme {theme!r}; the themes are {', '.join(sorted(BUILTIN_THEMES))}"
            raise ValueError(msg)
        return theme

    @classmethod
    @override
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Read the flags, then the environment, then the file of config_path()."""
        del dotenv_settings, file_secret_settings
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls, toml_file=config_path()),
        )


type Flags = dict[str, str | float]
"""The settings that the command line set, by field name. A flag that was not given is absent."""


def _flag_name(field: str) -> str:
    return "--" + field.replace("_", "-")


def _layer(field: str, flags: Flags) -> tuple[str, AppErrorKind]:
    """Name the layer that supplied a field, and the error kind of a bad value there."""
    if field in flags:
        return _flag_name(field), AppErrorKind.USAGE
    variable = ENV_PREFIX + field.upper()
    if variable in os.environ:
        return variable, AppErrorKind.CONFIG
    return str(config_path()), AppErrorKind.CONFIG


def _error(exc: ValidationError, flags: Flags) -> AppError:
    lines: list[str] = []
    kinds: set[AppErrorKind] = set()
    for problem in exc.errors():
        field = ".".join(str(part) for part in problem["loc"]) or "configuration"
        layer, kind = _layer(field, flags)
        kinds.add(kind)
        message = problem["msg"].removeprefix("Value error, ")
        # A flag or a variable names its field already; the file path does not.
        where = (
            f"{layer}: {field}"
            if kind is AppErrorKind.CONFIG and layer == str(config_path())
            else layer
        )
        lines.append(f"{where}: {message}")
    kind = AppErrorKind.USAGE if kinds == {AppErrorKind.USAGE} else AppErrorKind.CONFIG
    return AppError(kind=kind, message="\n".join(lines))


def load_settings(flags: Flags) -> Result[Settings, AppError]:
    """Resolve the settings from the flags, the environment, and the file."""
    try:
        return Success(Settings.model_validate(flags))
    except tomllib.TOMLDecodeError as exc:
        return Failure(
            AppError(kind=AppErrorKind.CONFIG, message=f"{config_path()}: invalid TOML: {exc}"),
        )
    except ValidationError as exc:
        return Failure(_error(exc, flags))
