"""The memory collector returns the memory and the swap."""

import dataclasses

import pytest
from returns.result import Failure, Success

from vitals.adapters.fake_source import FakeSource
from vitals.collectors.memory import collect_memory
from vitals.domain.samples import MemorySample


def test_the_sample_holds_memory_and_swap() -> None:
    """Both usages come back, with their share in percent."""
    match collect_memory(FakeSource()):
        case Success(MemorySample() as sample):
            assert round(sample.memory.percent) == 40
            assert sample.swap.total > sample.swap.used
        case _:
            raise AssertionError


def test_the_sample_is_frozen() -> None:
    """A sample cannot change after the collector returns it."""
    match collect_memory(FakeSource()):
        case Success(MemorySample() as sample):
            with pytest.raises(dataclasses.FrozenInstanceError):
                sample.memory = sample.swap  # type: ignore[misc]
        case _:
            raise AssertionError


def test_a_failed_source_fails() -> None:
    """A failed source gives a Failure."""
    assert isinstance(collect_memory(FakeSource(failing=frozenset({"memory"}))), Failure)
