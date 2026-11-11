"""The command line of vitals: the flags, the run, and main, the one exit boundary."""

import sys
import time
from dataclasses import dataclass
from typing import Annotated

import typer
from returns.result import Failure, Result, Success

from vitals.collectors.snapshot import Sources, collect_snapshot
from vitals.config import Flags, Settings, load_settings
from vitals.domain.outcome import outcome
from vitals.domain.units import Seconds
from vitals.errors import AppError, AppErrorKind, ExitCode, exit_code
from vitals.logs import LOGGER, configure_logging
from vitals.report import every_source_failed, snapshot_json
from vitals.sources import fake_sources, machine_sources

# psutil measures CPU usage between two reads, so --once waits this long after the first one.
_ONCE_WARMUP = Seconds(0.5)


@dataclass(frozen=True, slots=True, kw_only=True)
class Request:
    """What the command line asked for."""

    flags: Flags
    once: bool


def _views_help() -> str:
    from vitals.ui.app import view_names  # noqa: PLC0415 - --version loads no UI

    return f"The view to open: {', '.join(view_names())}."


def _version(value: bool) -> None:  # noqa: FBT001 - Typer passes the flag positionally
    if value:
        from importlib.metadata import version  # noqa: PLC0415

        typer.echo(f"vitals {version('vitals')}")
        raise typer.Exit


command = typer.Typer(
    add_completion=False, help="A terminal dashboard of the machine's vital signs."
)


@command.command()
def vitals(
    view: Annotated[str | None, typer.Option(help=_views_help(), show_default=False)] = None,
    interval: Annotated[
        float | None,
        typer.Option(help="The sampling interval, in seconds.", show_default=False),
    ] = None,
    theme: Annotated[
        str | None, typer.Option(help="The Textual theme.", show_default=False)
    ] = None,
    once: Annotated[  # noqa: FBT002 - a flag of the command line
        bool,
        typer.Option("--once", help="Print one snapshot as JSON on stdout, and exit."),
    ] = False,
    version: Annotated[  # noqa: FBT002 - a flag of the command line
        bool,
        typer.Option("--version", callback=_version, is_eager=True, help="Print the version."),
    ] = False,
) -> Request:
    """Open the dashboard of the machine's vital signs."""
    del version
    given = {"view": view, "interval": interval, "theme": theme}
    return Request(
        flags={name: value for name, value in given.items() if value is not None}, once=once
    )


def parse(argv: list[str]) -> Result[Request | None, AppError]:
    """Parse the command line. None means that --help or --version already answered."""
    try:
        parsed: object = command(args=argv, prog_name="vitals", standalone_mode=False)
    except typer.TyperException as exc:
        return Failure(AppError(kind=AppErrorKind.USAGE, message=str(exc)))
    if isinstance(parsed, Request):
        return Success(parsed)
    return Success(None)


def _sources(settings: Settings) -> Sources:
    return fake_sources() if settings.fake_sources else machine_sources()


def _once(settings: Settings) -> Result[None, AppError]:
    sources = _sources(settings)
    time.sleep(0 if settings.fake_sources else _ONCE_WARMUP)
    snapshot = collect_snapshot(sources)
    sys.stdout.write(snapshot_json(snapshot) + "\n")
    if every_source_failed(snapshot):
        return Failure(
            AppError(kind=AppErrorKind.UNAVAILABLE, message="no source of the machine can be read")
        )
    return Success(None)


def _dashboard(settings: Settings) -> Result[None, AppError]:
    from vitals.ui.app import run_app  # noqa: PLC0415 - --once loads no UI

    run_app(
        sources=_sources(settings),
        view=settings.view,
        interval=Seconds(settings.interval),
        theme=settings.theme,
    )
    return Success(None)


def run(argv: list[str]) -> Result[None, AppError]:
    """Run vitals for a command line, and return how it ended."""
    return parse(argv).bind(
        lambda request: (
            Success(None)
            if request is None
            else load_settings(request.flags).bind(
                lambda settings: _start(settings, once=request.once),
            )
        ),
    )


def _start(settings: Settings, *, once: bool) -> Result[None, AppError]:
    path = configure_logging()
    LOGGER.info(
        "start: view=%s interval=%s theme=%s once=%s",
        settings.view,
        settings.interval,
        settings.theme,
        once,
    )
    del path
    return _once(settings) if once else _dashboard(settings)


def main() -> None:
    """Run vitals, print a failure to stderr, and exit with its sysexits code."""
    try:
        result = run(sys.argv[1:])
    except Exception as exc:  # noqa: BLE001 - the one boundary turns any escape into exit 70
        LOGGER.exception("internal error")
        result = Failure(AppError(kind=AppErrorKind.INTERNAL, message=f"internal error: {exc}"))
    match outcome(result):
        case Success(_):
            sys.exit(ExitCode.OK)
        case Failure(error):
            sys.stderr.write(f"vitals: {error.message}\n")
            sys.exit(exit_code(error.kind))
