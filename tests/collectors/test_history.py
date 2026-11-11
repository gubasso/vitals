"""The temperature history keeps a fixed window."""

from vitals.collectors.history import TemperatureHistory, TemperaturePoint
from vitals.domain.units import Celsius, Seconds


def _point(value: float) -> TemperaturePoint:
    return TemperaturePoint(cpu_package=Celsius(value), gpu=None, nvme=None)


def test_the_ring_holds_the_window_over_the_interval() -> None:
    """Five minutes at 2 seconds is 150 points."""
    assert TemperatureHistory(interval=Seconds(2.0)).capacity == 150


def test_a_full_ring_drops_the_oldest_point() -> None:
    """The 151st point pushes out the first one."""
    history = TemperatureHistory(interval=Seconds(2.0))
    for value in range(151):
        history.append(_point(float(value)))
    points = history.points()
    assert len(points) == 150
    assert points[0].cpu_package == Celsius(1.0)
