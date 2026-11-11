"""The CPU collector returns the aggregate state and no value per core."""

from dataclasses import fields

from returns.result import Failure, Success

from vitals.adapters.fake_source import FakeSource
from vitals.collectors.cpu import collect_cpu
from vitals.domain.errors import CollectorError, CollectorErrorKind
from vitals.domain.samples import CpuSample
from vitals.domain.units import Celsius, Percent


def test_the_sample_is_aggregate() -> None:
    """The sample holds one usage, the package temperature, and no list of cores."""
    match collect_cpu(FakeSource()):
        case Success(CpuSample() as sample):
            assert sample.usage == Percent(37.0)
            assert sample.package_temperature == Celsius(68.0)
            assert {field.name for field in fields(sample)} == {
                "usage",
                "package_temperature",
                "frequency",
                "load",
            }
        case _:
            raise AssertionError


def test_a_failed_usage_fails_the_sample() -> None:
    """A source that cannot read the usage gives a Failure, not an exception."""
    result = collect_cpu(FakeSource(failing=frozenset({"cpu"})))
    assert result == Failure(
        CollectorError(kind=CollectorErrorKind.SOURCE_UNAVAILABLE, detail="fake cpu failure"),
    )


def test_missing_sensors_leave_the_temperature_empty() -> None:
    """Unreadable sensors keep the sample, without its temperature."""
    match collect_cpu(FakeSource(failing=frozenset({"temperatures"}))):
        case Success(CpuSample() as sample):
            assert sample.package_temperature is None
        case _:
            raise AssertionError
