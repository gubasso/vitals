"""The overview view: the vital signs of the machine at a glance."""

from typing import override

from returns.result import Failure, Success
from textual.containers import Grid, Vertical
from textual.widgets import Label
lazy from textual.app import ComposeResult

from vitals.domain.outcome import outcome
from vitals.domain.samples import CpuSample, DisksSample, GpuSample, MemorySample, Snapshot
from vitals.ui.format import gib
from vitals.ui.views.base import View
from vitals.ui.widgets.disk_bars import DiskBars
from vitals.ui.widgets.gauge import Gauge
from vitals.ui.widgets.gpu_panel import GpuBody
from vitals.ui.widgets.panel import Panel
from vitals.ui.widgets.temperature_chart import TemperatureChart
lazy from vitals.collectors.history import TemperaturePoint
lazy from vitals.domain.units import Seconds


def _error_label() -> Label:
    return Label("", classes="panel-error")


class OverviewView(View):
    """CPU, GPU, memory, swap, disks, and the temperature chart."""

    @override
    def compose(self) -> ComposeResult:
        """Yield the six titled panels between the header and the footer."""
        yield from self.compose_header()
        with Grid(id="overview"):
            with Panel("CPU", panel_id="cpu"):
                yield _error_label()
                with Vertical(classes="panel-body"):
                    yield Gauge("Usage", gauge_id="cpu-usage")
                    yield Label("", id="cpu-details", classes="detail")
                    yield Label("", id="cpu-load", classes="detail")
            with Panel("GPU", panel_id="gpu"):
                yield _error_label()
                yield GpuBody()
            with Panel("Memory", panel_id="memory"):
                yield _error_label()
                with Vertical(classes="panel-body"):
                    yield Gauge("Used", gauge_id="memory-used")
            with Panel("Swap", panel_id="swap"):
                yield _error_label()
                with Vertical(classes="panel-body"):
                    yield Gauge("Used", gauge_id="swap-used")
            with Panel("Disks", panel_id="disks"):
                yield _error_label()
                yield DiskBars()
            with Panel("Temperatures", panel_id="temperatures"):
                yield _error_label()
                yield TemperatureChart()
        yield from self.compose_footer()

    @override
    async def show(
        self,
        snapshot: Snapshot,
        points: tuple[TemperaturePoint, ...],
        interval: Seconds,
    ) -> None:
        """Draw every panel. A failed source shows its error kind in its panel."""
        self._show_cpu(snapshot)
        self._show_gpu(snapshot)
        self._show_memory(snapshot)
        await self._show_disks(snapshot)
        self._show_temperatures(snapshot, points, interval)

    def _panel(self, panel_id: str) -> Panel:
        return self.query_one(f"#{panel_id}", Panel)

    def _show_cpu(self, snapshot: Snapshot) -> None:
        panel = self._panel("cpu")
        match outcome(snapshot.cpu):
            case Success(CpuSample() as cpu):
                panel.show_values()
                self.query_one("#cpu-usage", Gauge).show(cpu.usage, f"{cpu.usage:.0f} %")
                temperature = (
                    "n/a"
                    if cpu.package_temperature is None
                    else f"{cpu.package_temperature:.0f} °C"
                )
                frequency = "n/a" if cpu.frequency is None else f"{cpu.frequency:.0f} MHz"
                self.query_one("#cpu-details", Label).update(
                    f"Package {temperature}   Frequency {frequency}",
                )
                load = cpu.load
                self.query_one("#cpu-load", Label).update(
                    f"Load {load.one:.2f}  {load.five:.2f}  {load.fifteen:.2f}",
                )
            case Failure(error):
                panel.show_failure(error)

    def _show_gpu(self, snapshot: Snapshot) -> None:
        panel = self._panel("gpu")
        match outcome(snapshot.gpu):
            case Success(GpuSample() as gpu):
                panel.show_values()
                self.query_one(GpuBody).show(gpu)
            case Failure(error):
                panel.show_failure(error)

    def _show_memory(self, snapshot: Snapshot) -> None:
        match outcome(snapshot.memory):
            case Success(MemorySample() as memory):
                for name, usage in (("memory", memory.memory), ("swap", memory.swap)):
                    self._panel(name).show_values()
                    self.query_one(f"#{name}-used", Gauge).show(
                        usage.percent,
                        f"{gib(usage.used)} / {gib(usage.total)} GiB",
                    )
            case Failure(error):
                self._panel("memory").show_failure(error)
                self._panel("swap").show_failure(error)

    async def _show_disks(self, snapshot: Snapshot) -> None:
        panel = self._panel("disks")
        match outcome(snapshot.disks):
            case Success(DisksSample() as disks):
                panel.show_values()
                await self.query_one(DiskBars).show(disks)
            case Failure(error):
                panel.show_failure(error)

    def _show_temperatures(
        self,
        snapshot: Snapshot,
        points: tuple[TemperaturePoint, ...],
        interval: Seconds,
    ) -> None:
        panel = self._panel("temperatures")
        match outcome(snapshot.temperatures):
            case Success(_):
                panel.show_values()
                self.query_one(TemperatureChart).show(points, interval)
            case Failure(error):
                panel.show_failure(error)
