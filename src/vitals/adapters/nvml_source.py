"""The NVML adapter: the one module that imports pynvml, behind a typed facade.

pynvml, from the distribution nvidia-ml-py, ships no type information. It loads
`libnvidia-ml.so.1` at runtime, from the loader path that the launcher of the host sets.
"""

import pynvml  # type: ignore[import-untyped]
from returns.result import Failure, Result, safe

from vitals.domain.errors import CollectorError, CollectorErrorKind
from vitals.domain.samples import GpuSample, Usage
from vitals.domain.units import Bytes, Celsius, Percent, Watts

_MILLIWATTS_PER_WATT = 1000.0


def nvml_error(exc: Exception) -> CollectorError:
    """Map an NVML exception to the error kind it means."""
    name = type(exc).__name__
    detail = str(exc) or name
    if name in {
        "NVMLError_LibraryNotFound",
        "NVMLError_DriverNotLoaded",
        "NVMLError_FunctionNotFound",
    }:
        kind = CollectorErrorKind.SOURCE_UNAVAILABLE
    elif name == "NVMLError_NoPermission":
        kind = CollectorErrorKind.PERMISSION_DENIED
    elif name in {"NVMLError_NotFound", "NVMLError_GpuNotFound", "NVMLError_GpuIsLost"}:
        kind = CollectorErrorKind.NO_DEVICE
    elif name == "NVMLError_NotSupported":
        kind = CollectorErrorKind.UNSUPPORTED
    else:
        kind = CollectorErrorKind.SOURCE_UNAVAILABLE
    return CollectorError(kind=kind, detail=detail)


def _initialize() -> None:
    pynvml.nvmlInit()


def _device_count() -> int:
    return int(pynvml.nvmlDeviceGetCount())


def _read_first_gpu() -> GpuSample:
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
    return GpuSample(
        name=str(pynvml.nvmlDeviceGetName(handle)),
        utilization=Percent(float(pynvml.nvmlDeviceGetUtilizationRates(handle).gpu)),
        vram=Usage(used=Bytes(int(memory.used)), total=Bytes(int(memory.total))),
        temperature=Celsius(
            float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)),
        ),
        power=Watts(float(pynvml.nvmlDeviceGetPowerUsage(handle)) / _MILLIWATTS_PER_WATT),
    )


class NvmlSource:
    """The first NVIDIA GPU, read through NVML."""

    def __init__(self) -> None:
        """Start unopened. The first read loads the library."""
        self._opened: Result[None, CollectorError] | None = None

    def _open(self) -> Result[None, CollectorError]:
        if self._opened is None:
            self._opened = safe(_initialize)().alt(nvml_error)
        return self._opened

    def first_gpu(self) -> Result[GpuSample, CollectorError]:
        """Return the state of the first NVIDIA device."""
        return (
            self._open()
            .bind(lambda _: safe(_device_count)().alt(nvml_error))
            .bind(self._read_when_present)
        )

    @staticmethod
    def _read_when_present(count: int) -> Result[GpuSample, CollectorError]:
        if count < 1:
            return Failure(
                CollectorError(kind=CollectorErrorKind.NO_DEVICE, detail="NVML reports no GPU"),
            )
        return safe(_read_first_gpu)().alt(nvml_error)
