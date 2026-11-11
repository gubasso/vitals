"""The disk collector collapses the mounts of one block device."""

from returns.result import Success

from vitals.adapters.fake_source import FAKE_MOUNTS, FakeSource
from vitals.collectors.disks import Mount, collapse_by_device, collect_disks
from vitals.domain.samples import DisksSample


def test_subvolumes_collapse_to_the_shortest_mount() -> None:
    """The tumblesuse table gives one bar each for the root, the EFI partition, and the drive."""
    assert [mount.mount_point for mount in collapse_by_device(FAKE_MOUNTS)] == [
        "/",
        "/boot/efi",
        "/run/media/gbasso/data",
    ]


def test_pseudo_filesystems_are_skipped() -> None:
    """A tmpfs or an overlay holds no data of a block device."""
    mounts = (
        Mount(device="tmpfs", mount_point="/run/user/1000", filesystem="tmpfs"),
        Mount(device="/dev/loop0", mount_point="/snap/core", filesystem="squashfs"),
    )
    assert collapse_by_device(mounts) == ()


def test_the_collector_reads_one_usage_per_device() -> None:
    """Each sample carries its device, its mount point, and its usage."""
    match collect_disks(FakeSource()):
        case Success(DisksSample() as sample):
            assert [disk.device for disk in sample.disks] == [
                "/dev/mapper/system-root",
                "/dev/nvme0n1p1",
                "/dev/sda1",
            ]
        case _:
            raise AssertionError
