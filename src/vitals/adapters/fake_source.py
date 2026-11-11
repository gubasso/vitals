"""A fake of every source, with fixed values, for the tests and the packaged smoke check."""

from dataclasses import dataclass, field
lazy from collections.abc import Sequence

from returns.result import Failure, Result, Success

from vitals.collectors.disks import Mount
from vitals.collectors.temperatures import SensorReading
from vitals.domain.errors import CollectorError, CollectorErrorKind
from vitals.domain.samples import GpuSample, HostSample, LoadAverage, ProcessEntry, Usage
from vitals.domain.units import Bytes, Celsius, Megahertz, Percent, Seconds, Watts

GIB = 1024**3


def _gib(amount: float) -> Bytes:
    return Bytes(int(amount * GIB))


FAKE_MOUNTS = (
    Mount(device="/dev/mapper/system-root", mount_point="/", filesystem="btrfs"),
    Mount(device="/dev/mapper/system-root", mount_point="/home", filesystem="btrfs"),
    Mount(device="/dev/mapper/system-root", mount_point="/var", filesystem="btrfs"),
    Mount(device="/dev/mapper/system-root", mount_point="/opt", filesystem="btrfs"),
    Mount(device="/dev/nvme0n1p1", mount_point="/boot/efi", filesystem="vfat"),
    Mount(device="/dev/sda1", mount_point="/run/media/gbasso/data", filesystem="ext4"),
    Mount(device="tmpfs", mount_point="/run", filesystem="tmpfs"),
)
"""The mount table of tumblesuse: btrfs subvolumes on one device, the EFI partition, and a drive."""

FAKE_USAGE = {
    "/": Usage(used=_gib(612.0), total=_gib(930.0)),
    "/boot/efi": Usage(used=_gib(0.02), total=_gib(0.5)),
    "/run/media/gbasso/data": Usage(used=_gib(1210.0), total=_gib(1830.0)),
}

FAKE_SENSORS = (
    SensorReading(chip="coretemp", label="Package id 0", current=Celsius(68.0)),
    SensorReading(chip="coretemp", label="Core 0", current=Celsius(66.0)),
    SensorReading(chip="nvme", label="Composite", current=Celsius(41.9)),
)

FAKE_PROCESSES = (
    ProcessEntry(pid=4211, name="firefox", user="gbasso", cpu=Percent(23.5), resident=_gib(2.4)),
    ProcessEntry(pid=1873, name="kitty", user="gbasso", cpu=Percent(4.1), resident=_gib(0.3)),
    ProcessEntry(pid=902, name="Xorg", user="root", cpu=Percent(2.7), resident=_gib(0.4)),
    ProcessEntry(pid=5530, name="python3.15", user="gbasso", cpu=Percent(1.2), resident=_gib(0.2)),
    ProcessEntry(pid=1, name="systemd", user="root", cpu=Percent(0.0), resident=_gib(0.01)),
)

FAKE_GPU = GpuSample(
    name="NVIDIA RTX 2000 Ada Generation Laptop GPU",
    utilization=Percent(12.0),
    vram=Usage(used=_gib(1.1), total=_gib(8.0)),
    temperature=Celsius(52.0),
    power=Watts(8.4),
)


@dataclass(frozen=True, slots=True, kw_only=True)
class FakeSource:
    """Every source, with fixed values. A name in `failing` fails with `failure_kind`."""

    failing: frozenset[str] = field(default_factory=frozenset)
    failure_kind: CollectorErrorKind = CollectorErrorKind.SOURCE_UNAVAILABLE

    def _value[T](self, name: str, value: T) -> Result[T, CollectorError]:
        if name in self.failing:
            return Failure(CollectorError(kind=self.failure_kind, detail=f"fake {name} failure"))
        return Success(value)

    def usage(self) -> Result[Percent, CollectorError]:
        """Return a fixed aggregate CPU usage."""
        return self._value("cpu", Percent(37.0))

    def frequency(self) -> Result[Megahertz | None, CollectorError]:
        """Return a fixed CPU frequency."""
        return self._value("cpu", Megahertz(3418.0))

    def load(self) -> Result[LoadAverage, CollectorError]:
        """Return a fixed load average."""
        return self._value("cpu", LoadAverage(one=2.1, five=1.8, fifteen=1.5))

    def sensors(self) -> Result[Sequence[SensorReading], CollectorError]:
        """Return fixed sensors with a CPU package and an NVMe drive."""
        return self._value("temperatures", FAKE_SENSORS)

    def memory(self) -> Result[Usage, CollectorError]:
        """Return a fixed memory usage."""
        return self._value("memory", Usage(used=_gib(12.4), total=_gib(31.0)))

    def swap(self) -> Result[Usage, CollectorError]:
        """Return a fixed swap usage."""
        return self._value("memory", Usage(used=_gib(0.5), total=_gib(2.0)))

    def mounts(self) -> Result[Sequence[Mount], CollectorError]:
        """Return the tumblesuse mount table."""
        return self._value("disks", FAKE_MOUNTS)

    def usage_of(self, mount_point: str) -> Result[Usage, CollectorError]:
        """Return the fixed usage of a mount point of the table."""
        usage = FAKE_USAGE.get(mount_point)
        if usage is None:
            return Failure(
                CollectorError(kind=CollectorErrorKind.NO_DEVICE, detail=f"no mount {mount_point}"),
            )
        return self._value("disks", usage)

    def first_gpu(self) -> Result[GpuSample, CollectorError]:
        """Return a fixed NVIDIA GPU."""
        return self._value("gpu", FAKE_GPU)

    def processes(self) -> Result[Sequence[ProcessEntry], CollectorError]:
        """Return a fixed process list."""
        return self._value("processes", FAKE_PROCESSES)

    def host(self) -> Result[HostSample, CollectorError]:
        """Return a fixed host name and uptime."""
        return self._value("host", HostSample(name="tumblesuse", uptime=Seconds(93_784.0)))
