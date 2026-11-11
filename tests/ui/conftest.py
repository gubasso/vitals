"""Build the app over the fakes, with a fixed temperature history."""

from collections.abc import Callable

import pytest
lazy from textual.pilot import Pilot

from vitals.adapters.fake_source import FakeSource
from vitals.collectors.history import TemperaturePoint
from vitals.domain.errors import CollectorErrorKind
from vitals.domain.units import Celsius
from vitals.sources import fake_sources
from vitals.ui.app import VitalsApp

# A fixed wave of five minutes at 2 seconds, so every snapshot draws the same chart.
_WAVE = tuple(
    TemperaturePoint(
        cpu_package=Celsius(55.0 + (index % 30)),
        gpu=Celsius(48.0 + (index % 12)),
        nvme=Celsius(41.0 + (index % 4)),
    )
    for index in range(149)
)

type AppFactory = Callable[..., VitalsApp]


@pytest.fixture
def make_app() -> AppFactory:
    """Return a factory of apps over the fakes. A name in `failing` fails that source."""

    def make(
        *,
        view: str = "overview",
        failing: frozenset[str] = frozenset(),
    ) -> VitalsApp:
        fake = FakeSource(failing=failing, failure_kind=CollectorErrorKind.SOURCE_UNAVAILABLE)
        app = VitalsApp(sources=fake_sources(fake), view=view)
        for point in _WAVE:
            app.history.append(point)
        return app

    return make


async def settle(pilot: Pilot[None]) -> None:
    """Wait for the first sample to reach the screen."""
    await pilot.pause()
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()
