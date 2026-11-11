"""Read every source of the real machine once. Run by hand: pytest -m host."""

import time

import pytest
from returns.result import Success

from vitals.collectors.snapshot import collect_snapshot
from vitals.sources import machine_sources


@pytest.mark.host
def test_every_source_of_this_machine_reads() -> None:
    """On tumblesuse, every source gives a Success, the GPU over NVML included."""
    sources = machine_sources()
    time.sleep(0.5)
    snapshot = collect_snapshot(sources)
    for name in ("host", "cpu", "memory", "disks", "temperatures", "gpu", "processes"):
        assert isinstance(getattr(snapshot, name), Success), name
