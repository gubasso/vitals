"""The processes view: the top processes by CPU and by memory."""

from typing import override

from returns.result import Failure, Success
from textual.containers import Horizontal
from textual.content import Content
from textual.widgets import DataTable, Label
lazy from textual.app import ComposeResult

from vitals.domain.outcome import outcome
from vitals.domain.samples import ProcessEntry, ProcessesSample, Snapshot
from vitals.ui.format import size
from vitals.ui.views.base import View
from vitals.ui.widgets.panel import Panel
lazy from vitals.collectors.history import TemperaturePoint
lazy from vitals.domain.units import Seconds

_COLUMNS = ("PID", "Name", "User", "CPU %", "Memory")


def _table(table_id: str) -> DataTable[str]:
    table: DataTable[str] = DataTable(id=table_id, classes="panel-body", cursor_type="row")
    table.add_columns(*_COLUMNS)
    return table


def _fill(table: DataTable[str], entries: tuple[ProcessEntry, ...]) -> None:
    """Replace the rows, with each column as wide as its widest cell.

    A column of automatic width takes its new width only when the table next
    goes idle, and a frame drawn before that keeps the header at the old width.
    So the columns are rebuilt with explicit widths, the same widths that the
    automatic ones settle on, and the first frame draws the header right.
    """
    rows = [
        (str(entry.pid), entry.name, entry.user, f"{entry.cpu:.1f}", size(entry.resident))
        for entry in entries
    ]
    table.clear(columns=True)
    for index, label in enumerate(_COLUMNS):
        widths = [Content(label).cell_length, *(Content(row[index]).cell_length for row in rows)]
        table.add_column(label, width=max(widths))
    table.add_rows(rows)


class ProcessesView(View):
    """Two read-only tables of the top processes."""

    @override
    def compose(self) -> ComposeResult:
        """Yield the two titled tables between the header and the footer."""
        yield from self.compose_header()
        with Horizontal(id="processes"):
            with Panel("Top CPU", panel_id="top-cpu"):
                yield Label("", classes="panel-error")
                yield _table("top-cpu-table")
            with Panel("Top memory", panel_id="top-memory"):
                yield Label("", classes="panel-error")
                yield _table("top-memory-table")
        yield from self.compose_footer()

    @override
    async def show(
        self,
        snapshot: Snapshot,
        points: tuple[TemperaturePoint, ...],
        interval: Seconds,
    ) -> None:
        """Draw both rankings, or the failure of the source in both panels."""
        del points, interval
        panels = (self.query_one("#top-cpu", Panel), self.query_one("#top-memory", Panel))
        match outcome(snapshot.processes):
            case Success(ProcessesSample() as processes):
                for panel in panels:
                    panel.show_values()
                _fill(self.query_one("#top-cpu-table", DataTable), processes.top_cpu)
                _fill(self.query_one("#top-memory-table", DataTable), processes.top_memory)
            case Failure(error):
                for panel in panels:
                    panel.show_failure(error)
