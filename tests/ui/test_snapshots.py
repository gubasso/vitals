"""Each view, each failed panel, and each terminal size, as a recorded screen."""

import pytest
lazy from textual.pilot import Pilot

from tests.ui.conftest import AppFactory, settle

SnapCompare = object  # pytest-textual-snapshot passes a callable; its type is not exported.

SIZES = ((120, 40), (100, 32))
FAILING_SOURCES = ("cpu", "gpu", "memory", "disks", "temperatures", "processes")


async def _ready(pilot: Pilot[None]) -> None:
    await settle(pilot)


@pytest.mark.parametrize("size", SIZES, ids=lambda size: f"{size[0]}x{size[1]}")
def test_overview(snap_compare: SnapCompare, make_app: AppFactory, size: tuple[int, int]) -> None:
    """The overview with every source populated."""
    assert snap_compare(make_app(), terminal_size=size, run_before=_ready)  # type: ignore[operator]


@pytest.mark.parametrize("size", SIZES, ids=lambda size: f"{size[0]}x{size[1]}")
def test_processes(snap_compare: SnapCompare, make_app: AppFactory, size: tuple[int, int]) -> None:
    """The processes view with both rankings."""
    app = make_app(view="processes")
    assert snap_compare(app, terminal_size=size, run_before=_ready)  # type: ignore[operator]


@pytest.mark.parametrize("source", FAILING_SOURCES)
def test_a_failed_source(snap_compare: SnapCompare, make_app: AppFactory, source: str) -> None:
    """A failed source shows its error kind in its panel, and the other panels draw."""
    view = "processes" if source == "processes" else "overview"
    app = make_app(view=view, failing=frozenset({source}))
    assert snap_compare(app, terminal_size=(120, 40), run_before=_ready)  # type: ignore[operator]
