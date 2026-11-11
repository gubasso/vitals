"""The temperature history: a ring of fixed length for the chart."""

from collections import deque
from dataclasses import dataclass

from vitals.domain.units import Celsius, Seconds

WINDOW = Seconds(300.0)
"""The span of the chart: five minutes."""


@dataclass(frozen=True, slots=True, kw_only=True)
class TemperaturePoint:
    """The temperatures of one sampling tick. A missing sensor is None."""

    cpu_package: Celsius | None
    gpu: Celsius | None
    nvme: Celsius | None


class TemperatureHistory:
    """The points of the last window, oldest first."""

    def __init__(self, interval: Seconds, window: Seconds = WINDOW) -> None:
        """Size the ring as the window divided by the interval."""
        if interval <= 0:
            msg = "the sampling interval must be positive"
            raise ValueError(msg)
        self._points: deque[TemperaturePoint] = deque(maxlen=max(1, round(window / interval)))

    @property
    def capacity(self) -> int:
        """How many points the ring keeps."""
        return self._points.maxlen or 0

    def append(self, point: TemperaturePoint) -> None:
        """Add a point, dropping the oldest one when the ring is full."""
        self._points.append(point)

    def points(self) -> tuple[TemperaturePoint, ...]:
        """Return the points of the window, oldest first."""
        return tuple(self._points)
