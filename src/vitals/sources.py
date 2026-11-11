"""Pick the sources of a run: the real machine, or the fakes."""

from vitals.adapters.fake_source import FakeSource
from vitals.adapters.nvml_source import NvmlSource
from vitals.adapters.psutil_source import PsutilSource
from vitals.collectors.snapshot import Sources


def machine_sources() -> Sources:
    """Return the sources of this machine: psutil for most, NVML for the GPU."""
    system = PsutilSource()
    return Sources(
        host=system,
        cpu=system,
        memory=system,
        disks=system,
        temperatures=system,
        gpu=NvmlSource(),
        processes=system,
    )


def fake_sources(fake: FakeSource | None = None) -> Sources:
    """Every source from one fake, for the tests and the packaged smoke check."""
    source = fake or FakeSource()
    return Sources(
        host=source,
        cpu=source,
        memory=source,
        disks=source,
        temperatures=source,
        gpu=source,
        processes=source,
    )
