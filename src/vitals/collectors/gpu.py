"""The GPU collector: the first NVIDIA device that NVML reports."""

from typing import Protocol

lazy from returns.result import Result

lazy from vitals.domain.errors import CollectorError
lazy from vitals.domain.samples import GpuSample


class GpuSource(Protocol):
    """What the GPU collector reads."""

    def first_gpu(self) -> Result[GpuSample, CollectorError]:
        """Return the state of the first NVIDIA device."""
        ...


def collect_gpu(source: GpuSource) -> Result[GpuSample, CollectorError]:
    """Read the first NVIDIA GPU."""
    return source.first_gpu()
