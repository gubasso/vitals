"""The line chart of the last five minutes of temperatures."""

from typing import TYPE_CHECKING

from textual_plot import HiResMode, LegendLocation, PlotWidget

lazy from vitals.collectors.history import TemperaturePoint

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from vitals.domain.units import Celsius, Seconds

# The space between the extreme values and the edges of the chart, so no line lies on an axis.
_MARGIN = 2.0

# Each series: its legend label, how to read it from a point, and the theme variable of its color.
_SERIES: tuple[tuple[str, Callable[[TemperaturePoint], Celsius | None], str], ...] = (
    ("CPU package", lambda point: point.cpu_package, "primary"),
    ("GPU", lambda point: point.gpu, "warning"),
    ("NVMe", lambda point: point.nvme, "success"),
)


def rich_color(token: str) -> str:
    """Return a theme color as Rich parses it: Textual names ANSI colors `ansi_<name>`."""
    return token.removeprefix("ansi_")


class TemperatureChart(PlotWidget):
    """One line per sensor over the window, with a legend and a degrees axis."""

    def __init__(self) -> None:
        """Create the empty chart."""
        super().__init__(classes="panel-body")
        # The chart is read-only: no focus, so the footer shows no zoom or pan key.
        self.can_focus = False

    def show(self, points: Sequence[TemperaturePoint], interval: Seconds) -> None:
        """Draw the points, the newest at 0 seconds and the oldest on the left."""
        self.clear()
        variables = self.app.theme_variables
        count = len(points)
        values: list[float] = []
        for label, read, color in _SERIES:
            pairs = [
                (-interval * (count - 1 - index), value)
                for index, point in enumerate(points)
                if (value := read(point)) is not None
            ]
            if not pairs:
                continue
            values.extend(y for _, y in pairs)
            self.plot(
                [x for x, _ in pairs],
                [y for _, y in pairs],
                line_style=rich_color(variables[color]),
                hires_mode=HiResMode.BRAILLE,
                label=label,
            )
        if values:
            self.set_ylimits(min(values) - _MARGIN, max(values) + _MARGIN)
        self.set_ylabel("°C")
        self.set_xlabel("seconds ago")
        self.show_legend(location=LegendLocation.TOPLEFT)
