"""The CPU collector: aggregate usage, package temperature, frequency, and load."""

from typing import TYPE_CHECKING, Protocol
lazy from collections.abc import Sequence

from returns.result import Result

from vitals.collectors.temperatures import SensorReading, package_temperature
from vitals.domain.samples import CpuSample, LoadAverage
lazy from vitals.domain.errors import CollectorError

if TYPE_CHECKING:
    from vitals.domain.units import Megahertz, Percent


class CpuSource(Protocol):
    """What the CPU collector reads."""

    def usage(self) -> Result[Percent, CollectorError]:
        """Return the aggregate usage since the previous read."""
        ...

    def frequency(self) -> Result[Megahertz | None, CollectorError]:
        """Return the current frequency, where the machine reports one."""
        ...

    def load(self) -> Result[LoadAverage, CollectorError]:
        """Return the load average."""
        ...

    def sensors(self) -> Result[Sequence[SensorReading], CollectorError]:
        """Every temperature sensor of the machine."""
        ...


def collect_cpu(source: CpuSource) -> Result[CpuSample, CollectorError]:
    """Read the aggregate CPU state. A missing temperature leaves that value empty."""
    temperature = source.sensors().map(package_temperature).value_or(None)
    return Result.do(
        CpuSample(usage=usage, package_temperature=temperature, frequency=frequency, load=load)
        for usage in source.usage()
        for frequency in source.frequency()
        for load in source.load()
    )
