"""The memory collector: the memory and the swap."""

from typing import Protocol

from returns.result import Result

from vitals.domain.samples import MemorySample, Usage
lazy from vitals.domain.errors import CollectorError


class MemorySource(Protocol):
    """What the memory collector reads."""

    def memory(self) -> Result[Usage, CollectorError]:
        """Return the memory used of total."""
        ...

    def swap(self) -> Result[Usage, CollectorError]:
        """Return the swap used of total."""
        ...


def collect_memory(source: MemorySource) -> Result[MemorySample, CollectorError]:
    """Read the memory and the swap."""
    return Result.do(
        MemorySample(memory=memory, swap=swap)
        for memory in source.memory()
        for swap in source.swap()
    )
