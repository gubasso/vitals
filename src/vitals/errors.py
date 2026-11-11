"""The failures of a run, and the sysexits code of each kind."""

from dataclasses import dataclass
from enum import IntEnum, StrEnum


class AppErrorKind(StrEnum):
    """Why a run of vitals failed."""

    USAGE = "usage"
    CONFIG = "config"
    UNAVAILABLE = "unavailable"
    INTERNAL = "internal"


class ExitCode(IntEnum):
    """The exit codes of BSD sysexits.h that vitals uses."""

    OK = 0
    USAGE = 64
    UNAVAILABLE = 69
    SOFTWARE = 70
    CONFIG = 78


@dataclass(frozen=True, slots=True, kw_only=True)
class AppError:
    """A failure of a run, with the message that stderr shows."""

    kind: AppErrorKind
    message: str


def exit_code(kind: AppErrorKind) -> ExitCode:
    """Return the sysexits code of an error kind."""
    match kind:
        case AppErrorKind.USAGE:
            return ExitCode.USAGE
        case AppErrorKind.CONFIG:
            return ExitCode.CONFIG
        case AppErrorKind.UNAVAILABLE:
            return ExitCode.UNAVAILABLE
        case AppErrorKind.INTERNAL:
            return ExitCode.SOFTWARE
