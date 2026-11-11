"""The temperature collector, and the sensor readings that the CPU collector shares."""

from dataclasses import dataclass
from typing import Protocol
lazy from collections.abc import Sequence

from returns.result import Failure, Result, Success

from vitals.domain.errors import CollectorError, CollectorErrorKind
from vitals.domain.samples import TemperatureSample
lazy from vitals.domain.units import Celsius

# The sensor of the CPU package, by chip, in the order a host is likely to report it.
_PACKAGE_SENSORS = (("coretemp", "Package id 0"), ("k10temp", "Tctl"), ("k10temp", "Tdie"))
_NVME_SENSOR = ("nvme", "Composite")


@dataclass(frozen=True, slots=True, kw_only=True)
class SensorReading:
    """One reading of one hardware sensor."""

    chip: str
    label: str
    current: Celsius


class TemperatureSource(Protocol):
    """What the temperature collector reads."""

    def sensors(self) -> Result[Sequence[SensorReading], CollectorError]:
        """Every temperature sensor of the machine."""
        ...


def _find(readings: Sequence[SensorReading], chip: str, label: str) -> Celsius | None:
    for reading in readings:
        if reading.chip == chip and reading.label == label:
            return reading.current
    return None


def package_temperature(readings: Sequence[SensorReading]) -> Celsius | None:
    """Return the temperature of the CPU package, where a known sensor reports it."""
    for chip, label in _PACKAGE_SENSORS:
        found = _find(readings, chip, label)
        if found is not None:
            return found
    return None


def _sample(readings: Sequence[SensorReading]) -> Result[TemperatureSample, CollectorError]:
    if not readings:
        return Failure(
            CollectorError(
                kind=CollectorErrorKind.NO_DEVICE,
                detail="the machine reports no temperature sensor",
            ),
        )
    return Success(
        TemperatureSample(
            cpu_package=package_temperature(readings),
            nvme=_find(readings, *_NVME_SENSOR),
        ),
    )


def collect_temperatures(source: TemperatureSource) -> Result[TemperatureSample, CollectorError]:
    """Read the CPU package and NVMe temperatures."""
    return source.sensors().bind(_sample)
