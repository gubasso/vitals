"""The psutil adapter: the one module that imports psutil."""

import os
import socket
import time
from typing import TYPE_CHECKING

import psutil
from returns.result import Result, safe

from vitals.collectors.disks import Mount
from vitals.collectors.temperatures import SensorReading
from vitals.domain.errors import CollectorError, error_from_exception
from vitals.domain.samples import HostSample, LoadAverage, ProcessEntry, Usage
from vitals.domain.units import Bytes, Celsius, Megahertz, Percent, Seconds

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


class PsutilSource:
    """Every source that psutil reads: CPU, memory, disks, sensors, processes, and host."""

    def __init__(self) -> None:
        """Prime the CPU counters, so the first usage read covers a real interval."""
        psutil.cpu_percent(interval=None)

    def usage(self) -> Result[Percent, CollectorError]:
        """Return the aggregate CPU usage since the previous read."""
        return safe(lambda: Percent(psutil.cpu_percent(interval=None)))().alt(error_from_exception)

    def frequency(self) -> Result[Megahertz | None, CollectorError]:
        """Return the current CPU frequency."""
        return safe(lambda: Megahertz(psutil.cpu_freq().current))().alt(error_from_exception)

    def load(self) -> Result[LoadAverage, CollectorError]:
        """Return the load average over 1, 5, and 15 minutes."""

        def read() -> LoadAverage:
            one, five, fifteen = os.getloadavg()
            return LoadAverage(one=one, five=five, fifteen=fifteen)

        return safe(read)().alt(error_from_exception)

    def sensors(self) -> Result[Sequence[SensorReading], CollectorError]:
        """Every temperature sensor of the machine."""

        def read() -> Sequence[SensorReading]:
            return tuple(
                SensorReading(chip=chip, label=entry.label, current=Celsius(entry.current))
                for chip, entries in psutil.sensors_temperatures().items()
                for entry in entries
            )

        return safe(read)().alt(error_from_exception)

    def memory(self) -> Result[Usage, CollectorError]:
        """Return the memory used of total."""

        def read() -> Usage:
            memory = psutil.virtual_memory()
            return Usage(used=Bytes(memory.total - memory.available), total=Bytes(memory.total))

        return safe(read)().alt(error_from_exception)

    def swap(self) -> Result[Usage, CollectorError]:
        """Return the swap used of total."""

        def read() -> Usage:
            swap = psutil.swap_memory()
            return Usage(used=Bytes(swap.used), total=Bytes(swap.total))

        return safe(read)().alt(error_from_exception)

    def mounts(self) -> Result[Sequence[Mount], CollectorError]:
        """Return the mounted physical filesystems."""

        def read() -> Sequence[Mount]:
            return tuple(
                Mount(device=part.device, mount_point=part.mountpoint, filesystem=part.fstype)
                for part in psutil.disk_partitions(all=False)
            )

        return safe(read)().alt(error_from_exception)

    def usage_of(self, mount_point: str) -> Result[Usage, CollectorError]:
        """Return the usage of the filesystem at a mount point."""

        def read() -> Usage:
            usage = psutil.disk_usage(mount_point)
            return Usage(used=Bytes(usage.used), total=Bytes(usage.total))

        return safe(read)().alt(error_from_exception)

    def processes(self) -> Result[Sequence[ProcessEntry], CollectorError]:
        """Every process that could be read, without the ones that exited during the read."""
        return safe(lambda: read_processes(psutil.process_iter()))().alt(
            error_from_exception,
        )

    def host(self) -> Result[HostSample, CollectorError]:
        """Return the name of the machine and the time since it booted."""

        def read() -> HostSample:
            return HostSample(
                name=socket.gethostname(),
                uptime=Seconds(time.time() - psutil.boot_time()),
            )

        return safe(read)().alt(error_from_exception)


def read_processes(processes: Iterable[psutil.Process]) -> tuple[ProcessEntry, ...]:
    """Read each process, and skip one that exits or denies access during the read."""
    entries: list[ProcessEntry] = []
    for process in processes:
        try:
            with process.oneshot():
                memory = process.memory_info()
                entries.append(
                    ProcessEntry(
                        pid=process.pid,
                        name=process.name(),
                        user=process.username(),
                        cpu=Percent(process.cpu_percent(interval=None)),
                        resident=Bytes(memory.rss),
                    ),
                )
        except psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess:
            continue
    return tuple(entries)
