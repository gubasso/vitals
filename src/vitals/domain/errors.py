"""The closed set of failures that a collector reports."""

from dataclasses import dataclass
from enum import StrEnum


class CollectorErrorKind(StrEnum):
    """Why a source gave no sample."""

    SOURCE_UNAVAILABLE = "source-unavailable"
    PERMISSION_DENIED = "permission-denied"
    NO_DEVICE = "no-device"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True, kw_only=True)
class CollectorError:
    """A failure of one source: its kind and a detail for the reader."""

    kind: CollectorErrorKind
    detail: str


def error_from_exception(exc: Exception) -> CollectorError:
    """Map an exception of a system library to the error kind it means."""
    if isinstance(exc, PermissionError):
        kind = CollectorErrorKind.PERMISSION_DENIED
    elif isinstance(exc, FileNotFoundError):
        kind = CollectorErrorKind.NO_DEVICE
    elif isinstance(exc, NotImplementedError):
        kind = CollectorErrorKind.UNSUPPORTED
    else:
        kind = CollectorErrorKind.SOURCE_UNAVAILABLE
    return CollectorError(kind=kind, detail=str(exc) or type(exc).__name__)
