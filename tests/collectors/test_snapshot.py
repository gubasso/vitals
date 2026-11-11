"""A snapshot holds one Result per source, and a failed source fails alone."""

from returns.result import Failure, Success

from vitals.adapters.fake_source import FakeSource
from vitals.collectors.snapshot import collect_snapshot
from vitals.sources import fake_sources


def test_only_the_gpu_fails() -> None:
    """A GPU failure leaves every other source a Success."""
    snapshot = collect_snapshot(fake_sources(FakeSource(failing=frozenset({"gpu"}))))
    assert isinstance(snapshot.gpu, Failure)
    for result in (
        snapshot.host,
        snapshot.cpu,
        snapshot.memory,
        snapshot.disks,
        snapshot.temperatures,
        snapshot.processes,
    ):
        assert isinstance(result, Success)
