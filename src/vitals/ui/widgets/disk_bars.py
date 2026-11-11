"""One labeled bar per disk."""

from textual.containers import Vertical

from vitals.ui.format import gib
from vitals.ui.widgets.gauge import Gauge
lazy from vitals.domain.samples import DisksSample


class DiskBars(Vertical):
    """A gauge for each disk, labeled with its mount point, used, and total."""

    def __init__(self) -> None:
        """Start with no bar."""
        super().__init__(classes="panel-body")
        self._mounts: tuple[str, ...] = ()

    async def show(self, sample: DisksSample) -> None:
        """Draw one bar per disk, and rebuild the bars when the disks change."""
        mounts = tuple(disk.mount_point for disk in sample.disks)
        if mounts != self._mounts:
            await self.remove_children()
            await self.mount_all(Gauge(mount) for mount in mounts)
            # Every label takes the width of the longest mount point, so the bars line up.
            width = max((len(mount) for mount in mounts), default=0) + 2
            for label in self.query(".gauge-label"):
                label.styles.width = width
            self._mounts = mounts
        for gauge, disk in zip(self.query(Gauge), sample.disks, strict=True):
            usage = disk.usage
            gauge.show(usage.percent, f"{gib(usage.used)} / {gib(usage.total)} GiB")
