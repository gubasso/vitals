"""The disk collector: one sample per block device, its mounts collapsed."""

from dataclasses import dataclass
from typing import Protocol
lazy from collections.abc import Sequence

from returns.result import Failure, Result, Success

from vitals.domain.outcome import outcome
from vitals.domain.samples import DiskSample, DisksSample, Usage
lazy from vitals.domain.errors import CollectorError

# Filesystems that hold no data of a block device.
PSEUDO_FILESYSTEMS = frozenset(
    {"tmpfs", "devtmpfs", "proc", "sysfs", "overlay", "squashfs", "ramfs", "efivarfs", "fuse"},
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Mount:
    """One mounted filesystem."""

    device: str
    mount_point: str
    filesystem: str


class DiskSource(Protocol):
    """What the disk collector reads."""

    def mounts(self) -> Result[Sequence[Mount], CollectorError]:
        """Return the mounted filesystems."""
        ...

    def usage_of(self, mount_point: str) -> Result[Usage, CollectorError]:
        """Return the usage of the filesystem at a mount point."""
        ...


def collapse_by_device(mounts: Sequence[Mount]) -> tuple[Mount, ...]:
    """Keep one mount per block device, the shortest mount point, in device order."""
    chosen: dict[str, Mount] = {}
    for mount in mounts:
        if mount.filesystem in PSEUDO_FILESYSTEMS or not mount.device.startswith("/dev/"):
            continue
        known = chosen.get(mount.device)
        if known is None or len(mount.mount_point) < len(known.mount_point):
            chosen[mount.device] = mount
    return tuple(sorted(chosen.values(), key=lambda mount: mount.mount_point))


def _sample(source: DiskSource, mounts: Sequence[Mount]) -> Result[DisksSample, CollectorError]:
    disks: list[DiskSample] = []
    for mount in collapse_by_device(mounts):
        match outcome(source.usage_of(mount.mount_point)):
            case Success(value):
                disks.append(
                    DiskSample(device=mount.device, mount_point=mount.mount_point, usage=value),
                )
            case Failure(_):
                # A mount that vanished between the two reads drops out of this sample.
                continue
    return Success(DisksSample(disks=tuple(disks)))


def collect_disks(source: DiskSource) -> Result[DisksSample, CollectorError]:
    """Read one usage per block device."""
    return source.mounts().bind(lambda mounts: _sample(source, mounts))
