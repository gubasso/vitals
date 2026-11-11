"""The processes collector ranks by CPU and by memory, and skips a vanished process."""

from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass

import psutil
from returns.result import Success

from vitals.adapters.fake_source import FakeSource
from vitals.adapters.psutil_source import read_processes
from vitals.collectors.processes import collect_processes
from vitals.domain.samples import ProcessesSample


@dataclass(frozen=True, slots=True, kw_only=True)
class _Memory:
    rss: int


@dataclass(frozen=True, slots=True, kw_only=True)
class FakeProcess:
    """A process for read_processes. A vanished one raises NoSuchProcess on its first read."""

    pid: int
    vanished: bool = False

    def oneshot(self) -> AbstractContextManager[None]:
        """Read every value at once."""
        return nullcontext()

    def memory_info(self) -> _Memory:
        """Return the resident memory, or raise for a vanished process."""
        if self.vanished:
            raise psutil.NoSuchProcess(self.pid)
        return _Memory(rss=1024 * self.pid)

    def name(self) -> str:
        """Return the name."""
        return f"proc{self.pid}"

    def username(self) -> str:
        """Return the user."""
        return "gbasso"

    def cpu_percent(self, interval: float | None = None) -> float:
        """Return the CPU usage."""
        del interval
        return float(self.pid)


def test_the_rankings_are_highest_first() -> None:
    """Firefox leads the CPU ranking, and the largest resident set leads the memory one."""
    match collect_processes(FakeSource()):
        case Success(ProcessesSample() as sample):
            assert sample.top_cpu[0].name == "firefox"
            assert sample.top_memory[0].name == "firefox"
            assert [entry.pid for entry in sample.top_cpu][-1] == 1
        case _:
            raise AssertionError


def test_a_vanished_process_is_skipped() -> None:
    """A process that exits during the read drops out, and the read succeeds."""
    processes = [FakeProcess(pid=10), FakeProcess(pid=11, vanished=True), FakeProcess(pid=12)]
    entries = read_processes(processes)  # type: ignore[arg-type]
    assert [entry.pid for entry in entries] == [10, 12]
