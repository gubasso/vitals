"""Build one Snapshot from every source."""

from dataclasses import dataclass

from vitals.collectors.cpu import CpuSource, collect_cpu
from vitals.collectors.disks import DiskSource, collect_disks
from vitals.collectors.gpu import GpuSource, collect_gpu
from vitals.collectors.host import HostSource, collect_host
from vitals.collectors.memory import MemorySource, collect_memory
from vitals.collectors.processes import ProcessSource, collect_processes
from vitals.collectors.temperatures import TemperatureSource, collect_temperatures
from vitals.domain.samples import Snapshot


@dataclass(frozen=True, slots=True, kw_only=True)
class Sources:
    """The source of each collector."""

    host: HostSource
    cpu: CpuSource
    memory: MemorySource
    disks: DiskSource
    temperatures: TemperatureSource
    gpu: GpuSource
    processes: ProcessSource


def collect_snapshot(sources: Sources) -> Snapshot:
    """Run every collector once. A failed source fails alone."""
    return Snapshot(
        host=collect_host(sources.host),
        cpu=collect_cpu(sources.cpu),
        memory=collect_memory(sources.memory),
        disks=collect_disks(sources.disks),
        temperatures=collect_temperatures(sources.temperatures),
        gpu=collect_gpu(sources.gpu),
        processes=collect_processes(sources.processes),
    )
