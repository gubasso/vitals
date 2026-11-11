"""A labeled gauge: a label, a bar, and the value with its unit."""

from typing import override

from textual.containers import Horizontal
from textual.widgets import Label, ProgressBar
lazy from textual.app import ComposeResult

from vitals.domain.units import Percent

WARNING_AT = Percent(70.0)
"""The share from which the bar takes the warning color."""

CRITICAL_AT = Percent(90.0)
"""The share from which the bar takes the error color."""


class Gauge(Horizontal):
    """One labeled bar of a share, with the value and its unit beside it."""

    def __init__(self, label: str, *, gauge_id: str | None = None) -> None:
        """Create an empty gauge with its label."""
        super().__init__(id=gauge_id, classes="gauge")
        self._label = label

    @override
    def compose(self) -> ComposeResult:
        """Yield the label, the bar, and the value."""
        yield Label(self._label, classes="gauge-label")
        yield ProgressBar(total=100.0, show_eta=False, show_percentage=False)
        yield Label("", classes="gauge-value")

    def show(self, share: Percent, value: str) -> None:
        """Set the bar to a share, and the text beside it to a value with its unit."""
        self.query_one(ProgressBar).update(progress=share)
        self.query_one(".gauge-value", Label).update(value)
        self.set_class(WARNING_AT <= share < CRITICAL_AT, "-warning")
        self.set_class(share >= CRITICAL_AT, "-critical")
