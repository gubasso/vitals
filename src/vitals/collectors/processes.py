"""The processes collector: the top processes by CPU and by memory."""

from typing import Protocol
lazy from collections.abc import Sequence

lazy from returns.result import Result

from vitals.domain.samples import ProcessEntry, ProcessesSample
lazy from vitals.domain.errors import CollectorError

TOP = 15
"""How many processes each ranking holds."""


class ProcessSource(Protocol):
    """What the processes collector reads."""

    def processes(self) -> Result[Sequence[ProcessEntry], CollectorError]:
        """Every process that could be read, without the ones that exited during the read."""
        ...


def rank(entries: Sequence[ProcessEntry], top: int = TOP) -> ProcessesSample:
    """Rank the processes by CPU and by resident memory, highest first."""
    by_cpu = sorted(entries, key=lambda entry: (-entry.cpu, entry.pid))
    by_memory = sorted(entries, key=lambda entry: (-entry.resident, entry.pid))
    return ProcessesSample(top_cpu=tuple(by_cpu[:top]), top_memory=tuple(by_memory[:top]))


def collect_processes(source: ProcessSource) -> Result[ProcessesSample, CollectorError]:
    """Read and rank the processes."""
    return source.processes().map(rank)
