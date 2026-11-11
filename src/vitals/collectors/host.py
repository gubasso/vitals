"""The host collector: the name of the machine and its uptime."""

from typing import Protocol

lazy from returns.result import Result

lazy from vitals.domain.errors import CollectorError
lazy from vitals.domain.samples import HostSample


class HostSource(Protocol):
    """What the host collector reads."""

    def host(self) -> Result[HostSample, CollectorError]:
        """Return the name of the machine and the time since it booted."""
        ...


def collect_host(source: HostSource) -> Result[HostSample, CollectorError]:
    """Read the name and the uptime of the machine."""
    return source.host()
