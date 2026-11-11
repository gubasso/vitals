"""The body of the GPU panel: utilization, VRAM, temperature, and power."""

from typing import override

from textual.containers import Vertical
from textual.widgets import Label
lazy from textual.app import ComposeResult

from vitals.ui.format import gib
from vitals.ui.widgets.gauge import Gauge
lazy from vitals.domain.samples import GpuSample


class GpuBody(Vertical):
    """Two gauges and a line of the temperature and the power draw."""

    def __init__(self) -> None:
        """Create the empty body."""
        super().__init__(classes="panel-body")

    @override
    def compose(self) -> ComposeResult:
        """Yield the device name, the gauges, and the details."""
        yield Label("", id="gpu-name", classes="detail")
        yield Gauge("Usage", gauge_id="gpu-usage")
        yield Gauge("VRAM", gauge_id="gpu-vram")
        yield Label("", id="gpu-details", classes="detail")

    def show(self, sample: GpuSample) -> None:
        """Draw a GPU sample."""
        self.query_one("#gpu-name", Label).update(sample.name)
        self.query_one("#gpu-usage", Gauge).show(sample.utilization, f"{sample.utilization:.0f} %")
        vram = sample.vram
        self.query_one("#gpu-vram", Gauge).show(
            vram.percent,
            f"{gib(vram.used)} / {gib(vram.total)} GiB",
        )
        self.query_one("#gpu-details", Label).update(
            f"Temperature {sample.temperature:.0f} °C   Power {sample.power:.1f} W",
        )
