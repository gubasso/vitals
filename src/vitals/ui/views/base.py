"""What every view shares: the header, the footer, and how it receives a snapshot."""

from abc import abstractmethod

from textual.screen import Screen
from textual.widgets import Footer, Header
lazy from textual.app import ComposeResult

lazy from vitals.collectors.history import TemperaturePoint
lazy from vitals.domain.samples import Snapshot
lazy from vitals.domain.units import Seconds


class View(Screen[None]):
    """A screen of the dashboard that draws each new snapshot."""

    def compose_header(self) -> ComposeResult:
        """Yield the header, which shows the host and its uptime."""
        yield Header(icon="◉")

    def compose_footer(self) -> ComposeResult:
        """Yield the footer, which shows the key bindings."""
        yield Footer()

    @abstractmethod
    async def show(
        self,
        snapshot: Snapshot,
        points: tuple[TemperaturePoint, ...],
        interval: Seconds,
    ) -> None:
        """Draw a snapshot and the temperature history."""
