"""Format the values of a sample as the text a panel shows."""

from typing import TYPE_CHECKING

lazy from vitals.domain.errors import CollectorError

if TYPE_CHECKING:
    from vitals.domain.units import Bytes, Seconds

_GIB = 1024**3
_MIB = 1024**2
_MINUTE = 60
_HOUR = 60 * _MINUTE
_DAY = 24 * _HOUR


def gib(amount: Bytes) -> str:
    """Return an amount in GiB with one decimal."""
    return f"{amount / _GIB:.1f}"


def size(amount: Bytes) -> str:
    """Return an amount in the largest unit that keeps it above one."""
    if amount >= _GIB:
        return f"{amount / _GIB:.1f} GiB"
    return f"{amount / _MIB:.0f} MiB"


def uptime(duration: Seconds) -> str:
    """Return a duration as days, hours, and minutes."""
    total = int(duration)
    days, rest = divmod(total, _DAY)
    hours, rest = divmod(rest, _HOUR)
    minutes = rest // _MINUTE
    if days:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"


def failure(error: CollectorError) -> str:
    """Return a failure of a source as its kind and its detail."""
    return f"{error.kind}: {error.detail}"
