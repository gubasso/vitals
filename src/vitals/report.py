"""Write a Snapshot as JSON, for `vitals --once`."""

import dataclasses
import json

from returns.result import Failure, Result, Success

from vitals.domain.outcome import outcome
lazy from vitals.domain.errors import CollectorError
lazy from vitals.domain.samples import Snapshot

type Json = bool | int | float | str | list[Json] | dict[str, Json] | None


def _value[T](result: Result[T, CollectorError]) -> Json:
    match outcome(result):
        case Success(sample):
            return _plain(sample)
        case Failure(error):
            return {"error": {"kind": str(error.kind), "detail": error.detail}}


def _plain(value: object) -> Json:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _plain(getattr(value, field.name)) for field in dataclasses.fields(value)
        }
    if isinstance(value, tuple | list):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, bool | int | float | str):
        return value
    return str(value)


def snapshot_json(snapshot: Snapshot) -> str:
    """Return the snapshot as one JSON object, with a failed source as its kind and detail."""
    document: dict[str, Json] = {
        field.name: _value(getattr(snapshot, field.name)) for field in dataclasses.fields(snapshot)
    }
    return json.dumps(document, indent=2)


def failures(snapshot: Snapshot) -> dict[str, CollectorError]:
    """Return the error of each failed source, by the field name of the snapshot."""
    found: dict[str, CollectorError] = {}
    for field in dataclasses.fields(snapshot):
        match outcome(getattr(snapshot, field.name)):
            case Failure(error):
                found[field.name] = error
            case Success(_):
                pass
    return found


def every_source_failed(snapshot: Snapshot) -> bool:
    """Return whether no source of the snapshot gave a value."""
    return all(
        isinstance(getattr(snapshot, field.name), Failure) for field in dataclasses.fields(snapshot)
    )
