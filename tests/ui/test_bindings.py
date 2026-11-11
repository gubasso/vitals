"""Each key binding of the dashboard does what the spec says."""

import time
from typing import override

from textual.widgets import DataTable
lazy from returns.result import Result

from tests.ui.conftest import AppFactory, settle
from vitals.adapters.fake_source import FakeSource
from vitals.domain.units import Percent, Seconds
from vitals.logs import configure_logging
from vitals.sources import fake_sources
from vitals.ui.app import VitalsApp, view_names
from vitals.ui.views.overview import OverviewView
from vitals.ui.views.processes import ProcessesView
from vitals.ui.widgets.gauge import Gauge
from vitals.ui.widgets.temperature_chart import TemperatureChart, rich_color
lazy from vitals.domain.errors import CollectorError


async def test_keys_switch_the_views(make_app: AppFactory) -> None:
    """`2` opens the processes view and `1` returns to the overview."""
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        assert isinstance(app.screen, OverviewView)
        await pilot.press("2")
        await settle(pilot)
        assert isinstance(app.screen, ProcessesView)
        assert app.screen.query_one("#top-cpu-table", DataTable).row_count == 5
        await pilot.press("1")
        assert isinstance(app.screen, OverviewView)


async def test_the_first_view_comes_from_the_caller(make_app: AppFactory) -> None:
    """An app started on `processes` opens that view first."""
    app = make_app(view="processes")
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        assert isinstance(app.screen, ProcessesView)


async def test_q_quits(make_app: AppFactory) -> None:
    """`q` ends the app."""
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await pilot.press("q")
    assert app.return_code == 0


async def test_question_mark_toggles_the_help(make_app: AppFactory) -> None:
    """`?` shows the key bindings, and a second `?` hides them."""
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await pilot.press("question_mark")
        assert app.screen.query("HelpPanel")
        await pilot.press("question_mark")
        await pilot.pause()
        assert not app.screen.query("HelpPanel")


async def test_ctrl_p_opens_the_palette(make_app: AppFactory) -> None:
    """`ctrl+p` opens the command palette, where the theme is picked."""
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        await pilot.press("ctrl+p")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "CommandPalette"


async def test_a_theme_change_reaches_every_panel(make_app: AppFactory) -> None:
    """A new theme changes the border color of every panel."""
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        before = {panel.id: panel.styles.border_top[1] for panel in app.screen.query(".panel")}
        app.theme = "nord"
        await pilot.pause()
        after = {panel.id: panel.styles.border_top[1] for panel in app.screen.query(".panel")}
        assert before.keys() == after.keys()
        assert all(before[key] != after[key] for key in before)


async def test_the_cpu_panel_holds_one_gauge(make_app: AppFactory) -> None:
    """The CPU panel draws the aggregate usage, and no gauge per core."""
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        assert len(app.screen.query_one("#cpu").query(Gauge)) == 1


class SlowCpu(FakeSource):
    """A fake whose CPU read takes a second."""

    @override
    def usage(self) -> Result[Percent, CollectorError]:
        """Answer after one second."""
        time.sleep(1.0)
        return super().usage()


async def test_keys_answer_while_a_source_is_slow() -> None:
    """The worker reads off the event loop, so `2` switches the view while the read waits."""
    app = VitalsApp(sources=fake_sources(SlowCpu()), interval=Seconds(10.0))
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        started = time.monotonic()
        await pilot.press("2")
        assert isinstance(app.screen, ProcessesView)
        assert time.monotonic() - started < 0.5


def test_the_registry_names_both_views() -> None:
    """The registry holds the overview on `1` and the processes on `2`."""
    assert view_names() == ("overview", "processes")


async def test_an_ansi_theme_draws_the_chart(make_app: AppFactory) -> None:
    """An ANSI theme names its colors `ansi_<name>`, and the chart still draws with it."""
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
        app.theme = "ansi-dark"
        app.sample()
        await settle(pilot)
        chart = app.screen.query_one(TemperatureChart)
        assert chart.region.height > 0
        assert rich_color(app.theme_variables["primary"]) == "blue"


async def test_a_failing_source_is_logged_to_the_file(make_app: AppFactory) -> None:
    """A source that starts to fail writes one warning to vitals.log."""
    path = configure_logging()
    app = make_app(failing=frozenset({"gpu"}))
    async with app.run_test(size=(120, 40)) as pilot:
        await settle(pilot)
    log = path.read_text(encoding="utf-8")
    assert log.count("source gpu failed: source-unavailable") == 1
