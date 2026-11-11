"""The GPU collector reads NVML, and maps its errors to the closed kinds."""

from returns.result import Failure, Success

from vitals.adapters.fake_source import FAKE_GPU, FakeSource
from vitals.adapters.nvml_source import nvml_error
from vitals.collectors.gpu import collect_gpu
from vitals.domain.errors import CollectorErrorKind


class NVMLError_LibraryNotFound(Exception):  # noqa: N801, N818 - the name pynvml gives it
    """Stand in for the pynvml error of a missing libnvidia-ml.so.1."""


class NVMLError_NoPermission(Exception):  # noqa: N801, N818 - the name pynvml gives it
    """Stand in for the pynvml error of a denied device."""


def test_the_sample_holds_the_four_values() -> None:
    """Utilization, VRAM, temperature, and power reach the sample."""
    assert collect_gpu(FakeSource()) == Success(FAKE_GPU)


def test_a_missing_library_is_source_unavailable() -> None:
    """A host without the NVIDIA driver library reports source-unavailable."""
    error = nvml_error(NVMLError_LibraryNotFound("libnvidia-ml.so.1 not found"))
    assert error.kind is CollectorErrorKind.SOURCE_UNAVAILABLE


def test_a_denied_device_is_permission_denied() -> None:
    """A device the user cannot open reports permission-denied."""
    assert nvml_error(NVMLError_NoPermission()).kind is CollectorErrorKind.PERMISSION_DENIED


def test_a_failed_gpu_fails_alone() -> None:
    """The fake GPU failure comes back as a Failure."""
    assert isinstance(collect_gpu(FakeSource(failing=frozenset({"gpu"}))), Failure)
