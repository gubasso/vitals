"""The Textual app: the view registry, the bindings, and the sampling worker."""

from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import ClassVar
lazy from collections.abc import Callable

from returns.result import Failure, Success
from textual import work
from textual.app import App
from textual.binding import Binding, BindingType
from textual.message import Message

from vitals.collectors.history import TemperatureHistory, TemperaturePoint
from vitals.collectors.snapshot import Sources, collect_snapshot
from vitals.domain.outcome import outcome, value_or_none
from vitals.domain.samples import HostSample, Snapshot
from vitals.domain.units import Seconds
from vitals.logs import LOGGER
from vitals.report import failures
from vitals.ui.format import uptime
from vitals.ui.views.base import View
from vitals.ui.views.overview import OverviewView
from vitals.ui.views.processes import ProcessesView

DEFAULT_INTERVAL = Seconds(2.0)
"""The sampling interval when the configuration names none."""

DEFAULT_THEME = "textual-dark"
"""The theme when the configuration names none."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ViewEntry:
    """One view of the registry: its name, its key, and its screen."""

    name: str
    key: str
    description: str
    screen: Callable[[], View]


VIEWS: tuple[ViewEntry, ...] = (
    ViewEntry(name="overview", key="1", description="Overview", screen=OverviewView),
    ViewEntry(name="processes", key="2", description="Processes", screen=ProcessesView),
)
"""Every view, in key order. A new view is one entry here."""


def view_names() -> tuple[str, ...]:
    """Return the names of the views, in key order."""
    return tuple(entry.name for entry in VIEWS)


class SnapshotReady(Message):
    """The worker built a new snapshot."""

    def __init__(self, snapshot: Snapshot) -> None:
        """Carry the snapshot to the app."""
        super().__init__()
        self.snapshot = snapshot


def _point(snapshot: Snapshot) -> TemperaturePoint:
    temperatures = value_or_none(snapshot.temperatures)
    gpu = value_or_none(snapshot.gpu)
    return TemperaturePoint(
        cpu_package=None if temperatures is None else temperatures.cpu_package,
        gpu=None if gpu is None else gpu.temperature,
        nvme=None if temperatures is None else temperatures.nvme,
    )


class VitalsApp(App[None]):
    """The dashboard of the vital signs of the machine."""

    CSS_PATH: ClassVar[str | PurePath | list[str | PurePath] | None] = (
        Path(__file__).parent / "vitals.tcss"
    )
    TITLE: str | None = "vitals"
    BINDINGS: ClassVar[list[BindingType]] = [
        *(Binding(entry.key, f"open_view('{entry.name}')", entry.description) for entry in VIEWS),
        Binding("q", "quit", "Quit"),
        Binding("question_mark", "toggle_help", "Help", key_display="?"),
    ]

    def __init__(
        self,
        *,
        sources: Sources,
        view: str = "overview",
        interval: Seconds = DEFAULT_INTERVAL,
        theme: str = DEFAULT_THEME,
    ) -> None:
        """Create the app over its sources, with its first view, interval, and theme."""
        super().__init__()
        self._sources = sources
        self._first_view = view
        self.interval = interval
        self.theme = theme
        self.history = TemperatureHistory(interval=interval)
        self.latest: Snapshot | None = None
        self._failing: dict[str, str] = {}

    async def on_mount(self) -> None:
        """Register the views, open the first one, sample now, and sample at every interval."""
        for entry in VIEWS:
            self.add_mode(entry.name, entry.screen)
        await self.switch_mode(self._first_view)
        self.sample()
        self.set_interval(self.interval, self.sample)

    @work(thread=True, exclusive=True, group="sampling")
    def sample(self) -> None:
        """Build a snapshot off the event loop, and post it to the app."""
        self.post_message(SnapshotReady(collect_snapshot(self._sources)))

    async def on_snapshot_ready(self, message: SnapshotReady) -> None:
        """Keep the snapshot, extend the history, and draw the active view."""
        self.latest = message.snapshot
        self._log_failures(message.snapshot)
        self.history.append(_point(message.snapshot))
        self._show_host(message.snapshot)
        await self._draw()

    async def action_open_view(self, name: str) -> None:
        """Open a view of the registry, and draw the latest snapshot on it at once."""
        await self.switch_mode(name)
        await self._draw()

    async def _draw(self) -> None:
        screen = self.screen
        if self.latest is not None and isinstance(screen, View):
            await screen.show(self.latest, self.history.points(), self.interval)

    def _log_failures(self, snapshot: Snapshot) -> None:
        """Log a source when it starts to fail, and when it recovers, once each."""
        for name, error in failures(snapshot).items():
            if self._failing.get(name) != str(error.kind):
                LOGGER.warning("source %s failed: %s: %s", name, error.kind, error.detail)
        for name in self._failing.keys() - failures(snapshot).keys():
            LOGGER.info("source %s recovered", name)
        self._failing = {name: str(error.kind) for name, error in failures(snapshot).items()}

    def _show_host(self, snapshot: Snapshot) -> None:
        match outcome(snapshot.host):
            case Success(HostSample() as host):
                self.sub_title = f"{host.name} · up {uptime(host.uptime)}"
            case Failure(error):
                self.sub_title = str(error.kind)

    def action_toggle_help(self) -> None:
        """Show the key bindings of the active view, or hide them."""
        if self.screen.query("HelpPanel"):
            self.action_hide_help_panel()
        else:
            self.action_show_help_panel()


def run_app(
    *,
    sources: Sources,
    view: str = "overview",
    interval: Seconds = DEFAULT_INTERVAL,
    theme: str = DEFAULT_THEME,
) -> None:
    """Run the dashboard until the user quits."""
    VitalsApp(sources=sources, view=view, interval=interval, theme=theme).run()
