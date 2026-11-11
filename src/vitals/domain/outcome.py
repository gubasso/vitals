"""Turn a Result into the union of its two cases, so mypy proves a match on it exhaustive."""

from returns.result import Failure, Result, Success


def outcome[T, E](result: Result[T, E]) -> Success[T] | Failure[E]:
    """Return the result as `Success[T] | Failure[E]`.

    `Result` is an abstract class, not a union, so mypy cannot prove that a `match` on it
    covers both cases. A `match` on the union that this function returns is exhaustive,
    and `exhaustive-match` fails the one that misses a case.
    """
    if isinstance(result, Success):
        return result
    if isinstance(result, Failure):
        return result
    # returns defines no third subclass of Result, so this line never runs.
    raise TypeError(type(result).__name__)


def value_or_none[T, E](result: Result[T, E]) -> T | None:
    """Return the value of a Success, or None for a Failure."""
    match outcome(result):
        case Success(value):
            return value
        case Failure(_):
            return None
