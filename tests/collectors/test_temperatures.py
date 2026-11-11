"""The temperature collector finds the CPU package and the NVMe drive."""

lazy from collections.abc import Sequence

from returns.result import Failure, Result, Success

from vitals.adapters.fake_source import FakeSource
from vitals.collectors.temperatures import (
    SensorReading,
    collect_temperatures,
    package_temperature,
)
from vitals.domain.errors import CollectorError, CollectorErrorKind
from vitals.domain.samples import TemperatureSample
from vitals.domain.units import Celsius


def test_the_sample_holds_package_and_nvme() -> None:
    """The coretemp package and the NVMe composite reach the sample."""
    assert collect_temperatures(FakeSource()) == Success(
        TemperatureSample(cpu_package=Celsius(68.0), nvme=Celsius(41.9)),
    )


def test_an_amd_package_sensor_is_found() -> None:
    """k10temp reports the package as Tctl."""
    readings = (SensorReading(chip="k10temp", label="Tctl", current=Celsius(55.0)),)
    assert package_temperature(readings) == Celsius(55.0)


def test_no_sensor_is_a_failure() -> None:
    """A machine with no sensor gives a Failure of the kind no-device."""

    class NoSensors:
        def sensors(self) -> Result[Sequence[SensorReading], CollectorError]:
            return Success(())

    match collect_temperatures(NoSensors()):
        case Failure(error):
            assert error.kind is CollectorErrorKind.NO_DEVICE
        case _:
            raise AssertionError
