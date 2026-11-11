"""The frozen samples that the collectors return and the dashboard draws."""

from dataclasses import dataclass

lazy from returns.result import Result

from vitals.domain.units import Bytes, Celsius, Megahertz, Percent, Seconds, Watts, percent_of
lazy from vitals.domain.errors import CollectorError


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadAverage:
    """The load average over 1, 5, and 15 minutes."""

    one: float
    five: float
    fifteen: float


@dataclass(frozen=True, slots=True, kw_only=True)
class CpuSample:
    """The aggregate state of the CPU, with no value per core."""

    usage: Percent
    package_temperature: Celsius | None
    frequency: Megahertz | None
    load: LoadAverage


@dataclass(frozen=True, slots=True, kw_only=True)
class Usage:
    """An amount used of a total."""

    used: Bytes
    total: Bytes

    @property
    def percent(self) -> Percent:
        """The share used."""
        return percent_of(self.used, self.total)


@dataclass(frozen=True, slots=True, kw_only=True)
class MemorySample:
    """The memory and the swap of the machine."""

    memory: Usage
    swap: Usage


@dataclass(frozen=True, slots=True, kw_only=True)
class DiskSample:
    """One block device with a mounted filesystem, under its shortest mount point."""

    device: str
    mount_point: str
    usage: Usage


@dataclass(frozen=True, slots=True, kw_only=True)
class DisksSample:
    """Every block device with a mounted physical filesystem."""

    disks: tuple[DiskSample, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class TemperatureSample:
    """The temperatures that the chart follows, apart from the GPU."""

    cpu_package: Celsius | None
    nvme: Celsius | None


@dataclass(frozen=True, slots=True, kw_only=True)
class GpuSample:
    """The state of the first NVIDIA GPU."""

    name: str
    utilization: Percent
    vram: Usage
    temperature: Celsius
    power: Watts


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessEntry:
    """One process of a ranking."""

    pid: int
    name: str
    user: str
    cpu: Percent
    resident: Bytes


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessesSample:
    """The top processes by CPU and by resident memory."""

    top_cpu: tuple[ProcessEntry, ...]
    top_memory: tuple[ProcessEntry, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class HostSample:
    """The name of the machine and the time since it booted."""

    name: str
    uptime: Seconds


@dataclass(frozen=True, slots=True, kw_only=True)
class Snapshot:
    """One reading of every source, each as its own Result."""

    host: Result[HostSample, CollectorError]
    cpu: Result[CpuSample, CollectorError]
    memory: Result[MemorySample, CollectorError]
    disks: Result[DisksSample, CollectorError]
    temperatures: Result[TemperatureSample, CollectorError]
    gpu: Result[GpuSample, CollectorError]
    processes: Result[ProcessesSample, CollectorError]
